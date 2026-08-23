import streamlit as st
import sqlite3
from datetime import datetime

# ==========================================
# 1. إعداد الصفحة واللغات (Dictionary)
# ==========================================
st.set_page_config(
    page_title="Padel 99 | حجز ملعبي بادل",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

LANG = {
    "ar": {
        "dir": "rtl",
        "align": "right",
        "title": "🎾 حجز تمارين بادل — قروب 99",
        "caption": "⚡ الموعد: 21:30 - 23:00 | نظام الملعبين (A & B) | الـ 7 مجاناً 🎁",
        "rules_title": "📜 قوانين وضوابط التمارين وتوزيع الملاعب",
        "rules_body": """
        1. **نظام الملعبين:** الملعب 1 مخصص للمستويات (المتقدمة/المتوسطة) والملعب 2 للمستويات (المتوسطة/المبتدئة).
        2. **التوزيع الآلي:** يوزعك النظام تلقائياً حسب مستواك لضمان تكافؤ اللعب، مع إمكانية تعديل الكابتن لجمع الأصحاب.
        3. **سياسة الاعتذار:** الإلغاء متاح حتى **7:30 مساءً** يوم التمرين برقم الجوال فقط.
        4. **تثبيت الحجز:** يرجى تحويل قيمة القطة فور التسجيل لتأكيد المقعد.
        """,
        "select_day": "📅 اختر موعد التمرين:",
        "days": ["الأحد", "الثلاثاء", "الخميس"],
        "court1_title": "🏟️ الملعب 1 (متقدم / متوسط)",
        "court2_title": "🏟️ الملعب 2 (متوسط / مبتدئ)",
        "level_lbl": "المستوى",
        "pay_lbl": "الدفع",
        "empty_court": "المقاعد شاغرة.. كن أول المنضمين!",
        "waitlist_lbl": "📋 قائمة الاحتياط العامة:",
        "tab_book": "📝 حجز مقعد",
        "tab_cancel": "❌ اعتذار / إلغاء",
        "name_lbl": "اسم اللاعب:",
        "phone_lbl": "رقم الجوال (05xxxxxxxx):",
        "skill_lbl": "مستوى اللعب:",
        "levels": ["متقدم", "متوسط", "مبتدئ+", "مبتدئ"],
        "btn_book": "🚀 تأكيد الحجز الفوري",
        "err_fields": "يرجى كتابة الاسم ورقم الجوال بالشكل الصحيح.",
        "succ_book_c1": "تم تأكيد حجزك في 🏟️ الملعب 1 يا كابتن {}!",
        "succ_book_c2": "تم تأكيد حجزك في 🏟️ الملعب 2 يا كابتن {}!",
        "succ_wait": "تمت إضافتك إلى قائمة الاحتياط بنجاح.",
        "cancel_title": "الاعتذار وإلغاء الحجز",
        "cancel_sub": "أدخل رقم جوالك المسجل لإخلاء المقعد تلقائياً للاحتياط.",
        "reason_lbl": "سبب الاعتذار الرئيسي:",
        "reasons": ["ظرف طارئ / عمل", "إصابة أو إجهاد بدني", "تعارض في الوقت", "صعوبة في الوصول", "أخرى"],
        "speed_lbl": "تقييمك لسرعة وسهولة الموقع:",
        "speed_opts": ["بطيء", "مقبول", "سريع وممتاز ⚡"],
        "notes_lbl": "ملاحظات أو اقتراح لتطوير الموقع (اختياري):",
        "btn_cancel": "تأكيد الاعتذار وتفريغ المقعد",
        "succ_cancel": "تم قبول اعتذارك يا كابتن {} وإخلاء المقعد.",
        "err_cancel": "لم يتم العثور على حجز مسجل بهذا الرقم في هذا الموعد.",
        "admin_lock": "⚙️",
        "admin_pin_lbl": "رمز الإدارة السري:",
        "admin_welcome": "لوحة إدارة الكابتن — قروب 99 👑",
        "btn_pay": "تأكيد 💳",
        "btn_unpay": "إلغاء 🔄",
        "btn_move_c2": "نقل لملعب 2 ➡️",
        "btn_move_c1": "نقل لملعب 1 ⬅️",
        "btn_del": "حذف ❌",
        "feedback_title": "📊 تقرير الاستبيان وسجل الاعتذارات"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "title": "🎾 Padel Booking — Group 99",
        "caption": "⚡ Time: 21:30 - 23:00 | 2 Courts System | 7th session FREE 🎁",
        "rules_title": "📜 Rules & Auto-Court Assignment",
        "rules_body": """
        1. **Dual Courts:** Court 1 (Advanced/Intermediate) & Court 2 (Intermediate/Beginner).
        2. **Auto-Assignment:** Auto-assigned based on skill. Captain can adjust to group friends.
        3. **Cancellation:** Allowed until **7:30 PM** with registered phone number.
        4. **Payment:** Please transfer share immediately to confirm slot.
        """,
        "select_day": "📅 Select Session Day:",
        "days": ["Sunday", "Tuesday", "Thursday"],
        "court1_title": "🏟️ Court 1 (Advanced / Mid)",
        "court2_title": "🏟️ Court 2 (Mid / Beginner)",
        "level_lbl": "Level",
        "pay_lbl": "Pay",
        "empty_court": "Court empty.. Be the first to book!",
        "waitlist_lbl": "📋 General Waitlist:",
        "tab_book": "📝 Book Slot",
        "tab_cancel": "❌ Cancel Booking",
        "name_lbl": "Player Name:",
        "phone_lbl": "Mobile (05xxxxxxxx):",
        "skill_lbl": "Skill Level:",
        "levels": ["Advanced", "Intermediate", "Beginner+", "Beginner"],
        "btn_book": "🚀 Confirm Booking",
        "err_fields": "Please enter a valid name and phone number.",
        "succ_book_c1": "Booked in 🏟️ Court 1 for Captain {}!",
        "succ_book_c2": "Booked in 🏟️ Court 2 for Captain {}!",
        "succ_wait": "Added to the general waitlist successfully.",
        "cancel_title": "Cancel Booking & Feedback",
        "cancel_sub": "Enter your registered phone number to release your spot.",
        "reason_lbl": "Cancellation Reason:",
        "reasons": ["Emergency / Work", "Injury / Fatigue", "Time Conflict", "Location / Distance", "Other"],
        "speed_lbl": "Site speed & ease rating:",
        "speed_opts": ["Slow", "Acceptable", "Fast & Great ⚡"],
        "notes_lbl": "Suggestions / Feedback (Optional):",
        "btn_cancel": "Confirm Cancellation",
        "succ_cancel": "Cancelled for Captain {}. Spot released.",
        "err_cancel": "No booking found for this phone number.",
        "admin_lock": "⚙️",
        "admin_pin_lbl": "Admin PIN:",
        "admin_welcome": "Captain Control Panel — Group 99 👑",
        "btn_pay": "Paid 💳",
        "btn_unpay": "Unpay 🔄",
        "btn_move_c2": "To Court 2 ➡️",
        "btn_move_c1": "To Court 1 ⬅️",
        "btn_del": "Del ❌",
        "feedback_title": "📊 Cancellation Logs & Feedback"
    }
}

# شريط اختيار اللغة
col_lang1, col_lang2 = st.columns([4, 1])
with col_lang2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# تنسيقات الواجهة والخفة
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}
    .stButton>button {{ width: 100%; border-radius: 8px; font-weight: 700; height: 2.7em; }}
    .player-card {{
        background: #1e293b;
        border-right: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        color: #ffffff;
    }}
    .court-header {{
        background: #0f172a;
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #334155;
        font-weight: bold;
        margin-bottom: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة البيانات المحسنة للملعبين
# ==========================================
DB_FILE = "group99_padel.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                session_day TEXT NOT NULL,
                court INTEGER DEFAULT 1,
                level TEXT NOT NULL,
                status TEXT DEFAULT 'confirmed',
                payment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # فحص إضافة عمود court إذا كان الجدول قديماً لتفادي أي أخطاء
        cursor.execute("PRAGMA table_info(bookings)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'court' not in cols:
            cursor.execute("ALTER TABLE bookings ADD COLUMN court INTEGER DEFAULT 1")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cancellations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT,
                player_phone TEXT,
                session_day TEXT,
                court INTEGER,
                reason TEXT,
                feedback_rating TEXT,
                feedback_notes TEXT,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# ==========================================
# 3. الهيدر وعرض الملعبين
# ==========================================
st.title(t["title"])
st.caption(t["caption"])

with st.expander(t["rules_title"]):
    st.markdown(t["rules_body"])

day_map_ar = {"Sunday": "الأحد", "Tuesday": "الثلاثاء", "Thursday": "الخميس"}
day_choice = st.selectbox(t["select_day"], t["days"])
db_day = day_map_ar.get(day_choice, day_choice)

COURT_CAP = 4  # سعة كل ملعب (4 لاعبين للمباراة)

# جلب بيانات الملعبين
with get_connection() as conn:
    c = conn.cursor()
    c.execute("SELECT id, name, phone, level, payment_status, court FROM bookings WHERE session_day=? AND court=1 AND status='confirmed' ORDER BY id ASC", (db_day,))
    c1_players = c.fetchall()
    c.execute("SELECT id, name, phone, level, payment_status, court FROM bookings WHERE session_day=? AND court=2 AND status='confirmed' ORDER BY id ASC", (db_day,))
    c2_players = c.fetchall()
    c.execute("SELECT id, name, phone, level FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (db_day,))
    waitlist = c.fetchall()

# عرض تشكيلة الملعبين جنباً إلى جنب
col_court1, col_court2 = st.columns(2)

with col_court1:
    st.markdown(f"<div class='court-header'>{t['court1_title']} ({len(c1_players)}/{COURT_CAP})</div>", unsafe_allow_html=True)
    if c1_players:
        for idx, p in enumerate(c1_players, 1):
            pay_icon = "✅" if p[4] == "paid" else "⏳"
            st.markdown(f"""
            <div class="player-card">
                <b>🎾 {idx}. {p[1]}</b><br>
                <span style="font-size:0.8em; opacity:0.85;">{t['level_lbl']}: <b>{p[3]}</b> | {t['pay_lbl']}: {pay_icon}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption(t["empty_court"])

with col_court2:
    st.markdown(f"<div class='court-header'>{t['court2_title']} ({len(c2_players)}/{COURT_CAP})</div>", unsafe_allow_html=True)
    if c2_players:
        for idx, p in enumerate(c2_players, 1):
            pay_icon = "✅" if p[4] == "paid" else "⏳"
            st.markdown(f"""
            <div class="player-card">
                <b>🎾 {idx}. {p[1]}</b><br>
                <span style="font-size:0.8em; opacity:0.85;">{t['level_lbl']}: <b>{p[3]}</b> | {t['pay_lbl']}: {pay_icon}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption(t["empty_court"])

if waitlist:
    st.caption(f"{t['waitlist_lbl']} " + " • ".join([f"{w[1]} ({w[3]})" for w in waitlist]))

st.divider()

# ==========================================
# 4. التبويبات العامة (حجز واعتذار)
# ==========================================
tab_book, tab_cancel = st.tabs([t["tab_book"], t["tab_cancel"]])

# --- تبويب الحجز مع التوزيع الذكي للملعبين ---
with tab_book:
    total_confirmed = len(c1_players) + len(c2_players)
    total_max = COURT_CAP * 2
    
    with st.form("form_booking", clear_on_submit=True):
        name = st.text_input(t["name_lbl"])
        phone = st.text_input(t["phone_lbl"])
        level = st.selectbox(t["skill_lbl"], t["levels"])
        btn_book = st.form_submit_button(t["btn_book"])

        if btn_book:
            clean_phone = phone.strip()
            clean_name = name.strip()
            if len(clean_name) < 3 or len(clean_phone) < 10:
                st.error(t["err_fields"])
            else:
                # منطق التوزيع الذكي حسب المستوى والمقاعد المتاحة
                target_court = 1
                status_to_set = 'confirmed'
                
                # المتقدم والمتوسط يفضلون ملعب 1، المبتدئ يفضل ملعب 2
                pref_c1 = level in ["متقدم", "Advanced", "متوسط", "Intermediate"]
                
                if pref_c1:
                    if len(c1_players) < COURT_CAP:
                        target_court = 1
                    elif len(c2_players) < COURT_CAP:
                        target_court = 2
                    else:
                        status_to_set = 'waitlist'
                else:
                    if len(c2_players) < COURT_CAP:
                        target_court = 2
                    elif len(c1_players) < COURT_CAP:
                        target_court = 1
                    else:
                        status_to_set = 'waitlist'

                with get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO bookings (name, phone, session_day, court, level, status) VALUES (?, ?, ?, ?, ?, ?)",
                                (clean_name, clean_phone, db_day, target_court, level, status_to_set))
                    conn.commit()

                if status_to_set == 'confirmed':
                    if target_court == 1:
                        st.success(t["succ_book_c1"].format(clean_name))
                    else:
                        st.success(t["succ_book_c2"].format(clean_name))
                else:
                    st.info(t["succ_wait"])
                st.rerun()

# --- تبويب الاعتذار مع الترقية الذكية ---
with tab_cancel:
    st.subheader(t["cancel_title"])
    st.caption(t["cancel_sub"])
    
    with st.form("form_cancellation"):
        c_phone = st.text_input(t["phone_lbl"])
        c_reason = st.selectbox(t["reason_lbl"], t["reasons"])
        c_speed = st.select_slider(t["speed_lbl"], options=t["speed_opts"])
        c_notes = st.text_input(t["notes_lbl"])
        btn_cancel = st.form_submit_button(t["btn_cancel"])

        if btn_cancel:
            clean_cp = c_phone.strip()
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, status, court FROM bookings WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')",
                            (clean_cp, db_day))
                target = cur.fetchone()

                if target:
                    cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (target[0],))
                    cur.execute("""
                        INSERT INTO cancellations (player_name, player_phone, session_day, court, reason, feedback_rating, feedback_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (target[1], clean_cp, db_day, target[3], c_reason, c_speed, c_notes.strip()))
                    
                    # ترقية أول احتياط إلى نفس الملعب الشاغر
                    if target[2] == 'confirmed':
                        cur.execute("SELECT id FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_day,))
                        first_wait = cur.fetchone()
                        if first_wait:
                            cur.execute("UPDATE bookings SET status='confirmed', court=? WHERE id=?", (target[3], first_wait[0]))
                    conn.commit()

                    st.success(t["succ_cancel"].format(target[1]))
                    st.rerun()
                else:
                    st.error(t["err_cancel"])

# ==========================================
# 5. لوحة الإدارة المخفية (تبديل الملاعب والدفع)
# ==========================================
st.write("")
with st.expander(t["admin_lock"], expanded=False):
    pin_input = st.text_input(t["admin_pin_lbl"], type="password", key="admin_pin_key")
    if pin_input == "9900":
        st.success(t["admin_welcome"])

        st.write(f"### ⚙️ إدارة لاعبي {day_choice}")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, phone, level, payment_status, court FROM bookings WHERE session_day=? AND status='confirmed' ORDER BY court ASC, id ASC", (db_day,))
            all_admin = cur.fetchall()

        if all_admin:
            for p in all_admin:
                c_lbl = f"🏟️ M{p[5]}"
                col_info, col_move, col_pay, col_del = st.columns([3, 3, 2, 2])
                col_info.write(f"{c_lbl}: **{p[1]}** (`{p[3]}`)")
                
                # زر نقل اللاعب بين الملعبين
                if p[5] == 1:
                    if col_move.button(t["btn_move_c2"], key=f"move_{p[0]}"):
                        with get_connection() as conn:
                            conn.execute("UPDATE bookings SET court=2 WHERE id=?", (p[0],))
                        st.rerun()
                else:
                    if col_move.button(t["btn_move_c1"], key=f"move_{p[0]}"):
                        with get_connection() as conn:
                            conn.execute("UPDATE bookings SET court=1 WHERE id=?", (p[0],))
                        st.rerun()

                # تأكيد / إلغاء الدفع
                if p[4] == 'pending':
                    if col_pay.button(t["btn_pay"], key=f"pay_{p[0]}"):
                        with get_connection() as conn:
                            conn.execute("UPDATE bookings SET payment_status='paid' WHERE id=?", (p[0],))
                        st.rerun()
                else:
                    if col_pay.button(t["btn_unpay"], key=f"unpay_{p[0]}"):
                        with get_connection() as conn:
                            conn.execute("UPDATE bookings SET payment_status='pending' WHERE id=?", (p[0],))
                        st.rerun()
                
                # حذف الحجز
                if col_del.button(t["btn_del"], key=f"del_{p[0]}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM bookings WHERE id=?", (p[0],))
                    st.rerun()
        else:
            st.info("لا توجد حجوزات مؤكدة لهذا اليوم.")

        st.divider()

        # سجل الاستبيانات والاعتذارات
        st.write(f"### {t['feedback_title']}")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT player_name, player_phone, session_day, reason, feedback_rating, feedback_notes, cancelled_at FROM cancellations ORDER BY id DESC LIMIT 10")
            feedbacks = cur.fetchall()

        if feedbacks:
            for row in feedbacks:
                note_str = f" | ملاحظة: _{row[5]}_" if row[5] else ""
                st.caption(f"👤 **{row[0]}** ({row[1]}) | يوم: {row[2]} | السبب: **{row[3]}** | السرعة: {row[4]}{note_str} | 🕒 {row[6]}")
        else:
            st.caption("لا توجد بيانات اعتذار مسجلة حتى الآن.")
            
    elif pin_input:
        st.error("الرمز السري غير صحيح.")

        