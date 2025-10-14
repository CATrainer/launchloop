import re
from typing import List


RESERVED_SUBDOMAINS = [
    "www", "api", "app", "admin", "staging", "dev", "test",
    "mail", "smtp", "pop", "imap", "ftp", "ssh",
    "blog", "shop", "store", "support", "help", "docs",
]

BANNED_PHRASES = [
    "revolutionary", "game-changing", "cutting-edge", "transform", "unlock",
    "best", "leading", "top", "#1", "trusted by thousands"
]


def validate_subdomain(subdomain: str) -> bool:
    """Validate subdomain format"""
    if not subdomain or len(subdomain) < 3 or len(subdomain) > 30:
        return False
    
    if subdomain.lower() in RESERVED_SUBDOMAINS:
        return False
    
    # Only alphanumeric and hyphens, no leading/trailing hyphens
    pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
    return bool(re.match(pattern, subdomain.lower()))


def validate_copy_content(text: str) -> tuple[bool, List[str]]:
    """
    Validate copy content for banned phrases and emojis
    Returns (is_valid, list_of_violations)
    """
    violations = []
    
    # Check for emojis
    emoji_pattern = re.compile("[\U0001F600-\U0001F64F]", flags=re.UNICODE)
    if emoji_pattern.search(text):
        violations.append("Contains emojis")
    
    # Check for banned phrases
    text_lower = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in text_lower:
            violations.append(f"Contains banned phrase: '{phrase}'")
    
    return len(violations) == 0, violations


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Truncate if too long
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    return text.strip()
