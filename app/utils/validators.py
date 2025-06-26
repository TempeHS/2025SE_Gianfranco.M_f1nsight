import re
from html import escape

def validate_password(password):
    """
    # VALIDATE PASSWORD REQUIREMENTS
    # - MIN 8 CHARACTERS
    # - AT LEAST 1 UPPERCASE
    # - AT LEAST 1 NUMBER
    """
    if len(password) < 8:
        return False, "password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "password must contain at least one number"
    return True, "password valid"

def validate_email(email):
    """
    # VALIDATE EMAIL FORMAT USING REGEX
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "invalid email format"
    return True, "email valid"

def validate_username(username):
    """
    # VALIDATE USERNAME LENGTH AND CHARACTERS
    """
    if len(username) > 20:
        return False, "username must be less than 20 characters"
    if not username.isalnum():
        return False, "username can only contain letters and numbers"
    return True, "username valid"

def sanitize_input(data):
    """
    # SANITIZE USER INPUT TO PREVENT XSS
    """
    if isinstance(data, str):
        return escape(data.strip())
    return data