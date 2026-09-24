"""
FlowAI API — thin Flask layer over the existing backend modules.

This file does not change any of your original logic in
route_analysis.py / ai_recommendations.py / notifications.py /
llm_assistant.py — it just exposes them over HTTP so the frontend
can call them.

Run:
    pip install -r requirements.txt
    python app.py
Server starts on http://localhost:5000
"""

import os
from functools import wraps
from flask import Flask, request, jsonify, session
from flask_cors import CORS

from route_analysis import get_route
from ai_recommendations import get_recommendations
from notifications import generate_notifications
from llm_assistant import ask_traffic_assistant
from models import db, User, SavedRoute, AnalysisLog

app = Flask(__name__)

# SECRET_KEY signs the login session cookie — set a real random value via
# env var in production. Falls back to a dev-only value locally.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///flowai.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "None"
# Browsers silently reject a SameSite=None cookie unless Secure is also
# true — this was defaulting to False on Render (since FLASK_ENV wasn't
# set there), which meant the login session cookie never actually got
# stored, so every request after login looked "logged out."
# Render always serves https, so default to secure=True; only disable it
# for explicit local http development.
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") != "development"

db.init_app(app)
with app.app_context():
    db.create_all()

# credentials=True is required so login-session cookies work across the
# frontend (different port/domain) — "*" is not allowed with credentials,
# so list the exact frontend origin(s) instead.
FRONTEND_ORIGINS = os.environ.get(
    "FRONTEND_ORIGIN", "http://localhost:8080,http://127.0.0.1:8080"
).split(",")
CORS(app, supports_credentials=True, origins=FRONTEND_ORIGINS)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.post("/api/auth/signup")
def signup():
    data = request.get_json(force=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "username, email and password are all required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already in use"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return jsonify({"user": user.to_dict()})


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username/email or password"}), 401

    session["user_id"] = user.id
    return jsonify({"user": user.to_dict()})


@app.post("/api/auth/logout")
def logout():
    session.pop("user_id", None)
    return jsonify({"ok": True})


@app.get("/api/auth/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"user": None})
    user = db.session.get(User, user_id)
    return jsonify({"user": user.to_dict() if user else None})


@app.post("/api/routes/save")
@login_required
def save_route():
    """
    Body: { route, distance_km, duration_min, congestion_index,
            traffic_level, advice, source: {lat,lng}, dest: {lat,lng} }
    (i.e. the same object /api/route returns, plus source/dest)
    """
    data = request.get_json(force=True) or {}
    source = data.get("source") or {}
    dest = data.get("dest") or {}

    saved = SavedRoute(
        user_id=session["user_id"],
        route_name=data.get("route", "Saved route"),
        distance_km=data.get("distance_km"),
        duration_min=data.get("duration_min"),
        congestion_index=data.get("congestion_index"),
        traffic_level=data.get("traffic_level"),
        advice=data.get("advice"),
        source_lat=source.get("lat"),
        source_lng=source.get("lng"),
        dest_lat=dest.get("lat"),
        dest_lng=dest.get("lng"),
    )
    db.session.add(saved)
    db.session.commit()
    return jsonify({"saved_route": saved.to_dict()})


@app.get("/api/routes/mine")
@login_required
def my_routes():
    routes = (
        SavedRoute.query.filter_by(user_id=session["user_id"])
        .order_by(SavedRoute.created_at.desc())
        .all()
    )
    return jsonify({"saved_routes": [r.to_dict() for r in routes]})


@app.delete("/api/routes/<int:route_id>")
@login_required
def delete_route(route_id):
    route = db.session.get(SavedRoute, route_id)
    if not route or route.user_id != session["user_id"]:
        return jsonify({"error": "Route not found"}), 404
    db.session.delete(route)
    db.session.commit()
    return jsonify({"ok": True})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "FlowAI backend"})


@app.post("/api/route")
def route():
    """
    Body: { "source": {"lat": 23.0395, "lng": 72.5714},
            "dest":   {"lat": 22.9961, "lng": 72.6019},
            "source_name": "Satellite",   # optional, for labeling
            "dest_name":   "Maninagar" }  # optional, for labeling
    """
    data = request.get_json(force=True) or {}
    source = data.get("source")
    dest = data.get("dest")
    source_name = data.get("source_name", "Origin")
    dest_name = data.get("dest_name", "Destination")

    if not source or not dest:
        return jsonify({"error": "source and dest are required, each as {lat, lng}"}), 400

    try:
        source_coords = [source["lng"], source["lat"]]
        dest_coords = [dest["lng"], dest["lat"]]
        result = get_route(source_coords, dest_coords)
        result["route"] = f"{source_name} → {dest_name}"

        # Quietly log this analysis for the trend feature — only if logged in,
        # and this is separate from explicitly "saving" a route.
        if "user_id" in session:
            log = AnalysisLog(
                user_id=session["user_id"],
                route_name=result["route"],
                congestion_index=result.get("congestion_index"),
            )
            db.session.add(log)
            db.session.commit()

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.get("/api/routes/trend")
@login_required
def route_trend():
    """
    Query param: ?route=Satellite%20%E2%86%92%20Maninagar
    Returns up to the last 5 congestion readings for this exact route name,
    for the logged-in user, oldest first.
    """
    route_name = request.args.get("route", "")
    logs = (
        AnalysisLog.query.filter_by(user_id=session["user_id"], route_name=route_name)
        .order_by(AnalysisLog.created_at.desc())
        .limit(5)
        .all()
    )
    logs.reverse()  # oldest first, for a left-to-right trend
    return jsonify({"trend": [l.to_dict() for l in logs]})


@app.post("/api/recommendations")
def recommendations():
    """
    Body: { "traffic_data": [ {route, distance_km, duration_min,
                                congestion_index, traffic_level}, ... ] }
    """
    data = request.get_json(force=True) or {}
    traffic_data = data.get("traffic_data")
    if not traffic_data:
        return jsonify({"error": "traffic_data (non-empty list) is required"}), 400
    try:
        recs = get_recommendations(traffic_data)
        return jsonify({"recommendations": recs})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.post("/api/notifications")
def notifications():
    """
    Body: { "traffic_data": [ {route, congestion_index}, ... ] }
    """
    data = request.get_json(force=True) or {}
    traffic_data = data.get("traffic_data")
    if not traffic_data:
        return jsonify({"error": "traffic_data (non-empty list) is required"}), 400
    try:
        notifs = generate_notifications(traffic_data)
        return jsonify({"notifications": notifs})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.post("/api/chat")
def chat():
    """
    Body: { "question": "...", "route_data": {...} | null }
    """
    data = request.get_json(force=True) or {}
    question = data.get("question")
    route_data = data.get("route_data")
    if not question:
        return jsonify({"error": "question is required"}), 400
    try:
        answer = ask_traffic_assistant(question, route_data)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
