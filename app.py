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
st.set_page_config(page_title="Trip Expense Splitter", layout="wide", page_icon="✈️",
                   initial_sidebar_state="collapsed")

st_autorefresh(interval=1000, limit=None, key="trip_app_live_refresh")

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Hide default sidebar toggle & header padding ── */
[data-testid="collapsedControl"] { display:none !important; }
[data-testid="stSidebar"]        { display:none !important; }
#MainMenu                        { display:none !important; }
footer                           { display:none !important; }
header[data-testid="stHeader"]   { display:none !important; }

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #f0f2f5 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    padding-top: 0 !important;
}
[data-testid="stMainBlockContainer"] {
    padding-top: 0 !important;
    max-width: 100% !important;
}
[data-testid="stMain"] { padding-top: 0 !important; }

/* ── Top Navbar ── */
.fb-navbar {
    position: sticky;
    top: 0;
    z-index: 999;
    background: #fff;
    border-bottom: 1px solid #dadde1;
    box-shadow: 0 2px 4px rgba(0,0,0,.08);
    padding: 0 16px;
    display: flex;
    align-items: center;
    height: 56px;
    gap: 12px;
}
.fb-navbar-logo {
    font-size: 28px; font-weight: 900; color: #1877f2;
    letter-spacing: -1px; flex-shrink: 0; text-decoration: none;
    font-family: Georgia, serif;
}
.fb-navbar-title {
    font-weight: 700; font-size: 16px; color: #1c1e21;
    white-space: nowrap; flex-shrink: 0;
}
.fb-navbar-sep { color: #dadde1; font-size: 20px; flex-shrink:0; }
.fb-navbar-trip {
    background: #e7f3ff; color: #1877f2;
    padding: 4px 12px; border-radius: 20px;
    font-weight: 600; font-size: 14px; white-space: nowrap;
}
.fb-navbar-spacer { flex: 1; }
.fb-navbar-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: #1877f2; color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 15px; flex-shrink: 0; cursor: pointer;
}
.fb-online-badge {
    background: #31a24c; color: #fff;
    padding: 2px 8px; border-radius: 20px;
    font-size: 12px; font-weight: 600; white-space: nowrap;
}
.fb-notif-badge {
    background: #fa3e3e; color: #fff;
    padding: 2px 8px; border-radius: 20px;
    font-size: 12px; font-weight: 700; white-space: nowrap;
}

/* ── Content area ── */
.fb-content { padding: 16px 24px; }

/* ── Menu bar (below navbar) ── */
.fb-menubar {
    background: #fff;
    border-bottom: 1px solid #dadde1;
    padding: 0 24px;
    display: flex;
    gap: 4px;
    align-items: center;
    overflow-x: auto;
}
.fb-menubar-item {
    padding: 12px 16px;
    font-weight: 600; font-size: 14px;
    color: #65676b; cursor: pointer;
    border-bottom: 3px solid transparent;
    white-space: nowrap;
    text-decoration: none;
}
.fb-menubar-item:hover { color: #1877f2; background: #f0f2f5; border-radius: 6px; }
.fb-menubar-item.active { color: #1877f2; border-bottom: 3px solid #1877f2; }

/* ── Cards ── */
.fb-card {
    background: #fff; border: 1px solid #dadde1;
    border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,.06);
    padding: 20px; margin-bottom: 16px;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #dadde1 !important;
    background: #fff !important; border-radius: 8px 8px 0 0 !important;
    padding: 0 8px !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: #65676b !important; font-weight: 600 !important;
    font-size: 15px !important; padding: 12px 16px !important;
    border-bottom: 3px solid transparent !important; border-radius: 0 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #1877f2 !important; border-bottom: 3px solid #1877f2 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 6px !important; font-weight: 600 !important; font-size: 14px !important;
}
.stButton > button[kind="primary"] {
    background: #1877f2 !important; border: none !important; color: #fff !important;
}
.stButton > button[kind="primary"]:hover { background: #166fe5 !important; }

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius: 20px !important; border: 1px solid #ccd0d5 !important;
    background: #f0f2f5 !important; font-size: 15px !important;
    padding: 8px 16px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #1877f2 !important; background: #fff !important;
    box-shadow: 0 0 0 2px rgba(24,119,242,.2) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #fff !important; border: 1px solid #dadde1 !important;
    border-radius: 8px !important; box-shadow: 0 1px 2px rgba(0,0,0,.06) !important;
    margin-bottom: 8px !important;
}

/* ── Messenger bubbles ── */
.fb-bubble-out {
    align-self: flex-end; background: #0084ff; color: #fff;
    padding: 8px 14px; border-radius: 18px 18px 4px 18px;
    max-width: 75%; font-size: 14px; line-height: 1.45;
    margin-left: auto; word-break: break-word;
}
.fb-bubble-in {
    align-self: flex-start; background: #f0f0f0; color: #1c1e21;
    padding: 8px 14px; border-radius: 18px 18px 18px 4px;
    max-width: 75%; font-size: 14px; line-height: 1.45; word-break: break-word;
}
.fb-bubble-sys {
    align-self: center; background: #e7f3ff; color: #1877f2;
    padding: 6px 14px; border-radius: 12px; max-width: 90%;
    font-size: 13px; border-left: 4px solid #1877f2; line-height: 1.45; word-break: break-word;
}
.fb-bubble-time { font-size: 11px; color: #8a8d91; margin-top: 2px; text-align: right; }
.fb-bubble-time.left { text-align: left; }
.fb-sender-name { font-size: 12px; color: #65676b; font-weight: 600; margin-bottom: 2px; margin-left: 2px; }
.fb-chat-body {
    background: #fff; min-height: 160px; max-height: 300px; overflow-y: auto;
    padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;
    border: 1px solid #e4e6eb; border-radius: 8px; margin-bottom: 8px;
}
.fb-badge {
    display: inline-block; background: #fa3e3e; color: #fff;
    border-radius: 10px; padding: 1px 7px; font-size: 12px; font-weight: 700;
    margin-left: 4px; vertical-align: middle;
}

/* ── Alert ── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* ── Remove top gap from blocks ── */
.block-container { padding-top: 0 !important; }
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

def compress_image(f):
    if f is None: return None
    img = Image.open(f)
    if img.mode in ("RGBA","P"): img = img.convert("RGB")
    img.thumbnail((800,800))
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=70)
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
for key, default in [
    ("current_online_user", None),
    ("active_menu", "home"),        # home | events | members | chat | account
    ("selected_trip_id", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state["current_online_user"]:
    update_online_heartbeat(st.session_state["current_online_user"])

online_users = get_currently_online_users()
me = st.session_state["current_online_user"]

# ─────────────────────────────────────────────
# 4. LOAD DATA
# ─────────────────────────────────────────────
conn_main = get_db_connection()
existing_all_users = [r["name"] for r in conn_main.execute("SELECT name FROM all_users").fetchall()]
active_trips_df = pd.read_sql_query("SELECT * FROM trips WHERE status=0", conn_main)
conn_main.close()

if not active_trips_df.empty:
    active_trips_df['display_name'] = active_trips_df.apply(
        lambda r: f"{r['name']} ({r['trip_date']})" if r['trip_date'] and str(r['trip_date']).strip() else r['name'], axis=1)
    trip_display_list = active_trips_df["display_name"].tolist()
    trip_id_list      = active_trips_df["id"].tolist()
else:
    trip_display_list = []
    trip_id_list = []

# Resolve selected trip
if st.session_state["selected_trip_id"] not in trip_id_list and trip_id_list:
    st.session_state["selected_trip_id"] = trip_id_list[0]

trip_id = st.session_state["selected_trip_id"]
current_trip, current_trip_date = None, None
if trip_id and not active_trips_df.empty:
    row_t = active_trips_df[active_trips_df["id"] == trip_id]
    if not row_t.empty:
        current_trip      = row_t.iloc[0]["name"]
        current_trip_date = row_t.iloc[0]["trip_date"]

existing_members = []
if trip_id:
    conn_m = get_db_connection()
    existing_members = [r["name"] for r in conn_m.execute("SELECT name FROM members WHERE trip_id=?", (trip_id,)).fetchall()]
    conn_m.close()

# Unread notif count
notif_count = 0
if me and trip_id:
    conn_nc = get_db_connection()
    row_nc = conn_nc.execute("SELECT COUNT(*) as cnt FROM notifications WHERE trip_id=? AND to_user=? AND is_read=0", (trip_id, me)).fetchone()
    notif_count = row_nc["cnt"] if row_nc else 0
    conn_nc.close()

# ─────────────────────────────────────────────
# 5. TOP NAVBAR  (pure HTML — always visible)
# ─────────────────────────────────────────────
trip_label = f"✈️ {current_trip}" if current_trip else "— ยังไม่เลือก Event —"
user_avatar = f'<div class="fb-navbar-avatar">{me[0].upper()}</div>' if me else '<div class="fb-navbar-avatar" style="background:#8a8d91;">?</div>'
online_html = f'<span class="fb-online-badge">🟢 {len(online_users)} ออนไลน์</span>' if online_users else ""
notif_html  = f'<span class="fb-notif-badge">🔔 {notif_count}</span>' if notif_count > 0 else ""

st.markdown(f"""
<div class="fb-navbar">
  <span class="fb-navbar-logo">f</span>
  <span class="fb-navbar-title">Trip Splitter</span>
  <span class="fb-navbar-sep">|</span>
  <span class="fb-navbar-trip">{trip_label}</span>
  <span class="fb-navbar-spacer"></span>
  {online_html}
  {notif_html}
  {user_avatar}
  <span style="font-size:13px;font-weight:600;color:#1c1e21;">{me or 'ยังไม่ล็อกอิน'}</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. MENU BAR  (Streamlit buttons styled as tabs)
# ─────────────────────────────────────────────
menu_items = [
    ("🏠", "หน้าหลัก",  "home"),
    ("🗓️", "Events",    "events"),
    ("👥", "สมาชิก",    "members"),
    ("💬", "แชท",       "chat"),
    ("👤", "บัญชีฉัน",  "account"),
]

nav_cols = st.columns(len(menu_items))
for col, (icon, label, key) in zip(nav_cols, menu_items):
    badge = f" 🔴{notif_count}" if key == "chat" and notif_count > 0 else ""
    is_active = st.session_state["active_menu"] == key
    btn_type = "primary" if is_active else "secondary"
    if col.button(f"{icon} {label}{badge}", key=f"nav_{key}", type=btn_type, use_container_width=True):
        st.session_state["active_menu"] = key
        st.rerun()

st.markdown("<hr style='margin:0 0 16px 0;border-color:#dadde1;'>", unsafe_allow_html=True)

active_menu = st.session_state["active_menu"]

# ══════════════════════════════════════════════════════════════
# PAGE: หน้าหลัก
# ══════════════════════════════════════════════════════════════
if active_menu == "home":
    if not me:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;background:#fff;border-radius:12px;border:1px solid #dadde1;">
          <div style="font-size:64px;">✈️</div>
          <h2 style="color:#1c1e21;">Trip Expense Splitter</h2>
          <p style="color:#65676b;">ไปที่ <b>บัญชีฉัน</b> เพื่อเข้าสู่ระบบก่อนเริ่มใช้งาน</p>
        </div>""", unsafe_allow_html=True)
    elif not trip_id or not current_trip:
        st.info("ไปที่ **Events** เพื่อสร้างหรือเลือก Event ก่อนครับ")
    else:
        has_date = current_trip_date and str(current_trip_date).strip()
        st.markdown(f"""
        <div class="fb-card" style="display:flex;align-items:center;gap:16px;">
          <div style="width:56px;height:56px;border-radius:50%;background:#1877f2;
                      display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0;">✈️</div>
          <div>
            <h2 style="margin:0;color:#1c1e21;">{current_trip}</h2>
            <p style="margin:0;color:#65676b;font-size:14px;">
              {'📅 ' + str(current_trip_date) if has_date else ''} &nbsp;·&nbsp; 👥 {len(existing_members)} สมาชิก
            </p>
          </div>
        </div>""", unsafe_allow_html=True)

        # Quick bill tabs
        tab1, tab2, tab3 = st.tabs(["📝 เพิ่มบิล", "📊 ประวัติบิล", "💰 สรุปเคลียร์เงิน"])

        # ── TAB 1: ADD BILL ──────────────────────────────────────
        with tab1:
            if not existing_members:
                st.warning("ยังไม่มีสมาชิกใน Event — ไปที่เมนู **สมาชิก** เพื่อเพิ่มก่อนครับ")
            else:
                with st.form("add_bill", clear_on_submit=True):
                    st.markdown("### ➕ เพิ่มรายการบิล")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        desc = st.text_input("📌 รายการ:", placeholder="เช่น ค่าอาหาร, ค่าแท็กซี่...")
                        amt  = st.number_input("💰 จำนวนเงิน (บาท):", min_value=0.0, step=10.0)
                    with col_b:
                        my_idx = existing_members.index(me) if me in existing_members else 0
                        payer  = st.selectbox("👤 คนสำรองจ่าย:", existing_members, index=my_idx)
                        file   = st.file_uploader("📎 แนบสลิป:", type=['jpg','png','jpeg'])
                    st.markdown("**👥 เลือกคนที่ร่วมหาร:**")
                    ncols = min(len(existing_members), 5)
                    split_cols = st.columns(ncols)
                    split_to = []
                    for i, m in enumerate(existing_members):
                        if split_cols[i % ncols].checkbox(m, value=True, key=f"add_{m}"):
                            split_to.append(m)
                    if st.form_submit_button("💾 บันทึกบิล", type="primary", use_container_width=True):
                        if desc and amt > 0 and split_to:
                            blob = compress_image(file)
                            conn_ab = get_db_connection()
                            conn_ab.execute("INSERT INTO expenses (trip_id,description,amount,payer_name,split_members,image_blob) VALUES (?,?,?,?,?,?)",
                                            (trip_id, desc, amt, payer, ",".join(split_to), blob))
                            conn_ab.commit()
                            share = amt / len(split_to)
                            for member in split_to:
                                if member != payer:
                                    sys_msg = f"📌 บิลใหม่: '{desc}'\n💰 รวม {amt:,.2f} บาท | จ่ายโดย: {payer}\n💸 ส่วนของคุณ: {share:,.2f} บาท"
                                    conn_ab.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,'ระบบสรุปยอด',?,1,0,datetime('now','localtime'))",
                                                    (trip_id, member, sys_msg))
                            conn_ab.commit(); conn_ab.close()
                            st.success(f"✅ บันทึก '{desc}' แล้ว!")
                            time.sleep(0.8); st.rerun()
                        else:
                            st.error("⚠️ กรอกข้อมูลให้ครบ")

        # ── TAB 2: HISTORY ───────────────────────────────────────
        with tab2:
            conn_h = get_db_connection()
            expenses = conn_h.execute("SELECT * FROM expenses WHERE trip_id=?", (trip_id,)).fetchall()
            conn_h.close()
            if not expenses:
                st.info("ยังไม่มีบิล")
            else:
                for row in expenses:
                    s_list = row['split_members'].split(",")
                    share  = row['amount'] / len(s_list)
                    with st.expander(f"📌 {row['description']} — {row['amount']:,.2f} บาท  |  จ่ายโดย {row['payer_name']}"):
                        c1, c2 = st.columns([1,1.5])
                        with c1:
                            if row['image_blob']:
                                st.image(row['image_blob'], use_container_width=True, caption="สลิป")
                            else:
                                st.markdown('<div style="background:#f0f2f5;border-radius:8px;height:100px;display:flex;align-items:center;justify-content:center;color:#8a8d91;">ไม่มีสลิป</div>', unsafe_allow_html=True)
                            st.markdown(f"**หารกัน {len(s_list)} คน:** {', '.join(s_list)}")
                            st.markdown(f"**คนละ:** {share:,.2f} บาท")
                        with c2:
                            with st.form(f"edit_{row['id']}"):
                                u_desc = st.text_input("รายการ:", value=row['description'])
                                u_amt  = st.number_input("จำนวนเงิน:", value=row['amount'])
                                payer_opts = existing_members if row['payer_name'] in existing_members else existing_members+[row['payer_name']]
                                u_payer = st.selectbox("คนจ่าย:", payer_opts, index=payer_opts.index(row['payer_name']))
                                st.write("คนหาร:")
                                u_split = [m for m in payer_opts if st.checkbox(m, value=(m in row['split_members'].split(",")), key=f"ed_{row['id']}_{m}")]
                                u_file  = st.file_uploader("เปลี่ยนสลิป:", type=['jpg','png','jpeg'])
                                del_img = st.checkbox("🗑️ ลบรูป", key=f"delimg_{row['id']}")
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

        # ── TAB 3: SETTLE ────────────────────────────────────────
        with tab3:
            conn_s = get_db_connection()
            expenses_rows = conn_s.execute("SELECT * FROM expenses WHERE trip_id=?", (trip_id,)).fetchall()
            user_profiles = {r['name']: {"promptpay":r['promptpay'],"bank_name":r['bank_name'],"bank_acc":r['bank_account']}
                             for r in conn_s.execute("SELECT name,promptpay,bank_name,bank_account FROM all_users").fetchall()}
            conn_s.close()
            if not expenses_rows:
                st.info("ยังไม่มีบิลสำหรับคำนวณ")
            else:
                all_inv = set(existing_members)
                for r in expenses_rows:
                    all_inv.add(r['payer_name'])
                    all_inv.update(r['split_members'].split(","))
                net = {m: 0.0 for m in all_inv}
                for r in expenses_rows:
                    net[r['payer_name']] += r['amount']
                    s_l = r['split_members'].split(","); sh = r['amount']/len(s_l)
                    for m in s_l: net[m] -= sh

                st.markdown("### 📊 ยอดสรุปรายคน")
                cols_net = st.columns(min(len(all_inv), 4))
                for i,(m,b) in enumerate(net.items()):
                    color = "#31a24c" if b>0.01 else ("#fa3e3e" if b<-0.01 else "#1877f2")
                    icon  = "🟢" if b>0.01 else ("🔴" if b<-0.01 else "⚖️")
                    label = "รับคืน" if b>0.01 else ("ต้องจ่าย" if b<-0.01 else "เท่ากัน")
                    with cols_net[i%4]:
                        st.markdown(f"""<div style="background:#fff;border-radius:10px;padding:14px;border:1px solid #dadde1;text-align:center;border-top:4px solid {color};margin-bottom:8px;">
                          <div style="font-size:20px;">{icon}</div>
                          <div style="font-weight:700;font-size:14px;color:#1c1e21;">{m}</div>
                          <div style="font-size:12px;color:#65676b;">{label}</div>
                          <div style="font-weight:700;font-size:17px;color:{color};">{abs(b):,.2f} ฿</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("### 🚀 แผนการโอนเงิน")
                debtors   = [[m,b] for m,b in net.items() if b<-0.01]
                creditors = [[m,b] for m,b in net.items() if b>0.01]
                final_tx  = []
                while debtors and creditors:
                    amt_t = min(abs(debtors[0][1]), creditors[0][1])
                    d_n,c_n = debtors[0][0], creditors[0][0]
                    prof = user_profiles.get(c_n,{}); pp=(prof.get("promptpay") or "").strip()
                    b_nm=(prof.get("bank_name") or "").strip(); b_acc=(prof.get("bank_acc") or "").strip()
                    is_me_tx = (d_n == me)
                    border = "border:2px solid #1877f2;" if is_me_tx else "border:1px solid #dadde1;"
                    bg     = "background:#e7f3ff;" if is_me_tx else "background:#fff;"
                    badge  = '<span style="background:#1877f2;color:#fff;padding:2px 8px;border-radius:10px;font-size:12px;">⚠️ คุณ</span>' if is_me_tx else ""
                    st.markdown(f"""<div style="{bg}{border}border-radius:12px;padding:14px;margin-bottom:10px;">
                      <div style="font-size:15px;font-weight:600;color:#1c1e21;margin-bottom:8px;">
                        💳 <b>{d_n}</b> {badge} &nbsp;→&nbsp; 👉 <b>{c_n}</b> &nbsp;
                        <span style="background:#fa3e3e;color:#fff;padding:3px 12px;border-radius:20px;font-size:14px;">{amt_t:,.2f} ฿</span>
                      </div></div>""", unsafe_allow_html=True)
                    if pp or b_acc:
                        pay_c = st.columns(2)
                        if pp:
                            pay_c[0].markdown(f"📱 **พร้อมเพย์ {c_n}**"); pay_c[0].code(pp)
                        if b_acc:
                            pay_c[1].markdown(f"🏦 **{b_nm or 'บัญชี'} {c_n}**"); pay_c[1].code(b_acc)
                    else:
                        st.warning(f"⚠️ {c_n} ยังไม่ได้บันทึกบัญชี")
                    final_tx.append((d_n,c_n,amt_t))
                    debtors[0][1]+=amt_t; creditors[0][1]-=amt_t
                    if abs(debtors[0][1])<0.01: debtors.pop(0)
                    if abs(creditors[0][1])<0.01: creditors.pop(0)

                # LINE
                st.markdown("### 📲 แชร์ไป LINE")
                line_msg = f"📊 สรุปบิลทริป: {current_trip}\n"
                if current_trip_date and str(current_trip_date).strip(): line_msg+=f"📅 วันที่: {current_trip_date}\n"
                line_msg+="===============================\n📋 รายละเอียด\n-------------------------------\n"
                total_all=0.0
                for i,r in enumerate(expenses_rows,1):
                    s=r['split_members'].split(","); sh=r['amount']/len(s)
                    line_msg+=f"{i}. {r['description']}\n   💰 {r['amount']:,.2f} บาท | จ่ายโดย: {r['payer_name']}\n   คนละ {sh:,.2f} บาท\n"
                    total_all+=r['amount']
                line_msg+=f"-------------------------------\n💵 รวม: {total_all:,.2f} บาท\n===============================\n🚀 แผนโอนเงิน\n"
                for d_n,c_n,a_m in final_tx:
                    line_msg+=f"💳 {d_n} → {c_n} = {a_m:,.2f} บาท\n"
                    prof=user_profiles.get(c_n,{}); pp=(prof.get("promptpay") or "").strip(); b_nm=(prof.get("bank_name") or "").strip(); b_acc=(prof.get("bank_acc") or "").strip()
                    if pp: line_msg+=f"   📱 {pp}\n"
                    if b_acc: line_msg+=f"   🏦 {b_nm or 'บัญชี'}: {b_acc}\n"
                line_msg+="==============================="
                st.text_area("ข้อความ LINE:", value=line_msg, height=200, disabled=True)
                encoded=urllib.parse.quote(line_msg)
                st.link_button("🟢 เปิด LINE", f"https://line.me/R/msg/text/?{encoded}", type="primary", use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE: Events
# ══════════════════════════════════════════════════════════════
elif active_menu == "events":
    st.markdown("## 🗓️ จัดการ Events")
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### ➕ สร้าง Event ใหม่")
        with st.form("create_event"):
            new_trip_name = st.text_input("ชื่อ Event:", placeholder="เช่น ทริปเชียงใหม่").strip()
            new_trip_date = st.date_input("วันที่จัด:", value=datetime.today())
            if st.form_submit_button("สร้าง Event", type="primary", use_container_width=True):
                if new_trip_name:
                    try:
                        conn_ce = get_db_connection()
                        conn_ce.execute("INSERT INTO trips (name,status,trip_date) VALUES (?,0,?)",
                                        (new_trip_name, new_trip_date.strftime("%Y-%m-%d")))
                        conn_ce.commit(); conn_ce.close()
                        st.success(f"✅ สร้าง '{new_trip_name}' สำเร็จ!"); time.sleep(0.5); st.rerun()
                    except: st.error("❌ ชื่อ Event ซ้ำ")
                else: st.error("⚠️ กรอกชื่อ Event")

        if trip_id and current_trip:
            st.markdown(f"### ✏️ แก้ไข Event ปัจจุบัน: *{current_trip}*")
            with st.form("edit_event"):
                rename_input = st.text_input("ชื่อใหม่:", value=current_trip).strip()
                try: default_date = datetime.strptime(str(current_trip_date),"%Y-%m-%d") if current_trip_date and str(current_trip_date).strip() else datetime.today()
                except: default_date = datetime.today()
                re_date = st.date_input("วันที่:", value=default_date)
                if st.form_submit_button("💾 ยืนยัน", type="primary"):
                    if rename_input:
                        try:
                            conn_re = get_db_connection()
                            conn_re.execute("UPDATE trips SET name=?,trip_date=? WHERE id=?",
                                            (rename_input, re_date.strftime("%Y-%m-%d"), trip_id))
                            conn_re.commit(); conn_re.close()
                            st.success("✅ แก้ไขแล้ว!"); time.sleep(0.5); st.rerun()
                        except: st.error("❌ ชื่อซ้ำ")
            if st.button("🗑️ ลบ Event นี้สู่ถังขยะ", type="secondary"):
                conn_del = get_db_connection()
                conn_del.execute("UPDATE trips SET status=1 WHERE id=?", (trip_id,))
                conn_del.commit(); conn_del.close()
                st.session_state["selected_trip_id"] = None
                st.toast("🗑️ ย้ายสู่ถังขยะแล้ว"); time.sleep(0.5); st.rerun()

    with col_right:
        st.markdown("### 🗺️ เลือก Event")
        if trip_display_list:
            for i, (disp, tid) in enumerate(zip(trip_display_list, trip_id_list)):
                is_selected = (tid == trip_id)
                border = "border:2px solid #1877f2;background:#e7f3ff;" if is_selected else "border:1px solid #dadde1;background:#fff;"
                st.markdown(f'<div style="{border}border-radius:10px;padding:12px 16px;margin-bottom:8px;cursor:pointer;">'
                            f'<span style="font-weight:600;color:#1c1e21;">{"✅ " if is_selected else ""}✈️ {disp}</span></div>',
                            unsafe_allow_html=True)
                if not is_selected:
                    if st.button(f"เลือก", key=f"sel_trip_{tid}", use_container_width=True):
                        st.session_state["selected_trip_id"] = tid
                        st.rerun()
        else:
            st.info("ยังไม่มี Event — สร้างใหม่ได้เลย")

        st.markdown("### 🗑️ ถังขยะ")
        conn_tr = get_db_connection()
        deleted_trips = conn_tr.execute("SELECT * FROM trips WHERE status=1").fetchall()
        if not deleted_trips:
            st.caption("ถังขยะว่างเปล่า")
        else:
            for dt in deleted_trips:
                has_dt = dt['trip_date'] and str(dt['trip_date']).strip()
                disp_del = f"{dt['name']} ({dt['trip_date']})" if has_dt else dt['name']
                c1,c2,c3 = st.columns([3,1,1])
                c1.write(disp_del)
                if c2.button("กู้คืน", key=f"res_{dt['id']}"):
                    conn_tr.execute("UPDATE trips SET status=0 WHERE id=?", (dt['id'],))
                    conn_tr.commit(); st.toast("🔄 กู้คืนแล้ว!"); time.sleep(0.5); st.rerun()
                if c3.button("ลบถาวร", key=f"pdel_{dt['id']}"):
                    for tbl in ["settlements","expenses","members","notifications"]:
                        conn_tr.execute(f"DELETE FROM {tbl} WHERE trip_id=?", (dt['id'],))
                    conn_tr.execute("DELETE FROM trips WHERE id=?", (dt['id'],))
                    conn_tr.commit(); st.toast("💥 ลบถาวร!"); time.sleep(0.5); st.rerun()
        conn_tr.close()

# ══════════════════════════════════════════════════════════════
# PAGE: สมาชิก
# ══════════════════════════════════════════════════════════════
elif active_menu == "members":
    st.markdown("## 👥 สมาชิกใน Event")
    if not trip_id:
        st.warning("กรุณาเลือก Event ก่อนที่เมนู Events")
    else:
        col_ml, col_mr = st.columns([1,1])
        available_users = [u for u in existing_all_users if u not in existing_members]

        with col_ml:
            st.markdown(f"### สมาชิกใน *{current_trip}* ({len(existing_members)} คน)")
            if existing_members:
                conn_ml = get_db_connection()
                for member in existing_members:
                    unread_row = conn_ml.execute("SELECT COUNT(*) as cnt FROM notifications WHERE trip_id=? AND to_user=? AND is_read=0",
                                                 (trip_id,member)).fetchone()
                    unread_cnt = unread_row["cnt"] if unread_row else 0
                    is_on = member in online_users
                    dot = "🟢" if is_on else "⚪"
                    badge_html = f'<span class="fb-badge">{unread_cnt}</span>' if unread_cnt > 0 else ""
                    you_tag = " <i>(คุณ)</i>" if member == me else ""
                    mc1, mc2 = st.columns([5,1])
                    mc1.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f5;">
                      <div style="width:36px;height:36px;border-radius:50%;background:#1877f2;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;flex-shrink:0;">{member[0].upper()}</div>
                      <div><div style="font-weight:600;font-size:14px;">{dot} {member}{you_tag}{badge_html}</div>
                      <div style="font-size:12px;color:#65676b;">{'ออนไลน์' if is_on else 'ออฟไลน์'}</div></div>
                    </div>""", unsafe_allow_html=True)
                    if mc2.button("ออก", key=f"rm_{member}"):
                        conn_ml.execute("DELETE FROM members WHERE trip_id=? AND name=?", (trip_id,member))
                        conn_ml.commit(); st.toast(f"ถอด {member}"); time.sleep(0.5); st.rerun()
                conn_ml.close()
            else:
                st.info("ยังไม่มีสมาชิกในกลุ่มนี้")

        with col_mr:
            st.markdown("### ➕ เชิญเพื่อนเข้าร่วม")
            if available_users:
                sel_user = st.selectbox("เลือกเพื่อนออนไลน์:", available_users)
                if st.button("➕ เพิ่มเข้ากลุ่ม", type="primary", use_container_width=True):
                    conn_am = get_db_connection()
                    conn_am.execute("INSERT INTO members (trip_id,name) VALUES (?,?)", (trip_id,sel_user))
                    conn_am.commit(); conn_am.close()
                    st.toast(f"✅ เพิ่ม {sel_user}"); time.sleep(0.5); st.rerun()
            else:
                st.info("สมาชิกทุกคนในระบบอยู่ในกลุ่มแล้ว")

            st.markdown("### 🌐 ออนไลน์ขณะนี้")
            if online_users:
                for u in online_users:
                    you = " *(คุณ)*" if u == me else ""
                    st.markdown(f"🟢 **{u}**{you}")
            else:
                st.caption("ไม่มีใครออนไลน์")

# ══════════════════════════════════════════════════════════════
# PAGE: แชท (Messenger style)
# ══════════════════════════════════════════════════════════════
elif active_menu == "chat":
    st.markdown("## 💬 Messenger")
    if not me:
        st.warning("กรุณาเข้าสู่ระบบที่เมนู **บัญชีฉัน** ก่อน")
    elif not trip_id:
        st.warning("กรุณาเลือก Event ก่อน")
    else:
        conn_ch = get_db_connection()
        all_chat_rows = conn_ch.execute(
            """SELECT * FROM notifications WHERE trip_id=?
               AND (to_user=? OR from_user=? OR (to_user=? AND is_auto=1))
               ORDER BY timestamp ASC, id ASC""",
            (trip_id, me, me, me)).fetchall()
        conn_ch.close()

        chat_groups = {}; unread_status = {}
        for n in all_chat_rows:
            partner = "🤖 ระบบ" if (n['is_auto']==1 or n['from_user']=="ระบบสรุปยอด") \
                      else (n['from_user'] if n['to_user']==me else n['to_user'])
            if partner not in chat_groups: chat_groups[partner]=[]; unread_status[partner]=0
            chat_groups[partner].append(n)
            if n['to_user']==me and n['is_read']==0: unread_status[partner]+=1

        col_chat_list, col_chat_main = st.columns([1, 2.5])

        with col_chat_list:
            st.markdown("### 💬 การสนทนา")
            if not chat_groups:
                st.caption("ยังไม่มีการสนทนา")
            for partner in chat_groups:
                unread = unread_status[partner]
                badge  = f" 🔴{unread}" if unread>0 else ""
                init   = partner[0].upper()
                if st.button(f"{init}  {partner}{badge}", key=f"chat_sel_{partner}", use_container_width=True):
                    st.session_state["chat_partner"] = partner
                    st.rerun()

            st.markdown("---")
            st.markdown("**📝 เริ่มแชทใหม่**")
            other_members = [m for m in existing_members if m != me]
            if other_members:
                with st.form("new_chat_form", clear_on_submit=True):
                    new_to   = st.selectbox("ถึง:", other_members)
                    new_msg  = st.text_input("", placeholder="พิมพ์ข้อความ...", label_visibility="collapsed")
                    c_s, c_l = st.columns([3,1])
                    if c_s.form_submit_button("ส่ง ▶", type="primary", use_container_width=True):
                        if new_msg.strip():
                            conn_ns = get_db_connection()
                            conn_ns.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                            (trip_id, new_to, me, new_msg.strip()))
                            conn_ns.commit(); conn_ns.close()
                            st.session_state["chat_partner"] = new_to
                            st.rerun()
                    if c_l.form_submit_button("👍"):
                        conn_ns = get_db_connection()
                        conn_ns.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                        (trip_id, new_to, me, "👍"))
                        conn_ns.commit(); conn_ns.close()
                        st.session_state["chat_partner"] = new_to
                        st.rerun()
            else:
                st.caption("ไม่มีสมาชิกอื่น")

        with col_chat_main:
            partner = st.session_state.get("chat_partner")
            if not partner:
                st.markdown("""
                <div style="text-align:center;padding:80px;background:#fff;border-radius:12px;border:1px solid #dadde1;">
                  <div style="font-size:48px;">💬</div>
                  <p style="color:#65676b;font-size:16px;">เลือกการสนทนาทางซ้าย หรือเริ่มแชทใหม่</p>
                </div>""", unsafe_allow_html=True)
            elif partner not in chat_groups and partner not in [m for m in existing_members]:
                st.info("เลือกการสนทนาจากรายการซ้ายมือ")
            else:
                messages = chat_groups.get(partner, [])
                unread = unread_status.get(partner, 0)

                # Mark as read
                if unread > 0:
                    conn_rd = get_db_connection()
                    if partner == "🤖 ระบบ":
                        conn_rd.execute("UPDATE notifications SET is_read=1 WHERE trip_id=? AND to_user=? AND is_auto=1 AND is_read=0", (trip_id,me))
                    else:
                        conn_rd.execute("UPDATE notifications SET is_read=1 WHERE trip_id=? AND to_user=? AND from_user=? AND is_read=0", (trip_id,me,partner))
                    conn_rd.commit(); conn_rd.close()

                # Header
                init_p = partner[0].upper()
                is_on_p = partner in online_users
                st.markdown(f"""
                <div style="background:#fff;border:1px solid #dadde1;border-radius:10px 10px 0 0;
                            padding:12px 16px;display:flex;align-items:center;gap:12px;">
                  <div style="width:40px;height:40px;border-radius:50%;background:#1877f2;
                              display:flex;align-items:center;justify-content:center;
                              color:#fff;font-weight:700;font-size:16px;">{init_p}</div>
                  <div>
                    <div style="font-weight:700;font-size:16px;color:#1c1e21;">{partner}</div>
                    <div style="font-size:12px;color:{'#31a24c' if is_on_p else '#8a8d91'};">
                      {'🟢 ออนไลน์' if is_on_p else '⚪ ออฟไลน์'}
                    </div>
                  </div>
                  <div style="margin-left:auto;display:flex;gap:16px;font-size:20px;color:#1877f2;">
                    <span>📞</span><span>📹</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Chat body
                bubbles_html = '<div class="fb-chat-body">'
                for notif in messages:
                    ts = ""
                    if notif['timestamp']:
                        try: ts = datetime.strptime(notif['timestamp'],"%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                        except: ts = str(notif['timestamp'])[11:16]
                    is_mine = (notif['from_user']==me and notif['is_auto']==0)
                    is_sys  = (notif['is_auto']==1 or notif['from_user']=="ระบบสรุปยอด")
                    msg_txt = notif['message'].replace('\n','<br>')

                    if is_sys:
                        bubbles_html += f'<div style="align-self:center;margin:6px 0;width:100%;"><div class="fb-bubble-sys">{msg_txt}</div><div class="fb-bubble-time" style="text-align:center;">{ts}</div></div>'
                    elif is_mine:
                        bubbles_html += f'<div style="display:flex;flex-direction:column;align-items:flex-end;margin:3px 0;"><div class="fb-bubble-out">{msg_txt}</div><div class="fb-bubble-time">{ts}</div></div>'
                    else:
                        bubbles_html += f'<div style="display:flex;flex-direction:column;align-items:flex-start;margin:3px 0;"><div class="fb-sender-name">{notif["from_user"]}</div><div class="fb-bubble-in">{msg_txt}</div><div class="fb-bubble-time left">{ts}</div></div>'
                bubbles_html += '</div>'
                st.markdown(bubbles_html, unsafe_allow_html=True)

                # Reply form
                if partner != "🤖 ระบบ":
                    with st.form(key=f"reply_{partner}", clear_on_submit=True):
                        col_in, col_btn, col_like = st.columns([6,1,1])
                        reply_txt = col_in.text_input("", placeholder=f"Aa  พิมพ์ข้อความถึง {partner}...", label_visibility="collapsed")
                        sent  = col_btn.form_submit_button("▶", type="primary", use_container_width=True)
                        liked = col_like.form_submit_button("👍", use_container_width=True)
                        if sent and reply_txt.strip():
                            conn_r = get_db_connection()
                            conn_r.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                           (trip_id, partner, me, reply_txt.strip()))
                            conn_r.commit(); conn_r.close(); st.rerun()
                        if liked:
                            conn_r = get_db_connection()
                            conn_r.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",
                                           (trip_id, partner, me, "👍"))
                            conn_r.commit(); conn_r.close(); st.rerun()

                # Delete messages
                if messages:
                    with st.expander("🗑️ ลบข้อความ"):
                        for notif in messages:
                            short = notif['message'][:40]+"..." if len(notif['message'])>40 else notif['message']
                            dc1,dc2 = st.columns([4,1])
                            dc1.caption(f"[{notif['from_user']}] {short}")
                            if dc2.button("ลบ", key=f"del_n_{notif['id']}"):
                                conn_dn = get_db_connection()
                                conn_dn.execute("DELETE FROM notifications WHERE id=?", (notif['id'],))
                                conn_dn.commit(); conn_dn.close()
                                st.rerun()

# ══════════════════════════════════════════════════════════════
# PAGE: บัญชีฉัน
# ══════════════════════════════════════════════════════════════
elif active_menu == "account":
    st.markdown("## 👤 บัญชีของฉัน")
    col_acc_l, col_acc_r = st.columns([1,1])

    with col_acc_l:
        if me is None:
            st.markdown("### 🔐 เข้าสู่ระบบ")
            login_mode = st.radio("", ["เลือกโปรไฟล์", "สร้างบัญชีใหม่"], horizontal=True)
            if login_mode == "เลือกโปรไฟล์":
                if existing_all_users:
                    user_select = st.selectbox("ชื่อของคุณ:", existing_all_users)
                    if st.button("เข้าสู่ระบบ", type="primary", use_container_width=True):
                        st.session_state["current_online_user"] = user_select
                        update_online_heartbeat(user_select)
                        st.toast(f"👋 ยินดีต้อนรับ, {user_select}!")
                        time.sleep(0.5); st.rerun()
                else:
                    st.caption("ยังไม่มีบัญชี กรุณาสร้างใหม่")
            else:
                new_name = st.text_input("ชื่อเล่น:", placeholder="ระบุชื่อของคุณ").strip()
                if st.button("สร้างบัญชี", type="primary", use_container_width=True):
                    if new_name:
                        try:
                            conn_nu = get_db_connection()
                            conn_nu.execute("INSERT INTO all_users (name) VALUES (?)", (new_name,))
                            conn_nu.commit(); conn_nu.close()
                            st.session_state["current_online_user"] = new_name
                            update_online_heartbeat(new_name)
                            time.sleep(0.5); st.rerun()
                        except: st.error("❌ ชื่อนี้มีในระบบแล้ว")
                    else: st.error("⚠️ กรอกชื่อก่อน")
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:16px;background:#fff;
                        border-radius:12px;padding:20px;border:1px solid #dadde1;margin-bottom:16px;">
              <div style="width:64px;height:64px;border-radius:50%;background:#1877f2;
                          display:flex;align-items:center;justify-content:center;
                          color:#fff;font-weight:700;font-size:28px;">{me[0].upper()}</div>
              <div>
                <div style="font-weight:700;font-size:20px;color:#1c1e21;">{me}</div>
                <div style="font-size:14px;color:#31a24c;font-weight:500;">🟢 ออนไลน์</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            conn_my = get_db_connection()
            my_data = conn_my.execute("SELECT * FROM all_users WHERE name=?", (me,)).fetchone()
            conn_my.close()

            st.markdown("### ⚙️ ข้อมูลการรับเงิน")
            with st.form("edit_profile"):
                edit_pp  = st.text_input("📱 เลขพร้อมเพย์:", value=my_data['promptpay'] or "", placeholder="เบอร์โทร หรือ เลขบัตร 13 หลัก")
                db_bank  = my_data['bank_name'] or "-- เลือกธนาคาร --"
                bank_idx = BANK_LIST.index(db_bank) if db_bank in BANK_LIST else 0
                edit_bank_name = st.selectbox("🏦 ธนาคาร:", BANK_LIST, index=bank_idx)
                edit_bank_acc  = st.text_input("🔢 เลขบัญชี:", value=my_data['bank_account'] or "")
                if st.form_submit_button("💾 บันทึก", type="primary", use_container_width=True):
                    final_bank = edit_bank_name if edit_bank_name != "-- เลือกธนาคาร --" else ""
                    conn_sp = get_db_connection()
                    conn_sp.execute("UPDATE all_users SET promptpay=?,bank_name=?,bank_account=? WHERE name=?",
                                    (edit_pp, final_bank, edit_bank_acc, me))
                    conn_sp.commit(); conn_sp.close()
                    st.toast("💾 บันทึกแล้ว!"); time.sleep(0.5); st.rerun()

            if st.button("🚪 ออกจากระบบ", type="secondary", use_container_width=True):
                conn_lo = get_db_connection()
                conn_lo.execute("DELETE FROM online_status WHERE name=?", (me,))
                conn_lo.commit(); conn_lo.close()
                st.session_state["current_online_user"] = None; st.rerun()

    with col_acc_r:
        st.markdown("### 🌐 สมาชิกทั้งหมดในระบบ")
        if existing_all_users:
            for u in existing_all_users:
                is_on = u in online_users
                dot = "🟢" if is_on else "⚪"
                you = " *(คุณ)*" if u == me else ""
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f5;">
                  <div style="width:34px;height:34px;border-radius:50%;background:#{'1877f2' if is_on else 'bcc0c4'};
                              display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;">{u[0].upper()}</div>
                  <div><div style="font-weight:600;font-size:14px;color:#1c1e21;">{u}{you}</div>
                  <div style="font-size:12px;color:#65676b;">{dot} {'ออนไลน์' if is_on else 'ออฟไลน์'}</div></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("ยังไม่มีสมาชิกในระบบ")
