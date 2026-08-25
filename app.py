import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import io
import csv
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة وتهيئة الجوال
# ==========================================
st.set_page_config(
    page_title="بادل 99 | Padel 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.block-container { 
    padding-top: 0.4rem !important; 
    padding-bottom: 1.5rem !important; 
    padding-left: 0.5rem !important; 
    padding-right: 0.5rem !important; 
    max-width: 100% !important; 
}

html, body, p, div, span, label, input, select, button, .stMarkdown {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Geeza Pro", Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
    box-sizing: border-box;
}

[data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"] {
    font-family: "Material Symbols Rounded", "Source Sans Pro", sans-serif !important;
}

.hero-header { font-size: 1.55em; font-weight: 800; color: #f8fafc; margin: 0; line-height: 1.2; }
.hero-sub { font-size: 0.85em; color: #94a3b8; margin: 2px 0 6px 0; }
.contrast-pill { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 4px 8px; font-size: 0.74em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }
.promo-badge { background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.74em; margin-bottom: 4px; }

.thankyou-box {
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid #10b981;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0;
    text-align: center;
}
.thankyou-title { color: #34d399; font-size: 0.95em; font-weight: 700; margin-bottom: 2px; }
.thankyou-sub { color: #e2e8f0; font-size: 0.8em; }

.alrajhi-card {
    background: #111418;
    border: 1.5px solid #2d3748;
    border-radius: 14px;
    padding: 12px;
    margin: 8px 0;
    color: #ffffff;
}
.card-top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 5px; margin-bottom: 8px; }
.bank-title { font-size: 0.9em; font-weight: 700; color: #f8fafc; }
.price-pill { background: #10b981; color: #022c22; padding: 2px 7px; border-radius: 12px; font-weight: 700; font-size: 0.8em; }
.qr-container { background: #ffffff; padding: 6px; border-radius: 8px; display: inline-block; margin: 2px auto 6px auto; }
.qr-container img { display: block; width: 115px; height: 115px; }
.card-owner { font-size: 1em; font-weight: 700; color: #f8fafc; margin-bottom: 6px; text-align: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.12); padding-bottom: 5px; }
.copy-badge {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    font-family: monospace;
    font-size: 0.84em;
    color: #38bdf8;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 5px;
}

.wa-btn {
    display: block;
    width: 100%;
    background: #25D366;
    color: white !important;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 6px;
    font-size: 0.88em;
}

.support-btn {
    display: block;
    width: 100%;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #cbd5e1 !important;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    margin-top: 10px;
    font-size: 0.8em;
}

.padel-court { background: #064e3b; border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 10px; padding: 8px; margin: 8px 0; }
.court-title { text-align: center; color: #a7f3d0; font-weight: 700; font-size: 0.85em; margin-bottom: 6px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 3px; }
.court-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.slot-box { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 5px 3px; text-align: center; min-height: 44px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.slot-occupied { color: #f4f4f5; font-weight: 600; font-size: 0.78em; line-height: 1.2; }
.slot-meta { display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 0.65em; margin-top: 2px; flex-wrap: wrap; }
.slot-empty { color: #64748b; font-size: 0.72em; }
.badge-loyalty { background-color: #1e3a8a; color: #93c5fd; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 600; }
.badge-level { background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 500; }

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. مؤقت التحديث الخفيف في الخلفية
# ==========================================
components.html(
    """
    <script>
    setTimeout(function(){
        window.parent.document.querySelector('button[kind="header"]')?.click();
    }, 7000);
    </script>
    """,
    height=0,
    width=0
)

# ==========================================
# 3. محرك قاعدة البيانات
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
                hear_about TEXT DEFAULT '',
                player_note TEXT DEFAULT '',
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cur.execute("PRAGMA table_info(bookings)")
        cols = [c[1] for c in cur.fetchall()]
        if "hear_about" not in cols:
            cur.execute("ALTER TABLE bookings ADD COLUMN hear_about TEXT DEFAULT '';")
        if "player_note" not in cols:
            cur.execute("ALTER TABLE bookings ADD COLUMN player_note TEXT DEFAULT '';")

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
# 4. دوال الفحص والتوحيد
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
        cur.execute("SELECT id FROM bookings WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')", (phone, session_key))
        return cur.fetchone() is not None

def get_loyalty_score(norm_phone):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT session_day) FROM bookings WHERE phone=? AND status='confirmed'", (norm_phone,))
        res = cur.fetchone()
        return res[0] if res else 0

def get_next_session():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    weekday = now.weekday()

    if weekday == 6:     # الأحد
        days_to_add = 0
        d_ar = "الأحد"
    elif weekday == 0:   # الإثنين
        days_to_add = 1
        d_ar = "الثلاثاء"
    elif weekday == 1:   # الثلاثاء
        days_to_add = 0
        d_ar = "الثلاثاء"
    elif weekday == 2:   # الأربعاء
        days_to_add = 1
        d_ar = "الخميس"
    elif weekday == 3:   # الخميس
        days_to_add = 0
        d_ar = "الخميس"
    elif weekday == 4:   # الجمعة
        days_to_add = 2
        d_ar = "الأحد"
    else:                # السبت
        days_to_add = 1
        d_ar = "الأحد"

    target_date = now + timedelta(days=days_to_add)
    label_ar = f"{d_ar} ({target_date.strftime('%d/%m')})"
    db_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"
    return label_ar, db_key

display_session, db_session_key = get_next_session()
COURT_CAPACITY = 6

with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT id, name, phone, payment_status, level FROM bookings WHERE session_day=? AND court=1 AND status='confirmed' ORDER BY id ASC LIMIT 6", (db_session_key,))
    c1 = c.fetchall()
    c.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (db_session_key,))
    waitlist = c.fetchall()

total_booked = len(c1)

# ==========================================
# 5. الواجهة الأساسية وحجز المقاعد
# ==========================================
st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session}. متعة اللعب، بتنظيم أبسط.</div>", unsafe_allow_html=True)
st.markdown("<div class='contrast-pill'>⚡ حجز فوري • 6 لاعبين للملعب • السابع علينا.</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين واحصل على السابع مجاناً</div>", unsafe_allow_html=True)
st.caption(f"⏰ 9:30 م إلى 11:00 م | كورت 1 • <b>المؤكدين: {total_booked}/6</b>", unsafe_allow_html=True)

tab_book, tab_rules, tab_cancel = st.tabs(["⚡ حجز مقعد", "📜 القواعد", "❌ اعتذار"])

with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        f_name = st.text_input("الاسم الثلاثي")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx")
        f_level_raw = st.selectbox("مستوى اللعب", [
            "🟢 متوسط - تبادل وثبات",
            "🔥 متقدم - سرعة وتكتيك",
            "⚪ مبتدئ - انطلاقة وتعلّم"
        ])
        f_level = "متوسط" if "متوسط" in f_level_raw else ("متقدم" if "متقدم" in f_level_raw else "مبتدئ")
        
        with st.expander("💡 استبيان سريع (اختياري)", expanded=False):
            f_source = st.selectbox("كيف سمعت عن بادل 99؟", ["قروب واتساب", "توصية من صديق", "منصة إكس أو تيك توك", "أخرى"])
            f_note = st.text_input("ملاحظة أو اقتراح لتمرين اليوم:", placeholder="مثلاً: تفضيل كور معينة أو وقت...")

        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button("تأكيد الانضمام 🚀", use_container_width=True)

        if btn_submit:
            if honeypot_val:
                st.error("تم رفض الطلب للاشتباه في نشاط آلي.")
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 2 or not clean_phone:
                st.error("فضلاً أدخل الاسم ورقم جوال صحيح يبدأ بـ 05.")
            elif check_active_booking(clean_phone, db_session_key):
                st.warning("أنت مسجل بالفعل في تمرين اليوم.")
            else:
                with get_db() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND court=1 AND status='confirmed'", (db_session_key,))
                    cur_c1 = cur.fetchone()[0]

                    status_val = 'confirmed' if cur_c1 < COURT_CAPACITY else 'waitlist'
                    cur.execute("""
                        INSERT INTO bookings (name, phone, session_day, court, level, status, hear_about, player_note) 
                        VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                    """, (clean_name, clean_phone, db_session_key, f_level, status_val, f_source, f_note))
                    
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

            st.markdown(f"""
            <div class="thankyou-box">
                <div class="thankyou-title">✅ تم تأكيد حجزك بنجاح! شكراً لك يا كابتن {lb['name']}</div>
                <div class="thankyou-sub">تم حجز مقعدك في <b>{lb['session']}</b>. نلتقي في الملعب!</div>
            </div>
            """, unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={iban_raw}&color=000000&bgcolor=ffffff"

            card_html = f"""
<div class="alrajhi-card">
    <div class="card-top">
        <div class="bank-title">🏛️ مصرف الراجحي</div>
        <div class="price-pill">65 ر.س</div>
    </div>
    <div style="text-align:center;">
        <div class="qr-container">
            <img src="{qr_url}" alt="QR" />
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
    <div style="margin-top: 6px; padding: 6px 8px; background: rgba(56, 189, 248, 0.08); border-radius: 6px; border: 1px dashed rgba(56, 189, 248, 0.3); display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 0.75em; color: #cbd5e1;">💡 <b>اسم المستفيد:</b></div>
        <div class="copy-badge" style="margin-bottom:0; padding:2px 6px; font-size:0.8em;" onclick="navigator.clipboard.writeText('بادل 99'); alert('تم نسخ اسم المستفيد: بادل 99 📋');">
            <span>بادل 99</span>
            <span>📋</span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:0.72em; color:#64748b; margin-top:6px;">
        <span>سويفت: <b>RJHISARI</b></span>
        <span>⚡ تحويل فوري</span>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {lb['name']}\nالتمرين: {lb['session']} (كورت 1)\nالمبلغ: 65 ر.س\n\nمرفق إشعار التحويل البنكي لحساب كابتن فارس العصيمي. نلتقي في الملعب."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتثبيت المقعد</a>', unsafe_allow_html=True)
        else:
            st.info(f"اكتملت المقاعد. أنت في صدارة الاحتياط رقم ({lb.get('wait_pos', 1)}). سيتم إشعارك وتصعيدك فور اعتذار أي لاعب.")

with tab_rules:
    st.markdown("""
    <div style="background:#18181b; border:1px solid #27272a; border-radius:10px; padding:10px; margin:8px 0; font-size:0.82em; color:#e2e8f0; line-height:1.4;">
        <div style="margin-bottom:8px;">⏱️ <b>قبل 4 ساعات:</b> استرجاع كامل أو ترحيل فوري لتمرينك القادم.</div>
        <div style="margin-bottom:8px;">⚠️ <b>أقل من 4 ساعات:</b> يُسترجع المبلغ فور تأكيد لاعب بديل من قائمة الانتظار.</div>
        <div>⚡ <b>تأكيد فوري:</b> أرسل إشعار التحويل خلال 15 دقيقة لضمان مقعدك.</div>
    </div>
    """, unsafe_allow_html=True)

with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input("رقم الجوال المسجل")
        can_reason = st.selectbox("سبب الاعتذار", [
            "تعارض في المواعيد أو انشغال طارئ",
            "إجهاد بدني أو إصابة",
            "ظرف عائلي طارئ",
            "صعوبة في المواصلات"
        ])
        btn_cancel_sub = st.form_submit_button("إلغاء المقعد وإتاحته للبديل", use_container_width=True)

        if btn_cancel_sub:
            clean_cp = clean_and_validate_sa_phone(can_phone_raw)
            if not clean_cp:
                st.error("فضلاً أدخل رقم جوال صحيح.")
            else:
                with get_db() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    cur = conn.cursor()
                    cur.execute("SELECT id, name, status FROM bookings WHERE phone=? AND session_day=? AND status IN ('confirmed', 'waitlist')", (clean_cp, db_session_key))
                    target = cur.fetchone()

                    if target:
                        cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (target[0],))
                        cur.execute("INSERT INTO cancellations (player_name, player_phone, session_day, court, reason) VALUES (?, ?, ?, 1, ?)",
                                    (target[1], clean_cp, db_session_key, can_reason))

                        promoted_name = None
                        if target[2] == 'confirmed':
                            cur.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_session_key,))
                            wait_player = cur.fetchone()
                            if wait_player:
                                cur.execute("UPDATE bookings SET status='confirmed', court=1 WHERE id=?", (wait_player[0],))
                                promoted_name = wait_player[1]
                        
                        conn.commit()

                        if "إصابة" in can_reason:
                            msg = f"سلامتك وما تشوف شر يا كابتن {target[1]}! 🌸 تم إلغاء حجزك بنجاح، وترجع لنا أقوى في التمارين القادمة."
                        elif "تعارض" in can_reason or "انشغال" in can_reason:
                            msg = f"تم قبول اعتذارك يا كابتن {target[1]}، نقدّر إبلاغك المبكر لإتاحة الفرصة لغيرك. مكانك محفوظ ونشوفك في التمرين الجاي! 🎾"
                        else:
                            msg = f"تم إلغاء الحجز بنجاح يا كابتن {target[1]}. تيسر أمورك وبانتظارك دائماً في بادل 99! ✨"

                        st.success(msg)
                        if promoted_name:
                            st.info(f"⚡ تم تصعيد الكابتن **{promoted_name}** من قائمة الانتظار للملعب مباشرة!")

                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error("لا يوجد حجز نشط مرتبط بهذا الرقم لتمرين اليوم.")

# ==========================================
# 6. تشكيلة الملعب
# ==========================================
st.markdown("---")

def get_level_badge(lvl):
    if lvl in ["Advanced", "متقدم"]:
        return "🔥 متقدم"
    elif lvl in ["Beginner", "مبتدئ"]:
        return "⚪ مبتدئ"
    return "🟢 متوسط"

slots_html = ""
for i in range(COURT_CAPACITY):
    if i < len(c1):
        p = c1[i]
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
        slots_html += '<div class="slot-box"><div class="slot-empty">مقعد شاغر ✨</div></div>'

st.markdown(f'<div class="padel-court"><div class="court-title">🏟️ كورت 1 ({len(c1)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>', unsafe_allow_html=True)

if waitlist:
    st.caption("📋 **قائمة الانتظار النشطة (تصعيد فوري):** " + " • ".join([f"#{idx+1} {w[1]}" for idx, w in enumerate(waitlist)]))

# ==========================================
# 7. زر الدعم المباشر
# ==========================================
support_msg = "مرحباً كابتن فارس، عندي استفسار بخصوص حجز بادل 99."
support_url = f"https://wa.me/966566261868?text={urllib.parse.quote(support_msg)}"
st.markdown(f'<a href="{support_url}" target="_blank" class="support-btn">💬 تواجه مشكلة؟ تواصل مباشرة عبر واتساب</a>', unsafe_allow_html=True)

# ==========================================
# 8. لوحة الإدارة والتحليلات وتصدير البيانات
# ==========================================
with st.expander("⚙️ لوحة الإدارة والتحليلات", expanded=False):
    pin_input = st.text_input("رمز الإدارة المشفر:", type="password")
    
    if pin_input:
        ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        p = str(pin_input).translate(ar_digits).strip()
        master_secret = None
        try:
            master_secret = st.secrets.get("ADMIN_PASSWORD", None) or st.secrets.get("ADMIN_PIN", None)
        except Exception:
            pass
        
        is_valid = hmac.compare_digest(p, str(master_secret).strip()) if master_secret else hmac.compare_digest(p, "Padel99#Master@2026")
        
        if is_valid:
            st.success("تم تأكيد الهوية 👑")
            
            with get_db() as conn:
                cur = conn.cursor()
                
                cur.execute("SELECT COUNT(*) FROM bookings WHERE status='confirmed'")
                total_confirmed = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM bookings WHERE payment_status='paid'")
                total_paid = cur.fetchone()[0]
                
                cur.execute("SELECT level, COUNT(*) FROM bookings GROUP BY level")
                levels_count = dict(cur.fetchall())
                
                c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
                c_kpi1.metric("إجمالي الحجوزات", total_confirmed)
                c_kpi2.metric("المؤكد دفعهم", f"{total_paid * 65} ر.س")
                c_kpi3.metric("المتوسط / المتقدم", f"{levels_count.get('متوسط', 0)} / {levels_count.get('متقدم', 0)}")
                
                cur.execute("""
                    SELECT session_day, name, phone, level, payment_status, 
                           COALESCE(hear_about, '-'), COALESCE(player_note, '-'),
                           strftime('%Y-%m-%d %H:%M', created_at)
                    FROM bookings 
                    ORDER BY id DESC
                """)
                raw_data = cur.fetchall()

            if raw_data:
                csv_buf = io.StringIO()
                csv_buf.write('\ufeff')
                writer = csv.writer(csv_buf)
                writer.writerow(["موعد التمرين", "اسم اللاعب", "رقم الجوال", "المستوى", "حالة الدفع", "مصدر المعرفة", "الملاحظات", "وقت التسجيل"])
                
                for row in raw_data:
                    clean_phone = clean_and_validate_sa_phone(row[2]) or row[2]
                    writer.writerow([row[0], row[1], f"'{clean_phone}", row[3], row[4], row[5], row[6], row[7]])
                    
                st.download_button(
                    "📥 تصدير السجل النظيف (Excel/CSV)",
                    csv_buf.getvalue().encode('utf-8-sig'),
                    f"padel_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )
        else:
            st.error("رمز الدخول غير صحيح.")
