from datetime import date, timedelta
from app.models import User, Zone, Attendance
from app.i18n import AR_WEEKDAYS, EN_WEEKDAYS_SHORT, get_current_lang, format_localized_date


def format_arabic_date(d):
    return format_localized_date(d, 'ar')


def get_dashboard_kpis(target_date=None):
    """KPI + donut numbers for 'today' (or a given date). Read-only, no mutation."""
    target_date = target_date or date.today()

    total_employees = User.query.filter_by(role='employee').count()
    today_rows = Attendance.query.filter_by(date=target_date).all()

    full_shift_count = sum(1 for a in today_rows if a.shift_status == 'full_shift')
    short_shift_count = sum(1 for a in today_rows if a.shift_status == 'short_shift')
    in_progress_count = sum(1 for a in today_rows if a.status == 'active')
    present_count = len(today_rows)
    absent_count = max(total_employees - present_count, 0)

    return {
        'total_employees': total_employees,
        'present_count': present_count,
        'full_shift_count': full_shift_count,
        'short_shift_count': short_shift_count,
        'in_progress_count': in_progress_count,
        'absent_count': absent_count,
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
    target_date = target_date or date.today()
    start_date = target_date - timedelta(days=6)
    
    if not lang:
        lang = get_current_lang()
    
    days_data = []
    curr = start_date
    while curr <= target_date:
        rows = Attendance.query.filter_by(date=curr).all()
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
