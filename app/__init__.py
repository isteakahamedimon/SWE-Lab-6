import os
from flask import Flask, session, g
from flask_wtf.csrf import CSRFProtect
from app.config import Config
from app.database import db

csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance directory exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.categories import categories_bp
    from app.routes.transactions import transactions_bp
    from app.routes.budgets import budgets_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(reports_bp)

    # Context processor to inject auth user and notifications to all templates
    @app.context_processor
    def inject_user_context():
        user_id = session.get("user_id")
        current_user = None
        unread_notifications = []
        if user_id:
            from app.models.user import User
            from app.models.notification import Notification

            current_user = db.session.get(User, user_id)
            if current_user:
                unread_notifications = (
                    Notification.query.filter_by(user_id=user_id, is_read=False)
                    .order_by(Notification.created_at.desc())
                    .all()
                )

        return {
            "current_user": current_user,
            "unread_notifications": unread_notifications,
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template("base.html", error_title="404 - Page Not Found", error_message="The page you requested does not exist."), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template("base.html", error_title="500 - Server Error", error_message="An unexpected server error occurred."), 500

    # Auto create tables on app start
    with app.app_context():
        db.create_all()

    return app
