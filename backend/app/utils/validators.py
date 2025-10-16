import re
from typing import List, Tuple


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


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address"""
    if not email:
        return False, "Email is required"
    
    # Basic format check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    # Check length
    if len(email) > 254:  # RFC 5321
        return False, "Email too long"
    
    # Check for common typos
    common_domains = {
        "gmial.com": "gmail.com",
        "gmai.com": "gmail.com",
        "yahooo.com": "yahoo.com",
        "hotmial.com": "hotmail.com",
    }
    
    domain = email.split('@')[1] if '@' in email else ""
    if domain.lower() in common_domains:
        suggested = email.split('@')[0] + '@' + common_domains[domain.lower()]
        return False, f"Did you mean {suggested}?"
    
    # Block disposable/temporary email domains
    disposable_domains = [
        "tempmail.com", "10minutemail.com", "guerrillamail.com",
        "mailinator.com", "throwaway.email", "trashmail.com"
    ]
    
    if domain.lower() in disposable_domains:
        return False, "Temporary email addresses are not allowed"
    
    return True, email.lower()  # Return normalized email


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Truncate if too long
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove other control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text.strip()


def sanitize_html(text: str) -> str:
    """Remove all HTML tags from text"""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Remove HTML entities
    clean = re.sub(r'&[a-zA-Z]+;', '', clean)
    return clean.strip()
