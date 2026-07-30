import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(page_title="NebulaChat", page_icon="💬", layout="wide")

DATA_FILE = "nebulachat_data.json"
REFRESH_INTERVAL = 3  # seconds, for auto-refresh polling

THEMES = {
    "Default": {"primary": "#7B61FF", "secondary": "#00D9FF", "bg1": "#0A0E27", "bg2": "#1A1E3F"},
    "Cyberpunk": {"primary": "#FF2E63", "secondary": "#00FFF5", "bg1": "#0D0221", "bg2": "#241734"},
    "Sunset": {"primary": "#FF8C42", "secondary": "#FF3C78", "bg1": "#1A0B2E", "bg2": "#2E1052"},
    "Ocean": {"primary": "#00B4D8", "secondary": "#48CAE4", "bg1": "#03071E", "bg2": "#0A1128"},
    "Midnight": {"primary": "#9D4EDD", "secondary": "#5A189A", "bg1": "#000000", "bg2": "#10002B"},
}

# ---------------------------------------------------------------------------
# DATA LAYER
# ---------------------------------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"rooms": {"General": []}, "users": {}}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ---------------------------------------------------------------------------
# SESSION / IDENTITY
# ---------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]
if "username" not in st.session_state:
    st.session_state.username = None
if "current_room" not in st.session_state:
    st.session_state.current_room = "General"
if "theme" not in st.session_state:
    st.session_state.theme = "Default"
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

theme = THEMES[st.session_state.theme]

# ---------------------------------------------------------------------------
# STYLING
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Outfit', sans-serif;
}}

.stApp {{
    background: radial-gradient(ellipse at top, {theme['bg2']} 0%, {theme['bg1']} 60%);
    background-attachment: fixed;
}}

.stApp::before {{
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image:
        radial-gradient(2px 2px at 20px 30px, white, transparent),
        radial-gradient(2px 2px at 60px 70px, white, transparent),
        radial-gradient(1px 1px at 90px 40px, white, transparent),
        radial-gradient(1px 1px at 130px 80px, white, transparent),
        radial-gradient(2px 2px at 160px 20px, white, transparent);
    background-repeat: repeat;
    background-size: 200px 200px;
    opacity: 0.15;
    pointer-events: none;
    z-index: 0;
}}

.glass-card {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    margin-bottom: 0.8rem;
}}

.chat-title {{
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, {theme['primary']}, {theme['secondary']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}}

.chat-sub {{
    color: rgba(255,255,255,0.5);
    font-size: 0.95rem;
    margin-top: -8px;
}}

.msg-bubble-mine {{
    background: linear-gradient(135deg, {theme['primary']}33, {theme['secondary']}22);
    border: 1px solid {theme['primary']}55;
    border-radius: 16px 16px 4px 16px;
    padding: 0.7rem 1rem;
    margin: 6px 0;
    margin-left: 20%;
    color: white;
}}

.msg-bubble-other {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px 16px 16px 4px;
    padding: 0.7rem 1rem;
    margin: 6px 0;
    margin-right: 20%;
    color: white;
}}

.msg-meta {{
    font-size: 0.72rem;
    color: rgba(255,255,255,0.4);
    margin-bottom: 2px;
}}

.room-pill {{
    display: inline-block;
    padding: 4px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    color: white;
    font-size: 0.85rem;
    margin-right: 6px;
}}

.online-dot {{
    height: 8px; width: 8px;
    background-color: {theme['secondary']};
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
    box-shadow: 0 0 8px {theme['secondary']};
}}

section[data-testid="stSidebar"] {{
    background: rgba(10, 14, 39, 0.6);
    backdrop-filter: blur(10px);
}}

::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-thumb {{ background: {theme['primary']}66; border-radius: 4px; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# USERNAME GATE
# ---------------------------------------------------------------------------
if not st.session_state.username:
    st.markdown('<p class="chat-title">💬 NebulaChat</p>', unsafe_allow_html=True)
    st.markdown('<p class="chat-sub">A multi-user messaging demo across the App Universe</p>', unsafe_allow_html=True)
    st.write("")
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        name = st.text_input("Pick a display name to join the chat", max_chars=20)
        if st.button("🚀 Enter NebulaChat", use_container_width=True):
            if name.strip():
                st.session_state.username = name.strip()
                data["users"][st.session_state.user_id] = {
                    "name": name.strip(),
                    "joined": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                }
                save_data(data)
                st.rerun()
            else:
                st.warning("Enter a name first.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f'<p class="chat-title" style="font-size:1.5rem;">💬 NebulaChat</p>', unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.username}** <span class='online-dot'></span>", unsafe_allow_html=True)
    st.caption(f"user id: {st.session_state.user_id}")
    st.divider()

    st.session_state.theme = st.selectbox("Theme", list(THEMES.keys()),
                                           index=list(THEMES.keys()).index(st.session_state.theme))

    st.divider()
    st.subheader("Rooms")
    room_names = list(data["rooms"].keys())
    for r in room_names:
        count = len(data["rooms"][r])
        label = f"# {r}  ({count})"
        if st.button(label, key=f"room_{r}", use_container_width=True):
            st.session_state.current_room = r
            st.rerun()

    with st.expander("➕ New room"):
        new_room = st.text_input("Room name", key="new_room_input")
        if st.button("Create room"):
            if new_room.strip() and new_room.strip() not in data["rooms"]:
                data["rooms"][new_room.strip()] = []
                save_data(data)
                st.session_state.current_room = new_room.strip()
                st.rerun()
            elif new_room.strip() in data["rooms"]:
                st.warning("Room already exists.")

    st.divider()
    st.subheader("Who's around")
    now = datetime.now()
    for uid, u in data.get("users", {}).items():
        try:
            last_seen = datetime.fromisoformat(u["last_seen"])
            active = (now - last_seen).total_seconds() < 30
        except Exception:
            active = False
        dot = "🟢" if active else "⚪"
        st.caption(f"{dot} {u['name']}")

    st.divider()
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    if st.button("🚪 Leave chat"):
        st.session_state.username = None
        st.rerun()

# ---------------------------------------------------------------------------
# UPDATE LAST SEEN
# ---------------------------------------------------------------------------
if st.session_state.user_id in data["users"]:
    data["users"][st.session_state.user_id]["last_seen"] = datetime.now().isoformat()
    save_data(data)

# ---------------------------------------------------------------------------
# MAIN CHAT AREA
# ---------------------------------------------------------------------------
room = st.session_state.current_room
if room not in data["rooms"]:
    room = "General"
    st.session_state.current_room = room

st.markdown(f'<p class="chat-title"># {room}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="chat-sub">{len(data["rooms"][room])} messages</p>', unsafe_allow_html=True)

chat_container = st.container(height=460)
with chat_container:
    for msg in data["rooms"][room]:
        is_mine = msg["user_id"] == st.session_state.user_id
        bubble_class = "msg-bubble-mine" if is_mine else "msg-bubble-other"
        ts = msg.get("time", "")
        try:
            ts_display = datetime.fromisoformat(ts).strftime("%H:%M")
        except Exception:
            ts_display = ""
        st.markdown(f"""
        <div class="{bubble_class}">
            <div class="msg-meta">{msg['name']} · {ts_display}</div>
            {msg['text']}
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# MESSAGE INPUT
# ---------------------------------------------------------------------------
with st.form("send_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        text = st.text_input("Message", label_visibility="collapsed", placeholder=f"Message #{room}...")
    with col2:
        submitted = st.form_submit_button("Send 🚀", use_container_width=True)

    if submitted and text.strip():
        data["rooms"][room].append({
            "user_id": st.session_state.user_id,
            "name": st.session_state.username,
            "text": text.strip(),
            "time": datetime.now().isoformat(),
        })
        # keep last 500 messages per room
        data["rooms"][room] = data["rooms"][room][-500:]
        save_data(data)
        st.rerun()

# ---------------------------------------------------------------------------
# AUTO-REFRESH (polling, simulates live multi-user updates)
# ---------------------------------------------------------------------------
if auto_refresh:
    time.sleep(REFRESH_INTERVAL)
    st.session_state.data = load_data()
    st.rerun()
