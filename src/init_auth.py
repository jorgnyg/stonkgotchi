import hashlib
import logging
from datetime import datetime
#from display import draw_qr_code
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def handle_response(response, context, state):
    if response.request.method == "POST" and "nnx-session/login" in response.url:
        logging.info(f"Login POST detected: {response.url}")
        state["ntag"] = response.headers.get("ntag")

        cookies = context.cookies()
        state["NNX_SESSION_ID"] = next((c["value"] for c in cookies if c["name"] == "NNX_SESSION_ID"), None)
        state["NEXT"] = next((c["value"] for c in cookies if c["name"] == "NEXT"), None)

        logging.info(f"ntag: {state['ntag']}")
        logging.info(f"NNX_SESSION_ID: {state['NNX_SESSION_ID']}")
        logging.info(f"NEXT: {state['NEXT']}")

        state["login_detected"] = True

def save_svg(svg_content):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"qr_code_{timestamp}.html"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>QR Code {timestamp}</title></head><body>{svg_content}</body></html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    logging.info(f"QR code saved to {filename}")

def monitor_auth(poll_interval=5, max_wait=120):
    state = {
        "login_detected": False,
        "last_svg_hash": None,
        "ntag": None,
        "NNX_SESSION_ID": None,
        "NEXT": None
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.on("response", lambda response: handle_response(response, context, state))

        page.goto("https://www.nordnet.no/login-next", wait_until="networkidle")
        page.wait_for_timeout(5000)

        logging.info("Started monitoring...")

        elapsed = 0
        while not state["login_detected"] and elapsed < max_wait:
            svg_elements = page.query_selector_all("svg")
            if len(svg_elements) >= 3:
                qr_svg = svg_elements[2]
                svg_outer = qr_svg.evaluate("node => node.outerHTML")
                current_hash = hashlib.sha256(svg_outer.encode("utf-8")).hexdigest()

                if current_hash != state["last_svg_hash"]:
                    save_svg(svg_outer)
                    # instead extract the d-value of the <path> element and set it to svg_paths
                    path_elements = qr_svg.query_selector_all("path")
                    svg_paths = path_elements[1].get_attribute("d") if len(path_elements) >= 2 else None


                    print(svg_paths)

                    #draw_qr_code(svg_paths)

                    state["last_svg_hash"] = current_hash
                else:
                    logging.info("QR code unchanged.")
            else:
                logging.warning("Third SVG not found yet.")

            page.wait_for_timeout(poll_interval * 1000)
            elapsed += poll_interval

        browser.close()

        if not state["login_detected"]:
            logging.warning("Login was not detected within timeout.")

        return {
            "ntag": state["ntag"],
            "NNX_SESSION_ID": state["NNX_SESSION_ID"],
            "NEXT": state["NEXT"]
        }

# Run the monitor
if __name__ == "__main__":
    result = monitor_auth()
    print("Final Result:")
    print(result)
