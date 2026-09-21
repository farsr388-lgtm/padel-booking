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

[data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"] {
    font-family: "Material Symbols Rounded", "Source Sans Pro", sans-serif !important;
}

.hero-header { font-size: 1.55em; font-weight: 800; color: #f8fafc; margin: 0; line-height: 1.2; }
.hero-sub { font-size: 0.85em; color: #94a3b8; margin: 2px 0 6px 0; }
.contrast-pill { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 4px 8px; font-size: 0.74em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }
.promo-badge { background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.74em; margin-bottom: 4px; }

.hold-box {
    background: rgba(234, 179, 8, 0.15);
    border: 1.5px solid #eab308;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0;
    text-align: center;
}
.hold-title { color: #facc15; font-size: 0.95em; font-weight: 700; margin-bottom: 2px; }
.hold-sub { color: #fef08a; font-size: 0.8em; }

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
.slot-hold { color: #fef08a; font-weight: 600; font-size: 0.78em; line-height: 1.2; }
.slot-meta { display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 0.65em; margin-top: 2px; flex-wrap: wrap; }
.slot-empty { color: #64748b; font-size: 0.72em; }
.badge-loyalty { background-color: #1e3a8a; color: #93c5fd; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 600; }
.badge-level { background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 500; }
.badge-hold { background-color: #854d0e; color: #fef08a; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 600; }

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الثوابت الاقتصادية ومحرك البيانات
# ==========================================
DB_FILE = "group99_padel.db"
COURT_CAPACITY = 6

# الثوابت بالهللات (تجنباً لأخطاء التقريب المالي)
STANDARD_PRICE_HALALAS = 6500     # 65.00 ر.س
LOYALTY_DISCOUNT_HALALAS = 2000   # 20.00 ر.س خصم ولاء آمن من هامش الربح
DISCOUNTED_PRICE_HALALAS = 4500   # 45.00 ر.س تغطي كامل تكلفة الملعب والمستلزمات

HOLD_DURATION_MINUTES = 15

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    with get_db() as conn:
        cur = conn.cursor()
        
        # 1. جدول الحجوزات التشغيلية
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                session_day TEXT NOT NULL,
                court INTEGER DEFAULT 1,
                level TEXT DEFAULT 'متوسط',
                status TEXT CHECK(status IN ('hold', 'confirmed', 'waitlist', 'cancelled', 'expired')) DEFAULT 'hold',
                due_amount_halalas INTEGER NOT NULL DEFAULT 6500,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. قيد فريد يمنع التسجيل المزدوج في الحالات النشطة
        cur.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_active_player_session 
            ON bookings (phone, session_day) 
            WHERE status IN ('hold', 'confirmed', 'waitlist');
        ''')

        # 3. دفتر الأستاذ المالي (Financial Ledger) بالهللات
        cur.execute('''
            CREATE TABLE IF NOT EXISTS financial_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                entry_type TEXT CHECK(entry_type IN ('CHARGE', 'PAYMENT_RECEIVED', 'LOYALTY_DISCOUNT', 'REFUND')) NOT NULL,
                amount_halalas INTEGER NOT NULL,
                status TEXT CHECK(status IN ('pending', 'settled', 'voided')) DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
            )
        ''')

        # 4. جدول سجل الاعتذارات
        cur.execute('''
            CREATE TABLE IF NOT EXISTS cancellations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER,
                player_name TEXT,
                player_phone TEXT,
                session_day TEXT,
                reason TEXT,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# ==========================================
# 3. المحرك المحاسبي والتحرير التلقائي للمقاعد
# ==========================================
def cleanup_expired_holds(session_key):
    """تحرير المقاعد التي انتهت مهلة الـ 15 دقيقة المخصصة لسدادها وتصعيد الاحتياط."""
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.cursor()
        
        # تحديد الحجوزات المعلقة المنتهية صلاحيتها
        cur.execute("""
            SELECT id, name, phone FROM bookings 
            WHERE session_day=? AND status='hold' AND expires_at < datetime('now', 'localtime')
        """, (session_key,))
        expired = cur.fetchall()

        for row in expired:
            b_id, p_name, p_phone = row
            # تحديث الحالة إلى منتهي
            cur.execute("UPDATE bookings SET status='expired' WHERE id=?", (b_id,))
            # إبطال القيود المالية المعلقة
            cur.execute("UPDATE financial_ledger SET status='voided' WHERE booking_id=? AND status='pending'", (b_id,))
            
            # تصعيد لاعب من قائمة الاحتياط إن وجد، وإعطاؤه مهلة 15 دقيقة جديدة
            cur.execute("""
                SELECT id FROM bookings 
                WHERE session_day=? AND status='waitlist' 
                ORDER BY id ASC LIMIT 1
            """, (session_key,))
            wait_candidate = cur.fetchone()
            if wait_candidate:
                new_expiry = (datetime.now() + timedelta(minutes=HOLD_DURATION_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE bookings SET status='hold', expires_at=? WHERE id=?", (new_expiry, wait_candidate[0]))

        conn.commit()

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
cleanup_expired_holds(db_session_key)

# ==========================================
# 4. الواجهة الأساسية
# ==========================================
st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session}. متعة اللعب، بأعلى موثوقية.</div>", unsafe_allow_html=True)
st.markdown("<div class='contrast-pill'>⚡ حجز فوري مؤقت 15 دقيقة • تثبيت المقعد بإشعار التحويل</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين، واحصل على خصم 20 ر.س على تمرينك السابع</div>", unsafe_allow_html=True)

tab_book, tab_rules, tab_cancel = st.tabs(["⚡ حجز مقعد", "📜 القواعد", "❌ اعتذار"])

# --- تبويب الحجز ---
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
        
        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button("حجز مقعد مؤقت (15 دقيقة) 🚀", use_container_width=True)

        if btn_submit:
            if honeypot_val:
                st.error("تم رفض الطلب للاشتباه في نشاط آلي.")
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 2 or not clean_phone:
                st.error("فضلاً أدخل الاسم ورقم جوال صحيح يبدأ بـ 05.")
            else:
                try:
                    cleanup_expired_holds(db_session_key)
                    with get_db() as conn:
                        conn.execute("BEGIN IMMEDIATE")
                        cur = conn.cursor()
                        
                        # حساب المقاعد المشغولة (المؤكدة + المحجوزة مؤقتاً)
                        cur.execute("""
                            SELECT COUNT(*) FROM bookings 
                            WHERE session_day=? AND court=1 AND status IN ('confirmed', 'hold')
                        """, (db_session_key,))
                        active_slots = cur.fetchone()[0]

                        is_available = active_slots < COURT_CAPACITY
                        status_val = 'hold' if is_available else 'waitlist'
                        
                        # حساب الخصم الآمن للولاء
                        loyalty_count = get_loyalty_score(clean_phone)
                        has_discount = (loyalty_count > 0 and loyalty_count % 6 == 0)
                        due_amount = DISCOUNTED_PRICE_HALALAS if has_discount else STANDARD_PRICE_HALALAS
                        
                        expires_at_val = None
                        if status_val == 'hold':
                            expires_at_val = (datetime.now() + timedelta(minutes=HOLD_DURATION_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')

                        cur.execute("""
                            INSERT INTO bookings (name, phone, session_day, court, level, status, due_amount_halalas, expires_at) 
                            VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                        """, (clean_name, clean_phone, db_session_key, f_level, status_val, due_amount, expires_at_val))
                        booking_id = cur.lastrowid

                        # تسجيل القيود المحاسبية بالهللات
                        if status_val == 'hold':
                            cur.execute("""
                                INSERT INTO financial_ledger (booking_id, entry_type, amount_halalas, status, notes)
                                VALUES (?, 'CHARGE', ?, 'settled', 'استحقاق تمرين')
                            """, (booking_id, STANDARD_PRICE_HALALAS))
                            
                            if has_discount:
                                cur.execute("""
                                    INSERT INTO financial_ledger (booking_id, entry_type, amount_halalas, status, notes)
                                    VALUES (?, 'LOYALTY_DISCOUNT', ?, 'settled', 'خصم ولاء آمن')
                                """, (booking_id, -LOYALTY_DISCOUNT_HALALAS))

                            cur.execute("""
                                INSERT INTO financial_ledger (booking_id, entry_type, amount_halalas, status, notes)
                                VALUES (?, 'PAYMENT_RECEIVED', ?, 'pending', 'في انتظار التحويل')
                            """, (booking_id, due_amount))

                        wait_pos = None
                        if status_val == 'waitlist':
                            cur.execute("SELECT COUNT(*) FROM bookings WHERE session_day=? AND status='waitlist'", (db_session_key,))
                            wait_pos = cur.fetchone()[0]

                        conn.commit()

                    st.session_state["last_booking"] = {
                        "id": booking_id,
                        "name": clean_name,
                        "phone": clean_phone,
                        "court": "كورت 1",
                        "status": status_val,
                        "due_sar": due_amount / 100.0,
                        "has_discount": has_discount,
                        "wait_pos": wait_pos,
                        "session": display_session,
                        "is_new": True
                    }
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.warning("أنت مسجل بالفعل في تمرين اليوم (سواء بحجز مؤقت، مؤكد، أو في الاحتياط).")

    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        if lb["status"] == "hold":
            st.markdown(f"""
            <div class="hold-box">
                <div class="hold-title">⏳ مقعدك محجوز مؤقتاً لمدة 15 دقيقة يا كابتن {lb['name']}</div>
                <div class="hold-sub">يرجى تحويل المبلغ وتأكيد الحجز عبر الواتساب لتثبيت مقعدك رسمياً قبل إلغائه تلقائياً.</div>
            </div>
            """, unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={iban_raw}&color=000000&bgcolor=ffffff"
            pill_class = "price-pill-discount" if lb.get("has_discount") else "price-pill"
            pill_note = " (عرض الولاء ⭐)" if lb.get("has_discount") else ""

            card_html = f"""
<div class="alrajhi-card">
    <div class="card-top">
        <div class="bank-title">🏛️ مصرف الراجحي</div>
        <div class="{pill_class}">{lb['due_sar']:.0f} ر.س{pill_note}</div>
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
        <div style="font-size: 0.75em; color: #cbd5e1;">💡 <b>لحفظ المستفيد:</b></div>
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
            
            wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {lb['name']}\nالتمرين: {lb['session']} (كورت 1)\nالمطلوب: {lb['due_sar']:.0f} ر.س\n\nمرفق إشعار التحويل البنكي لحساب كابتن فارس العصيمي لتثبيت المقعد."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتثبيت المقعد</a>', unsafe_allow_html=True)
        elif lb["status"] == "waitlist":
            st.info(f"اكتملت المقاعد النشطة حالياً. أنت في قائمة الاحتياط رقم ({lb.get('wait_pos', 1)}). إذا لم يؤكد أحد المحجوزين خلال 15 دقيقة، سيصلك المقعد تلقائياً.")

# --- تبويب القواعد ---
with tab_rules:
    st.markdown("""
    <div style="background:#18181b; border:1px solid #27272a; border-radius:10px; padding:10px; margin:8px 0; font-size:0.82em; color:#e2e8f0; line-height:1.4;">
        <div style="margin-bottom:8px;">⏱️ <b>مهلة السداد:</b> الحجز مؤقت لمدة 15 دقيقة ويتحرر المقعد تلقائياً للاحتياط إذا لم يُرسل الإشعار.</div>
        <div style="margin-bottom:8px;">⚠️ <b>الاعتذار:</b> يسترجع المبلغ كاملاً في حال توفر لاعب بديل من قائمة الاحتياط لتغطية المقعد.</div>
        <div>⭐ <b>الولاء الآمن:</b> كل 6 تمارين تمنحك خصماً بقيمة 20 ر.س على تمرينك القادم.</div>
    </div>
    """, unsafe_allow_html=True)

# --- تبويب الاعتذار ---
with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input("رقم الجوال المسجل")
        can_reason = st.selectbox("سبب الاعتذار", [
            "تعارض في المواعيد",
            "إجهاد بدني أو إصابة",
            "ظرف طارئ",
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
                    cur.execute("""
                        SELECT id, name, status, due_amount_halalas FROM bookings 
                        WHERE phone=? AND session_day=? AND status IN ('confirmed', 'hold', 'waitlist')
                    """, (clean_cp, db_session_key))
                    target = cur.fetchone()

                    if target:
                        b_id, p_name, old_status, due_amt = target
                        cur.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (b_id,))
                        cur.execute("INSERT INTO cancellations (booking_id, player_name, player_phone, session_day, reason) VALUES (?, ?, ?, ?, ?)",
                                    (b_id, p_name, clean_cp, db_session_key, can_reason))

                        # تسجيل قيد عكسي إن كان الحساب مؤكداً
                        if old_status == 'confirmed':
                            cur.execute("""
                                INSERT INTO financial_ledger (booking_id, entry_type, amount_halalas, status, notes)
                                VALUES (?, 'REFUND', ?, 'settled', 'استرداد نتيجة اعتذار مؤكد')
                            """, (b_id, -due_amt))

                        # تصعيد فوري لأول لاعب احتياط
                        if old_status in ('confirmed', 'hold'):
                            cur.execute("SELECT id FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_session_key,))
                            wait_player = cur.fetchone()
                            if wait_player:
                                wp_id = wait_player[0]
                                new_expiry = (datetime.now() + timedelta(minutes=HOLD_DURATION_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
                                cur.execute("UPDATE bookings SET status='hold', expires_at=? WHERE id=?", (new_expiry, wp_id))
                        
                        conn.commit()
                        st.success(f"تم قبول اعتذارك يا كابتن {p_name}. تم إتاحة المقعد للاعب التالي.")
                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error("لا يوجد حجز نشط مرتبط بهذا الرقم.")

# ==========================================
# 5. تشكيلة الملعب (تحديث حي عبر Fragment)
# ==========================================
st.markdown("---")

def get_level_badge(lvl):
    if lvl in ["Advanced", "متقدم"]:
        return "🔥 متقدم"
    elif lvl in ["Beginner", "مبتدئ"]:
        return "⚪ مبتدئ"
    return "🟢 متوسط"

@st.fragment(run_every="8s")
def render_live_court(session_key):
    cleanup_expired_holds(session_key)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, name, phone, level, status FROM bookings 
            WHERE session_day=? AND court=1 AND status IN ('confirmed', 'hold')
            ORDER BY id ASC LIMIT 6
        """, (session_key,))
        c1 = c.fetchall()
        c.execute("SELECT id, name, phone FROM bookings WHERE session_day=? AND status='waitlist' ORDER BY id ASC", (session_key,))
        waitlist = c.fetchall()

    confirmed_count = sum(1 for p in c1 if p[4] == 'confirmed')
    hold_count = sum(1 for p in c1 if p[4] == 'hold')
    st.caption(f"⏰ 9:30 م إلى 11:00 م | كورت 1 • <b>المؤكدين: {confirmed_count}/6</b> (معلق: {hold_count}) ⚡", unsafe_allow_html=True)

    slots_html = ""
    for i in range(COURT_CAPACITY):
        if i < len(c1):
            p = c1[i]
            points = (get_loyalty_score(p[2]) % 6)
            pts_badge = f"⭐ {points}/6"
            lvl_badge = get_level_badge(p[3])
            
            if p[4] == 'confirmed':
                status_icon = "✅"
                slot_class = "slot-occupied"
                badge_tag = f'<span class="badge-loyalty">{pts_badge}</span>'
            else:
                status_icon = "⏳ مهلة"
                slot_class = "slot-hold"
                badge_tag = '<span class="badge-hold">بانتظار التحويل</span>'

            slots_html += f'''<div class="slot-box">
                <div class="{slot_class}">🎾 {p[1]}</div>
                <div class="slot-meta">
                    <span class="badge-level">{lvl_badge}</span>
                    {badge_tag}
                    <span>{status_icon}</span>
                </div>
            </div>'''
        else:
            slots_html += '<div class="slot-box"><div class="slot-empty">مقعد شاغر ✨</div></div>'

    st.markdown(f'<div class="padel-court"><div class="court-title">🏟️ كورت 1 ({len(c1)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>', unsafe_allow_html=True)

    if waitlist:
        st.caption("📋 **أولوية الاحتياط:** " + " • ".join([f"{idx+1}. {w[1]}" for idx, w in enumerate(waitlist)]))

render_live_court(db_session_key)

# ==========================================
# 6. لوحة الإدارة واعتماد السداد الفوري
# ==========================================
support_msg = "مرحباً كابتن فارس، عندي استفسار بخصوص حجز بادل 99."
support_url = f"https://wa.me/966566261868?text={urllib.parse.quote(support_msg)}"
st.markdown(f'<a href="{support_url}" target="_blank" class="support-btn">💬 تواجه مشكلة؟ تواصل مباشرة عبر واتساب</a>', unsafe_allow_html=True)

with st.expander("⚙️ لوحة الإدارة واعتماد الحوالات", expanded=False):
    pin_input = st.text_input("رمز الإدارة المشفر:", type="password")
    
    if pin_input:
        ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        p = str(pin_input).translate(ar_digits).strip()
        master_secret = st.secrets.get("ADMIN_PIN", None)
        
        if not master_secret:
            st.error("⚠️ يرجى ضبط قيمة ADMIN_PIN داخل ملف secrets.toml.")
        elif hmac.compare_digest(p, str(master_secret).strip()):
            st.success("تم تأكيد الهوية والصلاحيات الإدارية 👑")
            
            with get_db() as conn:
                cur = conn.cursor()
                # جلب الحجوزات المعلقة لتأكيد السداد بنقرة زر
                cur.execute("""
                    SELECT id, name, phone, due_amount_halalas, expires_at 
                    FROM bookings 
                    WHERE session_day=? AND status='hold'
                """, (db_session_key,))
                pending_holds = cur.fetchall()

            if pending_holds:
                st.markdown("#### ⏳ حجوزات بانتظار تأكيد التحويل البنكي:")
                for ph in pending_holds:
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**{ph[1]}** ({ph[2]}) — المبلغ: {ph[3]/100:.0f} ر.س | ينتهي: {ph[4]}")
                    with col_btn:
                        if st.button("اعتماد ✅", key=f"settle_{ph[0]}", use_container_width=True):
                            with get_db() as conn:
                                cur = conn.cursor()
                                cur.execute("UPDATE bookings SET status='confirmed', expires_at=NULL WHERE id=?", (ph[0],))
                                cur.execute("UPDATE financial_ledger SET status='settled' WHERE booking_id=?", (ph[0],))
                                conn.commit()
                            st.rerun()
            else:
                st.info("لا توجد مقاعد معلقة بانتظار التحويل حالياً.")

            # تصدير التقرير المحاسبي الشامل
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT 
                        b.id, b.session_day, b.name, b.phone, b.status,
                        COALESCE(fl.entry_type, 'NONE'),
                        COALESCE(fl.amount_halalas / 100.0, 0.0),
                        COALESCE(fl.status, 'none'),
                        b.created_at
                    FROM bookings b
                    LEFT JOIN financial_ledger fl ON b.id = fl.booking_id
                    ORDER BY b.id DESC
                """)
                raw_data = cur.fetchall()

            if raw_data:
                csv_buf = io.StringIO()
                csv_buf.write('\ufeff')
                writer = csv.writer(csv_buf)
                writer.writerow(["معرف الحجز", "تاريخ التمرين", "الاسم", "الجوال", "حالة الحجز", "نوع القيد المالي", "المبلغ (ر.س)", "حالة القيد", "وقت التسجيل"])
                for row in raw_data:
                    writer.writerow(row)
                    
                st.download_button(
                    "📥 تصدير السجل المالي والمطابقة البنكية (CSV)",
                    csv_buf.getvalue().encode('utf-8-sig'),
                    f"padel_audit_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )
        else:
            st.error("رمز الدخول غير صحيح.")
