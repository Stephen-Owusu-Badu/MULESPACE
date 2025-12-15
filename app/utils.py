import os
from functools import wraps

import qrcode
from flask import jsonify
from flask_login import current_user


def generate_qr_code(event_id):
    """Generate QR code for event check-in."""
    qr_dir = os.path.join("app", "static", "qrcodes")
    os.makedirs(qr_dir, exist_ok=True)

    # Generate QR code data (URL to check-in endpoint)
    qr_data = f"https://mulespace.herokuapp.com/api/attendance/check-in?event_id={event_id}"

    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code
    filename = f"event_{event_id}.png"
    filepath = os.path.join(qr_dir, filename)
    img.save(filepath)

    return f"/static/qrcodes/{filename}"


def require_role(roles):
    """Decorator to require specific user roles."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401

            if current_user.role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_email(email):
    """Basic email validation."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None
