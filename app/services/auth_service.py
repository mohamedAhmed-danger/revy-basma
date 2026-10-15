from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.services.validators import validate_username, validate_password
from app.models import User


def authenticate_user(username, password):

    if not username or not password:
        return None

    user = User.query.filter_by(name=username.strip()).first()

    if user and user.is_active and check_password_hash(user.password_hash, password):
        return user

    return None


def validate_and_normalize_work_days(work_days):
    if work_days is None:
        raise ValueError('flash_work_days_required')
    if isinstance(work_days, str):
        raw_items = [x.strip() for x in work_days.split(',') if x.strip() != '']
    elif isinstance(work_days, (list, tuple, set)):
        raw_items = [str(x).strip() for x in work_days if str(x).strip() != '']
    else:
        raise ValueError('flash_work_days_invalid')

    if not raw_items:
        raise ValueError('flash_work_days_required')

    parsed = []
    for item in raw_items:
        try:
            val = int(item)
        except (ValueError, TypeError):
            raise ValueError('flash_work_days_invalid')
        if val < 0 or val > 6:
            raise ValueError('flash_work_days_invalid')
        parsed.append(val)

    if not parsed:
        raise ValueError('flash_work_days_required')

    return ','.join(str(d) for d in sorted(set(parsed)))


def create_user(name, password, role='employee', zone_id=None, shift_setting_id=None, work_days=None):

    name = validate_username(name)
    validate_password(password)

    if User.query.filter_by(name=name).first():
        raise ValueError('اسم المستخدم ده مستخدم بالفعل')

    if work_days is not None:
        normalized_work_days = validate_and_normalize_work_days(work_days)
    else:
        normalized_work_days = '5,6,0,1,2,3'

    user = User(
        name=name,
        password_hash=generate_password_hash(password),
        role=role,
        zone_id=zone_id,
        shift_setting_id=shift_setting_id,
        work_days=normalized_work_days,
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user_id, name=None, password=None, zone_id=None, shift_setting_id=None, is_active=True, work_days=None):
    user = User.query.get_or_404(user_id)
    if name and name.strip():
        name = validate_username(name)
        existing = User.query.filter_by(name=name).first()
        if existing and existing.id != user_id:
            raise ValueError('اسم المستخدم ده مستخدم بالفعل')
        user.name = name

    if password and password.strip():
        validate_password(password)
        user.password_hash = generate_password_hash(password)

    user.zone_id = int(zone_id) if zone_id else None
    user.shift_setting_id = int(shift_setting_id) if shift_setting_id else None
    user.is_active = bool(is_active)

    if work_days is not None:
        user.work_days = validate_and_normalize_work_days(work_days)

    db.session.commit()
    return user


def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        raise ValueError('لا يمكن حذف مدير النظام')
    db.session.delete(user)
    db.session.commit()