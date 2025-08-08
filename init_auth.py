import hashlib
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.nordnet.no/login-next")
    time.sleep(5)

    logging.info("Started monitoring...")

    elapsed = 0
    while not state["login_detected"] and elapsed < max_wait:
        svg_elements = driver.find_elements(By.TAG_NAME, "svg")
        if len(svg_elements) >= 3:
            qr_svg = svg_elements[2]
            svg_outer = qr_svg.get_attribute("outerHTML")
            current_hash = hashlib.sha256(svg_outer.encode("utf-8")).hexdigest()

            if current_hash != state["last_svg_hash"]:
                path_elements = qr_svg.find_elements(By.TAG_NAME, "path")
                svg_paths = path_elements[1].get_attribute("d") if len(path_elements) >= 2 else None

                print(svg_paths)

                # draw_qr_code(svg_paths)

                state["last_svg_hash"] = current_hash
            else:
                logging.info("QR code unchanged.")
        else:
            logging.warning("Third SVG not found yet.")

        # Check for login cookies
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie["name"] == "NNX_SESSION_ID":
                state["NNX_SESSION_ID"] = cookie["value"]
            elif cookie["name"] == "NEXT":
                state["NEXT"] = cookie["value"]

        # Simulate detection of login by presence of session cookies
        if state["NNX_SESSION_ID"] and state["NEXT"]:
            state["login_detected"] = True
            logging.info("Login detected via cookies.")
            logging.info(f"NNX_SESSION_ID: {state['NNX_SESSION_ID']}")
            logging.info(f"NEXT: {state['NEXT']}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    driver.quit()

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
