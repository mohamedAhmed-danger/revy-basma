from flask import Blueprint, redirect, url_for, session, request, make_response
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('employee.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/set-locale/<locale>')
def set_locale(locale):
    """Switch language between Arabic ('ar') and English ('en')."""
    if locale not in ('ar', 'en'):
        locale = 'ar'
    session['lang'] = locale
    
    # Redirect back to the referring page or fallback to home
    referrer = request.referrer
    if not referrer or '/set-locale/' in referrer:
        referrer = url_for('main.home')
    
    response = make_response(redirect(referrer))
    response.set_cookie('lang', locale, max_age=60*60*24*365, samesite='Lax')
    return response