import hashlib
import json
import re
import ssl

import requests
import urllib3
import websocket
from playwright.sync_api import sync_playwright

from config import EXTREME_PASSWORD, EXTREME_URL, EXTREME_USERNAME
from utils.timer import timed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EXTREME_INIT_API = "https://localhost:3000/api/extreme/init"


def _safe_text(text: str, limit: int = 800) -> str:
    return text[:limit] if text else ""


def solve_pow(prefix: str, difficulty: int) -> str:
    target = "0" * difficulty
    nonce = 0

    while True:
        candidate = f"{prefix}{nonce}".encode()
        digest = hashlib.sha256(candidate).hexdigest()
        if digest.startswith(target):
            return str(nonce)
        nonce += 1


def _extract_hex_after_label(text: str, label: str) -> str | None:
    pattern = rf"{label}[:\s]+([a-f0-9]{{16,128}})"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _run_ws_flow(ws_url: str):
    result = {
        "pow_prefix": None,
        "pow_difficulty": None,
        "pow_nonce": None,
        "pow_solved": False,
        "proof": None,
        "token": None,
        "messages": [],
        "error": None,
    }

    ws = None
    try:
        ws = websocket.create_connection(
            ws_url,
            sslopt={"cert_reqs": ssl.CERT_NONE},
            timeout=20,
        )

        # 1) Recebe o desafio POW
        msg = ws.recv()
        result["messages"].append(_safe_text(str(msg), 400))

        data = json.loads(msg)

        if data.get("type") != "pow_challenge":
            result["error"] = f"Mensagem inesperada no WS: {data.get('type')}"
            return result

        prefix = data["prefix"]
        difficulty = int(data["difficulty"])

        result["pow_prefix"] = prefix
        result["pow_difficulty"] = difficulty

        # 2) Resolve POW
        nonce = solve_pow(prefix, difficulty)
        result["pow_nonce"] = nonce

        # 3) Envia nonce para o servidor
        ws.send(json.dumps({"nonce": nonce}))
        result["pow_solved"] = True

        # 4) Lê mensagens seguintes até obter proof/token/success
        for _ in range(10):
            msg = ws.recv()
            result["messages"].append(_safe_text(str(msg), 400))

            try:
                data = json.loads(msg)
            except Exception:
                data = {}

            msg_type = data.get("type")

            if data.get("proof"):
                result["proof"] = data["proof"]
            if data.get("token"):
                result["token"] = data["token"]

            if msg_type in {"proof", "final", "success", "result"}:
                if not result["proof"]:
                    result["proof"] = _extract_hex_after_label(str(msg), "proof")
                if not result["token"]:
                    result["token"] = _extract_hex_after_label(str(msg), "token")
                break

        return result

    except Exception as exc:
        result["error"] = str(exc)
        return result

    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


@timed
def solve_extreme():
    captured_requests = []
    captured_responses = []

    final_url = None
    final_text = ""
    final_html = ""
    clicked = False
    success = False

    init_data = {}
    ws_url = None
    ws_result = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        def on_request(request):
            try:
                post_data = request.post_data
            except Exception:
                post_data = None

            captured_requests.append(
                {
                    "method": request.method,
                    "url": request.url,
                    "post_data": _safe_text(post_data or "", 500) or None,
                }
            )

        def on_response(response):
            body_preview = None
            try:
                ct = (response.headers.get("content-type") or "").lower()
                if any(x in ct for x in ["application/json", "text/plain", "text/html"]):
                    body_preview = _safe_text(response.text(), 500)
            except Exception:
                body_preview = None

            captured_responses.append(
                {
                    "status": response.status,
                    "url": response.url,
                    "body_preview": body_preview,
                }
            )

        page.on("request", on_request)
        page.on("response", on_response)

        page.goto(EXTREME_URL, wait_until="networkidle", timeout=30000)

        button_selectors = [
            'button[type="submit"]',
            'button',
            'a.btn',
            'input[type="submit"]',
        ]

        for sel in button_selectors:
            if page.locator(sel).count() > 0:
                try:
                    page.locator(sel).first.click()
                    clicked = True
                    break
                except Exception:
                    pass

        # dá tempo para o front chamar /api/extreme/init
        page.wait_for_timeout(3000)

        for item in captured_responses:
            if item["url"] == EXTREME_INIT_API and item["body_preview"]:
                try:
                    init_data = json.loads(item["body_preview"])
                except Exception:
                    init_data = {}
                break

        session_id = init_data.get("session_id")
        ws_ticket = init_data.get("ws_ticket")

        if session_id and ws_ticket:
            ws_url = (
                f"wss://localhost:3000/ws"
                f"?ticket={ws_ticket}&session_id={session_id}"
            )
            ws_result = _run_ws_flow(ws_url)

        # tempo para o front refletir a conclusão
        page.wait_for_timeout(3000)

        final_url = page.url
        final_html = page.content()
        try:
            final_text = page.locator("body").inner_text()
        except Exception:
            final_text = ""

        low = final_text.lower()
        success = (
            "autenticação completa" in low
            or "challenge resolvido" in low
            or "payload decriptado" in low
            or "step 5" in low
            or "proof" in low
            or "submissão final" in low
            or bool(ws_result.get("proof"))
            or bool(ws_result.get("token"))
        )

        browser.close()

    proof = ws_result.get("proof") or _extract_hex_after_label(final_text, "proof")
    token = ws_result.get("token") or _extract_hex_after_label(final_text, "token")

    return {
        "level": "extreme",
        "clicked_start": clicked,
        "success": success,
        "final_url": final_url,
        "proof": proof,
        "token": token,
        "pow_prefix": ws_result.get("pow_prefix"),
        "pow_difficulty": ws_result.get("pow_difficulty"),
        "pow_nonce": ws_result.get("pow_nonce"),
        "pow_solved": ws_result.get("pow_solved", False),
        "ws_url": ws_url,
        "ws_error": ws_result.get("error"),
        "ws_messages": ws_result.get("messages", [])[:10],
        "requests_seen": captured_requests[:25],
        "responses_seen": captured_responses[:25],
        "final_text_preview": _safe_text(final_text, 1000),
        "final_html_preview": _safe_text(final_html, 1000),
        "credentials_used": {
            "username": EXTREME_USERNAME,
            "password": EXTREME_PASSWORD,
        },
    }