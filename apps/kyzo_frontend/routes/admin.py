"""Admin routes blueprint — Admin panel with JWT authentication and role-based access control."""

import jwt
from flask import Blueprint, render_template, current_app, request, redirect, url_for

admin_bp = Blueprint("admin", __name__)


def get_user_role_from_token(token):
    """Extract user role from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        str: User role (admin, teacher, student) or None if not found
    """
    try:
        auth_secret = current_app.config.get("AUTH_SECRET_KEY", "")
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
        
        # Check for role in scope claim (backend uses "scope", singular)
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


def is_admin_user(token):
    """Check if the user has admin role.
    
    Args:
        token: JWT token string
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    role = get_user_role_from_token(token)
    return role == "admin" or (isinstance(role, list) and "admin" in role)


@admin_bp.route("/admin")
def admin_dashboard():
    """Admin dashboard route with JWT authentication and admin role requirement.
    
    - Requires valid JWT token
    - Requires admin role
    - Redirects to login if token is expired
    - Redirects to homepage if user is not admin
    """
    token = request.cookies.get("jwt_token")
    
    # If no token, redirect to login
    if not token:
        return redirect(url_for("main.login"))
    
    # Check if token is expired
    try:
        auth_secret = current_app.config.get("AUTH_SECRET_KEY", "")
        if auth_secret:
            jwt.decode(
                token,
                auth_secret,
                algorithms=["HS256"],
                options={"require": ["exp"]},
            )
        else:
            # Fallback: decode without verification (development only)
            jwt.decode(
                token,
                options={"verify_signature": False, "require": ["exp"]},
                algorithms=["HS256"],
            )
    except jwt.ExpiredSignatureError:
        # Token expired, redirect to login
        return redirect(url_for("main.login"))
    except jwt.InvalidTokenError:
        # Invalid token, redirect to login
        return redirect(url_for("main.login"))
    
    # Check if user is admin
    if not is_admin_user(token):
        # User is authenticated but not admin, redirect to homepage
        return redirect(url_for("main.index"))
    
    # User is authenticated and is admin, render admin dashboard
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("admin/dashboard.html", api_url=api_url)


@admin_bp.route("/admin/knowledge/subjects")
def knowledge_subjects():
    """Knowledge subjects management route.
    
    - Requires valid JWT token
    - Requires admin role
    - Redirects to login if token is expired
    - Redirects to homepage if user is not admin
    """
    token = request.cookies.get("jwt_token")
    
    # If no token, redirect to login
    if not token:
        return redirect(url_for("main.login"))
    
    # Check if token is expired
    try:
        auth_secret = current_app.config.get("AUTH_SECRET_KEY", "")
        if auth_secret:
            jwt.decode(
                token,
                auth_secret,
                algorithms=["HS256"],
                options={"require": ["exp"]},
            )
        else:
            # Fallback: decode without verification (development only)
            jwt.decode(
                token,
                options={"verify_signature": False, "require": ["exp"]},
                algorithms=["HS256"],
            )
    except jwt.ExpiredSignatureError:
        # Token expired, redirect to login
        return redirect(url_for("main.login"))
    except jwt.InvalidTokenError:
        # Invalid token, redirect to login
        return redirect(url_for("main.login"))
    
    # Check if user is admin
    if not is_admin_user(token):
        # User is authenticated but not admin, redirect to homepage
        return redirect(url_for("main.index"))
    
    # User is authenticated and is admin, render knowledge subjects management
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("admin/knowledge_subjects.html", api_url=api_url)

@admin_bp.route("/admin/knowledge/subjects/<int:subject_id>/topics")
def knowledge_topics(subject_id):
    """Knowledge topics management route for a specific subject.
    
    - Requires valid JWT token
    - Requires admin role
    - Redirects to login if token is expired
    - Redirects to homepage if user is not admin
    - Redirects to subjects list if subject_id is invalid
    
    Args:
        subject_id: ID of the subject to manage topics for
    """
    token = request.cookies.get("jwt_token")
    
    # If no token, redirect to login
    if not token:
        return redirect(url_for("main.login"))
    
    # Check if token is expired
    try:
        auth_secret = current_app.config.get("AUTH_SECRET_KEY", "")
        if auth_secret:
            jwt.decode(
                token,
                auth_secret,
                algorithms=["HS256"],
                options={"require": ["exp"]},
            )
        else:
            # Fallback: decode without verification (development only)
            jwt.decode(
                token,
                options={"verify_signature": False, "require": ["exp"]},
                algorithms=["HS256"],
            )
    except jwt.ExpiredSignatureError:
        # Token expired, redirect to login
        return redirect(url_for("main.login"))
    except jwt.InvalidTokenError:
        # Invalid token, redirect to login
        return redirect(url_for("main.login"))
    
    # Check if user is admin
    if not is_admin_user(token):
        # User is authenticated but not admin, redirect to homepage
        return redirect(url_for("main.index"))
    
    # User is authenticated and is admin, render knowledge topics management
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("admin/knowledge_topics.html", subject_id=subject_id, api_url=api_url)


@admin_bp.route("/admin/users")
def admin_users():
    """Users management route.
    
    - Requires valid JWT token
    - Requires admin role
    - Redirects to login if token is expired
    - Redirects to homepage if user is not admin
    """
    token = request.cookies.get("jwt_token")
    
    if not token:
        return redirect(url_for("main.login"))
    
    try:
        auth_secret = current_app.config.get("AUTH_SECRET_KEY", "")
        if auth_secret:
            jwt.decode(token, auth_secret, algorithms=["HS256"], options={"require": ["exp"]})
        else:
            jwt.decode(token, options={"verify_signature": False, "require": ["exp"]}, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return redirect(url_for("main.login"))
    except jwt.InvalidTokenError:
        return redirect(url_for("main.login"))
    
    if not is_admin_user(token):
        return redirect(url_for("main.index"))
    
    api_url = current_app.config.get("API_URL", "/api/v1")
    return render_template("admin/users.html", api_url=api_url)
