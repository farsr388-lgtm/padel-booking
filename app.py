import streamlit as st
import sqlite3
import io
import csv
import re
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
        "hero_sub": "تمرين {}. اللعب التشاركي الذكي.",
        "contrast_banner": "⚡ حجز مؤكد في ثوانٍ • 6 لاعبين لكل ملعب • تمرينك الـ 7 مجاناً",
        "promo_badge": "✨ برنامج الوفاء: العب 6 تمارين واحصل على السابع مجاناً.",
        "price_tag": "35 ر.س",
        "price_desc": "رسوم المشاركة لتمرين اليوم",
        "time_str": "⏰ ٩:٣٠ م – ١١:٠٠ م | كورت 1 & 2 (السعة: 12 لاعب)",
        "court1": "🏟️ كورت 1",
        "court2": "🏟️ كورت 2",
        "tab_book": "⚡ حجز مقعد",
        "tab_cancel": "❌ اعتذار / تعديل",
        "name_lbl": "الاسم الكامل",
        "phone_lbl": "رقم الجوال (05xxxxxxxx)",
        "level_lbl": "مستوى اللعب",
        "levels": ["متوسط", "متقدم", "مبتدئ"],
        "btn_book": "تأكيد الانضمام 🚀",
        "err_fields": "يرجى كتابة الاسم ورقم جوال سعودي صحيح يبدأ بـ 05.",
        "err_duplicate": "هذا الرقم مسجل بالفعل في تمرين اليوم!",
        "err_spam": "تم رفض الطلب للاشتباه في نشاط غير معتاد.",
        "succ_book": "أهلاً بك يا كابتن {}! تم تثبيت مقعدك في {}.",
        "succ_wait": "اكتملت المقاعد الأساسية (12 لاعب). تم إدراجك في صدارة قائمة الاحتياط برقم ({}).",
        "cancel_phone": "رقم الجوال المسجل:",
        "cancel_reason": "سبب الاعتذار:",
        "reasons": [
            "تعارض في الجدول / ارتباط مفاجئ",
            "إجهاد بدني / إصابة",
            "صعوبة في المواصلات",
            "انضممت لمجموعة أخرى",
            "ظرف شخصي طارئ"
        ],
        "btn_cancel": "تأكيد الاعتذار وإتاحة المقعد للبديل",
        "succ_cancel": "تم قبول اعتذارك يا كابتن {}. نتطلع لرؤيتك في التمارين القادمة.",
        "err_cancel": "لم يتم العثور على حجز مؤكد مرتبط بهذا الرقم في تمرين اليوم.",
        "admin_pin": "رمز الدخول السري:",
        "export_btn": "📥 تصدير السجل وقاعدة البيانات (Excel/CSV)"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "brand": "Padel 99.",
        "hero_sub": "{} Session. Shared community padel.",
        "contrast_banner": "⚡ Instant Booking • 6 Players/Court • 7th Session Free",
        "promo_badge": "✨ Loyalty Pass: Play 6 sessions, get the 7th free.",
        "price_tag": "35 SAR",
        "price_desc": "Session fee for today",
        "time_str": "⏰ 9:30 PM – 11:00 PM | Courts 1 & 2 (12 Max Slots)",
        "court1": "🏟️ Court 1",
        "court2": "🏟️ Court 2",
        "tab_book": "⚡ Reserve Slot",
        "tab_cancel": "❌ Cancel / Manage",
        "name_lbl": "Full Name",
        "phone_lbl": "Mobile (05xxxxxxxx)",
        "level_lbl": "Skill Level",
        "levels": ["Intermediate", "Advanced", "Beginner"],
        "btn_book": "Join Roster 🚀",
        "err_fields": "Please provide a valid name and Saudi mobile number (05xxxxxxxx).",
        "err_duplicate": "This phone number is already registered for today's session!",
        "err_spam": "Submission rejected due to suspected automated activity.",
        "succ_book": "Welcome Captain {}! Spot secured in {}.",
        "succ_wait": "Main roster full (12 players). You are #{} on the waitlist.",
        "cancel_phone": "Registered Mobile:",
        "cancel_reason": "Cancellation Reason:",
        "reasons": [
            "Schedule conflict",
            "Physical fatigue / Injury",
            "Transportation issue",
            "Joined another match",
            "Personal emergency"
        ],
        "btn_cancel": "Release Spot to Next Player",
        "succ_cancel": "Spot cancelled for Captain {}. See you next time.",
        "err_cancel": "No active booking found for this number today.",
        "admin_pin": "Admin Passcode:",
        "export_btn": "📥 Export Timesheet Data (Excel/CSV)"
    }
}

col_lang1, col_lang2 = st.columns([5, 1])
with col_lang2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# ==========================================
# 2. الهيكل البصري وبطاقة الدفع الفاخرة (CSS & Animations)
# ==========================================
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
* {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}
.block-container {{ padding: 0.8rem 0.5rem 1rem 0.5rem !important; max-width: 580px !important; }}
.stAppHeader {{ display: none; }}

/* عناصر الهوية */
.hero-header {{ font-size: 1.6em; font-weight: 900; letter-spacing: -0.5px; color: #f4f4f5; margin: 0; }}
.hero-sub {{ font-size: 0.9em; color: #a1a1aa; margin-bottom: 6px; }}
.contrast-pill {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 4px 8px; font-size: 0.75em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }}
.promo-badge {{ background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.75em; margin-bottom: 4px; }}

/* بطاقة الدفع الرقمية الفاخرة (Fintech Luxury Card) */
.wallet-card {{
    background: linear-gradient(135deg, #18181b 0%, #09090b 100%);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 16px;
    padding: 16px;
    margin: 12px 0;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(56, 189, 248, 0.1);
    position: relative;
    overflow: hidden;
}}
.wallet-card::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.05) 0%, transparent 70%);
    pointer-events: none;
}}
.wallet-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 10px;
    margin-bottom: 12px;
}}
.wallet-bank {{
    display: flex;
    align-items: center;
    gap: 6px;
    color: #f4f4f5;
    font-weight: 800;
    font-size: 0.95em;
}}
.wallet-price {{
    background: #10b981;
    color: #022c22;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 900;
    font-size: 0.85em;
    letter-spacing: 0.5px;
}}
.wallet-body {{
    text-align: center;
    margin: 10px 0;
}}
.iban-display-box {{
    background: #0f172a;
    border: 1.5px solid #0284c7;
    border-radius: 10px;
    padding: 12px 8px;
    margin: 8px 0;
    cursor: pointer;
    transition: all 0.2s ease;
}}
.iban-display-box:active {{
    transform: scale(0.98);
    border-color: #38bdf8;
}}
.iban-number {{
    font-family: 'Courier New', Courier, monospace;
    color: #38bdf8;
    font-weight: 800;
    font-size: 1.05em;
    letter-spacing: 1px;
    user-select: all;
    -webkit-user-select: all;
}}
.wallet-meta {{
    display: flex;
    justify-content: space-between;
    color: #a1a1aa;
    font-size: 0.75em;
    margin-top: 8px;
    padding: 0 4px;
}}
.wallet-steps {{
    display: flex;
    justify-content: space-around;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    padding: 8px 4px;
    margin-top: 12px;
    font-size: 0.72em;
    color: #cbd5e1;
    font-weight: 600;
}}

/* أزرار الإجراء السريع */
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
    transition: transform 0.15s ease;
}}
.wa-apple-btn:hover {{ transform: translateY(-1px); }}

/* الملاعب */
.padel-court {{ background: radial-gradient(circle, #064e3b 0%, #022c22 100%); border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 10px; padding: 8px; margin-bottom: 6px; }}
.court-title {{ text-align: center; color: #a7f3d0; font-weight: 800; font-size: 0.85em; margin-bottom: 6px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 4px; }}
.court-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }}
.slot-box {{ background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 4px 6px; text-align: center; min-height: 42px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
.slot-occupied {{ color: #f4f4f5; font-weight: 700; font-size: 0.78em; line-height: 1.1; }}
.slot-meta {{ font-size: 0.68em; margin-top: 2px; }}
.slot-empty {{ color: #52525b; font-size: 0.72em; }}
.badge-loyalty {{ background-color: #1e3a8a; color: #93c5fd; padding: 1px 3px; border-radius: 3px; font-size: 0.72em; font-weight: 700; }}

/* إخفاء مصيدة البوت */
div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) {{ display: none !important; }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 3. محرك البيانات المتقدم (WAL + Indexes)
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
# 4. دوال التحقق والحساب
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
    c.execute("SELECT id, name, phone, payment_status, level FROM bookings WHERE session_day=? AND court=2 AND status='confirmed' ORDER BY id ASC LIMIT 6", (db_session_key,))
    c2 = c.fetchall()
    c.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (db_session_key,))
    waitlist = c.fetchall()

total_booked = len(c1) + len(c2)

# ==========================================
# 6. واجهة المستخدم والتسجيل
# ==========================================
st.markdown(f"<div class='hero-header'>{t['brand']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>{t['hero_sub'].format(display_session)}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='contrast-pill'>{t['contrast_banner']}</div>", unsafe_allow_html=True)
st.markdown(f'<div class="promo-badge">{t["promo_badge"]}</div>', unsafe_allow_html=True)
st.caption(f"{t['time_str']} • <b>المؤكدين: {total_booked}/12</b>", unsafe_allow_html=True)

tab_book, tab_cancel = st.tabs([t["tab_book"], t["tab_cancel"]])

with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([3, 2])
        with c_in1:
            f_name = st.text_input(t["name_lbl"])
        with c_in2:
            f_phone = st.text_input(t["phone_lbl"], placeholder="05xxxxxxxx")
        
        f_level = st.selectbox(t["level_lbl"], t["levels"])
        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        
        btn_submit = st.form_submit_button(t["btn_book"])

        if btn_submit:
            if honeypot_val:
                st.error(t["err_spam"])
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 3 or not clean_phone:
                st.error(t["err_fields"])
            elif check_active_booking(clean_phone, db_session_key):
                st.warning(t["err_duplicate"])
            else:
                with get_db() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    cur = conn.cursor()
                    
                    cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND court=1 AND status='confirmed'", (db_session_key,))
                    cur_c1 = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND court=2 AND status='confirmed'", (db_session_key,))
                    cur_c2 = cur.fetchone()[0]

                    if cur_c1 < COURT_CAPACITY and cur_c2 < COURT_CAPACITY:
                        target_court = 1 if cur_c1 <= cur_c2 else 2
                        status_val = 'confirmed'
                    elif cur_c1 < COURT_CAPACITY:
                        target_court = 1
                        status_val = 'confirmed'
                    elif cur_c2 < COURT_CAPACITY:
                        target_court = 2
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
                    "court": f"كورت {target_court}",
                    "status": status_val,
                    "wait_pos": wait_pos,
                    "session": display_session
                }
                st.rerun()

    # بطاقة تأكيد الحجز والدفع الفاخرة
    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        if lb["status"] == "confirmed":
            st.success(t["succ_book"].format(lb["name"], lb["court"]))
            
            # بطاقة Apple Wallet التفاعلية للتحويل
            iban_raw = "SA9380000222608016013114"
            iban_formatted = "SA93 8000 0222 6080 1601 3114"
            
            st.markdown(f"""
            <div class="wallet-card">
                <div class="wallet-header">
                    <div class="wallet-bank">
                        <span>🏛️</span>
                        <span>مصرف الراجحي</span>
                    </div>
                    <div class="wallet-price">{t['price_tag']}</div>
                </div>
                
                <div class="wallet-body">
                    <div style="color: #a1a1aa; font-size: 0.78em; margin-bottom: 4px;">اضغط على الآيبان لنسخه فوراً:</div>
                    <div class="iban-display-box" onclick="navigator.clipboard.writeText('{iban_raw}'); alert('تم نسخ رقم الآيبان بنجاح! 📋');">
                        <div class="iban-number">{iban_formatted}</div>
                    </div>
                </div>

                <div class="wallet-meta">
                    <span>👤 المستفيد: <b>Padel 99 Community</b></span>
                    <span>⚡ تحويل فوري</span>
                </div>

                <div class="wallet-steps">
                    <span>1️⃣ انسخ الآيبان 📋</span>
                    <span>➔</span>
                    <span>2️⃣ حوّل من بنكك 💳</span>
                    <span>➔</span>
                    <span>3️⃣ أرسل الإشعار 📲</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # رسالة الواتساب الجاهزة
            wa_msg = f"🎾 تأكيد حجز مقعد - بادل 99\n\n👤 الكابتن: {lb['name']}\n📅 التمرين: {lb['session']}\n🏟️ الملعب: {lb['court']}\n💵 المبلغ: 35 ر.س\n\n⚡ مرفق صورة إشعار التحويل البنكي لإتمام التثبيت."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-apple-btn">📲 إرسال إشعار التحويل عبر WhatsApp وتثبيت المقعد</a>', unsafe_allow_html=True)
        else:
            st.info(t["succ_wait"].format(lb.get("wait_pos", 1)))

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

                        # تصعيد قائمة الانتظار
                        if target[2] == 'confirmed':
                            cur.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_session_key,))
                            wait_player = cur.fetchone()
                            if wait_player:
                                cur.execute("UPDATE bookings SET status='confirmed', court=? WHERE id=?", (target[3], wait_player[0]))
                        
                        conn.commit()
                        st.success(t["succ_cancel"].format(target[1]))
                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error(t["err_cancel"])

# ==========================================
# 7. التشكيلة المباشرة في الملاعب
# ==========================================
st.markdown("---")
col_c1, col_c2 = st.columns(2)

def render_court_roster(title, players):
    slots_html = ""
    for i in range(COURT_CAPACITY):
        if i < len(players):
            p = players[i]
            points = (get_loyalty_score(p[2]) % 7)
            pts_badge = f"⭐ {points}/6" if points < 6 else "🎁 مجاني!"
            pay_icon = "✅" if p[3] == "paid" else "⏳"
            slots_html += f'<div class="slot-box"><div class="slot-occupied">🎾 {p[1]}</div><div class="slot-meta"><span class="badge-loyalty">{pts_badge}</span> {pay_icon}</div></div>'
        else:
            slots_html += f'<div class="slot-box"><div class="slot-empty">مقعد {i+1} شاغر ✨</div></div>'
    return f'<div class="padel-court"><div class="court-title">{title} ({len(players)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>'

with col_c1:
    st.markdown(render_court_roster(t["court1"], c1), unsafe_allow_html=True)
with col_c2:
    st.markdown(render_court_roster(t["court2"], c2), unsafe_allow_html=True)

if waitlist:
    st.caption("📋 **أولوية الاحتياط:** " + " • ".join([f"{idx+1}. {w[1]}" for idx, w in enumerate(waitlist)]))

# ==========================================
# 8. لوحة الإدارة وتصدير البيانات
# ==========================================
with st.expander("⚙️ لوحة الإدارة والبيانات", expanded=False):
    pin = st.text_input(t["admin_pin"], type="password")
    if pin == "9900":
        st.success("تم تسجيل الدخول بصلاحيات الإدارة 👑")
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT reason, COUNT(*) as cnt FROM cancellations GROUP BY reason ORDER BY cnt DESC")
            reasons_data = cur.fetchall()
        
        if reasons_data:
            st.markdown("#### 📊 تحليل أسباب الاعتذار:")
            for r, cnt in reasons_data:
                st.caption(f"• **{r}:** {cnt} لاعبين")

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_day, court, name, phone, level, payment_status, attendance, created_at
                FROM bookings
                ORDER BY session_day DESC, court ASC, id ASC
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
