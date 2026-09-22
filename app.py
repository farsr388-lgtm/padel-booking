import streamlit as st
import sqlite3
import io
import csv
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة والهوية البصرية للجوال
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

.hero-header { font-size: 1.55em; font-weight: 800; color: #f8fafc; margin: 0; line-height: 1.2; }
.hero-sub { font-size: 0.85em; color: #94a3b8; margin: 2px 0 6px 0; }
.contrast-pill { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 4px 8px; font-size: 0.74em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }
.promo-badge { background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.74em; margin-bottom: 4px; }

/* صندوق المهلة */
.hold-box {
    background: rgba(245, 158, 11, 0.12);
    border: 1.5px solid #f59e0b;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0;
    text-align: center;
}
.hold-title { color: #fbbf24; font-size: 0.95em; font-weight: 700; margin-bottom: 2px; }
.hold-sub { color: #fef3c7; font-size: 0.8em; }

/* بطاقة الراجحي */
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
.price-pill-discount { background: #f59e0b; color: #451a03; padding: 2px 7px; border-radius: 12px; font-weight: 700; font-size: 0.8em; }
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

/* تخطيط الملعب */
.padel-court { background: #064e3b; border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 10px; padding: 8px; margin: 8px 0; }
.court-title { text-align: center; color: #a7f3d0; font-weight: 700; font-size: 0.85em; margin-bottom: 6px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 3px; }
.court-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.slot-box { background: rgba(15, 23, 42, 0.9); border-radius: 6px; padding: 6px 4px; text-align: center; min-height: 48px; display: flex; flex-direction: column; justify-content: center; align-items: center; }

.slot-confirmed { border: 1.5px solid #10b981; }
.slot-hold { border: 1.5px dashed #f59e0b; }
.slot-empty { border: 1px dashed rgba(255, 255, 255, 0.15); }

.badge-confirmed { background: #065f46; color: #6ee7b7; padding: 1px 5px; border-radius: 4px; font-size: 0.68em; font-weight: 700; }
.badge-hold { background: #78350f; color: #fde68a; padding: 1px 5px; border-radius: 4px; font-size: 0.68em; font-weight: 700; }
.badge-loyalty { background-color: #1e3a8a; color: #93c5fd; padding: 1px 4px; border-radius: 3px; font-size: 0.68em; font-weight: 600; }
.badge-level { background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 4px; border-radius: 3px; font-size: 0.68em; }

.kpi-container { display: flex; gap: 8px; margin-bottom: 10px; }
.kpi-card { flex: 1; background: #1e293b; border-radius: 8px; padding: 8px; text-align: center; border: 1px solid #334155; }
.kpi-num { font-size: 1.15em; font-weight: 800; }
.kpi-lbl { font-size: 0.72em; color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الثوابت وقاعدة البيانات
# ==========================================
DB_FILE = "group99_padel.db"
COURT_CAPACITY = 6
HOLD_MINUTES = 15

PRICE_STANDARD = 65
PRICE_DISCOUNTED = 45  # بعد خصم 20 ريال للولاء الآمن

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
                status TEXT CHECK(status IN ('hold', 'confirmed', 'waitlist', 'cancelled', 'expired')) DEFAULT 'hold',
                amount_sar INTEGER NOT NULL DEFAULT 65,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # منع تسجيل نفس اللاعب مرتين في نفس الحصة
        cur.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_active_player_session 
            ON bookings (phone, session_day) 
            WHERE status IN ('hold', 'confirmed', 'waitlist');
        ''')
        conn.commit()

init_db()

# ==========================================
# 3. محرك التحرير والتصعيد التلقائي للمقاعد
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

    if weekday == 6:      # الأحد
        days_to_add = 0
        d_ar = "الأحد"
    elif weekday == 0:    # الإثنين
        days_to_add = 1
        d_ar = "الثلاثاء"
    elif weekday == 1:    # الثلاثاء
        days_to_add = 0
        d_ar = "الثلاثاء"
    elif weekday == 2:    # الأربعاء
        days_to_add = 1
        d_ar = "الخميس"
    elif weekday == 3:    # الخميس
        days_to_add = 0
        d_ar = "الخميس"
    elif weekday == 4:    # الجمعة
        days_to_add = 2
        d_ar = "الأحد"
    else:                 # السبت
        days_to_add = 1
        d_ar = "الأحد"

    target_date = now + timedelta(days=days_to_add)
    label_ar = f"{d_ar} ({target_date.strftime('%d/%m')})"
    db_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"
    return label_ar, db_key

display_session, db_session_key = get_next_session()

def process_expirations_and_queue(session_key):
    """إلغاء من لم يؤكد تحويله خلال 15 دقيقة وسحب أول شخص من الاحتياط فوراً"""
    ksa_tz = timezone(timedelta(hours=3))
    now_str = datetime.now(ksa_tz).strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        
        # 1. رصد المقاعد المنتهية
        cur.execute("""
            SELECT id FROM bookings 
            WHERE session_day=? AND status='hold' AND expires_at < ?
        """, (session_key, now_str))
        expired_seats = cur.fetchall()

        for s in expired_seats:
            cur.execute("UPDATE bookings SET status='expired' WHERE id=?", (s[0],))
            
            # تصعيد أول لاعب من قائمة الاحتياط
            cur.execute("""
                SELECT id FROM bookings 
                WHERE session_day=? AND status='waitlist' 
                ORDER BY id ASC LIMIT 1
            """, (session_key,))
            candidate = cur.fetchone()
            if candidate:
                new_exp = (datetime.now(ksa_tz) + timedelta(minutes=HOLD_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE bookings SET status='hold', expires_at=? WHERE id=?", (new_exp, candidate[0]))

        conn.commit()

process_expirations_and_queue(db_session_key)

# ==========================================
# 4. الواجهة الأساسية
# ==========================================
st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session}. تنظيم آلي دقيق وحجز مؤكد.</div>", unsafe_allow_html=True)
st.markdown("<div class='contrast-pill'>⏱️ مهلة السداد: 15 دقيقة لإرسال إشعار التحويل قبل تحرير المقعد للاحتياط</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين، وتمرينك السابع بـ 45 ر.س فقط</div>", unsafe_allow_html=True)

tab_book, tab_cancel = st.tabs(["⚡ حجز مقعد", "❌ اعتذار"])

with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        f_name = st.text_input("الاسم الثلاثي")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx")
        f_level = st.selectbox("المستوى", ["متوسط", "متقدم", "مبتدئ"])
        btn_submit = st.form_submit_button("حجز مقعد (مهلة 15 دقيقة) 🚀", use_container_width=True)

        if btn_submit:
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 2 or not clean_phone:
                st.error("فضلاً أدخل الاسم ورقم جوال صحيح يبدأ بـ 05.")
            else:
                process_expirations_and_queue(db_session_key)
                ksa_tz = timezone(timedelta(hours=3))
                expiry_dt = datetime.now(ksa_tz) + timedelta(minutes=HOLD_MINUTES)
                expiry_str = expiry_dt.strftime('%Y-%m-%d %H:%M:%S')

                loyalty_count = get_loyalty_score(clean_phone)
                has_discount = (loyalty_count > 0 and loyalty_count % 6 == 0)
                amount_to_pay = PRICE_DISCOUNTED if has_discount else PRICE_STANDARD

                try:
                    with get_db() as conn:
                        conn.execute("BEGIN IMMEDIATE")
                        cur = conn.cursor()
                        
                        # حساب المقاعد المشغولة (المؤكدة + التي في مهلة الـ 15 دقيقة)
                        cur.execute("""
                            SELECT COUNT(*) FROM bookings 
                            WHERE session_day=? AND court=1 AND status IN ('confirmed', 'hold')
                        """, (db_session_key,))
                        active_count = cur.fetchone()[0]

                        assigned_status = 'hold' if active_count < COURT_CAPACITY else 'waitlist'
                        assigned_exp = expiry_str if assigned_status == 'hold' else None

                        cur.execute("""
                            INSERT INTO bookings (name, phone, session_day, court, level, status, amount_sar, expires_at)
                            VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                        """, (clean_name, clean_phone, db_session_key, f_level, assigned_status, amount_to_pay, assigned_exp))
                        b_id = cur.lastrowid
                        conn.commit()

                    st.session_state["ticket"] = {
                        "id": b_id,
                        "name": clean_name,
                        "status": assigned_status,
                        "amount": amount_to_pay,
                        "has_discount": has_discount,
                        "expires_at": expiry_dt
                    }
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.warning("أنت مسجل بالفعل في تمرين اليوم.")

    if "ticket" in st.session_state:
        tk = st.session_state["ticket"]
        if tk["status"] == "hold":
            ksa_tz = timezone(timedelta(hours=3))
            rem_minutes = max(0, int((tk["expires_at"] - datetime.now(ksa_tz)).total_seconds() // 60))

            pill_cls = "price-pill-discount" if tk.get("has_discount") else "price-pill"
            pill_tag = " (عرض الولاء ⭐)" if tk.get("has_discount") else ""

            st.markdown(f"""
            <div class="hold-box">
                <div class="hold-title">⏳ مقعدك محجوز مؤقتاً لمدة {rem_minutes} دقيقة يا كابتن {tk['name']}</div>
                <div class="hold-sub">يرجى تحويل المبلغ وتأكيد الحجز فورياً لتثبيت المقعد رسمياً.</div>
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
        <div class="{pill_cls}">{tk['amount']} ر.س{pill_tag}</div>
    </div>
    <div style="text-align:center;">
        <div class="qr-container">
            <img src="{qr_url}" alt="QR" />
        </div>
    </div>
    <div class="card-owner">فارس ربيع بن عواض العصيمي</div>
    <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الحساب (اضغط للنسخ):</div>
    <div class="copy-badge" onclick="navigator.clipboard.writeText('{acc_raw}'); alert('تم نسخ رقم الحساب! 📋');">
        <span>{acc_raw}</span><span>📋</span>
    </div>
    <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الآيبان (اضغط للنسخ):</div>
    <div class="copy-badge" onclick="navigator.clipboard.writeText('{iban_raw}'); alert('تم نسخ الآيبان! 📋');">
        <span>{iban_display}</span><span>📋</span>
    </div>
    <div style="margin-top: 6px; padding: 6px 8px; background: rgba(56, 189, 248, 0.08); border-radius: 6px; border: 1px dashed rgba(56, 189, 248, 0.3); display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 0.75em; color: #cbd5e1;">💡 <b>اسم المستفيد:</b></div>
        <div class="copy-badge" style="margin-bottom:0; padding:2px 6px; font-size:0.8em;" onclick="navigator.clipboard.writeText('بادل 99'); alert('تم النسخ! 📋');">
            <span>بادل 99</span><span>📋</span>
        </div>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
            wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {tk['name']}\nالتمرين: {display_session}\nالمطلوب: {tk['amount']} ر.س\n\nمرفق إشعار التحويل لحساب كابتن فارس العصيمي لتثبيت الحجز النهائي."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتثبيت المقعد</a>', unsafe_allow_html=True)
        elif tk["status"] == "waitlist":
            st.info("اكتملت المقاعد الـ 6 حالياً. تم إدراجك في قائمة الاحتياط؛ إذا لم يحوّل أحد اللاعبين خلال 15 دقيقة سيصعد مقعدك تلقائياً.")

with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input("رقم الجوال المسجل للإلغاء")
        if st.form_submit_button("إلغاء المقعد وإتاحته للبديل", use_container_width=True):
            clean_cp = clean_and_validate_sa_phone(can_phone_raw)
            if clean_cp:
                with get_db() as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE bookings SET status='cancelled' WHERE phone=? AND session_day=? AND status IN ('hold', 'confirmed')", (clean_cp, db_session_key))
                    conn.commit()
                process_expirations_and_queue(db_session_key)
                st.success("تم إلغاء المقعد بنجاح وتصعيد الاحتياط.")
                st.rerun()

# ==========================================
# 5. تشكيلة الملعب (تحديث لحظي كل 8 ثوانٍ)
# ==========================================
st.markdown("---")

def get_level_badge(lvl):
    if lvl in ["Advanced", "متقدم"]:
        return "🔥 متقدم"
    elif lvl in ["Beginner", "مبتدئ"]:
        return "⚪ مبتدئ"
    return "🟢 متوسط"

@st.fragment(run_every="8s")
def render_court_live(session_key):
    process_expirations_and_queue(session_key)
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, phone, level, status, expires_at 
            FROM bookings 
            WHERE session_day=? AND court=1 AND status IN ('confirmed', 'hold') 
            ORDER BY id ASC LIMIT 6
        """, (session_key,))
        players = cur.fetchall()

        cur.execute("SELECT id, name FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (session_key,))
        waitlist = cur.fetchall()

    slots_html = ""
    for i in range(COURT_CAPACITY):
        if i < len(players):
            p_id, p_name, p_phone, p_lvl, p_status, p_exp = players[i]
            pts = (get_loyalty_score(p_phone) % 6)
            lvl_b = get_level_badge(p_lvl)

            if p_status == 'confirmed':
                box_c = "slot-confirmed"
                badge = '<span class="badge-confirmed">مدفوع ومؤكد ✅</span>'
            else:
                rem_m = 0
                if p_exp:
                    exp_dt = datetime.strptime(p_exp, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ksa_tz)
                    rem_m = max(0, int((exp_dt - now).total_seconds() // 60))
                box_c = "slot-hold"
                badge = f'<span class="badge-hold">مهلة تحويل: {rem_m} د ⏳</span>'

            slots_html += f'''
            <div class="slot-box {box_c}">
                <div style="font-weight:700; font-size:0.82em; color:#fff;">🎾 {p_name}</div>
                <div style="margin-top:3px; display:flex; gap:3px; justify-content:center;">
                    <span class="badge-level">{lvl_b}</span>
                    <span class="badge-loyalty">⭐ {pts}/6</span>
                    {badge}
                </div>
            </div>'''
        else:
            slots_html += '''
            <div class="slot-box slot-empty">
                <div style="color:#64748b; font-size:0.75em;">مقعد شاغر ✨</div>
            </div>'''

    st.markdown(f'<div class="padel-court"><div class="court-title">🏟️ كورت 1 • حالة الملعب الآن ({len(players)}/6)</div><div class="court-grid">{slots_html}</div></div>', unsafe_allow_html=True)

    if waitlist:
        st.caption("📋 **قائمة الاحتياط:** " + " • ".join([f"{idx+1}. {w[1]}" for idx, w in enumerate(waitlist)]))

render_court_live(db_session_key)

# ==========================================
# 6. لوحة المنظم (فرز التحويلات والتأكيد بنقرة زر)
# ==========================================
with st.expander("⚙️ لوحة الإدارة (فرز التحويلات البنكية)", expanded=False):
    pin_input = st.text_input("رمز الدخول المشفر:", type="password")
    
    if pin_input:
        master_secret = st.secrets.get("ADMIN_PIN", None)
        ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        clean_pin = str(pin_input).translate(ar_digits).strip()

        if master_secret and hmac.compare_digest(clean_pin, str(master_secret).strip()):
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, phone, status, amount_sar, expires_at FROM bookings WHERE session_day=? AND court=1 AND status IN ('confirmed', 'hold')", (db_session_key,))
                roster = cur.fetchall()

            confirmed_players = [p for p in roster if p[3] == 'confirmed']
            hold_players = [p for p in roster if p[3] == 'hold']

            cash_in_bank = sum(p[4] for p in confirmed_players)
            cash_waiting = sum(p[4] for p in hold_players)

            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-card">
                    <div class="kpi-num" style="color:#10b981;">{cash_in_bank} ر.س</div>
                    <div class="kpi-lbl">تم استلامها في الحساب ({len(confirmed_players)} لاعبين)</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-num" style="color:#f59e0b;">{cash_waiting} ر.س</div>
                    <div class="kpi-lbl">بانتظار التحويل بالمهلة ({len(hold_players)} لاعبين)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### ⏳ لاعبين بانتظار التحويل (اضغط تأكيد عند وصول الإشعار):")
            if hold_players:
                for hp in hold_players:
                    c_info, c_action = st.columns([3, 1])
                    with c_info:
                        st.write(f"• **{hp[1]}** ({hp[2]}) — المبلغ: {hp[4]} ر.س")
                    with c_action:
                        if st.button("تأكيد الحوالة ✅", key=f"confirm_{hp[0]}", use_container_width=True):
                            with get_db() as conn:
                                cur = conn.cursor()
                                cur.execute("UPDATE bookings SET status='confirmed', expires_at=NULL WHERE id=?", (hp[0],))
                                conn.commit()
                            st.rerun()
            else:
                st.info("لا توجد مقاعد معلقة بانتظار التحويل.")

            st.markdown("##### ✅ المقاعد المؤكدة والمدفوعة:")
            if confirmed_players:
                for cp in confirmed_players:
                    st.write(f"• **{cp[1]}** ({cp[2]}) — مسدد: {cp[4]} ر.س")
            else:
                st.caption("لم يتم تأكيد أي مقعد بعد.")
        else:
            st.error("رمز الدخول غير صحيح.")
