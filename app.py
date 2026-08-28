import streamlit as st
from supabase import create_client, Client
import re
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الواجهة وتنسيق التجارب التفاعلية
# ==========================================
st.set_page_config(
    page_title="بادل 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 1.2rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 420px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
}

/* بطاقة الهيدر الذكية */
.hero-card {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 18px;
    padding: 16px 14px;
    text-align: center;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    margin-bottom: 14px;
}
.hero-title { font-size: 1.6em; font-weight: 900; color: #f8fafc; margin: 0; letter-spacing: -0.5px; }
.hero-sub { color: #38bdf8; font-size: 0.9em; font-weight: 600; margin-top: 4px; }

/* نقاط المقاعد الحية */
.seats-tracker {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
}
.seat-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    transition: all 0.3s ease;
}
.dot-booked { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.6); }
.dot-free { background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6); }

/* حقول الإدخال */
.stTextInput > div > div > input {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1.5px solid #334155 !important;
    border-radius: 10px !important;
    font-size: 1em !important;
    padding: 10px 12px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #22c55e !important;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.2) !important;
}

/* زر الحجز الرئيسي النبّاض */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    color: #ffffff !important;
    font-size: 1.2em !important;
    font-weight: 800 !important;
    height: 54px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 20px rgba(34, 197, 94, 0.4) !important;
    margin-top: 10px !important;
}

/* بطاقة الدفع المباشرة مع النسخ */
.pay-box {
    background: #0f172a;
    border: 1.5px solid #38bdf8;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 12px;
}
.copy-btn-iban {
    background: #1e293b;
    border: 1px dashed #38bdf8;
    color: #38bdf8;
    padding: 10px;
    border-radius: 8px;
    font-family: monospace;
    font-size: 0.95em;
    font-weight: bold;
    cursor: pointer;
    margin: 8px 0;
}

/* زر الواتساب */
.wa-btn {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 14px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 1.05em;
    text-decoration: none;
    box-shadow: 0 4px 15px rgba(37, 211, 102, 0.35);
    margin-top: 12px;
}

div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ربط قاعدة البيانات
# ==========================================
COURT_CAPACITY = 6

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"].strip().rstrip('/'), st.secrets["SUPABASE_KEY"].strip())

try:
    supabase = init_supabase()
except Exception:
    st.error("تعذر الاتصال بقاعدة البيانات.")
    st.stop()

# ==========================================
# 3. توقيت الجلسة والحساب التلقائي
# ==========================================
ksa_tz = timezone(timedelta(hours=3))
now = datetime.now(ksa_tz)
schedule = {6: (0, "الأحد"), 0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"), 2: (1, "الخميس"), 3: (0, "الخميس"), 4: (2, "الأحد"), 5: (1, "الأحد")}
days_to_add, d_ar = schedule.get(now.weekday(), (0, "الأحد"))
target_date = now + timedelta(days=days_to_add)
display_session = f"{d_ar} ({target_date.strftime('%d/%m')})"
db_session_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"

# جلب الحجوزات الحالية
res = supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "confirmed").execute()
booked_count = len(res.data or [])
seats_left = max(0, COURT_CAPACITY - booked_count)

# توليد نقاط المقاعد الحية
dots_html = "".join(['<div class="seat-dot dot-booked" title="محجوز"></div>' for _ in range(booked_count)])
dots_html += "".join(['<div class="seat-dot dot-free" title="متاح"></div>' for _ in range(seats_left)])

# ==========================================
# 4. واجهة المستخدم
# ==========================================

# بطاقة تفاصيل التمرين
st.markdown(f"""
<div class="hero-card">
    <div class="hero-title">🎾 بادل 99</div>
    <div class="hero-sub">تمرين {display_session} • 9:30 م</div>
    <div class="seats-tracker">
        {dots_html}
    </div>
    <div style="font-size:0.8em; color:#94a3b8; margin-top:8px;">
        {'🔥 متبقي ' + str(seats_left) + ' مقاعد فقط' if seats_left > 0 else '⚠️ المقاعد ممتلئة (قائمة الانتظار متاحة)'}
    </div>
</div>
""", unsafe_allow_html=True)

# شاشة ما بعد الحجز (تأكيد + دفع + واتساب)
if "booked" in st.session_state:
    b = st.session_state["booked"]
    if b["status"] == "confirmed":
        iban_raw = "SA9380000222608016013114"
        iban_display = "SA93 8000 0222 6080 1601 3114"
        
        st.markdown(f"""
        <div class="pay-box">
            <h3 style="color:#22c55e; margin:0 0 4px 0;">🎉 تم تثبيت مقعدك يا {b['name']}!</h3>
            <div style="font-size:0.88em; color:#e2e8f0; margin-bottom:8px;">المبلغ المطلوب: <b>65 ر.س</b></div>
            
            <div style="font-size:0.75em; color:#94a3b8;">اضغط على الآيبان لنسخه مباشرة:</div>
            <div class="copy-btn-iban" onclick="navigator.clipboard.writeText('{iban_raw}'); alert('تم نسخ الآيبان بنجاح!');">
                📋 {iban_display}
            </div>
            <div style="font-size:0.75em; color:#64748b;">مصرف الراجحي | فارس ربيع العصيمي</div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {b['name']}\nالتمرين: {display_session}\nالمبلغ: 65 ر.س\n\n(مرفق إيصال التحويل لتثبيت الحجز)"
        wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إيصال التحويل عبر واتساب</a>', unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ المقاعد ممتلئة. أنت الآن في قائمة الانتظار برقم ({b.get('pos', 1)}). سنتواصل معك فور توفر مقعد.")

else:
    # نموذج الحجز فائق السهولة (حقلين فقط)
    with st.form("ultra_fast_form", clear_on_submit=True):
        f_name = st.text_input("اسمك الكريم", placeholder="اكتب اسمك")
        f_phone = st.text_input("رقم الجوال", placeholder="05xxxxxxxx")
        hp = st.text_input("hp", label_visibility="collapsed")
        
        btn_submit = st.form_submit_button("احجز الآن بـ 65 ر.س ⚡", use_container_width=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            clean_phone = re.sub(r'[\s\-\+]', '', f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل الاسم ورقم جوال يبدأ بـ 05.")
            else:
                exists = supabase.table("bookings").select("id").eq("phone", clean_phone).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                if exists.data:
                    st.warning("أنت مسجل بالفعل في تمرين اليوم!")
                else:
                    status = "confirmed" if seats_left > 0 else "waitlist"
                    supabase.table("bookings").insert({
                        "name": clean_name,
                        "phone": clean_phone,
                        "session_day": db_session_key,
                        "court": 1,
                        "level": "متوسط",
                        "status": status,
                        "payment_status": "pending",
                        "hear_about": "",
                        "player_note": ""
                    }).execute()
                    
                    pos = len(supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "waitlist").execute().data or []) if status == "waitlist" else None
                    st.session_state["booked"] = {"name": clean_name, "status": status, "pos": pos}
                    st.rerun()

# ==========================================
# 5. خيار إضافي خفيف: إلغاء / استفسار
# ==========================================
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
contact_wa = f"https://wa.me/966566261868?text={urllib.parse.quote('مرحباً كابتن فارس، بخصوص حجز تمرين بادل 99:')}"
st.markdown(f"""
<div style="text-align:center; font-size:0.75em; color:#64748b;">
    هل ترغب بالاعتذار أو تواجه مشكلة؟ <a href="{contact_wa}" target="_blank" style="color:#38bdf8; text-decoration:none;">تواصل عبر واتساب</a>
</div>
""", unsafe_allow_html=True)
