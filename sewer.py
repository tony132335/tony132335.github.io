#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單的雙端口 HTTP 伺服器：
- 4372 端口：顯示「當前設備公網 IP」
- 80 端口：顯示「Minecraft 伺服器 IP 地址」 + 實時公網 IP
"""

import http.server
import socketserver
import requests
import threading
import time
from datetime import datetime

# 設定
PUBLIC_IP_URLS = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com"
]

# 全局變數儲存最新公網 IP（多線程安全）
current_public_ip = "獲取中..."
last_update_time = ""

def fetch_public_ip():
    """嘗試多個服務獲取公網 IP，取第一個成功的"""
    for url in PUBLIC_IP_URLS:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                ip = r.text.strip()
                if ip and "." in ip:  # 簡單驗證
                    return ip
        except Exception:
            pass
    return "無法獲取公網 IP（檢查網路）"

def update_ip_loop():
    """後台每 30 秒更新一次公網 IP"""
    global current_public_ip, last_update_time
    while True:
        new_ip = fetch_public_ip()
        if new_ip != current_public_ip:
            current_public_ip = new_ip
            last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{last_update_time}] 公網 IP 更新為: {current_public_ip}")
        time.sleep(30)

# 共用的 HTML 模板
def generate_html(title, content):
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #111; color: #0f0; text-align: center; padding: 50px; }}
        h1 {{ font-size: 3em; margin-bottom: 0.2em; }}
        .ip {{ font-size: 4em; font-weight: bold; color: #0f8; background: #000; padding: 20px; border-radius: 15px; display: inline-block; margin: 20px; }}
        .time {{ font-size: 1.2em; color: #888; }}
        .note {{ margin-top: 40px; color: #555; font-size: 1.1em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="ip">{content}</div>
    <div class="time">最後更新：{last_update_time or "正在獲取..."}</div>
    <div class="note">
        提示：如果你的 MC 伺服器在路由器後面，請確保已做端口轉發（25565）<br>
        玩家連線時使用的就是這個公網 IP:端口
    </div>
    <script>
        setTimeout(() => location.reload(), 30000);  // 每 30 秒自動刷新
    </script>
</body>
</html>"""

# 自訂 Handler
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        if self.server.server_port == 4372:
            html = generate_html("當前設備公網 IP", current_public_ip)
        else:  # 80 端口
            html = generate_html("Minecraft 伺服器 IP 地址", current_public_ip)
        
        self.wfile.write(html.encode("utf-8"))

# 啟動伺服器的函數
def run_server(port):
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        print(f"伺服器啟動在 http://0.0.0.0:{port}")
        httpd.serve_forever()

if __name__ == "__main__":
    # 先啟動 IP 更新線程
    ip_thread = threading.Thread(target=update_ip_loop, daemon=True)
    ip_thread.start()

    # 啟動兩個伺服器（用兩個 thread）
    t1 = threading.Thread(target=run_server, args=(4372,), daemon=True)
    t1.start()

    try:
        run_server(80)  # 主線程跑 80 端口（需要 root）
    except PermissionError:
        print("錯誤：80 端口需要 root 權限！")
        print("解決方式：")
        print("  1. 用 sudo python3 這個腳本.py")
        print("  2. 或把 80 改成 >1024 的端口，例如 8080")
        print("  3. 或用 iptables 做端口轉發：sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080")
    except KeyboardInterrupt:
        print("\n伺服器已關閉")#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單的雙端口 HTTP 伺服器：
- 4372 端口：顯示「當前設備公網 IP」
- 80 端口：顯示「Minecraft 伺服器 IP 地址」 + 實時公網 IP
"""

import http.server
import socketserver
import requests
import threading
import time
from datetime import datetime

# 設定
PUBLIC_IP_URLS = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com"
]

# 全局變數儲存最新公網 IP（多線程安全）
current_public_ip = "獲取中..."
last_update_time = ""

def fetch_public_ip():
    """嘗試多個服務獲取公網 IP，取第一個成功的"""
    for url in PUBLIC_IP_URLS:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                ip = r.text.strip()
                if ip and "." in ip:  # 簡單驗證
                    return ip
        except Exception:
            pass
    return "無法獲取公網 IP（檢查網路）"

def update_ip_loop():
    """後台每 30 秒更新一次公網 IP"""
    global current_public_ip, last_update_time
    while True:
        new_ip = fetch_public_ip()
        if new_ip != current_public_ip:
            current_public_ip = new_ip
            last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{last_update_time}] 公網 IP 更新為: {current_public_ip}")
        time.sleep(30)

# 共用的 HTML 模板
def generate_html(title, content):
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #111; color: #0f0; text-align: center; padding: 50px; }}
        h1 {{ font-size: 3em; margin-bottom: 0.2em; }}
        .ip {{ font-size: 4em; font-weight: bold; color: #0f8; background: #000; padding: 20px; border-radius: 15px; display: inline-block; margin: 20px; }}
        .time {{ font-size: 1.2em; color: #888; }}
        .note {{ margin-top: 40px; color: #555; font-size: 1.1em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="ip">{content}</div>
    <div class="time">最後更新：{last_update_time or "正在獲取..."}</div>
    <div class="note">
        提示：如果你的 MC 伺服器在路由器後面，請確保已做端口轉發（25565）<br>
        玩家連線時使用的就是這個公網 IP:端口
    </div>
    <script>
        setTimeout(() => location.reload(), 30000);  // 每 30 秒自動刷新
    </script>
</body>
</html>"""

# 自訂 Handler
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        if self.server.server_port == 4372:
            html = generate_html("當前設備公網 IP", current_public_ip)
        else:  # 80 端口
            html = generate_html("Minecraft 伺服器 IP 地址", current_public_ip)
        
        self.wfile.write(html.encode("utf-8"))

# 啟動伺服器的函數
def run_server(port):
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        print(f"伺服器啟動在 http://0.0.0.0:{port}")
        httpd.serve_forever()

if __name__ == "__main__":
    # 先啟動 IP 更新線程
    ip_thread = threading.Thread(target=update_ip_loop, daemon=True)
    ip_thread.start()

    # 啟動兩個伺服器（用兩個 thread）
    t1 = threading.Thread(target=run_server, args=(4372,), daemon=True)
    t1.start()

    try:
        run_server(80)  # 主線程跑 80 端口（需要 root）
    except PermissionError:
        print("錯誤：80 端口需要 root 權限！")
        print("解決方式：")
        print("  1. 用 sudo python3 這個腳本.py")
        print("  2. 或把 80 改成 >1024 的端口，例如 8080")
        print("  3. 或用 iptables 做端口轉發：sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080")
    except KeyboardInterrupt:
        print("\n伺服器已關閉")
