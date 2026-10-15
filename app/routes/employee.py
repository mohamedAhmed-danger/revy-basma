from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user

from app.models import Attendance
from app.services.attendance_service import (
    sign_in,
    sign_out,
    get_dashboard_context,
    get_history,
    get_employee_attendance_summary,
    CAIRO_TZ,
)
from app.services import webauthn_service

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


@employee_bp.route('/dashboard')
@login_required
def dashboard():
    cairo_today = datetime.now(timezone.utc).astimezone(CAIRO_TZ).date()
    is_today_workday = current_user.is_workday(cairo_today)
    month_start = date(cairo_today.year, cairo_today.month, 1)
    month_summary = get_employee_attendance_summary(current_user, month_start, cairo_today)

    today_attendance = Attendance.query.filter_by(
        user_id=current_user.id, date=cairo_today
    ).first()

    # Optional: the page auto-submits a plain GET form with lat/lng on load
    # (see dashboard.html) so the status card can show a *live* inside/outside
    # check — still a normal Flask route + render_template, no JSON/fetch.
    context = get_dashboard_context(
        current_user, today_attendance,
        live_lat=request.args.get('lat'),
        live_lng=request.args.get('lng'),
    )

    # Batch 12 — WebAuthn is a required third factor on sign-in/sign-out, so
    # before rendering we work out whether an action is pending today, and if
    # the employee already has a registered device, generate a fresh
    # authentication challenge for it *now* (server-rendered into the page,
    # per the project's no-fetch/no-JSON-endpoint convention) rather than via
    # any kind of API call from the browser.
    if today_attendance is None:
        pending_action = 'sign_in'
    elif today_attendance.status == 'active':
        pending_action = 'sign_out'
    else:
        pending_action = None

    has_webauthn = bool(context['webauthn_credentials'])
    webauthn_auth_options = None

    if pending_action and has_webauthn:
        try:
            options_json, challenge = webauthn_service.build_authentication_options(current_user)
            session['webauthn_auth_challenge'] = challenge
            webauthn_auth_options = options_json
        except ValueError:
            # Shouldn't happen since has_webauthn already gates this, but fail
            # closed into "register your device" rather than a broken button.
            has_webauthn = False

    # Batch 15 — the "live duration" ticking clock and the sign-out
    # confirmation card both need the sign-in moment as a client-side
    # timestamp (JS Date, not a server-formatted string), so it's computed
    # once here rather than re-parsed in the template.
    sign_in_epoch_ms = None
    if today_attendance and today_attendance.status == 'active' and today_attendance.sign_in_time:
        sign_in_time = today_attendance.sign_in_time
        if sign_in_time.tzinfo is None:
            sign_in_time = sign_in_time.replace(tzinfo=timezone.utc)
        sign_in_epoch_ms = int(sign_in_time.timestamp() * 1000)

    return render_template(
        'employee/dashboard.html',
        today_attendance=today_attendance,
        pending_action=pending_action,
        has_webauthn=has_webauthn,
        webauthn_auth_options=webauthn_auth_options,
        sign_in_epoch_ms=sign_in_epoch_ms,
        cairo_today=cairo_today,
        is_today_workday=is_today_workday,
        month_summary=month_summary,
        active_nav='home',
        **context,
    )


@employee_bp.route('/attendance')
@login_required
def history():
    records = get_history(current_user)
    return render_template('employee/history.html', records=records, active_nav='history')


@employee_bp.route('/profile')
@login_required
def profile():
    return render_template('employee/profile.html', active_nav='profile')


@employee_bp.route('/sign-in', methods=['POST'])
@login_required
def sign_in_route():
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    webauthn_credential = request.form.get('webauthn_credential')

    if not lat or not lng:
        flash('flash_location_unavailable', 'danger')
        return redirect(url_for('employee.dashboard'))

    # Batch 12 — WebAuthn check happens before the GPS/business-logic check,
    # as a third factor on top of location + time window (not instead of them).
    challenge = session.pop('webauthn_auth_challenge', None)
    try:
        webauthn_service.verify_authentication(current_user, webauthn_credential, challenge)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('employee.dashboard'))

    try:
        sign_in(current_user, lat, lng)
        flash('flash_signin_success', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/sign-out', methods=['POST'])
@login_required
def sign_out_route():
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    webauthn_credential = request.form.get('webauthn_credential')

    if not lat or not lng:
        flash('flash_location_unavailable', 'danger')
        return redirect(url_for('employee.dashboard'))

    challenge = session.pop('webauthn_auth_challenge', None)
    try:
        webauthn_service.verify_authentication(current_user, webauthn_credential, challenge)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('employee.dashboard'))

    try:
        sign_out(current_user, lat, lng)
        flash('flash_signout_success', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/webauthn/register')
@login_required
def webauthn_register():
    existing_credentials = current_user.webauthn_credentials

    # ── Security Rule ─────────────────────────────────────────────────────────
    # If the user already has a registered device, they CANNOT register a new
    # one without the admin first resetting their devices. This prevents an
    # attacker who stole the employee's email+password from registering their
    # own biometric and impersonating the employee.
    # ──────────────────────────────────────────────────────────────────────────
    if existing_credentials:
        flash(
            'flash_device_already_exists',
            'warning'
        )
        return redirect(url_for('employee.profile'))

    options_json, challenge = webauthn_service.build_registration_options(current_user)
    session['webauthn_reg_challenge'] = challenge
    return render_template(
        'employee/webauthn_register.html',
        webauthn_reg_options=options_json,
        credentials=existing_credentials,
        active_nav='profile',
    )


@employee_bp.route('/webauthn/register', methods=['POST'])
@login_required
def webauthn_register_submit():
    credential = request.form.get('credential')
    nickname = request.form.get('nickname')
    challenge = session.pop('webauthn_reg_challenge', None)

    # Double-check: if the user somehow POSTed directly but already has a device, reject it.
    if current_user.webauthn_credentials:
        flash('flash_device_locked', 'danger')
        return redirect(url_for('employee.profile'))

    try:
        webauthn_service.verify_and_save_registration(current_user, credential, challenge, nickname)
        flash('flash_device_enrolled', 'success')
        return redirect(url_for('employee.dashboard'))
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('employee.webauthn_register'))


@employee_bp.route('/webauthn/credentials/<int:credential_id>/delete', methods=['POST'])
@login_required
def webauthn_credential_delete(credential_id):
    try:
        webauthn_service.delete_credential(current_user, credential_id)
        flash('flash_device_deleted', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('employee.webauthn_register'))
