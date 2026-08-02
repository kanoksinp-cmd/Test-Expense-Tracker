import streamlit as st
import os
import pandas as pd
import sqlite3
import io
from PIL import Image, ImageDraw, ImageFont
import time
import urllib.parse
import base64
import re
import requests
import qrcode
import html
import hashlib
import secrets as pysecrets
import json
from zoneinfo import ZoneInfo
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
/* ══ [FIX v21] ฟอนต์ไทย ══
   ของเดิม -apple-system/Segoe UI ไม่มีฟอนต์ไทยในสแตกเลย บน Windows เลยตกไปใช้
   Leelawadee UI / Tahoma ซึ่งวรรณยุกต์เบียดและหน้าตาเก่า
   Kanit (ไม่มีหัว ทรงเรขาคณิต) = หัวข้อ + ตัวเลขเงิน ให้ดูมีบุคลิก
   IBM Plex Sans Thai (มีหัว) = เนื้อความ อ่านยาว ๆ สบายตากว่า */
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@500;600;700&family=IBM+Plex+Sans+Thai:wght@400;500;600;700&display=swap');

:root {
    --font-body: 'IBM Plex Sans Thai','Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif;
    --font-display: 'Kanit','IBM Plex Sans Thai','Segoe UI',sans-serif;
}

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
    font-family: var(--font-body) !important;
    line-height: 1.65 !important;   /* วรรณยุกต์ไทยต้องการที่หายใจมากกว่าละติน */
    padding-top: 0 !important;
}
[data-testid="stMainBlockContainer"] { max-width: 100% !important; }

/* ══ [FIX v25] แก้อาการกระพริบที่ขอบบนตอนเลื่อนหน้าจอ ══
   สาเหตุ: แถบบนสูงรวม 94px (navbar 50 + menubar 44) แต่เนื้อหาเริ่มที่ 102px
   เหลือช่องว่าง 8px ที่ "ไม่มีอะไรบัง" — เวลาเลื่อน เนื้อหาจะวิ่งผ่านช่องแคบ ๆ นี้
   ตัวหนังสือแวบผ่านช่อง 8px เลยเห็นเป็นการกระพริบ
   วิธีแก้: วางแผ่นทึบสีพื้นหลังคลุมตั้งแต่ 0 ถึง 104px ไว้ใต้แถบบนแต่เหนือเนื้อหา */
.hdr-fill {
    position: fixed;
    top: -2px; left: 0; right: 0;   /* -2px กันเส้นบางที่ขอบบนสุดตอน zoom ไม่ลงตัว */
    height: 108px;
    background: #dbeafe;
    z-index: 2147483645;      /* [FIX v26] ดันขึ้นให้ชิดใต้ menubar กันเนื้อหาแทรก */
    pointer-events: none;
}

/* ══ [FIX v27] ต้นเหตุจริงของการกระพริบทุก 3 วินาที ══
   ระหว่างที่สคริปต์รันใหม่ Streamlit จะทำเครื่องหมาย element เดิมว่า "เก่า"
   (data-stale="true") แล้วหรี่ความทึบเหลือ 0.33 เพื่อบอกผู้ใช้ว่ากำลังโหลด
   — ตรวจจากไฟล์ของ Streamlit เองแล้ว: {secondary:.6, stale:.33}
   ปกติแทบไม่ทันเห็น แต่แอปนี้ st_autorefresh สั่งรันใหม่ทุก 3 วินาที
   จึงกลายเป็นทั้งหน้าจอวูบทุก 3 วิ = อาการกระพริบที่เจอ
   แก้โดยบังคับความทึบเต็มเสมอ และตัด transition ที่ทำให้เห็นการไล่จาง */
[data-stale="true"],
[data-stale="true"] *,
.stElementContainer[data-stale="true"],
[data-testid="stElementContainer"][data-stale="true"],
[data-testid="stVerticalBlock"][data-stale="true"],
[data-testid="stHorizontalBlock"][data-stale="true"] {
    opacity: 1 !important;
    filter: none !important;
    transition: none !important;
}
/* ปิด transition ทั่วหน้าเฉพาะที่เกี่ยวกับ opacity เพื่อไม่ให้เห็นจังหวะไล่จาง
   (ยังคง transition ของปุ่ม/hover ที่เป็น background/filter ไว้เหมือนเดิม) */
[data-testid="stAppViewContainer"] * {
    transition-property: background-color, border-color, color, box-shadow, filter !important;
}

/* ══ [FIX v26] อีกสาเหตุของการกระพริบ: scroll anchoring ══
   หน้าจอ rerun ทุก 3 วินาที (st_autorefresh) ทุกครั้งที่ DOM ถูกวาดใหม่
   เบราว์เซอร์จะพยายาม "ยึด" ตำแหน่งสกรอลล์กับ element ที่มองเห็นอยู่
   ถ้าความสูงเปลี่ยนแม้แต่นิดเดียว มันจะเลื่อนชดเชยให้ = เห็นเป็นการกระตุก
   ปิดกลไกนี้แล้วตำแหน่งสกรอลล์จะนิ่งระหว่าง rerun */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.block-container, .main .block-container {
    overflow-anchor: none !important;
}

/* กันการเด้ง (rubber-band) ตอนเลื่อนสุดขอบบนบนมือถือ ซึ่งทำให้แถบบนแวบ */
html, body {
    overscroll-behavior-y: none;
}

/* ดันขึ้น GPU layer — ลดการวาดซ้ำระหว่างเลื่อน ซึ่งเป็นอีกสาเหตุของการกระพริบ
   โดยเฉพาะบนมือถือ (หมายเหตุ: ห้ามใส่ transform ให้ตัวที่มีลูกเป็น position:fixed
   เพราะจะทำให้ลูกยึดกับตัวเองแทนที่จะยึดกับหน้าจอ — ที่ใส่ไว้ข้างล่างไม่มีเคสนั้น) */
.navbar-wrap, div.st-key-menubar, .hdr-fill {
    transform: translateZ(0);
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
}

/* ══ NAVBAR (fixed at top) ══ */
.navbar-wrap {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 2147483647;   /* [FIX v3] สูงสุดเท่าที่ browser รับได้ */
    font-family: var(--font-body);
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

div.st-key-userbtn .stButton button {
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
div.st-key-userbtn .stButton button * { color: #fff !important; }
div.st-key-userbtn .stButton button p {
    margin: 0 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}
/* วงกลม avatar — ใช้รูปถ้ามี (--nb-img) ไม่มีก็ใช้อักษรตัวแรก (--nb-av) */
div.st-key-userbtn .stButton button::before {
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
div.st-key-userbtn .stButton button:hover { filter: brightness(1.12) !important; }
/* กำลังเปิดหน้าบัญชีอยู่ → ใส่ขอบขาวรอบนอกให้รู้ว่า active */
div.st-key-userbtn .stButton button[kind="primary"] {
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

/* [FIX v21] หัวข้อ ปุ่ม และตัวเลขเงิน ใช้ Kanit เพื่อให้มีบุคลิก
   ส่วนเนื้อความยาว ๆ ยังเป็น IBM Plex Sans Thai ที่อ่านสบายกว่า */
.navbar-wrap .nb-title, .section-head,
.stButton button, div[class*="st-key-tabbar"] .stButton button,
.pf-name, .money, h1, h2, h3, h4 {
    font-family: var(--font-display) !important;
    letter-spacing: 0 !important;
}
.money { font-variant-numeric: tabular-nums; font-weight: 600; }

/* ══ [FIX v20] เก็บช่องว่างที่เกิดจาก element ล่องหน ══
   ก่อนหน้าเนื้อหาจริงมี element อยู่ 7 ตัวที่ไม่แสดงอะไรในหน้าเลย
   (แท็ก <style> 2 ตัว, navbar/menubar/ปุ่มโปรไฟล์ ที่เป็น position:fixed,
   คอนเทนเนอร์ซ่อน และช่องสำรองของป๊อปอัพ)
   แต่ stVerticalBlock ใส่ gap ระหว่างลูกทุกตัว ต่อให้ลูกสูง 0
   → ได้ช่องว่างเปล่า ๆ ราว 7 × 1rem ≈ 112px ใต้แถบเมนู
   วิธีแก้: ดึงออกจาก flow ด้วย position:absolute เพราะลูกที่ absolute
   ไม่ถูกนับใน gap ของ flexbox (ตัวที่เป็น fixed อยู่แล้วยังแสดงปกติ) */
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdownContainer"] > style),
[data-testid="stElementContainer"]:has(.navbar-wrap),
[data-testid="stElementContainer"]:has(.hdr-fill),
[data-testid="stElementContainer"]:has(.flash-wrap),
[data-testid="stElementContainer"]:has(.flash-slot),
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div.st-key-menubar),
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div.st-key-userbtn),
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div.st-key-hidden_utils) {
    position: absolute !important;
    height: 0 !important; min-height: 0 !important;
    margin: 0 !important; padding: 0 !important;
    overflow: visible !important;
}

/* ══ PUSH CONTENT DOWN so fixed header doesn't cover it ══
   [FIX] เดิมมี .main .block-container{padding-top:8rem} ซ้อนกับ
   .block-container{padding-top:106px} → specificity ชนกัน ทำให้ระยะเพี้ยน
   ตอนนี้ประกาศค่าเดียวคุมทั้งสองตัวเลือก */
.block-container,
.main .block-container {
    padding-top: 102px !important;   /* navbar(50) + menubar(44) + เว้น 8 */
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
    div.st-key-userbtn .stButton button { max-width:104px !important; }
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

/* ══ [FIX v19] แถบแท็บที่ทำเองด้วยปุ่ม — หน้าตาให้เหมือน st.tabs เดิม ══
   selector ใช้ [class*="st-key-tabbar"] เพื่อครอบทุกแถบโดยไม่ต้องเขียนซ้ำ */
div[class*="st-key-tabbar"] {
    background: #eff6ff !important;
    border-bottom: 2px solid #93c5fd !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0 4px !important;
    margin-bottom: 14px !important;
}
div[class*="st-key-tabbar"] div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}
div[class*="st-key-tabbar"] div[data-testid="column"] {
    padding: 0 !important; min-width: 0 !important;
}
div[class*="st-key-tabbar"] .stButton { margin: 0 !important; }
div[class*="st-key-tabbar"] .stButton button {
    border-radius: 0 !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    background: transparent !important;
    color: #1e40af !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 10px 6px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    box-shadow: none !important;
}
div[class*="st-key-tabbar"] .stButton button p { color: inherit !important; margin: 0 !important; }
div[class*="st-key-tabbar"] .stButton button:hover {
    background: rgba(29,78,216,.07) !important;
}
div[class*="st-key-tabbar"] .stButton button[kind="primary"] {
    background: #fff !important;
    color: #1d4ed8 !important;
    border-bottom: 3px solid #1d4ed8 !important;
}
div[class*="st-key-tabbar"] .stButton button[kind="primary"] p { color: #1d4ed8 !important; }

/* ช่องว่างสำรองของป๊อปอัพ — ไม่กินพื้นที่ มีไว้ให้จำนวน element คงที่ */
.flash-slot { display: none; }

/* [FIX v20] สำรองสำหรับเบราว์เซอร์เก่าที่ไม่รองรับ :has()
   ตัด margin ของ element ล่องหนเท่าที่ทำได้โดยไม่ต้องพึ่ง :has() */
[data-testid="stMarkdownContainer"]:empty { display: none !important; }
[data-testid="stElementContainer"]:empty {
    display: none !important; height: 0 !important; margin: 0 !important;
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

/* ══ [FIX v21] ยอดของฉัน — ฉากเปิดของหน้าหลัก ══
   ตัวเลขใหญ่คือพระเอก ที่เหลือเงียบหมด */
.hero {
    background: #fff; border: 1.5px solid #bfdbfe; border-radius: 16px;
    padding: 16px 18px 18px; margin-bottom: 14px;
    box-shadow: 0 2px 10px rgba(29,78,216,.06);
}
.hero-top { display:flex; align-items:center; gap:11px; margin-bottom:14px; }
.hero-trip { min-width:0; flex:1; }
.hero-name {
    font-family: var(--font-display); font-weight:600; font-size:16px; color:#000 !important;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap; line-height:1.4;
}
.hero-meta { font-size:12px; color:#6b7280 !important; line-height:1.5; }
.hero-lbl {
    font-size:12px; font-weight:600; color:#6b7280 !important;
    letter-spacing:.04em; margin-bottom:2px;
}
.hero-amt {
    font-family: var(--font-display); font-weight:700;
    font-size:44px; line-height:1.15; letter-spacing:-.02em;
    font-variant-numeric: tabular-nums;
}
.hero-baht { font-size:20px; font-weight:500; margin-left:6px; opacity:.75; }
.hero-sub { font-size:12px; color:#6b7280 !important; margin-top:5px; line-height:1.5; }
@media (max-width:600px) { .hero-amt { font-size:38px; } }

/* ══ [FIX v21] แผนโอนเงินแบบเส้นโยง — ฉากเด่นของแอป ══ */
.flow {
    display:flex; align-items:flex-start; gap:10px;
    background:#fff; border:1.5px solid #bfdbfe; border-radius:14px;
    padding:16px 14px 12px; margin-bottom:10px;
}
.flow-me { border:2px solid #1d4ed8; background:#f5f9ff; }
.flow-side { width:78px; flex-shrink:0; display:flex; flex-direction:column; align-items:center; gap:6px; }
.flow-nm {
    font-size:12px; font-weight:600; color:#000 !important; text-align:center;
    line-height:1.35; word-break:break-word;
}
.flow-mid { flex:1; min-width:0; display:flex; flex-direction:column; align-items:center; padding-top:4px; }
.flow-amt {
    font-family:var(--font-display); font-weight:700; font-size:19px;
    color:#dc2626 !important; line-height:1.2; white-space:nowrap;
}
/* เส้นประ + จุดวิ่ง บอกทิศทางว่าเงินไหลไปทางไหน */
.flow-line {
    position:relative; width:100%; height:2px; margin:7px 0 5px;
    background-image:linear-gradient(90deg,#93c5fd 55%,transparent 0);
    background-size:9px 2px; background-repeat:repeat-x;
}
.flow-dot {
    position:absolute; top:50%; left:0; width:8px; height:8px; border-radius:50%;
    background:#1d4ed8; transform:translateY(-50%);
    /* [FIX v27] ผูกจังหวะกับนาฬิกาเดียวกันทุกครั้งที่วาดใหม่
       เดิม animation เริ่มนับใหม่ทุก rerun (ทุก 3 วิ) จุดจึงกระโดดกลับไปตั้งต้น
       negative delay ที่หารลงตัวกับรอบ ทำให้ต่อเนื่องเหมือนไม่เคยหยุด */
    animation: flowDot 3s linear infinite;
    animation-delay: -0.001s;
}
@keyframes flowDot {
      0% { left:0;    opacity:0; }
     12% { opacity:1; }
     88% { opacity:1; }
    100% { left:100%; opacity:0; }
}
@media (prefers-reduced-motion: reduce) {
    .flow-dot { animation:none; left:calc(50% - 4px); }
}
.flow-cap { font-size:11px; color:#6b7280 !important; }
.flow-clear {
    background:#f0fdf4; border:1.5px solid #86efac; border-radius:14px;
    padding:26px 18px; text-align:center; font-size:34px; margin-bottom:10px;
}
.flow-clear-t { font-family:var(--font-display); font-size:16px; font-weight:600; color:#15803d !important; margin-top:6px; }
.flow-clear-s { font-size:12.5px; color:#166534 !important; }
@media (max-width:600px) {
    .flow-side { width:64px; }
    .flow-amt { font-size:17px; }
}

/* ══ [FIX v21] หน้าจอว่าง — บอกทางต่อ ไม่ใช่แค่บอกว่าไม่มี ══ */
.empty {
    background:#fff; border:1.5px dashed #93c5fd; border-radius:14px;
    padding:30px 20px 22px; text-align:center; margin-bottom:12px;
}
.empty-ico { font-size:34px; line-height:1; }
.empty-t { font-family:var(--font-display); font-weight:600; font-size:15.5px; color:#000 !important; margin-top:9px; }
.empty-s { font-size:12.5px; color:#6b7280 !important; margin-top:4px; line-height:1.6; }

/* ══ [FIX v21] แถวบิลพร้อม thumbnail สลิป ══ */
.bill-row {
    display:flex; align-items:center; gap:12px;
    background:#fff; border:1.5px solid #bfdbfe; border-radius:12px;
    padding:10px 13px; margin-bottom:-6px;
}
.bill-slip {
    width:48px; height:48px; border-radius:9px; flex-shrink:0;
    background-size:cover; background-position:center;
    border:1px solid #bfdbfe;
}
.bill-noslip {
    background:#eff6ff; display:flex; align-items:center; justify-content:center;
    font-size:9.5px; color:#93c5fd !important; text-align:center; line-height:1.25;
}
.bill-mid { flex:1; min-width:0; }
.bill-desc {
    font-family:var(--font-display); font-weight:600; font-size:14.5px; color:#000 !important;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap; line-height:1.4;
}
.bill-meta { font-size:11.5px; color:#6b7280 !important; line-height:1.5;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.bill-amt {
    font-family:var(--font-display); font-weight:700; font-size:16px;
    color:#1d4ed8 !important; flex-shrink:0; white-space:nowrap;
}

/* ══ [FIX v22] กล่อง QR พร้อมเพย์ ══ */
.qr-box {
    background:#fff; border:1.5px solid #bfdbfe; border-radius:12px;
    padding:10px 10px 8px; text-align:center;
}
.qr-box img { width:100%; max-width:210px; height:auto; display:block; margin:0 auto; border-radius:6px; }
.qr-cap { font-size:11.5px; color:#374151 !important; line-height:1.55; margin-top:5px; }
.qr-cap b { color:#dc2626 !important; font-family:var(--font-display); font-size:14px; }

/* ══ [FIX v28] ของที่ต้องหิ้ว ══ */
.pk-bar { height:8px; background:#dbeafe; border-radius:6px; overflow:hidden; margin:2px 0 6px; }
.pk-bar-fill { height:100%; background:#16a34a; border-radius:6px; transition:width .3s; }
.pk-stat { font-size:12px; color:#6b7280 !important; margin-bottom:10px; }
.pk-who {
    display:inline-block; color:#fff !important; border-radius:20px;
    padding:1px 9px; font-size:11px; font-weight:600; margin-left:6px;
    vertical-align:middle;
}
.pk-none { background:#9ca3af; }

/* ══ [FIX v28] แคมป์: จุดกางเต็นท์ + พยากรณ์อากาศ ══ */
.camp-loc {
    display:flex; align-items:center; gap:12px;
    background:#fff; border:1.5px solid #bfdbfe; border-radius:12px;
    padding:13px 15px; margin-bottom:10px;
}
.camp-pin { font-size:26px; line-height:1; }
.camp-nm { font-family:var(--font-display); font-weight:600; font-size:15px; color:#000 !important; }
.camp-co { font-size:12px; color:#6b7280 !important; font-variant-numeric:tabular-nums; }
.camp-day {
    display:flex; align-items:center; gap:12px;
    background:#fff; border:1.5px solid #bfdbfe; border-radius:12px;
    padding:11px 14px; margin-bottom:7px;
}
.camp-day-warn { border-color:#fdba74; background:#fff7ed; }
.camp-dt {
    width:52px; flex-shrink:0; font-family:var(--font-display);
    font-weight:600; font-size:13px; color:#1e40af !important;
}
.camp-ico { font-size:26px; flex-shrink:0; line-height:1; }
.camp-mid { flex:1; min-width:0; }
.camp-txt { font-size:14px; font-weight:600; color:#000 !important; line-height:1.4; }
.camp-sub { font-size:11.5px; color:#6b7280 !important; line-height:1.5; }
.camp-tmp {
    font-family:var(--font-display); font-weight:700; font-size:19px;
    color:#dc2626 !important; flex-shrink:0; font-variant-numeric:tabular-nums;
}
.camp-tmin { font-size:14px; color:#6b7280 !important; font-weight:500; }
@media (max-width:600px) {
    .camp-sub { font-size:10.5px; }
    .camp-tmp { font-size:17px; }
}

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

/* ══ [FIX v17] ป๊อปอัพแจ้งเตือนกลางจอ — โชว์ 3 วิแล้วจางหายเอง ══
   ใช้ CSS animation ทำการหายไป ไม่ใช้ JS timer เพราะหน้าจอ rerun ทุก 3 วิ
   (st_autorefresh) ซึ่งจะล้าง timer ของ JS ทิ้งทุกครั้ง
   pointer-events:none เพื่อให้กดทะลุผ่านได้ ไม่บังปุ่มข้างหลัง */
.flash-wrap {
    position: fixed; inset: 0; z-index: 2147483647;
    display: flex; align-items: center; justify-content: center;
    pointer-events: none;
}
.flash-box {
    display: flex; align-items: center; gap: 12px;
    min-width: 230px; max-width: 80vw;
    padding: 18px 26px;
    border-radius: 14px;
    background: #1e3a8a;
    color: #fff !important;
    font-size: 16px; font-weight: 700; line-height: 1.45;
    text-align: left;
    box-shadow: 0 12px 40px rgba(0,0,0,.35);
    animation: flashPop 3s cubic-bezier(.22,1,.36,1) forwards;
}
.flash-box * { color: #fff !important; }
.flash-box .flash-ico { font-size: 24px; flex-shrink: 0; line-height: 1; }
.flash-ok   { background: #16a34a; }
.flash-err  { background: #dc2626; }
.flash-warn { background: #b45309; }
.flash-info { background: #1d4ed8; }
@keyframes flashPop {
      0% { opacity: 0; transform: translateY(14px) scale(.92); }
      7% { opacity: 1; transform: translateY(0)    scale(1);   }
     78% { opacity: 1; transform: translateY(0)    scale(1);   }
    100% { opacity: 0; transform: translateY(-8px) scale(.97); visibility: hidden; }
}
@media (max-width:600px) {
    .flash-box { min-width: 0; padding: 15px 20px; font-size: 15px; }
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
# [FIX v26] ปรับรอบรีเฟรชได้จากที่เดียว — ถ้ายังรู้สึกว่าหน้าจอกระตุก
#   ให้เพิ่มตัวเลขนี้ (เช่น 8000 = 8 วินาที) หรือใส่ 0 เพื่อปิดการรีเฟรชอัตโนมัติ
#   ทุกครั้งที่รีเฟรช Streamlit จะวาด DOM ใหม่ทั้งหน้า ยิ่งถี่ยิ่งมีโอกาสเห็นสะดุด
#   หมายเหตุ: ถ้าปิด สถานะ "ออนไลน์" ของเพื่อนจะไม่อัปเดตเองจนกว่าจะกดอะไรสักอย่าง
AUTOREFRESH_MS = 3000

with st.container(key="hidden_utils"):
    if AUTOREFRESH_MS:
        st_autorefresh(interval=AUTOREFRESH_MS, limit=None, key="live_refresh")

# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────
# [FIX v11] ตำแหน่งไฟล์ DB ตั้งค่าได้ผ่าน secrets/env — เผื่อวันหนึ่งย้ายไป
#   ชี้ที่ volume ถาวร โดยไม่ต้องแก้โค้ด
DB_FILE = os.environ.get("TRIP_DB_PATH", "trip_database.db")
TZ      = ZoneInfo("Asia/Bangkok")
MAX_UPLOAD_MB = 8

BANK_LIST = ["-- เลือกธนาคาร --","กสิกรไทย (KBank)","ไทยพาณิชย์ (SCB)","กรุงไทย (KTB)",
             "กรุงเทพ (BBL)","กรุงศรีอยุธยา (BAY)","ทหารไทยธนชาต (TTB)","ออมสิน (GSB)","ธ.ก.ส.","ยูโอบี (UOB)"]

def db():
    """[FIX v11] timeout=15 + WAL — เดิมไม่ได้ตั้งทั้งคู่ พอมีหลายคนใช้พร้อมกัน
    (heartbeat เขียนทุก 3 วิ/คน) จะเจอ 'database is locked' ทันที
    WAL ให้อ่านคู่ขนานกับเขียนได้ ส่วน busy_timeout ให้รอคิวแทนที่จะโยน error"""
    # [FIX v25] isolation_level=None + WAL ทำให้ connection ที่หลุดไม่ค้างล็อกยาว
    c = sqlite3.connect(DB_FILE, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=15000")
    c.execute("PRAGMA synchronous=NORMAL")
    return c

# ── [FIX v11] เวลา ────────────────────────────────────────────
def now_str():
    """เวลาไทยเป็นสตริง 'YYYY-MM-DD HH:MM:SS'
    ของเดิมใช้ SQLite datetime('now','localtime') ซึ่งอิง timezone ของ
    *เซิร์ฟเวอร์* — บน Streamlit Cloud คือ UTC → เวลาในแชทเพี้ยนไป 7 ชม.
    ย้ายมาคำนวณฝั่ง Python ด้วย ZoneInfo จะได้ผลเหมือนกันทุกที่ที่ deploy"""
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

def now_minus(seconds):
    return (datetime.now(TZ) - pd.Timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")

# ── [FIX v11] ความปลอดภัยของข้อความ ──────────────────────────
def esc(v):
    """escape ก่อนยัดเข้า unsafe_allow_html — ชื่อผู้ใช้/ชื่อทริป/ข้อความแชท
    เป็นข้อความที่ผู้ใช้พิมพ์เองทั้งหมด ถ้าไม่ escape แท็กที่ไม่สมดุลจะทำ
    layout พังทั้งหน้า (เคสเดียวกับที่ navbar เคยพัง) และเปิดช่อง inject"""
    return html.escape(str(v if v is not None else ""), quote=True)

NAME_MAXLEN = 24
def valid_name(n):
    """คืน (ok, ข้อความ error) — กฎสำคัญที่สุดคือห้ามมีลูกน้ำ เพราะ
    expenses.split_members เก็บรายชื่อคนหารเป็น 'ก,ข,ค' ถ้าชื่อมีลูกน้ำ
    การหารบิลจะเพี้ยนถาวรและกู้ไม่ได้"""
    n = (n or "").strip()
    if not n:                       return False, "กรุณากรอกชื่อ"
    if len(n) > NAME_MAXLEN:        return False, f"ชื่อยาวเกิน {NAME_MAXLEN} ตัวอักษร"
    if "," in n:                    return False, "ชื่อห้ามมีเครื่องหมายจุลภาค ( , )"
    if any(ch in n for ch in "<>&\"'"):  return False, "ชื่อห้ามมีอักขระ < > & \" '"
    return True, ""

# ── [FIX v11] รหัส PIN ────────────────────────────────────────
def hash_pin(pin, salt=None):
    """PBKDF2-SHA256 — ไม่เก็บ PIN เป็น plaintext"""
    salt = salt or pysecrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", str(pin).encode(), salt.encode(), 100_000)
    return h.hex(), salt

def check_pin(pin, stored_hash, salt):
    if not stored_hash or not salt: return False
    calc, _ = hash_pin(pin, salt)
    return pysecrets.compare_digest(calc, stored_hash)

def init_db():
    conn = db(); cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS all_users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cur.execute('CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, status INTEGER DEFAULT 0)')
    cur.execute('CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, name TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, description TEXT, amount REAL, payer_name TEXT, split_members TEXT, image_blob BLOB)')
    cur.execute('CREATE TABLE IF NOT EXISTS settlements (id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER, debtor TEXT, creditor TEXT, amount REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    cur.execute('CREATE TABLE IF NOT EXISTS online_status (name TEXT PRIMARY KEY, last_seen DATETIME)')
    # [FIX v28] ของที่ต้องหิ้วไปแคมป์ — ใครรับหน้าที่อะไร
    cur.execute("""CREATE TABLE IF NOT EXISTS packing (
        id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER,
        item TEXT NOT NULL, qty TEXT, assignee TEXT,
        done INTEGER DEFAULT 0, note TEXT,
        added_by TEXT, expense_id INTEGER,
        timestamp DATETIME)""")
    cur.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, trip_id INTEGER,
        to_user TEXT, from_user TEXT, message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_auto INTEGER DEFAULT 0, is_read INTEGER DEFAULT 0)''')
    # [FIX v11] เดิมใช้ except เปล่า ซึ่งกลืน error ทุกชนิด
    #   ALTER TABLE ที่คอลัมน์มีอยู่แล้วจะโยน OperationalError เท่านั้น
    #   จับให้ตรงชนิด เพื่อไม่ให้ปัญหา DB จริง ๆ เงียบหายไป
    for col, dtype in [('promptpay','TEXT'),('bank_name','TEXT'),('bank_account','TEXT'),
                       ('avatar_blob','BLOB'),('pin_hash','TEXT'),('pin_salt','TEXT')]:
        try: conn.execute(f"ALTER TABLE all_users ADD COLUMN {col} {dtype}")
        except sqlite3.OperationalError: pass
    try: conn.execute("ALTER TABLE trips ADD COLUMN trip_date TEXT")
    except sqlite3.OperationalError: pass
    # [FIX v22] split_detail = JSON บอกวิธีหาร (ไม่มี/ว่าง = หารเท่ากันแบบเดิม)
    #   เก็บแยกจาก split_members เพื่อให้บิลเก่าที่มีอยู่แล้วยังอ่านได้เหมือนเดิม
    # [FIX v24] created_by = คนที่สร้าง Event (ใช้จำกัดสิทธิ์การลบ)
    #   Event เก่าที่สร้างก่อนมีคอลัมน์นี้จะเป็น NULL = ไม่ทราบผู้สร้าง
    try: conn.execute("ALTER TABLE trips ADD COLUMN created_by TEXT")
    except sqlite3.OperationalError: pass
    # [FIX v28] จุดกางเต็นท์/จุดนัดพบ — เก็บพิกัดไว้ใช้ทั้งแผนที่และพยากรณ์อากาศ
    for _c, _t in [("place_name","TEXT"), ("lat","REAL"), ("lon","REAL")]:
        try: conn.execute(f"ALTER TABLE trips ADD COLUMN {_c} {_t}")
        except sqlite3.OperationalError: pass
    try: conn.execute("ALTER TABLE expenses ADD COLUMN split_detail TEXT")
    except sqlite3.OperationalError: pass
    # [FIX v22] สลิปยืนยันการโอน
    try: conn.execute("ALTER TABLE settlements ADD COLUMN slip_blob BLOB")
    except sqlite3.OperationalError: pass
    for col in ['is_auto','is_read','timestamp']:
        try: conn.execute(f"ALTER TABLE notifications ADD COLUMN {col} {'DATETIME DEFAULT CURRENT_TIMESTAMP' if col=='timestamp' else 'INTEGER DEFAULT 0'}")
        except sqlite3.OperationalError: pass

    # [FIX v11] กันเพิ่มสมาชิกซ้ำ — เดิมไม่มี UNIQUE ทำให้คนเดียวถูกนับสองครั้ง
    #   ตอนหารบิล ต้องลบตัวซ้ำที่ค้างอยู่ก่อนถึงจะสร้าง index ได้
    conn.execute("""DELETE FROM members WHERE id NOT IN
                    (SELECT MIN(id) FROM members GROUP BY trip_id, name)""")
    try: conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_members ON members(trip_id, name)")
    except sqlite3.OperationalError: pass

    # ดัชนีตามคอลัมน์ที่ query บ่อย (หน้าจอ refresh ทุก 3 วิ)
    for ddl in [
        "CREATE INDEX IF NOT EXISTS ix_exp_trip   ON expenses(trip_id)",
        "CREATE INDEX IF NOT EXISTS ix_notif_trip ON notifications(trip_id, to_user, is_read)",
        "CREATE INDEX IF NOT EXISTS ix_settle     ON settlements(trip_id)",
        "CREATE INDEX IF NOT EXISTS ix_packing    ON packing(trip_id)",
    ]:
        try: conn.execute(ddl)
        except sqlite3.OperationalError: pass

    conn.commit(); conn.close()

def compress_image(f):
    if f is None: return None
    img = Image.open(f)
    if img.mode in ("RGBA","P"): img = img.convert("RGB")
    img.thumbnail((800,800)); buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70); return buf.getvalue()

# [FIX v6] ── รูปโปรไฟล์ ────────────────────────────────────────
def compress_avatar(f):
    """ครอปเป็นสี่เหลี่ยมจัตุรัสตรงกลางแล้วย่อเหลือ 400px
    [FIX v10] เดิมเก็บแค่ 160px — พอกดดูรูปใหญ่แล้วแตก จึงเก็บต้นฉบับใหญ่ขึ้น
    ส่วนวงกลมเล็ก ๆ ให้ไปใช้ avatar_thumb_uri() ที่ย่อ+แคชไว้แทน"""
    if f is None: return None
    img = Image.open(f)
    if img.mode in ("RGBA","P","LA"): img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w-side)//2, (h-side)//2, (w+side)//2, (h+side)//2))
    img = img.resize((400,400), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=78)
    return buf.getvalue()

def avatar_uri(blob):
    if not blob: return None
    return "data:image/jpeg;base64," + base64.b64encode(blob).decode()

@st.cache_data(show_spinner=False, max_entries=64)
def avatar_thumb_uri(blob, px=96):
    """[FIX v10] data URI ขนาดเล็กสำหรับวงกลม avatar
    จำเป็นเพราะรูปต้นฉบับ 400px ถูกฝังเป็น base64 ใน HTML/CSS ทุกรอบ
    ที่หน้าจอ refresh (ทุก 3 วิ) — ถ้าใช้ต้นฉบับจะกินแบนด์วิดท์ฟรี ๆ
    แคชด้วย st.cache_data โดยใช้ตัว blob เป็น key จึงย่อแค่ครั้งเดียว"""
    if not blob: return None
    img = Image.open(io.BytesIO(blob)); img.thumbnail((px, px), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

# [FIX v21] สีประจำตัวของแต่ละคน — ได้จากการ hash ชื่อ จึงคงที่เสมอ
#   ทั้งในบิล แชท และสรุปเงิน ทำให้กวาดตาหาตัวเองเจอเร็วขึ้น
#   เลือกจากชุดสีที่คุมโทนไว้แล้ว (ไม่สุ่ม hue อิสระ) เพื่อไม่ให้ตีกับธีมน้ำเงิน
#   และคุมความสว่างให้ตัวอักษรขาวอ่านออกทุกสี
PERSON_COLORS = ["#1d4ed8","#0891b2","#7c3aed","#c026d3","#db2777",
                 "#e11d48","#ea580c","#ca8a04","#16a34a","#0d9488",
                 "#4f46e5","#9333ea"]

def person_color(name):
    if not name: return "#6b7280"
    h = hashlib.md5(str(name).encode("utf-8")).hexdigest()
    return PERSON_COLORS[int(h[:8], 16) % len(PERSON_COLORS)]

def avatar_html(name, blob=None, size=32, font=12, bg=None):
    """คืน <div> วงกลมเดียวแบบบรรทัดเดียว — ถ้ามีรูปใช้รูป ถ้าไม่มีใช้อักษรตัวแรก"""
    if bg is None: bg = person_color(name)
    uri = avatar_thumb_uri(blob, max(96, size * 3))
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
    ok, err = valid_name(new)          # [FIX v11] กันลูกน้ำ/แท็ก HTML
    if not ok: return False, err
    new = new.strip()
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

# ── [FIX v11] สำรอง / กู้คืนข้อมูล ────────────────────────────
BACKUP_TABLES = ["all_users","trips","members","expenses","settlements","notifications","packing"]

def export_backup():
    """[FIX v11] Streamlit Community Cloud ใช้ filesystem ชั่วคราว —
    ไฟล์ trip_database.db จะถูกลบทิ้งทุกครั้งที่ reboot หรือ deploy ใหม่
    ข้อมูลทั้งหมดหายโดยไม่มีคำเตือน จึงต้องมีทางดึงออกมาเก็บเอง
    (BLOB แปลงเป็น base64 เพื่อให้เป็น JSON ได้)"""
    c = db(); out = {"exported_at": now_str(), "version": 1, "data": {}}
    for t in BACKUP_TABLES:
        rows = []
        for r in c.execute(f"SELECT * FROM {t}").fetchall():
            d = {}
            for k in r.keys():
                v = r[k]
                d[k] = {"__b64__": base64.b64encode(v).decode()} if isinstance(v, bytes) else v
            rows.append(d)
        out["data"][t] = rows
    c.close()
    return json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8")

def import_backup(raw, wipe=True):
    """คืนค่า (ok, ข้อความ) — wipe=True คือล้างของเดิมแล้วเขียนทับทั้งหมด"""
    try:
        payload = json.loads(raw.decode("utf-8"))
        data = payload["data"]
    except (ValueError, KeyError, UnicodeDecodeError) as e:
        return False, f"ไฟล์ไม่ถูกต้อง: {e}"
    c = db()
    try:
        for t in BACKUP_TABLES:
            if t not in data: continue
            if wipe: c.execute(f"DELETE FROM {t}")
            have = {r[1] for r in c.execute(f"PRAGMA table_info({t})").fetchall()}
            for row in data[t]:
                row = {k: v for k, v in row.items() if k in have}   # ข้ามคอลัมน์ที่ schema ใหม่ไม่มี
                for k, v in row.items():
                    if isinstance(v, dict) and "__b64__" in v:
                        row[k] = base64.b64decode(v["__b64__"])
                cols = ",".join(row.keys()); qs = ",".join("?" * len(row))
                c.execute(f"INSERT OR REPLACE INTO {t} ({cols}) VALUES ({qs})", list(row.values()))
        c.commit()
    except sqlite3.Error as e:
        c.rollback(); c.close(); return False, f"กู้คืนไม่สำเร็จ: {e}"
    c.close()
    return True, "กู้คืนข้อมูลเรียบร้อย"

# ── [FIX v17] ป๊อปอัพแจ้งเตือนกลางจอ ──────────────────────────
#   แทน st.toast / st.success ที่อยู่มุมจอและหายเร็วเกินจะทันอ่าน
#   เก็บข้อความไว้ใน session_state พร้อมเวลาที่ตั้ง แล้ววาดใหม่ทุก rerun
#   จนกว่าจะครบ 3 วินาที — จำเป็นเพราะ st_autorefresh สั่ง rerun ทุก 3 วิ
#   ถ้าวาดครั้งเดียวแล้วลบทิ้ง ข้อความจะหายกลางคันเมื่อ rerun มาถึงก่อนเวลา
FLASH_SECONDS = 3.0
FLASH_ICONS = {"ok": "✅", "err": "❌", "warn": "⚠️", "info": "ℹ️"}

def flash(msg, kind="ok"):
    """ตั้งข้อความให้เด้งกลางจอ — เรียกก่อน st.rerun() ได้เลย ไม่ต้อง time.sleep"""
    st.session_state["flash"] = (str(msg), kind, time.time())

def render_flash():
    """[FIX v19] วาด element เสมอ (ว่างก็วาด) เพื่อให้จำนวน element คงที่ทุก rerun
    ถ้าโผล่บ้างหายบ้าง Streamlit จะ remount element ที่อยู่ถัดลงไป ทำให้
    แท็บที่ผู้ใช้เลือกไว้เด้งกลับอันแรก"""
    f = st.session_state.get("flash")
    if not f:
        st.markdown('<div class="flash-slot"></div>', unsafe_allow_html=True)
        return
    msg, kind, t0 = f
    elapsed = time.time() - t0
    if elapsed >= FLASH_SECONDS:
        st.session_state.pop("flash", None)
        st.markdown('<div class="flash-slot"></div>', unsafe_allow_html=True)
        return
    # เลื่อน animation ให้ไปเริ่มตรงจุดที่ค้างไว้ ข้อความจึงหายตรงเวลา
    # ไม่ว่าจะเกิด rerun กี่รอบระหว่างทาง
    cls = {"ok": "flash-ok", "err": "flash-err",
           "warn": "flash-warn", "info": "flash-info"}.get(kind, "flash-info")
    st.markdown(
        f'<div class="flash-wrap"><div class="flash-box {cls}" '
        f'style="animation-delay:-{elapsed:.2f}s;">'
        f'<span class="flash-ico">{FLASH_ICONS.get(kind, "ℹ️")}</span>'
        f'<span>{esc(msg)}</span></div></div>',
        unsafe_allow_html=True)

# ── [FIX v22] QR พร้อมเพย์ที่ฝังยอดเงินไว้ ────────────────────
#   มาตรฐาน EMVCo ที่ธนาคารไทยใช้ — สแกนแล้วยอดเด้งมาเอง ไม่ต้องพิมพ์
#   CRC เป็น CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF)
#   ตรวจแล้วว่าให้ค่า 0x29B1 กับสตริง "123456789" ตรงตามค่าตรวจสอบมาตรฐาน
def _pp_crc16(data):
    crc = 0xFFFF
    for ch in data.encode("ascii"):
        crc ^= ch << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def _pp_tlv(tag, value):
    return f"{tag}{len(value):02d}{value}"

def promptpay_target(raw):
    """แปลงเบอร์/เลขบัตรเป็นรูปแบบที่ QR ต้องการ — คืน (tag, ค่า) หรือ (None, None)"""
    d = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if len(d) == 13:                        return "02", d              # เลขบัตรประชาชน
    if len(d) == 10 and d.startswith("0"):  return "01", "0066" + d[1:] # 0812345678
    if len(d) == 9:                         return "01", "0066" + d     # 812345678
    if len(d) == 11 and d.startswith("66"): return "01", "00" + d       # 66812345678
    if len(d) == 15:                        return "03", d              # e-wallet
    return None, None

def promptpay_payload(raw, amount=None):
    tag, val = promptpay_target(raw)
    if not tag: return None
    merchant = _pp_tlv("00", "A000000677010111") + _pp_tlv(tag, val)
    p  = _pp_tlv("00", "01")
    p += _pp_tlv("01", "12" if amount else "11")   # 12 = ใช้ครั้งเดียว (มียอด)
    p += _pp_tlv("29", merchant)
    p += _pp_tlv("53", "764")                       # THB
    if amount: p += _pp_tlv("54", f"{float(amount):.2f}")
    p += _pp_tlv("58", "TH") + "6304"
    return p + _pp_crc16(p)

@st.cache_data(show_spinner=False, max_entries=128)
def promptpay_qr_png(raw, amount=None, box=10):
    """[FIX v24] คืน PNG bytes สำหรับปุ่มดาวน์โหลด/แชร์
    box ใหญ่กว่าที่แสดงบนจอ เพื่อให้ไฟล์ที่บันทึกไปคมพอให้แอปธนาคารสแกนติด"""
    payload = promptpay_payload(raw, amount)
    if not payload: return None
    q = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=box, border=3)
    q.add_data(payload); q.make(fit=True)
    img = q.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return buf.getvalue()

@st.cache_data(show_spinner=False, max_entries=128)
def promptpay_qr_uri(raw, amount=None, box=7):
    """คืน data URI ของรูป QR — แคชไว้เพราะหน้าจอ rerun ทุก 3 วิ
    ถ้าสร้างใหม่ทุกรอบจะเปลืองเวลาโดยเปล่าประโยชน์"""
    payload = promptpay_payload(raw, amount)
    if not payload: return None
    q = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=box, border=2)
    q.add_data(payload); q.make(fit=True)
    img = q.make_image(fill_color="#0f2a6b", back_color="white").convert("RGB")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── [FIX v28] พยากรณ์อากาศ + พระอาทิตย์ขึ้น-ตก ────────────────
#   ใช้ Open-Meteo: ฟรี ไม่ต้องสมัคร ไม่ต้องใช้ API key
#   ที่แคมป์ ฝนตกกับมืดเร็วคือสองเรื่องที่ทำให้ทริปพัง จึงดึงมาแค่นี้พอ
WMO = {
    0:("☀️","แดดจัด"), 1:("🌤️","แดดบางส่วน"), 2:("⛅","มีเมฆบางส่วน"), 3:("☁️","เมฆมาก"),
    45:("🌫️","หมอก"), 48:("🌫️","หมอกน้ำแข็ง"),
    51:("🌦️","ฝนปรอยเบา"), 53:("🌦️","ฝนปรอย"), 55:("🌦️","ฝนปรอยหนัก"),
    61:("🌧️","ฝนเบา"), 63:("🌧️","ฝนปานกลาง"), 65:("🌧️","ฝนหนัก"),
    71:("🌨️","หิมะเบา"), 73:("🌨️","หิมะ"), 75:("🌨️","หิมะหนัก"),
    80:("🌦️","ฝนซู่เบา"), 81:("🌧️","ฝนซู่"), 82:("⛈️","ฝนซู่หนัก"),
    95:("⛈️","พายุฝนฟ้าคะนอง"), 96:("⛈️","พายุลูกเห็บ"), 99:("⛈️","พายุลูกเห็บหนัก"),
}

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_forecast(lat, lon, days=7):
    """คืน (ok, ข้อมูล|ข้อความerror) — แคช 30 นาที เพราะหน้าจอ rerun ทุก 3 วิ
    ถ้าไม่แคชจะยิง API ซ้ำจนโดนบล็อก"""
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=12, params={
            "latitude": lat, "longitude": lon,
            "daily": ("weather_code,temperature_2m_max,temperature_2m_min,"
                      "precipitation_probability_max,precipitation_sum,"
                      "wind_speed_10m_max,sunrise,sunset"),
            "timezone": "Asia/Bangkok", "forecast_days": days})
        if r.status_code != 200:
            return False, f"เรียกข้อมูลไม่สำเร็จ ({r.status_code})"
        d = r.json().get("daily")
        if not d: return False, "ไม่มีข้อมูลพยากรณ์สำหรับพิกัดนี้"
        return True, d
    except requests.RequestException as e:
        return False, f"ต่ออินเทอร์เน็ตไม่ได้: {e}"

def parse_latlon(text):
    """รับได้ทั้ง '18.79, 98.98' และลิงก์ Google Maps ที่มี @lat,lon หรือ q=lat,lon
    คืน (lat, lon) หรือ (None, None)"""
    t = str(text or "")
    m = (re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', t)
         or re.search(r'[?&]q=(-?\d+\.\d+),\s*(-?\d+\.\d+)', t)
         or re.search(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)', t))
    if not m: return None, None
    la, lo = float(m.group(1)), float(m.group(2))
    if -90 <= la <= 90 and -180 <= lo <= 180:
        return la, lo
    return None, None


# ── [FIX v28] สรุปทริปเป็นรูป ไว้ใช้ตอนไม่มีสัญญาณ ────────────
#   ที่แคมป์เน็ตมักไม่มี แต่แอปนี้เป็นเว็บ = เปิดไม่ได้เลยตอนไปถึง
#   จึงต้องมีทางเอาข้อมูลสำคัญออกมาเก็บไว้ในเครื่องก่อนออกเดินทาง
def _supports_thai(path):
    """ทดสอบจริงว่าฟอนต์วาดอักษรไทยได้ไหม
    เช็คแค่ว่าไฟล์เปิดได้ไม่พอ — ฟอนต์ที่ไม่มีอักษรไทยจะวาดเป็นสี่เหลี่ยมเปล่า
    จึงต้องเทียบภาพของ 'ก' กับอักขระที่ไม่มีแน่ ๆ ถ้าเหมือนกัน = เป็นสี่เหลี่ยม"""
    try:
        f = ImageFont.truetype(path, 24)
        a = Image.new("L", (30, 30), 0); ImageDraw.Draw(a).text((2, 2), "ก", font=f, fill=255)
        b = Image.new("L", (30, 30), 0); ImageDraw.Draw(b).text((2, 2), "\uFFFF", font=f, fill=255)
        return bytes(a.tobytes()) != bytes(b.tobytes()) and a.getbbox() is not None
    except (OSError, IOError, ValueError):
        return False

# ดาวน์โหลดฟอนต์ไทยมาเก็บไว้เอง ถ้าเซิร์ฟเวอร์ไม่มี
#   Sarabun เป็นฟอนต์ราชการไทย อ่านง่าย มีสัญญาอนุญาต OFL ใช้ได้เสรี
THAI_FONT_URL = ("https://raw.githubusercontent.com/google/fonts/main/"
                 "ofl/sarabun/Sarabun-Regular.ttf")
THAI_FONT_CACHE = "/tmp/Sarabun-Regular.ttf"

@st.cache_resource(show_spinner=False)
def _thai_font_path():
    """[FIX v29] หาฟอนต์ไทยแบบไม่พึ่งโชค — ลำดับความพยายาม 3 ชั้น
    1) ฟอนต์ไทยที่ติดตั้งในเครื่อง (ถ้าใส่ fonts-thai-tlwg ใน packages.txt)
    2) ฟอนต์อื่นในเครื่องที่บังเอิญมีอักษรไทย
    3) โหลด Sarabun จาก Google Fonts มาเก็บไว้ที่ /tmp แล้วใช้ต่อ
    ที่ต้องมีชั้นที่ 3 เพราะ packages.txt ต้อง reboot app ถึงจะมีผล
    และบางสภาพแวดล้อมก็ลง apt ไม่ได้เลย"""
    import glob
    preferred = [
        "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
        "/usr/share/fonts/truetype/tlwg/Sarabun.ttf",
        "/usr/share/fonts/truetype/tlwg/Loma.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifThai-Regular.ttf",
    ]
    for path in preferred:
        if os.path.exists(path) and _supports_thai(path):
            return path

    if os.path.exists(THAI_FONT_CACHE) and _supports_thai(THAI_FONT_CACHE):
        return THAI_FONT_CACHE

    # ฟอนต์ระบบตัวอื่นที่พอวาดไทยได้ (เช่น FreeSerif) — ใช้เป็นตัวสำรอง
    system_fallback = None
    for path in sorted(glob.glob("/usr/share/fonts/**/*.tt[fc]", recursive=True)):
        if _supports_thai(path):
            system_fallback = path
            break

    try:
        r = requests.get(THAI_FONT_URL, timeout=25)
        if r.status_code == 200 and len(r.content) > 20000:
            with open(THAI_FONT_CACHE, "wb") as f:
                f.write(r.content)
            if _supports_thai(THAI_FONT_CACHE):
                return THAI_FONT_CACHE
    except (requests.RequestException, OSError):
        pass

    return system_fallback

def _thai_font(size):
    path = _thai_font_path()
    if path:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()

def offline_sheet(trip_id, trip_name, trip_date, members, me):
    """รวมยอดที่ต้องจ่าย แผนโอน QR พร้อมเพย์ และของที่ต้องหิ้ว เป็นรูปเดียว"""
    net, exps, _paid = compute_net(trip_id, members)
    plan = settle_plan(net)
    c = db()
    prof = {r['name']: r['promptpay'] for r in
            c.execute("SELECT name,promptpay FROM all_users").fetchall()}
    packs = c.execute("SELECT item,qty,assignee,done FROM packing WHERE trip_id=? ORDER BY done,id",
                      (trip_id,)).fetchall()
    c.close()

    W = 820
    f_big, f_mid, f_sm = _thai_font(38), _thai_font(23), _thai_font(18)
    my_rows = [(d, cr, a) for d, cr, a in plan if me in (d, cr)]
    # [FIX v28] วาดลงผืนสูงเผื่อไว้ก่อน แล้วค่อยตัดตามความสูงจริงตอนจบ
    #   ของเดิมคำนวณความสูงล่วงหน้าแล้วประเมินพลาด ทำให้ QR กับรายการของทับกัน
    #   วิธีนี้ไม่มีทางคำนวณผิดเพราะตัดตามตำแหน่งที่วาดจริง
    img = Image.new("RGB", (W, 2400), "#ffffff")
    dr = ImageDraw.Draw(img)

    dr.rectangle([0, 0, W, 96], fill="#1d4ed8")
    dr.text((28, 20), str(trip_name or "ทริป"), font=f_big, fill="#ffffff")
    sub = f"{trip_date or ''}   ·   {len(members)} คน   ·   {len(exps)} บิล"
    dr.text((30, 64), sub, font=f_sm, fill="#bfdbfe")

    y = 122
    mine = net.get(me, 0.0)
    if mine < -0.01:
        dr.text((28, y), "คุณต้องจ่าย", font=f_sm, fill="#6b7280")
        dr.text((28, y + 24), f"{abs(mine):,.2f} บาท", font=f_big, fill="#dc2626")
    elif mine > 0.01:
        dr.text((28, y), "คุณจะได้คืน", font=f_sm, fill="#6b7280")
        dr.text((28, y + 24), f"{mine:,.2f} บาท", font=f_big, fill="#16a34a")
    else:
        dr.text((28, y + 24), "เคลียร์หมดแล้ว", font=f_big, fill="#1d4ed8")
    y += 92

    dr.line([28, y, W - 28, y], fill="#dbeafe", width=2); y += 16
    dr.text((28, y), "แผนโอนเงิน", font=f_mid, fill="#000000"); y += 34
    if not plan:
        dr.text((36, y), "ไม่มีใครต้องโอนให้ใคร", font=f_sm, fill="#6b7280"); y += 30
    for d, cr, a in plan:
        hl = me in (d, cr)
        dr.text((36, y), f"{d}  →  {cr}", font=f_sm, fill="#000000" if hl else "#6b7280")
        dr.text((W - 200, y), f"{a:,.2f} บาท", font=f_sm,
                fill="#dc2626" if hl else "#9ca3af")
        y += 32

    # QR ของยอดที่เราต้องโอน — ส่วนที่มีค่าที่สุดตอนออฟไลน์
    for d, cr, a in my_rows:
        if d == me and prof.get(cr):
            png = promptpay_qr_png(prof[cr], a, box=6)
            if png:
                y += 8
                dr.text((28, y), f"สแกนโอนให้ {cr}  ({a:,.2f} บาท)", font=f_sm, fill="#000000")
                qr = Image.open(io.BytesIO(png)).convert("RGB")
                qr.thumbnail((210, 210))
                img.paste(qr, (28, y + 26))
                y += 26 + qr.size[1] + 10
            break

    if packs:
        dr.line([28, y, W - 28, y], fill="#dbeafe", width=2); y += 16
        dr.text((28, y), "ของที่ต้องหิ้ว", font=f_mid, fill="#000000"); y += 34
        for r in packs:
            mark = "[x]" if r['done'] else "[  ]"
            who = f" — {r['assignee']}" if r['assignee'] else " — ยังไม่มีคนรับ"
            line = f"{mark} {r['item']}" + (f" ({r['qty']})" if r['qty'] else "") + who
            dr.text((36, y), line[:74], font=f_sm,
                    fill="#9ca3af" if r['done'] else "#000000")
            y += 28

    img = img.crop((0, 0, W, min(int(y) + 26, 2400)))   # ตัดตามความสูงจริง
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return buf.getvalue()


def empty_state(icon, title, sub, btn_label=None, btn_key=None, goto=None):
    """[FIX v21] หน้าจอว่างที่บอกทางต่อ — ของเดิมใช้ st.info('ยังไม่มีบิล')
    ซึ่งบอกแค่ว่าไม่มี แต่ไม่บอกว่าให้ทำอะไรต่อ กลายเป็นทางตัน
    goto = (ชื่อ key ใน session_state, ค่าที่จะตั้ง) เช่น ("menu","manage")"""
    st.markdown(f'<div class="empty"><div class="empty-ico">{icon}</div>'
                f'<div class="empty-t">{esc(title)}</div>'
                f'<div class="empty-s">{esc(sub)}</div></div>', unsafe_allow_html=True)
    if btn_label and goto:
        bl, bc, br = st.columns([1, 2, 1])
        if bc.button(btn_label, key=btn_key, type="primary", use_container_width=True):
            st.session_state[goto[0]] = goto[1]
            st.rerun()


# ── [FIX v22] หารเงิน 3 แบบ + เกลี่ยเศษสตางค์ ─────────────────
#   ปัญหาเดิม: หารเท่ากันตรง ๆ แล้วปัดทศนิยม ทำให้ยอดรวมไม่ตรง
#   เช่น 100 ฿ หาร 3 คน = คนละ 33.33 รวมกลับได้ 99.99 (หาย 1 สตางค์)
#   หรือ 1000 ฿ หาร 7 คน = คนละ 142.86 รวมกลับได้ 1000.02 (เกิน 2 สตางค์)
#   วิธีแก้: คิดเป็นสตางค์ (จำนวนเต็ม) แล้วโยนเศษที่เหลือให้ทีละคน
#   ใครได้เศษก่อนหมุนตาม seed (id ของบิล) เพื่อไม่ให้ตกที่คนเดิมทุกครั้ง
def split_amounts(amount, names, detail=None, seed=0):
    """คืน dict ชื่อ -> ยอด (ปัด 2 ตำแหน่ง และรวมกันได้เท่ายอดบิลเป๊ะ)"""
    names = [n for n in names if n]
    if not names: return {}
    total = int(round(float(amount) * 100))     # ทำงานเป็นสตางค์ เลี่ยงปัญหา float
    mode, values = "equal", {}
    if detail:
        try:
            d = json.loads(detail) if isinstance(detail, str) else detail
            mode = d.get("mode", "equal"); values = d.get("values", {}) or {}
        except (ValueError, TypeError, AttributeError):
            mode, values = "equal", {}

    if mode == "amount":
        # ระบุยอดเอง — ส่วนที่ยังไม่ถูกระบุเอาไปหารเท่า ๆ กันในคนที่เหลือ
        fixed = {n: int(round(float(values.get(n, 0)) * 100)) for n in names if n in values}
        rest  = [n for n in names if n not in fixed]
        left  = total - sum(fixed.values())
        if rest and left > 0:
            base, rem = divmod(left, len(rest))
            out = dict(fixed)
            for i, n in enumerate(rest):
                out[n] = base + (1 if i < rem else 0)
        else:
            out = dict(fixed)
            for n in rest: out[n] = 0
            # ระบุมาไม่ครบยอด → เกลี่ยส่วนต่างให้คนที่ถูกระบุตามสัดส่วน
            diff = total - sum(out.values())
            if diff and fixed:
                ks = list(fixed.keys())
                for i in range(abs(diff)):
                    out[ks[i % len(ks)]] += 1 if diff > 0 else -1
    elif mode == "share":
        w = {n: max(0.0, float(values.get(n, 1) or 0)) for n in names}
        tw = sum(w.values())
        if tw <= 0: w = {n: 1.0 for n in names}; tw = float(len(names))
        raw = {n: total * w[n] / tw for n in names}
        out = {n: int(raw[n]) for n in names}          # ปัดลงก่อน
        rem = total - sum(out.values())                 # แล้วโยนเศษให้คนที่เศษเยอะสุด
        order = sorted(names, key=lambda n: (-(raw[n] - int(raw[n])), n))
        for i in range(rem): out[order[i % len(order)]] += 1
    else:
        base, rem = divmod(total, len(names))
        order = names[seed % len(names):] + names[:seed % len(names)]
        out = {n: base for n in names}
        for i in range(rem): out[order[i]] += 1

    return {n: out.get(n, 0) / 100.0 for n in names}


def compute_net(trip_id, members):
    """[FIX v21] คำนวณยอดสุทธิรายคน — แยกออกมาเพราะต้องใช้ทั้งที่ยอดสรุปด้านบน
    ของหน้าหลัก และในแท็บสรุปเงิน ถ้าเขียนซ้ำสองที่แล้วแก้ไม่ครบจะเพี้ยนคนละทาง
    คืน (net, exps, paid_rows)"""
    c = db()
    exps = c.execute("SELECT id,description,amount,payer_name,split_members,split_detail "
                     "FROM expenses WHERE trip_id=?", (trip_id,)).fetchall()
    paid = c.execute("SELECT id,debtor,creditor,amount,timestamp,slip_blob FROM settlements "
                     "WHERE trip_id=? ORDER BY id DESC", (trip_id,)).fetchall()
    c.close()
    inv = set(members)
    for r in exps:
        inv.add(r['payer_name']); inv.update(r['split_members'].split(","))
    for pr in paid:
        inv.add(pr['debtor']); inv.add(pr['creditor'])
    net = {m: 0.0 for m in inv}
    for r in exps:
        net[r['payer_name']] += r['amount']
        for m2, v in split_amounts(r['amount'], r['split_members'].split(","),
                                   r['split_detail'], seed=r['id']).items():
            net[m2] -= v
    for pr in paid:
        net[pr['debtor']]   += pr['amount']
        net[pr['creditor']] -= pr['amount']
    return net, exps, paid


def settle_plan(net):
    """[FIX v21] แผนโอนเงิน — จับคู่ยอดเท่ากันพอดีก่อน แล้วค่อย greedy
    (ทดสอบ 4,000 เคสแล้วได้จำนวนครั้งน้อยกว่าการเรียงเฉย ๆ ราว 10%)"""
    dbt = sorted([[m, b] for m, b in net.items() if b < -0.01], key=lambda x: x[1])
    crd = sorted([[m, b] for m, b in net.items() if b > 0.01], key=lambda x: -x[1])
    pairs, i = [], 0
    while i < len(dbt):
        m = next((j for j, cc in enumerate(crd) if abs(cc[1] + dbt[i][1]) < 0.01), None)
        if m is not None:
            pairs.append((dbt[i][0], crd[m][0], abs(dbt[i][1])))
            crd.pop(m); dbt.pop(i)
        else:
            i += 1
    while dbt and crd:
        a = min(abs(dbt[0][1]), crd[0][1])
        pairs.append((dbt[0][0], crd[0][0], a))
        dbt[0][1] += a; crd[0][1] -= a
        if abs(dbt[0][1]) < 0.01: dbt.pop(0)
        if abs(crd[0][1]) < 0.01: crd.pop(0)
    return pairs


# ── [FIX v19] แถบแท็บที่ "จำ" แท็บที่เลือกไว้ได้ ────────────────
#   ปัญหา: st.tabs เก็บแท็บที่เลือกไว้ฝั่งเบราว์เซอร์เท่านั้น ไม่ได้อยู่ใน
#   session_state พอ st_autorefresh สั่ง rerun ทุก 3 วินาที แล้วโครงสร้าง
#   element ด้านบนเปลี่ยน (ป้ายออนไลน์โผล่/หาย, ป๊อปอัพหมดเวลา) Streamlit จะ
#   ถอด-ประกอบ st.tabs ใหม่ → เด้งกลับแท็บแรกเอง ทั้งที่ผู้ใช้ไม่ได้กดอะไร
#   ทางแก้: ทำแท็บเองด้วยปุ่ม + session_state เหมือนแถบเมนูหลักที่ใช้ได้ดีอยู่แล้ว
def tab_bar(state_key, labels, default=0):
    """คืน index ของแท็บที่เลือก — สถานะอยู่ใน session_state จึงรอด rerun"""
    if state_key not in st.session_state:
        st.session_state[state_key] = default
    cur = st.session_state[state_key]
    if cur >= len(labels):
        cur = st.session_state[state_key] = default
    with st.container(key=f"tabbar_{state_key}"):
        cols = st.columns(len(labels))
        for i, (col, lb) in enumerate(zip(cols, labels)):
            if col.button(lb, key=f"{state_key}_t{i}",
                          type="primary" if i == cur else "secondary",
                          use_container_width=True):
                st.session_state[state_key] = i
                st.rerun()
    return st.session_state[state_key]

def heartbeat(u):
    if u:
        t = now_str()   # [FIX v11] เวลาไทย ไม่ใช่เวลาเซิร์ฟเวอร์
        c = db(); c.execute("INSERT INTO online_status (name,last_seen) VALUES (?,?) "
                            "ON CONFLICT(name) DO UPDATE SET last_seen=excluded.last_seen",(u,t))
        c.commit(); c.close()

def online_now():
    c = db(); rows = c.execute("SELECT name FROM online_status WHERE last_seen>=?",
                               (now_minus(15),)).fetchall(); c.close()
    return [r["name"] for r in rows]

# [FIX v23] ตรวจ schema ก่อนแล้วค่อยตัดสินใจว่าจะ init ไหม
#
#   ประวัติของบั๊กนี้:
#   v18 ห่อ init_db ด้วย @st.cache_resource เพื่อแก้ "database is locked"
#   (ของเดิมเรียกทุก rerun = ทุก 3 วิต่อคน และข้างในมี DELETE + CREATE INDEX
#   ที่ต้องล็อกเขียน) — แก้ปัญหานั้นได้จริง แต่สร้างปัญหาใหม่ที่ร้ายกว่า:
#   cache_resource อยู่ยาวตลอดอายุ process พอ deploy โค้ดใหม่ที่เพิ่มคอลัมน์
#   แล้ว Streamlit โหลดสคริปต์ใหม่โดยไม่ได้รีสตาร์ท process แคชยังอยู่
#   → init_db() ไม่ถูกเรียก → ALTER TABLE ตัวใหม่ไม่ทำงาน → คอลัมน์ไม่มีจริง
#   → sqlite3.OperationalError: no such column: split_detail
#
#   วิธีนี้แก้ได้ทั้งสองอย่าง: PRAGMA table_info เป็นการ "อ่าน" ล้วน ไม่ต้องล็อกเขียน
#   จึงเรียกทุก rerun ได้โดยไม่แย่งล็อก และถ้าคอลัมน์ไหนขาดจะ init ให้เองทันที
#   ไม่ต้องพึ่งการจำบัมพ์เลขเวอร์ชันด้วยมือ
SCHEMA_COLS = {
    "all_users":     {"promptpay","bank_name","bank_account","avatar_blob"},
    "trips":         {"trip_date","created_by","place_name","lat","lon"},
    "expenses":      {"split_detail"},
    "settlements":   {"slip_blob"},
    "notifications": {"is_auto","is_read","timestamp"},
    "members":       {"trip_id","name"},
    "online_status": {"name","last_seen"},
    "packing":       {"trip_id","item","assignee","done","expense_id"},
}

def schema_ready():
    """True เมื่อทุกตารางและคอลัมน์ที่โค้ดต้องใช้มีครบแล้ว"""
    try:
        c = db()
        try:
            for tbl, need in SCHEMA_COLS.items():
                cols = {r[1] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()}
                if not cols or not need <= cols:
                    return False
            return True
        finally:
            c.close()
    except sqlite3.Error:
        return False

if not schema_ready():
    init_db()
    if not schema_ready():
        st.error("⚠️ ฐานข้อมูลไม่สมบูรณ์ — กรุณากู้คืนจากไฟล์สำรอง "
                 "หรือแจ้งผู้ดูแลระบบ")
        st.stop()

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
cur_trip = cur_date = cur_owner = None
if trip_id and not trips_df.empty:
    row_t = trips_df[trips_df["id"]==trip_id]
    if not row_t.empty:
        cur_trip = row_t.iloc[0]["name"]; cur_date = row_t.iloc[0]["trip_date"]
        cur_owner = row_t.iloc[0].get("created_by")   # [FIX v24] ผู้สร้าง Event
        if cur_owner is not None and pd.isna(cur_owner): cur_owner = None

members = []
if trip_id:
    c = db(); members = [r["name"] for r in c.execute("SELECT name FROM members WHERE trip_id=?",(trip_id,)).fetchall()]; c.close()

notif_count = 0
if me and trip_id:
    c = db(); r = c.execute("SELECT COUNT(*) as n FROM notifications WHERE trip_id=? AND to_user=? AND is_read=0",(trip_id,me)).fetchone(); notif_count = r["n"] if r else 0; c.close()

# ─────────────────────────────────────────────────────────────
# FIXED HEADER (navbar + menubar)
# ─────────────────────────────────────────────────────────────
# [FIX v24] ยังไม่ล็อกอิน = ไม่เผยแม้แต่ชื่อทริปบนแถบบน
trip_lbl   = (cur_trip or "เลือก Event") if me else "ยังไม่เข้าสู่ระบบ"
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
    '<div class="hdr-fill"></div>'          # [FIX v25] แผ่นทึบกันเนื้อหาโผล่ที่ขอบบน
    '<div class="navbar-wrap"><div class="navbar">'
    '<span class="nb-icon">✈️</span>'
    '<span class="nb-title">Trip Splitter</span>'
    f'<span class="nb-trip">✈️ {esc(trip_lbl)}</span>'
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
    _av_vars = f'--nb-av:"";--nb-img:url({avatar_thumb_uri(_my_av, 128)});'
else:
    _av_vars = '--nb-av:"%s";--nb-img:none;' % av_char.replace('"', "").replace("\\", "")
# ล็อกอินแล้ว = เขียว / ยังไม่ล็อกอิน = ส้ม (ให้สะดุดตาว่ายังต้องล็อกอิน)
_col_vars = "--nb-main:#16a34a;--nb-line:#4ade80;" if me else "--nb-main:#f97316;--nb-line:#fdba74;"
st.markdown(f"<style>div.st-key-userbtn{{{_av_vars}{_col_vars}}}</style>",
            unsafe_allow_html=True)

with st.container(key="userbtn"):
    # [FIX v19] วาดเสมอแม้ไม่มีป้าย — ถ้าวาดบ้างไม่วาดบ้าง จำนวน element จะ
    #   เปลี่ยนไปมา ทำให้ Streamlit ถอด-ประกอบ element ที่อยู่ถัดลงไปใหม่
    #   (รวมถึง st.tabs) แท็บที่เลือกไว้เลยถูกรีเซ็ตกลับอันแรก
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

# [FIX v17] วาดป๊อปอัพหลังแถบเมนู เพื่อให้ลอยทับทุกหน้าเหมือนกัน
render_flash()

# [FIX v24] ประตูล็อกอินกลาง — ยังไม่ล็อกอินจะไม่เห็นข้อมูลใด ๆ ทั้งสิ้น
#   ทำที่จุดเดียวก่อนแยกหน้า ปลอดภัยกว่าไปเช็คทีละหน้าแล้วลืมหน้าใดหน้าหนึ่ง
#   (ก่อนหน้านี้หน้า "จัดการ" โชว์รายชื่อ Event และสมาชิกได้ทั้งที่ยังไม่ล็อกอิน)
if not me and menu != "account":
    st.markdown(
        '<div class="card" style="text-align:center;padding:44px 20px;">'
        '<div style="font-size:50px;">🔒</div>'
        '<div style="font-family:var(--font-display);font-weight:600;font-size:19px;'
        'margin:10px 0 6px;">กรุณาเข้าสู่ระบบก่อน</div>'
        '<div style="color:#6b7280;font-size:13px;">ข้อมูลบิล สมาชิก และแชท '
        'จะแสดงเมื่อเข้าสู่ระบบแล้วเท่านั้น</div></div>',
        unsafe_allow_html=True)
    _gl, _gc, _gr = st.columns([1, 2, 1])
    if _gc.button("🔐 ไปหน้าเข้าสู่ระบบ", type="primary", use_container_width=True):
        st.session_state["menu"] = "account"
        st.rerun()
    st.stop()

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

        # [FIX v21] ยอดของฉันเป็นสิ่งแรกที่เห็น — คำถามแรกของทุกคนคือ
        #   "ต้องจ่ายเท่าไหร่" ซึ่งเดิมถูกซ่อนอยู่ในแท็บที่ 3
        _net_all, _exp_all, _paid_all = compute_net(trip_id, members)
        _my = _net_all.get(me, 0.0)
        if _my < -0.01:
            _st_lbl, _st_amt, _st_col, _st_sub = "คุณต้องจ่าย", abs(_my), "#dc2626", "ดูวิธีโอนได้ที่แท็บสรุปเงิน"
        elif _my > 0.01:
            _st_lbl, _st_amt, _st_col, _st_sub = "คุณจะได้คืน", _my, "#16a34a", "รอเพื่อนโอนมา"
        else:
            _st_lbl, _st_amt, _st_col, _st_sub = "เคลียร์หมดแล้ว", 0.0, "#1d4ed8", "ไม่มียอดค้างกับใคร"
        _tot_all = sum(r['amount'] for r in _exp_all)

        st.markdown(
            '<div class="hero">'
            f'<div class="hero-top">{avatar_html(me, avatars.get(me), size=38, font=15)}'
            f'<div class="hero-trip"><div class="hero-name">{esc(cur_trip)}</div>'
            f'<div class="hero-meta">{("📅 "+esc(cur_date)+" · ") if has_date else ""}'
            f'👥 {len(members)} คน · {len(_exp_all)} บิล</div></div></div>'
            f'<div class="hero-lbl">{_st_lbl}</div>'
            f'<div class="hero-amt money" style="color:{_st_col};">{_st_amt:,.2f}<span class="hero-baht">฿</span></div>'
            f'<div class="hero-sub">{_st_sub} · ทริปนี้ใช้ไปแล้ว {_tot_all:,.0f} ฿</div>'
            '</div>', unsafe_allow_html=True)

        # [FIX v19] ใช้ tab_bar แทน st.tabs — แท็บที่เลือกจะไม่เด้งกลับเองอีก
        _ht = tab_bar("tab_home", ["➕ เพิ่มบิล", "📋 ประวัติ", "💰 สรุปเงิน",
                                   "🎒 ของที่ต้องหิ้ว", "⛺ แคมป์"])

        # ── TAB 1 ──────────────────────────────────────────────
        if _ht == 0:
            if not members:
                empty_state("👥", "ทริปนี้ยังไม่มีสมาชิก",
                            "เพิ่มเพื่อนเข้าทริปก่อน แล้วค่อยเริ่มบันทึกบิล",
                            "👥 ไปเพิ่มสมาชิก", "go_add_mem", ("menu", "manage"))
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

                    # [FIX v22] หารไม่เท่ากัน — ของเดิมหารเท่ากันเสมอ ซึ่งไม่ตรงกับ
                    #   การใช้จริง (คนไม่กินเหล้า ห้องพักคนละแบบ ใครสั่งเพิ่มจ่ายเพิ่ม)
                    _mode = st.radio("วิธีหาร:", ["หารเท่ากัน","ระบุยอดเอง","ตามสัดส่วน"],
                                     horizontal=True, key="new_split_mode")
                    _vals = {}
                    if _mode != "หารเท่ากัน":
                        _hint = ("ใส่ยอดของใครที่รู้แน่ ๆ ที่เหลือระบบหารเท่ากันให้"
                                 if _mode=="ระบุยอดเอง" else
                                 "ใส่จำนวนส่วน เช่น 2 = จ่ายเป็นสองเท่าของคนที่ใส่ 1 · ใส่ 0 = ไม่ร่วมจ่าย")
                        st.caption(_hint)
                        _vc = st.columns(min(len(members), 4))
                        for i, m in enumerate(members):
                            with _vc[i % len(_vc)]:
                                _vals[m] = st.number_input(
                                    m, min_value=0.0,
                                    value=(0.0 if _mode=="ระบุยอดเอง" else 1.0),
                                    step=(10.0 if _mode=="ระบุยอดเอง" else 1.0),
                                    key=f"sv_{m}")

                    if st.form_submit_button("💾 บันทึกบิล", type="primary", use_container_width=True):
                        if fup and fup.size > MAX_UPLOAD_MB*1024*1024:
                            st.error(f"⚠️ ไฟล์สลิปใหญ่เกิน {MAX_UPLOAD_MB} MB")
                        elif desc and amt>0 and split_to:
                            if _mode == "ระบุยอดเอง":
                                _det = json.dumps({"mode":"amount",
                                    "values":{m:v for m,v in _vals.items() if m in split_to and v>0}})
                            elif _mode == "ตามสัดส่วน":
                                _det = json.dumps({"mode":"share",
                                    "values":{m:v for m,v in _vals.items() if m in split_to}})
                            else:
                                _det = None
                            blob = compress_image(fup)
                            c = db()
                            cur_ = c.execute("INSERT INTO expenses (trip_id,description,amount,payer_name,split_members,image_blob,split_detail) VALUES (?,?,?,?,?,?,?)",
                                      (trip_id,desc,amt,payer,",".join(split_to),blob,_det))
                            c.commit()
                            _shares = split_amounts(amt, split_to, _det, seed=cur_.lastrowid or 0)
                            for m2 in split_to:
                                if m2!=payer:
                                    msg=f"📌 บิลใหม่: '{desc}'\n💰 {amt:,.2f} บาท | จ่ายโดย: {payer}\n💸 ส่วนคุณ: {_shares.get(m2,0):,.2f} บาท"
                                    c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,'ระบบสรุปยอด',?,1,0,?)",(trip_id,m2,msg,now_str()))
                            c.commit(); c.close()
                            flash(f"บันทึก '{desc}' แล้ว!", "ok"); st.rerun()
                        else: st.error("⚠️ กรอกข้อมูลให้ครบ")

        # ── TAB 2 ──────────────────────────────────────────────
        if _ht == 1:
            # [FIX v11] เดิม SELECT * ดึง image_blob ของ "ทุกบิล" มาทุก 3 วินาที
            #   ทริปละ 30 บิล = โหลดรูปหลายเมกะซ้ำ ๆ ฟรี ๆ
            #   ตอนนี้ดึงแค่ flag ว่ามีรูปไหม แล้วค่อยโหลด blob ตอนกางบิลจริง
            # [FIX v21] ดึง thumbnail เล็ก ๆ มาด้วย (ไม่ใช่รูปเต็ม) เพื่อโชว์ในรายการ
            #   สลิปคือหลักฐานจริงของโดเมนนี้ เดิมต้องกดเปิด expander ทีละใบถึงจะเห็น
            c = db(); exps = c.execute(
                "SELECT id,description,amount,payer_name,split_members,split_detail,image_blob,"
                "       (image_blob IS NOT NULL) AS has_img "
                "FROM expenses WHERE trip_id=? ORDER BY id DESC",(trip_id,)).fetchall(); c.close()
            if not exps:
                empty_state("🧾", "ยังไม่มีบิลในทริปนี้",
                            "บิลที่บันทึกไว้จะมาอยู่ตรงนี้ พร้อมรูปสลิปและรายชื่อคนหาร",
                            "➕ ไปเพิ่มบิล", "go_hist_add", ("tab_home", 0))
            else:
                for row in exps:
                    sl = row['split_members'].split(",")
                    # [FIX v22] ใช้ split_amounts เพื่อให้ตรงกับที่คำนวณจริง
                    _sh_map = split_amounts(row['amount'], sl, row['split_detail'], seed=row['id'])
                    _uneq = len(set(round(v,2) for v in _sh_map.values())) > 1
                    _mine = _sh_map.get(me)
                    # แถบสรุปพร้อม thumbnail สลิป — สแกนได้เร็วโดยไม่ต้องกางทีละใบ
                    _th = avatar_thumb_uri(row['image_blob'], 96) if row['has_img'] else None
                    _slip = (f'<div class="bill-slip" style="background-image:url({_th});"></div>'
                             if _th else '<div class="bill-slip bill-noslip">ไม่มี<br>สลิป</div>')
                    st.markdown(
                        '<div class="bill-row">' + _slip +
                        '<div class="bill-mid">'
                        f'<div class="bill-desc">{esc(row["description"])}</div>'
                        f'<div class="bill-meta">จ่ายโดย {esc(row["payer_name"])} · หาร {len(sl)} คน · '
                        + (f'ส่วนคุณ {_mine:,.2f} ฿' if _mine is not None
                           else ("หารไม่เท่ากัน" if _uneq else f"คนละ {row['amount']/len(sl):,.2f} ฿"))
                        + '</div></div>'
                        f'<div class="bill-amt money">{row["amount"]:,.2f} ฿</div>'
                        '</div>', unsafe_allow_html=True)
                    with st.expander("แก้ไขบิลนี้"):
                        a,b2 = st.columns([1,1.5])
                        with a:
                            if row['has_img']:
                                st.image(row['image_blob'], use_container_width=True)
                            else: st.markdown('<div style="background:#dbeafe;border-radius:8px;height:90px;display:flex;align-items:center;justify-content:center;color:#374151;font-size:13px;">ไม่มีสลิป</div>',unsafe_allow_html=True)
                            st.markdown("**ส่วนของแต่ละคน**")
                            for _n, _v in _sh_map.items():
                                st.markdown(f"- {esc(_n)} — **{_v:,.2f} ฿**")
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
                                    c.commit(); c.close(); flash("อัปเดต!", "ok"); st.rerun()
                            if st.button("🗑️ ลบบิล", key=f"db_{row['id']}", type="secondary"):
                                c=db(); c.execute("DELETE FROM expenses WHERE id=?",(row['id'],)); c.commit(); c.close()
                                flash("ลบแล้ว", "warn"); st.rerun()

        # ── TAB 3 ──────────────────────────────────────────────
        if _ht == 2:
            c = db()
            uprof = {r['name']:{"pp":r['promptpay'],"bn":r['bank_name'],"ba":r['bank_account']} for r in c.execute("SELECT name,promptpay,bank_name,bank_account FROM all_users").fetchall()}
            c.close()
            # [FIX v21] ใช้ compute_net ตัวเดียวกับยอดด้านบน จะได้ไม่มีทางเพี้ยนคนละทาง
            net, exps2, paid_rows = compute_net(trip_id, members)
            if not exps2:
                empty_state("💸", "ยังไม่มีบิลในทริปนี้",
                            "เพิ่มบิลแรกแล้วระบบจะคำนวณให้เองว่าใครต้องโอนให้ใคร",
                            "➕ ไปหน้าเพิ่มบิล", "go_sum_add", ("tab_home", 0))
            else:
                st.markdown("#### 📊 ยอดสรุปรายคน")
                nc2 = min(len(net),4); cols2 = st.columns(nc2)
                for i,(m2,b) in enumerate(sorted(net.items(), key=lambda x:-x[1])):
                    clr = "#16a34a" if b>0.01 else ("#dc2626" if b<-0.01 else "#6b7280")
                    lbl = "รับคืน" if b>0.01 else ("ต้องจ่าย" if b<-0.01 else "เท่ากัน")
                    ring = "border:2px solid #1d4ed8;" if m2==me else "border:1.5px solid #bfdbfe;"
                    with cols2[i%nc2]:
                        st.markdown(
                            f'<div style="background:#fff;border-radius:12px;padding:13px 10px;{ring}'
                            f'border-top:4px solid {clr};text-align:center;margin-bottom:10px;">'
                            '<div style="display:flex;justify-content:center;margin-bottom:7px;">'
                            + avatar_html(m2, avatars.get(m2), size=34, font=13) + '</div>'
                            f'<div style="font-weight:600;font-size:13px;color:#000;overflow:hidden;'
                            f'text-overflow:ellipsis;white-space:nowrap;">{esc(m2)}{" (คุณ)" if m2==me else ""}</div>'
                            f'<div style="font-size:11px;color:#6b7280;">{lbl}</div>'
                            f'<div class="money" style="font-weight:700;font-size:17px;color:{clr};">{abs(b):,.2f} ฿</div>'
                            '</div>', unsafe_allow_html=True)

                st.markdown("#### 🚀 แผนโอนเงิน")
                pairs = settle_plan(net)   # [FIX v21] ย้ายไปเป็นฟังก์ชันร่วม
                if not pairs:
                    st.markdown(
                        '<div class="flow-clear">🎉<div class="flow-clear-t">เคลียร์ครบทุกคนแล้ว</div>'
                        '<div class="flow-clear-s">ไม่มีใครต้องโอนให้ใครอีก</div></div>',
                        unsafe_allow_html=True)

                final_tx=[]
                for dn, cn, at in pairs:
                    p=uprof.get(cn,{}); pp=(p.get("pp") or "").strip(); bn=(p.get("bn") or "").strip(); ba=(p.get("ba") or "").strip()
                    is_me2 = me in (dn, cn)
                    # [FIX v21] เส้นโยงระหว่างคนสองคน — ฉากที่ทุกคนรอดู
                    #   avatar สองข้าง เส้นประตรงกลาง ยอดเงินลอยอยู่บนเส้น
                    st.markdown(
                        f'<div class="flow{" flow-me" if is_me2 else ""}">'
                        '<div class="flow-side">'
                        + avatar_html(dn, avatars.get(dn), size=44, font=17)
                        + f'<div class="flow-nm">{esc(dn)}{"<br><b>(คุณ)</b>" if dn==me else ""}</div></div>'
                        f'<div class="flow-mid"><div class="flow-amt money">{at:,.2f} ฿</div>'
                        '<div class="flow-line"><span class="flow-dot"></span></div>'
                        '<div class="flow-cap">โอนให้</div></div>'
                        '<div class="flow-side">'
                        + avatar_html(cn, avatars.get(cn), size=44, font=17)
                        + f'<div class="flow-nm">{esc(cn)}{"<br><b>(คุณ)</b>" if cn==me else ""}</div></div>'
                        '</div>', unsafe_allow_html=True)
                    # [FIX v22] QR พร้อมเพย์ที่ฝังยอดไว้แล้ว — สแกนแล้วยอดเด้งมาเอง
                    #   ไม่ต้อง copy เบอร์ไปพิมพ์ยอดเองในแอปธนาคาร (พิมพ์ผิดง่าย)
                    _qr = promptpay_qr_uri(pp, at) if pp else None
                    _qc = st.columns([1, 1.25]) if _qr else [st.container()]
                    if _qr:
                        with _qc[0]:
                            st.markdown(
                                f'<div class="qr-box"><img src="{_qr}" alt="QR พร้อมเพย์">'
                                f'<div class="qr-cap">สแกนจ่าย {esc(cn)}<br>'
                                f'<b>{at:,.2f} ฿</b> (ยอดใส่มาให้แล้ว)</div></div>',
                                unsafe_allow_html=True)
                    with (_qc[1] if _qr else _qc[0]):
                        if pp:
                            st.markdown(f"📱 **พร้อมเพย์ {esc(cn)}**"); st.code(pp)
                        if ba:
                            st.markdown(f"🏦 **{esc(bn or 'บัญชี')} {esc(cn)}**"); st.code(ba)
                        if not (pp or ba):
                            st.warning(f"{cn} ยังไม่ได้บันทึกบัญชี — บอกให้ไปกรอกที่เมนูโปรไฟล์")
                        # [FIX v24] โหลดรูป QR เก็บไว้ แล้วใช้ "สแกนจากคลังภาพ" ในแอปธนาคาร
                        #   หมายเหตุ: ธนาคารไทยไม่มี URL scheme สาธารณะที่รับ payload
                        #   พร้อมเพย์แล้วเปิดหน้าโอนให้เลย (ของ SCB ต้องเป็นพาร์ตเนอร์
                        #   Open Banking API และใช้กับร้านค้าเท่านั้น) วิธีที่ใช้ได้จริง
                        #   ทุกธนาคารคือบันทึกรูปแล้วสแกนจากคลังภาพ
                        if pp:
                            _png = promptpay_qr_png(pp, at)
                            if _png:
                                st.download_button(
                                    "⬇️ โหลดรูป QR",
                                    data=_png,
                                    file_name=f"promptpay_{cn}_{at:,.2f}.png".replace(",", ""),
                                    mime="image/png",
                                    key=f"qrdl_{dn}_{cn}_{trip_id}",
                                    use_container_width=True)
                                st.caption("บันทึกรูปแล้วเปิดแอปธนาคาร → สแกน QR → "
                                           "เลือกรูปจากคลังภาพ ยอดเงินจะขึ้นมาให้เอง")

                    # [FIX v11] ปิดหนี้ได้จริง — บันทึกลงตาราง settlements
                    #   ให้เฉพาะลูกหนี้หรือเจ้าหนี้ของรายการนั้นกดได้ คนอื่นกดแทนไม่ได้
                    if me in (dn, cn):
                        # [FIX v22] แนบสลิปตอนกดชำระ — ตรงกับพฤติกรรมจริงที่ทุกคน
                        #   ส่งสลิปเข้ากลุ่มอยู่แล้ว และทำให้เคลียร์กันได้สนิทกว่าเชื่อใจล้วน
                        _pk = f"{dn}_{cn}_{trip_id}"
                        _slip = st.file_uploader(f"📎 แนบสลิปการโอน (ถ้ามี)", type=['jpg','jpeg','png'],
                                                 key=f"sl_{_pk}")
                        _b1, _b2 = st.columns([2, 1])
                        if _b1.button(f"✅ ชำระแล้ว ({at:,.2f} ฿)", key=f"pay_{_pk}",
                                      type="primary", use_container_width=True):
                            if _slip and _slip.size > MAX_UPLOAD_MB*1024*1024:
                                st.error(f"⚠️ ไฟล์ใหญ่เกิน {MAX_UPLOAD_MB} MB")
                            else:
                                cp=db()
                                cp.execute("INSERT INTO settlements (trip_id,debtor,creditor,amount,timestamp,slip_blob) VALUES (?,?,?,?,?,?)",
                                           (trip_id,dn,cn,round(at,2),now_str(),compress_image(_slip)))
                                cp.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,'ระบบสรุปยอด',?,1,0,?)",
                                           (trip_id, cn if me==dn else dn,
                                            f"✅ บันทึกการชำระเงิน\n💳 {dn} → {cn}\n💰 {at:,.2f} บาท"
                                            + ("\n📎 แนบสลิปไว้แล้ว" if _slip else ""), now_str()))
                                cp.commit(); cp.close()
                                flash("บันทึกการชำระแล้ว", "ok"); st.rerun()
                        # [FIX v22] ปุ่มทวงเงิน — เจ้าหนี้กดแล้วส่งเข้าแชทให้ลูกหนี้เลย
                        if me == cn:
                            if _b2.button("🔔 ทวง", key=f"nudge_{_pk}", use_container_width=True):
                                _msg = (f"🔔 แจ้งเตือนยอดค้าง\n💳 {dn} → {cn}\n💰 {at:,.2f} บาท")
                                if pp: _msg += f"\n📱 พร้อมเพย์: {pp}"
                                if ba: _msg += f"\n🏦 {bn or 'บัญชี'}: {ba}"
                                _msg += "\n(ดู QR พร้อมยอดได้ที่แท็บสรุปเงิน)"
                                cn2=db()
                                cn2.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,?)",
                                            (trip_id, dn, me, _msg, now_str()))
                                cn2.commit(); cn2.close()
                                flash(f"ส่งข้อความทวงถึง {dn} แล้ว", "ok"); st.rerun()
                    else:
                        st.caption("รายการนี้ไม่เกี่ยวกับคุณ — ให้คู่กรณีเป็นคนกดยืนยัน")
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    final_tx.append((dn,cn,at))

                # ── [FIX v11] ประวัติการชำระ + ยกเลิกได้ ──────────
                if paid_rows:
                    with st.expander(f"🧾 ประวัติการชำระ ({len(paid_rows)} รายการ)"):
                        for pr in paid_rows:
                            h1,h2 = st.columns([4,1])
                            _has_slip = pr['slip_blob'] is not None   # [FIX v22]
                            h1.markdown(f"✅ **{esc(pr['debtor'])} → {esc(pr['creditor'])}** "
                                        f"· {pr['amount']:,.2f} ฿{'  📎' if _has_slip else ''}  \n"
                                        f"<span style='font-size:11px;color:#6b7280;'>{esc(pr['timestamp'])}</span>",
                                        unsafe_allow_html=True)
                            if _has_slip:
                                with st.expander("ดูสลิป"):
                                    st.image(pr['slip_blob'], width=260)
                            if h2.button("ยกเลิก", key=f"unpay_{pr['id']}"):
                                cu=db(); cu.execute("DELETE FROM settlements WHERE id=?",(pr['id'],)); cu.commit(); cu.close()
                                flash("ยกเลิกการชำระแล้ว", "ok"); st.rerun()

                st.markdown("#### 📲 แชร์ LINE")
                lm=f"📊 สรุปบิล: {cur_trip}\n"
                if has_date: lm+=f"📅 {cur_date}\n"
                lm+="========================\n"; tot=0.0
                for i2,r2 in enumerate(exps2,1):
                    sl2=r2['split_members'].split(",")
                    _m2=split_amounts(r2['amount'], sl2, r2['split_detail'], seed=r2['id'])
                    _uq = len(set(round(v,2) for v in _m2.values())) > 1
                    lm+=f"{i2}. {r2['description']} | {r2['amount']:,.2f} ฿ | {r2['payer_name']}\n"
                    if _uq:   # [FIX v22] หารไม่เท่ากันต้องแจกแจงรายคน ไม่งั้นอ่านไม่รู้เรื่อง
                        for _n,_v in _m2.items(): lm+=f"   - {_n} {_v:,.2f} ฿\n"
                    else:
                        lm+=f"   คนละ {list(_m2.values())[0]:,.2f} ฿\n"
                    tot+=r2['amount']
                lm+=f"รวม: {tot:,.2f} ฿\n========================\n"
                for dn2,cn2,am2 in final_tx:
                    lm+=f"💳 {dn2} → {cn2} = {am2:,.2f} ฿\n"
                    p2=uprof.get(cn2,{}); pp2=(p2.get("pp") or "").strip(); ba2=(p2.get("ba") or "").strip(); bn2=(p2.get("bn") or "").strip()
                    if pp2: lm+=f"   📱 {pp2}\n"
                    if ba2: lm+=f"   🏦 {bn2 or 'บัญชี'}: {ba2}\n"
                lm+="========================"
                st.text_area("ข้อความ LINE:", value=lm, height=180, disabled=True)
                st.link_button("🟢 เปิด LINE", f"https://line.me/R/msg/text/?{urllib.parse.quote(lm)}", type="primary", use_container_width=True)

        # ── TAB 4: ของที่ต้องหิ้ว ──────────────────────────────
        if _ht == 3:
            c = db()
            packs = c.execute("SELECT * FROM packing WHERE trip_id=? ORDER BY done, id",
                              (trip_id,)).fetchall()
            c.close()

            with st.form("add_pack", clear_on_submit=True):
                pc1, pc2, pc3 = st.columns([3, 1, 2])
                _it  = pc1.text_input("ของที่ต้องเอาไป:", placeholder="เต็นท์, เตาแก๊ส, ถ่าน, น้ำแข็ง")
                _qty = pc2.text_input("จำนวน:", placeholder="2 หลัง")
                _who = pc3.selectbox("ใครรับผิดชอบ:", ["— ยังไม่มีคนรับ —"] + members)
                if st.form_submit_button("➕ เพิ่มเข้ารายการ", type="primary", use_container_width=True):
                    if _it.strip():
                        c = db()
                        c.execute("INSERT INTO packing (trip_id,item,qty,assignee,done,added_by,timestamp) "
                                  "VALUES (?,?,?,?,0,?,?)",
                                  (trip_id, _it.strip(), _qty.strip(),
                                   None if _who.startswith("—") else _who, me, now_str()))
                        c.commit(); c.close()
                        flash(f"เพิ่ม '{_it.strip()}' แล้ว", "ok"); st.rerun()
                    else:
                        st.error("⚠️ กรอกชื่อของก่อน")

            if not packs:
                empty_state("🎒", "ยังไม่มีรายการของ",
                            "ใส่ของที่ต้องเอาไปแล้วแบ่งกันว่าใครหิ้วอะไร "
                            "จะได้ไม่มีใครลืมเต็นท์")
            else:
                _done = sum(1 for r in packs if r['done'])
                _mine = sum(1 for r in packs if r['assignee'] == me and not r['done'])
                _free = sum(1 for r in packs if not r['assignee'])
                st.markdown(
                    f'<div class="pk-bar"><div class="pk-bar-fill" style="width:{_done/len(packs)*100:.0f}%;"></div></div>'
                    f'<div class="pk-stat">เตรียมแล้ว {_done}/{len(packs)} · '
                    f'ของคุณค้างอยู่ {_mine} · ยังไม่มีคนรับ {_free}</div>',
                    unsafe_allow_html=True)

                for r in packs:
                    k = r['id']
                    row = st.columns([0.6, 4, 2.2, 1.2])
                    _new_done = row[0].checkbox("เตรียมแล้ว", value=bool(r['done']),
                                                key=f"pkdone_{k}", label_visibility="collapsed")
                    if _new_done != bool(r['done']):
                        c = db(); c.execute("UPDATE packing SET done=? WHERE id=?", (int(_new_done), k)); c.commit(); c.close()
                        st.rerun()
                    _sty = "opacity:.5;text-decoration:line-through;" if r['done'] else ""
                    _own = (f'<span class="pk-who" style="background:{person_color(r["assignee"])};">'
                            f'{esc(r["assignee"])}</span>' if r['assignee']
                            else '<span class="pk-who pk-none">ยังไม่มีคนรับ</span>')
                    row[1].markdown(
                        f'<div style="{_sty}padding-top:5px;">'
                        f'<b>{esc(r["item"])}</b>'
                        f'{" · " + esc(r["qty"]) if r["qty"] else ""} {_own}</div>',
                        unsafe_allow_html=True)
                    _opts = ["— ยังไม่มีคนรับ —"] + members
                    _cur = r['assignee'] if r['assignee'] in members else "— ยังไม่มีคนรับ —"
                    _pick = row[2].selectbox("ผู้รับผิดชอบ", _opts, index=_opts.index(_cur),
                                             key=f"pkwho_{k}", label_visibility="collapsed")
                    if _pick != _cur:
                        c = db(); c.execute("UPDATE packing SET assignee=? WHERE id=?",
                                            (None if _pick.startswith("—") else _pick, k)); c.commit(); c.close()
                        st.rerun()
                    if row[3].button("ลบ", key=f"pkdel_{k}", use_container_width=True):
                        c = db(); c.execute("DELETE FROM packing WHERE id=?", (k,)); c.commit(); c.close()
                        flash("ลบรายการแล้ว", "warn"); st.rerun()

                # [FIX v28] จุดที่เชื่อมกับระบบบิล — ของที่ซื้อมาแล้วกลายเป็นบิลได้เลย
                st.markdown('<div class="section-head" style="margin-top:14px;">'
                            '💸 ซื้อของแล้ว → ทำเป็นบิลหารกัน</div>', unsafe_allow_html=True)
                _buyable = [r for r in packs if not r['expense_id']]
                if not _buyable:
                    st.caption("ทุกรายการถูกบันทึกเป็นบิลไปแล้ว")
                else:
                    with st.form("pack_to_bill", clear_on_submit=True):
                        _lbl = {f"{r['item']}" + (f" ({r['qty']})" if r['qty'] else ""): r['id']
                                for r in _buyable}
                        _sel = st.selectbox("รายการที่ซื้อมาแล้ว:", list(_lbl.keys()))
                        _b1, _b2 = st.columns(2)
                        _amt = _b1.number_input("จ่ายไปเท่าไหร่ (บาท):", min_value=0.0, step=10.0)
                        _payer = _b2.selectbox("ใครเป็นคนจ่าย:", members,
                                               index=members.index(me) if me in members else 0)
                        if st.form_submit_button("💸 บันทึกเป็นบิลหารกัน", type="primary",
                                                 use_container_width=True):
                            if _amt <= 0:
                                st.error("⚠️ ใส่จำนวนเงินก่อน")
                            elif not members:
                                st.error("⚠️ ยังไม่มีสมาชิกในทริป")
                            else:
                                _pid = _lbl[_sel]
                                c = db()
                                c.execute("INSERT INTO expenses (trip_id,description,amount,payer_name,split_members) "
                                          "VALUES (?,?,?,?,?)",
                                          (trip_id, _sel, _amt, _payer, ",".join(members)))
                                _eid = c.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
                                c.execute("UPDATE packing SET expense_id=?, done=1 WHERE id=?", (_eid, _pid))
                                _sh = split_amounts(_amt, members)
                                for _m2 in members:
                                    if _m2 != _payer:
                                        c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) "
                                                  "VALUES (?,?,'ระบบสรุปยอด',?,1,0,?)",
                                                  (trip_id, _m2,
                                                   f"🎒 ของแคมป์: '{_sel}'\n💰 {_amt:,.2f} บาท | จ่ายโดย: {_payer}\n"
                                                   f"💸 ส่วนคุณ: {_sh.get(_m2,0):,.2f} บาท", now_str()))
                                c.commit(); c.close()
                                flash(f"บันทึก '{_sel}' เป็นบิลแล้ว", "ok"); st.rerun()

        # ── TAB 5: แคมป์ (พิกัด + อากาศ + เตรียมออฟไลน์) ────────
        if _ht == 4:
            c = db()
            _tr = c.execute("SELECT place_name,lat,lon FROM trips WHERE id=?", (trip_id,)).fetchone()
            c.close()
            _pname = _tr["place_name"] if _tr else None
            _lat, _lon = (_tr["lat"], _tr["lon"]) if _tr else (None, None)

            st.markdown('<div class="section-head">⛺ จุดกางเต็นท์ / จุดนัดพบ</div>',
                        unsafe_allow_html=True)
            with st.form("camp_loc"):
                _pn = st.text_input("ชื่อสถานที่:", value=_pname or "",
                                    placeholder="ลานกางเต็นท์ผาหล่มสัก")
                _co = st.text_input("พิกัด หรือลิงก์ Google Maps:",
                                    value=(f"{_lat}, {_lon}" if _lat is not None else ""),
                                    placeholder="18.7883, 98.9853 หรือวางลิงก์แผนที่มาเลย")
                if st.form_submit_button("💾 บันทึกจุดกางเต็นท์", type="primary",
                                         use_container_width=True):
                    _la, _lo = parse_latlon(_co)
                    if _co.strip() and _la is None:
                        st.error("⚠️ อ่านพิกัดไม่ออก — ใส่แบบ 18.7883, 98.9853 "
                                 "หรือวางลิงก์ Google Maps ที่มีพิกัดอยู่")
                    else:
                        c = db()
                        c.execute("UPDATE trips SET place_name=?, lat=?, lon=? WHERE id=?",
                                  (_pn.strip() or None, _la, _lo, trip_id))
                        c.commit(); c.close()
                        flash("บันทึกจุดกางเต็นท์แล้ว", "ok"); st.rerun()

            if _lat is not None:
                _url = f"https://www.google.com/maps/search/?api=1&query={_lat},{_lon}"
                _dir = f"https://www.google.com/maps/dir/?api=1&destination={_lat},{_lon}"
                st.markdown(
                    f'<div class="camp-loc"><div class="camp-pin">📍</div><div>'
                    f'<div class="camp-nm">{esc(_pname or "จุดกางเต็นท์")}</div>'
                    f'<div class="camp-co">{_lat:.5f}, {_lon:.5f}</div></div></div>',
                    unsafe_allow_html=True)

                # [FIX v29] แผนที่ในหน้าเว็บเลย ไม่ต้องกดออกไปข้างนอก
                #   ใช้ st.map ซึ่งเป็นของ Streamlit เอง — ไม่ต้องใช้ API key
                #   ไม่ต้องพึ่ง iframe ที่ปลายทางอาจบล็อก และเลื่อน/ซูมได้จริง
                _mv = st.radio("รูปแบบแผนที่", ["🗺️ แผนที่ในหน้า", "🌏 Google Maps (ฝัง)"],
                               horizontal=True, key="camp_mapmode",
                               label_visibility="collapsed")
                if _mv.startswith("🗺️"):
                    st.map(pd.DataFrame({"lat": [_lat], "lon": [_lon]}),
                           zoom=13, size=60, color="#dc2626")
                else:
                    # Google Maps แบบฝัง: ใช้ได้โดยไม่ต้องมี API key
                    #   แต่ Google อาจบล็อกการฝังในบาง network/เบราว์เซอร์
                    #   ถ้าขึ้นว่าง ให้สลับกลับไปใช้ "แผนที่ในหน้า" ได้ทันที
                    # [FIX v29] ใช้ st.html แทน components.iframe
                    #   ตัวหลังถูกประกาศเลิกใช้ตั้งแต่ 1 มิ.ย. 2026 (เลยกำหนดมาแล้ว)
                    st.html(
                        f'<iframe src="https://maps.google.com/maps?q={_lat},{_lon}'
                        f'&z=15&output=embed" width="100%" height="340" '
                        f'style="border:1.5px solid #bfdbfe;border-radius:12px;" '
                        f'loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>')
                    st.caption("ถ้าช่องแผนที่ว่างเปล่า แปลว่าเบราว์เซอร์บล็อกการฝังของ Google "
                               "— สลับไปใช้ “แผนที่ในหน้า” ได้เลย")

                _mc1, _mc2 = st.columns(2)
                _mc1.link_button("🗺️ เปิดใน Google Maps", _url, use_container_width=True)
                _mc2.link_button("🧭 นำทางไปที่นี่", _dir, use_container_width=True,
                                 type="primary")

                st.markdown('<div class="section-head" style="margin-top:16px;">'
                            '🌤️ อากาศ 7 วันข้างหน้า</div>', unsafe_allow_html=True)
                _ok, _fc = fetch_forecast(_lat, _lon)
                if not _ok:
                    st.warning(f"ดึงพยากรณ์อากาศไม่ได้: {_fc}")
                    st.caption("ลองใหม่อีกครั้ง หรือเช็คว่าเซิร์ฟเวอร์ต่อเน็ตออกได้ไหม")
                else:
                    _d = _fc
                    for _i, _day in enumerate(_d["time"]):
                        _code = _d["weather_code"][_i]
                        _ico, _txt = WMO.get(_code, ("🌡️", "—"))
                        _rain = _d["precipitation_probability_max"][_i]
                        _rain = 0 if _rain is None else _rain
                        _warn = "camp-day-warn" if (_rain >= 60 or _code in (95,96,99,82,65)) else ""
                        try:
                            _dt = datetime.strptime(_day, "%Y-%m-%d")
                            _lbl = ["จ","อ","พ","พฤ","ศ","ส","อา"][_dt.weekday()] + f" {_dt.day}/{_dt.month}"
                        except (ValueError, TypeError):
                            _lbl = _day
                        _sr = str(_d["sunrise"][_i])[11:16]
                        _ss = str(_d["sunset"][_i])[11:16]
                        st.markdown(
                            f'<div class="camp-day {_warn}">'
                            f'<div class="camp-dt">{_lbl}</div>'
                            f'<div class="camp-ico">{_ico}</div>'
                            f'<div class="camp-mid"><div class="camp-txt">{_txt}</div>'
                            f'<div class="camp-sub">💧 โอกาสฝน {_rain:.0f}% · '
                            f'💨 {_d["wind_speed_10m_max"][_i]:.0f} กม./ชม. · '
                            f'🌅 {_sr} · 🌇 {_ss}</div></div>'
                            f'<div class="camp-tmp">{_d["temperature_2m_max"][_i]:.0f}°'
                            f'<span class="camp-tmin">/{_d["temperature_2m_min"][_i]:.0f}°</span></div>'
                            f'</div>', unsafe_allow_html=True)
                    st.caption("ข้อมูลจาก Open-Meteo · แถบสีส้มคือวันที่ฝนน่าจะตกหนัก "
                               "ควรเตรียมผ้าใบกันฝนหรือเลื่อนวัน")
            else:
                empty_state("📍", "ยังไม่ได้ตั้งจุดกางเต็นท์",
                            "ใส่พิกัดหรือวางลิงก์ Google Maps ด้านบน "
                            "แล้วจะได้พยากรณ์อากาศกับเวลาพระอาทิตย์ตกของที่นั่นเลย")

            # ── เตรียมไว้ใช้ตอนไม่มีสัญญาณ ──
            st.markdown('<div class="section-head" style="margin-top:16px;">'
                        '📴 เตรียมไว้ใช้ตอนไม่มีสัญญาณ</div>', unsafe_allow_html=True)
            st.caption("ที่แคมป์ส่วนใหญ่เน็ตไม่มี แอปนี้เป็นเว็บจึงเปิดไม่ได้ — "
                       "โหลดสรุปเก็บไว้ในเครื่องก่อนออกเดินทาง")
            if _thai_font_path() is None:
                st.warning("หาฟอนต์ภาษาไทยไม่ได้เลย (ทั้งในเครื่องและดาวน์โหลด) "
                           "ตัวอักษรในรูปจะเป็นสี่เหลี่ยม — เพิ่มไฟล์ `packages.txt` "
                           "ที่มีบรรทัด `fonts-thai-tlwg` แล้ว reboot app")
            _png = offline_sheet(trip_id, cur_trip, cur_date, members, me)
            st.download_button("⬇️ โหลดสรุปทริปเป็นรูป (ใช้ได้ตอนออฟไลน์)",
                               data=_png, file_name=f"trip_{trip_id}_offline.png",
                               mime="image/png", type="primary", use_container_width=True)

# ═══════════════════════════════════════════════════════
# PAGE: จัดการ (Events + Members รวมกัน)
# ═══════════════════════════════════════════════════════
elif menu == "manage":
    # [FIX v19] ใช้ tab_bar แทน st.tabs ด้วยเหตุผลเดียวกับหน้าหลัก
    _mt = tab_bar("tab_manage", ["🗓️ Events", "👥 สมาชิก", "🗑️ ถังขยะ", "💾 สำรองข้อมูล"])

    # ── TAB: Events ────────────────────────────────────
    if _mt == 0:
        left, right = st.columns([1,1])
        with left:
            st.markdown('<div class="section-head">➕ สร้าง Event ใหม่</div>', unsafe_allow_html=True)
            with st.form("create_ev"):
                ne = st.text_input("ชื่อ Event:", placeholder="เช่น ทริปเชียงใหม่")
                nd = st.date_input("วันที่:", value=datetime.today())
                if st.form_submit_button("✅ สร้าง", type="primary", use_container_width=True):
                    ok_n, err_n = valid_name(ne)
                    if ok_n:
                        try:
                            c=db(); c.execute("INSERT INTO trips (name,status,trip_date,created_by) VALUES (?,0,?,?)",(ne.strip(),nd.strftime("%Y-%m-%d"),me)); c.commit(); c.close()
                            flash(f"สร้าง '{ne.strip()}' แล้ว!", "ok"); st.rerun()
                        except sqlite3.IntegrityError: st.error("❌ ชื่อซ้ำ")
                    else: st.error(f"⚠️ {err_n}")

            if trip_id and cur_trip:
                st.markdown(f'<div class="section-head">✏️ แก้ไข: {cur_trip}</div>', unsafe_allow_html=True)
                with st.form("edit_ev"):
                    rn = st.text_input("ชื่อใหม่:", value=cur_trip)
                    try: dd = datetime.strptime(str(cur_date),"%Y-%m-%d") if cur_date and str(cur_date).strip() else datetime.today()
                    except (ValueError, TypeError): dd = datetime.today()
                    rd = st.date_input("วันที่:", value=dd)
                    if st.form_submit_button("💾 บันทึก", type="primary"):
                        ok_r, err_r = valid_name(rn)
                        if ok_r:
                            try:
                                c=db(); c.execute("UPDATE trips SET name=?,trip_date=? WHERE id=?",(rn.strip(),rd.strftime("%Y-%m-%d"),trip_id)); c.commit(); c.close()
                                flash("แก้ไขแล้ว!", "ok"); st.rerun()
                            except sqlite3.IntegrityError: st.error("❌ ชื่อซ้ำ")
                        else: st.error(f"⚠️ {err_r}")
                # [FIX v26] ลบ Event ได้เฉพาะผู้สร้างเท่านั้น — บังคับเข้มขึ้น
                #   ของเดิมยกเว้นให้ Event เก่าที่ created_by ว่าง (ใครก็ลบได้)
                #   แต่ในเครื่องจริง Event ทั้งหมดที่มีอยู่ก่อนคือค่าว่าง
                #   กฎเลยไม่มีผลอะไรเลย ตอนนี้ Event ไร้เจ้าของจะลบไม่ได้
                #   จนกว่าจะมีคนกดรับเป็นเจ้าของก่อน (บันทึกไว้ว่าใครรับ)
                if cur_owner == me:
                    if st.button("🗑️ ลบ Event นี้", type="secondary", use_container_width=True):
                        c=db(); c.execute("UPDATE trips SET status=1 WHERE id=?",(trip_id,)); c.commit(); c.close()
                        st.session_state["trip_id"]=None; flash("ย้ายสู่ถังขยะ", "ok"); st.rerun()
                elif cur_owner:
                    st.button("🗑️ ลบ Event นี้", type="secondary",
                              use_container_width=True, disabled=True)
                    st.caption(f"🔒 ลบได้เฉพาะผู้สร้าง Event นี้ ({esc(cur_owner)}) เท่านั้น")
                else:
                    st.button("🗑️ ลบ Event นี้", type="secondary",
                              use_container_width=True, disabled=True)
                    st.caption("🔒 Event นี้ยังไม่มีเจ้าของ (สร้างก่อนระบบบันทึกผู้สร้าง) — "
                               "ต้องมีคนรับเป็นเจ้าของก่อนถึงจะลบได้")
                    if st.button("🙋 รับเป็นเจ้าของ Event นี้", key="claim_ev",
                                 use_container_width=True):
                        c=db()
                        # เขียนเฉพาะตอนที่ยังว่างจริง กันสองคนกดพร้อมกันแล้วทับกัน
                        c.execute("UPDATE trips SET created_by=? WHERE id=? AND "
                                  "(created_by IS NULL OR created_by='')", (me, trip_id))
                        c.commit(); c.close()
                        flash(f"{me} เป็นเจ้าของ Event นี้แล้ว", "ok"); st.rerun()

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
                empty_state("🗓️", "ยังไม่มี Event",
                            "สร้าง Event แรกจากช่องทางซ้ายมือ เช่น ทริปเชียงใหม่ หรือ ข้าวเย็น")

    # ── TAB: สมาชิก ─────────────────────────────────────
    if _mt == 1:
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
                            + f'<div><div style="font-weight:600;font-size:14px;color:#000;">{dot} {esc(mem)}{you}{bdg}</div>'
                            + f'<div style="font-size:12px;color:#374151;">{"ออนไลน์" if ion else "ออฟไลน์"}</div></div></div>',
                            unsafe_allow_html=True)
                        if mc2.button("ออก", key=f"rm_{mem}"):
                            # [FIX v25] ต้องปิด connection ก่อน st.rerun()
                            #   st.rerun() โยน exception เพื่อหยุดสคริปต์ทันที
                            #   c.close() ที่อยู่ท้ายลูปจึงไม่เคยถูกเรียก
                            #   → connection ค้างพร้อมล็อกเขียน แล้วทุกคนเจอ
                            #   sqlite3.OperationalError: database is locked
                            c.execute("DELETE FROM members WHERE trip_id=? AND name=?",(trip_id,mem))
                            c.commit(); c.close()
                            flash(f"ถอด {mem}", "ok"); st.rerun()
                    c.close()
                else:
                    empty_state("👥", "ยังไม่มีใครใน Event นี้",
                                "เลือกเพื่อนจากช่องทางขวาแล้วกดเพิ่มเข้า Event")

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
                            st.session_state["add_mem_msg"] = ("err", "กรุณาเลือกสมาชิกอย่างน้อย 1 คน")
                            return
                        c = db()
                        for su in sel:   # [FIX v11] OR IGNORE — ตอนนี้มี UNIQUE(trip_id,name) แล้ว
                            c.execute("INSERT OR IGNORE INTO members (trip_id, name) VALUES (?, ?)", (trip_id, su))
                        c.commit(); c.close()
                        st.session_state["chk_select_all_mems"] = False
                        st.session_state["ms_add_mems"] = []
                        st.session_state["add_mem_msg"] = ("ok", f"เพิ่ม {len(sel)} คนเข้า Event เรียบร้อย!")

                    st.button("➕ เพิ่มเข้า Event", type="primary",
                              use_container_width=True, on_click=add_selected_members)

                    # callback สั่ง rerun ให้เองอยู่แล้ว จึงมาอ่านผลลัพธ์ตรงนี้
                    _res = st.session_state.pop("add_mem_msg", None)
                    if _res:
                        flash(_res[1], "ok" if _res[0] == "ok" else "err")
                else:
                    st.info("ทุกคนอยู่ในกลุ่มแล้ว")

                st.markdown('<div class="section-head" style="margin-top:16px;">🌐 ออนไลน์ตอนนี้</div>', unsafe_allow_html=True)
                for u2 in online_users:
                    you2 = " (คุณ)" if u2 == me else ""
                    st.markdown(f"🟢 **{u2}**{you2}")
                if not online_users:
                    st.caption("ไม่มีใครออนไลน์")

    # ── TAB: ถังขยะ ──────────────────────────────────────
    if _mt == 2:
        c=db(); dels=c.execute("SELECT * FROM trips WHERE status=1").fetchall(); c.close()
        if not dels:
            empty_state("🗑️", "ถังขยะว่างเปล่า",
                        "Event ที่ลบจะพักไว้ที่นี่ก่อน กู้คืนได้ตลอด")
        else:
            for dt in dels:
                hd=dt['trip_date'] and str(dt['trip_date']).strip()
                dn2=f"{dt['name']} ({dt['trip_date']})" if hd else dt['name']
                # [FIX v24] ลบถาวรก็ต้องเป็นผู้สร้างเท่านั้น (กู้คืนใครก็ทำได้)
                try: _own = dt['created_by']
                except (KeyError, IndexError): _own = None
                _mine = (_own == me)   # [FIX v26] ไร้เจ้าของ = ลบถาวรไม่ได้
                dc1,dc2,dc3=st.columns([3,1,1])
                dc1.markdown(f"✈️ **{esc(dn2)}**" +
                             (f"  \n<span style='font-size:11px;color:#6b7280;'>สร้างโดย {esc(_own)}</span>"
                              if _own else
                              "  \n<span style='font-size:11px;color:#6b7280;'>ไม่มีเจ้าของ — "
                              "กู้คืนแล้วไปกดรับเป็นเจ้าของก่อนจึงจะลบถาวรได้</span>"),
                             unsafe_allow_html=True)
                if dc2.button("กู้คืน",key=f"rs_{dt['id']}",type="primary"):
                    c=db(); c.execute("UPDATE trips SET status=0 WHERE id=?",(dt['id'],)); c.commit(); c.close()
                    flash("กู้คืนแล้ว!", "ok"); st.rerun()
                if dc3.button("ลบถาวร",key=f"pd_{dt['id']}",type="secondary",disabled=not _mine):
                    c=db()
                    for tb in ["settlements","expenses","members","notifications"]: c.execute(f"DELETE FROM {tb} WHERE trip_id=?",(dt['id'],))
                    c.execute("DELETE FROM trips WHERE id=?",(dt['id'],)); c.commit(); c.close()
                    flash("ลบถาวร!", "ok"); st.rerun()

    # ── [FIX v11] TAB: สำรองข้อมูล ───────────────────────
    if _mt == 3:
        # [FIX v24] ไม่ถาม PIN ซ้ำที่นี่แล้ว — ผ่านประตูล็อกอินกลางมาตั้งแต่ต้นหน้า
        #   (PIN ใช้เฉพาะตอนล็อกอินตามที่ผู้ใช้ขอ)
        st.warning(
            "⚠️ **ข้อมูลไม่ถาวร** — Streamlit Community Cloud ล้างไฟล์ในเครื่องทุกครั้ง "
            "ที่ app reboot หรือ deploy โค้ดใหม่ บิล/แชท/ยอดหนี้จะหายทั้งหมด "
            "แนะนำให้ดาวน์โหลดไฟล์สำรองไว้หลังใช้งานทุกครั้ง")

        bl, br = st.columns(2)
        with bl:
            st.markdown('<div class="section-head">⬇️ ดาวน์โหลดข้อมูล</div>', unsafe_allow_html=True)
            c=db()
            _cnt = {t: c.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in BACKUP_TABLES}
            c.close()
            st.caption(" · ".join(f"{k}: {v}" for k, v in _cnt.items()))
            st.download_button(
                "💾 ดาวน์โหลดไฟล์สำรอง (.json)",
                data=export_backup(),
                file_name=f"trip_backup_{datetime.now(TZ).strftime('%Y%m%d_%H%M')}.json",
                mime="application/json", type="primary", use_container_width=True)

        with br:
            st.markdown('<div class="section-head">⬆️ กู้คืนข้อมูล</div>', unsafe_allow_html=True)
            up = st.file_uploader("เลือกไฟล์สำรอง (.json)", type=["json"], key="restore_file")
            mode = st.radio("วิธีกู้คืน:",
                            ["ล้างของเดิมแล้วเขียนทับ", "รวมกับของเดิม"],
                            key="restore_mode")
            confirm = st.checkbox("ฉันเข้าใจว่าการกู้คืนจะเขียนทับข้อมูลปัจจุบัน", key="restore_ok")
            if st.button("♻️ กู้คืนข้อมูล", type="secondary",
                         use_container_width=True, disabled=not (up and confirm)):
                ok, msg = import_backup(up.getvalue(), wipe=(mode == "ล้างของเดิมแล้วเขียนทับ"))
                if ok:
                    flash(f"{msg}", "ok"); st.rerun()
                else:
                    st.error(f"❌ {msg}")


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
            if not grps:
                st.markdown('<div class="empty" style="padding:22px 14px;">'
                            '<div class="empty-ico">💬</div>'
                            '<div class="empty-t">ยังไม่มีการสนทนา</div>'
                            '<div class="empty-s">เริ่มแชทใหม่ได้จากช่องด้านล่าง</div></div>',
                            unsafe_allow_html=True)
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
                    nm=st.text_input("ข้อความ", placeholder="พิมพ์ข้อความ...", label_visibility="collapsed")
                    b1,b2=st.columns([3,1])
                    if b1.form_submit_button("ส่ง ▶", type="primary", use_container_width=True) and nm.strip():
                        c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,?)",(trip_id,nt,me,nm.strip(),now_str())); c.commit(); c.close()
                        st.session_state["chat_partner"]=nt; st.rerun()
                    if b2.form_submit_button("👍"):
                        c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,?)",(trip_id,nt,me,"👍",now_str())); c.commit(); c.close()
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
                    <div style="font-weight:700;font-size:14px;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{esc(pt)}</div>
                    <div style="font-size:11px;color:{'#bbf7d0' if ion2 else '#bfdbfe'};">{'🟢 ออนไลน์' if ion2 else '⚪ ออฟไลน์'}</div>
                  </div>
                  <div style="font-size:17px;display:flex;gap:10px;">📞 📹</div>
                </div>""", unsafe_allow_html=True)

                bhtml='<div class="fb-chat-body">'
                for n2 in msgs:
                    ts=""
                    if n2['timestamp']:
                        try: ts=datetime.strptime(n2['timestamp'],"%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                        except (ValueError, TypeError): ts=str(n2['timestamp'])[11:16]
                    im2=(n2['from_user']==me and n2['is_auto']==0)
                    is2=(n2['is_auto']==1 or n2['from_user']=="ระบบสรุปยอด")
                    mt=esc(n2['message']).replace('\n','<br>')   # [FIX v11] escape ก่อนแปลงบรรทัด
                    if is2: bhtml+=f'<div><div class="fb-bubble-sys">{mt}</div><div class="fb-bubble-time" style="text-align:center;">{ts}</div></div>'
                    elif im2: bhtml+=f'<div style="display:flex;flex-direction:column;align-items:flex-end;"><div class="fb-bubble-out">{mt}</div><div class="fb-bubble-time r">{ts}</div></div>'
                    else: bhtml+=f'<div style="display:flex;flex-direction:column;align-items:flex-start;"><div class="fb-sender-name">{esc(n2["from_user"])}</div><div class="fb-bubble-in">{mt}</div><div class="fb-bubble-time">{ts}</div></div>'
                bhtml+='</div>'
                st.markdown(bhtml, unsafe_allow_html=True)

                if pt!="🤖 ระบบ":
                    with st.form(key=f"rp_{pt}", clear_on_submit=True):
                        ri,rb,rl=st.columns([6,1,1])
                        rtx=ri.text_input("ข้อความตอบกลับ",placeholder=f"พิมพ์ถึง {esc(pt)}...",label_visibility="collapsed")
                        snt=rb.form_submit_button("▶",type="primary",use_container_width=True)
                        lkd=rl.form_submit_button("👍",use_container_width=True)
                        if snt and rtx.strip():
                            c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,?)",(trip_id,pt,me,rtx.strip(),now_str())); c.commit(); c.close(); st.rerun()
                        if lkd:
                            c=db(); c.execute("INSERT INTO notifications (trip_id,to_user,from_user,message,is_auto,is_read,timestamp) VALUES (?,?,?,?,0,0,?)",(trip_id,pt,me,"👍",now_str())); c.commit(); c.close(); st.rerun()

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
            # [FIX v24] เอา PIN กลับมา — ใช้เฉพาะตอนล็อกอินและตอนสมัครเท่านั้น
            #   ไม่มีการถาม PIN ซ้ำที่หน้าอื่นอีก (สำรองข้อมูลก็ไม่ถาม)
            st.markdown('<div class="section-head">🔐 เข้าสู่ระบบ</div>', unsafe_allow_html=True)
            lm2=st.radio("วิธีเข้าใช้งาน",["เลือกโปรไฟล์","สร้างบัญชีใหม่"],horizontal=True,
                         label_visibility="collapsed")
            if lm2=="เลือกโปรไฟล์":
                if all_users:
                    with st.form("login_form"):
                        us2 = st.selectbox("ชื่อของคุณ:", all_users)
                        pin_in = st.text_input("🔑 PIN:", type="password", max_chars=4,
                                               placeholder="ตัวเลข 4 หลัก")
                        if st.form_submit_button("เข้าสู่ระบบ", type="primary", use_container_width=True):
                            c=db(); _r=c.execute("SELECT pin_hash,pin_salt FROM all_users WHERE name=?",(us2,)).fetchone(); c.close()
                            if _r is None:
                                st.error("❌ ไม่พบบัญชีนี้")
                            elif not _r["pin_hash"]:
                                # บัญชีที่สร้างไว้ตอนยังไม่มีระบบ PIN → ตั้ง PIN ครั้งแรกตรงนี้
                                if not (pin_in.isdigit() and len(pin_in) == 4):
                                    st.error("บัญชีนี้ยังไม่มี PIN — ตั้งใหม่ได้เลย (ตัวเลข 4 หลัก)")
                                else:
                                    _h,_sl = hash_pin(pin_in)
                                    c=db(); c.execute("UPDATE all_users SET pin_hash=?,pin_salt=? WHERE name=?",(_h,_sl,us2)); c.commit(); c.close()
                                    st.session_state["me"]=us2; heartbeat(us2)
                                    flash(f"ตั้ง PIN แล้ว ยินดีต้อนรับ {us2}!", "ok"); st.rerun()
                            elif check_pin(pin_in, _r["pin_hash"], _r["pin_salt"]):
                                st.session_state["me"]=us2; heartbeat(us2)
                                flash(f"ยินดีต้อนรับ, {us2}!", "ok"); st.rerun()
                            else:
                                st.error("❌ PIN ไม่ถูกต้อง")
                    st.caption("บัญชีที่สร้างก่อนมีระบบ PIN จะตั้ง PIN ครั้งแรกตอนล็อกอิน")
                else: st.caption("ยังไม่มีบัญชี")
            else:
                with st.form("signup_form"):
                    nn  = st.text_input("ชื่อเล่น:", placeholder="ชื่อของคุณ", max_chars=NAME_MAXLEN)
                    p1  = st.text_input("🔑 ตั้ง PIN:", type="password", max_chars=4,
                                        placeholder="ตัวเลข 4 หลัก")
                    p2  = st.text_input("🔑 ยืนยัน PIN:", type="password", max_chars=4)
                    if st.form_submit_button("สร้างบัญชี", type="primary", use_container_width=True):
                        ok, err = valid_name(nn)
                        if not ok:
                            st.error(f"⚠️ {err}")
                        elif not (p1.isdigit() and len(p1) == 4):
                            st.error("⚠️ PIN ต้องเป็นตัวเลข 4 หลัก")
                        elif p1 != p2:
                            st.error("⚠️ PIN ทั้งสองช่องไม่ตรงกัน")
                        else:
                            _h,_sl = hash_pin(p1)
                            try:
                                c=db(); c.execute("INSERT INTO all_users (name,pin_hash,pin_salt) VALUES (?,?,?)",(nn.strip(),_h,_sl)); c.commit(); c.close()
                                st.session_state["me"]=nn.strip(); heartbeat(nn.strip())
                                flash(f"ยินดีต้อนรับ {nn.strip()}!", "ok"); st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("❌ มีคนใช้ชื่อนี้แล้ว")
        else:
            # [FIX v16] ถอดฟีเจอร์กดดูรูปใหญ่ออกตามที่ผู้ใช้ขอ — กลับมาเป็น
            #   การ์ดนิ่ง ๆ ที่แสดงรูปโปรไฟล์เฉย ๆ (ไม่ต้องใช้ st.button/session_state
            #   จึงไม่มี rerun เวลากดโดนอีกต่อไป)
            st.markdown(
                '<div class="card" style="display:flex;align-items:center;gap:14px;padding:16px;">'
                + avatar_html(me, avatars.get(me), size=56, font=24)
                + f'<div><div style="font-weight:800;font-size:17px;color:#000;">{esc(me)}</div>'
                  '<div style="font-size:13px;color:#16a34a;font-weight:600;">🟢 ออนไลน์อยู่</div></div>'
                  '</div>',
                unsafe_allow_html=True)

            c=db(); md=c.execute("SELECT * FROM all_users WHERE name=?",(me,)).fetchone(); c.close()
            # [FIX v15] กันหน้าพังเมื่อ session ชี้ไปยังผู้ใช้ที่ไม่มีใน DB แล้ว
            #   เกิดได้จริงเมื่อฐานข้อมูลถูกรีเซ็ต (Streamlit Cloud reboot) หรือ
            #   กู้คืนข้อมูลทับ ขณะที่เบราว์เซอร์ยังถือ session เดิมอยู่
            #   ของเดิม md เป็น None แล้วไปเรียก md['promptpay'] → ทั้งหน้าล่ม
            if md is None:
                st.warning("ไม่พบบัญชีนี้ในระบบแล้ว (ข้อมูลอาจถูกรีเซ็ตหรือกู้คืนทับ) "
                           "กรุณาเข้าสู่ระบบใหม่")
                if st.button("🚪 ออกจากระบบ", type="primary"):
                    st.session_state["me"] = None
                    st.session_state["backup_unlocked"] = False
                    st.rerun()
                st.stop()

            # ── [FIX v6] แก้ชื่อ + รูปโปรไฟล์ ──────────────────
            st.markdown('<div class="section-head">👤 แก้ไขโปรไฟล์</div>', unsafe_allow_html=True)
            with st.form("edit_profile"):
                new_name = st.text_input("ชื่อที่แสดง:", value=me, max_chars=NAME_MAXLEN,
                                         help="เปลี่ยนแล้วบิล แชท และยอดหนี้เดิมจะตามไปด้วยทั้งหมด")
                new_pic  = st.file_uploader("🖼️ รูปโปรไฟล์:", type=['jpg','jpeg','png'])
                del_pic  = st.checkbox("🗑️ ลบรูปโปรไฟล์ (กลับไปใช้ตัวอักษร)",
                                       disabled=not md['avatar_blob'])
                if st.form_submit_button("💾 บันทึกโปรไฟล์", type="primary", use_container_width=True):
                    ok, err = True, ""
                    nn2 = new_name.strip()
                    # [FIX v11] ตรวจชื่อก่อนทำอะไรทั้งสิ้น (กันลูกน้ำ/แท็ก HTML)
                    if nn2 != me:
                        ok, err = valid_name(nn2)
                    if ok and new_pic and new_pic.size > MAX_UPLOAD_MB * 1024 * 1024:
                        ok, err = False, f"ไฟล์ใหญ่เกิน {MAX_UPLOAD_MB} MB"
                    if ok and (del_pic or new_pic):
                        blob = None if del_pic else compress_avatar(new_pic)
                        c=db(); c.execute("UPDATE all_users SET avatar_blob=? WHERE name=?",(blob,me)); c.commit(); c.close()
                    if ok and nn2 and nn2 != me:
                        ok, err = rename_user(me, nn2)
                        if ok:
                            st.session_state["me"] = nn2
                            if st.session_state.get("chat_partner") == me:
                                st.session_state["chat_partner"] = nn2
                    if ok:
                        flash("บันทึกโปรไฟล์แล้ว!", "ok"); st.rerun()
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
                    flash("บันทึกแล้ว!", "ok"); st.rerun()

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
                                  bg=None if ion3 else "#9ca3af")   # [FIX v21] สีประจำตัวเมื่อออนไลน์
                    + f'<div><div style="font-weight:600;font-size:14px;color:#000;">{esc(u5)}{you3}</div>'
                    + f'<div style="font-size:12px;color:#374151;">{dot3} {"ออนไลน์" if ion3 else "ออฟไลน์"}</div></div></div>',
                    unsafe_allow_html=True)
        else: st.caption("ยังไม่มีสมาชิก")
