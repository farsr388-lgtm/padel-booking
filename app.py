import streamlit as st
import sqlite3
import io
import csv
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة واللغات
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
        "title": "🎾 تمرين {} — قروب 99",
        "promo_badge": "🔥 عرض الوفاء: العب 6 تمارين والـ 7 مجاناً بالكامل! 🎁",
        "time_str": "⏰ 9:30 م - 11:00 م | كورت 1 & كورت 2 (12 مقعد)",
        "court1": "🏟️ كورت 1",
        "court2": "🏟️ كورت 2",
        "tab_book": "⚡ حجز مقعد فوري",
        "tab_cancel": "❌ اعتذار / إلغاء",
        "name_lbl": "اسم اللاعب:",
        "phone_lbl": "رقم الجوال (05xxxxxxx):",
        "btn_book": "🚀 تأكيد الحجز الفوري",
        "err_fields": "فضلاً أدخل الاسم ورقم الجوال بالشكل الصحيح.",
        "succ_book": "كفو يا كابتن {}! تم تثبيت مقعدك في {}.",
        "succ_wait": "اكتملت المقاعد الأساسية! تم تسجيلك في قائمة الاحتياط.",
        "cancel_phone": "رقم الجوال المسجل به الحجز:",
        "cancel_reason": "سبب الاعتذار الرئيسي:",
        "reasons": [
            "السعر غير مناسب",
            "لقيت مكان / ملعب أفضل",
            "صديقي نصحني بملعب آخر",
            "تعارض في الوقت / ظرف طارئ",
            "إجهاد بدني / إصابة",
            "بعد المكان / صعوبة مواصلات",
            "أخرى"
        ],
        "btn_cancel": "تأكيد الاعتذار وتفريغ المقعد",
        "succ_cancel": "تم قبول اعتذارك يا كابتن {} وتفريغ المقعد.",
        "err_cancel": "لم يتم العثور على حجز مؤكد بهذا الرقم.",
        "admin_pin": "الرمز السري:",
        "export_btn": "📥 تحميل تايم شيت الحضور (Excel)",
        "wa_msg_conf": "🎾 تم تأكيد حجز مقعدي ({}) في تمرين {} - {}! مرفق إشعار القطة ⚡",
        "wa_msg_wait": "🎾 تم تسجيل اسمي ({}) في احتياط تمرين {} ⏳"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "title": "🎾 {} Session — Group 99",
        "promo_badge": "🔥 Loyalty Reward: Play 6 sessions, get the 7th FREE! 🎁",
        "time_str": "⏰ 21:30 - 23:00 | Court 1 & Court 2 (12 Spots)",
        "court1": "🏟️ Court 1",
        "court2": "🏟️ Court 2",
        "tab_book": "⚡ Quick Book",
        "tab_cancel": "❌ Cancel Booking",
        "name_lbl": "Player Name:",
        "phone_lbl": "Mobile (05xxxxxxx):",
        "btn_book": "🚀 Confirm Booking",
        "err_fields": "Please enter a valid name and phone number.",
        "succ_book": "Confirmed for Captain {} in {}!",
        "succ_wait": "Main spots full! Added to the waitlist.",
        "cancel_phone": "Registered Mobile Number:",
        "cancel_reason": "Cancellation Reason:",
        "reasons": [
            "Price not suitable",
            "Found a better court/venue",
            "Friend suggested another place",
            "Schedule conflict / Sudden event",
            "Fatigue / Injury",
            "Distance / Transportation issue",
            "Other"
        ],
        "btn_cancel": "Confirm Cancellation",
        "succ_cancel": "Cancelled for Captain {}. Spot released.",
        "err_cancel": "No confirmed booking found for this number.",
        "admin_pin": "Admin PIN:",
        "export_btn": "📥 Download Timesheet (Excel)",
        "wa_msg_conf": "🎾 Slot confirmed for ({}) on {} - {}! Receipt attached ⚡",
        "wa_msg_wait": "🎾 Added ({}) to waitlist for {} ⏳"
    }
}

col_t1, col_t2 = st.columns([5, 1])
with col_t2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# ==========================================
# 2. الهوية البصرية وتصميم شاشات الجوال السريعة
# ==========================================
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap');
* {{ font-family: 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}
.promo-box {{
    background: linear-gradient(90deg, #1e3a8a 0%, #1e40af 100%);
    border: 1px solid #3b82f6;
    border-radius: 8px;
    padding: 6px 12px;
    text-align: center;
    color: #eff6ff;
    font-weight: 800;
    font-size: 0.85em;
    margin-bottom: 10px;
}}
.padel-court {{
    background: radial-gradient(circle, #064e3b 0%, #022c22 100%);
    border: 2px solid #10b981;
    border-radius: 10px;
    padding: 8px;
    margin-bottom: 8px;
}}
.court-title {{
    text-align: center;
    color: #a7f3d0;
    font-weight: 800;
    font-size: 0.95em;
    margin-bottom: 6px;
    border-bottom: 1px dashed #10b981;
    padding-bottom: 3px;
}}
.court-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
}}
.slot-box {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 6px;
    text-align: center;
    min-height: 48px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}}
.slot-occupied {{ color: #f8fafc; font-weight: 700; font-size: 0.82em; }}
.slot-meta {{ font-size: 0.7em; margin-top: 1px; }}
.slot-empty {{ color: #64748b; font-size: 0.72em; }}
.badge-loyalty {{ background-color: #1e3a8a; color: #93c5fd; padding: 1px 4px; border-radius: 3px; font-size: 0.75em; font-weight: 700; }}
.stButton>button {{ width: 100%; border-radius: 8px; font-weight: 800; height: 3em; font-size: 1em; }}
.wa-btn {{
    display: block;
    width: 100%;
    background-color: #25D366;
    color: white !important;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    font-weight: 800;
    text-decoration: none;
    margin-top: 6px;
}}
</style>""", unsafe_allow_html=True)

# ==========================================
# 3. حساب موعد التمرين القادم آلياً
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

# ==========================================
# 4. قاعدة البيانات وحساب نقاط الوفاء
# ==========================================
DB_FILE = "group99_padel.db"

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

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
                level TEXT DEFAULT 'عام',
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
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

def get_loyalty_score(norm_phone):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT session_day) FROM bookings WHERE phone=? AND status='confirmed'", (norm_phone,))
        res = cur.fetchone()
        return res[0] if res else 0

# ==========================================
# 5. عرض التشكيلة المباشرة (6 لاعبين لكل كورت)
# ==========================================
st.title(t["title"].format(display_session))
st.markdown(f'<div class="promo-box">{t["promo_badge"]}</div>', unsafe_allow_html=True)
st.caption(t["time_str"])

COURT_CAPACITY = 6  # 6 لاعبين لكل كورت

with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT id, name, phone, payment_status FROM bookings WHERE session_day=? AND court=1 AND status='confirmed' ORDER BY id ASC LIMIT 6", (db_session_key,))
    c1 = c.fetchall()
    c.execute("SELECT id, name, phone, payment_status FROM bookings WHERE session_day=? AND court=2 AND status='confirmed' ORDER BY id ASC LIMIT 6", (db_session_key,))
    c2 = c.fetchall()
    c.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (db_session_key,))
    waitlist = c.fetchall()

total_booked = len(c1) + len(c2)
st.markdown(f"**👥 تشكيلة الكورتين المباشرة ({total_booked}/12)**")

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

st.divider()

# ==========================================
# 6. الحجز السريع في حقلين فقط (الاسم + الجوال)
# ==========================================
tab_book, tab_cancel = st.tabs([t["tab_book"], t["tab_cancel"]])

with tab_book:
    with st.form("book_form", clear_on_submit=False):
        f_name = st.text_input(t["name_lbl"])
        f_phone = st.text_input(t["phone_lbl"])
        btn_book = st.form_submit_button(t["btn_book"])

        if btn_book:
            clean_name = f_name.strip()
            clean_p = normalize_phone(f_phone)

            if len(clean_name) < 2 or len(clean_p) < 8:
                st.error(t["err_fields"])
            else:
                # توزيع تلقائي سلس: كورت 1 أولاً حتى 6، ثم كورت 2 حتى 6
                if len(c1) < COURT_CAPACITY:
                    target_court = 1
                    status_val = 'confirmed'
                elif len(c2) < COURT_CAPACITY:
                    target_court = 2
                    status_val = 'confirmed'
                else:
                    target_court = 1
                    status_val = 'waitlist'

                with get_db() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO bookings (name, phone, session_day, court, status) VALUES (?, ?, ?, ?, ?)",
                                (clean_name, clean_p, db_session_key, target_court, status_val))
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

# --- تبويب الاعتذار مع تفريغ المقعد والترقية الفورية ---
with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input(t["cancel_phone"])
        can_reason = st.selectbox(t["cancel_reason"], t["reasons"])
        btn_cancel = st.form_submit_button(t["btn_cancel"])

        if btn_cancel:
            clean_cp = normalize_phone(can_phone_raw)
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, status, court FROM bookings WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')",
                            (clean_cp, db_session_key))
                target = cur.fetchone()

                if target:
                    cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (target[0],))
                    cur.execute("INSERT INTO cancellations (player_name, player_phone, session_day, court, reason) VALUES (?, ?, ?, ?, ?)",
                                (target[1], clean_cp, db_session_key, target[3], can_reason))
                    
                    # ترقية أول احتياط لكورت اللاعب المعتذر
                    if target[2] == 'confirmed':
                        cur.execute("SELECT id FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_session_key,))
                        first_wait = cur.fetchone()
                        if first_wait:
                            cur.execute("UPDATE bookings SET status='confirmed', court=? WHERE id=?", (target[3], first_wait[0]))
                    conn.commit()

                    st.success(t["succ_cancel"].format(target[1]))
                    if "recent_book" in st.session_state:
                        del st.session_state["recent_book"]
                    st.rerun()
                else:
                    st.error(t["err_cancel"])

# ==========================================
# 7. لوحة الإدارة (إحصائيات فورية + تصدير إكسل + تبديل)
# ==========================================
st.write("")
with st.expander("⚙️", expanded=False):
    pin = st.text_input(t["admin_pin"], type="password", key="adm_pin")
    if pin == "9900":
        st.success("لوحة تحكم الكابتن 👑")

        paid_count = len([p for p in (c1 + c2) if p[3] == 'paid'])
        m1, m2, m3 = st.columns(3)
        m1.metric("الأساسيين", f"{total_booked}/12")
        m2.metric("تم الدفع", f"{paid_count}/{total_booked}")
        m3.metric("الاحتياط", len(waitlist))

        st.divider()

        # تصدير التايم شيت لإكسل
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_day, court, name, phone,
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
            writer.writerow(["تاريخ التمرين", "الكورت", "الاسم", "رقم الجوال", "حالة القطة", "وقت التسجيل"])
            for r in raw_rows:
                formatted_phone = f'0{r[3]}' if not str(r[3]).startswith('0') else str(r[3])
                writer.writerow([r[0], f"كورت {r[1]}", r[2], f'="{formatted_phone}"', r[4], r[5]])
            
            st.download_button(t["export_btn"], output.getvalue().encode('utf-8-sig'), f"padel_timesheet_{datetime.now().strftime('%Y_%m')}.csv", "text/csv")

        st.divider()

        # إدارة الكورتين والتبديل
        st.write(f"### إدارة لاعبي {display_session}")
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, phone, payment_status, court FROM bookings WHERE session_day=? AND status='confirmed' ORDER BY court ASC, id ASC", (db_session_key,))
            players = cur.fetchall()

        if players:
            for p in players:
                col_i, col_m, col_p, col_d = st.columns([3, 3, 2, 2])
                col_i.write(f"C{p[4]}: **{p[1]}** (`0{p[2]}`)")
                
                # زر تبديل اللاعب بين كورت 1 وكورت 2
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

                # تأكيد / إلغاء الدفع
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

        st.divider()

        # سجل الاستبيان
        st.write("### 📊 تحليل أسباب الاعتذار")
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT player_name, player_phone, session_day, reason, cancelled_at FROM cancellations ORDER BY id DESC LIMIT 15")
            feedbacks = cur.fetchall()

        if feedbacks:
            for row in feedbacks:
                st.caption(f"👤 **{row[0]}** (`0{row[1]}`) | السبب: **{row[3]}** | 🕒 {row[4]}")
        else:
            st.caption("لا توجد اعتذارات مسجلة.")