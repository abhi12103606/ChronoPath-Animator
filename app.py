import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import re
import shutil
import math
import hashlib
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

st.set_page_config(
    layout='wide',
    page_title='ChronoPath | 10-Year Travel Animator',
    page_icon='🧭'
)

# --- CUSTOM BRAND LOGO & GLOBAL STYLING ---
LOGO_SVG = """
<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" rx="12" fill="url(#paint0_linear)"/>
  <path d="M12 34C16 26 20 30 24 22C28 14 32 18 36 12" stroke="#F8FAFC" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="12" cy="34" r="4" fill="#4ADE80"/>
  <circle cx="24" cy="22" r="3.5" fill="#FB923C"/>
  <circle cx="36" cy="12" r="4.5" fill="#38BDF8"/>
  <defs>
    <linearGradient id="paint0_linear" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
      <stop stop-color="#2563EB"/>
      <stop offset="1" stop-color="#7C3AED"/>
    </linearGradient>
  </defs>
</svg>
"""

st.markdown("""
<style>
    .brand-header {
        display: flex; align-items: center; gap: 16px;
        padding: 14px 22px; background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155; border-radius: 14px; margin-bottom: 20px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.35);
    }
    .brand-title { margin: 0; font-size: 26px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px; }
    .brand-sub { margin: 2px 0 0 0; font-size: 13.5px; color: #94a3b8; }
    .auth-card {
        background: #1e293b; border: 1px solid #334155; border-radius: 14px;
        padding: 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    .guide-card {
        background: #0f172a; border: 1px solid #334155; border-radius: 14px;
        padding: 22px; height: 100%;
    }
    .pw-rules {
        font-size: 12px; color: #94a3b8; background: #0f172a;
        padding: 8px 12px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 10px;
    }
    .wrapped-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 12px; padding: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25); height: 100%;
    }
    .wrapped-val { font-size: 22px; font-weight: 800; color: #38bdf8; margin: 4px 0; }
    .wrapped-lbl { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
""", unsafe_allow_html=True)

def render_brand_header():
    st.markdown(f"""
    <div class="brand-header">
        <div>{LOGO_SVG}</div>
        <div>
            <h1 class="brand-title">ChronoPath Animator</h1>
            <p class="brand-sub">Interactive 10-Year Mobile Timeline, Heatmap & Multi-Modal Route Visualizer</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_extraction_guide(expanded_default=True):
    with st.expander("📲 How to Extract Your Google Maps Timeline JSON File (Android & iOS Guide)", expanded=expanded_default):
        st.markdown("""
        **⚠️ Important Heads-Up:** Following Google's late 2024 update, the web-based version of Timeline was shut down, and location history is now **strictly stored on your mobile device**. Traditional exports via web-based Google Takeout no longer capture recent data. Follow the steps below on your phone to get your `Timeline.json` file:
        """)
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("""
            <div class="guide-card">
                <h4 style="margin-top:0; color:#4ade80;">🤖 For Android Users</h4>
                <p style="font-size:13px; color:#cbd5e1;">Export directly through your system's location settings:</p>
                <ol style="font-size:13.5px; line-height:1.7; color:#f8fafc;">
                    <li>Open your phone's <b>Settings</b> app.</li>
                    <li>Scroll down and select <b>Location</b> → <b>Location services</b>.</li>
                    <li>Tap on <b>Timeline</b>.</li>
                    <li>Tap <b>Export Timeline data</b>.</li>
                    <li>Tap <b>Continue</b> and select a folder on your device (such as your <code>Downloads</code> folder) to save your <code>Timeline.json</code> file.</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        with g_col2:
            st.markdown("""
            <div class="guide-card">
                <h4 style="margin-top:0; color:#38bdf8;">🍏 For iOS Users (iPhone & iPad)</h4>
                <p style="font-size:13px; color:#cbd5e1;">Export directly inside the Google Maps application:</p>
                <ol style="font-size:13.5px; line-height:1.7; color:#f8fafc;">
                    <li>Open the <b>Google Maps</b> app.</li>
                    <li>Tap your <b>profile picture or initials</b> in the top right corner.</li>
                    <li>Select <b>Settings</b> → <b>Personal content</b>.</li>
                    <li>Scroll down and tap <b>Export Timeline data</b>.</li>
                    <li>Use the share sheet to save the JSON file to your native Apple <b>Files</b> app.</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

# --- SHA-256 PASSWORD HASHING & VALIDATION ---
def hash_password(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def verify_password(stored_pw, provided_pw):
    if len(stored_pw) == 64 and all(c in '0123456789abcdef' for c in stored_pw.lower()):
        return stored_pw.lower() == hash_password(provided_pw).lower()
    return stored_pw == provided_pw

def validate_password_strength(pw):
    if len(pw) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", pw):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", pw):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"\d", pw):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;/~`]", pw):
        return False, "Password must contain at least one special character (e.g. !@#$%^&*)."
    return True, ""

# --- USER AUTHENTICATION & AUDIT SYSTEM ---
USERS_DIR = 'data/users'
USERS_FILE = 'data/users.json'
os.makedirs(USERS_DIR, exist_ok=True)

def save_users(users):
    os.makedirs('data', exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
        except Exception:
            users = {}
    else:
        users = {}

    modified = False
    if "abhishek" not in users:
        users["abhishek"] = {
            "password": hash_password("1234Abhi$%"),
            "role": "admin",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        modified = True

    for u, info in users.items():
        pw = info.get("password", "")
        if not (len(pw) == 64 and all(c in '0123456789abcdef' for c in pw.lower())):
            info["password"] = hash_password(pw)
            modified = True

    if modified:
        save_users(users)
    return users

def update_user_audit(username, total_trips=None, total_km=None, active_days=None):
    users = load_users()
    if username in users:
        users[username]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if total_trips is not None:
            users[username]["total_trips"] = int(total_trips)
        if total_km is not None:
            users[username]["total_km"] = round(float(total_km), 1)
        if active_days is not None:
            users[username]["active_days"] = int(active_days)
        save_users(users)
        st.session_state.users = users

st.session_state.users = load_users()

if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'inspect_user' not in st.session_state:
    st.session_state.inspect_user = None

render_brand_header()

# --- FULL-PAGE LOGIN / SIGN-UP GATE ---
if st.session_state.logged_in_user is None:
    auth_col, info_col = st.columns([1.15, 1.85], gap="large")

    with auth_col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.subheader("🔐 Welcome to ChronoPath")
        st.caption("Sign in or create an account to visualize your interactive travel timeline.")

        tab_login, tab_signup = st.tabs(["🔑 Log In", "✨ Sign Up (Instant Access)"])

        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("Username").strip().lower()
                login_pass = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Log In to Animator", use_container_width=True)

                if submit_login:
                    users_db = load_users()
                    u_obj = users_db.get(login_user)
                    if u_obj and verify_password(u_obj.get("password", ""), login_pass):
                        st.session_state.logged_in_user = login_user
                        st.session_state.role = u_obj.get("role", "user")
                        st.session_state.inspect_user = login_user
                        update_user_audit(login_user)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password.")

        with tab_signup:
            with st.form("signup_form"):
                new_user = st.text_input("Choose a Username (letters & numbers)").strip().lower()
                new_email = st.text_input("Email Address (Optional)").strip()
                new_pass = st.text_input("Create Password", type="password")
                new_pass_confirm = st.text_input("Confirm Password", type="password")
                st.markdown("""
                <div class="pw-rules">
                    🔒 <b>Password Requirements:</b> Min 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special symbol (<code>!@#$%^&*</code>). SHA-256 encrypted.
                </div>
                """, unsafe_allow_html=True)
                submit_signup = st.form_submit_button("🚀 Create Account & Continue", use_container_width=True)

                if submit_signup:
                    users_db = load_users()
                    pw_ok, pw_msg = validate_password_strength(new_pass)
                    if not new_user or not new_pass:
                        st.error("⚠️ Username and password are required.")
                    elif not new_user.isalnum():
                        st.error("⚠️ Username must contain only letters and numbers.")
                    elif new_user in users_db:
                        st.error("⚠️ Username already exists! Please switch to the Log In tab.")
                    elif not pw_ok:
                        st.error(f"⚠️ {pw_msg}")
                    elif new_pass != new_pass_confirm:
                        st.error("⚠️ Passwords do not match.")
                    else:
                        assigned_role = "admin" if new_user == "abhishek" else "user"
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        users_db[new_user] = {
                            "password": hash_password(new_pass),
                            "email": new_email,
                            "role": assigned_role,
                            "created_at": now_str,
                            "last_active": now_str,
                            "total_trips": 0,
                            "total_km": 0.0,
                            "active_days": 0
                        }
                        save_users(users_db)
                        os.makedirs(os.path.join(USERS_DIR, new_user), exist_ok=True)
                        st.session_state.users = users_db
                        st.session_state.logged_in_user = new_user
                        st.session_state.role = assigned_role
                        st.session_state.inspect_user = new_user
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with info_col:
        render_extraction_guide(expanded_default=True)

    st.stop()

# --- LOGGED-IN SIDEBAR & LEADERBOARD TOGGLE ---
active_account = st.session_state.inspect_user or st.session_state.logged_in_user
st.sidebar.markdown(f"### 👤 `{st.session_state.logged_in_user}`")
if active_account != st.session_state.logged_in_user:
    st.sidebar.info(f"👁️ Inspecting user: **{active_account}**")
    if st.sidebar.button("⬅️ Return to My Timeline", use_container_width=True):
        st.session_state.inspect_user = st.session_state.logged_in_user
        st.rerun()

show_leaderboard = st.sidebar.checkbox("🏆 View Community Leaderboard", value=False)

if st.sidebar.button("🚪 Log Out", use_container_width=True):
    st.session_state.logged_in_user = None
    st.session_state.role = None
    st.session_state.inspect_user = None
    st.rerun()

current_user_dir = os.path.join(USERS_DIR, active_account)
os.makedirs(current_user_dir, exist_ok=True)
current_user_file = os.path.join(current_user_dir, "Timeline.json")

if os.path.exists(current_user_file):
    if st.sidebar.button("🔄 Upload a Different Timeline File", use_container_width=True):
        os.remove(current_user_file)
        st.rerun()

# --- PRIVILEGED ADMIN DASHBOARD ---
if st.session_state.role == "admin":
    st.sidebar.markdown("---")
    st.sidebar.subheader("👑 Admin Control Center")
    open_admin = st.sidebar.checkbox("🛠️ Manage Users & Audit Log", value=False)

    if open_admin:
        st.markdown("## 👑 Admin Control Center: Audit Log, User Accounts & Timeline Files")
        st.caption("Inspect user activity, view any user's map directly, download their JSON, or permanently delete accounts.")

        users_db = load_users()
        user_rows = []
        for u_name, u_info in users_db.items():
            u_path = os.path.join(USERS_DIR, u_name, "Timeline.json")
            has_file = os.path.exists(u_path)
            size_mb = round(os.path.getsize(u_path) / (1024 * 1024), 2) if has_file else 0.0
            user_rows.append({
                "Username": u_name,
                "Role": u_info.get("role", "user"),
                "Email": u_info.get("email", "-"),
                "Status": "✅ Active File" if has_file else "❌ Empty",
                "File Size (MB)": size_mb,
                "Parsed Trips": u_info.get("total_trips", 0),
                "Lifetime KM": f"{u_info.get('total_km', 0.0):,.1f}",
                "Active Days": u_info.get("active_days", 0),
                "Last Active": u_info.get("last_active", u_info.get("created_at", "-"))
            })

        st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)

        all_usernames = list(users_db.keys())
        adm_col1, adm_col2 = st.columns([1.5, 3.5])
        with adm_col1:
            target_u = st.selectbox("Select User Account:", all_usernames)

        target_u_dir = os.path.join(USERS_DIR, target_u)
        target_u_file = os.path.join(target_u_dir, "Timeline.json")

        with adm_col2:
            st.write("**Privileged Admin Actions:**")
            act_c0, act_c1, act_c2, act_c3 = st.columns(4)

            with act_c0:
                if os.path.exists(target_u_file):
                    if st.button(f"👁️ View Map", use_container_width=True):
                        st.session_state.inspect_user = target_u
                        st.rerun()
                else:
                    st.button("No Map", disabled=True, use_container_width=True)

            with act_c1:
                if os.path.exists(target_u_file):
                    with open(target_u_file, "rb") as f:
                        st.download_button(
                            label=f"📥 Download",
                            data=f.read(),
                            file_name=f"{target_u}_Timeline.json",
                            mime="application/json",
                            use_container_width=True
                        )
                else:
                    st.button("No File", disabled=True, use_container_width=True)

            with act_c2:
                if os.path.exists(target_u_file):
                    if st.button(f"🗑️ Clear Data", use_container_width=True):
                        os.remove(target_u_file)
                        st.success(f"Removed Timeline file for '{target_u}'.")
                        st.rerun()
                else:
                    st.button("Empty", disabled=True, use_container_width=True)

            with act_c3:
                if target_u != "abhishek":
                    if st.button(f"❌ Delete", type="primary", use_container_width=True):
                        if os.path.exists(target_u_dir):
                            shutil.rmtree(target_u_dir, ignore_errors=True)
                        users_db.pop(target_u, None)
                        save_users(users_db)
                        st.session_state.users = users_db
                        if st.session_state.inspect_user == target_u:
                            st.session_state.inspect_user = st.session_state.logged_in_user
                        st.success(f"Account '{target_u}' permanently deleted!")
                        st.rerun()
                else:
                    st.button("🔒 Protected", disabled=True, use_container_width=True)

        st.markdown("---")

# --- COMMUNITY LEADERBOARD DASHBOARD ---
if show_leaderboard:
    st.markdown("## 🏆 Community Travel Leaderboard & Rankings")
    st.caption("Internal comparison across all users who have uploaded their timeline data.")
    
    users_db = load_users()
    lb_data = []
    for u_name, u_info in users_db.items():
        u_path = os.path.join(USERS_DIR, u_name, "Timeline.json")
        if os.path.exists(u_path):
            lb_data.append({
                "Username": u_name,
                "Total Distance (km)": u_info.get("total_km", 0.0),
                "Active Travel Days": u_info.get("active_days", 0),
                "Total Logged Trips": u_info.get("total_trips", 0)
            })
    
    if lb_data:
        df_lb = pd.DataFrame(lb_data)
        metric_choice = st.selectbox("Rank By:", ["Total Distance (km)", "Active Travel Days", "Total Logged Trips"])
        df_lb = df_lb.sort_values(by=metric_choice, ascending=False).reset_index(drop=True)
        df_lb.index += 1  # 1-based ranking
        df_lb.index.name = "Rank 🏅"
        st.dataframe(df_lb, use_container_width=True)
    else:
        st.info("No timeline data uploaded across accounts yet to generate rankings.")
    st.markdown("---")

render_extraction_guide(expanded_default=False)

# --- GPS PARSER, STAY-POINTS & TRANSPORT CLASSIFIER ---
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def parse_coord_str(pt_str):
    if not pt_str:
        return None
    try:
        parts = pt_str.replace('°', '').split(',')
        if len(parts) == 2:
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return [round(lat, 6), round(lon, 6)]
    except Exception:
        pass
    return None

def classify_transport(raw_type, dist_km, duration_hrs):
    raw_upper = str(raw_type).upper()
    speed_kmh = dist_km / duration_hrs if duration_hrs > 0.02 else 0.0

    if any(k in raw_upper for k in ['FLIGHT', 'FLYING', 'AIRPLANE']):
        return 'Flight ✈️'
    if any(k in raw_upper for k in ['TRAIN', 'SUBWAY', 'RAIL', 'TRAM']):
        return 'Train 🚆'
    if any(k in raw_upper for k in ['MOTORCYCLING', 'BOATING', 'DRIVING', 'IN_PASSENGER_VEHICLE', 'BUS', 'AUTOMOTIVE', 'CYCLING', 'BICYCLE']):
        if dist_km > 300 and speed_kmh > 135:
            return 'Flight ✈️'
        if dist_km > 120 and 58 <= speed_kmh <= 135 and duration_hrs >= 2.0:
            return 'Train 🚆'
        return 'Road / Bike 🏍️'
    if any(k in raw_upper for k in ['WALK', 'ON_FOOT', 'RUNNING', 'HIKING']):
        if speed_kmh <= 14:
            return 'Walk 🚶'

    if dist_km > 140 and speed_kmh > 130:
        return 'Flight ✈️'
    elif dist_km > 70 and 52 <= speed_kmh <= 130:
        return 'Train 🚆'
    elif speed_kmh < 10 and dist_km < 12:
        return 'Walk 🚶'
    else:
        return 'Road / Bike 🏍️'

MODE_META = {
    'Flight ✈️': {'color': '#c084fc', 'icon': '✈️'},
    'Train 🚆': {'color': '#38bdf8', 'icon': '🚆'},
    'Road / Bike 🏍️': {'color': '#fb923c', 'icon': '🏍️'},
    'Walk 🚶': {'color': '#4ade80', 'icon': '🚶'}
}

def generate_gpx_xml(df_subset, label_title="ChronoPath_Export"):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="ChronoPath Animator" xmlns="http://www.topografix.com/GPX/1/1">',
        f'  <metadata><name>{escape(label_title)}</name></metadata>'
    ]
    for _, row in df_subset.iterrows():
        trk_name = f"{row['date']} {row['start_str']} {row['mode']} ({row['dist_km']} km)"
        lines.append('  <trk>')
        lines.append(f'    <name>{escape(trk_name)}</name>')
        lines.append('    <trkseg>')
        for c in row['coords']:
            lines.append(f'      <trkpt lat="{c[0]}" lon="{c[1]}"></trkpt>')
        lines.append('    </trkseg>')
        lines.append('  </trk>')
    lines.append('</gpx>')
    return "\n".join(lines)

def load_and_verify_timeline(file_bytes, max_ground_jump_km=15.0):
    try:
        data = json.loads(file_bytes.decode('utf-8'))
    except Exception as e:
        return None, None, f"Invalid JSON file: {e}"

    segments = data.get('semanticSegments', [])
    parsed_trips = []
    parsed_stays = []

    def finalize_sub_segment(coords_list, times_list, raw_type, fallback_start, fallback_end):
        if len(coords_list) < 2:
            return

        t_start = pd.to_datetime(times_list[0] if times_list[0] else fallback_start, errors='coerce', utc=True)
        t_end = pd.to_datetime(times_list[-1] if times_list[-1] else fallback_end, errors='coerce', utc=True)
        if pd.isna(t_start):
            return
        if pd.isna(t_end) or t_end < t_start:
            t_end = t_start

        t_start_ist = t_start.tz_convert('Asia/Kolkata')
        t_end_ist = t_end.tz_convert('Asia/Kolkata')
        duration_hrs = max((t_end_ist - t_start_ist).total_seconds() / 3600.0, 0.01)

        total_dist_km = 0.0
        for i in range(1, len(coords_list)):
            total_dist_km += haversine_km(coords_list[i-1][0], coords_list[i-1][1], coords_list[i][0], coords_list[i][1])

        if total_dist_km < 0.05:
            return

        direct_dist_km = haversine_km(coords_list[0][0], coords_list[0][1], coords_list[-1][0], coords_list[-1][1])
        effective_dist = max(total_dist_km, direct_dist_km)
        avg_speed_kmh = effective_dist / duration_hrs

        if avg_speed_kmh > 950:
            return

        mode = classify_transport(raw_type, effective_dist, duration_hrs)

        pt_timestamps = []
        base_dt = t_start_ist
        step_sec = (duration_hrs * 3600.0) / max(len(coords_list) - 1, 1)
        for i in range(len(coords_list)):
            raw_t = pd.to_datetime(times_list[i], errors='coerce', utc=True) if i < len(times_list) else pd.NaT
            if not pd.isna(raw_t):
                pt_dt = raw_t.tz_convert('Asia/Kolkata')
            else:
                pt_dt = base_dt + pd.Timedelta(seconds=i * step_sec)
            pt_timestamps.append(pt_dt.strftime('%Y-%m-%d %H:%M'))

        parsed_trips.append({
            'date': t_start_ist.strftime('%Y-%m-%d'),
            'start_dt': t_start_ist,
            'end_dt': t_end_ist,
            'start_str': t_start_ist.strftime('%H:%M'),
            'end_str': t_end_ist.strftime('%H:%M'),
            'mode': mode,
            'raw_type': raw_type,
            'dist_km': round(effective_dist, 2),
            'duration_hrs': round(duration_hrs, 2),
            'speed_kmh': round(avg_speed_kmh, 1),
            'coords': coords_list,
            'pt_times': pt_timestamps
        })

    for seg in segments:
        seg_start_str = seg.get('startTime', '')
        seg_end_str = seg.get('endTime', '')

        if 'visit' in seg and seg['visit']:
            vis = seg['visit']
            top_cand = vis.get('topCandidate', {})
            loc_str = top_cand.get('placeLocation', {}).get('latLng', '')
            c_vis = parse_coord_str(loc_str)
            if c_vis:
                t_s = pd.to_datetime(seg_start_str, errors='coerce', utc=True)
                t_e = pd.to_datetime(seg_end_str, errors='coerce', utc=True)
                if not pd.isna(t_s) and not pd.isna(t_e):
                    t_s_ist = t_s.tz_convert('Asia/Kolkata')
                    t_e_ist = t_e.tz_convert('Asia/Kolkata')
                    dur_mins = (t_e_ist - t_s_ist).total_seconds() / 60.0
                    if dur_mins >= 30:
                        sem_type = top_cand.get('semanticType', 'Stopover').replace('TYPE_', '').title()
                        parsed_stays.append({
                            'date': t_s_ist.strftime('%Y-%m-%d'),
                            'start_str': t_s_ist.strftime('%H:%M'),
                            'end_str': t_e_ist.strftime('%H:%M'),
                            'dur_hrs': round(dur_mins / 60.0, 1),
                            'label': sem_type,
                            'coord': c_vis
                        })

        act = seg.get('activity', {})
        raw_type = act.get('topCandidate', {}).get('type', 'UNKNOWN') if act else 'UNKNOWN'
        is_explicit_flight = any(k in str(raw_type).upper() for k in ['FLIGHT', 'FLYING', 'AIRPLANE'])

        raw_coords = []
        raw_times = []

        if 'timelinePath' in seg and seg['timelinePath']:
            for pt in seg['timelinePath']:
                c = parse_coord_str(pt.get('point', ''))
                t = pt.get('time', seg_start_str)
                if c:
                    raw_coords.append(c)
                    raw_times.append(t)
        elif is_explicit_flight and act:
            s_c = parse_coord_str(act.get('start', {}).get('latLng', ''))
            e_c = parse_coord_str(act.get('end', {}).get('latLng', ''))
            if s_c and e_c:
                raw_coords = [s_c, e_c]
                raw_times = [seg_start_str, seg_end_str]

        if len(raw_coords) < 2:
            continue

        curr_coords = [raw_coords[0]]
        curr_times = [raw_times[0]]

        for i in range(1, len(raw_coords)):
            step_d = haversine_km(curr_coords[-1][0], curr_coords[-1][1], raw_coords[i][0], raw_coords[i][1])
            if step_d <= 0.015:
                continue

            if not is_explicit_flight and step_d > max_ground_jump_km:
                finalize_sub_segment(curr_coords, curr_times, raw_type, seg_start_str, seg_end_str)
                curr_coords = [raw_coords[i]]
                curr_times = [raw_times[i]]
            else:
                curr_coords.append(raw_coords[i])
                curr_times.append(raw_times[i])

        finalize_sub_segment(curr_coords, curr_times, raw_type, seg_start_str, seg_end_str)

    parsed_trips.sort(key=lambda x: x['start_dt'])
    return parsed_trips, parsed_stays, None

# --- SILENT BACKGROUND FILE SYNC ---
file_bytes = None
if os.path.exists(current_user_file):
    with open(current_user_file, "rb") as f:
        file_bytes = f.read()
else:
    uploaded_file = st.file_uploader(
        "📤 Upload your exported mobile Timeline.json file to visualize your routes:",
        type=['json']
    )
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        with open(current_user_file, "wb") as f:
            f.write(file_bytes)
        st.rerun()

trips = []
stays = []
if file_bytes:
    with st.spinner("Processing GPS coordinates, stay-points, and community rankings..."):
        trips, stays, err = load_and_verify_timeline(file_bytes)
    if err:
        st.error(err)

if trips:
    df_trips = pd.DataFrame(trips)
    df_stays = pd.DataFrame(stays) if stays else pd.DataFrame(columns=['date', 'start_str', 'end_str', 'dur_hrs', 'label', 'coord'])
    all_dates = sorted(df_trips['date'].unique())

    lifetime_km = df_trips['dist_km'].sum()
    update_user_audit(active_account, total_trips=len(df_trips), total_km=lifetime_km, active_days=len(all_dates))

    if 'date_idx' not in st.session_state or st.session_state.date_idx >= len(all_dates):
        st.session_state.date_idx = len(all_dates) - 1

    # --- 🏆 LIFETIME TRAVEL WRAPPED DASHBOARD ---
    with st.expander("🏆 Lifetime Travel Wrapped (All-Time Records & Breakdown)", expanded=False):
        earth_laps = lifetime_km / 40075.0
        longest_row = df_trips.loc[df_trips['dist_km'].idxmax()]
        fastest_ground_df = df_trips[df_trips['mode'] != 'Flight ✈️']
        fastest_row = fastest_ground_df.loc[fastest_ground_df['speed_kmh'].idxmax()] if not fastest_ground_df.empty else df_trips.loc[df_trips['speed_kmh'].idxmax()]

        mode_km = df_trips.groupby('mode')['dist_km'].sum().to_dict()
        road_pct = (mode_km.get('Road / Bike 🏍️', 0.0) / max(lifetime_km, 1)) * 100
        train_pct = (mode_km.get('Train 🚆', 0.0) / max(lifetime_km, 1)) * 100
        flight_pct = (mode_km.get('Flight ✈️', 0.0) / max(lifetime_km, 1)) * 100

        w1, w2, w3, w4 = st.columns(4)
        with w1:
            st.markdown(f"""
            <div class="wrapped-card">
                <div class="wrapped-lbl">🌍 Total Lifetime Distance</div>
                <div class="wrapped-val">{lifetime_km:,.1f} km</div>
                <div style="font-size:12.5px; color:#cbd5e1;">Equals <b>{earth_laps:.2f}x</b> around the Earth across <b>{len(all_dates)}</b> active travel days</div>
            </div>
            """, unsafe_allow_html=True)
        with w2:
            st.markdown(f"""
            <div class="wrapped-card">
                <div class="wrapped-lbl">📊 Mode Share Breakdown</div>
                <div class="wrapped-val" style="color:#fb923c;">{road_pct:.1f}% Road/Bike</div>
                <div style="font-size:12.5px; color:#cbd5e1;">🚆 Train: <b>{train_pct:.1f}%</b> &nbsp;|&nbsp; ✈️ Flight: <b>{flight_pct:.1f}%</b></div>
            </div>
            """, unsafe_allow_html=True)
        with w3:
            st.markdown(f"""
            <div class="wrapped-card">
                <div class="wrapped-lbl">🛣️ Longest Single Segment</div>
                <div class="wrapped-val" style="color:#4ade80;">{longest_row['dist_km']:,.1f} km</div>
                <div style="font-size:12.5px; color:#cbd5e1;">{longest_row['mode']} on <b>{longest_row['date']}</b> ({longest_row['duration_hrs']} hrs)</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🎯 Jump to {longest_row['date']}", key="jmp_longest", use_container_width=True):
                st.session_state.date_idx = all_dates.index(longest_row['date'])
                st.session_state.date_stepper_select = longest_row['date']
                st.rerun()
        with w4:
            st.markdown(f"""
            <div class="wrapped-card">
                <div class="wrapped-lbl">⚡ Peak Ground Speed Record</div>
                <div class="wrapped-val" style="color:#c084fc;">{fastest_row['speed_kmh']:.1f} km/h</div>
                <div style="font-size:12.5px; color:#cbd5e1;">{fastest_row['mode']} on <b>{fastest_row['date']}</b> ({fastest_row['dist_km']} km)</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"⚡ Jump to {fastest_row['date']}", key="jmp_fastest", use_container_width=True):
                st.session_state.date_idx = all_dates.index(fastest_row['date'])
                st.session_state.date_stepper_select = fastest_row['date']
                st.rerun()

    daily_summary = df_trips.groupby('date').agg(
        total_km=('dist_km', 'sum'),
        modes=('mode', lambda s: ', '.join(sorted(set(s))))
    ).reset_index()
    major_days_df = daily_summary[
        (daily_summary['total_km'] >= 80) |
        (daily_summary['modes'].str.contains('Flight|Train'))
    ].sort_values('date', ascending=False)
    major_day_options = [
        f"{r['date']} ({r['total_km']:.0f} km — {r['modes']})"
        for _, r in major_days_df.iterrows()
    ]

    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        view_scope = st.radio(
            '🔍 Select View Mode:',
            ['📅 Day-by-Day Stepper', '🚀 Major Trips (Flights/Trains/Highway)', '📆 Custom Date Range (Multi-Day Trip)'],
            horizontal=False,
            key='view_scope_radio'
        )
    with col2:
        selected_modes = st.multiselect(
            '🚦 Filter Transport Modes:',
            options=['Flight ✈️', 'Train 🚆', 'Road / Bike 🏍️', 'Walk 🚶'],
            default=['Flight ✈️', 'Train 🚆', 'Road / Bike 🏍️', 'Walk 🚶'],
            key='modes_multiselect'
        )
        map_style = st.selectbox(
            '🗺️ Map Tile Layer:',
            ['Google Roads (Crisp)', 'Google Satellite Hybrid', 'Night Roads (Dark Mode)'],
            key='map_style_select'
        )

    def prev_day_callback():
        if st.session_state.date_idx > 0:
            st.session_state.date_idx -= 1
            st.session_state.date_stepper_select = all_dates[st.session_state.date_idx]

    def next_day_callback():
        if st.session_state.date_idx < len(all_dates) - 1:
            st.session_state.date_idx += 1
            st.session_state.date_stepper_select = all_dates[st.session_state.date_idx]

    def dropdown_day_callback():
        chosen = st.session_state.date_stepper_select
        if chosen in all_dates:
            st.session_state.date_idx = all_dates.index(chosen)

    export_label = "ChronoPath_Route"
    with col3:
        if view_scope == '📅 Day-by-Day Stepper':
            b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
            with b_col1:
                st.button('⬅️ Prev Day', key='prev_day_btn', on_click=prev_day_callback, use_container_width=True)
            with b_col3:
                st.button('Next Day ➡️', key='next_day_btn', on_click=next_day_callback, use_container_width=True)
            with b_col2:
                st.selectbox(
                    'Jump to Date:',
                    all_dates,
                    index=st.session_state.date_idx,
                    label_visibility='collapsed',
                    key='date_stepper_select',
                    on_change=dropdown_day_callback
                )

            cur_date_str = all_dates[st.session_state.date_idx]
            export_label = f"ChronoPath_{cur_date_str}"
            active_df = df_trips[
                (df_trips['date'] == cur_date_str) &
                (df_trips['mode'].isin(selected_modes))
            ]
            active_stays_df = df_stays[df_stays['date'] == cur_date_str] if not df_stays.empty else pd.DataFrame()
        elif view_scope == '🚀 Major Trips (Flights/Trains/Highway)':
            if major_day_options:
                chosen_major = st.selectbox('Select a Long-Distance Travel Day:', major_day_options, key='major_trip_select')
                major_date = chosen_major.split(' ')[0]
                export_label = f"ChronoPath_Major_{major_date}"
                active_df = df_trips[
                    (df_trips['date'] == major_date) &
                    (df_trips['mode'].isin(selected_modes))
                ]
                active_stays_df = df_stays[df_stays['date'] == major_date] if not df_stays.empty else pd.DataFrame()
            else:
                st.info('No trips > 80 km found.')
                active_df = df_trips[df_trips['date'] == all_dates[-1]]
                active_stays_df = pd.DataFrame()
        else:
            min_d = datetime.strptime(all_dates[0], '%Y-%m-%d').date()
            max_d = datetime.strptime(all_dates[-1], '%Y-%m-%d').date()
            default_start = max(min_d, max_d - timedelta(days=7))
            c_start, c_end = st.columns(2)
            with c_start:
                start_d = st.date_input('Start Date:', value=default_start, min_value=min_d, max_value=max_d, key='start_d_picker')
            with c_end:
                end_d = st.date_input('End Date:', value=max_d, min_value=min_d, max_value=max_d, key='end_d_picker')
            s_d, e_d = start_d.strftime('%Y-%m-%d'), end_d.strftime('%Y-%m-%d')
            export_label = f"ChronoPath_{s_d}_to_{e_d}"
            active_df = df_trips[
                (df_trips['date'] >= s_d) &
                (df_trips['date'] <= e_d) &
                (df_trips['mode'].isin(selected_modes))
            ]
            active_stays_df = df_stays[(df_stays['date'] >= s_d) & (df_stays['date'] <= e_d)] if not df_stays.empty else pd.DataFrame()

    if not active_df.empty:
        total_km = active_df['dist_km'].sum()
        total_hrs = active_df['duration_hrs'].sum()
        mode_counts = active_df['mode'].value_counts().to_dict()
        mode_summary = " | ".join([f"{k}: {v} segs" for k, v in mode_counts.items()])
        num_stays = len(active_stays_df) if not active_stays_df.empty else 0

        sum_col, gpx_col = st.columns([4, 1])
        with sum_col:
            st.info(f"**Total Distance:** {total_km:,.1f} km  •  **Moving Time:** {total_hrs:,.1f} hrs  •  **Stopovers (≥30m):** {num_stays} pins  •  **Segments:** {mode_summary}")
        with gpx_col:
            gpx_data = generate_gpx_xml(active_df, label_title=export_label)
            st.download_button(
                label="📥 Export Route (.gpx)",
                data=gpx_data,
                file_name=f"{export_label}.gpx",
                mime="application/gpx+xml",
                use_container_width=True
            )

        js_segments = []
        render_records = active_df.to_dict('records')
        for idx, r in enumerate(render_records):
            meta = MODE_META.get(r['mode'], MODE_META['Road / Bike 🏍️'])
            js_segments.append({
                'id': idx + 1,
                'date': r['date'],
                'start_str': r['start_str'],
                'end_str': r['end_str'],
                'mode': r['mode'],
                'color': meta['color'],
                'icon': meta['icon'],
                'dist_km': r['dist_km'],
                'duration_hrs': r['duration_hrs'],
                'speed_kmh': r['speed_kmh'],
                'coords': r['coords'],
                'pt_times': r['pt_times']
            })

        js_stays = active_stays_df.to_dict('records') if not active_stays_df.empty else []

        dark_css = ""
        if map_style == 'Google Roads (Crisp)':
            tile_url = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
        elif map_style == 'Google Satellite Hybrid':
            tile_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
        else:
            tile_url = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
            dark_css = ".leaflet-tile-pane { filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%); }"

        segments_json = json.dumps(js_segments)
        stays_json = json.dumps(js_stays)

        custom_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
            <style>
                body {{ margin: 0; padding: 0; background: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #f8fafc; }}
                #control-bar {{
                    display: flex; align-items: center; gap: 12px; padding: 10px 16px;
                    background: #1e293b; border-bottom: 1px solid #334155; border-radius: 8px 8px 0 0;
                    flex-wrap: wrap;
                }}
                .btn {{
                    background: #3b82f6; color: white; border: none; padding: 8px 14px;
                    border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px;
                }}
                .btn:hover {{ background: #2563eb; }}
                .btn-secondary {{ background: #475569; }}
                .btn-secondary:hover {{ background: #334155; }}
                #scrubber {{ flex: 1; min-width: 140px; cursor: pointer; accent-color: #3b82f6; }}
                #hud {{
                    display: flex; gap: 14px; align-items: center; font-size: 13px;
                    background: #0f172a; padding: 6px 12px; border-radius: 6px; border: 1px solid #334155;
                }}
                .badge {{ padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; color: #0f172a; }}
                #map {{ width: 100%; height: 600px; border-radius: 0 0 8px 8px; }}
                {dark_css}
                .vehicle-marker {{
                    font-size: 22px; text-align: center; line-height: 28px;
                    background: rgba(15, 23, 42, 0.9); border: 2px solid white;
                    border-radius: 50%; width: 32px !important; height: 32px !important;
                    box-shadow: 0 0 10px rgba(0,0,0,0.6);
                }}
                .stay-pin {{
                    font-size: 15px; text-align: center; line-height: 22px;
                    background: #ef4444; color: white; border: 2px solid white;
                    border-radius: 50%; width: 24px !important; height: 24px !important;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
                }}
                .legend-box {{
                    display: flex; gap: 14px; font-size: 12px; padding: 6px 16px;
                    background: #0f172a; border-bottom: 1px solid #334155; align-items: center; flex-wrap: wrap;
                }}
                .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }}
            </style>
        </head>
        <body>
            <div id="control-bar">
                <button id="play-btn" class="btn" onclick="togglePlay()">⏸️ Pause</button>
                <button class="btn btn-secondary" onclick="restartAnim()">⏮️ Clear & Redraw</button>
                <input type="range" id="scrubber" min="0" value="0" step="1" oninput="onScrub(this.value)" />
                <label style="font-size:13px;">Speed:
                    <select id="speed-select" onchange="changeSpeed(this.value)" style="background:#0f172a;color:white;border:1px solid #475569;padding:4px 8px;border-radius:4px;">
                        <option value="120">1x (Detailed)</option>
                        <option value="50" selected>3x (Smooth)</option>
                        <option value="20">10x (Fast)</option>
                        <option value="5">30x (Ultra Fast)</option>
                    </select>
                </label>
                <label style="font-size:13px; cursor:pointer;">
                    <input type="checkbox" id="follow-cam" /> Follow Icon
                </label>
                <label style="font-size:13px; cursor:pointer;">
                    <input type="checkbox" id="toggle-stays" checked onchange="toggleStayMarkers(this.checked)" /> 📍 Stopovers
                </label>
                <label style="font-size:13px; cursor:pointer;">
                    <input type="checkbox" id="toggle-heat" onchange="toggleHeatmap(this.checked)" /> 🔥 Heatmap
                </label>
                <div id="hud">
                    <span id="hud-time">🕒 --</span>
                    <span id="hud-mode" class="badge" style="background:#fb923c;">--</span>
                    <span id="hud-stats">0.0 km | 0 km/h</span>
                </div>
            </div>
            <div class="legend-box">
                <span><b>Legend:</b></span>
                <span><span class="dot" style="background:#c084fc;"></span>Flight ✈️</span>
                <span><span class="dot" style="background:#38bdf8;"></span>Train 🚆</span>
                <span><span class="dot" style="background:#fb923c;"></span>Road / Bike 🏍️</span>
                <span><span class="dot" style="background:#4ade80;"></span>Walk 🚶</span>
                <span><span class="dot" style="background:#ef4444;"></span>Stopover Pin (≥30 mins) 📍</span>
            </div>
            <div id="map"></div>

            <script>
                const segments = {segments_json};
                const stays = {stays_json};
                const map = L.map('map', {{ preferCanvas: true }});
                L.tileLayer('{tile_url}', {{ maxZoom: 19, attribution: 'Map Data' }}).addTo(map);

                const flatSteps = [];
                const allBounds = [];
                const heatPoints = [];

                segments.forEach((seg, sIdx) => {{
                    seg.coords.forEach((c, cIdx) => {{
                        allBounds.push(c);
                        heatPoints.push([c[0], c[1], 0.65]);
                        flatSteps.push({{
                            sIdx: sIdx,
                            cIdx: cIdx,
                            coord: c,
                            time: seg.pt_times[cIdx] || (seg.date + ' ' + seg.start_str),
                            seg: seg
                        }});
                    }});
                }});

                const stayLayerGroup = L.layerGroup().addTo(map);
                const stayIcon = L.divIcon({{
                    className: 'stay-pin',
                    html: '📍',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                }});

                stays.forEach(st => {{
                    allBounds.push(st.coord);
                    heatPoints.push([st.coord[0], st.coord[1], 1.0]);
                    const m = L.marker(st.coord, {{ icon: stayIcon }});
                    m.bindTooltip(
                        `<b>📍 ${{st.label}} Stopover</b><br>Date: ${{st.date}}<br>Time: ${{st.start_str}} → ${{st.end_str}} (${{st.dur_hrs}} hrs)`,
                        {{ sticky: true }}
                    );
                    m.addTo(stayLayerGroup);
                }});

                const heatLayer = L.heatLayer(heatPoints, {{
                    radius: 20,
                    blur: 16,
                    maxZoom: 16
                }});

                function toggleStayMarkers(show) {{
                    if (show) map.addLayer(stayLayerGroup);
                    else map.removeLayer(stayLayerGroup);
                }}

                function toggleHeatmap(show) {{
                    if (show) map.addLayer(heatLayer);
                    else map.removeLayer(heatLayer);
                }}

                if (allBounds.length > 0) {{
                    map.fitBounds(allBounds, {{ padding: [35, 35] }});
                }} else {{
                    map.setView([12.9716, 77.5946], 13);
                }}

                const polylines = segments.map(seg => {{
                    const poly = L.polyline([], {{
                        color: seg.color,
                        weight: 4,
                        opacity: 0.95,
                        lineCap: 'round',
                        lineJoin: 'round'
                    }}).addTo(map);
                    poly.bindTooltip(
                        `<b>#${{seg.id}} ${{seg.mode}}</b><br>Date: ${{seg.date}}<br>Time: ${{seg.start_str}} → ${{seg.end_str}} (${{seg.duration_hrs}} hrs)<br>Distance: ${{seg.dist_km}} km | Avg Speed: ${{seg.speed_kmh}} km/h`,
                        {{ sticky: true }}
                    );
                    return poly;
                }});

                const vehicleIcon = L.divIcon({{
                    className: 'vehicle-marker',
                    html: '<div id="v-emoji">🏍️</div>',
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                }});
                const liveMarker = L.marker(allBounds[0] || [12.9716, 77.5946], {{ icon: vehicleIcon }}).addTo(map);

                const scrubber = document.getElementById('scrubber');
                scrubber.max = Math.max(flatSteps.length - 1, 0);

                let currentStep = 0;
                let isPlaying = true;
                let intervalMs = 50;
                let timer = null;

                function renderUpToStep(targetStep) {{
                    polylines.forEach(p => p.setLatLngs([]));

                    const segCoordBuckets = segments.map(() => []);
                    for (let i = 0; i <= targetStep && i < flatSteps.length; i++) {{
                        const st = flatSteps[i];
                        segCoordBuckets[st.sIdx].push(st.coord);
                    }}

                    segCoordBuckets.forEach((coordsList, idx) => {{
                        if (coordsList.length > 1) {{
                            polylines[idx].setLatLngs(coordsList);
                        }}
                    }});

                    if (flatSteps[targetStep]) {{
                        const cur = flatSteps[targetStep];
                        liveMarker.setLatLng(cur.coord);
                        const emojiEl = document.getElementById('v-emoji');
                        if (emojiEl) emojiEl.innerText = cur.seg.icon;

                        document.getElementById('hud-time').innerText = '🕒 ' + cur.time;
                        const modeEl = document.getElementById('hud-mode');
                        modeEl.innerText = cur.seg.mode;
                        modeEl.style.background = cur.seg.color;
                        document.getElementById('hud-stats').innerText =
                            `${{cur.seg.dist_km}} km (${{cur.seg.duration_hrs}} hrs) @ ${{cur.seg.speed_kmh}} km/h`;

                        if (document.getElementById('follow-cam').checked) {{
                            map.panTo(cur.coord, {{ animate: true, duration: 0.2 }});
                        }}
                    }}
                }}

                function tick() {{
                    if (!isPlaying) return;
                    if (currentStep < flatSteps.length - 1) {{
                        currentStep++;
                        scrubber.value = currentStep;
                        renderUpToStep(currentStep);
                    }} else {{
                        isPlaying = false;
                        document.getElementById('play-btn').innerText = '▶️ Replay';
                        clearInterval(timer);
                    }}
                }}

                function startLoop() {{
                    if (timer) clearInterval(timer);
                    timer = setInterval(tick, intervalMs);
                }}

                function togglePlay() {{
                    if (currentStep >= flatSteps.length - 1) {{
                        currentStep = 0;
                    }}
                    isPlaying = !isPlaying;
                    document.getElementById('play-btn').innerText = isPlaying ? '⏸️ Pause' : '▶️ Play';
                    if (isPlaying) startLoop();
                    else clearInterval(timer);
                }}

                function restartAnim() {{
                    currentStep = 0;
                    scrubber.value = 0;
                    renderUpToStep(0);
                    isPlaying = true;
                    document.getElementById('play-btn').innerText = '⏸️ Pause';
                    startLoop();
                }}

                function onScrub(val) {{
                    currentStep = parseInt(val);
                    renderUpToStep(currentStep);
                }}

                function changeSpeed(ms) {{
                    intervalMs = parseInt(ms);
                    if (isPlaying) startLoop();
                }}

                renderUpToStep(0);
                startLoop();
            </script>
        </body>
        </html>
        """

        components.html(custom_html, height=700)

        with st.expander('📊 View Exact Timestamp, Distance & Transport Estimation Log', expanded=True):
            log_df = active_df[['date', 'start_str', 'end_str', 'mode', 'dist_km', 'duration_hrs', 'speed_kmh', 'raw_type']].copy()
            log_df.columns = ['Date', 'Start (IST)', 'End (IST)', 'Estimated Transport', 'Distance (km)', 'Duration (hrs)', 'Avg Speed (km/h)', 'Google Tag']
            st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        st.warning('No travel segments match the selected date and transport filters.')
