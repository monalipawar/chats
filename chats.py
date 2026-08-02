import streamlit as st
import json
import os
import uuid
import hashlib
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(page_title="NebulaChat", page_icon="💬", layout="wide")

DATA_FILE = "nebulachat_data.json"
REFRESH_INTERVAL = 3  # seconds

THEMES = {
    "Default": {"primary": "#7B61FF", "secondary": "#00D9FF", "bg1": "#0A0E27", "bg2": "#1A1E3F"},
    "Cyberpunk": {"primary": "#FF2E63", "secondary": "#00FFF5", "bg1": "#0D0221", "bg2": "#241734"},
    "Sunset": {"primary": "#FF8C42", "secondary": "#FF3C78", "bg1": "#1A0B2E", "bg2": "#2E1052"},
    "Ocean": {"primary": "#00B4D8", "secondary": "#48CAE4", "bg1": "#03071E", "bg2": "#0A1128"},
    "Midnight": {"primary": "#9D4EDD", "secondary": "#5A189A", "bg1": "#000000", "bg2": "#10002B"},
}

AVATAR_PALETTE = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#7B61FF", "#00D9FF",
                   "#FF8C42", "#9D4EDD", "#48CAE4", "#FF2E63", "#06D6A0"]


def avatar_color(name):
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    return AVATAR_PALETTE[h % len(AVATAR_PALETTE)]


def initials(name):
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def relative_time(iso_str):
    try:
        t = datetime.fromisoformat(iso_str)
    except Exception:
        return ""
    diff = (datetime.now() - t).total_seconds()
    if diff < 60:
        return "just now"
    if diff < 3600:
        return f"{int(diff // 60)}m ago"
    if diff < 86400:
        return f"{int(diff // 3600)}h ago"
    return t.strftime("%b %d, %H:%M")

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
    qp_uid = st.query_params.get("uid")
    st.session_state.user_id = qp_uid if qp_uid else str(uuid.uuid4())[:8]
if "username" not in st.session_state:
    qp_name = st.query_params.get("name")
    if qp_name and qp_name.strip():
        st.session_state.username = qp_name.strip()
        # make sure this returning user is registered in the users table
        data["users"].setdefault(st.session_state.user_id, {
            "name": qp_name.strip(),
            "joined": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
        })
        save_data(data)
    else:
        st.session_state.username = None
if "current_room" not in st.session_state:
    st.session_state.current_room = "General"
if "theme" not in st.session_state:
    st.session_state.theme = "Default"
if "last_read" not in st.session_state:
    st.session_state.last_read = {}
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

theme = THEMES[st.session_state.theme]

# ---------------------------------------------------------------------------
# STYLING
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {{ font-family: 'Outfit', sans-serif; }}

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
    display: inline-block;
}}

.chat-sub {{ color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: -8px; }}

.msg-row {{ display: flex; align-items: flex-start; gap: 10px; margin: 14px 0; }}
.msg-row.mine {{ flex-direction: row-reverse; }}

.avatar {{
    width: 38px; height: 38px; min-width: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700; color: #0A0E27;
    box-shadow: 0 0 10px rgba(0,0,0,0.3);
    margin-top: 2px;
}}

.msg-bubble-mine {{
    background: linear-gradient(135deg, {theme['primary']}44, {theme['secondary']}22);
    border: 1px solid {theme['primary']}66;
    border-radius: 16px 16px 4px 16px;
    padding: 0.75rem 1.1rem;
    color: white;
    line-height: 1.5;
    max-width: 70%;
}}

.msg-bubble-other {{
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px 16px 16px 4px;
    padding: 0.75rem 1.1rem;
    color: white;
    line-height: 1.5;
    max-width: 70%;
}}

.msg-meta {{ font-size: 0.72rem; color: rgba(255,255,255,0.4); margin-bottom: 5px; }}
.msg-meta.mine {{ text-align: right; }}

.room-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 3px 10px; border-radius: 999px;
    background: {theme['primary']}33; color: {theme['secondary']};
    font-size: 0.72rem; font-weight: 600;
}}

.online-dot {{
    height: 8px; width: 8px;
    background-color: {theme['secondary']};
    border-radius: 50%; display: inline-block;
    box-shadow: 0 0 8px {theme['secondary']};
}}

.unread-badge {{
    background: {theme['primary']};
    color: white; font-size: 0.65rem; font-weight: 700;
    border-radius: 999px; padding: 1px 7px; margin-left: 6px;
}}

section[data-testid="stSidebar"] {{ background: rgba(10, 14, 39, 0.6); backdrop-filter: blur(10px); }}
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-thumb {{ background: {theme['primary']}66; border-radius: 4px; }}

div.st-key-chat_scroll {{ padding: 8px 14px; }}

div.st-key-info_btn_wrap button {{
    border-radius: 50% !important;
    width: 42px; height: 42px;
    font-weight: 700;
}}
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
                st.query_params["uid"] = st.session_state.user_id
                st.query_params["name"] = name.strip()
                st.rerun()
            else:
                st.warning("Enter a name first.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# RECENT ACTIVITY DIALOG (the "i" button)
# ---------------------------------------------------------------------------
@st.dialog("🕐 Recent Activity", width="large")
def show_recent_activity():
    live_data = load_data()
    all_msgs = []
    for room_name, msgs in live_data["rooms"].items():
        for m in msgs:
            all_msgs.append({**m, "room": room_name})
    all_msgs.sort(key=lambda m: m.get("time", ""), reverse=True)

    if not all_msgs:
        st.info("No messages anywhere yet — be the first to say something!")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Messages", len(all_msgs))
    c2.metric("Rooms", len(live_data["rooms"]))
    c3.metric("Users seen", len(live_data["users"]))

    st.divider()
    st.caption("Most recent across all rooms")

    for m in all_msgs[:25]:
        color = avatar_color(m["name"])
        st.markdown(
            f'<div style="display:flex; gap:10px; align-items:flex-start; margin-bottom:10px;">'
            f'<div class="avatar" style="background:{color};">{initials(m["name"])}</div>'
            f'<div><div class="msg-meta">'
            f'<b style="color:white;">{m["name"]}</b> '
            f'<span class="room-badge">#{m["room"]}</span> '
            f'· {relative_time(m.get("time",""))}'
            f'</div>'
            f'<div style="color: rgba(255,255,255,0.85);">{m["text"]}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    if st.button("Close", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f'<p class="chat-title" style="font-size:1.5rem;">💬 NebulaChat</p>', unsafe_allow_html=True)
    my_color = avatar_color(st.session_state.username)
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
        f'<div class="avatar" style="background:{my_color};">{initials(st.session_state.username)}</div>'
        f'<div><b>{st.session_state.username}</b><br>'
        f'<span class="online-dot"></span> '
        f'<span style="font-size:0.75rem; color:rgba(255,255,255,0.5);">online</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.session_state.theme = st.selectbox("Theme", list(THEMES.keys()),
                                           index=list(THEMES.keys()).index(st.session_state.theme))

    st.divider()
    st.subheader("Rooms")
    room_names = list(data["rooms"].keys())
    for r in room_names:
        msgs = data["rooms"][r]
        seen = st.session_state.last_read.get(r, 0)
        unread = max(0, len(msgs) - seen)
        active = (r == st.session_state.current_room)
        label = f"{'▶ ' if active else ''}# {r}"
        col_a, col_b = st.columns([4, 1])
        with col_a:
            if st.button(label, key=f"room_{r}", use_container_width=True):
                st.session_state.current_room = r
                st.session_state.last_read[r] = len(msgs)
                st.rerun()
        with col_b:
            if unread > 0 and not active:
                st.markdown(f'<span class="unread-badge">{unread}</span>', unsafe_allow_html=True)

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
        st.query_params.clear()
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
st.session_state.last_read[room] = len(data["rooms"][room])

header_l, header_r = st.columns([6, 1])
with header_l:
    st.markdown(f'<p class="chat-title"># {room}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="chat-sub">{len(data["rooms"][room])} messages</p>', unsafe_allow_html=True)
with header_r:
    with st.container(key="info_btn_wrap"):
        if st.button("ℹ️", help="See recent activity across all rooms", key="info_btn"):
            show_recent_activity()

st.session_state.search_query = st.text_input(
    "Search", placeholder="🔍 Search messages in this room...", label_visibility="collapsed",
    value=st.session_state.search_query
)


@st.fragment(run_every=REFRESH_INTERVAL if auto_refresh else None)
def render_chat():
    live_data = load_data()
    msgs = live_data["rooms"].get(room, [])
    query = st.session_state.search_query.strip().lower()
    if query:
        msgs = [m for m in msgs if query in m["text"].lower()]

    with st.container(height=480, key="chat_scroll"):
        if not msgs:
            st.caption("No messages match yet." if query else "No messages yet — say hello 👋")
        last_sender = None
        for msg in msgs:
            is_mine = msg["user_id"] == st.session_state.user_id
            row_class = "msg-row mine" if is_mine else "msg-row"
            bubble_class = "msg-bubble-mine" if is_mine else "msg-bubble-other"
            meta_class = "msg-meta mine" if is_mine else "msg-meta"
            color = avatar_color(msg["name"])
            show_meta = (msg["name"] != last_sender)
            last_sender = msg["name"]

            meta_html = (
                f'<div class="{meta_class}"><b style="color:white;">{msg["name"]}</b> · '
                f'{relative_time(msg.get("time",""))}</div>'
            ) if show_meta else ""

            st.markdown(
                f'<div class="{row_class}">'
                f'<div class="avatar" style="background:{color};">{initials(msg["name"])}</div>'
                f'<div>{meta_html}'
                f'<div class="{bubble_class}">{msg["text"]}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )


render_chat()

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
        fresh = load_data()
        fresh["rooms"].setdefault(room, [])
        fresh["rooms"][room].append({
            "user_id": st.session_state.user_id,
            "name": st.session_state.username,
            "text": text.strip(),
            "time": datetime.now().isoformat(),
        })
        fresh["rooms"][room] = fresh["rooms"][room][-500:]
        save_data(fresh)
        st.session_state.data = fresh
        st.session_state.last_read[room] = len(fresh["rooms"][room])
        st.rerun()
