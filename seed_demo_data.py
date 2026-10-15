# seed_demo_data.py
#
# NOT part of Batch 10 itself — Batches 4 (Shift Settings CRUD), 7 (Sign-In) and
# 8 (Sign-Out) are what would normally create ShiftSetting rows and Attendance
# rows through the UI. Since those batches aren't built yet, this script writes
# directly to the models (like seed.py already does for users) so the Batch 10
# admin dashboard has real rows to query and display instead of all zeros.
#
# Safe to re-run: it wipes and re-creates zones/shifts/employees/attendance only
# (never touches the admin user).

import random
from datetime import date, datetime, time, timedelta, timezone

from zoneinfo import ZoneInfo
from app import create_app
from app.extensions import db
from app.models import User, Zone, ShiftSetting, Attendance
from app.services.auth_service import create_user
from app.services.zone_service import create_zone

app = create_app()

EMPLOYEE_NAMES = [
    "أحمد محمد", "محمد السيد", "سارة خالد", "علي محمود", "منى حسن",
    "كريم عادل", "هدى إبراهيم", "يوسف طارق", "نورا فتحي", "مصطفى جمال",
    "ريم صلاح", "عمر رشدي", "داليا فؤاد", "حسام الدين", "ياسمين عمر",
]

CAIRO_TZ = ZoneInfo("Africa/Cairo")

with app.app_context():
    # wipe demo data only (keep the admin user)
    Attendance.query.delete()
    User.query.filter_by(role='employee').delete()
    ShiftSetting.query.delete()
    Zone.query.delete()
    db.session.commit()

    zones = [
        create_zone("فرع القاهرة", 30.0444, 31.2357, 50),
        create_zone("فرع الإسكندرية", 31.2001, 29.9187, 75),
        create_zone("فرع الجيزة", 30.0131, 31.2089, 60),
    ]

    morning = ShiftSetting(
        name="صباحي", shift_start_time=time(8, 0), sign_in_end_time=time(10, 0),
        grace_period_minutes=15, min_full_shift_hours=3.0,
    )
    evening = ShiftSetting(
        name="مسائي", shift_start_time=time(16, 0), sign_in_end_time=time(18, 0),
        grace_period_minutes=10, min_full_shift_hours=3.0,
    )
    db.session.add_all([morning, evening])
    db.session.commit()
    shifts = [morning, evening]

    today = datetime.now(timezone.utc).astimezone(CAIRO_TZ).date()
    today_weekday = today.weekday()
    # pick an off-day for testing day-off work (if today is 5, off is 4, etc.)
    off_weekday = (today_weekday + 1) % 7

    employees = []
    for i, name in enumerate(EMPLOYEE_NAMES):
        zone = random.choice(zones)
        shift = random.choice(shifts)
        # Give some employees custom working days
        if i == 0:
            # Employee with a day-off today (only works other days)
            days = [d for d in range(7) if d != today_weekday]
            work_days_str = ",".join(str(d) for d in sorted(days))
        elif i == 1:
            # Employee off on off_weekday
            days = [d for d in range(7) if d != off_weekday]
            work_days_str = ",".join(str(d) for d in sorted(days))
        elif i % 4 == 0:
            # Sun-Thu
            work_days_str = "6,0,1,2,3"
        else:
            # Sat-Thu (default)
            work_days_str = "5,6,0,1,2,3"

        emp = create_user(
            name=name, password="123456", role="employee",
            zone_id=zone.id, shift_setting_id=shift.id,
            work_days=work_days_str,
        )
        employees.append(emp)

    now = datetime.now(timezone.utc)

    # Generate attendance:
    # 1. First employee has day off today, but attended today (extra day worked)
    extra_emp = employees[0]
    extra_zone = Zone.query.get(extra_emp.zone_id)
    extra_sign_in = now.replace(hour=8, minute=10, second=0, microsecond=0)
    extra_hours = 6.0
    extra_sign_out = extra_sign_in + timedelta(hours=extra_hours)
    db.session.add(Attendance(
        user_id=extra_emp.id, zone_id=extra_zone.id, date=today,
        sign_in_time=extra_sign_in, sign_out_time=extra_sign_out,
        sign_in_latitude=extra_zone.latitude, sign_in_longitude=extra_zone.longitude,
        sign_in_distance=15.0,
        sign_out_latitude=extra_zone.latitude, sign_out_longitude=extra_zone.longitude,
        sign_out_distance=18.0,
        total_hours=extra_hours, is_late=False, late_minutes=0,
        status='completed', shift_status='full_shift',
    ))

    # For remaining employees, create attendance based on whether today is their workday
    scheduled_employees = [e for e in employees[1:] if e.is_workday(today)]
    outcomes = (["full_shift"] * 8) + (["short_shift"] * 3) + (["absent"] * 4)
    random.shuffle(outcomes)

    for emp, outcome in zip(scheduled_employees, outcomes):
        if outcome == "absent":
            continue

        zone = Zone.query.get(emp.zone_id)
        sign_in = now.replace(hour=8, minute=random.randint(0, 25), second=0, microsecond=0)
        is_late = sign_in.time() > time(8, 15)
        late_minutes = max(0, (sign_in.hour * 60 + sign_in.minute) - (8 * 60 + 15)) if is_late else 0

        hours = round(random.uniform(3.2, 8.5), 1) if outcome == "full_shift" else round(random.uniform(1.0, 2.8), 1)
        sign_out = sign_in + timedelta(hours=hours)

        db.session.add(Attendance(
            user_id=emp.id, zone_id=zone.id, date=today,
            sign_in_time=sign_in, sign_out_time=sign_out,
            sign_in_latitude=zone.latitude, sign_in_longitude=zone.longitude, sign_in_distance=round(random.uniform(2, 45), 1),
            sign_out_latitude=zone.latitude, sign_out_longitude=zone.longitude, sign_out_distance=round(random.uniform(2, 45), 1),
            total_hours=hours, is_late=is_late, late_minutes=late_minutes,
            status='completed', shift_status=outcome,
        ))

    db.session.commit()
    print(f"تم إنشاء {len(zones)} فروع، {len(shifts)} شفتات، {len(employees)} موظف، وبيانات حضور تجريبية لليوم (تشمل أيام العمل والإضافي).")
