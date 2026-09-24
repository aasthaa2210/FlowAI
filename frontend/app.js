/* ══════════════════════════════════════════════
   CONFIG
   Change this one line once your backend is deployed —
   e.g. "https://flowai-backend.onrender.com/api"
═══════════════════════════════════════════════ */
const API_BASE = "http://localhost:5000/api";

// Preset Ahmedabad locations (lat/lng) for the route selects.
// Purely geographic reference data, used to call your backend's
// get_route(source, dest).
const LOCATIONS = [
  { name: "Satellite",        lat: 23.0225, lng: 72.5138 },
  { name: "Vastrapur",        lat: 23.0367, lng: 72.5297 },
  { name: "Bopal",            lat: 23.0339, lng: 72.4661 },
  { name: "Thaltej",          lat: 23.0522, lng: 72.5066 },
  { name: "Science City",     lat: 23.0670, lng: 72.4880 },
  { name: "Gota",             lat: 23.1057, lng: 72.5306 },
  { name: "Chandkheda",       lat: 23.1102, lng: 72.5797 },
  { name: "Sabarmati",        lat: 23.0730, lng: 72.5820 },
  { name: "Naranpura",        lat: 23.0553, lng: 72.5556 },
  { name: "Ambawadi",         lat: 23.0257, lng: 72.5556 },
  { name: "Ellis Bridge",     lat: 23.0243, lng: 72.5714 },
  { name: "Kalupur",          lat: 23.0280, lng: 72.6010 },
  { name: "Paldi",            lat: 23.0128, lng: 72.5645 },
  { name: "Maninagar",        lat: 22.9961, lng: 72.6019 },
  { name: "Isanpur",          lat: 22.9762, lng: 72.6172 },
  { name: "Vatva GIDC",       lat: 22.9530, lng: 72.6435 },
  { name: "Narol",            lat: 22.9552, lng: 72.5964 },
  { name: "CTM",              lat: 23.0210, lng: 72.6280 },
  { name: "Bodakdev",         lat: 23.0396, lng: 72.5060 },
  { name: "Memnagar",         lat: 23.0447, lng: 72.5443 },
];

/* ══════════════════════════════════════════════
   STATE
═══════════════════════════════════════════════ */
let history = []; // array of { route, distance_km, duration_min, congestion_index, traffic_level }
let lastRouteData = null;
let lastFrom = null;   // { name, lat, lng } of the last analyzed "from"
let lastDest = null;   // { name, lat, lng } of the last analyzed "to"
let currentUser = null;
let savedRoutesCache = [];
let leafletMap = null;
let mapMarkers = [];
let mapLine = null;

// All API calls include credentials so the login-session cookie is sent —
// required since the frontend and backend run on different ports.
async function api(path, options = {}){
  return fetch(`${API_BASE}${path}`, { ...options, credentials: "include" });
}

/* ══════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  populateSelects();
  buildGaugeTicks();
  tickClock();
  setInterval(tickClock, 1000);

  document.getElementById("routeForm").addEventListener("submit", onAnalyze);
  document.getElementById("recBtn").addEventListener("click", onGenerateRecommendations);
  document.getElementById("chatToggle").addEventListener("click", toggleChat);
  document.getElementById("chatClose").addEventListener("click", toggleChat);
  document.getElementById("chatForm").addEventListener("submit", onChatSubmit);
  document.getElementById("saveRouteBtn").addEventListener("click", onSaveRoute);

  // auth
  document.getElementById("tabLogin").addEventListener("click", () => switchAuthTab("login"));
  document.getElementById("tabSignup").addEventListener("click", () => switchAuthTab("signup"));
  document.getElementById("loginForm").addEventListener("submit", onLogin);
  document.getElementById("signupForm").addEventListener("submit", onSignup);
  document.getElementById("logoutBtn").addEventListener("click", onLogout);

  // profile modal
  document.getElementById("profileBtn").addEventListener("click", openProfileModal);
  document.getElementById("profileClose").addEventListener("click", closeProfileModal);
  document.getElementById("profileModal").addEventListener("click", (e) => {
    if(e.target.id === "profileModal") closeProfileModal();
  });

  checkSession();
});

/* ══════════════════════════════════════════════
   AUTH
═══════════════════════════════════════════════ */
async function checkSession(){
  try{
    const res = await api("/auth/me");
    const data = await res.json();
    if(data.user){
      onLoggedIn(data.user);
    }else{
      showAuthScreen();
    }
  }catch(e){
    showAuthScreen();
  }
}

function showAuthScreen(){
  document.getElementById("authScreen").hidden = false;
  document.getElementById("appScreen").hidden = true;
}

function onLoggedIn(user){
  currentUser = user;
  document.getElementById("authScreen").hidden = true;
  document.getElementById("appScreen").hidden = false;
  document.getElementById("profileUsername").textContent = user.username;
  document.getElementById("profileAvatar").textContent = user.username.slice(0, 1);
  checkApiHealth();
  loadSavedRoutes();
}

function switchAuthTab(which){
  const isLogin = which === "login";
  document.getElementById("tabLogin").classList.toggle("active", isLogin);
  document.getElementById("tabSignup").classList.toggle("active", !isLogin);
  document.getElementById("loginForm").hidden = !isLogin;
  document.getElementById("signupForm").hidden = isLogin;
}

async function onLogin(e){
  e.preventDefault();
  const errBox = document.getElementById("loginError");
  errBox.hidden = true;
  const username = document.getElementById("loginId").value.trim();
  const password = document.getElementById("loginPassword").value;

  try{
    const res = await api("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Login failed");
    onLoggedIn(data.user);
  }catch(err){
    showError(errBox, err.message);
  }
}

async function onSignup(e){
  e.preventDefault();
  const errBox = document.getElementById("signupError");
  errBox.hidden = true;
  const username = document.getElementById("signupUsername").value.trim();
  const email = document.getElementById("signupEmail").value.trim();
  const password = document.getElementById("signupPassword").value;

  try{
    const res = await api("/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Signup failed");
    onLoggedIn(data.user);
  }catch(err){
    showError(errBox, err.message);
  }
}

async function onLogout(){
  try{ await api("/auth/logout", { method: "POST" }); }catch(e){}
  currentUser = null;
  history = [];
  lastRouteData = null;
  renderHistory();
  document.getElementById("resultBlock").hidden = true;
  document.getElementById("trendNote").hidden = true;
  document.getElementById("mapContainer").hidden = true;
  document.getElementById("recGrid").innerHTML = "";
  document.getElementById("notifList").innerHTML = `<div class="empty-state">Analyze a route to generate alerts.</div>`;
  showAuthScreen();
}

/* ══════════════════════════════════════════════
   PROFILE MODAL
═══════════════════════════════════════════════ */
function openProfileModal(){
  if(!currentUser) return;
  document.getElementById("profileModalUsername").textContent = currentUser.username;
  document.getElementById("profileModalEmail").textContent = currentUser.email;
  document.getElementById("profileModalCount").textContent =
    document.querySelectorAll("#savedList .saved-row").length;
  document.getElementById("profileModal").hidden = false;
}
function closeProfileModal(){
  document.getElementById("profileModal").hidden = true;
}

function populateSelects(){
  const from = document.getElementById("fromSelect");
  const to = document.getElementById("toSelect");
  LOCATIONS.forEach((loc, i) => {
    from.appendChild(new Option(loc.name, i));
    to.appendChild(new Option(loc.name, i));
  });
  from.selectedIndex = 0;
  to.selectedIndex = 1;
}

function buildGaugeTicks(){
  const wrap = document.getElementById("gaugeTicks");
  const heights = ["short","mid","short","mid","tall","mid","short","mid","short","mid","tall",
                    "short","mid","short","tall","mid","short","mid","short","tall","short"];
  wrap.innerHTML = "";
  heights.forEach(h => {
    const el = document.createElement("div");
    el.className = "tick " + h;
    wrap.appendChild(el);
  });
}

function tickClock(){
  const now = new Date();
  document.getElementById("clock").textContent = now.toLocaleTimeString("en-GB");
  document.getElementById("clockDate").textContent = now.toLocaleDateString("en-US", {
    weekday:"short", day:"2-digit", month:"short"
  });
}

async function checkApiHealth(){
  const el = document.getElementById("apiStatus");
  try{
    const res = await api("/health");
    if(!res.ok) throw new Error();
    el.textContent = "API connected";
    el.className = "api-status ok";
  }catch(e){
    el.textContent = "API unreachable — start the Flask server";
    el.className = "api-status err";
  }
}

/* ══════════════════════════════════════════════
   ROUTE ANALYSIS
═══════════════════════════════════════════════ */
async function onAnalyze(e){
  e.preventDefault();
  const fromIdx = +document.getElementById("fromSelect").value;
  const toIdx = +document.getElementById("toSelect").value;
  const from = LOCATIONS[fromIdx];
  const to = LOCATIONS[toIdx];

  if(fromIdx === toIdx){
    showError(document.getElementById("routeError"), "Pick two different locations.");
    return;
  }
  await doAnalyze(from, to);
}

async function onReanalyzeSaved(id){
  const saved = savedRoutesCache.find(r => String(r.id) === String(id));
  if(!saved) return;
  const [fromName, toName] = saved.route.split(" → ");
  const from = { name: fromName || "Origin", lat: saved.source.lat, lng: saved.source.lng };
  const to = { name: toName || "Destination", lat: saved.dest.lat, lng: saved.dest.lng };
  await doAnalyze(from, to);
  // scroll the result into view since this was triggered from a panel further down the page
  document.getElementById("resultBlock").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function doAnalyze(from, to){
  const errBox = document.getElementById("routeError");
  errBox.hidden = true;

  const btn = document.getElementById("analyzeBtn");
  btn.disabled = true;
  btn.textContent = "Analyzing…";

  try{
    const res = await api("/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: { lat: from.lat, lng: from.lng },
        dest: { lat: to.lat, lng: to.lng },
        source_name: from.name,
        dest_name: to.name
      })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Route request failed");

    lastRouteData = data;
    lastFrom = from;
    lastDest = to;
    renderResult(data);
    drawRouteOnMap(from, to, data.geometry);
    history.unshift(data);
    renderHistory();
    document.getElementById("recBtn").disabled = false;
    document.getElementById("saveRouteBtn").textContent = "☆ Save this route";
    document.getElementById("saveRouteBtn").classList.remove("saved");
    refreshNotifications();
    loadTrend(data.route);
  }catch(err){
    showError(errBox, err.message);
  }finally{
    btn.disabled = false;
    btn.textContent = "Analyze route";
  }
}

/* ══════════════════════════════════════════════
   CONGESTION TREND
═══════════════════════════════════════════════ */
async function loadTrend(routeName){
  const note = document.getElementById("trendNote");
  if(!currentUser){ note.hidden = true; return; }

  try{
    const res = await api(`/routes/trend?route=${encodeURIComponent(routeName)}`);
    const data = await res.json();
    if(!res.ok) throw new Error();

    const trend = data.trend || [];
    if(trend.length < 2){
      note.hidden = true;
      return;
    }
    const readings = trend.map(t => Number(t.congestion_index).toFixed(1)).join(" → ");
    note.hidden = false;
    note.innerHTML = `You've checked this route ${trend.length} times recently. Congestion: <span class="mono">${readings}</span>`;
  }catch(e){
    note.hidden = true;
  }
}

function showError(box, msg){
  box.textContent = msg;
  box.hidden = false;
}

function statusFromIndex(idx){
  if(idx <= 3) return "ok";
  if(idx <= 6) return "warn";
  return "bad";
}

function renderResult(data){
  const block = document.getElementById("resultBlock");
  block.hidden = false;

  document.getElementById("resultRoute").textContent = data.route || "—";
  document.getElementById("statDistance").textContent = fmtNum(data.distance_km);
  document.getElementById("statDuration").textContent = fmtNum(data.duration_min);

  const idx = Number(data.congestion_index) || 0;
  const status = statusFromIndex(idx);
  document.getElementById("gaugeValue").textContent = `${idx.toFixed(1)} / 10`;

  // needle position
  const pct = Math.min(Math.max(idx / 10, 0), 1) * 100;
  const needle = document.getElementById("gaugeNeedle");
  needle.style.left = `calc(${pct}% - 1px)`;

  // color the ticks up to the needle position
  const ticks = document.querySelectorAll("#gaugeTicks .tick");
  const activeCount = Math.round((idx / 10) * ticks.length);
  ticks.forEach((t, i) => {
    t.classList.remove("active-ok","active-warn","active-bad");
    if(i < activeCount) t.classList.add(`active-${status}`);
  });

  const tag = document.getElementById("adviceTag");
  tag.textContent = status === "ok" ? "Clear" : status === "warn" ? "Moderate" : "Heavy";
  tag.className = `advice-tag ${status}`;

  document.getElementById("adviceText").textContent =
    (data.traffic_level ? data.traffic_level.replace(/[🟢🟡🔴]/g,"").trim() + " — " : "") +
    describeCongestion(idx);
}

function describeCongestion(idx){
  if(idx <= 3) return "traffic is flowing normally on this route.";
  if(idx <= 6) return "expect some slowdowns, particularly at junctions.";
  return "significant delays likely — consider an alternate route or time.";
}

function fmtNum(n){
  const v = Number(n);
  return isNaN(v) ? "—" : v.toFixed(1);
}

function renderHistory(){
  const list = document.getElementById("historyList");
  if(history.length === 0){
    list.innerHTML = `<div class="empty-state">No routes analyzed yet.</div>`;
    return;
  }
  list.innerHTML = history.map((h, i) => {
    const status = statusFromIndex(Number(h.congestion_index) || 0);
    return `
      <div class="history-row">
        <div class="history-row-left">
          <span class="history-dot ${status}"></span>
          <span>${h.route}</span>
        </div>
        <span class="history-meta mono">${fmtNum(h.congestion_index)}/10</span>
      </div>`;
  }).join("");
}

/* ══════════════════════════════════════════════
   MAP (Leaflet)
═══════════════════════════════════════════════ */
function ensureMap(){
  if(leafletMap) return leafletMap;
  document.getElementById("mapContainer").hidden = false;
  leafletMap = L.map("map", { zoomControl: true, attributionControl: true })
    .setView([23.03, 72.55], 12); // Ahmedabad
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(leafletMap);
  // Leaflet needs a nudge to size correctly once its container becomes visible
  setTimeout(() => leafletMap.invalidateSize(), 50);
  return leafletMap;
}

function drawRouteOnMap(from, to, geometry){
  const map = ensureMap();

  mapMarkers.forEach(m => map.removeLayer(m));
  mapMarkers = [];
  if(mapLine) map.removeLayer(mapLine);

  const fromMarker = L.marker([from.lat, from.lng]).addTo(map).bindTooltip(from.name);
  const toMarker = L.marker([to.lat, to.lng]).addTo(map).bindTooltip(to.name);
  mapMarkers = [fromMarker, toMarker];

  if(Array.isArray(geometry) && geometry.length > 0){
    // backend returns [lng, lat] pairs (GeoJSON order) — Leaflet wants [lat, lng]
    const latlngs = geometry.map(([lng, lat]) => [lat, lng]);
    mapLine = L.polyline(latlngs, { color: "#16181d", weight: 3 }).addTo(map);
    map.fitBounds(mapLine.getBounds(), { padding: [24, 24] });
  }else{
    map.fitBounds(L.latLngBounds([[from.lat, from.lng], [to.lat, to.lng]]), { padding: [40, 40] });
  }
  setTimeout(() => map.invalidateSize(), 50);
}

/* ══════════════════════════════════════════════
   SAVE / SAVED ROUTES
═══════════════════════════════════════════════ */
async function onSaveRoute(){
  if(!lastRouteData || !lastFrom || !lastDest) return;
  const btn = document.getElementById("saveRouteBtn");
  btn.disabled = true;

  try{
    const res = await api("/routes/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...lastRouteData,
        source: { lat: lastFrom.lat, lng: lastFrom.lng },
        dest: { lat: lastDest.lat, lng: lastDest.lng }
      })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Couldn't save route");

    btn.textContent = "★ Saved";
    btn.classList.add("saved");
    loadSavedRoutes();
  }catch(err){
    alert(err.message); // small/rare action — a native alert is fine here
  }finally{
    btn.disabled = false;
  }
}

async function loadSavedRoutes(){
  const list = document.getElementById("savedList");
  try{
    const res = await api("/routes/mine");
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Couldn't load saved routes");

    const routes = data.saved_routes || [];
    if(routes.length === 0){
      list.innerHTML = `<div class="empty-state">No saved routes yet.</div>`;
      return;
    }
    list.innerHTML = routes.map(r => `
      <div class="saved-row" data-id="${r.id}">
        <div class="saved-row-main">
          <div class="saved-route-name">${escapeHtml(r.route)}</div>
          <div class="saved-route-meta mono">${fmtNum(r.distance_km)} km · ${fmtNum(r.congestion_index)}/10 congestion</div>
        </div>
        <button class="saved-reanalyze" data-id="${r.id}" title="Re-analyze this route">↻</button>
        <button class="saved-delete" aria-label="Delete" data-id="${r.id}">×</button>
      </div>`).join("");

    savedRoutesCache = routes;
    list.querySelectorAll(".saved-delete").forEach(btn => {
      btn.addEventListener("click", () => onDeleteSavedRoute(btn.dataset.id));
    });
    list.querySelectorAll(".saved-reanalyze").forEach(btn => {
      btn.addEventListener("click", () => onReanalyzeSaved(btn.dataset.id));
    });
  }catch(err){
    list.innerHTML = `<div class="empty-state">Couldn't load saved routes: ${escapeHtml(err.message)}</div>`;
  }
}

async function onDeleteSavedRoute(id){
  try{
    const res = await api(`/routes/${id}`, { method: "DELETE" });
    if(!res.ok){
      const data = await res.json();
      throw new Error(data.error || "Couldn't delete route");
    }
    loadSavedRoutes();
  }catch(err){
    alert(err.message);
  }
}


async function refreshNotifications(){
  const list = document.getElementById("notifList");
  if(history.length === 0) return;
  try{
    const res = await api("/notifications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ traffic_data: history })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Notifications request failed");

    const notifs = data.notifications || [];
    if(notifs.length === 0){
      list.innerHTML = `<div class="empty-state">No alerts right now.</div>`;
      return;
    }
    list.innerHTML = notifs.map(n => renderNotif(n)).join("");
  }catch(err){
    list.innerHTML = `<div class="empty-state">Couldn't load notifications: ${escapeHtml(err.message)}</div>`;
  }
}

function renderNotif(n){
  // Backend format may vary — handle string or object entries defensively.
  if(typeof n === "string"){
    return `
      <div class="notif-item info">
        <div class="notif-msg">${escapeHtml(n)}</div>
      </div>`;
  }
  const level = (n.level || n.type || "info").toString().toLowerCase();
  const cls = ["alert","warn","ok"].includes(level) ? level : "info";
  return `
    <div class="notif-item ${cls}">
      <div class="notif-head"><span>${escapeHtml(n.route || "Route alert")}</span><span>${escapeHtml(n.time || "")}</span></div>
      <div class="notif-title">${escapeHtml(n.title || n.level || "Alert")}</div>
      <div class="notif-msg">${escapeHtml(n.message || n.text || JSON.stringify(n))}</div>
    </div>`;
}

/* ══════════════════════════════════════════════
   AI RECOMMENDATIONS
═══════════════════════════════════════════════ */
async function onGenerateRecommendations(){
  const btn = document.getElementById("recBtn");
  const errBox = document.getElementById("recError");
  const grid = document.getElementById("recGrid");
  errBox.hidden = true;
  btn.disabled = true;
  btn.textContent = "Generating…";

  try{
    const res = await api("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ traffic_data: history })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Recommendations request failed");

    const recs = data.recommendations || [];
    grid.innerHTML = recs.map(r => renderRec(r)).join("") ||
      `<div class="empty-state">No recommendations returned.</div>`;
  }catch(err){
    showError(errBox, err.message);
  }finally{
    btn.disabled = false;
    btn.textContent = "Generate insights";
  }
}

function renderRec(r){
  if(typeof r === "string"){
    return `<div class="rec-card"><div class="rec-body">${escapeHtml(r)}</div></div>`;
  }
  const priority = (r.tag || r.priority || "info").toString().toLowerCase();
  const cls = ["urgent","active","pending"].includes(priority) ? priority : "info";
  const icon = r.icon ? escapeHtml(r.icon) + " " : "";
  return `
    <div class="rec-card">
      <div class="rec-head">
        <span class="rec-icon">${icon}</span>
        <span class="rec-title">${escapeHtml(r.title || r.route || "Recommendation")}</span>
      </div>
      <div class="rec-body">${escapeHtml(r.body || r.description || r.message || r.text || JSON.stringify(r))}</div>
      <span class="rec-tag ${cls}">${escapeHtml(priority)}</span>
    </div>`;
}

/* ══════════════════════════════════════════════
   CHAT ASSISTANT
═══════════════════════════════════════════════ */
function toggleChat(){
  const panel = document.getElementById("chatPanel");
  const toggle = document.getElementById("chatToggle");
  const open = panel.hidden;
  panel.hidden = !open;
  toggle.setAttribute("aria-expanded", String(open));
  if(open) document.getElementById("chatInput").focus();
}

async function onChatSubmit(e){
  e.preventDefault();
  const input = document.getElementById("chatInput");
  const question = input.value.trim();
  if(!question) return;
  input.value = "";

  appendChatMsg(question, "user");
  const pendingEl = appendChatMsg("Thinking…", "bot pending");

  try{
    const res = await api("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, route_data: lastRouteData })
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || "Chat request failed");
    pendingEl.textContent = data.answer;
    pendingEl.className = "chat-msg bot";
  }catch(err){
    pendingEl.textContent = `Couldn't reach the assistant: ${err.message}`;
    pendingEl.className = "chat-msg bot";
  }
}

function appendChatMsg(text, cls){
  const container = document.getElementById("chatMessages");
  const el = document.createElement("div");
  el.className = `chat-msg ${cls}`;
  el.textContent = text;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
  return el;
}

function escapeHtml(str){
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}
