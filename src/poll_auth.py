import requests
import time
from datetime import datetime
from display import draw_qr_code

URL = "http://192.168.1.116:8321/get-auth-status"
POLL_INTERVAL = 2  # seconds

def draw_svg_to_html(svg_paths):
    print("Drawing SVG paths:")
    print(svg_paths)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"qr_display_{timestamp}.html"

    # Create a basic SVG container with the path
    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>QR Code Display</title>
    </head>
    <body>
        <h2>QR Code SVG</h2>
        <svg width="300" height="300" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <path d="{svg_paths}" fill="black" />
        </svg>
    </body>
    </html>
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ SVG written to {filename}")

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
                #draw_svg_to_html(svg_paths)
                draw_qr_code(svg_paths)

                last_svg_hash = svg_hash

            print(f"Login detected: {login_detected}")
            if login_detected:
                print("Login detected. Pass tokens to nordnet client")
                break

        except requests.RequestException as e:
            print(f"Request failed: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    poll_auth_status()
