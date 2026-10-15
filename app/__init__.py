import os
from datetime import timezone, date
from zoneinfo import ZoneInfo
from flask import Flask, render_template
from app.config import Config
from app.extensions import db, migrate, login_manager
from app.models import User
from app.i18n import t, get_current_lang, format_localized_date

CAIRO_TZ = ZoneInfo("Africa/Cairo")


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    if isinstance(config_object, dict):
        app.config.from_object(Config)
        app.config.update(config_object)
    elif config_object:
        app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # models must be imported before migrate can see them
    from app.models import User, ShiftSetting, Attendance, Zone

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.employee import employee_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)

    @app.context_processor
    def inject_i18n():
        lang = get_current_lang()
        is_rtl = (lang == 'ar')
        dir_attr = 'rtl' if is_rtl else 'ltr'
        return {
            'current_lang': lang,
            'is_rtl': is_rtl,
            'dir_attr': dir_attr,
            't': t,
            '_': t,
            'today_display': format_localized_date(date.today(), lang)
        }

    @app.template_filter('t')
    def translate_filter(key, **kwargs):
        return t(key, **kwargs)

    @app.template_filter('cairo_time')
    def cairo_time(value, fmt='%I:%M %p'):
        """Display-only conversion of a stored UTC datetime to Africa/Cairo local time.
        Egypt has no fixed UTC offset (DST toggled in recent years), so this always
        goes through zoneinfo — never a hardcoded +2/+3."""
        if value is None:
            return '—'
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(CAIRO_TZ).strftime(fmt)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app