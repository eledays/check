"""Telegram Mini App authentication utilities."""
import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from typing import Optional


def verify_telegram_web_app_data(init_data: str, bot_token: str) -> dict | None:
    """
    Verify that the init data received from Telegram Mini App is valid.
    
    Args:
        init_data: Init data string from Telegram.WebApp.initData
        bot_token: Your Telegram Bot Token
    
    Returns:
        Parsed user data if valid, None otherwise
    """
    try:
        # Parse the init data
        parsed_data = dict(parse_qsl(init_data))
        
        if 'hash' not in parsed_data:
            return None
        
        received_hash = parsed_data.pop('hash')
        
        # Create data check string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = '\n'.join(data_check_arr)
        
        # Calculate secret key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            return None
        
        # Parse user data
        if 'user' in parsed_data:
            user_data = json.loads(parsed_data['user'])
            return user_data
        
        return None
        
    except Exception as e:
        print(f"Error verifying Telegram data: {e}")
        return None


def get_or_create_user(telegram_id: int):
    """
    Get existing user by telegram_id or create a new one.
    
    Args:
        telegram_id: Telegram user ID
    
    Returns:
        User object
    """
    from app.models import User
    from app import db
    
    user = User.query.filter_by(telegram_id=telegram_id).first()
    
    if not user:
        user = User()
        user.telegram_id = telegram_id
        db.session.add(user)
        db.session.commit()
    
    return user
