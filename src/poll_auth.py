import requests
import time

URL = "http://127.0.0.1:8000/get-auth-status"
POLL_INTERVAL = 5  # seconds

def draw_svg(svg_paths):
    print("🎨 Drawing SVG paths:")
    if isinstance(svg_paths, list):
        for path in svg_paths:
            print(f" - {path}")
    else:
        print(f" - {svg_paths}")

def poll_auth_status():
    last_svg_hash = None

    while True:
        try:
            response = requests.get(URL)
            response.raise_for_status()
            data = response.json()

            login_detected = data.get("login_detected", False)
            svg_paths = data.get("svg_paths")
            svg_hash = data.get("svg_hash")

            if svg_paths and svg_hash != last_svg_hash:
                draw_svg(svg_paths)
                last_svg_hash = svg_hash

            print(f"Login detected: {login_detected}")
            if login_detected:
                print("✅ Login detected. Stopping polling.")
                break

        except requests.RequestException as e:
            print(f"⚠️ Request failed: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    poll_auth_status()
