from flask import Blueprint, render_template, session, request
from datetime import date
from app.routes.auth import login_required
from app.services.report_service import ReportService

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")
report_service = ReportService()


@reports_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    report_type = request.args.get("type", "monthly_summary")
    selected_month = request.args.get("month", date.today().strftime("%Y-%m"))
    category_type = request.args.get("cat_type", "expense")

    report_data = None
    error = None

    try:
        report_data = report_service.generate_report(
            report_type=report_type,
            user_id=user_id,
            month=selected_month,
            type=category_type,
            limit=12,
        )
    except Exception as e:
        error = str(e)

    return render_template(
        "reports/index.html",
        report_type=report_type,
        selected_month=selected_month,
        category_type=category_type,
        report=report_data,
        error=error,
    )
