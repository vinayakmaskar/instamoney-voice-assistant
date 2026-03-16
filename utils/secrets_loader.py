"""
Utility to load secrets from secrets.json file.
"""
import json
import os
from pathlib import Path


def load_secrets():
    """
    Load secrets from secrets.json file.
    
    Returns:
        dict: Dictionary containing all secrets
    """
    # Get project root directory
    project_root = Path(__file__).resolve().parent.parent
    secrets_file = project_root / 'secrets.json'
    
    if not secrets_file.exists():
        raise FileNotFoundError(
            f"secrets.json not found at {secrets_file}. "
            "Please copy secrets.json.example to secrets.json and fill in your values."
        )
    
    with open(secrets_file, 'r') as f:
        secrets = json.load(f)
    
    # Validate required secrets
    required_secrets = ['GEMINI_API_KEY', 'SECRET_KEY', 'JWT_SECRET_KEY']
    missing = [key for key in required_secrets if not secrets.get(key)]
    
    if missing:
        raise ValueError(
            f"Missing required secrets in secrets.json: {', '.join(missing)}"
        )
    
    return secrets


def get_secret(key, default=None):
    """
    Get a specific secret value.
    
    Args:
        key: Secret key name
        default: Default value if key not found
    
    Returns:
        Secret value or default
    """
    try:
        secrets = load_secrets()
        return secrets.get(key, default)
    except (FileNotFoundError, ValueError):
        # Fallback to environment variable
        return os.environ.get(key, default)

