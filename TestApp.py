import streamlit as st
import pandas as pd
import sqlite3
import io
from PIL import Image
import time
import urllib.parse
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Trip Expense Splitter", layout="wide",
                   page_icon="✈️", initial_sidebar_state="collapsed")

# [FIX v2] ย้าย st_autorefresh() ไปไว้ในคอนเทนเนอร์ซ่อน (ดูท้ายบล็อก CSS)
#          เพราะ st_autorefresh เป็น custom component → Streamlit จะ render
#          <iframe> สีขาวจริง ๆ ลงในหน้า ซึ่งคือ "แถบขาว" ที่โผล่ด้านบน

# ─────────────────────────────────────────────────────────────
# CSS  — blue theme, black text, fixed header, mobile-ready
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ══ LIGHT MODE FORCE ══ */
:root { color-scheme: light only !important; }
html, body { color-scheme: light !important; background: #dbeafe !important; }

/* ══ [FIX v2] ซ่อน TOOLBAR มุมขวาบน ══
   ใช้แค่ display:none — ของเดิมที่ใส่ height:0/width:0 พร้อมกันทำให้ลูกที่ถูก
   portal ออกมาหลุดตำแหน่ง กลายเป็นกล่องขาวลอยแทนที่จะหายไป
   หมายเหตุ: CSS อย่างเดียวเอาไม่อยู่ทุก version → มี JS ลบซ้ำที่ท้ายบล็อกนี้ */
[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stConnectionStatus"],
[data-testid="stMainMenu"],
[data-testid="stDecoration"],
[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
.stAppToolbar,
.stAppDeployButton,
.stDeployButton,
#MainMenu, header, footer {
    display: none !important;
}

/* ══ [FIX v2] คอนเทนเนอร์ซ่อนสำหรับ component ที่ไม่มี UI ══
   (st_autorefresh + ตัวฉีด JS) — ห้ามใช้ display:none เพราะ browser จะ
   throttle timer ใน iframe ที่ถูกซ่อนแบบนั้น → autorefresh จะหยุดทำงาน
   จึงใช้วิธีหลุดออกจาก layout flow + opacity 0 แทน */
div.st-key-hidden_utils {
    position: fixed !important;
    top: 0 !important; left: 0 !important;
    width: 1px !important; height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -1 !important;
    margin: 0 !important; padding: 0 !important;
}
div.st-key-hidden_utils iframe {
    width: 1px !important; height: 1px !important;
    border: none !important; display: block !important;
}

/* ══ GLOBAL FONT & BG ══ */
html,body,
[data-testid="stAppViewContainer"],
[data-testid="stMainBlockContainer"],
[data-testid="stMain"] {
    background: #dbeafe !important;
    font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important;
    padding-top: 0 !important;
}
[data-testid="stMainBlockContainer"] { max-width: 100% !important; }

/* ══ NAVBAR (fixed at top) ══ */
.navbar-wrap {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 2147483647;   /* [FIX v3] สูงสุดเท่าที่ browser รับได้ */
    font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}
.navbar-wrap .navbar {
    background: #1d4ed8;
    display: flex; align-items: center;
    height: 50px; padding: 0 12px; gap: 8px;
    padding-right: 250px;   /* [FIX v7] เว้นที่ให้กลุ่ม ป้าย+ปุ่มโปรไฟล์ ที่ลอยทับอยู่ */
    box-shadow: 0 2px 6px rgba(0,0,0,.3);
}

/* ══ [FIX v5/v6] ปุ่มโปรไฟล์มุมขวาบน (แทนเมนู "บัญชี" เดิม) ══
   [FIX v6] ใช้ selector แบบ descendant (ไม่ใช่ "> button") เพราะถ้าใส่ help=
   ให้ st.button, Streamlit จะห่อปุ่มด้วย tooltip wrapper อีกชั้น → "> button"
   หลุด match → ปุ่มกลับไปใช้สีส้ม default ของ Streamlit
   สี / อักษรย่อ / รูปโปรไฟล์ ส่งเข้ามาทาง CSS variable จากฝั่ง Python */
div.st-key-userbtn {
    position: fixed !important;
    top: 8px !important;
    right: 12px !important;
    left: auto !important;
    width: auto !important;
    display: inline-flex !important;
    z-index: 2147483647 !important;
    margin: 0 !important; padding: 0 !important;
}
/* [FIX v7] เรียงลูกในคอนเทนเนอร์แนวนอน: [ป้ายออนไลน์][ป้ายแจ้งเตือน][ปุ่มโปรไฟล์]
   ทำแบบนี้แทนการเว้นระยะใน navbar เพราะความกว้างปุ่มเปลี่ยนตามความยาวชื่อ
   การเว้นระยะตายตัวจึงเหลือช่องว่างเสมอ
   [FIX v8] ต้องสั่ง flex-direction:row ให้ "ทุกชั้น" เพราะ Streamlit ใส่ class
   st-key-* ไว้คนละชั้นกันแล้วแต่ version — บาง version อยู่ที่ตัว
   stVerticalBlock เอง บาง version อยู่ที่ wrapper ชั้นนอก ถ้าสั่งผิดชั้น
   ชั้นที่ถือลูกจริงจะยังเป็น column อยู่ → ปุ่มตกลงไปทับแถบเมนูข้างล่าง */
div.st-key-userbtn,
div.st-key-userbtn > div,
div.st-key-userbtn > div > div,
div.st-key-userbtn [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: flex-end !important;
    gap: 8px !important;
    width: auto !important;
    max-width: none !important;
}
div.st-key-userbtn [data-testid="stElementContainer"],
div.st-key-userbtn [data-testid="stMarkdownContainer"],
div.st-key-userbtn .stButton { width: auto !important; margin: 0 !important; flex: 0 0 auto !important; }

/* [FIX v8] กลไกสำรอง — ดึงป้ายออกจาก flow ไปวางชิดซ้ายของปุ่มโดยตรง
   วิธีนี้ไม่พึ่ง flex-direction เลย ต่อให้ selector ด้านบนพลาดทุกชั้น
   ปุ่มก็ยังเป็นลูกเดียวใน flow → ไม่มีทางถูกดันตกลงไปแถวล่าง */
div.st-key-userbtn [data-testid="stElementContainer"]:has(.nb-badges) {
    position: absolute !important;
    right: 100% !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    margin-right: 8px !important;
}

div.st-key-userbtn button {
    position: relative !important;
    display: inline-flex !important;
    align-items: center !important;
    width: auto !important;          /* [FIX v6] พอดีตัวอักษร ไม่ยืดเต็มกรอบ */
    min-width: 0 !important;
    max-width: 150px !important;
    height: 32px !important;
    padding: 0 11px 0 3px !important;
    gap: 0 !important;
    border-radius: 20px !important;
    background: var(--nb-main, #f97316) !important;
    border: 1.5px solid var(--nb-line, #fdba74) !important;
    color: #fff !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    transition: filter .15s !important;
}
div.st-key-userbtn button * { color: #fff !important; }
div.st-key-userbtn button p {
    margin: 0 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}
/* วงกลม avatar — ใช้รูปถ้ามี (--nb-img) ไม่มีก็ใช้อักษรตัวแรก (--nb-av) */
div.st-key-userbtn button::before {
    content: var(--nb-av, "?");
    flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    width: 24px; height: 24px; border-radius: 50%;
    margin-right: 7px;
    background-color: rgba(255,255,255,.28);
    background-image: var(--nb-img, none);
    background-size: cover;
    background-position: center;
    border: 1.5px solid rgba(255,255,255,.65);
    font-size: 11.5px; font-weight: 800; line-height: 1;
}
div.st-key-userbtn button:hover { filter: brightness(1.12) !important; }
/* กำลังเปิดหน้าบัญชีอยู่ → ใส่ขอบขาวรอบนอกให้รู้ว่า active */
div.st-key-userbtn button[kind="primary"] {
    box-shadow: 0 0 0 2px #fff !important;
}
.navbar-wrap .navbar * { color: #fff !important; }
.navbar-wrap .nb-icon  { font-size: 20px; flex-shrink:0; }
.navbar-wrap .nb-title { font-weight:800; font-size:15px; white-space:nowrap; flex-shrink:0; }
.navbar-wrap .nb-trip  {
    background: rgba(255,255,255,.2); border:1px solid rgba(255,255,255,.35);
    border-radius:20px; padding:2px 10px; font-size:12px; font-weight:600;
    max-width:150px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex-shrink:1;
}
.navbar-wrap .nb-spacer { flex:1; }
/* [FIX v7] ป้ายออนไลน์/แจ้งเตือน — ย้ายออกจาก navbar ไปอยู่ในกลุ่มเดียวกับ
   ปุ่มโปรไฟล์ จึงต้องเป็น selector ระดับ global ไม่ผูกกับ .navbar-wrap */
.nb-badge-g, .nb-badge-r {
    display:inline-block; color:#fff !important;
    border-radius:20px; padding:2px 8px;
    font-size:11px; font-weight:700; line-height:17px;
    white-space:nowrap; flex-shrink:0;
}
.nb-badge-g { background:#16a34a; }
.nb-badge-r { background:#dc2626; }
.nb-badges  { display:flex; align-items:center; gap:6px; }
.nb-badges p { margin:0 !important; }
.navbar-wrap .nb-avatar {
    width:28px; height:28px; border-radius:50%;
    background:rgba(255,255,255,.25); border:2px solid rgba(255,255,255,.5);
    display:flex; align-items:center; justify-content:center;
    font-weight:800; font-size:13px; flex-shrink:0;
}
.navbar-wrap .nb-name {
    font-size:12px; font-weight:600;
    max-width:65px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex-shrink:1;
}

/* ══ MENUBAR — anchored to a real, stable Streamlit container via key="menubar" ══ */
div.st-key-menubar {
    position: fixed !important;
    top: 50px !important;
    left: 0 !important; right: 0 !important;
    z-index: 2147483646 !important;   /* [FIX v3] */
    background: #1e3a8a !important;
    padding: 0 !important; margin: 0 !important;
    border-bottom: 3px solid #60a5fa !important;
    width: 100% !important;
}
div.st-key-menubar div[data-testid="stHorizontalBlock"] {
    gap: 0 !important; margin: 0 !important; padding: 0 !important;
}
div.st-key-menubar div[data-testid="column"] {
    padding: 0 !important; flex: 1 !important; min-width: 0 !important;
}
div.st-key-menubar .stButton { margin: 0 !important; }
div.st-key-menubar .stButton > button {
    border-radius: 0 !important;
    height: 44px !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    padding: 0 2px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    width: 100% !important;
}
div.st-key-menubar .stButton > button[kind="secondary"] {
    background: #1e3a8a !important; color: #93c5fd !important;
}
div.st-key-menubar .stButton > button[kind="secondary"] p {
    color: #93c5fd !important;
}
div.st-key-menubar .stButton > button[kind="primary"] {
    background: #1d4ed8 !important; color: #fff !important;
    border-bottom: 3px solid #60a5fa !important;
}
div.st-key-menubar .stButton > button[kind="primary"] p {
    color: #fff !important;
}

/* ══ PUSH CONTENT DOWN so fixed header doesn't cover it ══
   [FIX] เดิมมี .main .block-container{padding-top:8rem} ซ้อนกับ
   .block-container{padding-top:106px} → specificity ชนกัน ทำให้ระยะเพี้ยน
   ตอนนี้ประกาศค่าเดียวคุมทั้งสองตัวเลือก */
.block-container,
.main .block-container {
    padding-top: 106px !important;   /* navbar(50) + menubar(44) + gap(12) */
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}
@media (max-width:600px) {
    .block-container, .main .block-container {
        padding-left:.5rem !important; padding-right:.5rem !important;
    }
    .navbar-wrap .nb-title { display:none; }
    .navbar-wrap .nb-trip  { max-width:100px; }
    .navbar-wrap .navbar   { padding-right:206px; }        /* [FIX v7] */
    div.st-key-userbtn button { max-width:104px !important; }
}

/* ══ STREAMLIT BUTTON (non-nav) ══ */
.stButton > button {
    border-radius: 8px !important; font-weight:700 !important;
    font-size:13px !important; padding:8px 12px !important;
    border: 1.5px solid #93c5fd !important;
    transition: all .15s !important;
}
.stButton > button[kind="primary"] {
    background:#1d4ed8 !important; color:#fff !important; border-color:#1d4ed8 !important;
}
.stButton > button[kind="primary"] * { color:#fff !important; }
.stButton > button[kind="primary"]:hover { background:#1e40af !important; }
.stButton > button[kind="secondary"] {
    background:#eff6ff !important; color:#1e40af !important; border-color:#93c5fd !important;
}
.stButton > button[kind="secondary"] * { color:#1e40af !important; }
.stButton > button[kind="secondary"]:hover { background:#dbeafe !important; }

/* ══ INPUTS ══ */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background:#fff !important; color:#000 !important;
    border:1.5px solid #93c5fd !important; border-radius:8px !important;
    font-size:14px !important; padding:8px 12px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color:#1d4ed8 !important;
    box-shadow:0 0 0 3px rgba(29,78,216,.12) !important; background:#fff !important;
}
[data-testid="stTextInput"] label,[data-testid="stNumberInput"] label,
[data-testid="stTextArea"] label,[data-testid="stSelectbox"] label,
[data-testid="stDateInput"] label,[data-testid="stFileUploader"] label,
[data-testid="stCheckbox"] label p,[data-testid="stRadio"] label p {
    color:#000 !important; font-weight:500 !important; font-size:14px !important;
}
[data-testid="stSelectbox"] > div > div {
    background:#fff !important; color:#000 !important;
    border:1.5px solid #93c5fd !important; border-radius:8px !important;
}

/* ══ TABS (content area tabs, not nav) ══ */
[data-testid="stTabs"] [role="tablist"] {
    background:#eff6ff !important; border-bottom:2px solid #93c5fd !important;
    border-radius:8px 8px 0 0 !important; padding:0 4px !important; overflow-x:auto !important;
}
[data-testid="stTabs"] [role="tab"] {
    color:#1e40af !important; font-weight:700 !important; font-size:13px !important;
    padding:10px 14px !important; border-bottom:3px solid transparent !important; white-space:nowrap !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color:#1d4ed8 !important; border-bottom-color:#1d4ed8 !important; background:#fff !important;
}

/* ══ EXPANDERS ══ */
[data-testid="stExpander"] {
    background:#fff !important; border:1.5px solid #bfdbfe !important;
    border-radius:10px !important; margin-bottom:10px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * { color:#000 !important; font-weight:600 !important; }

/* ══ ALERTS ══ */
[data-testid="stAlert"] { border-radius:10px !important; }
[data-testid="stAlert"] p,[data-testid="stAlert"] span { color:#000 !important; }

/* ══ TEXT ══ */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color:#000 !important; }
[data-testid="stCaptionContainer"] p { color:#374151 !important; }

/* ══ CARDS ══ */
.card {
    background:#fff; border:1.5px solid #bfdbfe; border-radius:12px;
    padding:16px; margin-bottom:14px;
}
.card * { color:#000 !important; }
.section-head {
    font-size:15px; font-weight:800; color:#000 !important;
    padding:10px 0 8px; border-bottom:2px solid #bfdbfe; margin-bottom:12px;
}

/* ══ CHAT BUBBLES ══ */
.fb-bubble-out {
    align-self:flex-end; background:#1d4ed8; color:#fff !important;
    padding:9px 14px; border-radius:18px 18px 4px 18px;
    max-width:78%; font-size:14px; line-height:1.5; word-break:break-word;
}
.fb-bubble-out * { color:#fff !important; }
.fb-bubble-in {
    align-self:flex-start; background:#eff6ff; color:#000 !important;
    padding:9px 14px; border-radius:18px 18px 18px 4px;
    max-width:78%; font-size:14px; line-height:1.5; word-break:break-word;
    border:1px solid #bfdbfe;
}
.fb-bubble-in * { color:#000 !important; }
.fb-bubble-sys {
    background:#dbeafe; color:#1e40af !important;
    padding:8px 14px; border-radius:10px; font-size:13px;
    border-left:3px solid #1d4ed8; line-height:1.5; word-break:break-word; width:100%;
}
.fb-bubble-sys * { color:#1e40af !important; }
.fb-bubble-time { font-size:11px; color:#6b7280 !important; margin-top:3px; }
.fb-bubble-time.r { text-align:right; }
.fb-sender-name { font-size:11px; color:#374151 !important; font-weight:600; margin-bottom:2px; margin-left:4px; }
.fb-chat-body {
    background:#f0f9ff; min-height:180px; max-height:380px; overflow-y:auto;
    padding:14px; display:flex; flex-direction:column; gap:8px;
    border:1.5px solid #bfdbfe; border-radius:0 0 10px 10px; margin-bottom:10px;
}
.fb-badge {
    display:inline-block; background:#dc2626; color:#fff !important;
    border-radius:10px; padding:1px 7px; font-size:11px; font-weight:700; margin-left:4px;
}

/* ══ SCROLLBAR ══ */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#dbeafe; }
::-webkit-scrollbar-thumb { background:#93c5fd; border-radius:4px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# [FIX v2] HIDDEN UTILS — st_autorefresh เป็น custom component ที่ Streamlit
#   บังคับ render เป็น <iframe> สีขาวลงในหน้าจริง ๆ (คือ "แถบขาว" ที่โผล่ด้านบน)
#   จึงต้องยัดไว้ในคอนเทนเนอร์ที่ถูกดันออกนอก layout
# ─────────────────────────────────────────────────────────────
with st.container(key="hidden_utils"):
    # interval 3000ms — เดิม 1000ms ทำให้กะพริบและ query DB ถี่เกินจำเป็น
    # (เกณฑ์ online คือ 15 วินาที จึงยังเหลือ margin เยอะ)
    st_autorefresh(interval=3000, limit=None, key="live_refresh")

# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────
DB_FILE = "trip_database.db"
BANK_LIST = ["-- เลือกธนาคาร --","กสิกรไทย (KBank)","ไทยพาณิชย์ (SCB)","กรุงไทย (KTB)",
             "กรุงเทพ (BBL)","กรุงศรีอยุธยา (BAY)","ทหารไทยธนชาต (TTB)","ออมสิน (GSB)","ธ.ก.ส.","ยูโอบี (UOB)"]

def db():
    c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row; return c

def init_db():
    conn = db(); cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS all_users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cur.execute('CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, status INTEGER DEFAULT 0)')
    cur.execute('CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, name TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, description TEXT, amount REAL, payer_name TEXT, split_members TEXT, image_blob BLOB)')
    cur.execute('CREATE TABLE IF NOT EXISTS settlements (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, debtor TEXT, creditor TEXT, amount REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    cur.execute('CREATE TABLE IF NOT EXISTS online_status (name TEXT PRIMARY KEY, last_seen DATETIME)')
    cur.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER,
        to_user TEXT, from_user TEXT, message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_auto INTEGER DEFAULT 0, is_read INTEGER DEFAULT 0)''')
    for col, dtype in [('promptpay','TEXT'),('bank_name','TEXT'),('bank_account','TEXT'),('avatar_blob','BLOB')]:
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
    img.thumbnail((800,800)); buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70); return buf.getvalue()

# [FIX v6] ── รูปโปรไฟล์ ────────────────────────────────────────
def compress_avatar(f):
    """ครอปเป็นสี่เหลี่ยมจัตุรัสตรงกลางแล้วย่อเหลือ 160px — ให้ base64 สั้นพอ
    ที่จะยัดลง CSS variable ของปุ่มบน navbar ได้"""
    if f is None: return None
    img = Image.open(f)
    if img.mode in ("RGBA","P","LA"): img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w-side)//2, (h-side)//2, (w+side)//2, (h+side)//2))
    img = img.resize((160,160), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=72)
    return buf.getvalue()

def avatar_uri(blob):
    if not blob: return None
    return "data:image/jpeg;base64," + base64.b64encode(blob).decode()

def avatar_html(name, blob=None, size=32, font=12, bg="#1d4ed8"):
    """คืน <div> วงกลมเดียวแบบบรรทัดเดียว — ถ้ามีรูปใช้รูป ถ้าไม่มีใช้อักษรตัวแรก"""
    uri = avatar_uri(blob)
    if uri:
        fill = f"background-image:url({uri});background-size:cover;background-position:center;"
        ch = ""
    else:
        fill = f"background:{bg};"
        ch = (name[0].upper() if name else "?")
    return (f'<div style="width:{size}px;height:{size}px;border-radius:50%;{fill}'
            f'flex-shrink:0;display:flex;align-items:center;justify-content:center;'
            f'color:#fff;font-weight:700;font-size:{font}px;">{ch}</div>')

# [FIX v6] ── เปลี่ยนชื่อผู้ใช้ ───────────────────────────────────
def rename_user(old, new):
    """ชื่อผู้ใช้ถูกเก็บเป็น TEXT กระจายอยู่หลายตาราง (ไม่ได้ใช้ user_id)
    จึงต้องไล่แก้ให้ครบทุกที่ ไม่งั้นบิล/แชท/ยอดหนี้เดิมจะกำพร้า"""
    if not new or new == old: return False, "ชื่อไม่เปลี่ยนแปลง"
    c = db()
    if c.execute("SELECT 1 FROM all_users WHERE name=?", (new,)).fetchone():
        c.close(); return False, "มีคนใช้ชื่อนี้แล้ว"
    c.execute("UPDATE all_users     SET name=?        WHERE name=?",        (new, old))
    c.execute("UPDATE members       SET name=?        WHERE name=?",        (new, old))
    c.execute("UPDATE expenses      SET payer_name=?  WHERE payer_name=?",  (new, old))
    c.execute("UPDATE settlements   SET debtor=?      WHERE debtor=?",      (new, old))
    c.execute("UPDATE settlements   SET creditor=?    WHERE creditor=?",    (new, old))
    c.execute("UPDATE notifications SET to_user=?     WHERE to_user=?",     (new, old))
    c.execute("UPDATE notifications SET from_user=?   WHERE from_user=?",   (new, old))
    c.execute("DELETE FROM online_status WHERE name=?", (new,))
    c.execute("UPDATE online_status SET name=?        WHERE name=?",        (new, old))
    # split_members เก็บเป็น "a,b,c" → ต้องแยกแล้วประกอบใหม่ทีละแถว
    for r in c.execute("SELECT id, split_members FROM expenses").fetchall():
        parts = (r["split_members"] or "").split(",")
        if old in parts:
            c.execute("UPDATE expenses SET split_members=? WHERE id=?",
                      (",".join(new if p == old else p for p in parts), r["id"]))
    c.commit(); c.close()
    return True, ""

def heartbeat(u):
    if u:
        c = db(); c.execute("INSERT INTO online_status (name,last_seen) VALUES (?,datetime('now','localtime')) ON CONFLICT(name) DO UPDATE SET last_seen=datetime('now','localtime')",(u,)); c.commit(); c.close()

def online_now():
    c = db(); rows = c.execute("SELECT name FROM online_status WHERE last_seen>=datetime('now','localtime','-15 seconds')").fetchall(); c.close()
    return [r["name"] for r in rows]

init_db()

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
for k,v in [("me",None),("menu","home"),("trip_id",None),("chat_partner",None)]:
    if k not in st.session_state: st.session_state[k]=v

me = st.session_state["me"]
if me: heartbeat(me)
online_users = online_now()

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
conn0 = db()
_urows    = conn0.execute("SELECT name, avatar_blob FROM all_users").fetchall()
all_users = [r["name"] for r in _urows]
avatars   = {r["name"]: r["avatar_blob"] for r in _urows}   # [FIX v6] รูปโปรไฟล์
trips_df  = pd.read_sql_query("SELECT * FROM trips WHERE status=0", conn0)
conn0.close()

if not trips_df.empty:
    trips_df['disp'] = trips_df.apply(
        lambda r: f"{r['name']}  ({r['trip_date']})" if r['trip_date'] and str(r['trip_date']).strip() else r['name'], axis=1)
    tid_list = trips_df["id"].tolist()
else:
    tid_list = []

if st.session_state["trip_id"] not in tid_list:
    st.session_state["trip_id"] = tid_list[0] if tid_list else None

trip_id = st.session_state["trip_id"]
cur_trip = cur_date = None
if trip_id and not trips_df.empty:
    row_t = trips_df[trips_df["id"]==trip_id]
    if not row_t.empty:
        cur_trip = row_t.iloc[0]["name"]; cur_date = row_t.iloc[0]["trip_date"]

members = []
if trip_id:
    c = db(); members = [r["name"] for r in c.execute("SELECT name FROM members WHERE trip_id=?",(trip_id,)).fetchall()]; c.close()

notif_count = 0
if me and trip_id:
    c = db(); r = c.execute("SELECT COUNT(*) as n FROM notifications WHERE trip_id=? AND to_user=? AND is_read=0",(trip_id,me)).fetchone(); notif_count = r["n"] if r else 0; c.close()

# ─────────────────────────────────────────────────────────────
# FIXED HEADER (navbar + menubar)
# ─────────────────────────────────────────────────────────────
trip_lbl   = cur_trip or "เลือก Event"
av_char    = me[0].upper() if me else "?"
name_str   = me if me else "ล็อกอิน"
green_part = f'<span class="nb-badge-g">🟢 {len(online_users)}</span>' if online_users else ""
red_part   = f'<span class="nb-badge-r">🔔 {notif_count}</span>' if notif_count > 0 else ""

# [FIX v5] ถอด "บัญชี" ออกจากแถบเมนู — ย้ายไปเป็นปุ่มโปรไฟล์มุมขวาบนแทน
MENUS = [
    ("🏠", "หลัก",   "home"),
    ("🗓️", "จัดการ", "manage"),
    ("💬", "แชท",    "chat"),
]

cur_menu = st.session_state["menu"]

# ── Navbar HTML ──────────────────────────────────────────────
# [FIX v4] ต้นเหตุจริงของ "กล่องขาวมุมขวาบน"
#   ของเดิมเขียน HTML แบบหลายบรรทัด และมีบรรทัด "    {green_part}{red_part}"
#   ซึ่งตอนไม่มีคนออนไลน์/ไม่มีแจ้งเตือน ทั้งสองตัวเป็นค่าว่าง → เหลือแค่ช่องว่าง 4 ตัว
#   = บรรทัดว่างในสายตา Markdown → ปิดบล็อก HTML ทันที
#   บรรทัดที่เหลือ (<div class="nb-avatar">... ) ย่อหน้า 4 ช่อง → Markdown ตีความ
#   เป็น "code block" → กลายเป็นกล่องขาวโชว์ HTML ดิบ ๆ ทับ navbar
#   วิธีแก้: ต่อเป็นสตริงบรรทัดเดียว ไม่มีขึ้นบรรทัดใหม่/ย่อหน้าเลย
navbar_html = (
    '<div class="navbar-wrap"><div class="navbar">'
    '<span class="nb-icon">✈️</span>'
    '<span class="nb-title">Trip Splitter</span>'
    f'<span class="nb-trip">✈️ {trip_lbl}</span>'
    '<span class="nb-spacer"></span>'
    '</div></div>'
)
st.markdown(navbar_html, unsafe_allow_html=True)

# ── ปุ่มโปรไฟล์มุมขวาบน ────────────────────────────────────────
# [FIX v5] ใช้ st.button จริง (ไม่ใช่ <a href>) เพราะลิงก์ HTML จะทำให้หน้า
#   reload ทั้งหน้า → session_state หาย → ผู้ใช้หลุดล็อกอินทันที
# [FIX v6] สี/อักษรย่อ/รูป ส่งเข้า CSS ผ่าน variable — และห้ามใส่ help=
#   เพราะ tooltip wrapper จะทำให้ selector ของปุ่มหลุด (ปุ่มกลายเป็นสีส้ม default)
_my_av = avatars.get(me) if me else None
if _my_av:
    _av_vars = f'--nb-av:"";--nb-img:url({avatar_uri(_my_av)});'
else:
    _av_vars = '--nb-av:"%s";--nb-img:none;' % av_char.replace('"', "").replace("\\", "")
# ล็อกอินแล้ว = เขียว / ยังไม่ล็อกอิน = ส้ม (ให้สะดุดตาว่ายังต้องล็อกอิน)
_col_vars = "--nb-main:#16a34a;--nb-line:#4ade80;" if me else "--nb-main:#f97316;--nb-line:#fdba74;"
st.markdown(f"<style>div.st-key-userbtn{{{_av_vars}{_col_vars}}}</style>",
            unsafe_allow_html=True)

with st.container(key="userbtn"):
    if green_part or red_part:   # [FIX v7] ป้ายอยู่ติดปุ่มเสมอ ไม่ว่าชื่อจะสั้นหรือยาว
        st.markdown(f'<div class="nb-badges">{green_part}{red_part}</div>',
                    unsafe_allow_html=True)
    if st.button(name_str, key="btn_user",
                 type="primary" if cur_menu == "account" else "secondary"):
        st.session_state["menu"] = "account"
        st.rerun()

# ── Menu bar — wrapped in a keyed container so CSS has a stable,
#    version-proof hook (`.st-key-menubar`) instead of guessing DOM nesting ──
with st.container(key="menubar"):
    nav_cols = st.columns(len(MENUS))
    for col, (icon, label, key) in zip(nav_cols, MENUS):
        badge = f" {notif_count}🔴" if key == "chat" and notif_count > 0 else ""
        active = cur_menu == key
        if col.button(f"{icon} {label}{badge}", key=f"nav_{key}",
                      type="primary" if active else "secondary",
                      use_container_width=True):
            st.session_state["menu"] = key
            st.rerun()

menu = st.session_state["menu"]

# ═══════════════════════════════════════════════════════
# PAGE ROUTING
# ═══════════════════════════════════════════════════════
if menu == "home":
    if not me:
        st.markdown("""<div class="card" style="text-align:center;padding:48px 20px;">
          <div style="font-size:52px;">✈️</div>
          <div style="font-weight:800;font-size:20px;margin:10px 0 6px;">Trip Expense Splitter</div>
          <div style="color:#374151;">ไปที่เมนู <b>บัญชี</b> เพื่อเข้าสู่ระบบก่อนใช้งาน</div>
        </div>""", unsafe_allow_html=True)
    elif not trip_id:
        st.info("ไปที่เมนู **จัดการ** เพื่อสร้างหรือเลือก Event ก่อนครับ")
    else:
        has_date = cur_date and str(cur_date).strip()
        st.markdown(f"""<div class="card" style="display:flex;align-items:center;gap:14px;padding:14px 16px;">
          <div style="width:46px;height:46px;border-radius:12px;background:#1d4ed8;flex-shrink:0;
                      display:flex;align-items:center;justify-content:center;font-size:22px;">✈️</div>
          <div style="min-width:0;flex:1;">
            <div style="font-weight:800;font-size:17px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{cur_trip}</div>
            <div style="font-size:13px;color:#374151;">{'📅 '+str(cur_date)+'  ·  ' if has_date else ''}👥 {len(members)} สมาชิก</div>
          </div>
        </div>""", unsafe_allow_html=True)

        tab1,tab2,tab3 = st.tabs(["➕ เพิ่มบิล","📋 ประวัติ","💰 สรุปเงิน"])

        # ── TAB 1 ──────────────────────────────────────────────
        with tab1:
            if not members:
                st.warning("ยังไม่มีสมาชิก — ไปที่ **จัดการ** เพื่อเพิ่มสมาชิกก่อน")
            else:
                with st.form("add_bill", clear_on_submit=True):
                    c1,c2 = st.columns(2)
                    with c1:
                        desc = st.text_input("📌 รายการ:", placeholder="ค่าอาหาร, ค่าแท็กซี่...")
                        amt  = st.number_input("💰 จำนวนเงิน (บาท):", min_value=0.0, step=10.0)
                    with c2:
                        my_idx = members.index(me) if me in members else 0
                        payer  = st.selectbox("👤 คนสำรองจ่าย:", members, index=my_idx)
                        fup    = st.file_uploader("📎 สลิป:", type=['jpg','png','jpeg'])
                    st.markdown("**👥 ร่วมหาร:**")
                    nc = min(len(members),5)
                    sc = st.columns(nc)
                    split_to = [m for i,m in enumerate(members) if sc[i%nc].checkbox(m, value=True, key=f"sp_{m}")]
                    if st.form_submit_button("💾 บันทึกบิล", type="primary", use_container_width=True):
                        if desc and amt>0 and split_to:
                            blob = compress_image(fup)
                            c = db()
                            c.execute("INSERT INTO expenses (trip_id,description,amount,payer_name,split_members,image_blob) VALUES (?,?,?,?,?,?)",
                                      (trip_id,desc,amt,payer,",".join(split_to),blob))
                            c.commit()
                            sh = amt/len(split_to)
                            for m2 in split_to:
                                if m2!=payer:
                                    msg=f"📌 บิลใหม่: '{desc}'\n💰 {amt:,.2f} บาท | จ่ายโดย: {payer}\n💸 ส่วนคุณ: {sh:,.2f} บาท"
                                    c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,'ระบบสรุปยอด',?,1,0,datetime('now','localtime'))",(trip_id,m2,msg))
                            c.commit(); c.close()
                            st.success(f"✅ บันทึก '{desc}' แล้ว!"); time.sleep(0.6); st.rerun()
                        else: st.error("⚠️ กรอกข้อมูลให้ครบ")

        # ── TAB 2 ──────────────────────────────────────────────
        with tab2:
            c = db(); exps = c.execute("SELECT * FROM expenses WHERE trip_id=?",(trip_id,)).fetchall(); c.close()
            if not exps: st.info("ยังไม่มีบิล")
            else:
                for row in exps:
                    sl = row['split_members'].split(","); sh = row['amount']/len(sl)
                    with st.expander(f"📌 {row['description']} — {row['amount']:,.2f} ฿  |  {row['payer_name']}"):
                        a,b2 = st.columns([1,1.5])
                        with a:
                            if row['image_blob']: st.image(row['image_blob'], use_container_width=True)
                            else: st.markdown('<div style="background:#dbeafe;border-radius:8px;height:90px;display:flex;align-items:center;justify-content:center;color:#374151;font-size:13px;">ไม่มีสลิป</div>',unsafe_allow_html=True)
                            st.markdown(f"**{len(sl)} คน** หาร · คนละ **{sh:,.2f} ฿**")
                        with b2:
                            with st.form(f"ed_{row['id']}"):
                                ud = st.text_input("รายการ:", value=row['description'])
                                ua = st.number_input("จำนวน:", value=row['amount'])
                                po = members if row['payer_name'] in members else members+[row['payer_name']]
                                up = st.selectbox("คนจ่าย:", po, index=po.index(row['payer_name']))
                                st.write("คนหาร:"); us = [m for m in po if st.checkbox(m, value=(m in row['split_members'].split(",")), key=f"ed_{row['id']}_{m}")]
                                uf = st.file_uploader("สลิป:", type=['jpg','png','jpeg'])
                                di = st.checkbox("🗑️ ลบรูป", key=f"di_{row['id']}")
                                if st.form_submit_button("💾 อัปเดต", type="primary"):
                                    c=db()
                                    if di: c.execute("UPDATE expenses SET description=?,amount=?,payer_name=?,split_members=?,image_blob=NULL WHERE id=?",(ud,ua,up,",".join(us),row['id']))
                                    elif uf: c.execute("UPDATE expenses SET description=?,amount=?,payer_name=?,split_members=?,image_blob=? WHERE id=?",(ud,ua,up,",".join(us),compress_image(uf),row['id']))
                                    else: c.execute("UPDATE expenses SET description=?,amount=?,payer_name=?,split_members=? WHERE id=?",(ud,ua,up,",".join(us),row['id']))
                                    c.commit(); c.close(); st.success("✅ อัปเดต!"); time.sleep(0.5); st.rerun()
                            if st.button("🗑️ ลบบิล", key=f"db_{row['id']}", type="secondary"):
                                c=db(); c.execute("DELETE FROM expenses WHERE id=?",(row['id'],)); c.commit(); c.close()
                                st.warning("ลบแล้ว"); time.sleep(0.5); st.rerun()

        # ── TAB 3 ──────────────────────────────────────────────
        with tab3:
            c = db()
            exps2 = c.execute("SELECT * FROM expenses WHERE trip_id=?",(trip_id,)).fetchall()
            uprof = {r['name']:{"pp":r['promptpay'],"bn":r['bank_name'],"ba":r['bank_account']} for r in c.execute("SELECT name,promptpay,bank_name,bank_account FROM all_users").fetchall()}
            c.close()
            if not exps2: st.info("ยังไม่มีบิล")
            else:
                inv = set(members)
                for r in exps2: inv.add(r['payer_name']); inv.update(r['split_members'].split(","))
                net = {m:0.0 for m in inv}
                for r in exps2:
                    net[r['payer_name']]+=r['amount']
                    sl=r['split_members'].split(","); sh=r['amount']/len(sl)
                    for m2 in sl: net[m2]-=sh

                st.markdown("#### 📊 ยอดสรุปรายคน")
                nc2 = min(len(inv),4); cols2 = st.columns(nc2)
                for i,(m2,b) in enumerate(net.items()):
                    clr = "#16a34a" if b>0.01 else ("#dc2626" if b<-0.01 else "#1d4ed8")
                    ico = "🟢" if b>0.01 else ("🔴" if b<-0.01 else "⚖️")
                    lbl = "รับคืน" if b>0.01 else ("ต้องจ่าย" if b<-0.01 else "เท่ากัน")
                    with cols2[i%nc2]:
                        st.markdown(f"""<div style="background:#fff;border-radius:10px;padding:14px 10px;
                          border:1.5px solid #bfdbfe;border-top:4px solid {clr};text-align:center;margin-bottom:10px;">
                          <div style="font-size:18px;">{ico}</div>
                          <div style="font-weight:700;font-size:13px;color:#000;">{m2}</div>
                          <div style="font-size:11px;color:#374151;">{lbl}</div>
                          <div style="font-weight:800;font-size:16px;color:{clr};">{abs(b):,.2f} ฿</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("#### 🚀 แผนโอนเงิน")
                dbt = [[m2,b] for m2,b in net.items() if b<-0.01]
                crd = [[m2,b] for m2,b in net.items() if b>0.01]
                final_tx=[]
                while dbt and crd:
                    at=min(abs(dbt[0][1]),crd[0][1]); dn,cn=dbt[0][0],crd[0][0]
                    p=uprof.get(cn,{}); pp=(p.get("pp") or "").strip(); bn=(p.get("bn") or "").strip(); ba=(p.get("ba") or "").strip()
                    is_me2=(dn==me)
                    bg2="background:#eff6ff;" if is_me2 else "background:#fff;"
                    brd="border:2px solid #1d4ed8;" if is_me2 else "border:1.5px solid #bfdbfe;"
                    bdg='<span style="background:#1d4ed8;color:#fff;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;">⚠️ คุณ</span>' if is_me2 else ""
                    st.markdown(f"""<div style="{bg2}{brd}border-radius:12px;padding:14px 14px;margin-bottom:10px;">
                      <div style="font-size:14px;font-weight:700;color:#000;display:flex;align-items:center;flex-wrap:wrap;gap:6px;">
                        💳 <span>{dn}</span> {bdg}
                        <span style="color:#6b7280;">→</span>
                        👉 <span>{cn}</span>
                        <span style="background:#dc2626;color:#fff;padding:2px 12px;border-radius:20px;font-size:13px;font-weight:700;margin-left:auto;">{at:,.2f} ฿</span>
                      </div></div>""", unsafe_allow_html=True)
                    if pp or ba:
                        pc=st.columns(2)
                        if pp: pc[0].markdown(f"📱 **พร้อมเพย์ {cn}**"); pc[0].code(pp)
                        if ba: pc[1].markdown(f"🏦 **{bn or 'บัญชี'} {cn}**"); pc[1].code(ba)
                    else: st.warning(f"⚠️ {cn} ยังไม่ได้บันทึกบัญชี")
                    final_tx.append((dn,cn,at)); dbt[0][1]+=at; crd[0][1]-=at
                    if abs(dbt[0][1])<0.01: dbt.pop(0)
                    if abs(crd[0][1])<0.01: crd.pop(0)

                st.markdown("#### 📲 แชร์ LINE")
                lm=f"📊 สรุปบิล: {cur_trip}\n"
                if has_date: lm+=f"📅 {cur_date}\n"
                lm+="========================\n"; tot=0.0
                for i2,r2 in enumerate(exps2,1):
                    sl2=r2['split_members'].split(","); sh2=r2['amount']/len(sl2)
                    lm+=f"{i2}. {r2['description']} | {r2['amount']:,.2f} ฿ | {r2['payer_name']}\n   คนละ {sh2:,.2f} ฿\n"; tot+=r2['amount']
                lm+=f"รวม: {tot:,.2f} ฿\n========================\n"
                for dn2,cn2,am2 in final_tx:
                    lm+=f"💳 {dn2} → {cn2} = {am2:,.2f} ฿\n"
                    p2=uprof.get(cn2,{}); pp2=(p2.get("pp") or "").strip(); ba2=(p2.get("ba") or "").strip(); bn2=(p2.get("bn") or "").strip()
                    if pp2: lm+=f"   📱 {pp2}\n"
                    if ba2: lm+=f"   🏦 {bn2 or 'บัญชี'}: {ba2}\n"
                lm+="========================"
                st.text_area("ข้อความ LINE:", value=lm, height=180, disabled=True)
                st.link_button("🟢 เปิด LINE", f"https://line.me/R/msg/text/?{urllib.parse.quote(lm)}", type="primary", use_container_width=True)

# ═══════════════════════════════════════════════════════
# PAGE: จัดการ (Events + Members รวมกัน)
# ═══════════════════════════════════════════════════════
elif menu == "manage":
    t_event, t_member, t_trash = st.tabs(["🗓️ Events", "👥 สมาชิก", "🗑️ ถังขยะ"])

    # ── TAB: Events ────────────────────────────────────
    with t_event:
        left, right = st.columns([1,1])
        with left:
            st.markdown('<div class="section-head">➕ สร้าง Event ใหม่</div>', unsafe_allow_html=True)
            with st.form("create_ev"):
                ne = st.text_input("ชื่อ Event:", placeholder="เช่น ทริปเชียงใหม่")
                nd = st.date_input("วันที่:", value=datetime.today())
                if st.form_submit_button("✅ สร้าง", type="primary", use_container_width=True):
                    if ne.strip():
                        try:
                            c=db(); c.execute("INSERT INTO trips (name,status,trip_date) VALUES (?,0,?)",(ne.strip(),nd.strftime("%Y-%m-%d"))); c.commit(); c.close()
                            st.success(f"สร้าง '{ne.strip()}' แล้ว!"); time.sleep(0.5); st.rerun()
                        except: st.error("❌ ชื่อซ้ำ")
                    else: st.error("⚠️ กรอกชื่อก่อน")

            if trip_id and cur_trip:
                st.markdown(f'<div class="section-head">✏️ แก้ไข: {cur_trip}</div>', unsafe_allow_html=True)
                with st.form("edit_ev"):
                    rn = st.text_input("ชื่อใหม่:", value=cur_trip)
                    try: dd = datetime.strptime(str(cur_date),"%Y-%m-%d") if cur_date and str(cur_date).strip() else datetime.today()
                    except: dd = datetime.today()
                    rd = st.date_input("วันที่:", value=dd)
                    if st.form_submit_button("💾 บันทึก", type="primary"):
                        if rn.strip():
                            try:
                                c=db(); c.execute("UPDATE trips SET name=?,trip_date=? WHERE id=?",(rn.strip(),rd.strftime("%Y-%m-%d"),trip_id)); c.commit(); c.close()
                                st.success("✅ แก้ไขแล้ว!"); time.sleep(0.5); st.rerun()
                            except: st.error("❌ ชื่อซ้ำ")
                if st.button("🗑️ ลบ Event นี้", type="secondary", use_container_width=True):
                    c=db(); c.execute("UPDATE trips SET status=1 WHERE id=?",(trip_id,)); c.commit(); c.close()
                    st.session_state["trip_id"]=None; st.toast("ย้ายสู่ถังขยะ"); time.sleep(0.5); st.rerun()

        with right:
            st.markdown('<div class="section-head">🗺️ เลือก Event</div>', unsafe_allow_html=True)
            if not trips_df.empty:
                for _, row in trips_df.iterrows():
                    tid2 = int(row["id"])
                    sel = (tid2 == trip_id)

                    # กำหนด Label และ Type ตามสถานะการเลือก
                    chk = "✅ " if sel else ""
                    btn_label = f"{chk}✈️ {row['disp']}"
                    btn_type = "primary" if sel else "secondary"

                    # เมื่อกดปุ่มชื่อ Event
                    if st.button(btn_label, key=f"sel_ev_{tid2}", type=btn_type, use_container_width=True):
                        st.session_state["trip_id"] = tid2
                        st.rerun()
            else:
                st.info("ยังไม่มี Event")

    # ── TAB: สมาชิก ─────────────────────────────────────
    with t_member:
        if not trip_id:
            st.warning("กรุณาเลือก Event ที่แท็บ Events ก่อน")
        else:
            avail = [u for u in all_users if u not in members]
            left2, right2 = st.columns([1,1])

            with left2:
                st.markdown(f'<div class="section-head">👥 สมาชิก ({len(members)} คน)</div>', unsafe_allow_html=True)
                if members:
                    c=db()
                    for mem in members:
                        nr=c.execute("SELECT COUNT(*) as n FROM notifications WHERE trip_id=? AND to_user=? AND is_read=0",(trip_id,mem)).fetchone()
                        nc3=nr["n"] if nr else 0
                        ion=mem in online_users
                        dot="🟢" if ion else "⚪"
                        bdg=f'<span class="fb-badge">{nc3}</span>' if nc3>0 else ""
                        you=" (คุณ)" if mem==me else ""
                        mc1,mc2=st.columns([5,1])
                        mc1.markdown(
                            '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #dbeafe;">'
                            + avatar_html(mem, avatars.get(mem), size=34, font=13)   # [FIX v6] รูปโปรไฟล์
                            + f'<div><div style="font-weight:600;font-size:14px;color:#000;">{dot} {mem}{you}{bdg}</div>'
                            + f'<div style="font-size:12px;color:#374151;">{"ออนไลน์" if ion else "ออฟไลน์"}</div></div></div>',
                            unsafe_allow_html=True)
                        if mc2.button("ออก", key=f"rm_{mem}"):
                            c.execute("DELETE FROM members WHERE trip_id=? AND name=?",(trip_id,mem)); c.commit()
                            st.toast(f"ถอด {mem}"); time.sleep(0.5); st.rerun()
                    c.close()
                else: st.info("ยังไม่มีสมาชิก")

            with right2:
                st.markdown('<div class="section-head">➕ เพิ่มสมาชิก</div>', unsafe_allow_html=True)
                if avail:
                    # ฟังก์ชั่น Callback สำหรับอัปเดตรายการที่เลือกเมื่อกดติ๊ก Checkbox
                    def toggle_select_all():
                        if st.session_state.get("chk_select_all_mems"):
                            st.session_state["ms_add_mems"] = avail.copy()
                        else:
                            st.session_state["ms_add_mems"] = []

                    # Checkbox พร้อมผูกการทำงานเข้ากับ on_change Callback
                    st.checkbox(
                        "☑️ เลือกทั้งหมด",
                        key="chk_select_all_mems",
                        on_change=toggle_select_all
                    )

                    # [FIX v9] ล้างค่าค้างที่หลุดออกจาก options ไปแล้ว — จำเป็นเพราะ
                    #   หน้าจอ refresh ทุก 3 วิและเป็นระบบหลายคน เพื่อนที่เราเลือกค้างไว้
                    #   อาจถูกคนอื่นเพิ่มเข้า Event ไปก่อน → ค่าใน state ไม่มีใน options
                    #   → Streamlit error. ทำตรงนี้ได้เพราะยังไม่ถึงบรรทัดที่สร้าง widget
                    _kept = [x for x in st.session_state.get("ms_add_mems", []) if x in avail]
                    if _kept != st.session_state.get("ms_add_mems", []):
                        st.session_state["ms_add_mems"] = _kept

                    # Multiselect อ่านและอัปเดตค่าผ่าน session_state ล่าสุด
                    st.multiselect(
                        "เลือกเพื่อน:",
                        options=avail,
                        key="ms_add_mems",
                        placeholder="เลือกเพื่อนที่ต้องการเพิ่ม..."
                    )

                    # [FIX v9] ย้ายงานทั้งหมดมาไว้ใน callback
                    #   ของเดิมเขียน st.session_state["chk_select_all_mems"] = False
                    #   ไว้ใน body ของ if st.button(...) ซึ่งรันหลังจาก widget ถูกสร้างไปแล้ว
                    #   → Streamlit โยน StreamlitAPIException ("cannot be modified after
                    #   the widget ... is instantiated") เพราะห้ามเขียนทับ state ของ widget
                    #   ที่ instantiate ไปแล้วในรอบเดียวกัน
                    #   callback ของ on_click รัน "ก่อน" สคริปต์รอบถัดไปจะสร้าง widget
                    #   จึงเป็นที่เดียวที่ล้างค่า widget ได้อย่างถูกต้อง
                    def add_selected_members():
                        sel = list(st.session_state.get("ms_add_mems", []))
                        if not sel:
                            st.session_state["add_mem_msg"] = ("err", "⚠️ กรุณาเลือกสมาชิกอย่างน้อย 1 คน")
                            return
                        c = db()
                        for su in sel:
                            c.execute("INSERT INTO members (trip_id, name) VALUES (?, ?)", (trip_id, su))
                        c.commit(); c.close()
                        st.session_state["chk_select_all_mems"] = False
                        st.session_state["ms_add_mems"] = []
                        st.session_state["add_mem_msg"] = ("ok", f"เพิ่ม {len(sel)} คนเข้า Event เรียบร้อย!")

                    st.button("➕ เพิ่มเข้า Event", type="primary",
                              use_container_width=True, on_click=add_selected_members)

                    # callback สั่ง rerun ให้เองอยู่แล้ว จึงมาอ่านผลลัพธ์ตรงนี้
                    _res = st.session_state.pop("add_mem_msg", None)
                    if _res:
                        (st.toast if _res[0] == "ok" else st.error)(_res[1])
                else:
                    st.info("ทุกคนอยู่ในกลุ่มแล้ว")

                st.markdown('<div class="section-head" style="margin-top:16px;">🌐 ออนไลน์ตอนนี้</div>', unsafe_allow_html=True)
                for u2 in online_users:
                    you2 = " (คุณ)" if u2 == me else ""
                    st.markdown(f"🟢 **{u2}**{you2}")
                if not online_users:
                    st.caption("ไม่มีใครออนไลน์")

    # ── TAB: ถังขยะ ──────────────────────────────────────
    with t_trash:
        c=db(); dels=c.execute("SELECT * FROM trips WHERE status=1").fetchall(); c.close()
        if not dels: st.info("ถังขยะว่างเปล่า")
        else:
            for dt in dels:
                hd=dt['trip_date'] and str(dt['trip_date']).strip()
                dn2=f"{dt['name']} ({dt['trip_date']})" if hd else dt['name']
                dc1,dc2,dc3=st.columns([3,1,1])
                dc1.markdown(f"✈️ **{dn2}**")
                if dc2.button("กู้คืน",key=f"rs_{dt['id']}",type="primary"):
                    c=db(); c.execute("UPDATE trips SET status=0 WHERE id=?",(dt['id'],)); c.commit(); c.close()
                    st.toast("กู้คืนแล้ว!"); time.sleep(0.5); st.rerun()
                if dc3.button("ลบถาวร",key=f"pd_{dt['id']}",type="secondary"):
                    c=db()
                    for tb in ["settlements","expenses","members","notifications"]: c.execute(f"DELETE FROM {tb} WHERE trip_id=?",(dt['id'],))
                    c.execute("DELETE FROM trips WHERE id=?",(dt['id'],)); c.commit(); c.close()
                    st.toast("ลบถาวร!"); time.sleep(0.5); st.rerun()

# ═══════════════════════════════════════════════════════
# PAGE: แชท
# ═══════════════════════════════════════════════════════
elif menu == "chat":
    if not me:
        st.warning("กรุณาเข้าสู่ระบบที่เมนู **บัญชี** ก่อน")
    elif not trip_id:
        st.warning("กรุณาเลือก Event ที่เมนู **จัดการ** ก่อน")
    else:
        c=db()
        rows=c.execute("""SELECT * FROM notifications WHERE trip_id=?
            AND (to_user=? OR from_user=? OR (to_user=? AND is_auto=1))
            ORDER BY timestamp ASC, id ASC""",(trip_id,me,me,me)).fetchall()
        c.close()

        grps={}; unrd={}
        for n in rows:
            pt="🤖 ระบบ" if (n['is_auto']==1 or n['from_user']=="ระบบสรุปยอด") else (n['from_user'] if n['to_user']==me else n['to_user'])
            if pt not in grps: grps[pt]=[]; unrd[pt]=0
            grps[pt].append(n)
            if n['to_user']==me and n['is_read']==0: unrd[pt]+=1

        cl,cr=st.columns([1,2.5])
        with cl:
            st.markdown('<div class="section-head">💬 การสนทนา</div>', unsafe_allow_html=True)
            if not grps: st.caption("ยังไม่มีการสนทนา")
            for pt in grps:
                u3=unrd[pt]; bdg=f" 🔴{u3}" if u3>0 else ""
                if st.button(f"{pt[0].upper()}  {pt}{bdg}", key=f"cs_{pt}", use_container_width=True):
                    st.session_state["chat_partner"]=pt; st.rerun()
            st.markdown("---")
            st.markdown("**📝 เริ่มแชทใหม่**")
            others=[m for m in members if m!=me]
            if others:
                with st.form("ncf", clear_on_submit=True):
                    nt=st.selectbox("ถึง:", others)
                    nm=st.text_input("", placeholder="พิมพ์ข้อความ...", label_visibility="collapsed")
                    b1,b2=st.columns([3,1])
                    if b1.form_submit_button("ส่ง ▶", type="primary", use_container_width=True) and nm.strip():
                        c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",(trip_id,nt,me,nm.strip())); c.commit(); c.close()
                        st.session_state["chat_partner"]=nt; st.rerun()
                    if b2.form_submit_button("👍"):
                        c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",(trip_id,nt,me,"👍")); c.commit(); c.close()
                        st.session_state["chat_partner"]=nt; st.rerun()
            else: st.caption("ไม่มีสมาชิกอื่น")

        with cr:
            pt=st.session_state.get("chat_partner")
            if not pt:
                st.markdown("""<div style="background:#fff;border:1.5px solid #bfdbfe;border-radius:12px;
                  text-align:center;padding:60px 20px;">
                  <div style="font-size:40px;margin-bottom:10px;">💬</div>
                  <div style="font-weight:700;font-size:15px;color:#000;">เลือกการสนทนา</div>
                  <div style="font-size:13px;color:#374151;margin-top:4px;">เลือกจากรายการซ้าย หรือเริ่มใหม่</div>
                </div>""", unsafe_allow_html=True)
            else:
                msgs=grps.get(pt,[]); u4=unrd.get(pt,0)
                if u4>0:
                    c=db()
                    if pt=="🤖 ระบบ": c.execute("UPDATE notifications SET is_read=1 WHERE trip_id=? AND to_user=? AND is_auto=1 AND is_read=0",(trip_id,me))
                    else: c.execute("UPDATE notifications SET is_read=1 WHERE trip_id=? AND to_user=? AND from_user=? AND is_read=0",(trip_id,me,pt))
                    c.commit(); c.close()
                ion2=pt in online_users
                st.markdown(f"""<div style="background:#1d4ed8;border-radius:10px 10px 0 0;
                  padding:12px 14px;display:flex;align-items:center;gap:10px;">
                  <div style="width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,.25);flex-shrink:0;
                              display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:14px;">{pt[0].upper()}</div>
                  <div style="flex:1;min-width:0;">
                    <div style="font-weight:700;font-size:14px;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{pt}</div>
                    <div style="font-size:11px;color:{'#bbf7d0' if ion2 else '#bfdbfe'};">{'🟢 ออนไลน์' if ion2 else '⚪ ออฟไลน์'}</div>
                  </div>
                  <div style="font-size:17px;display:flex;gap:10px;">📞 📹</div>
                </div>""", unsafe_allow_html=True)

                bhtml='<div class="fb-chat-body">'
                for n2 in msgs:
                    ts=""
                    if n2['timestamp']:
                        try: ts=datetime.strptime(n2['timestamp'],"%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                        except: ts=str(n2['timestamp'])[11:16]
                    im2=(n2['from_user']==me and n2['is_auto']==0)
                    is2=(n2['is_auto']==1 or n2['from_user']=="ระบบสรุปยอด")
                    mt=n2['message'].replace('\n','<br>')
                    if is2: bhtml+=f'<div><div class="fb-bubble-sys">{mt}</div><div class="fb-bubble-time" style="text-align:center;">{ts}</div></div>'
                    elif im2: bhtml+=f'<div style="display:flex;flex-direction:column;align-items:flex-end;"><div class="fb-bubble-out">{mt}</div><div class="fb-bubble-time r">{ts}</div></div>'
                    else: bhtml+=f'<div style="display:flex;flex-direction:column;align-items:flex-start;"><div class="fb-sender-name">{n2["from_user"]}</div><div class="fb-bubble-in">{mt}</div><div class="fb-bubble-time">{ts}</div></div>'
                bhtml+='</div>'
                st.markdown(bhtml, unsafe_allow_html=True)

                if pt!="🤖 ระบบ":
                    with st.form(key=f"rp_{pt}", clear_on_submit=True):
                        ri,rb,rl=st.columns([6,1,1])
                        rtx=ri.text_input("",placeholder=f"พิมพ์ถึง {pt}...",label_visibility="collapsed")
                        snt=rb.form_submit_button("▶",type="primary",use_container_width=True)
                        lkd=rl.form_submit_button("👍",use_container_width=True)
                        if snt and rtx.strip():
                            c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",(trip_id,pt,me,rtx.strip())); c.commit(); c.close(); st.rerun()
                        if lkd:
                            c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,datetime('now','localtime'))",(trip_id,pt,me,"👍")); c.commit(); c.close(); st.rerun()

                if msgs:
                    with st.expander("🗑️ ลบข้อความ"):
                        for n3 in msgs:
                            sh3=n3['message'][:40]+"..." if len(n3['message'])>40 else n3['message']
                            x1,x2=st.columns([4,1]); x1.caption(f"[{n3['from_user']}] {sh3}")
                            if x2.button("ลบ",key=f"dn_{n3['id']}"):
                                c=db(); c.execute("DELETE FROM notifications WHERE id=?",(n3['id'],)); c.commit(); c.close(); st.rerun()

# ═══════════════════════════════════════════════════════
# PAGE: บัญชี
# ═══════════════════════════════════════════════════════
elif menu == "account":
    al,ar=st.columns([1,1])
    with al:
        if me is None:
            st.markdown('<div class="section-head">🔐 เข้าสู่ระบบ</div>', unsafe_allow_html=True)
            lm2=st.radio("",["เลือกโปรไฟล์","สร้างบัญชีใหม่"],horizontal=True)
            if lm2=="เลือกโปรไฟล์":
                if all_users:
                    us2=st.selectbox("ชื่อของคุณ:",all_users)
                    if st.button("เข้าสู่ระบบ",type="primary",use_container_width=True):
                        st.session_state["me"]=us2; heartbeat(us2)
                        st.toast(f"👋 ยินดีต้อนรับ, {us2}!"); time.sleep(0.5); st.rerun()
                else: st.caption("ยังไม่มีบัญชี")
            else:
                nn=st.text_input("ชื่อเล่น:",placeholder="ชื่อของคุณ")
                if st.button("สร้างบัญชี",type="primary",use_container_width=True):
                    if nn.strip():
                        try:
                            c=db(); c.execute("INSERT INTO all_users (name) VALUES (?)",(nn.strip(),)); c.commit(); c.close()
                            st.session_state["me"]=nn.strip(); heartbeat(nn.strip()); time.sleep(0.5); st.rerun()
                        except: st.error("❌ ชื่อมีแล้ว")
                    else: st.error("⚠️ กรอกชื่อก่อน")
        else:
            # [FIX v6] การ์ดโปรไฟล์ — โชว์รูปจริงถ้าอัปโหลดไว้
            st.markdown(
                '<div class="card" style="display:flex;align-items:center;gap:14px;padding:16px;">'
                + avatar_html(me, avatars.get(me), size=56, font=24)
                + f'<div><div style="font-weight:800;font-size:17px;color:#000;">{me}</div>'
                  '<div style="font-size:13px;color:#16a34a;font-weight:600;">🟢 ออนไลน์อยู่</div></div>'
                  '</div>',
                unsafe_allow_html=True)

            c=db(); md=c.execute("SELECT * FROM all_users WHERE name=?",(me,)).fetchone(); c.close()

            # ── [FIX v6] แก้ชื่อ + รูปโปรไฟล์ ──────────────────
            st.markdown('<div class="section-head">👤 แก้ไขโปรไฟล์</div>', unsafe_allow_html=True)
            with st.form("edit_profile"):
                new_name = st.text_input("ชื่อที่แสดง:", value=me,
                                         help="เปลี่ยนแล้วบิล แชท และยอดหนี้เดิมจะตามไปด้วยทั้งหมด")
                new_pic  = st.file_uploader("🖼️ รูปโปรไฟล์:", type=['jpg','jpeg','png'])
                del_pic  = st.checkbox("🗑️ ลบรูปโปรไฟล์ (กลับไปใช้ตัวอักษร)",
                                       disabled=not md['avatar_blob'])
                if st.form_submit_button("💾 บันทึกโปรไฟล์", type="primary", use_container_width=True):
                    ok, err = True, ""
                    # รูปก่อน — ทำกับชื่อเดิมที่ยังไม่เปลี่ยน
                    if del_pic or new_pic:
                        blob = None if del_pic else compress_avatar(new_pic)
                        c=db(); c.execute("UPDATE all_users SET avatar_blob=? WHERE name=?",(blob,me)); c.commit(); c.close()
                    nn2 = new_name.strip()
                    if nn2 and nn2 != me:
                        ok, err = rename_user(me, nn2)
                        if ok:
                            st.session_state["me"] = nn2
                            if st.session_state.get("chat_partner") == me:
                                st.session_state["chat_partner"] = nn2
                    if ok:
                        st.toast("💾 บันทึกโปรไฟล์แล้ว!"); time.sleep(0.5); st.rerun()
                    else:
                        st.error(f"❌ {err}")

            st.markdown('<div class="section-head">⚙️ ข้อมูลรับเงิน</div>', unsafe_allow_html=True)
            with st.form("ep"):
                epp=st.text_input("📱 พร้อมเพย์:",value=md['promptpay'] or "",placeholder="เบอร์โทร / เลขบัตร 13 หลัก")
                db_b=md['bank_name'] or "-- เลือกธนาคาร --"
                bi=BANK_LIST.index(db_b) if db_b in BANK_LIST else 0
                ebn=st.selectbox("🏦 ธนาคาร:",BANK_LIST,index=bi)
                eba=st.text_input("🔢 เลขบัญชี:",value=md['bank_account'] or "")
                if st.form_submit_button("💾 บันทึก",type="primary",use_container_width=True):
                    fb=ebn if ebn!="-- เลือกธนาคาร --" else ""
                    c=db(); c.execute("UPDATE all_users SET promptpay=?,bank_name=?,bank_account=? WHERE name=?",(epp,fb,eba,me)); c.commit(); c.close()
                    st.toast("💾 บันทึกแล้ว!"); time.sleep(0.5); st.rerun()

            if st.button("🚪 ออกจากระบบ",type="secondary",use_container_width=True):
                c=db(); c.execute("DELETE FROM online_status WHERE name=?",(me,)); c.commit(); c.close()
                st.session_state["me"]=None; st.rerun()

    with ar:
        st.markdown('<div class="section-head">🌐 สมาชิกในระบบ</div>', unsafe_allow_html=True)
        if all_users:
            for u5 in all_users:
                ion3=u5 in online_users; dot3="🟢" if ion3 else "⚪"; you3=" (คุณ)" if u5==me else ""
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #dbeafe;">'
                    + avatar_html(u5, avatars.get(u5), size=32, font=12,            # [FIX v6] รูปโปรไฟล์
                                  bg="#1d4ed8" if ion3 else "#9ca3af")
                    + f'<div><div style="font-weight:600;font-size:14px;color:#000;">{u5}{you3}</div>'
                    + f'<div style="font-size:12px;color:#374151;">{dot3} {"ออนไลน์" if ion3 else "ออฟไลน์"}</div></div></div>',
                    unsafe_allow_html=True)
        else: st.caption("ยังไม่มีสมาชิก")
