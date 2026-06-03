import streamlit as st
import pandas as pd
import sqlite3
import io
from PIL import Image
import time
import urllib.parse
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────
# 1. CONFIG & BOOTSTRAP
# ─────────────────────────────────────────────
st.set_page_config(page_title="Trip Expense Splitter Pro", layout="wide", page_icon="✈️")

st_autorefresh(interval=1000, limit=None, key="trip_app_live_refresh")

# ─── Global CSS: Facebook-like look ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@400;500;600;700&display=swap');

/* ── Reset & base ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #f0f2f5 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}

/* ── Sidebar (Facebook left nav) ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #dadde1 !important;
    box-shadow: 2px 0 4px rgba(0,0,0,.06) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* Sidebar header */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #1c1e21 !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    padding: 8px 0 4px 0 !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] button {
    border-radius: 6px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: background .15s !important;
}

/* ── Top header bar ── */
header[data-testid="stHeader"] {
    background: #ffffff !important;
    border-bottom: 1px solid #dadde1 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.1) !important;
    height: 56px !important;
}

/* ── Tab bar (Facebook-style blue underline) ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #dadde1 !important;
    background: #fff !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0 8px !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: #65676b !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 0 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #1877f2 !important;
    border-bottom: 3px solid #1877f2 !important;
}

/* ── Cards / expanders ── */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #dadde1 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,.06) !important;
    margin-bottom: 8px !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
.stButton > button[kind="primary"] {
    background: #1877f2 !important;
    border: none !important;
    color: #fff !important;
}
.stButton > button[kind="primary"]:hover { background: #166fe5 !important; }

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius: 20px !important;
    border: 1px solid #ccd0d5 !important;
    background: #f0f2f5 !important;
    font-size: 15px !important;
    padding: 8px 16px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #1877f2 !important;
    background: #fff !important;
    box-shadow: 0 0 0 2px rgba(24,119,242,.2) !important;
}

/* ── Main title ── */
h1 { color: #1c1e21 !important; font-weight: 700 !important; }
h2 { color: #1c1e21 !important; font-weight: 700 !important; }

/* ── Success / Warning / Error badges ── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── Messenger chat bubbles CSS ── */
.fb-chat-window {
    background: #fff;
    border: 1px solid #dadde1;
    border-radius: 10px;
    box-shadow: 0 4px 16px rgba(0,0,0,.14);
    overflow: hidden;
    margin-bottom: 12px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}
.fb-chat-header {
    background: #fff;
    border-bottom: 1px solid #e4e6eb;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.fb-chat-header-avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    background: #1877f2;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 700; font-size: 14px;
}
.fb-chat-header-name {
    font-weight: 700; font-size: 15px; color: #1c1e21; flex: 1;
}
.fb-chat-header-actions { display: flex; gap: 12px; }
.fb-chat-header-actions span { font-size: 18px; color: #1877f2; cursor: pointer; }

.fb-chat-body {
    background: #fff;
    min-height: 180px;
    max-height: 320px;
    overflow-y: auto;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

/* ── Outgoing bubble (right / green-ish blue) ── */
.fb-bubble-out {
    align-self: flex-end;
    background: #0084ff;
    color: #fff;
    padding: 8px 14px;
    border-radius: 18px 18px 4px 18px;
    max-width: 75%;
    font-size: 14px;
    line-height: 1.45;
    margin-left: auto;
    word-break: break-word;
}
/* ── Incoming bubble (left / grey) ── */
.fb-bubble-in {
    align-self: flex-start;
    background: #f0f0f0;
    color: #1c1e21;
    padding: 8px 14px;
    border-radius: 18px 18px 18px 4px;
    max-width: 75%;
    font-size: 14px;
    line-height: 1.45;
    word-break: break-word;
}
/* ── System / auto bubble ── */
.fb-bubble-sys {
    align-self: center;
    background: #e7f3ff;
    color: #1877f2;
    padding: 6px 14px;
    border-radius: 12px;
    max-width: 90%;
    font-size: 13px;
    border-left: 4px solid #1877f2;
    line-height: 1.45;
    word-break: break-word;
}
.fb-bubble-time {
    font-size: 11px;
    color: #8a8d91;
    margin-top: 2px;
    text-align: right;
}
.fb-bubble-time.left { text-align: left; }

.fb-sender-name {
    font-size: 12px; color: #65676b; font-weight: 600;
    margin-bottom: 2px; margin-left: 2px;
}

.fb-chat-footer {
    border-top: 1px solid #e4e6eb;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    background: #fff;
}
.fb-chat-footer-input {
    flex: 1;
    background: #f0f2f5;
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 14px;
    border: none;
    outline: none;
    color: #1c1e21;
}
.fb-chat-footer-icons { display: flex; gap: 6px; font-size: 20px; }
.fb-thumbsup { font-size: 22px; cursor: pointer; }

/* Notification badge */
.fb-badge {
    display: inline-block;
    background: #fa3e3e;
    color: #fff;
    border-radius: 10px;
    padding: 1px 7px;
    font-size: 12px;
    font-weight: 700;
    margin-left: 4px;
    vertical-align: middle;
}

/* Online dot */
.online-dot { color: #31a24c; }
.offline-dot { color: #bcc0c4; }

/* Member row */
.member-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 6px 0; border-bottom: 1px solid #f0f2f5;
}
.member-name { font-size: 14px; font-weight: 500; color: #1c1e21; }
</style>
""", unsafe_allow_html=True)

DB_FILE = "trip_database.db"

BANK_LIST = [
    "-- เลือกธนาคาร --",
    "กสิกรไทย (KBank)", "ไทยพาณิชย์ (SCB)", "กรุงไทย (KTB)",
    "กรุงเทพ (BBL)", "กรุงศรีอยุธยา (BAY)", "ทหารไทยธนชาต (TTB)",
    "ออมสิน (GSB)", "ธ.ก.ส.", "ยูโอบี (UOB)"
]

# ─────────────────────────────────────────────
# 2. DATABASE
# ─────────────────────────────────────────────
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS all_users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, status INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, name TEXT, FOREIGN KEY(trip_id) REFERENCES trips(id))')
    c.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, description TEXT, amount REAL, payer_name TEXT, split_members TEXT, image_blob BLOB, FOREIGN KEY(trip_id) REFERENCES trips(id))')
    c.execute('CREATE TABLE IF NOT EXISTS settlements (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, debtor TEXT, creditor TEXT, amount REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(trip_id) REFERENCES trips(id))')
    c.execute('CREATE TABLE IF NOT EXISTS online_status (name TEXT PRIMARY KEY, last_seen DATETIME)')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_id INTEGER, to_user TEXT, from_user TEXT, message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_auto INTEGER DEFAULT 0, is_read INTEGER DEFAULT 0,
        FOREIGN KEY(trip_id) REFERENCES trips(id))''')

    for col, dtype in [('promptpay','TEXT'),('bank_name','TEXT'),('bank_account','TEXT')]:
        try: conn.execute(f"ALTER TABLE all_users ADD COLUMN {col} {dtype}")
        except: pass
    try: conn.execute("ALTER TABLE trips ADD COLUMN trip_date TEXT")
    except: pass
    for col in ['is_auto','is_read','timestamp']:
        try: conn.execute(f"ALTER TABLE notifications ADD COLUMN {col} {'DATETIME DEFAULT CURRENT_TIMESTAMP' if col=='timestamp' else 'INTEGER DEFAULT 0'}")
        except: pass

    conn.commit(); conn.close()

def compress_image(uploaded_file):
    if uploaded_file is None: return None
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA","P"): img = img.convert("RGB")
    img.thumbnail((800,800))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()

def update_online_heartbeat(username):
    if username:
        conn = get_db_connection()
        conn.execute("INSERT INTO online_status (name, last_seen) VALUES (?, datetime('now','localtime')) ON CONFLICT(name) DO UPDATE SET last_seen=datetime('now','localtime')", (username,))
        conn.commit(); conn.close()

def get_currently_online_users():
    conn = get_db_connection()
    rows = conn.execute("SELECT name FROM online_status WHERE last_seen >= datetime('now','localtime','-15 seconds')").fetchall()
    conn.close()
    return [r["name"] for r in rows]

init_db()

# ─────────────────────────────────────────────
# 3. SESSION STATE
# ─────────────────────────────────────────────
if "current_online_user" not in st.session_state:
    st.session_state["current_online_user"] = None
if st.session_state["current_online_user"]:
    update_online_heartbeat(st.session_state["current_online_user"])

# ─────────────────────────────────────────────
# 4. SIDEBAR — LOGIN
# ─────────────────────────────────────────────
# Facebook-style sidebar header
st.sidebar.markdown("""
<div style="background:#1877f2;margin:-1rem -1rem 12px -1rem;padding:14px 16px;display:flex;align-items:center;gap:10px;">
  <span style="font-size:26px;font-weight:900;color:#fff;letter-spacing:-1px;">f</span>
  <span style="color:#fff;font-weight:700;font-size:16px;">Trip Expense Splitter</span>
</div>
""", unsafe_allow_html=True)

conn = get_db_connection()
existing_all_users = [r["name"] for r in conn.execute("SELECT name FROM all_users").fetchall()]
conn.close()

if st.session_state["current_online_user"] is None:
    st.sidebar.markdown("### 🔐 เข้าสู่ระบบ")
    login_mode = st.sidebar.radio("", ["เลือกโปรไฟล์", "สร้างใหม่"], horizontal=True)
    if login_mode == "เลือกโปรไฟล์":
        if existing_all_users:
            user_select = st.sidebar.selectbox("ชื่อของคุณ:", existing_all_users)
            if st.sidebar.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
                st.session_state["current_online_user"] = user_select
                update_online_heartbeat(user_select)
                st.toast(f"👋 ยินดีต้อนรับ, {user_select}!")
                time.sleep(0.5); st.rerun()
        else:
            st.sidebar.caption("ยังไม่มีสมาชิก กรุณาสร้างใหม่")
    else:
        new_name = st.sidebar.text_input("ชื่อเล่น:").strip()
        if st.sidebar.button("สร้างบัญชี", type="primary", use_container_width=True):
            if new_name:
                try:
                    conn = get_db_connection()
                    conn.execute("INSERT INTO all_users (name) VALUES (?)", (new_name,))
                    conn.commit(); conn.close()
                    st.session_state["current_online_user"] = new_name
                    update_online_heartbeat(new_name)
                    time.sleep(0.5); st.rerun()
                except: st.sidebar.error("❌ ชื่อนี้มีแล้ว")
            else: st.sidebar.error("⚠️ กรอกชื่อก่อน")
else:
    me = st.session_state["current_online_user"]
    # Profile row
    st.sidebar.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:6px 0 10px 0;">
      <div style="width:38px;height:38px;border-radius:50%;background:#1877f2;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:16px;flex-shrink:0;">{me[0].upper()}</div>
      <div>
        <div style="font-weight:700;font-size:15px;color:#1c1e21;">{me}</div>
        <div style="font-size:12px;color:#31a24c;font-weight:500;">🟢 ออนไลน์</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    my_data = conn.execute("SELECT * FROM all_users WHERE name=?", (me,)).fetchone()
    conn.close()

    with st.sidebar.expander("⚙️ แก้ไขโปรไฟล์"):
        edit_pp = st.text_input("พร้อมเพย์:", value=my_data['promptpay'] or "")
        db_bank = my_data['bank_name'] or "-- เลือกธนาคาร --"
        bank_idx = BANK_LIST.index(db_bank) if db_bank in BANK_LIST else 0
        edit_bank_name = st.selectbox("ธนาคาร:", BANK_LIST, index=bank_idx)
        edit_bank_acc = st.text_input("เลขบัญชี:", value=my_data['bank_account'] or "")
        if st.button("💾 บันทึก", type="primary", use_container_width=True):
            final_bank = edit_bank_name if edit_bank_name != "-- เลือกธนาคาร --" else ""
            conn = get_db_connection()
            conn.execute("UPDATE all_users SET promptpay=?,bank_name=?,bank_account=? WHERE name=?",
                         (edit_pp, final_bank, edit_bank_acc, me))
            conn.commit(); conn.close()
            st.toast("💾 บันทึกแล้ว!"); time.sleep(0.5); st.rerun()

    if st.sidebar.button("🚪 ออกจากระบบ", use_container_width=True):
        conn = get_db_connection()
        conn.execute("DELETE FROM online_status WHERE name=?", (me,))
        conn.commit(); conn.close()
        st.session_state["current_online_user"] = None; st.rerun()

# ─── Online users ──────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("**🌐 ออนไลน์ตอนนี้**")
online_users = get_currently_online_users()
if online_users:
    for u in online_users:
        tag = " *(คุณ)*" if u == st.session_state["current_online_user"] else ""
        dot = "🟢"
        st.sidebar.markdown(f"<div style='font-size:14px;padding:2px 0;'>{dot} <b>{u}</b>{tag}</div>", unsafe_allow_html=True)
else:
    st.sidebar.caption("ไม่มีใครออนไลน์")

# ─── Create Event ──────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("**➕ สร้าง Event ใหม่**")
new_trip_name = st.sidebar.text_input("ชื่อ Event:").strip()
new_trip_date = st.sidebar.date_input("วันที่:", value=datetime.today())
if st.sidebar.button("สร้าง Event", type="primary", use_container_width=True):
    if new_trip_name:
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO trips (name, status, trip_date) VALUES (?,0,?)", (new_trip_name, new_trip_date.strftime("%Y-%m-%d")))
            conn.commit(); conn.close()
            st.success(f"✈️ สร้าง '{new_trip_name}' สำเร็จ!"); time.sleep(0.5); st.rerun()
        except: st.sidebar.error("❌ ชื่อ Event ซ้ำ")
    else: st.sidebar.error("⚠️ กรอกชื่อ Event")

# ─── Trash ────────────────────────────────────────────────────────────────
conn = get_db_connection()
with st.sidebar.expander("🗑️ ถังขยะ"):
    deleted_trips = conn.execute("SELECT * FROM trips WHERE status=1").fetchall()
    if not deleted_trips: st.caption("ถังขยะว่าง")
    else:
        for dt in deleted_trips:
            c1,c2 = st.columns([2,1])
            has_dt = dt['trip_date'] and str(dt['trip_date']).strip()
            disp = f"{dt['name']} ({dt['trip_date']})" if has_dt else dt['name']
            c1.write(disp)
            s1,s2 = c2.columns(2)
            if s1.button("กู้",key=f"res_{dt['id']}"):
                conn.execute("UPDATE trips SET status=0 WHERE id=?", (dt['id'],))
                conn.commit(); st.toast("🔄 กู้คืนแล้ว!"); time.sleep(0.5); st.rerun()
            if s2.button("ลบ",key=f"pdel_{dt['id']}"):
                for tbl in ["settlements","expenses","members"]:
                    conn.execute(f"DELETE FROM {tbl} WHERE trip_id=?", (dt['id'],))
                conn.execute("DELETE FROM trips WHERE id=?", (dt['id'],))
                conn.commit(); st.toast("💥 ลบถาวร!"); time.sleep(0.5); st.rerun()

active_trips_df = pd.read_sql_query("SELECT * FROM trips WHERE status=0", conn)
if not active_trips_df.empty:
    active_trips_df['display_name'] = active_trips_df.apply(
        lambda r: f"{r['name']} 📅 ({r['trip_date']})" if r['trip_date'] and str(r['trip_date']).strip() else r['name'], axis=1)
    active_trip_display_list = active_trips_df["display_name"].tolist()
else:
    active_trip_display_list = []

if not active_trip_display_list:
    st.title("✈️ Trip Expense Splitter Pro")
    st.info("กรุณาสร้าง Event ใหม่หรือกู้คืนจากถังขยะที่เมนูซ้าย")
    st.stop()

st.sidebar.markdown("---")
selected_display_trip = st.sidebar.selectbox("🗺️ เลือก Event:", active_trip_display_list)
matched_trip = active_trips_df[active_trips_df['display_name'] == selected_display_trip].iloc[0]
current_trip = matched_trip['name']
trip_id = int(matched_trip['id'])
current_trip_date = matched_trip['trip_date']

with st.sidebar.expander("✏️ แก้ไข Event"):
    rename_input = st.text_input("ชื่อใหม่:", value=current_trip).strip()
    try:
        default_date = datetime.strptime(str(current_trip_date), "%Y-%m-%d") if current_trip_date and str(current_trip_date).strip() else datetime.today()
    except: default_date = datetime.today()
    re_date_input = st.date_input("วันที่:", value=default_date)
    if st.button("💾 ยืนยัน", type="primary"):
        if rename_input:
            try:
                conn2 = get_db_connection()
                conn2.execute("UPDATE trips SET name=?,trip_date=? WHERE id=?", (rename_input, re_date_input.strftime("%Y-%m-%d"), trip_id))
                conn2.commit(); conn2.close()
                st.success("✏️ อัปเดตแล้ว!"); time.sleep(0.5); st.rerun()
            except: st.error("❌ ชื่อซ้ำ")

if st.sidebar.button("🗑️ ลบ Event นี้"):
    conn.execute("UPDATE trips SET status=1 WHERE id=?", (trip_id,))
    conn.commit(); st.toast("🗑️ ย้ายสู่ถังขยะ"); time.sleep(0.5); st.rerun()

# ─────────────────────────────────────────────
# 5. MEMBERS SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("**👥 สมาชิกใน Event**")
all_users_list = [r["name"] for r in conn.execute("SELECT name FROM all_users").fetchall()]
existing_members = [r["name"] for r in conn.execute("SELECT name FROM members WHERE trip_id=?", (trip_id,)).fetchall()]
available_users = [u for u in all_users_list if u not in existing_members]

if existing_members:
    conn_mn = get_db_connection()
    for member in existing_members:
        unread_row = conn_mn.execute(
            "SELECT COUNT(*) as cnt FROM notifications WHERE trip_id=? AND to_user=? AND is_read=0",
            (trip_id, member)).fetchone()
        unread_cnt = unread_row["cnt"] if unread_row else 0
        is_online = member in online_users
        dot = "🟢" if is_online else "⚪"
        badge_html = f'<span class="fb-badge">{unread_cnt}</span>' if unread_cnt > 0 else ""
        you_tag = " <i>(คุณ)</i>" if member == st.session_state["current_online_user"] else ""
        
        col_m, col_btn = st.sidebar.columns([4,1])
        col_m.markdown(f"<div style='font-size:14px;padding:3px 0;'>{dot} <b>{member}</b>{you_tag}{badge_html}</div>", unsafe_allow_html=True)
        if col_btn.button("ออก", key=f"rm_{member}"):
            conn_mn.execute("DELETE FROM members WHERE trip_id=? AND name=?", (trip_id, member))
            conn_mn.commit(); st.toast(f"ถอด {member} แล้ว"); time.sleep(0.5); st.rerun()
    conn_mn.close()

sel_user = st.sidebar.selectbox("เชิญเพื่อน:", ["-- เลือก --"] + available_users)
if st.sidebar.button("➕ เพิ่มเข้ากลุ่ม", type="primary", use_container_width=True):
    if sel_user != "-- เลือก --":
        conn.execute("INSERT INTO members (trip_id, name) VALUES (?,?)", (trip_id, sel_user))
        conn.commit(); st.toast(f"➕ เพิ่ม {sel_user} แล้ว!"); time.sleep(0.5); st.rerun()
conn.close()

# ─────────────────────────────────────────────
# 6. MESSENGER-STYLE CHAT (Facebook popup UI)
# ─────────────────────────────────────────────
st.sidebar.markdown("---")

my_name = st.session_state["current_online_user"]
notif_count = 0
if my_name:
    conn_c = get_db_connection()
    row_c = conn_c.execute("SELECT COUNT(*) as cnt FROM notifications WHERE trip_id=? AND to_user=? AND is_read=0", (trip_id, my_name)).fetchone()
    notif_count = row_c["cnt"] if row_c else 0
    conn_c.close()

# Header with badge like Facebook Messenger
badge_str = f'<span class="fb-badge">{notif_count}</span>' if notif_count > 0 else ""
st.sidebar.markdown(f"""
<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
  <span style="font-size:20px;">💬</span>
  <span style="font-weight:700;font-size:16px;color:#1c1e21;">Messenger</span>
  {badge_str}
</div>
""", unsafe_allow_html=True)

if my_name:
    conn_notif = get_db_connection()
    all_chat_rows = conn_notif.execute(
        """SELECT * FROM notifications WHERE trip_id=?
           AND (to_user=? OR from_user=? OR (to_user=? AND is_auto=1))
           ORDER BY timestamp ASC, id ASC""",
        (trip_id, my_name, my_name, my_name)).fetchall()
    conn_notif.close()

    # Group by conversation partner
    chat_groups = {}
    unread_status = {}
    for n in all_chat_rows:
        if n['is_auto'] == 1 or n['from_user'] == "ระบบสรุปยอด":
            partner = "🤖 ระบบ"
        else:
            partner = n['from_user'] if n['to_user'] == my_name else n['to_user']
        if partner not in chat_groups:
            chat_groups[partner] = []; unread_status[partner] = 0
        chat_groups[partner].append(n)
        if n['to_user'] == my_name and n['is_read'] == 0:
            unread_status[partner] += 1

    # Render each chat as a Messenger-style window
    for partner, messages in chat_groups.items():
        unread = unread_status[partner]
        badge_p = f'<span class="fb-badge">{unread}</span>' if unread > 0 else ""
        init = partner[0].upper() if partner != "🤖 ระบบ" else "🤖"

        exp_label = f"{partner}{(' 🔴' + str(unread)) if unread > 0 else ''}"
        with st.sidebar.expander(exp_label, expanded=(unread > 0)):
            # Mark as read when opened
            if unread > 0:
                conn_rd = get_db_connection()
                if partner == "🤖 ระบบ":
                    conn_rd.execute("UPDATE notifications SET is_read=1 WHERE trip_id=? AND to_user=? AND is_auto=1 AND is_read=0", (trip_id, my_name))
                else:
                    conn_rd.execute("UPDATE notifications SET is_read=1 WHERE trip_id=? AND to_user=? AND from_user=? AND is_read=0", (trip_id, my_name, partner))
                conn_rd.commit(); conn_rd.close()
                st.rerun()

            # ── Chat header (Facebook Messenger style) ──────────────────────
            st.markdown(f"""
            <div class="fb-chat-window">
              <div class="fb-chat-header">
                <div class="fb-chat-header-avatar">{init}</div>
                <div class="fb-chat-header-name">{partner}</div>
                <div class="fb-chat-header-actions">
                  <span title="โทร">📞</span>
                  <span title="วิดีโอ">📹</span>
                </div>
              </div>
              <div class="fb-chat-body">
            """, unsafe_allow_html=True)

            # ── Render message bubbles ───────────────────────────────────────
            bubbles_html = ""
            for notif in messages:
                ts = ""
                if notif['timestamp']:
                    try: ts = datetime.strptime(notif['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                    except: ts = str(notif['timestamp'])[11:16]

                is_mine = (notif['from_user'] == my_name and notif['is_auto'] == 0)
                is_sys  = (notif['is_auto'] == 1 or notif['from_user'] == "ระบบสรุปยอด")
                msg_txt = notif['message'].replace('\n','<br>')

                if is_sys:
                    bubbles_html += f"""
                    <div style="align-self:center;margin:6px 0;width:100%;">
                      <div class="fb-bubble-sys">{msg_txt}</div>
                      <div class="fb-bubble-time" style="text-align:center;">{ts}</div>
                    </div>"""
                elif is_mine:
                    bubbles_html += f"""
                    <div style="display:flex;flex-direction:column;align-items:flex-end;margin:3px 0;">
                      <div class="fb-bubble-out">{msg_txt}</div>
                      <div class="fb-bubble-time">{ts}</div>
                    </div>"""
                else:
                    bubbles_html += f"""
                    <div style="display:flex;flex-direction:column;align-items:flex-start;margin:3px 0;">
                      <div class="fb-sender-name">{notif['from_user']}</div>
                      <div class="fb-bubble-in">{msg_txt}</div>
                      <div class="fb-bubble-time left">{ts}</div>
                    </div>"""

            st.markdown(bubbles_html + "</div></div>", unsafe_allow_html=True)

            # ── Delete buttons ───────────────────────────────────────────────
            with st.expander("🗑️ ลบข้อความ"):
                for notif in messages:
                    short = notif['message'][:30] + "..." if len(notif['message']) > 30 else notif['message']
                    col_t, col_d = st.columns([3,1])
                    col_t.caption(short)
                    if col_d.button("ลบ", key=f"del_n_{notif['id']}"):
                        conn_del = get_db_connection()
                        conn_del.execute("DELETE FROM notifications WHERE id=?", (notif['id'],))
                        conn_del.commit(); conn_del.close()
                        st.toast("ลบแล้ว"); time.sleep(0.3); st.rerun()

            # ── Reply input (like Messenger footer) ─────────────────────────
            if partner != "🤖 ระบบ":
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                with st.form(key=f"reply_{partner}", clear_on_submit=True):
                    reply_txt = st.text_input("", placeholder=f"Aa   ส่งข้อความถึง {partner}...", label_visibility="collapsed")
                    c_send, c_like = st.columns([4,1])
                    sent = c_send.form_submit_button("ส่ง ▶", type="primary", use_container_width=True)
                    liked = c_like.form_submit_button("👍", use_container_width=True)
                    if sent and reply_txt.strip():
                        conn_r = get_db_connection()
                        conn_r.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                       (trip_id, partner, my_name, reply_txt.strip()))
                        conn_r.commit(); conn_r.close()
                        st.toast(f"🚀 ส่งหา {partner}!"); time.sleep(0.3); st.rerun()
                    if liked:
                        conn_r = get_db_connection()
                        conn_r.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                       (trip_id, partner, my_name, "👍"))
                        conn_r.commit(); conn_r.close()
                        st.rerun()

    # ── New chat ──────────────────────────────────────────────────────────
    st.sidebar.markdown("**📝 เริ่มแชทใหม่**")
    other_members = [m for m in existing_members if m != my_name]
    if other_members:
        send_to = st.sidebar.selectbox("เลือกคน:", other_members, key="new_chat_to")
        with st.sidebar.form("new_chat_form", clear_on_submit=True):
            new_msg = st.text_input("", placeholder="พิมพ์ข้อความ...", label_visibility="collapsed")
            c1_nc, c2_nc = st.columns([3,1])
            if c1_nc.form_submit_button("ส่ง ▶", type="primary", use_container_width=True):
                if new_msg.strip():
                    conn_ns = get_db_connection()
                    conn_ns.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                    (trip_id, send_to, my_name, new_msg.strip()))
                    conn_ns.commit(); conn_ns.close()
                    st.toast(f"🚀 ส่งหา {send_to}!"); time.sleep(0.3); st.rerun()
            if c2_nc.form_submit_button("👍"):
                conn_ns = get_db_connection()
                conn_ns.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                (trip_id, send_to, my_name, "👍"))
                conn_ns.commit(); conn_ns.close(); st.rerun()
    else:
        st.sidebar.caption("ไม่มีสมาชิกอื่นในกลุ่ม")
else:
    st.sidebar.caption("กรุณาเข้าสู่ระบบเพื่อใช้แชท")

# ─────────────────────────────────────────────
# 7. MAIN CONTENT AREA
# ─────────────────────────────────────────────
if st.session_state["current_online_user"] is None:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;">
      <div style="font-size:64px;">✈️</div>
      <h1 style="color:#1c1e21;">Trip Expense Splitter Pro</h1>
      <p style="color:#65676b;font-size:16px;">กรุณาเลือกโปรไฟล์หรือสร้างบัญชีใหม่ที่แถบซ้าย</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not existing_members:
    st.markdown(f"""
    <div style="background:#fff;border-radius:12px;padding:32px;border:1px solid #dadde1;text-align:center;margin-top:20px;">
      <div style="font-size:48px;margin-bottom:12px;">👥</div>
      <h2>Event: {current_trip}</h2>
      <p style="color:#65676b;">ยังไม่มีสมาชิก — เชิญเพื่อนที่แถบซ้ายก่อนเริ่มบิล</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

has_valid_date = current_trip_date and str(current_trip_date).strip()

# ── Page hero ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#fff;border-radius:12px;padding:20px 24px;border:1px solid #dadde1;
            box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:20px;
            display:flex;align-items:center;gap:16px;">
  <div style="width:56px;height:56px;border-radius:50%;background:#1877f2;
              display:flex;align-items:center;justify-content:center;
              font-size:28px;flex-shrink:0;">✈️</div>
  <div>
    <h2 style="margin:0;color:#1c1e21;font-size:22px;">{current_trip}</h2>
    <p style="margin:0;color:#65676b;font-size:14px;">
      {'📅 ' + str(current_trip_date) if has_valid_date else ''} &nbsp;·&nbsp; 
      👥 {len(existing_members)} สมาชิก
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📝 เพิ่มบิล", "📊 ประวัติบิล", "💰 สรุปเคลียร์เงิน"])

# ══════════════════════════════════════════════
# TAB 1 — ADD BILL
# ══════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div style="background:#fff;border-radius:12px;padding:24px;border:1px solid #dadde1;box-shadow:0 1px 3px rgba(0,0,0,.08);">
    """, unsafe_allow_html=True)
    st.header("➕ เพิ่มรายการบิล")

    with st.form("add_bill", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            desc = st.text_input("📌 รายการ:", placeholder="เช่น ค่าอาหาร, ค่าแท็กซี่...")
            amt  = st.number_input("💰 จำนวนเงิน (บาท):", min_value=0.0, step=10.0)
        with col_b:
            my_idx = existing_members.index(my_name) if my_name in existing_members else 0
            payer  = st.selectbox("👤 คนสำรองจ่าย:", existing_members, index=my_idx)
            file   = st.file_uploader("📎 แนบสลิป:", type=['jpg','png','jpeg'])

        st.markdown("**👥 เลือกคนที่ร่วมหาร:**")
        cols_split = st.columns(min(len(existing_members), 4))
        split_to = []
        for i, m in enumerate(existing_members):
            if cols_split[i % 4].checkbox(m, value=True, key=f"add_{m}"):
                split_to.append(m)

        if st.form_submit_button("💾 บันทึกบิล", type="primary", use_container_width=True):
            if desc and amt > 0 and split_to:
                blob = compress_image(file)
                conn_ab = get_db_connection()
                conn_ab.execute("INSERT INTO expenses (trip_id,description,amount,payer_name,split_members,image_blob) VALUES (?,?,?,?,?,?)",
                                (trip_id, desc, amt, payer, ",".join(split_to), blob))
                conn_ab.commit()
                share = amt / len(split_to)
                for m in split_to:
                    if m != payer:
                        sys_msg = f"📌 บิลใหม่: '{desc}'\n💰 รวม {amt:,.2f} บาท | จ่ายโดย: {payer}\n💸 ส่วนของคุณ: {share:,.2f} บาท"
                        conn_ab.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,'ระบบสรุปยอด',?,1,0,datetime('now','localtime'))",
                                        (trip_id, m, sys_msg))
                conn_ab.commit(); conn_ab.close()
                st.success(f"✅ บันทึก '{desc}' แล้ว และส่งแจ้งเตือนสมาชิก!")
                time.sleep(0.8); st.rerun()
            else:
                st.error("⚠️ กรอกข้อมูลให้ครบ: รายการ, จำนวนเงิน, และเลือกผู้หาร")
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 2 — HISTORY
# ══════════════════════════════════════════════
with tab2:
    conn_h = get_db_connection()
    expenses = conn_h.execute("SELECT * FROM expenses WHERE trip_id=?", (trip_id,)).fetchall()
    conn_h.close()

    if not expenses:
        st.markdown("""
        <div style="text-align:center;padding:60px;background:#fff;border-radius:12px;border:1px solid #dadde1;">
          <div style="font-size:48px;margin-bottom:12px;">📭</div>
          <p style="color:#65676b;font-size:16px;">ยังไม่มีบิล — บิลจะอัปเดตแบบเรียลไทม์</p>
        </div>""", unsafe_allow_html=True)
    else:
        for row in expenses:
            s_list = row['split_members'].split(",")
            share = row['amount'] / len(s_list)
            with st.expander(f"📌 {row['description']} — {row['amount']:,.2f} บาท  |  จ่ายโดย {row['payer_name']}"):
                c1, c2 = st.columns([1,1.5])
                with c1:
                    if row['image_blob']:
                        st.image(row['image_blob'], use_container_width=True, caption="สลิป")
                    else:
                        st.markdown("""
                        <div style="background:#f0f2f5;border-radius:8px;height:120px;
                                    display:flex;align-items:center;justify-content:center;
                                    color:#8a8d91;font-size:14px;">ไม่มีสลิป</div>""", unsafe_allow_html=True)
                    st.markdown(f"**หารกัน {len(s_list)} คน:** {', '.join(s_list)}")
                    st.markdown(f"**คนละ:** {share:,.2f} บาท")
                with c2:
                    with st.form(f"edit_{row['id']}"):
                        u_desc  = st.text_input("รายการ:", value=row['description'])
                        u_amt   = st.number_input("จำนวนเงิน:", value=row['amount'])
                        payer_opts = existing_members if row['payer_name'] in existing_members else existing_members+[row['payer_name']]
                        u_payer = st.selectbox("คนจ่าย:", payer_opts, index=payer_opts.index(row['payer_name']))
                        st.write("คนหาร:")
                        u_split = [m for m in payer_opts if st.checkbox(m, value=(m in row['split_members'].split(",")), key=f"ed_{row['id']}_{m}")]
                        u_file  = st.file_uploader("เปลี่ยนสลิป:", type=['jpg','png','jpeg'])
                        del_img = st.checkbox("🗑️ ลบรูปสลิป", key=f"delimg_{row['id']}")
                        if st.form_submit_button("💾 อัปเดต", type="primary"):
                            conn_u = get_db_connection()
                            if del_img:
                                conn_u.execute("UPDATE expenses SET description=?,amount=?,payer_name=?,split_members=?,image_blob=NULL WHERE id=?",
                                               (u_desc,u_amt,u_payer,",".join(u_split),row['id']))
                            elif u_file:
                                conn_u.execute("UPDATE expenses SET description=?,amount=?,payer_name=?,split_members=?,image_blob=? WHERE id=?",
                                               (u_desc,u_amt,u_payer,",".join(u_split),compress_image(u_file),row['id']))
                            else:
                                conn_u.execute("UPDATE expenses SET description=?,amount=?,payer_name=?,split_members=? WHERE id=?",
                                               (u_desc,u_amt,u_payer,",".join(u_split),row['id']))
                            conn_u.commit(); conn_u.close()
                            st.success("✅ อัปเดตแล้ว!"); time.sleep(0.5); st.rerun()
                    if st.button("🗑️ ลบบิลนี้", key=f"del_b_{row['id']}", type="secondary"):
                        conn_d = get_db_connection()
                        conn_d.execute("DELETE FROM expenses WHERE id=?", (row['id'],))
                        conn_d.commit(); conn_d.close()
                        st.warning("ลบบิลแล้ว"); time.sleep(0.5); st.rerun()

# ══════════════════════════════════════════════
# TAB 3 — SETTLE UP
# ══════════════════════════════════════════════
with tab3:
    conn_s = get_db_connection()
    expenses_rows = conn_s.execute("SELECT * FROM expenses WHERE trip_id=?", (trip_id,)).fetchall()
    user_profiles = {r['name']: {"promptpay":r['promptpay'],"bank_name":r['bank_name'],"bank_acc":r['bank_account']}
                     for r in conn_s.execute("SELECT name,promptpay,bank_name,bank_account FROM all_users").fetchall()}
    conn_s.close()

    if not expenses_rows:
        st.markdown("""
        <div style="text-align:center;padding:60px;background:#fff;border-radius:12px;border:1px solid #dadde1;">
          <div style="font-size:48px;">💰</div>
          <p style="color:#65676b;font-size:16px;">ยังไม่มีบิลสำหรับคำนวณ</p>
        </div>""", unsafe_allow_html=True)
    else:
        all_inv = set(existing_members)
        for r in expenses_rows:
            all_inv.add(r['payer_name'])
            all_inv.update(r['split_members'].split(","))

        net = {m: 0.0 for m in all_inv}
        for r in expenses_rows:
            net[r['payer_name']] += r['amount']
            s_l = r['split_members'].split(",")
            sh = r['amount'] / len(s_l)
            for m in s_l: net[m] -= sh

        # Summary cards
        st.markdown("### 📊 ยอดสรุปรายคน")
        cols_net = st.columns(min(len(all_inv), 4))
        for i, (m, b) in enumerate(net.items()):
            with cols_net[i % 4]:
                color = "#31a24c" if b > 0.01 else ("#fa3e3e" if b < -0.01 else "#1877f2")
                icon  = "🟢" if b > 0.01 else ("🔴" if b < -0.01 else "⚖️")
                label = "รับคืน" if b > 0.01 else ("ต้องจ่าย" if b < -0.01 else "เท่ากัน")
                st.markdown(f"""
                <div style="background:#fff;border-radius:10px;padding:16px;
                            border:1px solid #dadde1;text-align:center;margin-bottom:8px;
                            border-top:4px solid {color};">
                  <div style="font-size:22px;">{icon}</div>
                  <div style="font-weight:700;font-size:15px;color:#1c1e21;">{m}</div>
                  <div style="font-size:13px;color:#65676b;">{label}</div>
                  <div style="font-weight:700;font-size:18px;color:{color};">{abs(b):,.2f} ฿</div>
                </div>""", unsafe_allow_html=True)

        # Transfer plan
        st.markdown("### 🚀 แผนการโอนเงิน")
        debtors   = [[m,b] for m,b in net.items() if b < -0.01]
        creditors = [[m,b] for m,b in net.items() if b > 0.01]
        final_tx  = []

        while debtors and creditors:
            amt_t = min(abs(debtors[0][1]), creditors[0][1])
            d_n, c_n = debtors[0][0], creditors[0][0]
            prof = user_profiles.get(c_n, {})
            pp    = (prof.get("promptpay") or "").strip()
            b_nm  = (prof.get("bank_name") or "").strip()
            b_acc = (prof.get("bank_acc") or "").strip()
            is_me = d_n == my_name

            border = "border:2px solid #1877f2;" if is_me else "border:1px solid #dadde1;"
            highlight = "background:#e7f3ff;" if is_me else "background:#fff;"
            me_badge = '<span style="background:#1877f2;color:#fff;padding:2px 8px;border-radius:10px;font-size:12px;margin-left:8px;">⚠️ คุณ</span>' if is_me else ""

            st.markdown(f"""
            <div style="{highlight}{border}border-radius:12px;padding:16px;margin-bottom:12px;">
              <div style="font-size:15px;font-weight:600;color:#1c1e21;margin-bottom:10px;">
                💳 <b>{d_n}</b> {me_badge} &nbsp;→&nbsp; 👉 <b>{c_n}</b> &nbsp;
                <span style="background:#fa3e3e;color:#fff;padding:3px 12px;border-radius:20px;font-size:14px;">{amt_t:,.2f} ฿</span>
              </div>
            """, unsafe_allow_html=True)

            if pp or b_acc:
                pay_cols = st.columns(2)
                with pay_cols[0]:
                    if pp:
                        st.markdown(f"📱 **พร้อมเพย์ {c_n}**")
                        st.code(pp, language="text")
                with pay_cols[1]:
                    if b_acc:
                        lbl = f"🏦 {b_nm}" if b_nm else "🏦 บัญชีธนาคาร"
                        st.markdown(f"{lbl} **{c_n}**")
                        st.code(b_acc, language="text")
            else:
                st.warning(f"⚠️ {c_n} ยังไม่ได้บันทึกข้อมูลบัญชี")
            st.markdown("</div>", unsafe_allow_html=True)

            final_tx.append((d_n, c_n, amt_t))
            debtors[0][1]   += amt_t; creditors[0][1] -= amt_t
            if abs(debtors[0][1])   < 0.01: debtors.pop(0)
            if abs(creditors[0][1]) < 0.01: creditors.pop(0)

        # LINE Share
        st.markdown("### 📲 แชร์ไป LINE")
        line_msg = f"📊 สรุปบิลทริป: {current_trip}\n"
        if has_valid_date: line_msg += f"📅 วันที่: {current_trip_date}\n"
        line_msg += "===============================\n📋 รายละเอียด\n-------------------------------\n"
        total_all = 0.0
        for i, r in enumerate(expenses_rows, 1):
            s = r['split_members'].split(",")
            sh = r['amount']/len(s)
            line_msg += f"{i}. {r['description']}\n   💰 {r['amount']:,.2f} บาท | จ่ายโดย: {r['payer_name']}\n   👥 หาร {len(s)} คน | คนละ {sh:,.2f} บาท\n"
            total_all += r['amount']
        line_msg += f"-------------------------------\n💵 รวม: {total_all:,.2f} บาท\n===============================\n🚀 แผนโอนเงิน\n-------------------------------\n"
        for d_n, c_n, a_m in final_tx:
            line_msg += f"💳 {d_n} → {c_n} = {a_m:,.2f} บาท\n"
            prof = user_profiles.get(c_n, {})
            pp = (prof.get("promptpay") or "").strip()
            b_nm = (prof.get("bank_name") or "").strip()
            b_acc = (prof.get("bank_acc") or "").strip()
            if pp:   line_msg += f"   📱 พร้อมเพย์: {pp}\n"
            if b_acc: line_msg += f"   🏦 {b_nm or 'บัญชี'}: {b_acc}\n"
        line_msg += "==============================="

        st.text_area("ข้อความสำหรับ LINE:", value=line_msg, height=220, disabled=True)
        encoded = urllib.parse.quote(line_msg)
        st.link_button("🟢 เปิด LINE แชร์สรุปยอด", f"https://line.me/R/msg/text/?{encoded}", type="primary", use_container_width=True)
