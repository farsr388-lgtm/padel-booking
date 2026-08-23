import streamlit as st
import sqlite3
import io
import csv
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. ضبط الصفحة والهوية البصرية للجوال
# ==========================================
st.set_page_config(
    page_title="حجز بادل 99 | Padel 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap');
* { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
.padel-court {
    background: radial-gradient(circle, #064e3b 0%, #022c22 100%);
    border: 2px solid #10b981;
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 12px;
}
.court-title {
    text-align: center;
    color: #a7f3d0;
    font-weight: 900;
    font-size: 1em;
    margin-bottom: 8px;
    border-bottom: 1px dashed #10b981;
    padding-bottom: 4px;
}
.court-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
}
.slot-box {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px;
    text-align: center;
    min-height: 58px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.slot-occupied { color: #f8fafc; font-weight: 800; font-size: 0.85em; }
.slot-meta { font-size: 0.72em; margin-top: 2px; }
.slot-empty { color: #64748b; font-size: 0.75em; }
.badge-loyalty { background-color: #1e3a8a; color: #93c5fd; padding: 1px 4px; border-radius: 4px; font-size: 0.85em; }
.stButton>button { width: 100%; border-radius: 10px; font-weight: 800; height: 3.2em; font-size: 1.05em; }
.wa-btn {
    display: block;
    width: 100%;
    background-color: #25D366;
    color: white !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 800;
    text-decoration: none;
    margin-top: 8px;
}
</style>""", unsafe_allow_html=True)

# ==========================================
# 2. تحديد أقرب تمرين آلياً (توقيت السعودية)
# ==========================================
def get_auto_session_day():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    weekday = now.weekday()
    hour = now.hour

    if weekday == 6:
        return "الأحد" if hour < 23 else "الثلاثاء"
    elif weekday == 0:
        return "الثلاثاء"
    elif weekday == 1:
        return "الثلاثاء" if hour < 23 else "الخميس"
    elif weekday == 2:
        return "الخميس"
    elif weekday == 3:
        return "الخميس" if hour < 23 else "الأحد"
    elif weekday in [4, 5]:
        return "الأحد"
    return "الأحد"

current_session_day = get_auto_session_day()

# ==========================================
# 3. إدارة قاعدة البيانات
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
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

def get_player_loyalty_count(phone):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT session_day) FROM bookings WHERE phone=? AND status='confirmed'", (phone,))
        res = cur.fetchone()
        return res[0] if res else 0

# ==========================================
# 4. واجهة تشكيلة الملاعب (بدون فراغات برمجية)
# ==========================================
st.title(f"🎾 تمرين {current_session_day} — قروب 99")
st.caption("⚡ الموعد: 21:30 - 23:00 | نظام الملعبين | التمرين الـ 7 مجاناً 🎁")

with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT id, name, phone, level, payment_status FROM bookings WHERE session_day=? AND court=1 AND status='confirmed' ORDER BY id ASC", (current_session_day,))
    c1 = c.fetchall()
    c.execute("SELECT id, name, phone, level, payment_status FROM bookings WHERE session_day=? AND court=2 AND status='confirmed' ORDER BY id ASC", (current_session_day,))
    c2 = c.fetchall()
    c.execute("SELECT id, name, level FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (current_session_day,))
    waitlist = c.fetchall()

st.markdown(f"### 🏟️ تشكيلة تمرين {current_session_day} ({len(c1)+len(c2)}/8 لاعبين)")

col_c1, col_c2 = st.columns(2)

def render_court_clean(title, players):
    items_html = ""
    for i in range(4):
        if i < len(players):
            p = players[i]
            loyalty_cnt = (get_player_loyalty_count(p[2]) % 7)
            loyalty_str = f"⭐ {loyalty_cnt}/6" if loyalty_cnt < 6 else "🎁 مجاني!"
            pay_str = "✅ مدفوع" if p[4] == "paid" else "⏳ قطة"
            pay_color = "#34d399" if p[4] == "paid" else "#fbbf24"
            items_html += f'<div class="slot-box"><div class="slot-occupied">🎾 {p[1]}</div><div class="slot-meta"><span class="badge-loyalty">{loyalty_str}</span> <span style="color:{pay_color};font-weight:700;">{pay_str}</span></div></div>'
        else:
            items_html += f'<div class="slot-box"><div class="slot-empty">مقعد {i+1} شاغر ✨</div></div>'
    return f'<div class="padel-court"><div class="court-title">{title} ({len(players)}/4)</div><div class="court-grid">{items_html}</div></div>'

with col_c1:
    st.markdown(render_court_clean("🏟️ الملعب 1", c1), unsafe_allow_html=True)

with col_c2:
    st.markdown(render_court_clean("🏟️ الملعب 2", c2), unsafe_allow_html=True)

if waitlist:
    st.caption("📋 **قائمة الاحتياط:** " + " • ".join([f"{w[1]}" for w in waitlist]))

st.divider()

# ==========================================
# 5. الحجز السريع وزر الواتساب
# ==========================================
tab_book, tab_cancel = st.tabs(["⚡ الحجز السريع", "❌ اعتذار / إلغاء"])

with tab_book:
    with st.form("quick_booking", clear_on_submit=False):
        name = st.text_input("1️⃣ اسم اللاعب الكريم:")
        phone = st.text_input("2️⃣ رقم الجوال (05xxxxxxxx):")
        level = st.selectbox("3️⃣ المستوى في اللعب:", ["متقدم", "متوسط", "مبتدئ"])
        
        btn_submit = st.form_submit_button(f"🚀 تأكيد الحجز لتمرين {current_session_day}")

        if btn_submit:
            c_name = name.strip()
            c_phone = phone.strip()
            
            if len(c_name) < 3 or len(c_phone) < 10:
                st.error("يرجى إدخال الاسم ورقم الجوال بشكل صحيح.")
            else:
                if level == "متقدم":
                    target_court = 1 if len(c1) < 4 else (2 if len(c2) < 4 else 0)
                elif level == "مبتدئ":
                    target_court = 2 if len(c2) < 4 else (1 if len(c1) < 4 else 0)
                else:
                    target_court = 1 if len(c1) < 4 else (2 if len(c2) < 4 else 0)

                status_to_set = 'confirmed' if target_court > 0 else 'waitlist'
                final_court = target_court if target_court > 0 else 1

                with get_db() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO bookings (name, phone, session_day, court, level, status) VALUES (?, ?, ?, ?, ?, ?)",
                                (c_name, c_phone, current_session_day, final_court, level, status_to_set))
                    conn.commit()

                st.session_state["booked_user"] = {
                    "name": c_name,
                    "court": final_court,
                    "status": status_to_set,
                    "day": current_session_day
                }
                st.rerun()

    if "booked_user" in st.session_state:
        b = st.session_state["booked_user"]
        if b["status"] == "confirmed":
            st.success(f"كفو يا كابتن {b['name']}! تم تثبيت مقعدك في 🏟️ الملعب {b['court']}.")
            wa_msg = f"🎾 تم حجز مقعدي ({b['name']}) في تمرين {b['day']} - 🏟️ ملعب {b['court']}! مرفق إشعار التحويل ⚡"
        else:
            st.info(f"الملاعب مكتملة! تمت إضافتك يا كابتن {b['name']} لقائمة الاحتياط.")
            wa_msg = f"🎾 تم تسجيل اسمي ({b['name']}) في قائمة احتياط تمرين {b['day']} ⏳"

        wa_link = f"https://wa.me/?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 إرسال إشعار التأكيد في قروب الواتساب</a>', unsafe_allow_html=True)

# --- تبويب الاعتذار ---
with tab_cancel:
    st.caption("أدخل رقم جوالك لتفريغ المقعد تلقائياً للاعبين في قائمة الاحتياط.")
    with st.form("quick_cancel"):
        can_phone = st.text_input("رقم الجوال المسجل به الحجز:")
        can_reason = st.selectbox("سبب الاعتذار:", ["ظرف طارئ / عمل", "إصابة أو إجهاد", "تعارض في الوقت", "أخرى"])
        btn_can = st.form_submit_button("تأكيد الاعتذار وتفريغ المقعد")

        if btn_can:
            clean_p = can_phone.strip()
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, status, court FROM bookings WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')",
                            (clean_p, current_session_day))
                target = cur.fetchone()

                if target:
                    cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (target[0],))
                    cur.execute("INSERT INTO cancellations (player_name, player_phone, session_day, court, reason) VALUES (?, ?, ?, ?, ?)",
                                (target[1], clean_p, current_session_day, target[3], can_reason))
                    
                    if target[2] == 'confirmed':
                        cur.execute("SELECT id FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (current_session_day,))
                        first_wait = cur.fetchone()
                        if first_wait:
                            cur.execute("UPDATE bookings SET status='confirmed', court=? WHERE id=?", (target[3], first_wait[0]))
                    conn.commit()

                    st.success(f"تم قبول اعتذارك يا كابتن {target[1]} وتفريغ المقعد بنجاح.")
                    if "booked_user" in st.session_state:
                        del st.session_state["booked_user"]
                    st.rerun()
                else:
                    st.error("لم يتم العثور على حجز مسجل بهذا الرقم في تمرين اليوم.")

# ==========================================
# 6. لوحة الإدارة المخفية
# ==========================================
st.write("")
with st.expander("⚙️", expanded=False):
    pin = st.text_input("رمز الإدارة:", type="password", key="admin_pin_input")
    if pin == "9900":
        st.success("لوحة تحكم الكابتن 👑")

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_day, court, name, phone, level,
                       CASE WHEN payment_status='paid' THEN 'تم الدفع' ELSE 'معلق' END as pay_state,
                       created_at
                FROM bookings WHERE status='confirmed'
                ORDER BY session_day, court, id
            """)
            rows = cur.fetchall()

        if rows:
            output = io.StringIO()
            output.write('\ufeff')
            writer = csv.writer(output)
            writer.writerow(["اليوم", "الملعب", "الاسم", "الجوال", "المستوى", "حالة القطة", "تاريخ الحجز"])
            writer.writerows(rows)
            st.download_button("📥 تحميل تايم شيت الحضور (Excel)", output.getvalue().encode('utf-8-sig'), f"attendance_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

        st.divider()

        st.write(f"### إدارة لاعبي تمرين {current_session_day}")
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, phone, level, payment_status, court FROM bookings WHERE session_day=? AND status='confirmed' ORDER BY court ASC, id ASC", (current_session_day,))
            players = cur.fetchall()

        if players:
            for p in players:
                col_i, col_m, col_p, col_d = st.columns([3, 3, 2, 2])
                col_i.write(f"🏟️ M{p[5]}: **{p[1]}** (`{p[3]}`)")
                
                if p[5] == 1:
                    if col_m.button("نقل لـ 2 ➡️", key=f"m2_{p[0]}"):
                        with get_db() as conn:
                            conn.execute("UPDATE bookings SET court=2 WHERE id=?", (p[0],))
                        st.rerun()
                else:
                    if col_m.button("نقل لـ 1 ⬅️", key=f"m1_{p[0]}"):
                        with get_db() as conn:
                            conn.execute("UPDATE bookings SET court=1 WHERE id=?", (p[0],))
                        st.rerun()

                if p[4] == 'pending':
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
            st.info("لا توجد حجوزات مؤكدة لهذا اليوم.")