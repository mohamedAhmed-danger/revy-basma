from datetime import date, datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from app.models import User, Zone, Attendance
from app.i18n import AR_WEEKDAYS, EN_WEEKDAYS_SHORT, get_current_lang, format_localized_date

CAIRO_TZ = ZoneInfo("Africa/Cairo")
DEFAULT_SIGN_IN_END_TIME = time(18, 0)


def format_arabic_date(d):
    return format_localized_date(d, 'ar')


def get_dashboard_kpis(target_date=None):
    """
    KPI + donut numbers for a given date (default today).
    Only counts active employees (is_active=True, role='employee').
    
    Returns:
    - total_employees: count of all active employees
    - scheduled_total: employees scheduled to work on target_date
    - scheduled_present_count: scheduled employees who attended
    - pending_count: scheduled employees not yet attended whose sign_in window has NOT closed
    - absent_count: scheduled employees not attended whose sign_in window HAS passed
    - extra_present_count: employees who attended on a day off (not part of scheduled_total)
    - present_count: total attendances (scheduled_present + extra_present)
    - full_shift_count, short_shift_count, in_progress_count
    
    Scheduled total = scheduled_present_count + absent_count + pending_count.
    """
    cairo_now = datetime.now(timezone.utc).astimezone(CAIRO_TZ)
    cairo_today = cairo_now.date()
    current_cairo_time = cairo_now.time()

    target_date = target_date or cairo_today

    active_employees = User.query.filter_by(role='employee', is_active=True).all()
    total_employees = len(active_employees)

    today_rows = Attendance.query.filter_by(date=target_date).all()
    user_att_map = {a.user_id: a for a in today_rows}

    scheduled_present_count = 0
    extra_present_count = 0
    absent_count = 0
    pending_count = 0
    scheduled_total = 0

    for emp in active_employees:
        if emp.created_at and emp.created_at.date() > target_date:
            continue

        is_workday = emp.is_workday(target_date)
        att = user_att_map.get(emp.id)

        if is_workday:
            scheduled_total += 1
            if att:
                scheduled_present_count += 1
            else:
                shift = emp.shift_setting
                sign_in_end = shift.sign_in_end_time if (shift and shift.sign_in_end_time) else DEFAULT_SIGN_IN_END_TIME
                if target_date == cairo_today:
                    if current_cairo_time > sign_in_end:
                        absent_count += 1
                    else:
                        pending_count += 1
                elif target_date < cairo_today:
                    absent_count += 1
                else:
                    pending_count += 1
        else:
            if att:
                extra_present_count += 1

    total_present = scheduled_present_count + extra_present_count

    active_emp_ids = {emp.id for emp in active_employees}
    active_rows = [a for a in today_rows if a.user_id in active_emp_ids]
    full_shift_count = sum(1 for a in active_rows if a.shift_status == 'full_shift')
    short_shift_count = sum(1 for a in active_rows if a.shift_status == 'short_shift')
    in_progress_count = sum(1 for a in active_rows if a.status == 'active')

    return {
        'total_employees': total_employees,
        'scheduled_total': scheduled_total,
        'present_count': total_present,
        'scheduled_present_count': scheduled_present_count,
        'extra_present_count': extra_present_count,
        'absent_count': absent_count,
        'pending_count': pending_count,
        'full_shift_count': full_shift_count,
        'short_shift_count': short_shift_count,
        'in_progress_count': in_progress_count,
    }


def get_zones_overview():
    return Zone.query.order_by(Zone.id).all()


def get_daily_report(target_date, zone_id=None, status=None, search=None):
    """Filtered attendance rows for the daily report table (date/zone/status/name)."""
    query = (
        Attendance.query
        .join(User, Attendance.user_id == User.id)
        .filter(Attendance.date == target_date)
    )

    if zone_id:
        query = query.filter(Attendance.zone_id == zone_id)

    if status == 'full_shift':
        query = query.filter(Attendance.shift_status == 'full_shift')
    elif status == 'short_shift':
        query = query.filter(Attendance.shift_status == 'short_shift')
    elif status == 'active':
        query = query.filter(Attendance.status == 'active')

    if search:
        query = query.filter(User.name.ilike(f'%{search.strip()}%'))

    return query.order_by(Attendance.sign_in_time.desc()).all()


def get_weekly_trend(target_date=None, lang=None):
    """Calculates weekly attendance trend (last 7 days) for dashboard chart with localized weekday names."""
    cairo_now = datetime.now(timezone.utc).astimezone(CAIRO_TZ)
    target_date = target_date or cairo_now.date()
    start_date = target_date - timedelta(days=6)
    
    if not lang:
        lang = get_current_lang()
    
    active_emp_ids = {emp.id for emp in User.query.filter_by(role='employee', is_active=True).all()}

    days_data = []
    curr = start_date
    while curr <= target_date:
        rows = [a for a in Attendance.query.filter_by(date=curr).all() if a.user_id in active_emp_ids]
        full_cnt = sum(1 for a in rows if a.shift_status == 'full_shift')
        short_cnt = sum(1 for a in rows if a.shift_status == 'short_shift')
        active_cnt = sum(1 for a in rows if a.status == 'active')
        
        weekday_label = EN_WEEKDAYS_SHORT[curr.weekday()] if lang == 'en' else AR_WEEKDAYS[curr.weekday()]
        
        days_data.append({
            'day_name': weekday_label,
            'date_str': curr.strftime('%d/%m'),
            'full_shift': full_cnt,
            'short_shift': short_cnt,
            'active': active_cnt
        })
        curr += timedelta(days=1)
        
    return days_data
