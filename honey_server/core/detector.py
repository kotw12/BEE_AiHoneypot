import re

# Comprehensive regular expressions for detection
SQLI_PATTERNS = [
    r"(?i)(union\s+all\s+select|union\s+select|select\s+.*\s+from|insert\s+into|update\s+.*\s+set|drop\s+table)",
    r"(?i)(--|#|/\*|\*/|;)",
    r"(?i)\b(OR|AND)\b\s+['\"]?\w+['\"]?\s*[=<>!]\s*['\"]?\w+['\"]?",
    r"(?i)(waitfor\s+delay|pg_sleep|sleep\()",
    r"(?i)(exec\s*\(|execute\s*\(|sp_executesql)",
    r"(?i)('|\"|\b)(union|select|insert|update|delete|drop|truncate|alter|create)('|\"|\b)"
]

XSS_PATTERNS = [
    r"(?i)<script[^>]*>[\s\S]*?</script>",
    r"(?i)javascript:",
    r"(?i)vbscript:",
    r"(?i)onload\s*=|onerror\s*=|onmouseover\s*=|onclick\s*=",
    r"(?i)<img[^>]+src[^>]+>",
    r"(?i)<iframe[^>]+src[^>]+>",
    r"(?i)alert\s*\(|prompt\s*\(|confirm\s*\("
]

# Keyword matching for Jailbreak / Prompt Injection attempts
# (Legacy: Will be replaced by LLM-based detection, kept for reference or fallback if needed)
PROMPT_INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore all instructions",
    "이전 지시 무시",
    "이전 명령 무시",
    "system prompt",
    "시스템 프롬프트",
    "you are a developer",
    "개발자 모드",
    "admin",
    "관리자 권한",
    "jailbreak",
    "DAN",
    "do anything now",
    "forget what you were told",
    "이전에 들은 것은 잊어버려",
    "what were your original instructions"
]

CMD_PATTERNS = [
    r"(?i)([;&|`\$]|\b(and|or)\b)\s*(ls|cat|pwd|whoami|echo|wget|curl|ping|netstat|nc|bash|sh|cmd|powershell)\b",
    r"(?i)system\s*\(.*\)",
    r"(?i)exec\s*\(.*\)"
]

LFI_PATTERNS = [
    r"(?i)(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.\.%2f)",
    r"(?i)(/etc/passwd|/etc/shadow|/etc/hosts|c:\\windows\\system32|/proc/self/environ|boot\.ini)"
]

RFI_PATTERNS = [
    r"(?i)(http|https|ftp)://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?\?\w+=(http|https|ftp)://",
    r"(?i)(php://input|php://filter|data://text|expect://)"
]

def detect_sqli(payload: str) -> bool:
    for pattern in SQLI_PATTERNS:
        if re.search(pattern, payload):
            return True
    return False

def detect_xss(payload: str) -> bool:
    for pattern in XSS_PATTERNS:
        if re.search(pattern, payload):
            return True
    return False

def detect_cmd(payload: str) -> bool:
    for pattern in CMD_PATTERNS:
        if re.search(pattern, payload):
            return True
    return False

def detect_lfi(payload: str) -> bool:
    for pattern in LFI_PATTERNS:
        if re.search(pattern, payload):
            return True
    return False

def detect_rfi(payload: str) -> bool:
    for pattern in RFI_PATTERNS:
        if re.search(pattern, payload):
            return True
    return False

def analyze_payload(payload: str) -> dict:
    """
    Analyzes a payload to determine if it's an attack, and extract context.
    Returns: {"is_attack": bool, "attack_type": str, "context": str}
    """
    result = {"is_attack": False, "attack_type": "none", "context": payload}
    
    # Prompt injection is now handled asynchronously by LLM, so it's removed from this regex pipeline
    
    # Check OS Command Injection
    if detect_cmd(payload):
        result["is_attack"] = True
        result["attack_type"] = "OS Command Injection"
        result["target_data"] = "Server OS / System Shell"
    # Check LFI
    elif detect_lfi(payload):
        result["is_attack"] = True
        result["attack_type"] = "Local File Inclusion (LFI)"
        result["target_data"] = "Local File System / Config"
    # Check RFI
    elif detect_rfi(payload):
        result["is_attack"] = True
        result["attack_type"] = "Remote File Inclusion (RFI)"
        result["target_data"] = "Remote Execution"
    # Check XSS before SQLi because SQLi patterns like <, > might falsely flag XSS as SQLi
    elif detect_xss(payload):
        result["is_attack"] = True
        result["attack_type"] = "Cross-Site Scripting (XSS)"
        result["target_data"] = "Client-Side Execution"
    # Check SQLi
    elif detect_sqli(payload):
        result["is_attack"] = True
        result["attack_type"] = "SQL Injection"
        # Extract intent - simply looking at the table names or keywords
        if "user" in payload.lower() or "admin" in payload.lower() or "member" in payload.lower():
            result["target_data"] = "User Credentials"
        else:
            result["target_data"] = "Database Schema/System Information"
            
    return result
