"""
Revy Basma - Internationalization (i18n) Module
Provides Arabic and English translations for all UI components, badges, forms, and messages.
"""

from flask import session, request
from datetime import date

AR_WEEKDAYS = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
AR_WEEKDAYS_SHORT = ['إثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت', 'أحد']
AR_MONTHS = [
    'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر',
]

EN_WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
EN_WEEKDAYS_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
EN_MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

# Weekday checkboxes and listings ordered Sat, Sun, Mon, Tue, Wed, Thu, Fri (5, 6, 0, 1, 2, 3, 4)
WEEKDAY_OPTIONS = [
    {'day': 5, 'name_key': 'weekday_sat', 'short_key': 'weekday_sat_short'},
    {'day': 6, 'name_key': 'weekday_sun', 'short_key': 'weekday_sun_short'},
    {'day': 0, 'name_key': 'weekday_mon', 'short_key': 'weekday_mon_short'},
    {'day': 1, 'name_key': 'weekday_tue', 'short_key': 'weekday_tue_short'},
    {'day': 2, 'name_key': 'weekday_wed', 'short_key': 'weekday_wed_short'},
    {'day': 3, 'name_key': 'weekday_thu', 'short_key': 'weekday_thu_short'},
    {'day': 4, 'name_key': 'weekday_fri', 'short_key': 'weekday_fri_short'},
]

TRANSLATIONS = {
    # Brand & Global
    "brand_name": {
        "ar": "ريفي بصمة",
        "en": "Revy Basma"
    },
    "brand_tagline": {
        "ar": "نظام الحضور والانصراف الذكي",
        "en": "Smart Biometric & Geo Attendance"
    },
    "dev_by": {
        "ar": "تطوير",
        "en": "Developed by"
    },
    "copyright": {
        "ar": "2026 © جميع الحقوق محفوظة لـ",
        "en": "2026 © All rights reserved to"
    },
    
    # Common UI
    "save": {"ar": "حفظ التعديلات", "en": "Save Changes"},
    "cancel": {"ar": "إلغاء", "en": "Cancel"},
    "delete": {"ar": "حذف", "en": "Delete"},
    "edit": {"ar": "تعديل", "en": "Edit"},
    "add": {"ar": "إضافة", "en": "Add"},
    "create": {"ar": "إنشاء", "en": "Create"},
    "back": {"ar": "رجوع", "en": "Back"},
    "filter": {"ar": "تصفية", "en": "Filter"},
    "reset": {"ar": "إعادة تعيين", "en": "Reset"},
    "search": {"ar": "بحث", "en": "Search"},
    "search_placeholder": {"ar": "ابحث عن موظف بالاسم...", "en": "Search employee by name..."},
    "actions": {"ar": "الإجراءات", "en": "Actions"},
    "status": {"ar": "الحالة", "en": "Status"},
    "all": {"ar": "الكل", "en": "All"},
    "menu": {"ar": "القائمة", "en": "Menu"},
    "hours": {"ar": "ساعة", "en": "hrs"},
    "minutes": {"ar": "دقيقة", "en": "min"},
    "unassigned": {"ar": "غير مخصص", "en": "Unassigned"},
    "no_device": {"ar": "لا يوجد جهاز", "en": "No Device"},
    "devices_registered": {"ar": "جهاز مسجل", "en": "Device(s)"},
    "device_name_label": {"ar": "اسم الجهاز", "en": "Device Name"},
    "device_name_optional": {"ar": "اختياري", "en": "Optional"},
    # Employee list page
    "add_employee": {"ar": "+ إضافة موظف جديد", "en": "+ Add Employee"},
    "employees_sub": {"ar": "عرض وإضافة وتعديل بيانات الموظفين وإدارة الأجهزة المسجلة", "en": "View, add, and manage employee accounts and registered biometric devices"},
    "emp_suspended": {"ar": "موقف", "en": "Suspended"},
    "reset_device": {"ar": "إعادة ضبط البصمة", "en": "Reset Biometric"},
    "working_days": {"ar": "أيام العمل", "en": "Working Days"},
    "working_days_help": {"ar": "تعديل أيام عمل الموظف ينطبق أيضاً على تقارير الفترات السابقة.", "en": "Changing an employee's work days also applies to past reports."},
    "weekday_sat": {"ar": "السبت", "en": "Saturday"},
    "weekday_sun": {"ar": "الأحد", "en": "Sunday"},
    "weekday_mon": {"ar": "الإثنين", "en": "Monday"},
    "weekday_tue": {"ar": "الثلاثاء", "en": "Tuesday"},
    "weekday_wed": {"ar": "الأربعاء", "en": "Wednesday"},
    "weekday_thu": {"ar": "الخميس", "en": "Thursday"},
    "weekday_fri": {"ar": "الجمعة", "en": "Friday"},
    "weekday_sat_short": {"ar": "سبت", "en": "Sat"},
    "weekday_sun_short": {"ar": "أحد", "en": "Sun"},
    "weekday_mon_short": {"ar": "إثنين", "en": "Mon"},
    "weekday_tue_short": {"ar": "ثلاثاء", "en": "Tue"},
    "weekday_wed_short": {"ar": "أربعاء", "en": "Wed"},
    "weekday_thu_short": {"ar": "خميس", "en": "Thu"},
    "weekday_fri_short": {"ar": "جمعة", "en": "Fri"},
    # Confirm dialog strings
    "confirm_delete_employee": {"ar": "تأكيد حذف الموظف", "en": "Confirm deleting employee"},
    "confirm_reset_devices": {"ar": "تأكيد إعادة ضبط وحذف الأجهزة المسجلة للموظف", "en": "Confirm resetting registered devices for employee"},
    "confirm_delete_shift": {"ar": "تأكيد حذف الشفت؟", "en": "Confirm deleting this shift?"},
    "confirm_close_attendance": {"ar": "هل أنت متأكد من رغبتك في إغلاق سجل الحضور هذا يدوياً؟", "en": "Are you sure you want to manually close this attendance record?"},
    "btn_close_attendance": {"ar": "إغلاق الانصراف", "en": "Close Attendance"},
    # Shift page
    "add_shift": {"ar": "+ إضافة شفت جديد", "en": "+ Add Shift"},
    "shifts_sub": {"ar": "إدارة جداول وأوقات الشفتات المختلفة للموظفين", "en": "Manage employee shift schedules and sign-in windows"},
    "no_shifts_title": {"ar": "لا توجد شفتات مضافة", "en": "No Shifts Found"},
    "no_shifts_hint": {"ar": "اضغط على \"+ إضافة شفت جديد\" لتعريف جداول الدوام.", "en": "Click \"+ Add Shift\" to define attendance schedules."},
    # Employees empty state
    "no_employees_title": {"ar": "لا يوجد موظفون مسجلون", "en": "No Employees Found"},
    "no_employees_hint": {"ar": "اضغط على \"+ إضافة موظف جديد\" لإضافة أول حساب موظف للنظام.", "en": "Click \"+ Add Employee\" to create the first employee account."},
    # HTTPS warning
    "https_warning_title": {"ar": "تحذير: الاتصال غير آمن", "en": "Warning: Insecure Connection"},
    "https_warning_text": {"ar": "تسجيل الحضور والبصمة الحيوية يتطلبان اتصال HTTPS آمن. يرجى التواصل مع المدير لتفعيل HTTPS.", "en": "Biometric check-in and GPS attendance require a secure HTTPS connection. Please contact your administrator."},
    # Settings
    "settings_save_notice": {"ar": "الإعدادات للعرض فقط في هذا الإصدار. تواصل مع المطور لتفعيل الحفظ.", "en": "Settings display is read-only in this version. Contact the developer to enable persistence."},

    "date": {"ar": "التاريخ", "en": "Date"},
    "time": {"ar": "الوقت", "en": "Time"},
    "today": {"ar": "اليوم", "en": "Today"},
    "from_date": {"ar": "من تاريخ", "en": "From Date"},
    "to_date": {"ar": "إلى تاريخ", "en": "To Date"},
    "view_all": {"ar": "عرض الكل", "en": "View All"},
    "loading": {"ar": "جاري التحميل...", "en": "Loading..."},
    "close": {"ar": "إغلاق", "en": "Close"},
    "confirm": {"ar": "تأكيد", "en": "Confirm"},
    "warning": {"ar": "تنبيه", "en": "Warning"},
    "error": {"ar": "خطأ", "en": "Error"},
    "success": {"ar": "نجاح", "en": "Success"},
    "no_data": {"ar": "لا توجد بيانات متاحة حالياً.", "en": "No data available at this time."},
    "no_records_title": {"ar": "لا توجد سجلات", "en": "No Records Found"},
    "no_records_hint": {"ar": "لم يتم العثور على أي بيانات مطابقة للشروط المحددة.", "en": "No data matches your specified criteria."},
    "no_chart_data": {"ar": "لا توجد بيانات حضور مسجلة لهذا الأسبوع.", "en": "No attendance records available for this week."},

    # Auth & Login
    "login_title": {"ar": "تسجيل الدخول", "en": "Sign In"},
    "login_sub": {"ar": "تسجيل الدخول إلى حسابك بنظام ريفي بصمة", "en": "Sign in to your Revy Basma account"},
    "username": {"ar": "اسم المستخدم", "en": "Username"},
    "username_placeholder": {"ar": "أدخل اسم المستخدم", "en": "Enter username"},
    "password": {"ar": "كلمة المرور", "en": "Password"},
    "password_placeholder": {"ar": "أدخل كلمة المرور", "en": "Enter password"},
    "sign_in_btn": {"ar": "تسجيل الدخول", "en": "Sign In"},
    "logout": {"ar": "تسجيل الخروج", "en": "Sign Out"},

    # Admin Navigation
    "admin_panel": {"ar": "لوحة الإدارة", "en": "Admin Panel"},
    "sys_admin": {"ar": "مدير النظام", "en": "System Admin"},
    "nav_dashboard": {"ar": "الرئيسية", "en": "Dashboard"},
    "nav_employees": {"ar": "الموظفين", "en": "Employees"},
    "nav_zones": {"ar": "المقرات (Zones)", "en": "Work Zones"},
    "nav_shifts": {"ar": "إعدادات الشفت", "en": "Shift Settings"},
    "nav_reports": {"ar": "التقارير", "en": "Reports"},
    "nav_settings": {"ar": "الإعدادات", "en": "Settings"},
    "notifications": {"ar": "الإشعارات", "en": "Notifications"},

    # Admin Dashboard KPIs & Charts
    "dash_title": {"ar": "لوحة التحكم الرئيسية", "en": "Executive Dashboard"},
    "dash_sub": {"ar": "نظرة عامة على أداء الحضور اليومي للموظفين المقيدين بالنظام", "en": "Real-time overview of daily employee attendance and biometric logs"},
    "kpi_total_employees": {"ar": "إجمالي الموظفين", "en": "Total Employees"},
    "kpi_present_now": {"ar": "الحاضرون الآن", "en": "Present Now"},
    "kpi_absent_today": {"ar": "الغائبون اليوم", "en": "Absent Today"},
    "kpi_full_shift": {"ar": "شفت كامل", "en": "Full Shift"},
    "kpi_short_shift": {"ar": "شفت غير كامل", "en": "Short Shift"},
    "kpi_of_total": {"ar": "من الإجمالي", "en": "of total"},
    "kpi_of_present": {"ar": "من الحاضرين", "en": "of present"},
    "chart_shift_distribution": {"ar": "توزيع حالات الشفت اليوم", "en": "Today's Shift Distribution"},
    "chart_weekly_trend": {"ar": "أداء الحضور خلال الأسبوع", "en": "Weekly Attendance Trend"},
    "chart_total_attendance": {"ar": "إجمالي الحضور", "en": "Total Attendance"},
    "today_attendance": {"ar": "حضور اليوم", "en": "Today's Attendance"},
    "all_zones": {"ar": "كل الفروع والمقرات", "en": "All Work Zones"},
    "all_shifts": {"ar": "كل الشفتات", "en": "All Shifts"},
    "all_statuses": {"ar": "جميع الحالات", "en": "All Statuses"},
    "in_progress": {"ar": "قيد التسجيل", "en": "In Progress"},
    "absent": {"ar": "غائب", "en": "Absent"},
    "kpi_scheduled_today": {"ar": "مجدولون اليوم", "en": "Scheduled Today"},
    "kpi_pending_today": {"ar": "بانتظار الحضور اليوم", "en": "Pending Today"},
    "kpi_extra_today": {"ar": "حاضرون في عطلة", "en": "Day-off Present"},
    "scheduled_today": {"ar": "مجدولون اليوم", "en": "Scheduled Today"},
    "pending": {"ar": "بانتظار الحضور", "en": "Pending"},
    "extra_present": {"ar": "حضور عطلة", "en": "Extra (Day Off)"},

    # Table Headers
    "col_num": {"ar": "#", "en": "#"},
    "col_employee": {"ar": "اسم الموظف", "en": "Employee Name"},
    "col_zone": {"ar": "المقر / الفرع", "en": "Work Zone"},
    "col_sign_in": {"ar": "وقت الحضور", "en": "Check In"},
    "col_sign_out": {"ar": "وقت الانصراف", "en": "Check Out"},
    "col_total_hours": {"ar": "إجمالي الساعات", "en": "Total Hours"},
    "col_late": {"ar": "التأخير", "en": "Delay"},
    "col_status": {"ar": "الحالة", "en": "Status"},
    "col_national_id": {"ar": "الرقم القومي / المعرف", "en": "National ID / Code"},
    "col_shift": {"ar": "الشفت المخصص", "en": "Assigned Shift"},
    "col_devices": {"ar": "الأجهزة المسجلة", "en": "Registered Devices"},
    "col_role": {"ar": "الدور", "en": "Role"},
    "col_active": {"ar": "الحساب نشط", "en": "Active Account"},
    "col_coordinates": {"ar": "الإحداثيات", "en": "Coordinates"},
    "col_radius": {"ar": "نطاق السماح (متر)", "en": "Radius (Meters)"},
    "col_start_time": {"ar": "بداية الشفت", "en": "Shift Start"},
    "col_sign_in_end": {"ar": "نهاية نافذة الحضور", "en": "Sign-In Window End"},
    "col_grace_period": {"ar": "فترة السماح", "en": "Grace Period"},
    "col_min_hours": {"ar": "ساعات الشفت الكامل", "en": "Min Full Shift Hours"},
    "zones_sub": {"ar": "إضافة وتعديل فروع ومواقع الشركة وتحديد نطاق الـ Geofencing", "en": "Manage company branches, locations, and geofence radiuses"},
    "add_zone": {"ar": "إضافة مقر جديد", "en": "Add Work Zone"},
    "zones_list": {"ar": "قائمة المقرات", "en": "Work Zones List"},
    "zone_name": {"ar": "اسم المقر", "en": "Zone Name"},
    "zone_map_title": {"ar": "موقع المقر على الخريطة", "en": "Zone Map Location"},
    "zone_details_title": {"ar": "تفاصيل المقر المحدد", "en": "Selected Zone Details"},
    "name": {"ar": "الاسم", "en": "Name"},
    "edit_zone_btn": {"ar": "تعديل البيانات", "en": "Edit Details"},
    "select_zone_hint": {"ar": "حدد مقراً من القائمة لعرض بياناته الجغرافية.", "en": "Select a zone from the list to view its geographic details."},
    "no_zones_title": {"ar": "لا توجد مقرات مضافة", "en": "No Work Zones Found"},
    "no_zones_hint": {"ar": "اضغط على \"+ إضافة مقر جديد\" لتعيين الفروع ومواقع العمل الجغرافية.", "en": "Click \"+ Add Work Zone\" to set up company branches and geofence locations."},
    "confirm_delete_zone": {"ar": "تأكيد حذف المقر؟", "en": "Confirm deleting this zone?"},
    "active": {"ar": "نشط", "en": "Active"},
    "inactive": {"ar": "غير نشط", "en": "Inactive"},

    # Status Badges
    "badge_active": {"ar": "حاضر الآن", "en": "Active Now"},
    "badge_full_shift": {"ar": "شفت كامل", "en": "Full Shift"},
    "badge_short_shift": {"ar": "شفت غير كامل", "en": "Short Shift"},
    "badge_on_time": {"ar": "في الموعد", "en": "On Time"},
    "badge_late": {"ar": "متأخر", "en": "Late"},
    "badge_inside": {"ar": "داخل النطاق", "en": "Inside Zone"},
    "badge_outside": {"ar": "خارج النطاق", "en": "Outside Zone"},
    "badge_enrolled": {"ar": "بصمة مسجلة", "en": "Device Enrolled"},
    "badge_not_enrolled": {"ar": "غير مسجل", "en": "Not Enrolled"},

    # Employee Panel
    "emp_role": {"ar": "موظف • ريفي بصمة", "en": "Employee • Revy Basma"},
    "emp_nav_home": {"ar": "الرئيسية", "en": "Home"},
    "emp_nav_history": {"ar": "السجل", "en": "History"},
    "emp_nav_profile": {"ar": "حسابي", "en": "Profile"},
    "current_location": {"ar": "موقعك الحالي", "en": "Your Current Location"},
    "no_zone_assigned": {"ar": "لم يتم تحديد مقر لك بعد", "en": "No work zone assigned yet"},
    "distance": {"ar": "المسافة", "en": "Distance"},
    "meters": {"ar": "متر", "en": "meters"},
    "allowed": {"ar": "المسموح", "en": "Allowed"},
    "loc_detecting": {"ar": "جاري تحديد موقعك الجغرافي بدقة...", "en": "Accurately detecting your location..."},
    "sign_out_success": {"ar": "تم تسجيل الانصراف بنجاح", "en": "Check-out completed successfully"},
    "total_work_hours": {"ar": "إجمالي ساعات العمل لليوم", "en": "Total working hours today"},
    "elapsed_time": {"ar": "الوقت المنقضي حتى الآن", "en": "Elapsed Time So Far"},
    "you_are_present": {"ar": "أنت حاضر الآن", "en": "You are Checked In"},
    "current_time": {"ar": "الوقت الحالي", "en": "Current Time"},
    "check_in_today": {"ar": "تسجيل حضور اليوم", "en": "Today's Attendance Check-in"},
    "btn_check_in": {"ar": "تسجيل الحضور بالبصمة", "en": "Biometric Check In"},
    "btn_check_in_late": {"ar": "تسجيل حضور متأخر", "en": "Late Biometric Check In"},
    "btn_check_out": {"ar": "تسجيل الانصراف", "en": "Biometric Check Out"},
    "outside_zone_alert_title": {"ar": "أنت خارج النطاق الجغرافي للمقر", "en": "You are outside the branch geo-fence"},
    "outside_zone_alert_text": {"ar": "لا يمكن تسجيل الحضور إلا من داخل محيط مقر العمل.", "en": "Check-in is only allowed within the authorized branch radius."},
    "early_window_alert_title": {"ar": "لم تبدأ نافذة تسجيل الحضور بعد", "en": "Sign-in window is not open yet"},
    "expired_window_alert_title": {"ar": "انتهى وقت تسجيل الحضور اليوم", "en": "Sign-in window has expired for today"},
    "late_warning_title": {"ar": "تسجيل حضور متأخر", "en": "Late Attendance Check In"},
    "late_warning_text": {"ar": "تجاوزت فترة السماح للشفت، سيتم توثيق دقائق التأخير بالسجل.", "en": "Grace period exceeded. Delay minutes will be recorded in your history."},
    "register_device_first": {"ar": "يلزم تسجيل بصمة جهازك (Face ID / Fingerprint) لتمكين الحضور.", "en": "You must register your biometric device (Face ID / Fingerprint) to enable attendance."},
    "register_device_btn": {"ar": "تسجيل بصمة الجهاز", "en": "Register Biometric Device"},
    "shift_schedule": {"ar": "مواعيد الشفت", "en": "Shift Schedule"},
    "confirm_sign_out_title": {"ar": "تأكيد تسجيل الانصراف؟", "en": "Confirm Sign Out?"},
    "expected_status": {"ar": "الحالة المتوقعة", "en": "Expected Status"},
    "status_today_workday": {"ar": "اليوم يوم عمل رسمي", "en": "Today is a work day"},
    "status_today_day_off": {"ar": "اليوم يوم عطلتك الأسبوعية", "en": "Today is your day off"},
    "day_off_signin_note": {"ar": "تسجيل الحضور متاح اليوم، وسيتم توثيقه كيوم عمل إضافي في رصيدك.", "en": "Signing in is available today and will be recorded as an extra day worked."},
    "my_schedule_title": {"ar": "جدول مواعيدي الأسبوعي", "en": "My Weekly Schedule"},
    "month_attendance_progress": {"ar": "حضور الشهر الحالي", "en": "This Month's Progress"},
    "badge_today": {"ar": "اليوم", "en": "Today"},
    "badge_workday": {"ar": "يوم عمل", "en": "Work"},
    "badge_day_off": {"ar": "عطلة", "en": "Off"},
    "days_attended_of_expected": {"ar": "{attended} من {expected} يوم متوقع", "en": "{attended} of {expected} expected days"},
    "btn_check_in_extra": {"ar": "تسجيل حضور إضافي (عطلة)", "en": "Biometric Check In (Day Off)"},
    "shift_window_time": {"ar": "فترة السماح بالحضور", "en": "Sign-in Window"},

    
    # Reports Page
    "reports_title": {"ar": "التقارير وسجل الحضور", "en": "Attendance Reports"},
    "reports_sub": {"ar": "عرض وتصفية وتصدير تقارير الحضور والانصراف بالتفصيل", "en": "View, filter, and export detailed attendance records"},
    "export_excel": {"ar": "تصدير Excel (.xlsx)", "en": "Export Excel (.xlsx)"},
    "export_csv": {"ar": "تصدير CSV", "en": "Export CSV"},
    "report_total": {"ar": "إجمالي السجلات", "en": "Total Records"},
    "report_late_count": {"ar": "حالات التأخير", "en": "Late Count"},
    "report_details": {"ar": "تفاصيل سجلات الحضور", "en": "Attendance Details"},
    "extra_days": {"ar": "أيام عمل العطلة", "en": "Days Off Worked"},
    "days_off_worked": {"ar": "أيام عمل العطلة", "en": "Days Off Worked"},
    "absent_days": {"ar": "أيام الغياب", "en": "Absent Days"},
    "attendance_rate": {"ar": "نسبة الحضور", "en": "Attendance Rate"},
    "expected_days": {"ar": "الأيام المتوقعة", "en": "Expected Days"},
    "attended_days": {"ar": "أيام الحضور", "en": "Attended Days"},
    "no_absent_days": {"ar": "لا يوجد غياب", "en": "None"},
    "no_extra_days": {"ar": "لا يوجد", "en": "None"},
    
    # Settings Page
    "settings_title": {"ar": "إعدادات النظام", "en": "System Settings"},
    "settings_sub": {"ar": "تكوين إعدادات الشركة، التوقيت، ومعايير الأمان الحيوي", "en": "Configure organization preferences, timezones, and biometric security"},
    "system_name": {"ar": "اسم النظام", "en": "System Name"},
    "server_timezone": {"ar": "توقيت الخادم المعتمد", "en": "Server Timezone"},
    "server_timezone_desc": {"ar": "تعتمد المنظومة ساعة السيرفر الرسمية لتحديد زمن الحضور والانصراف بدقة.", "en": "The system relies on official server time for precise attendance logs."},
    "gps_accuracy_mode": {"ar": "دقة الموقع الجغرافي", "en": "GPS Accuracy Mode"},
    "gps_high_accuracy": {"ar": "دقة عالية جداً (GPS + Wi-Fi + أبراج الاتصال)", "en": "High Accuracy (GPS + Wi-Fi + Cell)"},
    "gps_balanced": {"ar": "دقة متوازنة (Balanced)", "en": "Balanced Mode"},
    "require_passkeys": {"ar": "فرض البصمة الحيوية (Passkeys) كعامل أمان أساسي", "en": "Enforce biometric Passkeys as primary security factor"},
    "system_stats": {"ar": "إحصائيات المنظومة", "en": "System Statistics"},
    "security_status": {"ar": "حالة الأمان وحماية البيانات", "en": "Security & Protection Status"},
    "security_layer_1": {"ar": "تشفير كلمات المرور والبيانات الحساسة بأعلى المعايير.", "en": "Encrypted credentials and sensitive data protection."},
    "security_layer_2": {"ar": "نطاق جغرافي صارم ومحدد لكل مقر عمل.", "en": "Strict geofencing radius per branch location."},
    "security_layer_3": {"ar": "توثيق حيوي مشفر عبر عتاد الجهاز (WebAuthn).", "en": "Hardware-bound biometric WebAuthn credentials."},
    
    # Employee History & Profile
    "history_title": {"ar": "سجل الحضور والانصراف", "en": "Attendance History"},
    "profile_title": {"ar": "الملف الشخصي", "en": "My Profile"},
    "account_details": {"ar": "تفاصيل الحساب والعمل", "en": "Account & Job Details"},
    "full_name": {"ar": "الاسم الكامل", "en": "Full Name"},
    "reg_date": {"ar": "تاريخ التسجيل", "en": "Enrollment Date"},
    "bio_security": {"ar": "بصمة وأمان الجهاز الحيوي", "en": "Biometric Device Security"},
    "manage_devices": {"ar": "إدارة الأجهزة", "en": "Manage Devices"},
    "webauthn_enroll_title": {"ar": "تسجيل بصمة الجهاز", "en": "Biometric Enrollment"},
    "webauthn_enroll_sub": {"ar": "ربط Face ID أو بصمة الإصبع أو Windows Hello بحسابك لتسجيل الحضور بأمان", "en": "Link Face ID, Fingerprint, or Windows Hello to your account for secure attendance"},

    # ── Flash message keys ────────────────────────────────────────────────────
    # All flash() calls use these keys. They are translated in the base template
    # at render time so the active language is always respected.

    # Admin — Zones
    "flash_zone_created":   {"ar": "تم إضافة الفرع بنجاح", "en": "Branch added successfully"},
    "flash_zone_updated":   {"ar": "تم تعديل بيانات الفرع بنجاح", "en": "Branch updated successfully"},
    "flash_zone_deleted":   {"ar": "تم حذف الفرع بنجاح", "en": "Branch deleted successfully"},

    # Admin — Shifts
    "flash_shift_created":  {"ar": "تم إضافة الشفت بنجاح", "en": "Shift added successfully"},
    "flash_shift_updated":  {"ar": "تم تعديل الشفت بنجاح", "en": "Shift updated successfully"},
    "flash_shift_deleted":  {"ar": "تم حذف الشفت بنجاح", "en": "Shift deleted successfully"},

    # Admin — Employees
    "flash_employee_created":       {"ar": "تم إضافة الموظف بنجاح", "en": "Employee added successfully"},
    "flash_employee_updated":       {"ar": "تم تعديل بيانات الموظف بنجاح", "en": "Employee updated successfully"},
    "flash_employee_deleted":       {"ar": "تم حذف الموظف بنجاح", "en": "Employee deleted successfully"},
    "flash_employee_admin_edit":    {"ar": "لا يمكن تعديل بيانات المدير من هذه الصفحة", "en": "Admin account cannot be edited from this page"},
    "flash_devices_reset":          {"ar": "تم إزالة الأجهزة المسجلة للموظف بنجاح، ويمكنه الآن تسجيل جهاز جديد", "en": "Registered devices removed successfully. The employee can now enroll a new device"},
    "flash_work_days_required":     {"ar": "يجب اختيار يوم عمل واحد على الأقل للموظف", "en": "At least one working day must be selected for the employee"},
    "flash_work_days_invalid":      {"ar": "أيام العمل المحددة غير صالحة", "en": "Selected working days are invalid"},

    # Admin — Settings
    "flash_settings_saved":         {"ar": "تم حفظ إعدادات النظام بنجاح", "en": "System settings saved successfully"},
    "flash_settings_read_only":     {"ar": "الإعدادات للعرض فقط في هذا الإصدار ولا يتم حفظ التعديلات حالياً.", "en": "Settings are display-only in this version; changes are not persisted."},
    "flash_attendance_closed":      {"ar": "تم إغلاق سجل الحضور واحتساب ساعات العمل بنجاح.", "en": "Attendance record closed and work hours calculated successfully."},
    "flash_attendance_close_error": {"ar": "تعذر إغلاق سجل الحضور.", "en": "Failed to close attendance record."},

    # Auth — Login
    "flash_login_invalid":          {"ar": "اسم المستخدم أو كلمة المرور غلط", "en": "Invalid username or password"},

    # Employee — Sign in / out
    "flash_location_unavailable":   {"ar": "تعذر تحديد موقعك. تأكد من السماح للمتصفح بالوصول إلى الموقع وأعد المحاولة.", "en": "Unable to determine your location. Please allow browser location access and try again."},
    "flash_signin_success":         {"ar": "تم تسجيل الحضور بنجاح", "en": "Sign-in recorded successfully"},
    "flash_signout_success":        {"ar": "تم تسجيل الانصراف بنجاح", "en": "Sign-out recorded successfully"},

    # Employee — WebAuthn / devices
    "flash_device_already_exists":  {"ar": "لديك جهاز مسجل بالفعل. لا يمكن إضافة جهاز جديد إلا بعد مسح البصمة الحالية من قِبل المسؤول.", "en": "You already have a registered device. Contact your admin to reset it before enrolling a new one."},
    "flash_device_locked":          {"ar": "لا يمكن إضافة جهاز جديد. يرجى التواصل مع المسؤول لإعادة ضبط البصمة أولاً.", "en": "Cannot add a new device. Please contact your admin to reset biometric first."},
    "flash_device_enrolled":        {"ar": "تم تسجيل بصمة الجهاز بنجاح", "en": "Device biometric enrolled successfully"},
    "flash_device_deleted":         {"ar": "تم حذف الجهاز بنجاح", "en": "Device removed successfully"},

    # ── Export / Report translation keys ─────────────────────────────────────
    # Used by report_service.py for CSV headers, Excel sheet/title, status labels
    "export_sheet_title":       {"ar": "تقرير الحضور والغياب", "en": "Attendance Report"},
    "export_title_banner":      {"ar": "تقرير حضور وانصراف الموظفين — ريفي بصمة", "en": "Employee Attendance Report — Revy Basma"},
    "export_col_date":          {"ar": "التاريخ", "en": "Date"},
    "export_col_employee":      {"ar": "اسم الموظف", "en": "Employee Name"},
    "export_col_zone":          {"ar": "الفرع", "en": "Branch"},
    "export_col_signin":        {"ar": "وقت الحضور", "en": "Sign-in Time"},
    "export_col_signout":       {"ar": "وقت الانصراف", "en": "Sign-out Time"},
    "export_col_total_hours":   {"ar": "إجمالي الساعات", "en": "Total Hours"},
    "export_col_shift_status":  {"ar": "حالة الشفت", "en": "Shift Status"},
    "export_col_late":          {"ar": "التأخير", "en": "Late"},
    "export_col_late_minutes":  {"ar": "دقائق التأخير", "en": "Late Minutes"},
    "export_col_expected_days": {"ar": "الأيام المتوقعة", "en": "Expected Days"},
    "export_col_attended_days": {"ar": "أيام الحضور", "en": "Attended Days"},
    "export_col_absent_days":   {"ar": "أيام الغياب", "en": "Absent Days"},
    "export_col_extra_days":    {"ar": "حضور أيام العطلة", "en": "Days Off Worked"},
    "export_col_attendance_rate": {"ar": "نسبة الحضور", "en": "Attendance Rate"},
    "export_status_full":       {"ar": "شفت كامل", "en": "Full Shift"},
    "export_status_short":      {"ar": "شفت غير كامل", "en": "Short Shift"},
    "export_status_active":     {"ar": "قيد العمل", "en": "In Progress"},
    "export_hours_suffix":      {"ar": "ساعة", "en": "hrs"},
    "export_yes":               {"ar": "نعم", "en": "Yes"},
    "export_no":                {"ar": "لا", "en": "No"},
    "export_filename_csv":      {"ar": "تقرير_الحضور", "en": "attendance_report"},
    "export_filename_excel":    {"ar": "تقرير_الحضور", "en": "attendance_report"},
}



def get_current_lang():
    """Returns 'ar' or 'en' based on session or cookie preference."""
    if 'lang' in session and session['lang'] in ('ar', 'en'):
        return session['lang']
    cookie_lang = request.cookies.get('lang') if request else None
    if cookie_lang in ('ar', 'en'):
        return cookie_lang
    return 'ar'


def t(key, lang=None, **kwargs):
    """Translate a key into target language with optional formatting variables."""
    if not lang:
        lang = get_current_lang()
    
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    
    text = entry.get(lang) or entry.get('ar') or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def format_localized_date(d=None, lang=None):
    """Returns localized full date string (e.g., 'الجمعة، 9 أكتوبر 2026' or 'Friday, 9 October 2026')."""
    if d is None:
        d = date.today()
    if not lang:
        lang = get_current_lang()
    if lang == 'en':
        return f"{EN_WEEKDAYS[d.weekday()]}, {d.day} {EN_MONTHS[d.month - 1]} {d.year}"
    return f"{AR_WEEKDAYS[d.weekday()]}، {d.day} {AR_MONTHS[d.month - 1]} {d.year}"


def format_work_days_short(work_days_val, lang=None):
    """Returns localized short weekday names in Sat..Fri order (e.g. 'سبت، أحد، إثنين' or 'Sat, Sun, Mon')."""
    if not lang:
        lang = get_current_lang()
    if hasattr(work_days_val, 'work_days_list'):
        days_list = work_days_val.work_days_list
    elif isinstance(work_days_val, str):
        try:
            days_list = [int(x.strip()) for x in work_days_val.split(',') if x.strip() != '']
        except ValueError:
            days_list = []
    elif isinstance(work_days_val, (list, set, tuple)):
        days_list = [int(x) for x in work_days_val]
    else:
        days_list = []

    short_names = []
    for opt in WEEKDAY_OPTIONS:
        if opt['day'] in days_list:
            if lang == 'en':
                short_names.append(EN_WEEKDAYS_SHORT[opt['day']])
            else:
                short_names.append(AR_WEEKDAYS_SHORT[opt['day']])
    sep = ', ' if lang == 'en' else '، '
    return sep.join(short_names) if short_names else '—'

