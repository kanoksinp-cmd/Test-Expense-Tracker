"""
รันสคริปต์นี้ "บนเครื่องตัวเอง" ครั้งเดียว เพื่อขอ refresh_token ของ Google Drive
แล้วเอาค่าที่ได้ไปใส่ใน Streamlit Secrets

    pip install requests
    python get_gdrive_token.py client_secret_xxxxx.json

ถ้าไม่ใส่ชื่อไฟล์ สคริปต์จะหาไฟล์ client_secret*.json ในโฟลเดอร์ปัจจุบันให้เอง
หรือจะพิมพ์ client_id / client_secret เองก็ได้

ไฟล์ JSON ต้องเป็นชนิด "Desktop app" (ข้างในขึ้นต้นด้วย {"installed": ...})
ถ้าเป็น {"web": ...} จะใช้กับ flow นี้ไม่ได้ ต้องสร้าง Desktop app ใหม่
(ดูขั้นตอนใน GOOGLE_DRIVE_SETUP.md)
"""
import glob
import http.server
import json
import os
import socketserver
import sys
import threading
import urllib.parse
import webbrowser

import requests

PORT = 8765
REDIRECT = f"http://localhost:{PORT}/"
# drive.file = เข้าถึงได้เฉพาะไฟล์ที่แอปนี้สร้างเอง
# เป็น scope แบบ non-sensitive จึงไม่ต้องผ่าน security audit ของ Google
SCOPE = "https://www.googleapis.com/auth/drive.file"

code_box = {}


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        p = urllib.parse.parse_qs(q)
        code_box.update({k: v[0] for k, v in p.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = "code" in code_box
        msg = "เรียบร้อย! กลับไปที่หน้าต่าง terminal ได้เลย" if ok else "ไม่สำเร็จ ลองใหม่อีกครั้ง"
        self.wfile.write(f"<h2 style='font-family:sans-serif'>{msg}</h2>".encode())


def load_client(path):
    """อ่าน client_id/secret จากไฟล์ JSON ที่โหลดมาจาก Google Cloud Console
    คืน (client_id, client_secret) หรือ (None, ข้อความ error)"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return None, f"อ่านไฟล์ไม่ได้: {e}"

    if "installed" in data:
        blk = data["installed"]
    elif "web" in data:
        return None, ("ไฟล์นี้เป็นชนิด 'web' ใช้กับ flow นี้ไม่ได้\n"
                      "   ต้องไปสร้าง OAuth client ใหม่โดยเลือก Application type = Desktop app")
    else:
        return None, "รูปแบบไฟล์ไม่ถูกต้อง (ไม่เจอทั้ง 'installed' และ 'web')"

    cid, csec = blk.get("client_id"), blk.get("client_secret")
    if not cid or not csec:
        return None, "ในไฟล์ไม่มี client_id หรือ client_secret"
    return (cid, csec), blk.get("project_id", "")


def pick_credentials():
    """เลือกที่มาของ credential: argv -> ไฟล์ในโฟลเดอร์ -> พิมพ์เอง"""
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        found = sorted(glob.glob("client_secret*.json"))
        if len(found) == 1:
            path = found[0]
            print(f"เจอไฟล์: {path}")
        elif len(found) > 1:
            print("เจอไฟล์หลายอัน เลือกหมายเลข:")
            for i, f in enumerate(found, 1):
                print(f"  {i}. {f}")
            try:
                path = found[int(input("เลือก: ").strip()) - 1]
            except (ValueError, IndexError):
                print("!! เลือกไม่ถูกต้อง")
                return None, None

    if path and os.path.exists(path):
        res, extra = load_client(path)
        if res is None:
            print(f"!! {extra}")
            return None, None
        if extra:
            print(f"project: {extra}")
        return res

    print("ไม่เจอไฟล์ JSON — พิมพ์เองก็ได้")
    cid = input("client_id     : ").strip()
    csec = input("client_secret : ").strip()
    return (cid, csec) if cid and csec else (None, None)


def main():
    print("=" * 60)
    print("ขอ refresh token สำหรับ Google Drive")
    print("=" * 60)
    cid, csec = pick_credentials()
    if not cid or not csec:
        print("!! ไม่มี credential ให้ใช้")
        return
    print(f"client_id: {cid[:28]}...\n")

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",   # จำเป็น ถึงจะได้ refresh_token
        "prompt": "consent",        # บังคับขอใหม่ ไม่งั้นรอบสองจะไม่ส่ง refresh_token มา
    })

    srv = socketserver.TCPServer(("", PORT), Handler)
    threading.Thread(target=srv.handle_request, daemon=True).start()

    print(f"\nกำลังเปิด browser... ถ้าไม่เปิดเอง ให้ copy ลิงก์นี้ไปวาง:\n{auth_url}\n")
    print('เจอหน้าจอ "Google hasn\'t verified this app" ให้กด Advanced -> Go to ... (unsafe)')
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("รออนุญาตจาก browser...")
    for _ in range(300):
        if "code" in code_box or "error" in code_box:
            break
        threading.Event().wait(1)
    srv.server_close()

    if "code" not in code_box:
        print("!! ไม่ได้รับ code:", code_box.get("error", "หมดเวลา"))
        return

    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "code": code_box["code"],
        "client_id": cid,
        "client_secret": csec,
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    })
    if r.status_code != 200:
        print("!! แลก token ไม่สำเร็จ:", r.status_code, r.text[:400])
        return

    tok = r.json()
    rt = tok.get("refresh_token")
    if not rt:
        print("!! ไม่ได้ refresh_token กลับมา")
        print("   ลองเข้า https://myaccount.google.com/permissions ถอนสิทธิ์แอปนี้ออกก่อน แล้วรันใหม่")
        print("   response:", json.dumps(tok, indent=2)[:400])
        return

    print("\n" + "=" * 60)
    print("สำเร็จ! copy ข้อความข้างล่างนี้ไปวางใน Streamlit Secrets")
    print("(Streamlit Cloud -> Manage app -> Settings -> Secrets)")
    print("=" * 60)
    print(f'''
[gdrive]
client_id     = "{cid}"
client_secret = "{csec}"
refresh_token = "{rt}"
folder_id     = ""   # ใส่ ID ของโฟลเดอร์ถ้าอยากให้ลงโฟลเดอร์นั้น
''')
    print("=" * 60)
    print("อย่าลืม! ที่ Google Cloud Console -> OAuth consent screen")
    print("ต้องกด PUBLISH APP ให้เป็นสถานะ 'In production'")
    print("ถ้าปล่อยเป็น 'Testing' refresh token จะหมดอายุใน 7 วัน")
    print("=" * 60)


if __name__ == "__main__":
    main()
