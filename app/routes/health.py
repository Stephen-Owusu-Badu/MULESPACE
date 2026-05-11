"""Operational endpoints (no authentication)."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """Liveness probe for load balancers and process supervisors."""
    return jsonify({"status": "ok", "service": "mulespace"}), 200
