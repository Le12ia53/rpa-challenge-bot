import json
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import urllib3
from playwright.sync_api import sync_playwright

from config import HARD_PASSWORD, HARD_URL, HARD_USERNAME, PFX_PASSWORD, PFX_PATH
from utils.timer import timed
from utils.tls import extract_pfx_to_pem

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HARD_LOGIN_API = "https://localhost:3000/api/hard/login"
HARD_VERIFY_ORIGIN = "https://localhost:3001"


def _extract_token_from_text(text: str) -> str | None:
    patterns = [
        r'"token"\s*:\s*"([^"]+)"',
        r"token=([a-f0-9]{32,128})",
        r"Token:\s*([A-Za-z0-9._\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


@timed
def solve_hard():
    if not Path(PFX_PATH).exists():
        return {
            "level": "hard",
            "error": f"Certificado não encontrado em {PFX_PATH}",
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        cert_pem = str(Path(tmpdir) / "client-cert.pem")
        key_pem = str(Path(tmpdir) / "client-key.pem")
        extract_pfx_to_pem(PFX_PATH, PFX_PASSWORD, cert_pem, key_pem)

        captured_login_payload = None
        captured_verify_url = None
        captured_token = None
        clicked = False

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                ignore_https_errors=True,
                client_certificates=[
                    {
                        "origin": HARD_VERIFY_ORIGIN,
                        "certPath": cert_pem,
                        "keyPath": key_pem,
                    }
                ],
            )

            page = context.new_page()

            def on_request(request):
                nonlocal captured_login_payload
                if request.url == HARD_LOGIN_API and request.method == "POST":
                    try:
                        captured_login_payload = request.post_data
                    except Exception:
                        captured_login_payload = None

            def on_response(response):
                nonlocal captured_verify_url, captured_token
                try:
                    if "/verify?token=" in response.url:
                        captured_verify_url = response.url
                        parsed = urlparse(response.url)
                        token_list = parse_qs(parsed.query).get("token")
                        if token_list:
                            captured_token = token_list[0]
                except Exception:
                    pass

            page.on("request", on_request)
            page.on("response", on_response)

            page.goto(HARD_URL, wait_until="networkidle", timeout=30000)

            user_selectors = [
                'input[name="username"]',
                'input[name="user"]',
                'input[name="login"]',
                'input[type="text"]',
            ]
            pass_selectors = [
                'input[name="password"]',
                'input[name="pass"]',
                'input[name="senha"]',
                'input[type="password"]',
            ]
            button_selectors = [
                'button[type="submit"]',
                'button',
                'input[type="submit"]',
            ]

            for sel in user_selectors:
                if page.locator(sel).count() > 0:
                    page.locator(sel).first.fill(HARD_USERNAME)
                    break

            for sel in pass_selectors:
                if page.locator(sel).count() > 0:
                    page.locator(sel).first.fill(HARD_PASSWORD)
                    break

            for sel in button_selectors:
                if page.locator(sel).count() > 0:
                    page.locator(sel).first.click()
                    clicked = True
                    break

            # deixa o browser completar o fluxo e ir para a porta 3001
            try:
                page.wait_for_url("**localhost:3001/**", timeout=10000)
            except Exception:
                page.wait_for_timeout(5000)

            final_url = page.url
            final_html = page.content()
            final_text = page.locator("body").inner_text()

            browser.close()

        if not clicked:
            return {
                "level": "hard",
                "error": "Botão de autenticação não encontrado.",
            }

        parsed_payload = None
        if captured_login_payload:
            try:
                parsed_payload = json.loads(captured_login_payload)
            except Exception:
                parsed_payload = captured_login_payload

        cert_cn = None
        cn_match = re.search(r"CN:\s*([^\n]+)", final_text, flags=re.IGNORECASE)
        if cn_match:
            cert_cn = cn_match.group(1).strip()

        token = _extract_token_from_text(final_html)
        if not token:
            token = captured_token

        success = (
            "certificado digital aceito" in final_text.lower()
            or "autenticação bem-sucedida" in final_text.lower()
            or "token:" in final_text.lower()
        )

        return {
            "level": "hard",
            "captured_login_payload": parsed_payload,
            "verify_url": captured_verify_url,
            "final_url": final_url,
            "cert_cn": cert_cn,
            "token": token,
            "success": success,
            "final_text_preview": final_text[:800],
            "final_html_preview": final_html[:800],
        }