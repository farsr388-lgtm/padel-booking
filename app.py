import streamlit as st
from supabase import create_client, Client
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. الإعداد والتصميم البسيط المباشر
# ==========================================
st.set_page_config(
    page_title="حجز تمرين بادل",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"] { display: none !important; }
#MainMenu, footer { visibility: hidden; }

.block-container { 
    padding-top: 1rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 480px !important;
    margin: 0 auto;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
}

/* زر الحجز الرئيسي */
div[data-testid="stFormSubmitButton"] > button {
    background: #16a34a !important;
    color: #ffffff !important;
    font-size: 1.1em !important;
    font-weight: 700 !important;
    height: 48px !important;
    border-radius: 8px !important;
    border: none !important;
    width: 100% !important;
    margin-top: 6px !important;
}

/* صندوق الدفع المباشر بعد التأكيد */
.pay-card {
    background: #0f172a;
    border: 2px solid #22c55e;
    border-radius: 10px;
    padding: 14px;
    margin: 12px 0;
    text-align: center;
}
.copy-text {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
    font-family: monospace;
    font-size: 1em;
    color: #38bdf8;
    font-weight: 700;
    margin: 6px 0;
    user-select: all;
}
.wa-link {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 12px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1em;
    text-decoration: none;
    margin-top: 8px;
}

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ربط قاعدة البيانات
# ==========================================
COURT_CAPACITY = 6

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("تعذر الاتصال بالنظام، يرجى المحاولة لاحقاً.")
    st.stop()

def get_session_bookings(db_session_key):
    try:
        res = supabase.table("bookings").select("*").eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).order("id").execute()
        data = res.data or []
        confirmed = [d for d in data if d["status"] == "confirmed"][:COURT_CAPACITY]
        waitlist = [d for d in data if d["status"] == "waitlist"]
        return confirmed, waitlist
    except Exception:
        return [], []

# ==========================================
# 3. المنطق والمواعيد
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

def get_next_session():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    weekday = now.weekday()

    schedule = {
        6: (0, "الأحد"),
        0: (1, "الثلاثاء"),
        1: (0, "الثلاثاء"),
        2: (1, "الخميس"),
        3: (0, "الخميس"),
        4: (2, "الأحد"),
        5: (1, "الأحد")
    }
    
    days_to_add, d_ar = schedule.get(weekday, (0, "الأحد"))
    target_date = now + timedelta(days=days_to_add)
    label_ar = f"{d_ar} ({target_date.strftime('%d/%m')})"
    db_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"
    return label_ar, db_key

# ==========================================
# 4. الواجهة المباشرة
# ==========================================
display_session, db_session_key = get_next_session()
confirmed_players, waitlist = get_session_bookings(db_session_key)
seats_left = max(0, COURT_CAPACITY - len(confirmed_players))

# تفاصيل التمرين بوضوح
st.subheader("🎾 حجز تمرين بادل 99")
st.write(f"📅 **الموعد:** {display_session} (9:30 م - 11:00 م)")
st.write(f"💵 **الرسوم:** 65 ر.س | **المقاعد المتاحة:** {seats_left} من 6")

# نموذج الحجز المباشر
with st.form("booking_form", clear_on_submit=True):
    f_name = st.text_input("الاسم", placeholder="اكتب اسمك")
    f_phone = st.text_input("رقم الجوال", placeholder="05xxxxxxxx")
    f_level_raw = st.selectbox("المستوى", ["متوسط", "متقدم", "مبتدئ"])
    
    honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
    btn_submit = st.form_submit_button("تأكيد الحجز 👈", use_container_width=True)

    if btn_submit:
        if honeypot_val:
            st.stop()
            
        clean_name = f_name.strip()
        clean_phone = clean_and_validate_sa_phone(f_phone)

        if len(clean_name) < 2:
            st.error("فضلاً أدخل الاسم.")
        elif not clean_phone:
            st.error("فضلاً أدخل رقم جوال يبدأ بـ 05.")
        else:
            try:
                existing = supabase.table("bookings").select("id").eq("phone", clean_phone).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                
                if existing.data and len(existing.data) > 0:
                    st.warning("أنت مسجل بالفعل في هذا التمرين.")
                else:
                    conf_res = supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "confirmed").execute()
                    status_val = "confirmed" if len(conf_res.data or []) < COURT_CAPACITY else "waitlist"

                    insert_data = {
                        "name": clean_name,
                        "phone": clean_phone,
                        "session_day": db_session_key,
                        "court": 1,
                        "level": f_level_raw,
                        "status": status_val,
                        "payment_status": "pending",
                        "hear_about": "",
                        "player_note": ""
                    }
                    supabase.table("bookings").insert(insert_data).execute()

                    wait_pos = None
                    if status_val == "waitlist":
                        w_res = supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "waitlist").execute()
                        wait_pos = len(w_res.data or [])

                    st.session_state["last_booking"] = {
                        "name": clean_name,
                        "status": status_val,
                        "wait_pos": wait_pos,
                        "session": display_session
                    }
                    st.rerun()
            except Exception as err:
                st.error(f"حدث خطأ أثناء الحجز: {err}")

# بطاقة الدفع والإشعار المباشرة
if "last_booking" in st.session_state:
    lb = st.session_state["last_booking"]
    if lb["status"] == "confirmed":
        iban_val = "SA9380000222608016013114"
        iban_display = "SA93 8000 0222 6080 1601 3114"
        
        st.markdown(f"""
        <div class="pay-card">
            <h4 style="color:#22c55e; margin:0 0 6px 0;">✅ تم حجز مقعدك بنجاح!</h4>
            <div style="font-size:0.9em; color:#cbd5e1;">المبلغ: <b>65 ر.س</b> (الراجحي: فارس ربيع العصيمي)</div>
            <div style="font-size:0.8em; color:#94a3b8; margin-top:6px;">الآيبان (اضغط للنسخ):</div>
            <div class="copy-text">{iban_display}</div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_msg = f"🎾 تأكيد حجز بادل 99\nالاسم: {lb['name']}\nالتمرين: {lb['session']}\nالمبلغ: 65 ر.س\n(مرفق إشعار التحويل البنكي)"
        wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📲 إرسال إيصال التحويل عبر واتساب</a>', unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ اكتملت المقاعد. أنت في قائمة الانتظار رقم ({lb.get('wait_pos', 1)}). سنتواصل معك فور توفر مقعد.")

# ==========================================
# 5. قائمة الأسماء الحالية والإلغاء
# ==========================================
st.markdown("---")

# عرض الأسماء كنص مباشر وقائمة بدون تعقيد
if confirmed_players:
    st.markdown("**اللاعبون المسجلون:**")
    names_list = " • ".join([f"{p['name']} ({p.get('level', 'متوسط')})" for p in confirmed_players])
    st.write(names_list)

# إلغاء الحجز بشكل مبسط جداً
with st.expander("❌ إلغاء حجز سابق"):
    can_phone_raw = st.text_input("رقم الجوال لإلغاء الحجز:", key="cancel_phone")
    if st.button("تأكيد الإلغاء", use_container_width=True):
        clean_cp = clean_and_validate_sa_phone(can_phone_raw)
        if clean_cp:
            try:
                rec = supabase.table("bookings").select("*").eq("phone", clean_cp).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                if rec.data and len(rec.data) > 0:
                    target = rec.data[0]
                    was_confirmed = target["status"] == "confirmed"
                    
                    supabase.table("bookings").update({"status": "cancelled"}).eq("id", target["id"]).execute()
                    
                    if was_confirmed:
                        w_player = supabase.table("bookings").select("*").eq("session_day", db_session_key).eq("status", "waitlist").order("id").limit(1).execute()
                        if w_player.data and len(w_player.data) > 0:
                            supabase.table("bookings").update({"status": "confirmed"}).eq("id", w_player.data[0]["id"]).execute()
                    
                    st.success("تم إلغاء الحجز.")
                    if "last_booking" in st.session_state:
                        del st.session_state["last_booking"]
                    st.rerun()
                else:
                    st.error("لا يوجد حجز مسجل بهذا الرقم اليوم.")
            except Exception as err:
                st.error(f"خطأ أثناء الإلغاء: {err}")
        else:
            st.error("أدخل رقم جوال صحيح.")

# ==========================================
# 6. لوحة الإدارة
# ==========================================
with st.expander("⚙️ الإدارة"):
    pin = st.text_input("رمز الدخول:", type="password")
    if pin and hmac.compare_digest(pin.strip(), "Padel99#Master@2026"):
        st.success("لوحة التحكم")
        if st.button("تصفير تمرين اليوم 🔄", use_container_width=True):
            supabase.table("bookings").delete().eq("session_day", db_session_key).execute()
            st.success("تم التصفير!")
            st.rerun()
