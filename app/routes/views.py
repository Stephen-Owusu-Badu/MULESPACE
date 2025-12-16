"""
View routes for rendering HTML templates.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Homepage - redirects based on user role."""
    if current_user.is_authenticated:
        if current_user.role in ['admin', 'department_admin']:
            return redirect(url_for("views.admin_dashboard"))
        else:
            return redirect(url_for("views.student_dashboard"))
    return render_template("index.html")


@views_bp.route("/login")
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for("views.events"))
    return render_template("login.html")


@views_bp.route("/logout")
@login_required
def logout():
    """Logout user and redirect to login page."""
    from flask_login import logout_user
    logout_user()
    return redirect(url_for("views.login"))


@views_bp.route("/register")
def register():
    """Registration page."""
    if current_user.is_authenticated:
        return redirect(url_for("views.events"))
    return render_template("register.html")


@views_bp.route("/events")
def events():
    """Events listing page."""
    return render_template("events.html")


@views_bp.route("/events/<int:event_id>")
def event_detail(event_id):
    """Single event detail page."""
    return render_template("event_detail.html", event_id=event_id)


@views_bp.route("/calendar")
@login_required
def calendar():
    """Calendar view page."""
    return render_template("calendar.html")


@views_bp.route("/my-events")
@login_required
def my_events():
    """My events page (same as calendar)."""
    return render_template("calendar.html")


@views_bp.route("/admin")
@login_required
def admin_dashboard():
    """Admin dashboard - requires admin role."""
    if current_user.role not in ['admin', 'department_admin']:
        return redirect(url_for("views.student_dashboard"))
    return render_template("admin.html")


@views_bp.route("/student")
@login_required
def student_dashboard():
    """Student dashboard."""
    return render_template("student_dashboard.html")


@views_bp.route("/check-in")
def check_in_form():
    """Check-in form page (accessed via QR code)."""
    return render_template("checkin_form.html")


@views_bp.route("/profile")
@login_required
def profile():
    """User profile page."""
    return render_template("profile.html")
