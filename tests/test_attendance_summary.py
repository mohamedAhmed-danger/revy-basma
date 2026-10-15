import pytest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from app.extensions import db
from app.models import User, Zone, ShiftSetting, Attendance
from app.services.attendance_service import get_employee_attendance_summary, CAIRO_TZ
from app.services.auth_service import create_user, update_user, validate_and_normalize_work_days
from app.services.admin_stats_service import get_dashboard_kpis
from app.services.report_service import export_csv, export_excel
from app.i18n import t


def test_work_days_model_defaults_and_helpers(app):
    with app.app_context():
        zone = Zone.query.first()
        shift = ShiftSetting.query.first()
        # Default creation without specifying work_days
        user = User(
            name="Default Days User",
            password_hash="hash",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=shift.id,
        )
        db.session.add(user)
        db.session.commit()

        assert user.work_days == "5,6,0,1,2,3"
        assert user.work_days_list == [5, 6, 0, 1, 2, 3]

        # Saturday = 5, Friday = 4
        # 2026-10-10 is Saturday (weekday 5), 2026-10-16 is Friday (weekday 4)
        sat = date(2026, 10, 10)
        fri = date(2026, 10, 16)
        assert sat.weekday() == 5
        assert fri.weekday() == 4
        assert user.is_workday(sat) is True
        assert user.is_workday(fri) is False


def test_work_days_validation_and_normalization():
    # Valid
    val = validate_and_normalize_work_days(["5", "0", "2"])
    assert val == "0,2,5"

    val = validate_and_normalize_work_days("6, 1, 3")
    assert val == "1,3,6"

    # Empty / none selected
    with pytest.raises(ValueError, match="flash_work_days_required"):
        validate_and_normalize_work_days([])

    with pytest.raises(ValueError, match="flash_work_days_required"):
        validate_and_normalize_work_days("")

    with pytest.raises(ValueError, match="flash_work_days_required"):
        validate_and_normalize_work_days(None)

    # Invalid values
    with pytest.raises(ValueError, match="flash_work_days_invalid"):
        validate_and_normalize_work_days(["0", "7"])

    with pytest.raises(ValueError, match="flash_work_days_invalid"):
        validate_and_normalize_work_days(["abc"])


def test_admin_create_and_edit_employee_form_validation(client, app):
    admin = User.query.filter_by(role='admin').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    # 1. Try to create employee with no work_days
    res = client.post('/admin/employees/create', data={
        'name': 'No Days Employee',
        'password': 'password123',
        'zone_id': 1,
        'shift_setting_id': 1,
        'is_active': 'on',
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "No Days Employee" in res.get_data(as_text=True)
    # Ensure user was not created
    assert User.query.filter_by(name='No Days Employee').first() is None

    # 2. Try to create employee with invalid work_days
    res = client.post('/admin/employees/create', data={
        'name': 'Bad Days Employee',
        'password': 'password123',
        'zone_id': 1,
        'shift_setting_id': 1,
        'work_days': ['99'],
        'is_active': 'on',
    }, follow_redirects=True)
    assert res.status_code == 200
    assert User.query.filter_by(name='Bad Days Employee').first() is None

    # 3. Create employee with valid work_days (Sat, Sun, Mon = 5, 6, 0)
    res = client.post('/admin/employees/create', data={
        'name': 'Valid Days Employee',
        'password': 'password123',
        'zone_id': 1,
        'shift_setting_id': 1,
        'work_days': ['5', '6', '0'],
        'is_active': 'on',
    }, follow_redirects=True)
    assert res.status_code == 200
    created = User.query.filter_by(name='Valid Days Employee').first()
    assert created is not None
    assert created.work_days == "0,5,6"

    # 4. Edit employee with empty work_days -> should fail and preserve inputs
    res = client.post(f'/admin/employees/{created.id}/edit', data={
        'name': 'Valid Days Employee Edited',
        'zone_id': 1,
        'shift_setting_id': 1,
        'is_active': 'on',
    }, follow_redirects=True)
    assert res.status_code == 200
    # work_days should not have changed
    refreshed = db.session.get(User, created.id)
    assert refreshed.work_days == "0,5,6"

    # 5. Edit employee with new valid work_days
    res = client.post(f'/admin/employees/{created.id}/edit', data={
        'name': 'Valid Days Employee Edited',
        'zone_id': 1,
        'shift_setting_id': 1,
        'work_days': ['1', '2'],
        'is_active': 'on',
    }, follow_redirects=True)
    assert res.status_code == 200
    refreshed = db.session.get(User, created.id)
    assert refreshed.work_days == "1,2"
    assert refreshed.name == 'Valid Days Employee Edited'


def test_attendance_summary_normal_week(app):
    with app.app_context():
        zone = Zone.query.first()
        shift = ShiftSetting.query.first()
        # Employee works Mon-Thu (0, 1, 2, 3)
        user = create_user(
            name="Normal Week User",
            password="password123",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=shift.id,
            work_days="0,1,2,3",
        )
        user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        db.session.commit()

        # Consider past week: Monday 2026-05-04 to Sunday 2026-05-10
        # Expected days: 05-04 (Mon), 05-05 (Tue), 05-06 (Wed), 05-07 (Thu) => 4 expected
        # Friday 05-08, Saturday 05-09, Sunday 05-10 are days off
        start = date(2026, 5, 4)
        end = date(2026, 5, 10)

        # Attended on Monday (late) and Tuesday (on time)
        mon_dt = datetime(2026, 5, 4, 8, 30, tzinfo=timezone.utc)
        tue_dt = datetime(2026, 5, 5, 8, 0, tzinfo=timezone.utc)
        att_mon = Attendance(
            user_id=user.id, zone_id=zone.id, date=date(2026, 5, 4),
            sign_in_time=mon_dt, sign_out_time=mon_dt + timedelta(hours=8),
            is_late=True, late_minutes=15, total_hours=8.0, status='completed'
        )
        att_tue = Attendance(
            user_id=user.id, zone_id=zone.id, date=date(2026, 5, 5),
            sign_in_time=tue_dt, sign_out_time=tue_dt + timedelta(hours=7.5),
            is_late=False, late_minutes=0, total_hours=7.5, status='completed'
        )
        db.session.add_all([att_mon, att_tue])
        db.session.commit()

        summary = get_employee_attendance_summary(user, start, end)
        assert summary['expected_days'] == 4
        assert summary['attended_days'] == 2
        # Absent days should be Wednesday 05-06 and Thursday 05-07
        assert summary['absent_days'] == [date(2026, 5, 6), date(2026, 5, 7)]
        assert summary['extra_days'] == []
        assert len(summary['extra_days']) == 0
        assert summary['late_count'] == 1
        assert summary['total_hours'] == 15.5
        assert summary['attendance_rate'] == 50.0  # 2 / 4 * 100


def test_attendance_summary_joined_mid_range(app):
    with app.app_context():
        zone = Zone.query.first()
        shift = ShiftSetting.query.first()
        # Employee works Mon-Fri (0, 1, 2, 3, 4)
        user = create_user(
            name="Mid Range User",
            password="password123",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=shift.id,
            work_days="0,1,2,3,4",
        )
        # Joined on Wednesday 2026-05-06
        user.created_at = datetime(2026, 5, 6, 9, 0, tzinfo=timezone.utc)
        db.session.commit()

        # Query range from Monday 2026-05-04 to Sunday 2026-05-10
        start = date(2026, 5, 4)
        end = date(2026, 5, 10)

        # Expected range considered must start from 2026-05-06
        # Expected workdays: Wed 05-06, Thu 05-07, Fri 05-08 => 3 expected days
        summary = get_employee_attendance_summary(user, start, end)
        assert summary['expected_days'] == 3
        assert summary['attended_days'] == 0
        assert summary['absent_days'] == [date(2026, 5, 6), date(2026, 5, 7), date(2026, 5, 8)]
        assert summary['attendance_rate'] == 0.0


def test_attendance_summary_day_off_worked(app):
    with app.app_context():
        zone = Zone.query.first()
        shift = ShiftSetting.query.first()
        # Employee works Sun-Thu (6, 0, 1, 2, 3)
        user = create_user(
            name="Day Off Worker",
            password="password123",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=shift.id,
            work_days="6,0,1,2,3",
        )
        user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        db.session.commit()

        # Friday 2026-05-08 is a day off (weekday 4)
        # Saturday 2026-05-09 is a day off (weekday 5)
        # Sunday 2026-05-10 is a workday (weekday 6)
        start = date(2026, 5, 8)
        end = date(2026, 5, 10)

        # Employee attends on Friday (day off) and Sunday (workday)
        fri_dt = datetime(2026, 5, 8, 8, 0, tzinfo=timezone.utc)
        sun_dt = datetime(2026, 5, 10, 8, 0, tzinfo=timezone.utc)
        att_fri = Attendance(
            user_id=user.id, zone_id=zone.id, date=date(2026, 5, 8),
            sign_in_time=fri_dt, sign_out_time=fri_dt + timedelta(hours=6),
            total_hours=6.0, status='completed'
        )
        att_sun = Attendance(
            user_id=user.id, zone_id=zone.id, date=date(2026, 5, 10),
            sign_in_time=sun_dt, sign_out_time=sun_dt + timedelta(hours=8),
            total_hours=8.0, status='completed'
        )
        db.session.add_all([att_fri, att_sun])
        db.session.commit()

        summary = get_employee_attendance_summary(user, start, end)
        # Expected: only Sunday 05-10 => 1 expected
        assert summary['expected_days'] == 1
        # Attended total records in range = 2
        assert summary['attended_days'] == 2
        # Friday attendance was on non-workday => 1 extra day
        assert summary['extra_days'] == [date(2026, 5, 8)]
        assert len(summary['extra_days']) == 1
        # No workday was missed
        assert summary['absent_days'] == []
        assert summary['attendance_rate'] == 100.0


def test_attendance_summary_today_cutoff_and_shift_window(app):
    with app.app_context():
        zone = Zone.query.first()
        # Shift ending at 11:00
        shift = ShiftSetting(
            name="Morning Early Cutoff",
            shift_start_time=time(7, 0),
            sign_in_end_time=time(11, 0),
            grace_period_minutes=15,
            min_full_shift_hours=3.0,
        )
        db.session.add(shift)
        db.session.commit()

        cairo_now = datetime.now(timezone.utc).astimezone(CAIRO_TZ)
        cairo_today = cairo_now.date()
        today_wd = cairo_today.weekday()

        user = create_user(
            name="Today Cutoff User",
            password="password123",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=shift.id,
            work_days=str(today_wd),
        )
        user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        db.session.commit()

        # If cairo_now.time() <= shift.sign_in_end_time: today should NOT be in absent_days
        # If cairo_now.time() > shift.sign_in_end_time: today SHOULD be in absent_days
        summary = get_employee_attendance_summary(user, cairo_today, cairo_today)
        assert summary['expected_days'] == 1
        assert summary['attended_days'] == 0

        if cairo_now.time() > shift.sign_in_end_time:
            assert summary['absent_days'] == [cairo_today]
        else:
            assert summary['absent_days'] == []

        # Test fallback shift setting when user has no shift_setting_id
        user_no_shift = create_user(
            name="No Shift User",
            password="password123",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=None,
            work_days=str(today_wd),
        )
        user_no_shift.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        db.session.commit()

        # Fallback sign_in_end_time is time(18, 0)
        fallback_time = time(18, 0)
        summary_no_shift = get_employee_attendance_summary(user_no_shift, cairo_today, cairo_today)
        if cairo_now.time() > fallback_time:
            assert summary_no_shift['absent_days'] == [cairo_today]
        else:
            assert summary_no_shift['absent_days'] == []


def test_dashboard_kpis_pending_absent_extra_split(app):
    with app.app_context():
        # Clean users and attendance for clean KPI testing
        Attendance.query.delete()
        User.query.filter_by(role='employee').delete()
        ShiftSetting.query.delete()
        db.session.commit()

        zone = Zone.query.first()
        cairo_now = datetime.now(timezone.utc).astimezone(CAIRO_TZ)
        cairo_today = cairo_now.date()
        today_wd = cairo_today.weekday()
        off_wd = (today_wd + 1) % 7

        # 1. Past shift: sign_in_end_time was 1 hour ago
        past_end_time = (cairo_now - timedelta(hours=1)).time()
        past_shift = ShiftSetting(
            name="Past Shift",
            shift_start_time=time(6, 0),
            sign_in_end_time=past_end_time,
            grace_period_minutes=0,
            min_full_shift_hours=3.0,
        )

        # 2. Future shift: sign_in_end_time is 2 hours in the future
        future_end_time = (cairo_now + timedelta(hours=2)).time()
        future_shift = ShiftSetting(
            name="Future Shift",
            shift_start_time=time(12, 0),
            sign_in_end_time=future_end_time,
            grace_period_minutes=0,
            min_full_shift_hours=3.0,
        )
        db.session.add_all([past_shift, future_shift])
        db.session.commit()

        # Emp 1: Scheduled today, attended -> scheduled_present
        emp_scheduled_present = create_user(
            name="Scheduled Present", password="password123", role="employee",
            zone_id=zone.id, shift_setting_id=past_shift.id, work_days=str(today_wd)
        )
        # Emp 2: Scheduled today, past shift, did not attend -> absent
        emp_absent = create_user(
            name="Scheduled Absent", password="password123", role="employee",
            zone_id=zone.id, shift_setting_id=past_shift.id, work_days=str(today_wd)
        )
        # Emp 3: Scheduled today, future shift, did not attend yet -> pending
        emp_pending = create_user(
            name="Scheduled Pending", password="password123", role="employee",
            zone_id=zone.id, shift_setting_id=future_shift.id, work_days=str(today_wd)
        )
        # Emp 4: NOT scheduled today (day off), but attended -> extra_present
        emp_extra = create_user(
            name="Day Off Worker", password="password123", role="employee",
            zone_id=zone.id, shift_setting_id=past_shift.id, work_days=str(off_wd)
        )
        # Emp 5: Inactive employee scheduled today -> MUST NOT BE COUNTED
        emp_inactive = create_user(
            name="Inactive Emp", password="password123", role="employee",
            zone_id=zone.id, shift_setting_id=past_shift.id, work_days=str(today_wd)
        )
        emp_inactive.is_active = False

        # Add attendance for Emp 1 and Emp 4
        att_sched = Attendance(
            user_id=emp_scheduled_present.id, zone_id=zone.id, date=cairo_today,
            sign_in_time=cairo_now, status='active'
        )
        att_extra = Attendance(
            user_id=emp_extra.id, zone_id=zone.id, date=cairo_today,
            sign_in_time=cairo_now, status='active'
        )
        db.session.add_all([att_sched, att_extra])
        db.session.commit()

        kpis = get_dashboard_kpis(cairo_today)

        # Active employees scheduled today = Emp 1, Emp 2, Emp 3 = 3
        assert kpis['scheduled_total'] == 3
        assert kpis['scheduled_present_count'] == 1
        assert kpis['absent_count'] == 1
        assert kpis['pending_count'] == 1
        assert kpis['scheduled_present_count'] + kpis['absent_count'] + kpis['pending_count'] == kpis['scheduled_total']

        # Extra present count = Emp 4
        assert kpis['extra_present_count'] == 1
        # Total present = scheduled present + extra present
        assert kpis['present_count'] == 2
        # Total active employees = Emp 1, Emp 2, Emp 3, Emp 4 = 4
        assert kpis['total_employees'] == 4


def test_report_service_exports(client, app):
    with app.app_context():
        zone = Zone.query.first()
        shift = ShiftSetting.query.first()
        user = create_user(
            name="Export Test User",
            password="password123",
            role="employee",
            zone_id=zone.id,
            shift_setting_id=shift.id,
            work_days="0,1,2,3,4",
        )
        user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        att = Attendance(
            user_id=user.id,
            zone_id=zone.id,
            date=date(2026, 1, 5),
            sign_in_time=datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc),
            sign_out_time=datetime(2026, 1, 5, 16, 0, tzinfo=timezone.utc),
            total_hours=8.0,
            status='completed',
            shift_status='full_shift',
        )
        db.session.add(att)
        db.session.commit()

        # Direct test on export_csv
        csv_ar = export_csv([att], lang='ar', date_from=date(2026, 1, 1), date_to=date(2026, 1, 7))
        csv_ar_text = csv_ar.get_data(as_text=True)
        assert t('export_col_absent_days', lang='ar') in csv_ar_text
        assert t('export_col_extra_days', lang='ar') in csv_ar_text
        assert t('export_col_attendance_rate', lang='ar') in csv_ar_text

        csv_en = export_csv([att], lang='en', date_from=date(2026, 1, 1), date_to=date(2026, 1, 7))
        csv_en_text = csv_en.get_data(as_text=True)
        assert t('export_col_absent_days', lang='en') in csv_en_text
        assert t('export_col_extra_days', lang='en') in csv_en_text
        assert t('export_col_attendance_rate', lang='en') in csv_en_text

        # Direct test on export_excel
        excel_ar = export_excel([att], lang='ar', date_from=date(2026, 1, 1), date_to=date(2026, 1, 7))
        assert excel_ar.status_code == 200
        assert len(excel_ar.data) > 0

        excel_en = export_excel([att], lang='en', date_from=date(2026, 1, 1), date_to=date(2026, 1, 7))
        assert excel_en.status_code == 200
        assert len(excel_en.data) > 0
