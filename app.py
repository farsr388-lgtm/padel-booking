import streamlit as st
import sqlite3
import io
import csv
import re
import hmac
import time
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة والهوية البصرية (Apple Minimalist)
# ==========================================
st.set_page_config(
    page_title="Padel 99 | بادل 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

LANG = {
    "ar": {
        "dir": "rtl",
        "align": "right",
        "brand": "Padel 99.",
        "hero_sub": "تمرين {}. متعة اللعب، بتنظيم أبسط.",
        "contrast_banner": "⚡ حجز فوري • 6 لاعبين للملعب • السابع علينا.",
        "promo_badge": "✨ العب 6 تمارين. والسابع مجاناً.",
        "price_tag": "65 ر.س",
        "time_str": "⏰ ٩:٣٠ م – ١١:٠٠ م | كورت 1 (6 مقاعد)",
        "court1": "🏟️ كورت 1",
        "tab_book": "⚡ حجز مقعد",
        "tab_rules": "📜 القواعد",
        "tab_cancel": "❌ اعتذار",
        "name_lbl": "الاسم",
        "phone_lbl": "رقم الجوال (05xxxxxxxx)",
        "level_lbl": "مستوى اللعب",
        "levels": [
            "🟢 متوسط • تبادل مستمر وثبات",
            "🔥 متقدم • سرعة وتكتيك",
            "⚪ مبتدئ • انطلاقة وتعلّم"
        ],
        "btn_book": "تأكيد الانضمام 🚀",
        "err_fields": "فضلاً أدخل الاسم ورقم جوال سعودي يبدأ بـ 05.",
        "err_duplicate": "أنت مسجل بالفعل في تمرين اليوم.",
        "err_spam": "تم رفض الطلب للاشتباه في نشاط آلي.",
        "succ_book_title": "✅ تم تأكيد حجزك بنجاح! شكراً لك يا كابتن {}",
        "succ_book_desc": "تم حجز مقعدك في <b>{}</b>. نتطلع لرؤيتك وتقديم تمرين ممتع!",
        "succ_wait": "اكتملت المقاعد. أنت في صدارة الاحتياط (#{}).",
        "cancel_phone": "رقم الجوال:",
        "cancel_reason": "السبب:",
        "reasons": [
            "تعارض في المواعيد",
            "إجهاد بدني أو إصابة",
            "ظرف طارئ",
            "صعوبة في المواصلات"
        ],
        "btn_cancel": "إلغاء المقعد وإتاحته للبديل",
        "succ_cancel": "تم قبول اعتذارك يا كابتن {}. نراك في التمرين القادم.",
        "err_cancel": "لا يوجد حجز مؤكد مرتبط بهذا الرقم.",
        "admin_pin": "رمز الإدارة السري المشفر:",
        "export_btn": "📥 تصدير السجل (Excel/CSV)"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "brand": "Padel 99.",
        "hero_sub": "{} Session. Pure play, zero hassle.",
        "contrast_banner": "⚡ Instant Booking • 6 Players • 7th on Us.",
        "promo_badge": "✨ Play 6 sessions. The 7th is free.",
        "price_tag": "65 SAR",
        "time_str": "⏰ 9:30 PM – 11:00 PM | Court 1 (6 Slots)",
        "court1": "🏟️ Court 1",
        "tab_book": "⚡ Reserve",
        "tab_rules": "📜 Rules",
        "tab_cancel": "❌ Cancel",
        "name_lbl": "Name",
        "phone_lbl": "Mobile (05xxxxxxxx)",
        "level_lbl": "Skill Level",
        "levels": [
            "🟢 Intermediate • Steady rallies",
            "🔥 Advanced • Fast & tactical",
            "⚪ Beginner • Starting out"
        ],
        "btn_book": "Confirm Spot 🚀",
        "err_fields": "Enter a valid name and Saudi mobile (05xxxxxxxx).",
        "err_duplicate": "Already registered for today's session.",
        "err_spam": "Request rejected due to automated activity.",
        "succ_book_title": "✅ Booking Confirmed! Thank you Captain {}",
        "succ_book_desc": "Your slot is locked for <b>{}</b>. See you on the court!",
        "succ_wait": "Roster full. You are #{} on the waitlist.",
        "cancel_phone": "Mobile Number:",
        "cancel_reason": "Reason:",
        "reasons": [
            "Schedule conflict",
            "Fatigue or injury",
            "Personal emergency",
            "Transportation issue"
        ],
        "btn_cancel": "Release Spot",
        "succ_cancel": "Cancelled for Captain {}. See you next time.",
        "err_cancel": "No active booking found for this number.",
        "admin_pin": "Encrypted Passcode:",
        "export_btn": "📥 Export Timesheet (Excel/CSV)"
    }
}

col_lang1, col_lang2 = st.columns([5, 1])
with col_lang2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# ==========================================
# 2. الواجهة البصرية المستوحاة من Apple
# ==========================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
* {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}
.block-container {{ padding: 0.8rem 0.5rem 1rem 0.5rem !important; max-width: 580px !important; }}
.stAppHeader {{ display: none; }}

.hero-header {{ font-size: 1.65em; font-weight: 900; letter-spacing: -0.5px; color: #f4f4f5; margin: 0; }}
.hero-sub {{ font-size: 0.88em; color: #a1a1aa; margin-bottom: 6px; }}
.contrast-pill {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 4px 8px; font-size: 0.75em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }}
.promo-badge {{ background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.75em; margin-bottom: 4px; }}

.thankyou-box {{
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 78, 59, 0.25) 100%);
    border: 1.5px solid #10b981;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 10px 0;
    text-align: center;
}}
.thankyou-title {{
    color: #34d399;
    font-size: 1.05em;
    font-weight: 800;
    margin-bottom: 4px;
}}
.thankyou-sub {{
    color: #e2e8f0;
    font-size: 0.84em;
}}

.rules-card {{
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 14px;
    padding: 14px;
    margin: 8px 0;
}}
.rule-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 12px;
    font-size: 0.82em;
    color: #e2e8f0;
    line-height: 1.4;
}}
.rule-item:last-child {{ margin-bottom: 0; }}
.rule-icon {{ font-size: 1.1em; }}

.alrajhi-card {{
    background: #111418;
    border: 1.5px solid #2d3748;
    border-radius: 18px;
    padding: 16px;
    margin: 12px 0;
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    color: #ffffff;
}}
.card-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 8px;
    margin-bottom: 12px;
}}
.bank-title {{ font-size: 0.95em; font-weight: 800; color: #f8fafc; }}
.price-pill {{ background: #10b981; color: #022c22; padding: 3px 10px; border-radius: 20px; font-weight: 900; font-size: 0.85em; }}
.qr-container {{ background: #ffffff; padding: 10px; border-radius: 12px; display: inline-block; margin: 4px auto 10px auto; }}
.qr-container img {{ display: block; width: 135px; height: 135px; }}
.card-owner {{ font-size: 1.15em; font-weight: 800; color: #f8fafc; margin-bottom: 10px; text-align: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.12); padding-bottom: 8px; }}
.copy-badge {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 10px;
    font-family: monospace;
    font-size: 0.92em;
    color: #38bdf8;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 8px;
}}
.copy-badge:active {{ background: #0f172a; border-color: #38bdf8; }}

.wa-apple-btn {{
    display: block;
    width: 100%;
    background: linear-gradient(180deg, #25D366 0%, #1da851 100%);
    color: white !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 800;
    text-decoration: none;
    margin-top: 8px;
    font-size: 0.95em;
    box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
}}

.padel-court {{ background: radial-gradient(circle, #064e3b 0%, #022c22 100%); border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 12px; padding: 12px; margin-bottom: 6px; }}
.court-title {{ text-align: center; color: #a7f3d0; font-weight: 800; font-size: 0.95em; margin-bottom: 10px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 6px; }}
.court-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.slot-box {{ background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 8px 6px; text-align: center; min-height: 52px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
.slot-occupied {{ color: #f4f4f5; font-weight: 700; font-size: 0.84em; line-height: 1.2; }}
.slot-meta {{ display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.70em; margin-top: 4px; flex-wrap: wrap; }}
.slot-empty {{ color: #52525b; font-size: 0.78em; }}
.badge-loyalty {{ background-color: #1e3a8a; color: #93c5fd; padding: 1px 4px; border-radius: 3px; font-size: 0.72em; font-weight: 700; }}
.badge-level {{ background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 4px; border-radius: 3px; font-size: 0.70em; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.15); }}

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. محرك البيانات وقاعدة البيانات
# ==========================================
DB_FILE = "group99_padel.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                session_day TEXT NOT NULL,
                court INTEGER DEFAULT 1,
                level TEXT DEFAULT 'متوسط',
                status TEXT DEFAULT 'confirmed',
                payment_status TEXT DEFAULT 'pending',
                attendance TEXT DEFAULT 'unknown',
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cur.execute("PRAGMA table_info(bookings)")
        existing_cols = [row[1] for row in cur.fetchall()]
        if "payment_status" not in existing_cols:
            cur.execute("ALTER TABLE bookings ADD COLUMN payment_status TEXT DEFAULT 'pending';")
        if "attendance" not in existing_cols:
            cur.execute("ALTER TABLE bookings ADD COLUMN attendance TEXT DEFAULT 'unknown';")
        if "level" not in existing_cols:
            cur.execute("ALTER TABLE bookings ADD COLUMN level TEXT DEFAULT 'متوسط';")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_sess_court ON bookings(session_day, court, status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_phone ON bookings(phone);")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS cancellations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT,
                player_phone TEXT,
                session_day TEXT,
                court INTEGER,
                reason TEXT,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# ==========================================
# 4. دوال التحقق والحماية العالية
# ==========================================
def clean_and_validate_sa_phone(raw_phone):
    if not raw_phone:
        return None
    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    p = str(raw_phone).translate(ar_digits).strip()
    p = re.sub(r'[\s\-\(\)\+]', '', p)
    if p.startswith("966"):
        p = "0" + p[3:]
    elif p.startswith("5"):
        p = "0" + p
    if re.match(r"^05[0-9]{8}$", p):
        return p
    return None

def check_active_booking(phone, session_key):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM bookings 
            WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')
        """, (phone, session_key))
        return cur.fetchone() is not None

def get_loyalty_score(norm_phone):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT session_day) FROM bookings WHERE phone=? AND status='confirmed'", (norm_phone,))
        res = cur.fetchone()
        return res[0] if res else 0

def verify_admin_security(input_pin):
    now = time.time()
    if "admin_attempts" not in st.session_state:
        st.session_state["admin_attempts"] = 0
    if "admin_lockout_until" not in st.session_state:
        st.session_state["admin_lockout_until"] = 0
        
    if now < st.session_state["admin_lockout_until"]:
        remaining_sec = int(st.session_state["admin_lockout_until"] - now)
        minutes = remaining_sec // 60
        seconds = remaining_sec % 60
        st.error(f"🔒 تم قفل لوحة الإدارة مؤقتاً. يرجى الانتظار: {minutes}:{seconds:02d} دقيقة.")
        return False

    if not input_pin:
        return False

    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    p = str(input_pin).translate(ar_digits).strip()
    
    is_valid = False
    master_secret = None
    try:
        master_secret = st.secrets.get("ADMIN_PASSWORD", None) or st.secrets.get("ADMIN_PIN", None)
    except Exception:
        pass

    if master_secret:
        clean_secret = str(master_secret).translate(ar_digits).strip()
        is_valid = hmac.compare_digest(p, clean_secret)
    else:
        is_valid = hmac.compare_digest(p, "Padel99#Master@2026")

    if is_valid:
        st.session_state["admin_attempts"] = 0
        return True
    else:
        st.session_state["admin_attempts"] += 1
        if st.session_state["admin_attempts"] >= 3:
            st.session_state["admin_lockout_until"] = now + 600
            st.error("🚨 تم حظر المحاولات وقفل لوحة الإدارة لمدة 10 دقائق بسبب تكرار الخطأ.")
        else:
            left = 3 - st.session_state["admin_attempts"]
            st.error(f"رمز الدخول غير صحيح. (المحاولات المتبقية: {left})")
        return False

# ==========================================
# 5. محرك التجدد الزمني التلقائي
# ==========================================
def get_next_session():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    weekday = now.weekday()

    if weekday == 6:     # الأحد
        days_to_add = 0
        d_ar, d_en = "الأحد", "Sunday"
    elif weekday == 0:   # الإثنين
        days_to_add = 1
        d_ar, d_en = "الثلاثاء", "Tuesday"
    elif weekday == 1:   # الثلاثاء
        days_to_add = 0
        d_ar, d_en = "الثلاثاء", "Tuesday"
    elif weekday == 2:   # الأربعاء
        days_to_add = 1
        d_ar, d_en = "الخميس", "Thursday"
    elif weekday == 3:   # الخميس
        days_to_add = 0
        d_ar, d_en = "الخميس", "Thursday"
    elif weekday == 4:   # الجمعة
        days_to_add = 2
        d_ar, d_en = "الأحد", "Sunday"
    else:                # السبت
        days_to_add = 1
        d_ar, d_en = "الأحد", "Sunday"

    target_date = now + timedelta(days=days_to_add)
    date_str = target_date.strftime("%d/%m")
    label_ar = f"{d_ar} ({date_str})"
    label_en = f"{d_en} ({date_str})"
    db_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"
    return label_ar, label_en, db_key

sess_ar, sess_en, db_session_key = get_next_session()
display_session = sess_ar if l_code == "ar" else sess_en

COURT_CAPACITY = 6

with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT id, name, phone, payment_status, level FROM bookings WHERE session_day=? AND court=1 AND status='confirmed' ORDER BY id ASC LIMIT 6", (db_session_key,))
    c1 = c.fetchall()
    c.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (db_session_key,))
    waitlist = c.fetchall()

total_booked = len(c1)

# ==========================================
# 6. واجهة المستخدم والتسجيل
# ==========================================
st.markdown(f"<div class='hero-header'>{t['brand']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>{t['hero_sub'].format(display_session)}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='contrast-pill'>{t['contrast_banner']}</div>", unsafe_allow_html=True)
st.markdown(f'<div class="promo-badge">{t["promo_badge"]}</div>', unsafe_allow_html=True)
st.caption(f"{t['time_str']} • <b>المؤكدين: {total_booked}/6</b>", unsafe_allow_html=True)

tab_book, tab_rules, tab_cancel = st.tabs([t["tab_book"], t["tab_rules"], t["tab_cancel"]])

with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([3, 2])
        with c_in1:
            f_name = st.text_input(t["name_lbl"])
        with c_in2:
            f_phone = st.text_input(t["phone_lbl"], placeholder="05xxxxxxxx")
        
        f_level_raw = st.selectbox(t["level_lbl"], t["levels"])
        f_level = "متوسط" if "متوسط" in f_level_raw or "Intermediate" in f_level_raw else ("متقدم" if "متقدم" in f_level_raw or "Advanced" in f_level_raw else "مبتدئ")
        
        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button(t["btn_book"])

        if btn_submit:
            if honeypot_val:
                st.error(t["err_spam"])
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 2 or not clean_phone:
                st.error(t["err_fields"])
            elif check_active_booking(clean_phone, db_session_key):
                st.warning(t["err_duplicate"])
            else:
                with get_db() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    cur = conn.cursor()
                    
                    cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND court=1 AND status='confirmed'", (db_session_key,))
                    cur_c1 = cur.fetchone()[0]

                    if cur_c1 < COURT_CAPACITY:
                        target_court = 1
                        status_val = 'confirmed'
                    else:
                        target_court = 1
                        status_val = 'waitlist'

                    cur.execute("""
                        INSERT INTO bookings (name, phone, session_day, court, level, status) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (clean_name, clean_phone, db_session_key, target_court, f_level, status_val))
                    
                    wait_pos = None
                    if status_val == 'waitlist':
                        cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND status='waitlist'", (db_session_key,))
                        wait_pos = cur.fetchone()[0]

                    conn.commit()

                st.session_state["last_booking"] = {
                    "name": clean_name,
                    "phone": clean_phone,
                    "court": "كورت 1",
                    "status": status_val,
                    "wait_pos": wait_pos,
                    "session": display_session,
                    "is_new": True
                }
                st.rerun()

    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        if lb["status"] == "confirmed":
            if lb.get("is_new", False):
                st.balloons()
                lb["is_new"] = False

            thank_html = f"""
            <div class="thankyou-box">
                <div class="thankyou-title">{t["succ_book_title"].format(lb["name"])}</div>
                <div class="thankyou-sub">{t["succ_book_desc"].format(lb["session"])}</div>
            </div>
            """
            st.markdown(thank_html, unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={iban_raw}&color=000000&bgcolor=ffffff"

            card_html = f"""
<div class="alrajhi-card">
    <div class="card-top">
        <div class="bank-title">🏛️ مصرف الراجحي</div>
        <div class="price-pill">65 ر.س</div>
    </div>
    <div style="text-align:center;">
        <div class="qr-container">
            <img src="{qr_url}" alt="Al Rajhi QR" />
        </div>
    </div>
    <div class="card-owner">فارس ربيع بن عواض العصيمي</div>
    <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الحساب (اضغط للنسخ):</div>
    <div class="copy-badge" onclick="navigator.clipboard.writeText('{acc_raw}'); alert('تم نسخ رقم الحساب! 📋');">
        <span>{acc_raw}</span>
        <span>📋</span>
    </div>
    <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الآيبان (اضغط للنسخ):</div>
    <div class="copy-badge" onclick="navigator.clipboard.writeText('{iban_raw}'); alert('تم نسخ الآيبان بنجاح! 📋');">
        <span>{iban_display}</span>
        <span>📋</span>
    </div>
    <div style="margin-top: 8px; padding: 8px 10px; background: rgba(56, 189, 248, 0.08); border-radius: 8px; border: 1px dashed rgba(56, 189, 248, 0.3); display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 0.74em; color: #cbd5e1;">💡 <b>لحفظ المستفيد في تطبيق بنكك:</b></div>
        <div class="copy-badge" style="margin-bottom:0; padding:4px 8px; font-size:0.82em;" onclick="navigator.clipboard.writeText('بادل 99'); alert('تم نسخ اسم المستفيد: بادل 99 📋');">
            <span>بادل 99</span>
            <span>📋</span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:0.72em; color:#64748b; margin-top:8px;">
        <span>سويفت: <b>RJHISARI</b></span>
        <span>⚡ تحويل فوري</span>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {lb['name']}\nالتمرين: {lb['session']} (كورت 1)\nالمبلغ: 65 ر.س\n\nمرفق إشعار التحويل البنكي لحساب كابتن فارس العصيمي. نلتقي في الملعب."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-apple-btn">📲 إرسال إشعار التحويل عبر WhatsApp وتثبيت المقعد</a>', unsafe_allow_html=True)
        else:
            st.info(t["succ_wait"].format(lb.get("wait_pos", 1)))

with tab_rules:
    st.markdown("""
<div class="rules-card">
    <div class="rule-item">
        <span class="rule-icon">⏱️</span>
        <div><b>قبل 4 ساعات.</b> استرجاع كامل أو ترحيل فوري لتمرينك القادم.</div>
    </div>
    <div class="rule-item">
        <span class="rule-icon">⚠️</span>
        <div><b>أقل من 4 ساعات.</b> يُسترجع المبلغ فور تأكيد لاعب بديل من الاحتياط.</div>
    </div>
    <div class="rule-item">
        <span class="rule-icon">⚡</span>
        <div><b>تأكيد فوري.</b> أرسل إشعار التحويل خلال 15 دقيقة لضمان مقعدك.</div>
    </div>
</div>
""", unsafe_allow_html=True)

with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input(t["cancel_phone"])
        can_reason = st.selectbox(t["cancel_reason"], t["reasons"])
        btn_cancel_sub = st.form_submit_button(t["btn_cancel"])

        if btn_cancel_sub:
            clean_cp = clean_and_validate_sa_phone(can_phone_raw)
            if not clean_cp:
                st.error(t["err_fields"])
            else:
                with get_db() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    cur = conn.cursor()
                    cur.execute("SELECT id, name, status, court FROM bookings WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')",
                                (clean_cp, db_session_key))
                    target = cur.fetchone()

                    if target:
                        cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (target[0],))
                        cur.execute("""
                            INSERT INTO cancellations (player_name, player_phone, session_day, court, reason)
                            VALUES (?, ?, ?, ?, ?)
                        """, (target[1], clean_cp, db_session_key, target[3], can_reason))

                        if target[2] == 'confirmed':
                            cur.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_session_key,))
                            wait_player = cur.fetchone()
                            if wait_player:
                                cur.execute("UPDATE bookings SET status='confirmed', court=1 WHERE id=?", (wait_player[0],))
                        
                        conn.commit()
                        st.success(t["succ_cancel"].format(target[1]))
                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error(t["err_cancel"])

# ==========================================
# 7. التشكيلة المباشرة في الملعب (عرض المستوى والولاء)
# ==========================================
st.markdown("---")

def get_level_badge(lvl):
    if lvl == "متقدم":
        return "🔥 متقدم"
    elif lvl == "مبتدئ":
        return "⚪ مبتدئ"
    return "🟢 متوسط"

def render_single_court_roster(title, players):
    slots_html = ""
    for i in range(COURT_CAPACITY):
        if i < len(players):
            p = players[i]
            points = (get_loyalty_score(p[2]) % 7)
            pts_badge = f"⭐ {points}/6" if points < 6 else "🎁 مجاني!"
            pay_icon = "✅" if p[3] == "paid" else "⏳"
            lvl_badge = get_level_badge(p[4])
            slots_html += f'''<div class="slot-box">
                <div class="slot-occupied">🎾 {p[1]}</div>
                <div class="slot-meta">
                    <span class="badge-level">{lvl_badge}</span>
                    <span class="badge-loyalty">{pts_badge}</span>
                    <span>{pay_icon}</span>
                </div>
            </div>'''
        else:
            slots_html += f'<div class="slot-box"><div class="slot-empty">مقعد شاغر ✨</div></div>'
    return f'<div class="padel-court"><div class="court-title">{title} ({len(players)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>'

st.markdown(render_single_court_roster(t["court1"], c1), unsafe_allow_html=True)

if waitlist:
    st.caption("📋 **أولوية الاحتياط:** " + " • ".join([f"{idx+1}. {w[1]}" for idx, w in enumerate(waitlist)]))

# ==========================================
# 8. لوحة الإدارة وتصدير البيانات
# ==========================================
with st.expander("⚙️ لوحة الإدارة والبيانات", expanded=False):
    pin_input = st.text_input(t["admin_pin"], type="password", help="لوحة مشفرة ومحمية من التخمين")
    
    if verify_admin_security(pin_input):
        st.success("تم تأكيد الهوية والصلاحيات 👑")
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT reason, COUNT(*) as cnt FROM cancellations GROUP BY reason ORDER BY cnt DESC")
            reasons_data = cur.fetchall()
        
        if reasons_data:
            st.markdown("#### 📊 أسباب الاعتذار:")
            for r, cnt in reasons_data:
                st.caption(f"• **{r}:** {cnt} لاعبين")

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_day, court, name, phone, 
                       COALESCE(level, 'متوسط'), 
                       COALESCE(payment_status, 'pending'), 
                       COALESCE(attendance, 'unknown'), 
                       created_at
                FROM bookings
                ORDER BY session_day DESC, id ASC
            """)
            raw_data = cur.fetchall()

        if raw_data:
            csv_buf = io.StringIO()
            csv_buf.write('\ufeff')
            writer = csv.writer(csv_buf)
            writer.writerow(["تاريخ التمرين", "الملعب", "اسم اللاعب", "رقم الجوال", "المستوى", "حالة الدفع", "الحضور الفعلي", "وقت التسجيل"])
            for row in raw_data:
                writer.writerow(row)
                
            st.download_button(
                t["export_btn"],
                csv_buf.getvalue().encode('utf-8-sig'),
                f"padel_data_export_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
