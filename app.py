import streamlit as st
import sqlite3
import io
import csv
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة واللغات (Apple Aesthetic & Minimalist Copy)
# ==========================================
st.set_page_config(
    page_title="Padel 99 | بادل 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def normalize_phone(phone_input):
    if not phone_input:
        return ""
    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    p = str(phone_input).translate(ar_digits)
    p = "".join([c for c in p if c.isdigit()])
    if p.startswith("966"):
        p = p[3:]
    if p.startswith("0"):
        p = p[1:]
    return p

LANG = {
    "ar": {
        "dir": "rtl",
        "align": "right",
        "hero_title": "Padel 99.",
        "hero_sub": "تمرين {}. اللعب كما ينبغي أن يكون.",
        "promo_badge": "✨ برنامج الوفاء: 6 تمارين تمنحك السابع مجاناً بالكامل.",
        "discount_badge": "🏷️ عرض استثنائي: خصم 20% لتمرين اليوم.",
        "time_str": "⏰ ٩:٣٠ م – ١١:٠٠ م | كورت 1 & 2 • المقاعد محدودة (12 لاعب)",
        "privacy_note": "🔒 أمان وخصوصية تامة: بياناتك تُستخدم حصرياً لتأكيد مقعدك وبرنامج الوفاء.",
        "court1": "🏟️ كورت 1",
        "court2": "🏟️ كورت 2",
        "tab_book": "⚡ تأكيد المقعد",
        "tab_cancel": "❌ تعديل / اعتذار",
        "name_lbl": "الاسم الكامل",
        "phone_lbl": "رقم الجوال",
        "level_lbl": "مستوى الأداء",
        "levels": ["متوسط", "متقدم", "مبتدئ"],
        "btn_book": "انضم إلى التشكيلة 🚀",
        "err_fields": "يرجى التحقق من صحة الاسم ورقم الجوال للمتابعة.",
        "succ_book": "أهلاً بك في الملعب يا كابتن {}! تم حجز مكانك في {}.",
        "succ_wait": "اكتملت التشكيلة الأساسية. تم إدراجك في أولوية قائمة الاحتياط.",
        "cancel_phone": "رقم الجوال المسجل به الحجز:",
        "cancel_reason": "سبب الاعتذار الرئيسي:",
        "reasons": [
            "قيمة المساهمة غير مناسبة",
            "أفضّل ملعباً بمواصفات أو موقع آخر",
            "وجدت خياراً بديلاً أقرب",
            "انضممت لمجموعة لعب أخرى",
            "أبحث عن مستوى تنافسي مختلف",
            "ارتباط مفاجئ / تعارض في الجدول",
            "إجهاد بدني أو حاجة للاستشفاء",
            "صعوبة في الوصول أو المواصلات",
            "ظرف شخصي طارئ"
        ],
        "btn_cancel": "تأكيد الاعتذار وإتاحة المقعد",
        "succ_cancel": "تم تسجيل اعتذارك يا كابتن {}. نتطلع لرؤيتك في التمرين القادم.",
        "succ_cancel_refund": "تم قبول اعتذارك يا كابتن {}. تم توثيق طلب استرجاع مساهمتك تلقائياً ✅.",
        "err_cancel": "لم يتم العثور على حجز مؤكد مرتبط بهذا الرقم في تمرين اليوم.",
        "admin_pin": "رمز الدخول السري:",
        "export_btn": "📥 تصدير سجل الحضور والمطابقات (Excel)",
        "btn_wa_captain": "مشاركة إشعار التأكيد مع الكابتن (WhatsApp) ⚡",
        "cal_btn": "إضافة الموعد إلى التقويم 📅",
        "pay_card_title": "المحفظة الرقمية | التحويل المباشر",
        "pay_subtitle": "اللمسة الأخيرة لاكتمال مقعدك في التشكيلة الأساسية"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "hero_title": "Padel 99.",
        "hero_sub": "{} Session. Pure padel, perfected.",
        "promo_badge": "✨ Loyalty Pass: Play 6 sessions, get the 7th entirely on us.",
        "discount_badge": "🏷️ Special Edition: 20% OFF today's session pass.",
        "time_str": "⏰ 9:30 PM – 11:00 PM | Courts 1 & 2 • Limited (12 Slots)",
        "privacy_note": "🔒 Privacy Guaranteed: Your data is solely used for court access & loyalty perks.",
        "court1": "🏟️ Court 1",
        "court2": "🏟️ Court 2",
        "tab_book": "⚡ Reserve Spot",
        "tab_cancel": "❌ Manage / Cancel",
        "name_lbl": "Full Name",
        "phone_lbl": "Mobile Number",
        "level_lbl": "Performance Level",
        "levels": ["Intermediate", "Advanced", "Beginner"],
        "btn_book": "Join the Squad 🚀",
        "err_fields": "Please check your name and mobile number to proceed.",
        "succ_book": "Welcome to the court, Captain {}! Secured in {}.",
        "succ_wait": "Main roster full. You have priority access on the waitlist.",
        "cancel_phone": "Registered Mobile:",
        "cancel_reason": "Primary Cancellation Reason:",
        "reasons": [
            "Session fee is not optimal",
            "Prefer a different court venue",
            "Found an alternate match nearby",
            "Playing with another group",
            "Seeking a different competitive tier",
            "Sudden schedule or work conflict",
            "Physical fatigue / Recovery day",
            "Commute / Transportation issue",
            "Personal emergency"
        ],
        "btn_cancel": "Confirm Cancellation & Release Spot",
        "succ_cancel": "Cancelled for Captain {}. We hope to see you next time.",
        "succ_cancel_refund": "Cancelled for Captain {}. Your refund is logged for priority processing ✅.",
        "err_cancel": "No confirmed reservation found for this number today.",
        "admin_pin": "Passcode:",
        "export_btn": "📥 Export Timesheet & Logs (Excel)",
        "btn_wa_captain": "Share Pass Receipt via WhatsApp ⚡",
        "cal_btn": "Add to Calendar 📅",
        "pay_card_title": "Digital Wallet | Direct Pass",
        "pay_subtitle": "The final touch to secure your place on the roster"
    }
}

col_t1, col_t2 = st.columns([5, 1])
with col_t2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# ==========================================
# 2. الهوية البصرية بنمط Apple (Dark Mode, Frosted Glass & SF Aesthetics)
# ==========================================
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=SF+Pro+Display:wght@400;600;700;800&display=swap');
* {{ font-family: 'SF Pro Display', 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}

.block-container {{
    padding-top: 0.6rem !important;
    padding-bottom: 0.8rem !important;
    padding-left: 0.4rem !important;
    padding-right: 0.4rem !important;
    max-width: 580px !important;
}}
.stAppHeader {{ display: none; }}

/* Hero Styling */
.hero-header {{
    font-size: 1.6em;
    font-weight: 900;
    letter-spacing: -0.5px;
    margin: 0;
    color: #f4f4f5;
}}
.hero-sub {{
    font-size: 0.9em;
    color: #a1a1aa;
    margin-top: -2px;
    margin-bottom: 4px;
}}

.promo-badge {{
    background: rgba(30, 58, 138, 0.4);
    border: 1px solid rgba(59, 130, 246, 0.4);
    backdrop-filter: blur(10px);
    border-radius: 8px;
    padding: 4px 8px;
    text-align: center;
    color: #bfdbfe;
    font-weight: 700;
    font-size: 0.78em;
    margin-bottom: 3px;
}}
.discount-badge {{
    background: rgba(180, 83, 9, 0.35);
    border: 1px solid rgba(245, 158, 11, 0.4);
    backdrop-filter: blur(10px);
    border-radius: 8px;
    padding: 4px 8px;
    text-align: center;
    color: #fde68a;
    font-weight: 700;
    font-size: 0.78em;
    margin-bottom: 4px;
}}
.privacy-badge {{
    font-size: 0.68em;
    color: #71717a;
    text-align: center;
    margin-top: 4px;
    margin-bottom: 4px;
}}

/* Apple Wallet Style Digital Card */
.apple-card {{
    background: linear-gradient(145deg, #18181b 0%, #09090b 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 12px;
    margin: 6px 0;
    text-align: center;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
}}
.apple-card-title {{
    color: #10b981;
    font-size: 0.85em;
    font-weight: 800;
    letter-spacing: 0.3px;
}}
.apple-card-sub {{
    color: #a1a1aa;
    font-size: 0.72em;
    margin-bottom: 8px;
}}
.qr-frame {{
    background: #ffffff;
    padding: 6px;
    border-radius: 8px;
    display: inline-block;
    margin-bottom: 6px;
}}
.card-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 3px 0;
    font-size: 0.76em;
}}
.card-lbl {{ color: #71717a; font-weight: 600; }}
.card-val {{ color: #f4f4f5; font-weight: 800; font-family: monospace; }}

/* Form Components */
div[data-testid="stForm"] {{
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    padding: 8px 10px !important;
    background: #121215;
    margin-top: 2px !important;
    margin-bottom: 4px !important;
}}
.stTextInput, .stSelectbox {{
    margin-bottom: -10px !important;
}}
div[data-baseweb="input"] > div {{
    min-height: 36px !important;
    height: 36px !important;
    background-color: #18181b !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
    border-radius: 6px !important;
}}
.stButton>button {{
    width: 100%;
    border-radius: 8px;
    font-weight: 800;
    height: 2.6em;
    font-size: 0.95em;
    background: #10b981;
    color: #ffffff;
    border: none;
    transition: all 0.2s ease;
}}
.stButton>button:hover {{
    background: #059669;
    color: #ffffff;
}}
.wa-apple-btn {{
    display: block;
    width: 100%;
    background-color: #25D366;
    color: white !important;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    font-weight: 800;
    text-decoration: none;
    margin-top: 4px;
    margin-bottom: 3px;
    font-size: 0.88em;
}}
.cal-apple-btn {{
    display: block;
    width: 100%;
    background-color: #1e293b;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8 !important;
    text-align: center;
    padding: 6px;
    border-radius: 8px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 2px;
    margin-bottom: 4px;
    font-size: 0.8em;
}}

/* Pitch Aesthetics */
.padel-court {{
    background: radial-gradient(circle, #064e3b 0%, #022c22 100%);
    border: 1.5px solid rgba(16, 185, 129, 0.6);
    border-radius: 10px;
    padding: 5px;
    margin-bottom: 3px;
}}
.court-title {{
    text-align: center;
    color: #a7f3d0;
    font-weight: 800;
    font-size: 0.82em;
    margin-bottom: 4px;
    border-bottom: 1px dashed rgba(16, 185, 129, 0.4);
    padding-bottom: 2px;
}}
.court-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3px;
}}
.slot-box {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 3px 4px;
    text-align: center;
    min-height: 38px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}}
.slot-occupied {{ color: #f4f4f5; font-weight: 700; font-size: 0.76em; line-height: 1.1; }}
.slot-meta {{ font-size: 0.65em; margin-top: 1px; }}
.slot-empty {{ color: #52525b; font-size: 0.68em; }}
.badge-loyalty {{ background-color: #1e3a8a; color: #93c5fd; padding: 0px 3px; border-radius: 3px; font-size: 0.7em; font-weight: 700; }}
.refund-alert-box {{
    background: rgba(69, 26, 3, 0.6);
    border: 1px solid rgba(245, 158, 11, 0.5);
    border-radius: 8px;
    padding: 6px 8px;
    margin-bottom: 5px;
    color: #fef3c7;
    font-size: 0.85em;
}}
</style>""", unsafe_allow_html=True)

# ==========================================
# 3. محرك قاعدة البيانات عالي الاستقرار (WAL Mode)
# ==========================================
DB_FILE = "group99_padel.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                session_day TEXT NOT NULL,
                court INTEGER DEFAULT 1,
                level TEXT DEFAULT 'متوسط',
                status TEXT DEFAULT 'confirmed',
                payment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cancellations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT,
                player_phone TEXT,
                session_day TEXT,
                court INTEGER,
                reason TEXT,
                was_paid TEXT DEFAULT 'no',
                refund_status TEXT DEFAULT 'none',
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute("PRAGMA table_info(cancellations)")
        c_cols = [c[1] for c in cursor.fetchall()]
        if 'was_paid' not in c_cols:
            cursor.execute("ALTER TABLE cancellations ADD COLUMN was_paid TEXT DEFAULT 'no'")
        if 'refund_status' not in c_cols:
            cursor.execute("ALTER TABLE cancellations ADD COLUMN refund_status TEXT DEFAULT 'none'")
        conn.commit()

init_db()

def get_setting(key, default="0"):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM app_settings WHERE key=?", (key,))
        res = c.fetchone()
        return res[0] if res else default

def set_setting(key, val):
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, str(val)))
        conn.commit()

def get_loyalty_score(norm_phone):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT session_day) FROM bookings WHERE phone=? AND status='confirmed'", (norm_phone,))
        res = cur.fetchone()
        return res[0] if res else 0

# ==========================================
# 4. التحديد الآلي للتمرين القادم
# ==========================================
def get_next_session():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    weekday = now.weekday()
    hour = now.hour

    day_name_ar = "الأحد"
    day_name_en = "Sunday"
    days_to_add = 0

    if weekday == 6:
        if hour < 23:
            days_to_add = 0
            day_name_ar, day_name_en = "الأحد", "Sunday"
        else:
            days_to_add = 2
            day_name_ar, day_name_en = "الثلاثاء", "Tuesday"
    elif weekday == 0:
        days_to_add = 1
        day_name_ar, day_name_en = "الثلاثاء", "Tuesday"
    elif weekday == 1:
        if hour < 23:
            days_to_add = 0
            day_name_ar, day_name_en = "الثلاثاء", "Tuesday"
        else:
            days_to_add = 2
            day_name_ar, day_name_en = "الخميس", "Thursday"
    elif weekday == 2:
        days_to_add = 1
        day_name_ar, day_name_en = "الخميس", "Thursday"
    elif weekday == 3:
        if hour < 23:
            days_to_add = 0
            day_name_ar, day_name_en = "الخميس", "Thursday"
        else:
            days_to_add = 3
            day_name_ar, day_name_en = "الأحد", "Sunday"
    elif weekday == 4:
        days_to_add = 2
        day_name_ar, day_name_en = "الأحد", "Sunday"
    elif weekday == 5:
        days_to_add = 1
        day_name_ar, day_name_en = "الأحد", "Sunday"

    target_date = now + timedelta(days=days_to_add)
    date_str = target_date.strftime("%d/%m")
    
    label_ar = f"{day_name_ar} ({date_str})"
    label_en = f"{day_name_en} ({date_str})"
    db_key = f"{day_name_ar} {target_date.strftime('%Y-%m-%d')}"
    
    cal_start = target_date.strftime("%Y%m%d") + "T213000"
    cal_end = target_date.strftime("%Y%m%d") + "T230000"
    cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('🎾 تمرين بادل — قروب 99')}&dates={cal_start}/{cal_end}&details={urllib.parse.quote('تمرين بادل قروب 99 من 9:30 حتى 11:00 مساءً')}&location={urllib.parse.quote('ملعب بادل 99')}"

    return label_ar, label_en, db_key, cal_url

sess_ar, sess_en, db_session_key, session_cal_url = get_next_session()
display_session = sess_ar if l_code == "ar" else sess_en

COURT_CAPACITY = 6
is_promo_active = (get_setting("promo_20_active", "0") == "1")
captain_wa_number = get_setting("captain_whatsapp", "966566261868")

# جلب بيانات الملاعب
with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT id, name, phone, payment_status FROM bookings WHERE session_day=? AND court=1 AND status='confirmed' ORDER BY id ASC LIMIT 6", (db_session_key,))
    c1 = c.fetchall()
    c.execute("SELECT id, name, phone, payment_status FROM bookings WHERE session_day=? AND court=2 AND status='confirmed' ORDER BY id ASC LIMIT 6", (db_session_key,))
    c2 = c.fetchall()
    c.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (db_session_key,))
    waitlist = c.fetchall()

total_booked = len(c1) + len(c2)

# ==========================================
# 5. الترويسة الأنيقة (Apple Hero Section)
# ==========================================
st.markdown(f"<div class='hero-header'>{t['hero_title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>{t['hero_sub'].format(display_session)}</div>", unsafe_allow_html=True)
st.markdown(f'<div class="promo-badge">{t["promo_badge"]}</div>', unsafe_allow_html=True)

if is_promo_active:
    st.markdown(f'<div class="discount-badge">{t["discount_badge"]}</div>', unsafe_allow_html=True)

st.caption(f"{t['time_str']} • <b>المؤكدين: {total_booked}/12</b>", unsafe_allow_html=True)

# ==========================================
# 6. الحجز السريع والبطاقة الرقمية
# ==========================================
tab_book, tab_cancel = st.tabs([t["tab_book"], t["tab_cancel"]])

with tab_book:
    with st.form("book_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([3, 2])
        with c_in1:
            f_name = st.text_input(t["name_lbl"])
        with c_in2:
            f_phone = st.text_input(t["phone_lbl"])
        f_level = st.selectbox(t["level_lbl"], t["levels"])
        btn_book = st.form_submit_button(t["btn_book"])

        if btn_book:
            clean_name = f_name.strip()
            clean_p = normalize_phone(f_phone)

            if len(clean_name) < 2 or len(clean_p) < 8:
                st.error(t["err_fields"])
            else:
                with get_db() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND court=1 AND status='confirmed'", (db_session_key,))
                    cur_c1 = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND court=2 AND status='confirmed'", (db_session_key,))
                    cur_c2 = cur.fetchone()[0]

                    if cur_c1 < COURT_CAPACITY:
                        target_court = 1
                        status_val = 'confirmed'
                    elif cur_c2 < COURT_CAPACITY:
                        target_court = 2
                        status_val = 'confirmed'
                    else:
                        target_court = 1
                        status_val = 'waitlist'

                    cur.execute("INSERT INTO bookings (name, phone, session_day, court, level, status) VALUES (?, ?, ?, ?, ?, ?)",
                                (clean_name, clean_p, db_session_key, target_court, f_level, status_val))
                    conn.commit()

                court_label = f"كورت {target_court}" if l_code == "ar" else f"Court {target_court}"
                st.session_state["recent_book"] = {
                    "name": clean_name,
                    "court": court_label,
                    "status": status_val,
                    "session": display_session
                }
                st.rerun()

    # بطاقة الدفع الرقمية الأنيقة بعد الحجز
    if "recent_book" in st.session_state:
        b = st.session_state["recent_book"]
        if b["status"] == "confirmed":
            st.success(t["succ_book"].format(b["name"], b["court"]))
            
            # بطاقة Apple Wallet للتحويل
            qr_api_url = "https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=SA9380000222608016013114&margin=0"
            st.markdown(f"""
            <div class="apple-card">
                <div class="apple-card-title">{t['pay_card_title']}</div>
                <div class="apple-card-sub">{t['pay_subtitle']}</div>
                <div class="qr-frame">
                    <img src="{qr_api_url}" width="130" height="130" alt="QR Code" style="display:block; border-radius:6px;">
                </div>
                <div class="card-row" style="margin-top: 6px;">
                    <span class="card-lbl">المستفيد:</span>
                    <span style="color:#ffffff; font-weight:700;">فارس ربيع بن عواض العصيمي</span>
                </div>
                <div class="card-row">
                    <span class="card-lbl">رقم الحساب:</span>
                    <span class="card-val">222000010006086013114</span>
                </div>
                <div class="card-row">
                    <span class="card-lbl">رقم الآيبان:</span>
                    <span class="card-val">SA93 8000 0222 6080 1601 3114</span>
                </div>
                <div class="card-row">
                    <span class="card-lbl">سويفت كود:</span>
                    <span class="card-val">RJHISARI</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("📋 **اضغط لنسخ رقم الآيبان فوراً:**")
            st.code("SA9380000222608016013114", language=None)

            msg = f"🎾 هلا كابتن فارس، تم تأكيد حجزي ({b['name']}) في تمرين {b['session']} - {b['court']}. تم التحويل على حساب الراجحي ومرفق الإشعار ⚡"
            wa_url = f"https://wa.me/{captain_wa_number}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-apple-btn">{t["btn_wa_captain"]}</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="{session_cal_url}" target="_blank" class="cal-apple-btn">{t["cal_btn"]}</a>', unsafe_allow_html=True)
        else:
            st.info(t["succ_wait"])
            msg = f"🎾 هلا كابتن فارس، سجلت اسمي ({b['name']}) في قائمة الاحتياط لتمرين {b['session']} ⏳"
            wa_url = f"https://wa.me/{captain_wa_number}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-apple-btn">{t["btn_wa_captain"]}</a>', unsafe_allow_html=True)

    st.markdown(f'<div class="privacy-badge">{t["privacy_note"]}</div>', unsafe_allow_html=True)

# --- تبويب الاعتذار مع فحص الدفع والاسترجاع ---
with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input(t["cancel_phone"])
        can_reason = st.selectbox(t["cancel_reason"], t["reasons"])
        btn_cancel = st.form_submit_button(t["btn_cancel"])

        if btn_cancel:
            clean_cp = normalize_phone(can_phone_raw)
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                cur = conn.cursor()
                cur.execute("SELECT id, name, status, court, payment_status FROM bookings WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')",
                            (clean_cp, db_session_key))
                target = cur.fetchone()

                if target:
                    was_paid = (target[4] == 'paid')
                    refund_st = 'pending_refund' if was_paid else 'none'

                    cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (target[0],))
                    cur.execute("""
                        INSERT INTO cancellations (player_name, player_phone, session_day, court, reason, was_paid, refund_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (target[1], clean_cp, db_session_key, target[3], can_reason, 'yes' if was_paid else 'no', refund_st))
                    
                    if target[2] == 'confirmed':
                        cur.execute("SELECT id FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_session_key,))
                        first_wait = cur.fetchone()
                        if first_wait:
                            cur.execute("UPDATE bookings SET status='confirmed', court=? WHERE id=?", (target[3], first_wait[0]))
                    conn.commit()

                    if was_paid:
                        st.warning(t["succ_cancel_refund"].format(target[1]))
                    else:
                        st.success(t["succ_cancel"].format(target[1]))

                    if "recent_book" in st.session_state:
                        del st.session_state["recent_book"]
                    st.rerun()
                else:
                    st.error(t["err_cancel"])

# ==========================================
# 7. التشكيلة والملاعب (The Arena Visual)
# ==========================================
col_c1, col_c2 = st.columns(2)

def build_court_ui(title, players):
    items = ""
    for i in range(COURT_CAPACITY):
        if i < len(players):
            p = players[i]
            points = (get_loyalty_score(p[2]) % 7)
            pts_badge = f"⭐ {points}/6" if points < 6 else "🎁 مجاني!"
            pay_str = "✅" if p[3] == "paid" else "⏳"
            items += f'<div class="slot-box"><div class="slot-occupied">🎾 {p[1]}</div><div class="slot-meta"><span class="badge-loyalty">{pts_badge}</span> {pay_str}</div></div>'
        else:
            items += f'<div class="slot-box"><div class="slot-empty">مقعد {i+1} شاغر ✨</div></div>'
    return f'<div class="padel-court"><div class="court-title">{title} ({len(players)}/{COURT_CAPACITY})</div><div class="court-grid">{items}</div></div>'

with col_c1:
    st.markdown(build_court_ui(t["court1"], c1), unsafe_allow_html=True)

with col_c2:
    st.markdown(build_court_ui(t["court2"], c2), unsafe_allow_html=True)

if waitlist:
    st.caption("📋 **أولوية الاحتياط:** " + " • ".join([f"{w[1]}" for w in waitlist]))

# ==========================================
# 8. لوحة الإدارة الذكية (Executive Control)
# ==========================================
with st.expander("⚙️", expanded=False):
    pin = st.text_input(t["admin_pin"], type="password", key="adm_pin")
    if pin == "9900":
        st.success("لوحة تحكم الكابتن 👑")
        
        # 1. إدارة استرجاع المبالغ
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, player_name, player_phone, session_day, reason, cancelled_at
                FROM cancellations 
                WHERE refund_status = 'pending_refund'
                ORDER BY id DESC
            """)
            refund_list = cur.fetchall()

        if refund_list:
            st.markdown("### ⚠️ مطلوب استرجاع مبالغ:")
            for r in refund_list:
                st.markdown(f"""
                <div class="refund-alert-box">
                    <b>👤 {r[1]}</b> (`0{r[2]}`)<br>
                    <span>📅 تمرين: {r[3]} | السبب: <i>{r[4]}</i></span><br>
                    <span style="font-size:0.8em; opacity:0.85;">🕒 وقت الاعتذار: {r[5]}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"✅ تم تحويل المبلغ لـ {r[1]}", key=f"ref_{r[0]}"):
                    with get_db() as conn:
                        conn.execute("UPDATE cancellations SET refund_status='refunded' WHERE id=?", (r[0],))
                        conn.commit()
                    st.success(f"تم إغلاق طلب استرجاع الكابتن {r[1]}.")
                    st.rerun()
            st.divider()

        # 2. حاسبة العروض وخصم الـ 20%
        st.markdown("### 🏷️ حاسبة العروض وخصم الـ 20%")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            base_price = st.number_input("سعر القطة الأساسي (ريال):", min_value=10, max_value=200, value=50, step=5)
        with c_p2:
            discount_val = base_price * 0.20
            final_price = base_price - discount_val
            st.metric("السعر بعد الخصم", f"{final_price:.0f} ريال", f"-{discount_val:.0f} ريال خصم")

        promo_toggle = st.checkbox("📢 تفعيل بنر خصم 20% في واجهة الموقع", value=is_promo_active)
        if promo_toggle != is_promo_active:
            set_setting("promo_20_active", "1" if promo_toggle else "0")
            st.rerun()

        st.divider()

        # 3. تصدير التايم شيت لإكسل
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_day, court, name, phone, level,
                       CASE WHEN payment_status='paid' THEN 'تم الدفع' ELSE 'معلق' END as pay_state,
                       created_at
                FROM bookings WHERE status='confirmed'
                ORDER BY session_day DESC, court ASC, id ASC
            """)
            raw_rows = cur.fetchall()

        if raw_rows:
            output = io.StringIO()
            output.write('\ufeff')
            writer = csv.writer(output)
            writer.writerow(["تاريخ التمرين", "الكورت", "الاسم", "رقم الجوال", "المستوى", "حالة القطة", "وقت التسجيل"])
            for r in raw_rows:
                formatted_phone = f'0{r[3]}' if not str(r[3]).startswith('0') else str(r[3])
                writer.writerow([r[0], f"كورت {r[1]}", r[2], f'="{formatted_phone}"', r[4], r[5], r[6]])
            st.download_button(t["export_btn"], output.getvalue().encode('utf-8-sig'), f"padel_timesheet_{datetime.now().strftime('%Y_%m')}.csv", "text/csv")

        st.divider()

        # 4. إدارة لاعبي اليوم والتبديل والدفع
        st.write(f"### إدارة وتوزيع لاعبي {display_session}")
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, phone, payment_status, court, level FROM bookings WHERE session_day=? AND status='confirmed' ORDER BY court ASC, id ASC", (db_session_key,))
            players = cur.fetchall()

        if players:
            for p in players:
                col_i, col_m, col_p, col_d = st.columns([4, 3, 2, 2])
                col_i.write(f"C{p[4]}: **{p[1]}** `[{p[5]}]` (`0{p[2]}`)")
                
                if p[4] == 1:
                    if col_m.button("نقل لـ 2 ➡️", key=f"m2_{p[0]}"):
                        with get_db() as conn:
                            conn.execute("UPDATE bookings SET court=2 WHERE id=?", (p[0],))
                        st.rerun()
                else:
                    if col_m.button("نقل لـ 1 ⬅️", key=f"m1_{p[0]}"):
                        with get_db() as conn:
                            conn.execute("UPDATE bookings SET court=1 WHERE id=?", (p[0],))
                        st.rerun()

                if p[3] == 'pending':
                    if col_p.button("تأكيد 💳", key=f"pay_{p[0]}"):
                        with get_db() as conn:
                            conn.execute("UPDATE bookings SET payment_status='paid' WHERE id=?", (p[0],))
                        st.rerun()
                else:
                    if col_p.button("إلغاء 🔄", key=f"un_{p[0]}"):
                        with get_db() as conn:
                            conn.execute("UPDATE bookings SET payment_status='pending' WHERE id=?", (p[0],))
                        st.rerun()

                if col_d.button("حذف ❌", key=f"del_{p[0]}"):
                    with get_db() as conn:
                        conn.execute("DELETE FROM bookings WHERE id=?", (p[0],))
                    st.rerun()
        else:
            st.info("لا توجد حجوزات لهذا اليوم.")