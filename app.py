import streamlit as st
import streamlit.components.v1 as components
import psycopg2
import pandas as pd
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعدادات النظام وتجريد الواجهة
# ==========================================
st.set_page_config(
    page_title="بادل 99 | مجتمع الرياضيين",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"], footer, #MainMenu { display: none !important; }
.block-container { padding: 0.5rem !important; max-width: 600px !important; }
p, div, span, label, input, select, button, h1, h2, h3, .stMarkdown {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    direction: rtl; text-align: right; box-sizing: border-box;
}
[data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"] { font-family: "Material Symbols Rounded" !important; }

.hero-header { font-size: 1.6em; font-weight: 800; color: #fdf4ff; margin: 0; line-height: 1.2; }
.hero-sub { font-size: 0.85em; color: #cbd5e1; margin: 4px 0 8px 0; }
.hero-pill { background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 6px; padding: 4px 8px; font-size: 0.75em; color: #7dd3fc; font-weight: 600; display: inline-block; margin-bottom: 8px;}

.thankyou-box { background: rgba(16, 185, 129, 0.15); border: 1.5px solid #10b981; border-radius: 10px; padding: 10px; margin: 8px 0; text-align: center; }
.waitlist-box { background: rgba(245, 158, 11, 0.15); border: 1.5px solid #f59e0b; border-radius: 10px; padding: 10px; margin: 8px 0; text-align: center; }
.alrajhi-card { background: #111418; border: 1.5px solid #2d3748; border-radius: 14px; padding: 12px; margin: 8px 0; color: #ffffff; }
.card-top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 5px; margin-bottom: 8px; }
.bank-title { font-size: 0.9em; font-weight: 700; color: #f8fafc; }
.price-pill { background: #10b981; color: #022c22; padding: 2px 7px; border-radius: 12px; font-weight: 700; font-size: 0.8em; }
.qr-container { background: #ffffff; padding: 6px; border-radius: 8px; display: inline-block; margin: 2px auto 6px auto; }
.qr-container img { display: block; width: 115px; height: 115px; }
.copy-badge { background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 6px 8px; font-family: monospace; font-size: 0.84em; color: #38bdf8; font-weight: 600; display: flex; justify-content: space-between; align-items: center; cursor: pointer; margin-bottom: 5px; }
.wa-btn { display: block; width: 100%; background: #25D366; color: white !important; text-align: center; padding: 10px; border-radius: 8px; font-weight: 700; text-decoration: none; margin-top: 6px; font-size: 0.88em; }

.slot-box { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 6px; text-align: center; min-height: 48px; display: flex; flex-direction: column; justify-content: center; align-items: center; margin-bottom: 6px; }
.slot-occupied { color: #f4f4f5; font-weight: 600; font-size: 0.8em; line-height: 1.2; }
.slot-meta { display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.7em; margin-top: 2px; }
.slot-empty { color: #64748b; font-size: 0.75em; }
.court-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }

div[data-testid="stTextInput"]:has(input[aria-label="hp_sec"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# مؤقت التحديث اللحظي
components.html("<script>setTimeout(function(){window.parent.document.querySelector('button[kind=\"header\"]')?.click();}, 8000);</script>", height=0, width=0)

# ==========================================
# 2. الثوابت وقاعدة البيانات السحابية
# ==========================================
COURT_COST = 300       
TICKET_PRICE = 65      
CAPACITY = 6           
BREAK_EVEN_POINT = 5   
LOYALTY_LIABILITY = round(TICKET_PRICE / 7, 2) 

DB_URL = st.secrets["SUPABASE_DB_URL"]

def fetch_all(query, params=()):
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()

def fetch_one(query, params=()):
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
    finally:
        conn.close()

def execute_query(query, params=()):
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
    finally:
        conn.close()

def init_db():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                session_day TEXT NOT NULL,
                court INTEGER DEFAULT 1,
                level TEXT DEFAULT 'متوسط',
                status TEXT DEFAULT 'confirmed',
                payment_status TEXT DEFAULT 'pending',
                hear_about TEXT DEFAULT '',
                player_note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        execute_query('''
            CREATE TABLE IF NOT EXISTS cancellations (
                id SERIAL PRIMARY KEY,
                player_name TEXT,
                player_phone TEXT,
                session_day TEXT,
                reason TEXT,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")

init_db()

# ==========================================
# 3. دوال مساعدة
# ==========================================
def sanitize_phone(raw_phone):
    if not raw_phone: return None
    p = re.sub(r'\D', '', str(raw_phone).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
    if p.startswith("966"): p = "0" + p[3:]
    elif p.startswith("5"): p = "0" + p
    return p if re.match(r"^05[0-9]{8}$", p) else None

def mask_name_for_privacy(full_name):
    parts = full_name.strip().split()
    if len(parts) == 1: return parts[0]
    return f"{parts[0]} {parts[1][0]}."

def get_session_info():
    tz = timezone(timedelta(hours=3))
    now = datetime.now(tz)
    days_to_add = 0 if now.weekday() in [1, 3, 6] else 1 
    target = now + timedelta(days=days_to_add)
    d_name = {6: "الأحد", 0: "الثلاثاء", 1: "الثلاثاء", 2: "الخميس", 3: "الخميس", 4: "الأحد", 5: "الأحد"}[now.weekday()]
    return f"{d_name} ({target.strftime('%d/%m')})", f"{d_name} {target.strftime('%Y-%m-%d')}"

display_sess, db_sess_key = get_session_info()

# ==========================================
# 4. الواجهة الأساسية والاستبيان
# ==========================================
st.markdown("<div class='hero-header'>بادل 99 | مجتمع الرياضيين</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-sub'>تجمع أبطال البادل، تحدي، وحماس للجيل الجديد.</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-pill'>⚡ مباريات تنافسية • تنظيم احترافي • مجتمع رياضي</div>", unsafe_allow_html=True)
st.caption(f"⏰ {display_sess} | 9:00 م – 11:00 م | السعة: {CAPACITY} لاعبين")

c1_players = fetch_all("SELECT id, name, phone, payment_status, level FROM bookings WHERE session_day=%s AND status='confirmed' ORDER BY id ASC LIMIT %s", (db_sess_key, CAPACITY))
waitlist = fetch_all("SELECT id, name FROM bookings WHERE session_day=%s AND status='waitlist' ORDER BY id ASC", (db_sess_key,))

tab_book, tab_rules, tab_cancel = st.tabs(["⚡ حجز مقعد", "📜 قوانين التجمع", "❌ اعتذار"])

with tab_book:
    with st.form("book_form", clear_on_submit=False):
        name = st.text_input("الاسم الكريم")
        phone = st.text_input("رقم الجوال (للتواصل الإداري ولا يظهر علناً)", placeholder="05xxxxxxxx")
        level = st.selectbox("مستوى اللعب", ["🟢 متوسط - تبادل", "🔥 متقدم - تكتيك", "⚪ مبتدئ - تعلم"])
        
        with st.expander("💡 ملاحظات إضافية (اختياري)", expanded=False):
            f_source = st.selectbox("كيف تعرفت على الجلسات؟", ["قروب واتساب رياضي", "توصية من صديق", "منصة إكس / تيك توك", "أخرى"])
            f_note = st.text_input("أي تفضيل يخص التمرين:", placeholder="مثلاً: تفضيل وقت محدد، كرات معينة...")

        hp = st.text_input("hp_sec", label_visibility="collapsed") 
        
        if st.form_submit_button("تأكيد المقعد 🚀", use_container_width=True):
            if hp: st.stop()
            clean_p = sanitize_phone(phone)
            
            if len(name.strip()) < 2 or not clean_p:
                st.error("بيانات غير مكتملة، تأكد من إدخال رقم جوال سعودي صحيح.")
            else:
                if fetch_one("SELECT id FROM bookings WHERE phone=%s AND session_day=%s AND status IN ('confirmed', 'waitlist')", (clean_p, db_sess_key)):
                    st.warning("أنت مسجل مسبقاً في هذا التمرين.")
                else:
                    status = 'confirmed' if len(c1_players) < CAPACITY else 'waitlist'
                    execute_query("INSERT INTO bookings (name, phone, session_day, level, status, hear_about, player_note) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                  (name.strip(), clean_p, db_sess_key, level, status, f_source, f_note))
                    st.session_state["last_booking"] = {"name": name.strip(), "status": status, "session": display_sess}
                    st.rerun()

    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        if lb["status"] == "confirmed":
            st.markdown(f'<div class="thankyou-box"><div style="color:#10b981; font-weight:bold;">✅ تم تأكيد حجزك يا كابتن {lb["name"]}!</div><div style="font-size:0.85em; color:#e2e8f0;">مقعدك محجوز في تمرين {lb["session"]}.</div></div>', unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={iban_raw}&color=000000&bgcolor=ffffff"
            
            st.markdown(f"""
            <div class="alrajhi-card">
                <div class="card-top"><div class="bank-title">🏛️ مصرف الراجحي</div><div class="price-pill">{TICKET_PRICE} ر.س</div></div>
                <div style="text-align:center;"><div class="qr-container"><img src="{qr_url}" alt="QR" /></div></div>
                <div style="text-align:center; font-weight:bold; margin-bottom:8px;">فارس ربيع بن عواض العصيمي</div>
                <div style="font-size:0.75em; color:#94a3b8; margin-bottom:2px;">رقم الحساب (اضغط للنسخ):</div>
                <div class="copy-badge" onclick="navigator.clipboard.writeText('{acc_raw}'); alert('تم نسخ الحساب!');"><span>{acc_raw}</span><span>📋</span></div>
                <div style="font-size:0.75em; color:#94a3b8; margin-bottom:2px;">الآيبان:</div>
                <div class="copy-badge" onclick="navigator.clipboard.writeText('{iban_raw}'); alert('تم نسخ الآيبان!');"><span>SA93 8000 0222 6080 1601 3114</span><span>📋</span></div>
                <div style="margin-top:6px; padding:6px; background:rgba(56,189,248,0.1); border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.8em; color:#cbd5e1;">💡 اسم المستفيد:</span>
                    <div class="copy-badge" style="margin:0; padding:2px 6px;" onclick="navigator.clipboard.writeText('بادل 99'); alert('تم النسخ');"><span>بادل 99</span><span>📋</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {lb['name']}\nالتمرين: {lb['session']}\nالمبلغ: {TICKET_PRICE} ر.س\n\nمرفق إشعار التحويل."
            st.markdown(f'<a href="https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}" target="_blank" class="wa-btn">📲 أرسل إشعار التحويل لتثبيت المقعد</a>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="waitlist-box"><div style="color:#f59e0b; font-weight:bold;">⚠️ اكتملت المقاعد الأساسية يا كابتن {lb["name"]}</div><div style="font-size:0.85em; color:#e2e8f0;">أنت الآن في صدارة قائمة الانتظار. سيصلك تنبيه فور توفر مقعد.<br><b>(الرجاء عدم تحويل أي مبلغ حالياً)</b></div></div>', unsafe_allow_html=True)

with tab_cancel:
    with st.form("cancel_form"):
        c_phone = st.text_input("رقم الجوال المسجل")
        c_reason = st.selectbox("سبب الإلغاء", ["ظرف طارئ", "إصابة أو إجهاد", "تغيير خطة"])
        if st.form_submit_button("إلغاء المقعد", use_container_width=True):
            cp = sanitize_phone(c_phone)
            target = fetch_one("SELECT id, name, status FROM bookings WHERE phone=%s AND session_day=%s AND status IN ('confirmed', 'waitlist')", (cp, db_sess_key)) if cp else None
            
            if target:
                execute_query("UPDATE bookings SET status='cancelled' WHERE id=%s", (target[0],))
                execute_query("INSERT INTO cancellations (player_name, player_phone, session_day, reason) VALUES (%s, %s, %s, %s)", (target[1], cp, db_sess_key, c_reason))
                
                if target[2] == 'confirmed':
                    wait_p = fetch_one("SELECT id, name FROM bookings WHERE session_day=%s AND status='waitlist' ORDER BY id ASC LIMIT 1", (db_sess_key,))
                    if wait_p:
                        execute_query("UPDATE bookings SET status='confirmed' WHERE id=%s", (wait_p[0],))
                        st.info(f"⚡ تم تصعيد الكابتن {mask_name_for_privacy(wait_p[1])} من قائمة الانتظار!")
                if "last_booking" in st.session_state: del st.session_state["last_booking"]
                st.success("تم الإلغاء بنجاح، نراك في التمارين القادمة!")
                st.rerun()
            else:
                st.error("رقم الجوال غير مسجل في تمرين اليوم.")

# ==========================================
# 5. التشكيلة المباشرة
# ==========================================
st.markdown("---")
html_slots = ""
for i in range(CAPACITY):
    if i < len(c1_players):
        p = c1_players[i]
        icon = "✅" if p[3] == "paid" else "⏳"
        lvl = "🔥" if "متقدم" in p[4] else ("⚪" if "مبتدئ" in p[4] else "🟢")
        display_name = mask_name_for_privacy(p[1])
        html_slots += f'<div class="slot-box"><div class="slot-occupied">🎾 {display_name}</div><div class="slot-meta"><span style="background:rgba(255,255,255,0.1); padding:2px 4px; border-radius:4px;">{lvl}</span> <span>{icon}</span></div></div>'
    else:
        html_slots += '<div class="slot-box"><div class="slot-empty">مقعد متاح ✨</div></div>'

st.markdown(f'<div class="court-grid">{html_slots}</div>', unsafe_allow_html=True)
if waitlist: st.caption("📋 الاحتياط: " + " • ".join([f"{mask_name_for_privacy(w[1])}" for w in waitlist]))

st.markdown('<br><a href="https://wa.me/966566261868" target="_blank" style="display:block; text-align:center; color:#94a3b8; font-size:0.8em; text-decoration:none;">💬 استفسار؟ تواصل معنا عبر واتساب</a>', unsafe_allow_html=True)

# ==========================================
# 6. المحرك المالي ولوحة الإدارة
# ==========================================
with st.expander("⚙️ لوحة الإدارة المالية والتصدير", expanded=False):
    pin = st.text_input("رمز الأمان:", type="password")
    if pin:
        p_clean = str(pin).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")).strip()
        sec = st.secrets.get("ADMIN_PIN", "Padel99#Master@2026")
        
        if hmac.compare_digest(p_clean, sec):
            st.success("تمت المصادقة 🛡️")
            
            paid_count = sum(1 for p in c1_players if p[3] == 'paid')
            cash_in_hand = paid_count * TICKET_PRICE
            operating_cash_flow = cash_in_hand - COURT_COST
            
            total_historical = fetch_one("SELECT COUNT(*) FROM bookings WHERE status='confirmed'")[0]
            deferred_liability = total_historical * LOYALTY_LIABILITY

            st.markdown("##### 💵 التدفق النقدي التشغيلي ($OCF$):")
            m1, m2 = st.columns(2)
            m1.metric("المحصل فعلياً (كاش)", f"{cash_in_hand} ر.س", f"{paid_count} لاعبين")
            m2.metric("التدفق النقدي الصافي", f"{operating_cash_flow} ر.س", f"التكلفة: {COURT_COST}-", delta_color="normal" if operating_cash_flow >= 0 else "inverse")

            st.markdown("##### 📉 نظام وقف الخسارة التشغيلي (Stop-Loss):")
            if len(c1_players) < BREAK_EVEN_POINT:
                st.error(f"⚠️ المؤكدين ({len(c1_players)}) أقل من نقطة التعادل ({BREAK_EVEN_POINT}). راقب الوقت لإلغاء الملعب مبكراً لمنع الخسارة.")
            else:
                st.success("✅ الجلسة آمنة مالياً (تم تغطية تكلفة الملعب).")
            
            st.info(f"💡 التزامات المقاعد المجانية المؤجلة: **{round(deferred_liability, 1)} ر.س**")

            st.markdown("##### ⚡ تسوية الدفع:")
            for p in c1_players:
                if p[3] == 'pending':
                    c_name, c_btn = st.columns([3, 1])
                    c_name.caption(f"🎾 {p[1]} ({p[2]})")
                    if c_btn.button("سداد ✅", key=f"pay_{p[0]}", use_container_width=True):
                        execute_query("UPDATE bookings SET payment_status='paid' WHERE id=%s", (p[0],))
                        st.rerun()

            st.markdown("---")
            conn = psycopg2.connect(DB_URL)
            try:
                df = pd.read_sql_query("SELECT name, phone, session_day, level, status, payment_status, hear_about, player_note, created_at FROM bookings ORDER BY id DESC", conn)
                if not df.empty:
                    csv_data = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 تصدير السجل المالي والاستبيان (Excel/CSV)", data=csv_data, file_name=f"padel_data_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            finally:
                conn.close()

            if st.button("تصفير الجلسة الحالية 🔄", use_container_width=True):
                execute_query("DELETE FROM bookings WHERE session_day=%s", (db_sess_key,))
                execute_query("DELETE FROM cancellations WHERE session_day=%s", (db_sess_key,))
                st.rerun()
        else:
            st.error("الرمز السري غير صحيح.")
