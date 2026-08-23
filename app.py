import streamlit as st
import sqlite3
import io
import csv
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة واللغات (20% UI -> 80% Speed)
# ==========================================
st.set_page_config(
    page_title="Padel 99 | بادل 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# دالة توحيد وتنظيف رقم الجوال (تقضي على 80% من أخطاء الإدخال)
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
        "title": "🎾 تمرين {} — قروب 99",
        "promo_badge": "🔥 عداد الوفاء: العب 6 تمارين والـ 7 مجاناً بالكامل! 🎁",
        "discount_badge": "⚡ عرض خاص: خصم 20% على قطة تمرين اليوم! 🏷️",
        "time_str": "⏰ ٩:٣٠ م حتى ١١:٠٠ م | كورت 1 & 2 (12 مقعد)",
        "privacy_note": "🔒 خصوصيتك محفوظة: رقم جوالك يُستخدم للتحقق ونقاط وفائك واسترجاع المبالغ فقط.",
        "court1": "🏟️ كورت 1",
        "court2": "🏟️ كورت 2",
        "tab_book": "⚡ حجز مقعد فوري",
        "tab_cancel": "❌ اعتذار / إلغاء",
        "name_lbl": "اسم اللاعب:",
        "phone_lbl": "الجوال (05xxxxxxx):",
        "level_lbl": "المستوى:",
        "levels": ["متوسط", "متقدم", "مبتدئ"],
        "btn_book": "🚀 تأكيد الحجز الفوري",
        "err_fields": "فضلاً أدخل الاسم ورقم الجوال بالشكل الصحيح.",
        "succ_book": "كفو يا كابتن {}! تم تثبيت مقعدك في {}.",
        "succ_wait": "اكتملت المقاعد! تم تسجيلك في قائمة الاحتياط.",
        "cancel_phone": "رقم الجوال المسجل:",
        "cancel_reason": "سبب الاعتذار الرئيسي:",
        "reasons": [
            "السعر / قيمة القطة غير مناسبة",
            "مكان أو جودة الملعب غير مريحة",
            "لقيت حجز في ملعب أفضل أو أقرب",
            "صديقي أو مجموعتي يلعبون في مكان آخر",
            "مستوى التمرين غير متكافئ معي",
            "تعارض في الوقت / ارتباط مفاجئ",
            "إجهاد بدني أو إصابة عضلية",
            "بعد المسافة / صعوبة مواصلات",
            "أخرى (ظرف شخصي طارئ)"
        ],
        "btn_cancel": "تأكيد الاعتذار وتفريغ المقعد",
        "succ_cancel": "تم قبول اعتذارك يا كابتن {} وتفريغ المقعد.",
        "succ_cancel_refund": "تم قبول اعتذارك يا كابتن {} وتفريغ المقعد. (تم تسجيل طلب استرجاع المبلغ للكابتن ✅).",
        "err_cancel": "لم يتم العثور على حجز مؤكد بهذا الرقم في تمرين اليوم.",
        "admin_pin": "الرمز السري:",
        "export_btn": "📥 تحميل تايم شيت وسجل الاسترجاعات (Excel)",
        "wa_msg_conf": "🎾 تم تأكيد حجز مقعدي ({}) في تمرين {} - {}! مرفق إشعار القطة ⚡",
        "wa_msg_wait": "🎾 تم تسجيل اسمي ({}) في احتياط تمرين {} ⏳"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "title": "🎾 {} Session — Group 99",
        "promo_badge": "🔥 Loyalty Counter: Play 6 sessions, get the 7th FREE! 🎁",
        "discount_badge": "⚡ Special Offer: 20% OFF today's session share! 🏷️",
        "time_str": "⏰ 9:30 PM until 11:00 PM | Courts 1 & 2 (12 Spots)",
        "privacy_note": "🔒 Privacy Protected: Phone used solely for verification, loyalty points & refunds.",
        "court1": "🏟️ Court 1",
        "court2": "🏟️ Court 2",
        "tab_book": "⚡ Quick Book",
        "tab_cancel": "❌ Cancel",
        "name_lbl": "Player Name:",
        "phone_lbl": "Mobile (05xxxxxxx):",
        "level_lbl": "Skill Level:",
        "levels": ["Intermediate", "Advanced", "Beginner"],
        "btn_book": "🚀 Confirm Slot",
        "err_fields": "Please enter a valid name and phone number.",
        "succ_book": "Confirmed for Captain {} in {}!",
        "succ_wait": "Courts full! Added to waitlist.",
        "cancel_phone": "Registered Mobile:",
        "cancel_reason": "Cancellation Reason:",
        "reasons": [
            "Price not suitable",
            "Venue quality uncomfortable",
            "Found a better / closer venue",
            "Group playing elsewhere",
            "Skill level mismatch",
            "Schedule conflict / Work",
            "Fatigue / Injury",
            "Distance issue",
            "Other"
        ],
        "btn_cancel": "Confirm Cancellation",
        "succ_cancel": "Cancelled for Captain {}. Spot released.",
        "succ_cancel_refund": "Cancelled for Captain {}. (Refund logged for processing ✅).",
        "err_cancel": "No confirmed booking found for this number today.",
        "admin_pin": "Admin PIN:",
        "export_btn": "📥 Download Timesheet & Refunds (Excel)",
        "wa_msg_conf": "🎾 Confirmed ({}) for {} - {}! Receipt attached ⚡",
        "wa_msg_wait": "🎾 Added ({}) to waitlist for {} ⏳"
    }
}

col_t1, col_t2 = st.columns([5, 1])
with col_t2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# ==========================================
# 2. التنسيق البصري الفائق (Zero Padding & Max Compactness)
# ==========================================
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap');
* {{ font-family: 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}

.block-container {{
    padding-top: 0.6rem !important;
    padding-bottom: 0.6rem !important;
    padding-left: 0.4rem !important;
    padding-right: 0.4rem !important;
    max-width: 580px !important;
}}
.stAppHeader {{ display: none; }}

.promo-box {{
    background: linear-gradient(90deg, #1e3a8a 0%, #1e40af 100%);
    border: 1px solid #3b82f6;
    border-radius: 6px;
    padding: 3px 6px;
    text-align: center;
    color: #eff6ff;
    font-weight: 800;
    font-size: 0.78em;
    margin-bottom: 2px;
}}
.discount-box {{
    background: linear-gradient(90deg, #b45309 0%, #d97706 100%);
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 3px 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 800;
    font-size: 0.78em;
    margin-bottom: 3px;
}}
.privacy-badge {{
    font-size: 0.68em;
    color: #94a3b8;
    text-align: center;
    margin-top: 2px;
    margin-bottom: 4px;
}}

div[data-testid="stForm"] {{
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 6px 8px !important;
    background: #0f172a;
    margin-top: 2px !important;
    margin-bottom: 4px !important;
}}
.stTextInput, .stSelectbox {{
    margin-bottom: -12px !important;
}}
div[data-baseweb="input"] > div {{
    min-height: 34px !important;
    height: 34px !important;
}}
.stButton>button {{
    width: 100%;
    border-radius: 6px;
    font-weight: 800;
    height: 2.5em;
    font-size: 0.95em;
    margin-top: 4px !important;
}}
.wa-btn {{
    display: block;
    width: 100%;
    background-color: #25D366;
    color: white !important;
    text-align: center;
    padding: 6px;
    border-radius: 6px;
    font-weight: 800;
    text-decoration: none;
    margin-top: 3px;
    margin-bottom: 4px;
    font-size: 0.85em;
}}

.padel-court {{
    background: radial-gradient(circle, #064e3b 0%, #022c22 100%);
    border: 1.5px solid #10b981;
    border-radius: 8px;
    padding: 4px;
    margin-bottom: 2px;
}}
.court-title {{
    text-align: center;
    color: #a7f3d0;
    font-weight: 800;
    font-size: 0.8em;
    margin-bottom: 3px;
    border-bottom: 1px dashed #10b981;
    padding-bottom: 1px;
}}
.court-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3px;
}}
.slot-box {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 2px 4px;
    text-align: center;
    min-height: 36px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}}
.slot-occupied {{ color: #f8fafc; font-weight: 700; font-size: 0.75em; line-height: 1.1; }}
.slot-meta {{ font-size: 0.65em; margin-top: 1px; }}
.slot-empty {{ color: #64748b; font-size: 0.68em; }}
.badge-loyalty {{ background-color: #1e3a8a; color: #93c5fd; padding: 0px 2px; border-radius: 2px; font-size: 0.7em; font-weight: 700; }}
.refund-alert-box {{
    background: #451a03;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 6px 8px;
    margin-bottom: 5px;
    color: #fef3c7;
    font-size: 0.85em;
}}
</style>""", unsafe_allow_html=True)

# ==========================================
# 3. محرك قاعدة البيانات (High Concurrency & WAL)
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
    
    return label_ar, label_en, db_key

sess_ar, sess_en, db_session_key = get_next_session()
display_session = sess_ar if l_code == "ar" else sess_en

COURT_CAPACITY = 6
is_promo_active = (get_setting("promo_20_active", "0") == "1")

# جلب بيانات الملاعب لتمرين اليوم
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
# 5. الترويسة والعداد فوق أولاً
# ==========================================
st.markdown(f"<h3 style='margin:0; font-size:1.15em;'>{t['title'].format(display_session)}</h3>", unsafe_allow_html=True)
st.markdown(f'<div class="promo-box">{t["promo_badge"]}</div>', unsafe_allow_html=True)

if is_promo_active:
    st.markdown(f'<div class="discount-box">{t["discount_badge"]}</div>', unsafe_allow_html=True)

st.caption(f"{t['time_str']} • <b>المسجلين: {total_booked}/12</b>", unsafe_allow_html=True)

# ==========================================
# 6. التسجيل أولاً (مباشرة بالأعلى لتقليل الاحتكاك)
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

    if "recent_book" in st.session_state:
        b = st.session_state["recent_book"]
        if b["status"] == "confirmed":
            st.success(t["succ_book"].format(b["name"], b["court"]))
            msg = t["wa_msg_conf"].format(b["name"], b["session"], b["court"])
        else:
            st.info(t["succ_wait"])
            msg = t["wa_msg_wait"].format(b["name"], b["session"])

        wa_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال التأكيد في قروب الواتساب</a>', unsafe_allow_html=True)

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
# 7. العين والتشكيلة المباشرة (في الأسفل)
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
    st.caption("📋 **قائمة الاحتياط:** " + " • ".join([f"{w[1]}" for w in waitlist]))

# ==========================================
# 8. لوحة الإدارة (20% جهد تشغيلي -> 80% تحكم كامل)
# ==========================================
with st.expander("⚙️", expanded=False):
    pin = st.text_input(t["admin_pin"], type="password", key="adm_pin")
    if pin == "9900":
        st.success("لوحة تحكم الكابتن 👑")
        
        # 1. إدارة استرجاع المبالغ (دفعوا واعتذروا)
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