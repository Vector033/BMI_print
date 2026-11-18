import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import re
import os
import webbrowser

PORT = 8000

class AppRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local APIs
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/sheets':
            query = urllib.parse.parse_qs(parsed.query)
            sheet_id = query.get('id', [''])[0].strip()
            if not re.match(r'^[a-zA-Z0-9_-]{10,120}$', sheet_id):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Invalid Google Sheet ID'}).encode('utf-8'))
                return
            try:
                html_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/htmlview'
                req = urllib.request.Request(
                    html_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    html = response.read().decode('utf-8', errors='replace')
                tabs = []
                seen = set()
                for m in re.finditer(r'items\.push\(\{name:\s*"((?:[^"\\]|\\.)*)",\s*pageUrl:[^}]+?gid:\s*"(\d+)"', html):
                    raw_name, gid = m.group(1), m.group(2)
                    try:
                        name = json.loads(f'"{raw_name}"')
                    except Exception:
                        name = raw_name
                    if gid not in seen:
                        seen.add(gid)
                        tabs.append({'name': name, 'gid': gid})
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'sheetId': sheet_id, 'tabs': tabs}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
            return

        if parsed.path == '/api/fetch-sheet':
            query = urllib.parse.parse_qs(parsed.query)
            sheet_url = query.get('url', [''])[0].strip()
            if not sheet_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing url parameter'}).encode('utf-8'))
                return

            # Extract Google Sheet ID and GID if present
            sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
            gid_match = re.search(r'[#&?]gid=([0-9]+)', sheet_url)

            if sheet_id_match:
                sheet_id = sheet_id_match.group(1)
                if gid_match:
                    export_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid_match.group(1)}'
                else:
                    export_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
            else:
                export_url = sheet_url

            try:
                req = urllib.request.Request(
                    export_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    csv_data = response.read().decode('utf-8', errors='replace')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'csv': csv_data,
                    'exportUrl': export_url
                }).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': str(e)
                }).encode('utf-8'))
            return

        # Fallback to serving static files
        super().do_GET()

def run_server():
    global PORT
    for attempt_port in [8000, 8080, 8888, 3000, 5000]:
        try:
            handler = AppRequestHandler
            with socketserver.TCPServer(("", attempt_port), handler) as httpd:
                PORT = attempt_port
                url = f"http://localhost:{PORT}/"
                print(f"=====================================================")
                print(f"  ระบบพิมพ์ใบรายงานสมรรถภาพทางกาย (A5) เริ่มทำงานแล้ว")
                print(f"  เปิดใช้งานที่: {url}")
                print(f"=====================================================")
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                httpd.serve_forever()
                break
        except OSError:
            continue

if __name__ == '__main__':
    run_server()
