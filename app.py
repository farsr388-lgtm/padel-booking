from contextlib import contextmanager
import csv
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import hmac
import html
import io
import re
import sqlite3
import urllib.parse
import streamlit as st


# ==============================================================================
# 1. الإعدادات والثوابت التشغيلية
# ==============================================================================
@dataclass(frozen=True)
class AppConfig:
    DB_NAME: str = "easy_padel.db"

    # التكاليف وسعة الملعب
    COURT_TOTAL_COST: float = 190.0
    COURT_CAPACITY: int = 6
    LOYALTY_THRESHOLD: int = 6

    # بيانات التواصل والحساب البنكي
    ADMIN_WHATSAPP: str = "966566261868"
    ADMIN_PIN: str = "9900"
    BANK_NAME: str = "البنك الأهلي السعودي (SNB)"
    BENEFICIARY_NAME: str = "فارس"
    ACCOUNT_NUMBER: str = "11100320673600"
    IBAN_NUMBER: str = "SA0310000011100320673600"

    # جدول التمارين والإغلاق الزمني
    SESSION_START_TIME: str = "21:30"  # 9:30 م
    SESSION_END_TIME: str = "23:00"  # 11:00 م
    CUTOFF_HOURS_BEFORE: int = 2  # إغلاق الحجز والإلغاء الذاتي الساعة 7:30 م

    LEVELS: tuple = ("مبتدئ 🌱", "متوسط ⚡", "متقدم 🔥")
    DAYS_MAP: dict = None

    @property
    def BASE_SHARE_PRICE(self) -> float:
        return round(self.COURT_TOTAL_COST / self.COURT_CAPACITY, 2)

    def __post_init__(self):
        if self.DAYS_MAP is None:
            object.__setattr__(self, 'DAYS_MAP', {
                "الأحد": 6,
                "الإثنين": 0,
                "الثلاثاء": 1,
                "الأربعاء": 2
            })


config = AppConfig()

# ==============================================================================
# 2. إعدادات الواجهة والتصميم
# ==============================================================================
st.set_page_config(page_title="حجز بادل — قروب 99", page_icon="🎾", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0F172A; color: #F8FAFC; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: #FFFFFF;
        font-weight: 700;
        border-radius: 12px;
        padding: 14px;
        font-size: 18px;
        border: none;
    }
    .ticket-box {
        background: linear-gradient(145deg, #064E3B 0%, #022C22 100%);
        border: 2px solid #10B981;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        margin: 15px 0;
    }
    .step-card {
        background: #1E293B;
        padding: 14px 18px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 3. إدارة قاعدة البيانات والهجرة التلقائية
# ==============================================================================
class DB:
    @staticmethod
    @contextmanager
    def get_connection():
        conn = sqlite3.connect(config.DB_NAME, timeout=15)
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        with cls.get_connection() as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_date TEXT NOT NULL,
                        session_day TEXT NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        level TEXT DEFAULT 'متوسط ⚡',
                        amount REAL NOT NULL,
                        is_free INTEGER DEFAULT 0,
                        is_paid INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(session_date, phone)
                    )
                """)
                # ترقية تلقائية في حال كان الجدول موجوداً مسبقاً
                try:
                    conn.execute("ALTER TABLE bookings ADD COLUMN level TEXT DEFAULT 'متوسط ⚡'")
                except sqlite3.OperationalError:
                    pass
                try:
                    conn.execute("ALTER TABLE bookings ADD COLUMN is_paid INTEGER DEFAULT 0")
                except sqlite3.OperationalError:
                    pass

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS loyalty (
                        phone TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        paid_count INTEGER DEFAULT 0,
                        free_claimed INTEGER DEFAULT 0
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS waitlist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_date TEXT NOT NULL,
                        session_day TEXT NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        level TEXT DEFAULT 'متوسط ⚡',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(session_date, phone)
                    )
                """)
                try:
                    conn.execute("ALTER TABLE waitlist ADD COLUMN level TEXT DEFAULT 'متوسط ⚡'")
                except sqlite3.OperationalError:
                    pass


DB.init_db()


# ==============================================================================
# 4. محرك الجدولة والتحقق
# ==============================================================================
class ScheduleManager:
    @staticmethod
    def clean_phone(p: str) -> str:
        digits = str(p).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
        cleaned = re.sub(r"\D", "", digits)
        if cleaned.startswith("966"):
            cleaned = "0" + cleaned[3:]
        return cleaned

    @staticmethod
    def get_next_date_for_day(day_name: str) -> str:
        target_weekday = config.DAYS_MAP[day_name]
        today = date.today()
        days_ahead = target_weekday - today.weekday()
        if days_ahead < 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    @classmethod
    def check_cutoff(cls, session_date_str: str) -> tuple[bool, str]:
        now = datetime.now()
        d = datetime.strptime(session_date_str, "%Y-%m-%d").date()
        h, m = map(int, config.SESSION_START_TIME.split(":"))
        session_start = datetime.combine(d, time(h, m))
        cutoff_time = session_start - timedelta(hours=config.CUTOFF_HOURS_BEFORE)

        if now > session_start:
            return False, "⚠️ انتهى موعد هذا التمرين بالفعل."
        if now >= cutoff_time:
            cutoff_str = cutoff_time.strftime("%I:%M %p").replace("PM", "م").replace("AM", "ص")
            return False, f"⏳ أُغلق باب الحجز والإلغاء الذاتي (يقفل الحجز تلقائياً الساعة {cutoff_str})."
        return True, "متاح"


# ==============================================================================
# 5. منطق الخدمات والعمليات
# ==============================================================================
class PadelService:
    @classmethod
    def get_public_roster(cls, session_date: str) -> list[dict]:
        """جلب أسماء ومستويات اللاعبين فقط دون كشف أرقام الجوالات"""
        with DB.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT name, level FROM bookings WHERE session_date = ? ORDER BY id ASC", (session_date,))
            return [{"name": r[0], "level": r[1] or "متوسط ⚡"} for r in c.fetchall()]

    @classmethod
    def process_booking(cls, name: str, phone: str, level: str, day_name: str) -> tuple[bool, str, dict]:
        session_date = ScheduleManager.get_next_date_for_day(day_name)

        is_open, msg = ScheduleManager.check_cutoff(session_date)
        if not is_open:
            return False, msg, {}

        clean_name = html.escape(name.strip())
        valid_phone = ScheduleManager.clean_phone(phone)
        if not clean_name or not re.match(r"^05\d{8}$", valid_phone):
            return False, "⚠️ يرجى إدخال اسم صحيح ورقم جوال بصيغة (05XXXXXXXX).", {}

        with DB.get_connection() as conn:
            cursor = conn.cursor()
            try:
                conn.execute("BEGIN IMMEDIATE")

                cursor.execute("SELECT COUNT(*) FROM bookings WHERE session_date = ?", (session_date,))
                if cursor.fetchone()[0] >= config.COURT_CAPACITY:
                    return False, "⚠️ عذراً! اكتملت مقاعد هذا التمرين بالكامل.", {}

                cursor.execute("SELECT paid_count FROM loyalty WHERE phone = ?", (valid_phone,))
                row = cursor.fetchone()
                paid_count = row[0] if row else 0
                is_free = (paid_count > 0) and (paid_count % config.LOYALTY_THRESHOLD == 0)
                due_amount = 0.0 if is_free else config.BASE_SHARE_PRICE

                cursor.execute("""
                    INSERT INTO bookings (session_date, session_day, name, phone, level, amount, is_free)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_date, day_name, clean_name, valid_phone, level, due_amount, 1 if is_free else 0))

                if is_free:
                    cursor.execute("""
                        UPDATE loyalty SET paid_count = 0, free_claimed = free_claimed + 1, name = ?
                        WHERE phone = ?
                    """, (clean_name, valid_phone))
                else:
                    cursor.execute("""
                        INSERT INTO loyalty (phone, name, paid_count) VALUES (?, ?, 1)
                        ON CONFLICT(phone) DO UPDATE SET paid_count = paid_count + 1, name = ?
                    """, (valid_phone, clean_name, clean_name))

                conn.commit()
                return True, "تم قفل مقعدك بنجاح!", {
                    "name": clean_name, "phone": valid_phone, "level": level, "day": day_name,
                    "date": session_date, "amount": due_amount, "is_free": is_free
                }
            except sqlite3.IntegrityError:
                conn.rollback()
                return False, "⚠️ أنت مسجل بالفعل كلاعب أساسي في هذا التمرين!", {}
            except Exception as e:
                conn.rollback()
                return False, f"حدث خطأ: {str(e)}", {}

    @classmethod
    def join_waitlist(cls, name: str, phone: str, level: str, day_name: str) -> tuple[bool, str]:
        session_date = ScheduleManager.get_next_date_for_day(day_name)
        clean_name = html.escape(name.strip())
        valid_phone = ScheduleManager.clean_phone(phone)

        if not clean_name or not re.match(r"^05\d{8}$", valid_phone):
            return False, "⚠️ يرجى إدخال اسم صحيح ورقم جوال صالح."

        with DB.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM bookings WHERE session_date = ? AND phone = ?",
                               (session_date, valid_phone))
                if cursor.fetchone():
                    return False, "⚠️ أنت مسجل بالفعل كلاعب أساسي!"

                cursor.execute("""
                    INSERT INTO waitlist (session_date, session_day, name, phone, level)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_date, day_name, clean_name, valid_phone, level))
                conn.commit()
                return True, f"تم تسجيلك في قائمة الاحتياط لتمرين {day_name} ({session_date}) ⏳"
            except sqlite3.IntegrityError:
                return False, "⚠️ أنت مسجل مسبقاً في قائمة الاحتياط لهذا اليوم."

    @classmethod
    def player_self_cancel(cls, phone: str, day_name: str) -> tuple[bool, str]:
        session_date = ScheduleManager.get_next_date_for_day(day_name)
        is_open, msg = ScheduleManager.check_cutoff(session_date)
        if not is_open:
            return False, msg

        valid_phone = ScheduleManager.clean_phone(phone)
        with DB.get_connection() as conn:
            cursor = conn.cursor()
            try:
                conn.execute("BEGIN IMMEDIATE")
                cursor.execute("SELECT id, is_free, name FROM bookings WHERE session_date = ? AND phone = ?",
                               (session_date, valid_phone))
                row = cursor.fetchone()
                if not row:
                    return False, "⚠️ لم يتم العثور على حجز نشط بهذا الرقم لتمرين هذا اليوم."

                b_id, is_free, player_name = row[0], bool(row[1]), row[2]
                cursor.execute("DELETE FROM bookings WHERE id = ?", (b_id,))

                if is_free:
                    cursor.execute(
                        "UPDATE loyalty SET paid_count = ?, free_claimed = MAX(0, free_claimed - 1) WHERE phone = ?",
                        (config.LOYALTY_THRESHOLD, valid_phone))
                else:
                    cursor.execute("UPDATE loyalty SET paid_count = MAX(0, paid_count - 1) WHERE phone = ?",
                                   (valid_phone,))

                conn.commit()
                return True, f"✅ تم إلغاء حجزك بنجاح كابتن {player_name}."
            except Exception as e:
                conn.rollback()
                return False, f"حدث خطأ: {str(e)}"


# ==============================================================================
# 6. واجهة المستخدم
# ==============================================================================
tab_book, tab_cancel, tab_admin = st.tabs(["🎾 حجز مقعد", "🚫 اعتذار عن تمرين", "📊 لوحة الإدارة"])

# ------------------------------------------------------------------------------
# تبويب 1: الحجز وعرض الأسماء
# ------------------------------------------------------------------------------
with tab_book:
    st.title("🎾 حجز تمرين بادل (قروب 99)")
    st.caption(
        f"⚡ الموعد: {config.SESSION_START_TIME} - {config.SESSION_END_TIME} | الوفاء: كل {config.LOYALTY_THRESHOLD} تمارين والـ 7 مجاناً 🎁")

    selected_day = st.selectbox("اختر موعد التمرين القادم:", list(config.DAYS_MAP.keys()), key="book_day")
    session_date = ScheduleManager.get_next_date_for_day(selected_day)
    is_open, window_msg = ScheduleManager.check_cutoff(session_date)

    if not is_open:
        st.error(window_msg)
    else:
        # إشهار قائمة اللاعبين المؤكدين بدون أرقام جوالاتهم
        roster = PadelService.get_public_roster(session_date)
        seats_left = max(0, config.COURT_CAPACITY - len(roster))

        st.markdown(f"#### 👥 تشكيلة تمرين {selected_day} ({len(roster)}/{config.COURT_CAPACITY} لاعبين):")
        if roster:
            cols = st.columns(2)
            for idx, p in enumerate(roster):
                with cols[idx % 2]:
                    st.markdown(
                        f"<div class='step-card' style='padding:10px 14px; margin-bottom:8px;'>"
                        f"<b>{idx + 1}. {p['name']}</b> &nbsp; "
                        f"<span style='color:#94A3B8; font-size:13px;'>({p['level']})</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
        else:
            st.caption("لا يوجد لاعبين مسجلين حتى الآن.. كن أول المنضمين! 🚀")

        st.markdown("---")

        if seats_left > 0:
            st.info(f"🔥 متبقي **{seats_left} مقاعد** لإغلاق تمرين {selected_day}")
            with st.form("book_form"):
                u_name = st.text_input("الاسم الكريم:", placeholder="مثال: فارس")
                u_phone = st.text_input("رقم الجوال:", placeholder="05XXXXXXXX")
                u_level = st.selectbox("مستواك في اللعبة:", config.LEVELS, index=1)
                submit_book = st.form_submit_button("🚀 تأكيد الحجز الفوري")

            if submit_book:
                success, msg, summary = PadelService.process_booking(u_name, u_phone, u_level, selected_day)
                if success:
                    st.markdown(f"""
                        <div class="ticket-box">
                            <h3 style="color:#34D399; margin:0;">🎉 {msg}</h3>
                            <p style="margin:5px 0;">اللاعب: <strong>{summary['name']}</strong> ({summary['level']})</p>
                            <p style="margin:5px 0;">📅 <strong>{summary['day']}</strong> ({summary['date']}) | ⏰ 9:30 م</p>
                            <p style="margin:5px 0; color:#FBBF24;">المطلوب: <strong>{summary['amount']} ريال</strong> {'(مجاني 🎁)' if summary['is_free'] else ''}</p>
                        </div>
                    """, unsafe_allow_html=True)

                    if not summary['is_free']:
                        with st.expander("💳 بيانات التحويل البنكي (القطة)", expanded=True):
                            st.markdown(f"**المستفيد:** {config.BENEFICIARY_NAME} | **البنك:** {config.BANK_NAME}")
                            st.write("📋 **رقم الآيبان (اضغط للنسخ):**")
                            st.code(config.IBAN_NUMBER, language="text")

                    pay_text = "🎁 مجاناً (مكافأة ولاء)" if summary[
                        'is_free'] else f"{summary['amount']} ريال\n💳 الآيبان: `{config.IBAN_NUMBER}`"
                    wa_msg = (
                        f"🎾 *تأكيد حجز بادل — قروب 99* 🎾\n\n"
                        f"👤 *اللاعب:* {summary['name']} ({summary['level']})\n"
                        f"📅 *الموعد:* {summary['day']} ({summary['date']})\n"
                        f"⏰ *الوقت:* 9:30 م - 11:00 م\n"
                        f"💰 *المبلغ:* {pay_text}\n"
                        f"📍 *الموقع:* Padel IN (سوق 7)\n"
                        f"جاهزين لتكسير الملاعب! 🔥"
                    )
                    wa_url = f"https://wa.me/{config.ADMIN_WHATSAPP}?text={urllib.parse.quote(wa_msg)}"
                    st.link_button("📲 إرسال التأكيد لقروب الواتساب مباشرة", wa_url)
                else:
                    st.error(msg)
        else:
            st.warning(f"⚠️ تمرين {selected_day} مكتمل بالكامل (6/6 لاعبين).")
            st.markdown("<div class='step-card'><b>⏳ الانضمام لقائمة الاحتياط:</b></div>", unsafe_allow_html=True)
            with st.form("waitlist_form"):
                w_name = st.text_input("الاسم الكريم:", placeholder="مثال: أحمد")
                w_phone = st.text_input("رقم الجوال:", placeholder="05XXXXXXXX")
                w_level = st.selectbox("مستواك في اللعبة:", config.LEVELS, index=1)
                submit_wait = st.form_submit_button("⏳ تسجيل في قائمة الاحتياط")
            if submit_wait:
                w_ok, w_msg = PadelService.join_waitlist(w_name, w_phone, w_level, selected_day)
                if w_ok:
                    st.success(w_msg)
                else:
                    st.error(w_msg)

# ------------------------------------------------------------------------------
# تبويب 2: خدمة الاعتذار الذاتي
# ------------------------------------------------------------------------------
with tab_cancel:
    st.subheader("🚫 الاعتذار عن حضور التمرين")
    st.caption("متاح قبل موعد التمرين بساعتين (حتى الساعة 7:30 م) لإتاحة المقعد للاحتياط.")

    with st.form("self_cancel_form"):
        c_day = st.selectbox("اختر يوم التمرين المراد الاعتذار عنه:", list(config.DAYS_MAP.keys()), key="cancel_day")
        c_phone = st.text_input("رقم الجوال المسجل به الحجز:", placeholder="05XXXXXXXX")
        submit_cancel = st.form_submit_button("إلغاء حجزي وتحرير المقعد")

    if submit_cancel:
        c_ok, c_msg = PadelService.player_self_cancel(c_phone, c_day)
        if c_ok:
            st.success(c_msg)
        else:
            st.error(c_msg)

# ------------------------------------------------------------------------------
# تبويب 3: لوحة الإدارة
# ------------------------------------------------------------------------------
with tab_admin:
    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        st.subheader("🔒 لوحة تحكم القروب (خاص بالإدارة)")
        with st.form("admin_login"):
            pin_code = st.text_input("أدخل الرمز السري:", type="password")
            if st.form_submit_button("دخول"):
                if hmac.compare_digest(pin_code.strip(), config.ADMIN_PIN):
                    st.session_state.admin_auth = True
                    st.rerun()
                else:
                    st.error("الرمز السري غير صحيح!")
    else:
        col_t, col_l = st.columns([3, 1])
        col_t.subheader("📈 الإحصائيات وإدارة السداد")
        if col_l.button("🚪 خروج"):
            st.session_state.admin_auth = False
            st.rerun()

        with DB.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT 
                    COUNT(*),
                    COALESCE(SUM(CASE WHEN is_paid = 1 THEN amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN is_paid = 0 AND is_free = 0 THEN amount ELSE 0 END), 0),
                    COALESCE(SUM(is_free), 0)
                FROM bookings
            """)
            tot_b, col_rev, pend_rev, tot_free = c.fetchone()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي المقاعد", tot_b)
        m2.metric("المحصل 💰", f"{col_rev:.2f} ر.س")
        m3.metric("المعلق ⏳", f"{pend_rev:.2f} ر.س")
        m4.metric("المجانية 🎁", tot_free)

        # زر تصدير Excel متضمناً مستوى اللاعب
        st.markdown("---")
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["رقم الحجز", "التاريخ", "اليوم", "اللاعب", "المستوى", "الجوال", "المبلغ", "النوع", "حالة السداد",
             "تاريخ التسجيل"])
        with DB.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, session_date, session_day, name, level, phone, amount, is_free, is_paid, created_at FROM bookings ORDER BY session_date DESC")
            for r in c.fetchall():
                writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], "مجاني" if r[7] else "مدفوع",
                                 "تم التحويل" if r[8] else ("معفى" if r[7] else "معلق"), r[9]])
        st.download_button("📥 تنزيل تقرير كشف الحسابات (Excel/CSV)", data=output.getvalue().encode("utf-8-sig"),
                           file_name=f"padel_report_{date.today()}.csv", mime="text/csv")

        # إدارة الحجوزات والسداد
        st.markdown("---")
        st.subheader("📋 الحجوزات الحالية")
        with DB.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, session_date, session_day, name, level, phone, amount, is_free, is_paid FROM bookings ORDER BY session_date ASC, id ASC")
            bookings = c.fetchall()

        if bookings:
            for b in bookings:
                b_id, b_date, b_day, b_name, b_level, b_phone, b_amt, b_free, b_paid = b
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2.5, 2.5, 2])
                    with c1:
                        st.markdown(f"**👤 {b_name}** <small>({b_level})</small>", unsafe_allow_html=True)
                        st.caption(f"📱 {b_phone}")
                    with c2:
                        st.markdown(f"📅 **{b_day}** ({b_date})")
                        st.caption("🎁 مجاني" if b_free else f"💰 {b_amt} ريال")
                    with c3:
                        if b_free:
                            st.markdown("🟢 **معفى (مجاني)**")
                        elif b_paid:
                            st.markdown("✅ **تم التحويل**")
                            if st.button("تحويل لمعلق", key=f"u_{b_id}"):
                                with DB.get_connection() as conn:
                                    conn.execute("UPDATE bookings SET is_paid = 0 WHERE id = ?", (b_id,))
                                st.rerun()
                        else:
                            st.markdown("🔴 **معلق**")
                            btn_p, btn_w = st.columns(2)
                            if btn_p.button("سدد 💰", key=f"p_{b_id}"):
                                with DB.get_connection() as conn:
                                    conn.execute("UPDATE bookings SET is_paid = 1 WHERE id = ?", (b_id,))
                                st.rerun()
                            remind_msg = f"أهلاً كابتن {b_name} 👋\nتذكير بسداد قطة البادل ({b_amt} ريال) لتمرين يوم {b_day}.\n💳 الآيبان: `{config.IBAN_NUMBER}` ({config.BENEFICIARY_NAME})"
                            target_p = "966" + b_phone[1:]
                            btn_w.link_button("📲", f"https://wa.me/{target_p}?text={urllib.parse.quote(remind_msg)}")
                    with c4:
                        if st.button("❌ حذف", key=f"del_{b_id}"):
                            with DB.get_connection() as conn:
                                conn.execute("DELETE FROM bookings WHERE id = ?", (b_id,))
                            st.rerun()
                    st.divider()
        else:
            st.info("لا توجد حجوزات مسجلة حالياً.")

        # قائمة الاحتياط
        st.markdown("---")
        st.subheader("⏳ قائمة الاحتياط (تواصل يدوي قبل التثبيت)")
        with DB.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, session_date, session_day, name, phone, level FROM waitlist ORDER BY id ASC")
            waits = c.fetchall()

        if waits:
            for w in waits:
                w_id, w_date, w_day, w_name, w_phone, w_lvl = w
                col_w1, col_w2, col_w3 = st.columns([3, 3, 2])
                with col_w1:
                    st.write(f"**{w_name}** ({w_phone}) — <small>{w_lvl}</small>", unsafe_allow_html=True)
                with col_w2:
                    st.caption(f"{w_day} ({w_date})")
                with col_w3:
                    w_msg = f"أهلاً كابتن {w_name} 👋\nتوفر مقعد شاغر لتمرين يوم {w_day} ({w_date}). هل لا زلت متاحاً للحضور معنا؟"
                    st.link_button("📲 مراسلة الاحتياط",
                                   f"https://wa.me/966{w_phone[1:]}?text={urllib.parse.quote(w_msg)}")
                st.divider()
        else:
            st.caption("لا يوجد لاعبين في قائمة الاحتياط حالياً.")