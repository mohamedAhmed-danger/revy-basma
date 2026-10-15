"""
attendance_service.py

Batch 6 created this file empty as a checkpoint. Batch 7 filled in sign_in().
Batch 8 adds sign_out() below.
"""

import math
from datetime import date, datetime, timezone, timedelta, time
from zoneinfo import ZoneInfo

from app.extensions import db
from app.models import Attendance
from app.services import geo_service

CAIRO_TZ = ZoneInfo("Africa/Cairo")
DEFAULT_SIGN_IN_END_TIME = time(18, 0)


def _now_utc():
    return datetime.now(timezone.utc)


def sign_in(user, latitude, longitude):
    """Create today's Attendance row for `user` after validating the sign-in window,
    the GPS zone check, and that they haven't already signed in today.

    Raises ValueError with a specific, user-facing message per failure case.
    Returns the created Attendance row on success.
    """
    if not user.zone_id or not user.shift_setting_id:
        raise ValueError('لازم يتحدد لك فرع وشفت الأول قبل ما تسجل حضور')

    zone = user.zone
    shift = user.shift_setting

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError('مقدرناش نقرأ إحداثيات موقعك، جرب تاني')

    # SEC-06: reject NaN / Inf that would silently pass the distance check
    if not (math.isfinite(latitude) and math.isfinite(longitude)):
        raise ValueError('إحداثيات الموقع غير صالحة، حاول تاني')

    # Basic range sanity: lat ∈ [-90, 90], lng ∈ [-180, 180], not (0, 0)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError('إحداثيات الموقع خارج النطاق المسموح به')
    if latitude == 0.0 and longitude == 0.0:
        raise ValueError('إحداثيات الموقع غير صالحة، حاول تاني')

    now_utc = _now_utc()

    # Business decision (sign-in window) is made on the server clock, converted
    # to Cairo local time for the comparison — never on client/browser time.
    now_cairo = now_utc.astimezone(CAIRO_TZ)
    now_cairo_time = now_cairo.time()
    today = now_cairo.date()

    if not (shift.shift_start_time <= now_cairo_time <= shift.sign_in_end_time):
        raise ValueError('برا وقت تسجيل الحضور المسموح بيه للشفت ده')

    inside, distance = geo_service.is_inside_zone(latitude, longitude, zone)
    if not inside:
        raise ValueError('انت برا نطاق الفرع، اقترب من المقر وحاول تاني')

    existing = Attendance.query.filter_by(user_id=user.id, date=today).first()
    if existing and (existing.status == 'active' or existing.sign_in_time is not None):
        raise ValueError('انت مسجل حضور بالفعل النهاردة')

    # Punctuality (is_late/late_minutes) vs. shift length (shift_status) are
    # tracked independently — this only computes punctuality; shift_status is
    # set later at sign-out (Batch 8).
    start_minutes = shift.shift_start_time.hour * 60 + shift.shift_start_time.minute
    now_minutes = now_cairo_time.hour * 60 + now_cairo_time.minute
    late_minutes = max(0, now_minutes - start_minutes - shift.grace_period_minutes)
    is_late = late_minutes > 0

    attendance = Attendance(
        user_id=user.id,
        zone_id=zone.id,
        date=today,
        sign_in_time=now_utc,
        sign_in_latitude=latitude,
        sign_in_longitude=longitude,
        sign_in_distance=distance,
        is_late=is_late,
        late_minutes=late_minutes,
        status='active',
    )
    db.session.add(attendance)
    db.session.commit()
    return attendance


def sign_out(user, latitude, longitude):
    """Close out today's active Attendance row for `user` after validating the
    GPS zone check (same rule as sign-in — no time-window check on sign-out,
    only on sign-in).

    Raises ValueError with a specific, user-facing message per failure case.
    Returns the updated Attendance row on success.
    """
    now_utc = _now_utc()
    today = now_utc.astimezone(CAIRO_TZ).date()

    attendance = Attendance.query.filter_by(
        user_id=user.id, date=today, status='active'
    ).first()
    if not attendance:
        raise ValueError('لسه ما سجلتش حضور النهاردة، مينفعش تسجل انصراف')

    zone = user.zone
    shift = user.shift_setting

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError('مقدرناش نقرأ إحداثيات موقعك، جرب تاني')

    # SEC-06: same validation as sign_in
    if not (math.isfinite(latitude) and math.isfinite(longitude)):
        raise ValueError('إحداثيات الموقع غير صالحة، حاول تاني')
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError('إحداثيات الموقع خارج النطاق المسموح به')
    if latitude == 0.0 and longitude == 0.0:
        raise ValueError('إحداثيات الموقع غير صالحة، حاول تاني')

    inside, distance = geo_service.is_inside_zone(latitude, longitude, zone)
    if not inside:
        raise ValueError('انت برا نطاق الفرع، اقترب من المقر وحاول تاني')

    now_utc = _now_utc()

    # SQLite drops tzinfo on stored DateTime columns — the value we get back
    # is still UTC, just naive, so re-attach tzinfo before doing arithmetic
    # (same normalization the cairo_time filter already does for display).
    sign_in_time = attendance.sign_in_time
    if sign_in_time.tzinfo is None:
        sign_in_time = sign_in_time.replace(tzinfo=timezone.utc)

    # total_hours is computed purely from server-side UTC timestamps —
    # never from client/browser time.
    total_hours = (now_utc - sign_in_time).total_seconds() / 3600.0

    # Punctuality (is_late/late_minutes, set at sign-in) and shift length
    # (shift_status, set here) are independent — a row can be "late" and
    # still "full_shift", that's expected and correct, not a bug.
    shift_status = 'full_shift' if total_hours >= shift.min_full_shift_hours else 'short_shift'

    attendance.sign_out_time = now_utc
    attendance.sign_out_latitude = latitude
    attendance.sign_out_longitude = longitude
    attendance.sign_out_distance = distance
    attendance.total_hours = total_hours
    attendance.shift_status = shift_status
    attendance.status = 'completed'

    db.session.commit()
    return attendance


def get_dashboard_context(user, today_attendance, live_lat=None, live_lng=None):
    """Batch 9 — everything the employee dashboard template needs, computed
    here in Python (not in Jinja).

    live_lat/live_lng are optional: when present (passed from the page's
    on-load GPS refresh, a plain GET form — see dashboard.html), a fresh
    is_inside_zone check is run so the status card can show the employee's
    *current* zone status, not just their state at sign-in/out time.
    """
    zone = user.zone
    shift = user.shift_setting

    live_status = None
    if live_lat is not None and live_lng is not None and zone is not None:
        try:
            inside, distance = geo_service.is_inside_zone(float(live_lat), float(live_lng), zone)
            live_status = {'inside': inside, 'distance': distance}
        except (TypeError, ValueError):
            live_status = None

    # Shift progress: elapsed hours (server clock, not client) vs. the shift's
    # min_full_shift_hours target — independent of is_late/shift_status, this
    # is purely a "how far into today's shift am I" display value.
    elapsed_hours = 0.0
    if today_attendance and shift:
        if today_attendance.status == 'completed' and today_attendance.total_hours is not None:
            elapsed_hours = today_attendance.total_hours
        elif today_attendance.status == 'active' and today_attendance.sign_in_time is not None:
            sign_in_time = today_attendance.sign_in_time
            if sign_in_time.tzinfo is None:
                sign_in_time = sign_in_time.replace(tzinfo=timezone.utc)
            elapsed_hours = (_now_utc() - sign_in_time).total_seconds() / 3600.0

    required_hours = shift.min_full_shift_hours if shift else None
    if required_hours and required_hours > 0:
        shift_progress_percent = max(0, min(100, round((elapsed_hours / required_hours) * 100)))
    else:
        shift_progress_percent = 0

    now_cairo_time = _now_utc().astimezone(CAIRO_TZ).time()
    window_status = None
    if shift:
        start_m = shift.shift_start_time.hour * 60 + shift.shift_start_time.minute
        grace_m = start_m + shift.grace_period_minutes
        end_m = shift.sign_in_end_time.hour * 60 + shift.sign_in_end_time.minute
        now_m = now_cairo_time.hour * 60 + now_cairo_time.minute

        if now_m < start_m:
            window_status = 'early'
        elif start_m <= now_m <= grace_m:
            window_status = 'on_time'
        elif grace_m < now_m <= end_m:
            window_status = 'late'
        else:
            window_status = 'expired'

    return {
        'zone': zone,
        'shift': shift,
        'live_status': live_status,
        'elapsed_hours': elapsed_hours,
        'required_hours': required_hours,
        'shift_progress_percent': shift_progress_percent,
        'window_status': window_status,
        'webauthn_credentials': user.webauthn_credentials,
    }


def get_history(user, limit=30):
    """Batch 15 — past attendance rows for the employee history page
    (/employee/attendance), most recent first. Only rows that have at least
    a sign-in are relevant here (there shouldn't be any without one, but stay
    defensive).
    """
    return (
        Attendance.query
        .filter(Attendance.user_id == user.id, Attendance.sign_in_time.isnot(None))
        .order_by(Attendance.date.desc())
        .limit(limit)
        .all()
    )


def get_employee_attendance_summary(user, start, end):
    """
    Calculates comprehensive attendance summary for `user` across [start, end].

    Rules:
    - Count only dates from max(start, user.created_at.date()) to min(end, cairo_today).
    - Expected days = dates in that range where user.is_workday(date).
    - Do not mark TODAY as absent until the employee's shift sign_in_end_time has passed.
    - Uses the employee's own shift_setting, falling back to DEFAULT_SIGN_IN_END_TIME (18:00).
    - Attended = an Attendance row exists for that user and date.
    
    Returns a dict with:
      expected_days: int
      attended_days: int
      attended_expected_days: int
      absent_days: list of dates
      extra_days: list of dates (attended on non-working day)
      late_count: int
      total_hours: float
      attendance_rate: float (percentage)
      pending_today: bool
    """
    cairo_now = _now_utc().astimezone(CAIRO_TZ)
    cairo_today = cairo_now.date()
    current_cairo_time = cairo_now.time()

    user_join_date = user.created_at.date() if user.created_at else start
    effective_start = max(start, user_join_date)
    effective_end = min(end, cairo_today)

    if effective_start > effective_end:
        return {
            'expected_days': 0,
            'attended_days': 0,
            'attended_expected_days': 0,
            'absent_days': [],
            'extra_days': [],
            'late_count': 0,
            'total_hours': 0.0,
            'attendance_rate': 100.0,
            'pending_today': False,
        }

    attendances = Attendance.query.filter(
        Attendance.user_id == user.id,
        Attendance.date >= effective_start,
        Attendance.date <= effective_end
    ).all()

    attendance_by_date = {att.date: att for att in attendances}

    expected_dates = []
    absent_days = []
    extra_days = []
    attended_on_expected = []
    late_count = 0
    total_hours = 0.0
    pending_today = False

    shift = user.shift_setting
    sign_in_end = shift.sign_in_end_time if (shift and shift.sign_in_end_time) else DEFAULT_SIGN_IN_END_TIME

    curr = effective_start
    while curr <= effective_end:
        is_workday = user.is_workday(curr)
        att = attendance_by_date.get(curr)

        if is_workday:
            expected_dates.append(curr)
            if att:
                attended_on_expected.append(curr)
            else:
                if curr == cairo_today:
                    if current_cairo_time > sign_in_end:
                        absent_days.append(curr)
                    else:
                        pending_today = True
                else:
                    absent_days.append(curr)
        else:
            if att:
                extra_days.append(curr)

        curr += timedelta(days=1)

    for att in attendances:
        if att.is_late:
            late_count += 1
        if att.total_hours is not None:
            total_hours += att.total_hours

    expected_count = len(expected_dates)
    attended_count = len(attendances)

    evaluated_expected = expected_count - (1 if pending_today else 0)
    if evaluated_expected > 0:
        attendance_rate = round((len(attended_on_expected) / evaluated_expected) * 100.0, 1)
    else:
        attendance_rate = 100.0

    return {
        'expected_days': expected_count,
        'attended_days': attended_count,
        'attended_expected_days': len(attended_on_expected),
        'absent_days': absent_days,
        'extra_days': extra_days,
        'late_count': late_count,
        'total_hours': round(total_hours, 1),
        'attendance_rate': attendance_rate,
        'pending_today': pending_today,
    }


def admin_close_attendance(attendance_id):
    """SEC-09: Close an unclosed/active Attendance row on behalf of an employee who
    forgot to sign out. Computes work hours and shift_status from server clock time.
    """
    attendance = Attendance.query.get(attendance_id)
    if not attendance:
        raise ValueError('سجل الحضور غير موجود')

    if attendance.status != 'active':
        raise ValueError('سجل الحضور مغلق بالفعل')

    now_utc = _now_utc()
    sign_in_time = attendance.sign_in_time
    if sign_in_time:
        if sign_in_time.tzinfo is None:
            sign_in_time = sign_in_time.replace(tzinfo=timezone.utc)
        total_seconds = max(0.0, (now_utc - sign_in_time).total_seconds())
        total_hours = total_seconds / 3600.0
    else:
        total_hours = 0.0

    user = attendance.user
    shift = user.shift_setting if user else None
    min_hours = shift.min_full_shift_hours if shift else 3.0
    shift_status = 'full_shift' if total_hours >= min_hours else 'short_shift'

    attendance.sign_out_time = now_utc
    attendance.total_hours = round(total_hours, 2)
    attendance.shift_status = shift_status
    attendance.status = 'completed'

    db.session.commit()
    return attendance

