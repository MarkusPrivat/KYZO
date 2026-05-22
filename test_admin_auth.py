#!/usr/bin/env python3
"""
Test script to verify admin authentication works correctly
"""

import jwt
from datetime import datetime, timedelta, timezone

# Simulate the backend token creation (from auth_service.py)
def create_backend_token():
    """Create a token like the backend does"""
    # Simulate user data
    user_email = "john-smith@kyzo.com"
    user_role = "admin"  # This comes from UserRole.ADMIN.value
    
    # Create token payload like backend does
    to_encode = {
        "sub": user_email, 
        "scope": user_role  # Backend uses "scope" (singular)
    }
    
    # Add expiration
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    
    # Sign with a test secret
    test_secret = "test-secret-key-for-development"
    token = jwt.encode(to_encode, test_secret, algorithm="HS256")
    
    return token

# Simulate the frontend token parsing (from admin.py - FIXED version)
def get_user_role_from_token_frontend(token, auth_secret=""):
    """Extract user role from JWT token - FIXED version"""
    try:
        if auth_secret:
            payload = jwt.decode(
                token,
                auth_secret,
                algorithms=["HS256"],
                options={"verify_signature": True},
            )
        else:
            # Fallback: decode without verification (development only)
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256"],
            )
        
        # Check for role in scope claim (backend uses "scope", singular) - FIXED
        if "scope" in payload and payload["scope"]:
            return payload["scope"]
        # Also check legacy field names for backward compatibility
        elif "scopes" in payload and payload["scopes"]:
            return payload["scopes"]
        elif "role" in payload:
            return payload["role"]
        elif "user_role" in payload:
            return payload["user_role"]
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    
    return None

def is_admin_user(token, auth_secret=""):
    """Check if the user has admin role"""
    role = get_user_role_from_token_frontend(token, auth_secret)
    return role == "admin" or (isinstance(role, list) and "admin" in role)

# Test the fix
if __name__ == "__main__":
    print("Testing admin authentication fix...")
    
    # Create a token like the backend does
    test_secret = "test-secret-key-for-development"
    token = create_backend_token()
    
    print(f"Created token: {token}")
    
    # Decode the token to see its contents
    payload = jwt.decode(token, test_secret, algorithms=["HS256"])
    print(f"Token payload: {payload}")
    
    # Test the FIXED frontend parsing
    role = get_user_role_from_token_frontend(token, test_secret)
    print(f"Extracted role: {role}")
    
    # Test admin check
    is_admin = is_admin_user(token, test_secret)
    print(f"Is admin user: {is_admin}")
    
    if is_admin:
        print("SUCCESS: Admin authentication should now work!")
        print("The user will be allowed to access the admin dashboard.")
    else:
        print("FAILURE: Admin authentication still not working.")
        print("The user will be redirected to the homepage.")