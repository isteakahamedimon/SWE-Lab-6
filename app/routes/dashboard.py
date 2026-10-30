from flask import Blueprint, render_template, redirect, url_for, session, request
from app.routes.auth import login_required
from app.services.report_service import ReportService
from app.repositories.notification_repository import NotificationRepository

dashboard_bp = Blueprint("dashboard", __name__)
report_service = ReportService()
notification_repo = NotificationRepository()


@dashboard_bp.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user_id = session["user_id"]
    summary = report_service.get_dashboard_summary(user_id)
    return render_template("dashboard/index.html", summary=summary)


@dashboard_bp.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    user_id = session["user_id"]
    notification_repo.mark_all_as_read(user_id)
    next_url = request.referrer or url_for("dashboard.index")
    return redirect(next_url)
