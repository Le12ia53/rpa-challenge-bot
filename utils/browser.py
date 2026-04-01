import re
from typing import Optional


def extract_token_from_text(text: str) -> Optional[str]:
    """
    Tenta extrair um JWT ou token Bearer do texto fornecido.
    Retorna None se não encontrar.
    """
    # JWT padrão: xxxxx.yyyyy.zzzzz
    jwt_pattern = r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
    match = re.search(jwt_pattern, text)
    if match:
        return match.group(0)

    # Bearer token genérico
    bearer_pattern = r'[Bb]earer\s+([A-Za-z0-9\-._~+/]+=*)'
    match = re.search(bearer_pattern, text)
    if match:
        return match.group(1)

    return None


def safe_fill(page, selector: str, value: str) -> bool:
    """
    Tenta preencher um campo. Retorna True se conseguiu, False caso contrário.
    """
    try:
        locator = page.locator(selector)
        if locator.count() > 0:
            locator.first.fill(value)
            return True
    except Exception:
        pass
    return False


def safe_click(page, selector: str) -> bool:
    """
    Tenta clicar num elemento. Retorna True se conseguiu.
    """
    try:
        locator = page.locator(selector)
        if locator.count() > 0:
            locator.first.click()
            return True
    except Exception:
        pass
    return False
