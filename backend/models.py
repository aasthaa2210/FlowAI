from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    saved_routes = db.relationship("SavedRoute", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email}


class AnalysisLog(db.Model):
    """Every route analysis a logged-in user runs gets logged here
    (separate from SavedRoute, which is an explicit bookmark) so we can
    show a congestion trend for routes checked more than once."""
    __tablename__ = "analysis_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    route_name = db.Column(db.String(200), nullable=False)
    congestion_index = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "congestion_index": self.congestion_index,
            "created_at": self.created_at.isoformat(),
        }


class SavedRoute(db.Model):
    __tablename__ = "saved_routes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    route_name = db.Column(db.String(200), nullable=False)
    distance_km = db.Column(db.Float)
    duration_min = db.Column(db.Float)
    congestion_index = db.Column(db.Float)
    traffic_level = db.Column(db.String(50))
    advice = db.Column(db.String(255))

    source_lat = db.Column(db.Float)
    source_lng = db.Column(db.Float)
    dest_lat = db.Column(db.Float)
    dest_lng = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "route": self.route_name,
            "distance_km": self.distance_km,
            "duration_min": self.duration_min,
            "congestion_index": self.congestion_index,
            "traffic_level": self.traffic_level,
            "advice": self.advice,
            "source": {"lat": self.source_lat, "lng": self.source_lng},
            "dest": {"lat": self.dest_lat, "lng": self.dest_lng},
            "created_at": self.created_at.isoformat(),
        }

