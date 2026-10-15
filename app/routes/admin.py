from datetime import date, datetime, timedelta, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.utils import admin_required
from app.models import Zone, User, ShiftSetting
from app.services.zone_service import create_zone, update_zone, delete_zone
from app.services.shift_service import create_shift, update_shift, delete_shift
from app.services.admin_stats_service import (
    get_dashboard_kpis,
    get_zones_overview,
    get_daily_report,
    get_weekly_trend,
    format_arabic_date,
)
from app.services.attendance_service import get_employee_attendance_summary, CAIRO_TZ, admin_close_attendance
from app.services.report_service import get_report, export_csv, export_excel
from app.i18n import get_current_lang

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    cairo_now = datetime.now(timezone.utc).astimezone(CAIRO_TZ)
    cairo_today = cairo_now.date()

    date_param = request.args.get('date')
    try:
        target_date = datetime.strptime(date_param, '%Y-%m-%d').date() if date_param else cairo_today
    except ValueError:
        target_date = cairo_today

    zone_id = request.args.get('zone_id', type=int)
    status = request.args.get('status') or None
    search = request.args.get('q') or None

    kpis = get_dashboard_kpis(target_date)
    zones = get_zones_overview()
    report_rows = get_daily_report(target_date, zone_id=zone_id, status=status, search=search)
    weekly_trend = get_weekly_trend(target_date)

    return render_template(
        'admin/dashboard.html',
        kpis=kpis,
        zones=zones,
        report_rows=report_rows,
        weekly_trend=weekly_trend,
        target_date=target_date,
        today_display=format_arabic_date(cairo_today),
        filters={'zone_id': zone_id, 'status': status, 'q': search or ''},
    )


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    cairo_now = datetime.now(timezone.utc).astimezone(CAIRO_TZ)
    cairo_today = cairo_now.date()

    date_from_param = request.args.get('date_from')
    date_to_param = request.args.get('date_to')

    try:
        date_from = datetime.strptime(date_from_param, '%Y-%m-%d').date() if date_from_param else cairo_today - timedelta(days=6)
    except ValueError:
        date_from = cairo_today - timedelta(days=6)

    try:
        date_to = datetime.strptime(date_to_param, '%Y-%m-%d').date() if date_to_param else cairo_today
    except ValueError:
        date_to = cairo_today

    # Keep the range sane regardless of what was typed into the two date inputs.
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    zone_id = request.args.get('zone_id', type=int)
    status = request.args.get('status') or None
    employee_id = request.args.get('employee_id', type=int)

    rows = get_report(date_from, date_to, zone_id=zone_id, status=status, employee_id=employee_id)

    lang = get_current_lang()

    if request.args.get('export') in ('excel', 'xlsx'):
        return export_excel(rows, lang=lang, date_from=date_from, date_to=date_to)
    elif request.args.get('export') == 'csv':
        return export_csv(rows, lang=lang, date_from=date_from, date_to=date_to)

    zones_list = Zone.query.order_by(Zone.id).all()
    employees = User.query.filter_by(role='employee', is_active=True).order_by(User.name).all()

    # Calculate employee attendance summaries
    active_query = User.query.filter_by(role='employee', is_active=True)
    if employee_id:
        target_employees = active_query.filter_by(id=employee_id).all()
    elif zone_id:
        target_employees = active_query.filter_by(zone_id=zone_id).all()
    else:
        target_employees = active_query.all()

    total_expected_days = 0
    total_attended_days = 0
    total_absent_days_count = 0
    total_extra_days_count = 0
    user_summaries = {}

    for emp in target_employees:
        s = get_employee_attendance_summary(emp, date_from, date_to)
        user_summaries[emp.id] = s
        total_expected_days += s['expected_days']
        total_attended_days += s['attended_days']
        total_absent_days_count += len(s['absent_days'])
        total_extra_days_count += len(s['extra_days'])

    overall_attendance_rate = round((total_attended_days / total_expected_days) * 100.0, 1) if total_expected_days > 0 else 100.0

    summary_stats = {
        'expected_days': total_expected_days,
        'attended_days': total_attended_days,
        'absent_days_count': total_absent_days_count,
        'extra_days_count': total_extra_days_count,
        'attendance_rate': overall_attendance_rate,
    }

    return render_template(
        'admin/reports.html',
        rows=rows,
        zones=zones_list,
        employees=employees,
        summary_stats=summary_stats,
        user_summaries=user_summaries,
        date_from=date_from,
        date_to=date_to,
        today_display=format_arabic_date(cairo_today),
        filters={'zone_id': zone_id, 'status': status, 'employee_id': employee_id},
    )


@admin_bp.route('/zones')
@login_required
@admin_required
def zones():
    all_zones = Zone.query.order_by(Zone.id).all()
    return render_template('admin/zones/list.html', zones=all_zones)


@admin_bp.route('/zones/create', methods=['GET', 'POST'])
@login_required
@admin_required
def zones_create():
    if request.method == 'POST':
        try:
            create_zone(
                request.form.get('name'),
                request.form.get('latitude'),
                request.form.get('longitude'),
                request.form.get('radius_meters'),
            )
            flash('flash_zone_created', 'success')
            return redirect(url_for('admin.zones'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/zones/create.html')


@admin_bp.route('/zones/<int:zone_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def zones_edit(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    if request.method == 'POST':
        try:
            update_zone(
                zone_id,
                request.form.get('name'),
                request.form.get('latitude'),
                request.form.get('longitude'),
                request.form.get('radius_meters'),
                is_active=bool(request.form.get('is_active')),
            )
            flash('flash_zone_updated', 'success')
            return redirect(url_for('admin.zones'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/zones/edit.html', zone=zone)


@admin_bp.route('/zones/<int:zone_id>/delete', methods=['POST'])
@login_required
@admin_required
def zones_delete(zone_id):
    try:
        delete_zone(zone_id)
        flash('flash_zone_deleted', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.zones'))


@admin_bp.route('/shifts')
@login_required
@admin_required
def shifts():
    all_shifts = ShiftSetting.query.order_by(ShiftSetting.id).all()
    return render_template('admin/shifts/list.html', shifts=all_shifts)


@admin_bp.route('/shifts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def shifts_create():
    if request.method == 'POST':
        try:
            create_shift(
                request.form.get('name'),
                request.form.get('shift_start_time'),
                request.form.get('sign_in_end_time'),
                request.form.get('grace_period_minutes'),
                request.form.get('min_full_shift_hours'),
            )
            flash('flash_shift_created', 'success')
            return redirect(url_for('admin.shifts'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/shifts/create.html')


@admin_bp.route('/shifts/<int:shift_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def shifts_edit(shift_id):
    shift = ShiftSetting.query.get_or_404(shift_id)
    if request.method == 'POST':
        try:
            update_shift(
                shift_id,
                request.form.get('name'),
                request.form.get('shift_start_time'),
                request.form.get('sign_in_end_time'),
                request.form.get('grace_period_minutes'),
                request.form.get('min_full_shift_hours'),
                is_active=bool(request.form.get('is_active')),
            )
            flash('flash_shift_updated', 'success')
            return redirect(url_for('admin.shifts'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('admin/shifts/edit.html', shift=shift)


@admin_bp.route('/shifts/<int:shift_id>/delete', methods=['POST'])
@login_required
@admin_required
def shifts_delete(shift_id):
    try:
        delete_shift(shift_id)
        flash('flash_shift_deleted', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.shifts'))


# --- Employees Management Routes ----------------------------------------------

@admin_bp.route('/employees')
@login_required
@admin_required
def employees():
    all_employees = User.query.filter_by(role='employee').order_by(User.id.desc()).all()
    return render_template('admin/employees/list.html', employees=all_employees)


@admin_bp.route('/employees/create', methods=['GET', 'POST'])
@login_required
@admin_required
def employees_create():
    zones_list = Zone.query.filter_by(is_active=True).all()
    shifts_list = ShiftSetting.query.filter_by(is_active=True).all()
    default_work_days = [5, 6, 0, 1, 2, 3]
    selected_work_days = default_work_days
    form_data = {}

    if request.method == 'POST':
        work_days = request.form.getlist('work_days')
        selected_work_days = [int(x) for x in work_days if x.isdigit()]
        form_data = request.form
        try:
            from app.services.auth_service import create_user
            create_user(
                name=request.form.get('name'),
                password=request.form.get('password'),
                role='employee',
                zone_id=request.form.get('zone_id', type=int),
                shift_setting_id=request.form.get('shift_setting_id', type=int),
                work_days=work_days,
            )
            flash('flash_employee_created', 'success')
            return redirect(url_for('admin.employees'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template(
        'admin/employees/create.html',
        zones=zones_list,
        shifts=shifts_list,
        selected_work_days=selected_work_days,
        form_data=form_data,
    )


@admin_bp.route('/employees/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def employees_edit(user_id):
    emp = User.query.get_or_404(user_id)
    if emp.role == 'admin':
        flash('flash_employee_admin_edit', 'danger')
        return redirect(url_for('admin.employees'))

    zones_list = Zone.query.filter_by(is_active=True).all()
    shifts_list = ShiftSetting.query.filter_by(is_active=True).all()
    selected_work_days = emp.work_days_list
    form_data = None

    if request.method == 'POST':
        work_days = request.form.getlist('work_days')
        selected_work_days = [int(x) for x in work_days if x.isdigit()]
        form_data = request.form
        try:
            from app.services.auth_service import update_user
            update_user(
                user_id=user_id,
                name=request.form.get('name'),
                password=request.form.get('password'),
                zone_id=request.form.get('zone_id'),
                shift_setting_id=request.form.get('shift_setting_id'),
                is_active=bool(request.form.get('is_active')),
                work_days=work_days,
            )
            flash('flash_employee_updated', 'success')
            return redirect(url_for('admin.employees'))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template(
        'admin/employees/edit.html',
        employee=emp,
        zones=zones_list,
        shifts=shifts_list,
        selected_work_days=selected_work_days,
        form_data=form_data,
    )


@admin_bp.route('/employees/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def employees_delete(user_id):
    try:
        from app.services.auth_service import delete_user
        delete_user(user_id)
        flash('flash_employee_deleted', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.employees'))


@admin_bp.route('/employees/<int:user_id>/reset-devices', methods=['POST'])
@login_required
@admin_required
def employees_reset_devices(user_id):
    emp = User.query.get_or_404(user_id)
    try:
        from app.models import WebAuthnCredential
        from app.extensions import db
        WebAuthnCredential.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        flash('flash_devices_reset', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.employees'))


# --- System Settings Routes --------------------------------------------------

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        # SEC-10: Settings are read-only in this version; flashing "saved" was misleading.
        flash('flash_settings_read_only', 'info')
        return redirect(url_for('admin.settings'))

    from app.models import User, Zone, ShiftSetting, Attendance, WebAuthnCredential
    stats = {
        'total_employees': User.query.filter_by(role='employee').count(),
        'total_zones': Zone.query.count(),
        'total_shifts': ShiftSetting.query.count(),
        'total_attendance': Attendance.query.count(),
        'registered_devices': WebAuthnCredential.query.count(),
    }

    return render_template('admin/settings.html', stats=stats)


# --- Attendance Admin Actions ------------------------------------------------

@admin_bp.route('/attendance/<int:attendance_id>/close', methods=['POST'])
@login_required
@admin_required
def attendance_close(attendance_id):
    """SEC-09: Admin action to close an active attendance record for an employee
    who forgot to sign out.
    """
    try:
        admin_close_attendance(attendance_id)
        flash('flash_attendance_closed', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception:
        flash('flash_attendance_close_error', 'danger')
    return redirect(request.referrer or url_for('admin.dashboard'))