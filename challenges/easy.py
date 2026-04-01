import re

import requests
import urllib3
from bs4 import BeautifulSoup

from config import EASY_PASSWORD, EASY_URL, EASY_USERNAME
from utils.timer import timed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EASY_API_URL = "https://localhost:3000/api/easy/login"


def _extract_token_from_text(text: str) -> str | None:
    patterns = [
        r'"token"\s*:\s*"([^"]+)"',
        r'"access_token"\s*:\s*"([^"]+)"',
        r"Token:\s*([A-Za-z0-9._\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


@timed
def solve_easy():
    session = requests.Session()
    session.verify = False

    page_resp = session.get(EASY_URL, timeout=20)
    page_resp.raise_for_status()

    soup = BeautifulSoup(page_resp.text, "lxml")

    payload = {
        "username": EASY_USERNAME,
        "password": EASY_PASSWORD,
    }

    form = soup.find("form")
    if form:
        for inp in form.find_all("input"):
            name = inp.get("name")
            value = inp.get("value", "")
            input_type = (inp.get("type") or "").lower()
            if name and input_type == "hidden":
                payload[name] = value

    login_resp = session.post(
        EASY_API_URL,
        json=payload,
        timeout=20,
        allow_redirects=True,
    )

    if login_resp.status_code >= 400:
        login_resp = session.post(
            EASY_API_URL,
            data=payload,
            timeout=20,
            allow_redirects=True,
        )

    token = _extract_token_from_text(login_resp.text)

    if not token:
        try:
            data = login_resp.json()
            token = data.get("token") or data.get("access_token")
        except Exception:
            pass

    elapsed_ms = None
    level = "easy"
    try:
        data = login_resp.json()
        elapsed_ms = data.get("elapsed_ms")
        level = data.get("level") or "easy"
    except Exception:
        pass

    return {
        "level": level,
        "status_code": login_resp.status_code,
        "submit_url": EASY_API_URL,
        "token": token,
        "elapsed_ms_api": elapsed_ms,
        "cookies": session.cookies.get_dict(),
        "response_preview": login_resp.text[:500],
    }