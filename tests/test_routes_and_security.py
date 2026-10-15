import pytest
from flask import url_for
from app.models import User, Zone, ShiftSetting, Attendance
from app.extensions import db
from app.i18n import t


def test_public_routes(client):
    res = client.get('/')
    assert res.status_code == 302
    assert '/login' in res.location

    res_login = client.get('/login')
    assert res_login.status_code == 200
    assert "تسجيل الدخول" in res_login.get_data(as_text=True)


def test_unauthenticated_access_protected_routes(client):
    protected_urls = [
        '/employee/dashboard',
        '/employee/attendance',
        '/employee/profile',
        '/admin/dashboard',
        '/admin/employees',
        '/admin/shifts',
        '/admin/zones',
        '/admin/reports',
        '/admin/settings',
    ]
    for url in protected_urls:
        res = client.get(url)
        assert res.status_code == 302
        assert '/login' in res.location


def test_employee_cannot_access_admin_routes(client, app):
    employee = User.query.filter_by(role='employee').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(employee.id)

    admin_urls = [
        '/admin/dashboard',
        '/admin/employees',
        '/admin/shifts',
        '/admin/zones',
        '/admin/reports',
        '/admin/settings',
    ]
    for url in admin_urls:
        res = client.get(url)
        assert res.status_code == 302 or res.status_code == 403


def test_admin_full_flow_page_renders(client, app):
    admin = User.query.filter_by(role='admin').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    # Admin Dashboard
    res_dash = client.get('/admin/dashboard')
    assert res_dash.status_code == 200

    # Employees List & Create Page
    res_emp = client.get('/admin/employees')
    assert res_emp.status_code == 200
    res_emp_create = client.get('/admin/employees/create')
    assert res_emp_create.status_code == 200

    # Shifts List & Create Page
    res_shifts = client.get('/admin/shifts')
    assert res_shifts.status_code == 200
    res_shifts_create = client.get('/admin/shifts/create')
    assert res_shifts_create.status_code == 200

    # Zones List & Create Page
    res_zones = client.get('/admin/zones')
    assert res_zones.status_code == 200
    res_zones_create = client.get('/admin/zones/create')
    assert res_zones_create.status_code == 200

    # Reports & Settings Page
    res_reports = client.get('/admin/reports')
    assert res_reports.status_code == 200
    res_settings = client.get('/admin/settings')
    assert res_settings.status_code == 200


def test_employee_full_flow_page_renders(client, app):
    employee = User.query.filter_by(role='employee').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(employee.id)

    # Dashboard
    res_dash = client.get('/employee/dashboard')
    assert res_dash.status_code == 200

    # Attendance History
    res_history = client.get('/employee/attendance')
    assert res_history.status_code == 200

    # Profile
    res_profile = client.get('/employee/profile')
    assert res_profile.status_code == 200

    # WebAuthn register page
    res_webauthn = client.get('/employee/webauthn/register')
    assert res_webauthn.status_code == 200


def test_reports_export_excel_and_csv(client, app):
    admin = User.query.filter_by(role='admin').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    # Arabic default
    res_excel_ar = client.get('/admin/reports?export=excel')
    assert res_excel_ar.status_code == 200
    assert 'spreadsheetml' in res_excel_ar.content_type

    res_csv_ar = client.get('/admin/reports?export=csv')
    assert res_csv_ar.status_code == 200
    assert 'csv' in res_csv_ar.content_type
    # Must start with UTF-8 BOM
    assert res_csv_ar.data.startswith(b'\xef\xbb\xbf')

    # English mode
    with client.session_transaction() as sess:
        sess['lang'] = 'en'

    res_excel_en = client.get('/admin/reports?export=excel')
    assert res_excel_en.status_code == 200
    assert 'spreadsheetml' in res_excel_en.content_type

    res_csv_en = client.get('/admin/reports?export=csv')
    assert res_csv_en.status_code == 200
    assert 'csv' in res_csv_en.content_type
    assert res_csv_en.data.startswith(b'\xef\xbb\xbf')
    assert b'Date' in res_csv_en.data
    assert b'Employee Name' in res_csv_en.data


def test_sec04_deactivated_user_session_rejected(client, app):
    """SEC-04: Deactivated user must be logged out immediately by user_loader."""
    with app.app_context():
        user = User.query.filter_by(role='employee').first()
        user.is_active = False
        db.session.commit()
        user_id = user.id

    try:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)

        # Inactive user accessing employee page must be redirected to login
        res = client.get('/employee/dashboard')
        assert res.status_code == 302
        assert '/login' in res.headers.get('Location', '')
    finally:
        with app.app_context():
            user = User.query.get(user_id)
            user.is_active = True
            db.session.commit()


def test_sec05_unique_attendance_constraint(app):
    """SEC-05: Database must reject duplicate (user_id, date) rows via UniqueConstraint."""
    from sqlalchemy.exc import IntegrityError
    from datetime import date
    with app.app_context():
        emp = User.query.filter_by(role='employee').first()
        test_date = date(2026, 7, 15)
        # Clean any preexisting row
        Attendance.query.filter_by(user_id=emp.id, date=test_date).delete()
        db.session.commit()

        att1 = Attendance(user_id=emp.id, zone_id=emp.zone_id, date=test_date, status='completed')
        db.session.add(att1)
        db.session.commit()

        att2 = Attendance(user_id=emp.id, zone_id=emp.zone_id, date=test_date, status='completed')
        db.session.add(att2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Cleanup
        Attendance.query.filter_by(user_id=emp.id, date=test_date).delete()
        db.session.commit()


def test_sec06_nan_inf_coordinates_rejected(app):
    """SEC-06: NaN and Inf coordinates must be rejected by sign_in and sign_out."""
    from app.services.attendance_service import sign_in, sign_out, CAIRO_TZ
    from datetime import datetime, timezone
    with app.app_context():
        emp = User.query.filter_by(role='employee').first()
        with pytest.raises(ValueError):
            sign_in(emp, float('nan'), 31.0)

        with pytest.raises(ValueError):
            sign_in(emp, float('inf'), 31.0)

        # Ensure an active attendance exists so sign_out reaches the coordinate validation
        cairo_today = datetime.now(timezone.utc).astimezone(CAIRO_TZ).date()
        att = Attendance.query.filter_by(user_id=emp.id, date=cairo_today).first()
        if not att:
            att = Attendance(user_id=emp.id, zone_id=emp.zone_id, date=cairo_today, status='active', sign_in_time=datetime.now(timezone.utc))
            db.session.add(att)
            db.session.commit()
        else:
            att.status = 'active'
            db.session.commit()

        with pytest.raises(ValueError):
            sign_out(emp, 30.0, float('nan'))

        with pytest.raises(ValueError):
            sign_out(emp, float('inf'), 31.0)


def test_sec09_admin_close_attendance(client, app):
    """SEC-09: Admin can manually close forgotten active attendance rows."""
    from datetime import date, datetime, timezone
    from app.services.attendance_service import CAIRO_TZ
    with app.app_context():
        emp = User.query.filter_by(role='employee').first()
        cairo_today = datetime.now(timezone.utc).astimezone(CAIRO_TZ).date()
        att = Attendance.query.filter_by(user_id=emp.id, date=cairo_today).first()
        if not att:
            att = Attendance(
                user_id=emp.id,
                zone_id=emp.zone_id,
                date=cairo_today,
                sign_in_time=datetime.now(timezone.utc),
                status='active',
            )
            db.session.add(att)
            db.session.commit()
        else:
            att.status = 'active'
            att.sign_out_time = None
            db.session.commit()
        att_id = att.id

    admin = User.query.filter_by(role='admin').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = client.post(f'/admin/attendance/{att_id}/close')
    assert res.status_code == 302

    with app.app_context():
        closed_att = Attendance.query.get(att_id)
        assert closed_att.status == 'completed'
        assert closed_att.sign_out_time is not None
        assert closed_att.total_hours is not None


def test_sec10_settings_post_read_only(client, app):
    """SEC-10: Settings POST should flash read-only notice, not a fake saved success message."""
    admin = User.query.filter_by(role='admin').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = client.post('/admin/settings', data={'system_name': 'Hacked'}, follow_redirects=True)
    assert res.status_code == 200
    expected_msg = t('flash_settings_read_only', lang='ar')
    assert expected_msg in res.data.decode('utf-8')


def test_sec19_formula_injection_sanitization():
    """SEC-19: CSV/Excel cell values starting with =, +, -, @ must be neutralized."""
    from app.services.report_service import _sanitize_cell
    assert _sanitize_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert _sanitize_cell("+201000000000") == "'+201000000000"
    assert _sanitize_cell("-admin") == "'-admin"
    assert _sanitize_cell("@mention") == "'@mention"
    assert _sanitize_cell("Normal Text") == "Normal Text"
    assert _sanitize_cell(123) == 123
    assert _sanitize_cell(0) == 0
    assert _sanitize_cell(None) == ''


def test_employee_dashboard_schedule_and_day_off_states(client, app):
    """Test employee schedule strip, status banner, monthly progress, and day-off states."""
    from datetime import datetime, timezone
    from app.services.attendance_service import CAIRO_TZ

    emp = User.query.filter_by(role='employee').first()
    from app.models import WebAuthnCredential
    if not emp.webauthn_credentials:
        cred = WebAuthnCredential(
            user_id=emp.id,
            credential_id='test_cred_dash_schedule',
            public_key=b'test_public_key',
            sign_count=0,
        )
        db.session.add(cred)
        db.session.commit()

    cairo_today = datetime.now(timezone.utc).astimezone(CAIRO_TZ).date()
    today_weekday = cairo_today.weekday()
    # Ensure emp's work_days include today
    emp.work_days = str(today_weekday)
    db.session.commit()

    with client.session_transaction() as sess:
        sess['_user_id'] = str(emp.id)

    # 1. Today is a work day
    res_work = client.get('/employee/dashboard')
    assert res_work.status_code == 200
    html_work = res_work.data.decode('utf-8')
    assert 'schedule-status-banner--work' in html_work
    assert t('status_today_workday', lang='ar') in html_work
    assert t('my_schedule_title', lang='ar') in html_work
    assert 'schedule-strip' in html_work
    assert 'schedule-day--today' in html_work
    assert t('month_attendance_progress', lang='ar') in html_work

    # 2. Today is a day off
    off_day = (today_weekday + 1) % 7
    emp.work_days = str(off_day)
    db.session.commit()

    res_off = client.get('/employee/dashboard')
    assert res_off.status_code == 200
    html_off = res_off.data.decode('utf-8')
    assert 'schedule-status-banner--off' in html_off
    assert t('status_today_day_off', lang='ar') in html_off
    assert t('day_off_signin_note', lang='ar') in html_off
    assert 'btn--day-off' in html_off
    assert t('btn_check_in_extra', lang='ar') in html_off

    # Restore default work days
    emp.work_days = '5,6,0,1,2,3'
    db.session.commit()



