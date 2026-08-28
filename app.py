import streamlit as st
from supabase import create_client, Client
import re
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة والواجهة التفاعلية
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
    max-width: 440px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Tahoma, sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
}

/* بطاقة الهيدر */
.hero-card {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 16px 14px;
    text-align: center;
    margin-bottom: 12px;
}
.hero-title { font-size: 1.6em; font-weight: 900; color: #f8fafc; margin: 0; }
.hero-sub { color: #38bdf8; font-size: 0.9em; font-weight: 600; margin-top: 4px; }

/* نقاط المقاعد الحية */
.seats-tracker {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin: 10px 0 6px 0;
}
.seat-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
}
.dot-booked { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.6); }
.dot-free { background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6); }

/* قائمة المسجلين الحالية */
.roster-box {
    background: rgba(15, 23, 42, 0.6);
    border: 1px dashed #334155;
    border-radius: 10px;
    padding: 8px 12px;
    margin-bottom: 14px;
    font-size: 0.82em;
    color: #cbd5e1;
}

/* زر الحجز الأساسي */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    color: #ffffff !important;
    font-size: 1.15em !important;
    font-weight: 800 !important;
    height: 52px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 18px rgba(34, 197, 94, 0.35) !important;
    margin-top: 8px !important;
}

/* بطاقة الدفع والنسخ */
.pay-box {
    background: #0f172a;
    border: 1.5px solid #38bdf8;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 10px;
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
    margin-top: 10px;
}

div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الاتصال بقاعدة البيانات
# ==========================================
COURT_CAPACITY = 6
PRICE_PER_SEAT = 65

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"].strip().rstrip('/'), st.secrets["SUPABASE_KEY"].strip())

try:
    supabase = init_supabase()
except Exception:
    st.error("تعذر الاتصال بقاعدة البيانات.")
    st.stop()

# ==========================================
# 3. المنطق وجدول المواعيد التلقائي
# ==========================================
ksa_tz = timezone(timedelta(hours=3))
now = datetime.now(ksa_tz)
schedule = {6: (0, "الأحد"), 0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"), 2: (1, "الخميس"), 3: (0, "الخميس"), 4: (2, "الأحد"), 5: (1, "الأحد")}
days_to_add, d_ar = schedule.get(now.weekday(), (0, "الأحد"))
target_date = now + timedelta(days=days_to_add)
display_session = f"{d_ar} ({target_date.strftime('%d/%m')})"
db_session_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"

# جلب الحجوزات الحالية لجلسة اليوم المحددة
session_data = supabase.table("bookings").select("*").eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).order("id").execute().data or []
confirmed_players = [d for d in session_data if d["status"] == "confirmed"][:COURT_CAPACITY]
booked_count = len(confirmed_players)
seats_left = max(0, COURT_CAPACITY - booked_count)

# توليد نقاط المقاعد
dots_html = "".join(['<div class="seat-dot dot-booked" title="محجوز"></div>' for _ in range(booked_count)])
dots_html += "".join(['<div class="seat-dot dot-free" title="متاح"></div>' for _ in range(seats_left)])

# ==========================================
# 4. بناء الواجهة
# ==========================================
st.markdown(f"""
<div class="hero-card">
    <div class="hero-title">🎾 بادل 99</div>
    <div class="hero-sub">تمرين {display_session} • 9:30 م</div>
    <div class="seats-tracker">{dots_html}</div>
    <div style="font-size:0.82em; color:#94a3b8; margin-top:6px;">
        {'🔥 متبقي ' + str(seats_left) + ' مقاعد فقط' if seats_left > 0 else '⚠️ المقاعد ممتلئة (قائمة الانتظار مفتوحة)'}
    </div>
</div>
""", unsafe_allow_html=True)

# استعراض أسماء اللاعبين المسجلين حالياً لتحفيز إكمال الحجز
if confirmed_players:
    names_str = " • ".join([f"<b>{p['name'].split()[0]}</b> ({p.get('level', 'متوسط')})" for p in confirmed_players])
    st.markdown(f'<div class="roster-box">👥 <b>في الملعب الآن:</b> {names_str}</div>', unsafe_allow_html=True)

# شاشة ما بعد الحجز المباشرة
if "booked" in st.session_state:
    b = st.session_state["booked"]
    total_price = b["seats"] * PRICE_PER_SEAT
    
    if b["status"] == "confirmed":
        iban_raw = "SA9380000222608016013114"
        iban_display = "SA93 8000 0222 6080 1601 3114"
        seats_desc = "مقعدك ومقعد خويك" if b["seats"] == 2 else "مقعدك"
        
        st.markdown(f"""
        <div class="pay-box">
            <h3 style="color:#22c55e; margin:0 0 4px 0;">🎉 تم حجز {seats_desc} بنجاح!</h3>
            <div style="font-size:0.9em; color:#e2e8f0; margin-bottom:8px;">المبلغ المطلوب ({b['seats']} مقعد): <b style="color:#38bdf8; font-size:1.1em;">{total_price} ر.س</b></div>
            
            <div style="font-size:0.75em; color:#94a3b8;">اضغط على الآيبان للنسخ:</div>
            <div class="copy-btn-iban" onclick="navigator.clipboard.writeText('{iban_raw}'); alert('تم نسخ الآيبان بنجاح!');">
                📋 {iban_display}
            </div>
            <div style="font-size:0.75em; color:#64748b;">مصرف الراجحي | فارس ربيع العصيمي</div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالاسم: {b['name']}\nعدد المقاعد: {b['seats']}\nالتمرين: {display_session}\nالمبلغ الإجمالي: {total_price} ر.س\n\n(مرفق إشعار التحويل لتثبيت الحجز)"
        wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال وتثبيت المقاعد</a>', unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ المقاعد الأساسية اكتملت. تم تسجيلك في قائمة الانتظار برقم ({b.get('pos', 1)}). سنتواصل معك فور توفر مقعد.")

else:
    # نموذج الحجز المباشر والسريع
    with st.form("smart_booking_form", clear_on_submit=True):
        f_name = st.text_input("اسمك الكريم", placeholder="اكتب اسمك")
        f_phone = st.text_input("رقم الجوال", placeholder="05xxxxxxxx")
        
        c_lvl, c_plus = st.columns([1.2, 1])
        with c_lvl:
            f_level = st.selectbox("المستوى", ["متوسط", "متقدم", "مبتدئ"])
        with c_plus:
            add_friend = st.checkbox("+ حجز مقعد لخويي", help="احجز مقعدين دفعة واحدة بنفس الجوال")
            
        friend_name = ""
        if add_friend:
            friend_name = st.text_input("اسم خويك", placeholder="اسم الخوي")
            
        hp = st.text_input("hp", label_visibility="collapsed")
        
        btn_label = f"احجز مقعدين بـ {PRICE_PER_SEAT * 2} ر.س ⚡" if add_friend else f"احجز مقعدك بـ {PRICE_PER_SEAT} ر.س ⚡"
        btn_submit = st.form_submit_button(btn_label, use_container_width=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            clean_phone = re.sub(r'[\s\-\+]', '', f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل اسمك ورقم جوال يبدأ بـ 05.")
            elif add_friend and len(friend_name.strip()) < 2:
                st.error("فضلاً أدخل اسم خويك.")
            else:
                exists = supabase.table("bookings").select("id").eq("phone", clean_phone).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                if exists.data:
                    st.warning("أنت مسجل بالفعل في تمرين اليوم!")
                else:
                    needed_seats = 2 if add_friend else 1
                    status_val = "confirmed" if seats_left >= needed_seats else "waitlist"
                    
                    # تسجيل الحجز الأساسي
                    supabase.table("bookings").insert({
                        "name": clean_name,
                        "phone": clean_phone,
                        "session_day": db_session_key,
                        "court": 1,
                        "level": f_level,
                        "status": status_val,
                        "payment_status": "pending",
                        "hear_about": "",
                        "player_note": f"حجز مرافق: {friend_name.strip()}" if add_friend else ""
                    }).execute()
                    
                    # تسجيل مقعد المرافق
                    if add_friend:
                        supabase.table("bookings").insert({
                            "name": f"{friend_name.strip()} (طرف {clean_name.split()[0]})",
                            "phone": clean_phone,
                            "session_day": db_session_key,
                            "court": 1,
                            "level": f_level,
                            "status": status_val,
                            "payment_status": "pending",
                            "hear_about": "",
                            "player_note": "مرافق"
                        }).execute()
                    
                    pos = len(supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "waitlist").execute().data or []) if status_val == "waitlist" else None
                    st.session_state["booked"] = {
                        "name": clean_name,
                        "status": status_val,
                        "seats": needed_seats,
                        "pos": pos
                    }
                    st.rerun()

# ==========================================
# 5. خيار الإلغاء السريع بدون تشتيت
# ==========================================
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
with st.expander("❌ إلغاء حجز مسجل"):
    can_phone = st.text_input("أدخل رقم الجوال للإلغاء:", key="c_p")
    if st.button("تأكيد الإلغاء", use_container_width=True):
        clean_cp = re.sub(r'[\s\-\+]', '', can_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
        if clean_cp.startswith("966"): clean_cp = "0" + clean_cp[3:]
        elif clean_cp.startswith("5"): clean_cp = "0" + clean_cp
        
        recs = supabase.table("bookings").select("*").eq("phone", clean_cp).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute().data or []
        if recs:
            for r in recs:
                supabase.table("bookings").update({"status": "cancelled"}).eq("id", r["id"]).execute()
            
            # تصعيد من قائمة الانتظار تلقائياً
            w_players = supabase.table("bookings").select("*").eq("session_day", db_session_key).eq("status", "waitlist").order("id").limit(len(recs)).execute().data or []
            for wp in w_players:
                supabase.table("bookings").update({"status": "confirmed"}).eq("id", wp["id"]).execute()
                
            st.success("تم إلغاء الحجز بنجاح.")
            if "booked" in st.session_state:
                del st.session_state["booked"]
            st.rerun()
        else:
            st.error("لا يوجد حجز مسجل بهذا الرقم لتمرين اليوم.")
