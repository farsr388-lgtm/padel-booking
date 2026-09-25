import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة وتنسيق الموبايل فائق السرعة
# ==============================================================================
st.set_page_config(
    page_title="بادل 99 | Padel 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 440px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
}

/* بطاقة الهيدر الرئيسية */
.hero-box {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 14px;
    text-align: center;
    margin-bottom: 8px;
}
.hero-title { font-size: 1.6em; font-weight: 900; color: #f8fafc; margin: 0; }
.hero-desc { color: #94a3b8; font-size: 0.84em; margin-top: 4px; }
.features-pill {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid #38bdf8;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 0.78em;
    color: #38bdf8;
    margin: 6px 0;
    display: inline-block;
    font-weight: 700;
}

/* بطاقة الكورت وشبكة المقاعد الستة */
.court-container {
    background: #0f172a;
    border: 1.5px solid #1e3a8a;
    border-radius: 14px;
    padding: 12px;
    margin: 8px 0;
}
.court-header {
    text-align: center;
    font-weight: 800;
    font-size: 0.9em;
    color: #38bdf8;
    margin-bottom: 8px;
}
.seats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.seat-card {
    border-radius: 8px;
    padding: 10px 6px;
    text-align: center;
    font-size: 0.82em;
    font-weight: 800;
}
.seat-empty {
    background: rgba(30, 41, 59, 0.6);
    border: 1px dashed #38bdf8;
    color: #93c5fd;
}
.seat-taken {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
}

/* بطاقة تفاصيل التدوير والأمريكانو */
.rotation-info-box {
    background: rgba(15, 23, 42, 0.7);
    border: 1px dashed #334155;
    border-radius: 12px;
    padding: 10px;
    margin: 8px 0;
    font-size: 0.8em;
    color: #cbd5e1;
    line-height: 1.6;
}

/* بطاقات الحالة والتأكيد */
.status-card-success {
    background: rgba(34, 197, 94, 0.12);
    border: 2px solid #22c55e;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 8px;
}
.status-card-waitlist {
    background: rgba(245, 158, 11, 0.12);
    border: 2px solid #d97706;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 8px;
}

.memo-tag {
    background: #0b0f19;
    border: 1.5px dashed #38bdf8;
    border-radius: 8px;
    padding: 6px 10px;
    display: inline-block;
    font-family: monospace;
    font-size: 1.15em;
    color: #38bdf8;
    font-weight: 800;
    margin: 6px 0;
}

.finance-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
}
.stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.84em;
    padding: 5px 0;
    border-bottom: 1px solid #1e293b;
}

div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    color: #ffffff !important;
    font-size: 1.15em !important;
    font-weight: 800 !important;
    height: 52px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.35) !important;
    margin-top: 6px !important;
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
    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
    margin-top: 10px;
}

div[data-testid="stCodeBlock"] {
    direction: ltr !important;
    border-radius: 10px !important;
    border: 1px dashed #38bdf8 !important;
}

div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ربط قاعدة البيانات السحابية (Supabase)
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"].strip().rstrip('/'),
        st.secrets["SUPABASE_KEY"].strip()
    )

try:
    supabase = get_supabase_client()
except Exception:
    st.error("تعذر الاتصال بالسحابة. يرجى التحقق من إعدادات Secrets.")
    st.stop()

# ==============================================================================
# 3. محرك الجدولة الزمنية التلقائية
# ==============================================================================
def resolve_next_session() -> tuple[str, str, datetime]:
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    # 0: الإثنين, 1: الثلاثاء, 2: الأربعاء, 3: الخميس, 4: الجمعة, 5: السبت, 6: الأحد
    weekday_offsets = {
        0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"),
        2: (1, "الخميس"),   3: (0, "الخميس"),
        4: (2, "الأحد"),    5: (1, "الأحد"),
        6: (0, "الأحد")
    }
    
    days_to_add, day_name = weekday_offsets.get(now.weekday(), (0, "الأحد"))
    
    if days_to_add == 0 and (now.hour > 22 or (now.hour == 22 and now.minute >= 30)):
        next_dt = now + timedelta(days=1)
        days_to_add, day_name = weekday_offsets.get(next_dt.weekday(), (0, "الأحد"))
        days_to_add += 1
        
    target_date = now + timedelta(days=days_to_add)
    session_start_dt = target_date.replace(hour=21, minute=30, second=0, microsecond=0)
    
    return f"{day_name} ({target_date.strftime('%d/%m')})", f"{day_name} {target_date.strftime('%Y-%m-%d')}", session_start_dt

display_session, db_session_key, session_start_time = resolve_next_session()

# ==============================================================================
# 4. محرك المالية والأسعار الفوري (Reactive & Resilient)
# ==============================================================================
COURT_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PIN_HASH = "9900"

def fetch_financial_settings(session_key: str) -> dict:
    defaults = {
        "court_cost": 300,
        "unit_price": 65,
        "balls_cost": 35,
        "water_cost": 15,
        "court_paid": False,
        "iban_number": "SA9380000222608016013114",
        "account_name": "مصرف الراجحي | فارس ربيع العصيمي"
    }
    if "override_fin" in st.session_state:
        return st.session_state["override_fin"]
    try:
        res = supabase.table("session_finance").select("*").eq("session_day", session_key).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception:
        pass
    return defaults

fin_data = fetch_financial_settings(db_session_key)
UNIT_PRICE = float(fin_data.get("unit_price", 65))
COURT_COST = float(fin_data.get("court_cost", 300))
BALLS_COST = float(fin_data.get("balls_cost", 35))
WATER_COST = float(fin_data.get("water_cost", 15))
COURT_IS_PAID = bool(fin_data.get("court_paid", False))
IBAN_NUMBER = str(fin_data.get("iban_number", "SA9380000222608016013114"))
ACCOUNT_NAME = str(fin_data.get("account_name", "مصرف الراجحي | فارس ربيع العصيمي"))

# ==============================================================================
# 5. محرك الشلال التلقائي وتصفية المقاعد
# ==============================================================================
def process_waterfall_and_roster(session_key: str):
    now_utc = datetime.now(timezone.utc)
    now_utc_iso = now_utc.isoformat()
    
    try:
        all_players = supabase.table("bookings") \
            .select("*") \
            .eq("session_day", session_key) \
            .order("id") \
            .execute().data or []
            
        confirmed_active = []
        waitlist_players = []
        
        for p in all_players:
            if p.get("status") == "waitlist":
                waitlist_players.append(p)
            elif p.get("status") == "confirmed":
                is_paid = p.get("payment_status") == "paid"
                is_expired = p.get("expires_at") and p["expires_at"] <= now_utc_iso
                
                # إلغاء المقعد المعلق بعد انقضاء الـ 15 دقيقة
                if not is_paid and is_expired:
                    supabase.table("bookings").update({
                        "status": "cancelled",
                        "player_note": "انتهاء مهلة السداد (15 دقيقة)"
                    }).eq("id", p["id"]).execute()
                else:
                    confirmed_active.append(p)
        
        # تصعيد الانتظار تلقائياً في حال وجود شواغر
        vacancies = COURT_CAPACITY - len(confirmed_active)
        if vacancies > 0 and waitlist_players:
            to_promote = waitlist_players[:vacancies]
            for wp in to_promote:
                new_exp = (now_utc + timedelta(minutes=15)).isoformat()
                supabase.table("bookings").update({
                    "status": "confirmed",
                    "payment_status": "pending",
                    "expires_at": new_exp,
                    "player_note": "تصعيد تلقائي من قائمة الانتظار"
                }).eq("id", wp["id"]).execute()
                
                wp["status"] = "confirmed"
                wp["payment_status"] = "pending"
                wp["expires_at"] = new_exp
                confirmed_active.append(wp)
                waitlist_players.remove(wp)
                
        return confirmed_active[:COURT_CAPACITY], waitlist_players
    except Exception:
        return [], []

confirmed_players, waitlist_players = process_waterfall_and_roster(db_session_key)
booked_count = len(confirmed_players)
waitlist_count = len(waitlist_players)
seats_left = max(0, COURT_CAPACITY - booked_count)

# ==============================================================================
# 6. واجهة المستخدم والعداد التنازلي المباشر
# ==============================================================================
cutoff_epoch_ms = int(session_start_time.astimezone(timezone.utc).timestamp() * 1000)

st.markdown(f"""
<div class="hero-box">
    <div class="hero-title">🎾 Padel 99</div>
    <div class="hero-desc">تمرين {display_session} • تنظيم متكامل وتنافسي</div>
    <div class="features-pill">⚡ كرات جديدة • مياه مبردة • تدوير عادل كل 15 دقيقة</div>
    <div style="font-size:0.86em; color:#e2e8f0; margin-top:4px;">
        ⏰ 9:30 م - 11:30 م | كورت 1 ({COURT_CAPACITY} مقاعد) • 
        <b>{'متبقي ' + str(seats_left) + ' مقاعد فقط! 🔥' if seats_left > 0 else 'المقاعد مكتملة (الانتظار متاح ⏳)'}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# عداد موعد التمرين
components.html(f"""
<!DOCTYPE html>
<div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 10px; padding: 7px; color: #f59e0b; font-size: 13px; font-weight: 700;">
    ⏳ متبقي على انطلاق التمرين: <span id="event_timer" style="font-family: monospace; font-size: 16px; color: #fbbf24; font-weight: 900;">--:--:--</span>
</div>
<script>
    var target = {cutoff_epoch_ms};
    function updateClock() {{
        var diff = target - new Date().getTime();
        var el = document.getElementById('event_timer');
        if (!el) return;
        if (diff <= 0) {{
            el.innerHTML = "بدأ التمرين الآن 🎾";
            return;
        }}
        var hrs = Math.floor(diff / (1000 * 60 * 60));
        var mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        var secs = Math.floor((diff % (1000 * 60)) / 1000);
        el.innerHTML = (hrs < 10 ? "0" : "") + hrs + ":" + 
                       (mins < 10 ? "0" : "") + mins + ":" + 
                       (secs < 10 ? "0" : "") + secs;
    }}
    updateClock();
    setInterval(updateClock, 1000);
</script>
""", height=48)

# عرض شبكة الكورت
seats_html = []
for i in range(COURT_CAPACITY):
    if i < booked_count:
        p_name = html.escape(confirmed_players[i]['name'].split()[0])
        seats_html.append(f'<div class="seat-card seat-taken">👤 {p_name} (محجوز)</div>')
    else:
        seats_html.append('<div class="seat-card seat-empty">✨ مقعد شاغر</div>')

st.markdown(f"""
<div class="court-container">
    <div class="court-header">🏟️ كورت 1 ({booked_count}/{COURT_CAPACITY})</div>
    <div class="seats-grid">{''.join(seats_html)}</div>
</div>
""", unsafe_allow_html=True)

# بطاقة خطة التدوير العادل (الأمريكانو)
with st.expander("📋 نظام التدوير وضمان حقك باللعب (نظام الأمريكانو 120 دقيقة)"):
    st.markdown("""
    <div class="rotation-info-box">
        • <b>مدة التمرين:</b> ساعتان كاملة (120 دقيقة) مقسمة على 6 جولات منظمة.<br>
        • <b>وقت اللعب الفعلي:</b> يلعب كل مشترك 4 جولات كاملة (72 دقيقة لعب عالي الكثافة).<br>
        • <b>فترات الراحة:</b> جولتان منفصلتان (36 دقيقة) للاسترجاع، شرب الماء، والتواصل الاجتماعي.<br>
        • <b>العدالة:</b> تدوير شركاء اللعب بالتساوي لضمان التكافؤ والتنافسية للجميع 🎾.
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. شاشات ما بعد التسجيل (المهلة الصريحة والكود المرجعي)
# ==============================================================================
if "booked" in st.session_state:
    b = st.session_state["booked"]
    
    # 1. شاشة قائمة الانتظار
    if b.get("is_waitlist", False):
        st.markdown(f"""
        <div class="status-card-waitlist">
            <h2 style="color:#fbbf24; margin:0 0 6px 0;">⏳ تم تسجيلك في قائمة الانتظار</h2>
            <div style="font-size:1.05em; color:#fef3c7; margin:8px 0;">
                ترتيبك الحالي: <b style="font-size:1.4em; color:#ffffff;">#{b.get('pos', 1)}</b>
            </div>
            <div style="font-size:0.84em; color:#fde68a; line-height:1.6;">
                النظام يراقب المقاعد لحظياً؛ بمجرد اعتذار أي لاعب أو انقضاء مهلة الـ 15 دقيقة، 
                <b>يتم تصعيدك تلقائياً لتدخل الملعب وتتاح لك مهلة التحويل.</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_wait_msg = f"هلا كابتن فارس 🎾\nأنا مسجل في انتظار تمرين بادل 99 ({display_session})\n👤 الاسم: {b['name']}\n🔢 ترتيبي: #{b.get('pos', 1)}\n\nبلغني لو توفر مقعد شاغر عشان أحول فوراً! 🔥"
        wa_wait_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_wait_msg)}"
        st.markdown(f'<a href="{wa_wait_url}" target="_blank" class="wa-btn" style="background:#d97706;">📲 تأكيد وجودي بالانتظار عبر واتساب</a>', unsafe_allow_html=True)
        
    # 2. شاشة الحجز المؤكد والدفع
    else:
        target_epoch_ms = b.get("expire_timestamp", 0)
        memo_code = b.get("memo_code", "P99")
        
        st.markdown(f"""
        <div class="status-card-success">
            <h2 style="color:#22c55e; margin:0 0 4px 0;">🎉 تم حجز مقعدك بنجاح!</h2>
            <div style="font-size:1em; color:#e2e8f0; margin:6px 0;">
                المبلغ المطلوب للسداد: <b style="color:#22c55e; font-size:1.35em;">{int(UNIT_PRICE)} ر.س</b>
            </div>
            <div style="font-size:0.85em; color:#94a3b8; margin-top:4px;">
                كود الحجز المرجعي الخاص بك:
            </div>
            <div class="memo-tag">#{memo_code}</div>
            <div style="font-size:0.75em; color:#f87171;">(يرجى كتابة الكود في خانة الملاحظات أثناء التحويل البنكي)</div>
        </div>
        """, unsafe_allow_html=True)
        
        # عداد الـ 15 دقيقة الواضح
        components.html(f"""
        <!DOCTYPE html>
        <div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; border-radius: 14px; padding: 12px; color: #fca5a5; margin: 4px auto;">
            <div style="font-size: 14px; font-weight: 700; margin-bottom: 4px;">⏱️ مهلة سداد وتثبيت المقعد:</div>
            <div id="big_pay_timer" style="font-family: monospace; font-size: 36px; color: #ef4444; font-weight: 900; letter-spacing: 2px;">--:--</div>
            <div style="font-size: 11px; color: #f87171; margin-top: 2px;">(تنبيه: بعد انتهاء العداد يتحول المقعد تلقائياً للاعب التالي في الانتظار)</div>
        </div>
        <script>
            var payTarget = {target_epoch_ms};
            function updatePayTimer() {{
                var diff = payTarget - new Date().getTime();
                var el = document.getElementById('big_pay_timer');
                if (!el) return;
                if (diff <= 0) {{
                    el.innerHTML = "00:00";
                    el.style.color = "#991b1b";
                    return;
                }}
                var m = Math.floor(diff / 60000);
                var s = Math.floor((diff % 60000) / 1000);
                el.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            }}
            updatePayTimer();
            setInterval(updatePayTimer, 1000);
        </script>
        """, height=110)

        st.markdown(f"""
        <div style="background:#1e293b; border:1px solid #334155; border-radius:10px; padding:8px 12px; text-align:center; margin-top:8px;">
            <div style="font-size:0.8em; color:#94a3b8;">{ACCOUNT_NAME}</div>
            <div style="font-size:0.75em; color:#38bdf8; margin-top:2px;">اضغط على الأيقونة لنسخ رقم الآيبان مباشرة 👇</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.code(IBAN_NUMBER, language=None)
        
        wa_msg = f"هلا كابتن فارس 🎾\nأكدت حجز مقعدي في تمرين بادل 99 🤩\n\n👤 الكابتن: {b['name']}\n🔖 كود الحجز: #{memo_code}\n📅 تمرين: {display_session}\n💵 المبلغ المحول: {int(UNIT_PRICE)} ر.س\n\nمرفق إيصال التحويل لتثبيت المقعد! 🔥"
        wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال عبر واتساب وتأكيد المقعد</a>', unsafe_allow_html=True)

# ==============================================================================
# 8. نموذج التسجيل الموحد (حجز فوري أو انتظار ذكي)
# ==============================================================================
else:
    is_mode_waitlist = (seats_left == 0)
    btn_label = "التسجيل في قائمة الانتظار ⏳" if is_mode_waitlist else "تثبيت المقعد والانتقال للسداد 💸"
    
    if is_mode_waitlist:
        st.warning(f"⚠️ اكتملت مقاعد الكورت الـ 6. التسجيل متاح في قائمة الانتظار (يوجد {waitlist_count} لاعبين بالانتظار).")
        
    with st.form("main_booking_unified_v5", clear_on_submit=True):
        f_name = st.text_input("اسم اللاعب", placeholder="اكتب اسمك الثلاثي أو الثنائي", key="f_name_v5")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx", key="f_phone_v5")
        f_level = st.selectbox(
            "مستوى اللعب", 
            ["🟢 متوسط • ثبات في التبادلات والتمركز", "🔵 متقدم • سرعة وتكتيك وقوة ضربات", "🟡 مبتدئ متمكن • معرفة بقواعد اللعب والإرسال"],
            key="f_level_v5"
        )
        hp = st.text_input("hp", label_visibility="collapsed", key="f_hp_v5")
        
        btn_submit = st.form_submit_button(btn_label, use_container_width=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل اسمك ورقم جوال سعودي صحيح يبدأ بـ 05.")
            else:
                try:
                    c_active, w_active = process_waterfall_and_roster(db_session_key)
                    
                    if any(item["phone"] == clean_phone for item in c_active):
                        st.warning("أنت مسجل بالفعل ومقعدك محجوز في هذا التمرين!")
                    elif any(item["phone"] == clean_phone for item in w_active):
                        st.warning("أنت مسجل مسبقاً في قائمة الانتظار!")
                    else:
                        memo_id = f"P99-{clean_phone[-4:]}"
                        if len(c_active) < COURT_CAPACITY:
                            now_utc = datetime.now(timezone.utc)
                            expire_dt = now_utc + timedelta(minutes=15)
                            
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": db_session_key,
                                "court": 1,
                                "level": f_level.split("•")[0].strip(),
                                "status": "confirmed",
                                "payment_status": "pending",
                                "expires_at": expire_dt.isoformat(),
                                "hear_about": "DIRECT",
                                "player_note": f"MEMO:{memo_id}"
                            }).execute()
                            
                            st.session_state["booked"] = {
                                "name": clean_name,
                                "memo_code": memo_id,
                                "is_waitlist": False,
                                "expire_timestamp": int(expire_dt.timestamp() * 1000)
                            }
                            st.rerun()
                        else:
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": db_session_key,
                                "court": 1,
                                "level": f_level.split("•")[0].strip(),
                                "status": "waitlist",
                                "payment_status": "unpaid",
                                "hear_about": "WAITLIST",
                                "player_note": "انتظار"
                            }).execute()
                            
                            st.session_state["booked"] = {
                                "name": clean_name,
                                "is_waitlist": True,
                                "pos": len(w_active) + 1
                            }
                            st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {ex}")

# ==============================================================================
# 9. لوحة الإدارة الذكية والمؤشرات المالية
# ==============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة والتحكم المالي"):
    admin_pin = st.text_input("رمز الدخول السري (PIN):", type="password", key="admin_pin_input_master_v5")
    
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PIN_HASH):
        st.success("🔓 تم فتح لوحة التحكم الإدارية والمالية.")
        
        tab1, tab2, tab3 = st.tabs(["💰 المركز المالي", "👥 كشف الملعب والانتظار", "🛠️ تعديل الأسعار الفوري"])
        
        # 1. المركز المالي
        with tab1:
            all_records = supabase.table("bookings") \
                .select("id, name, phone, status, payment_status") \
                .eq("session_day", db_session_key) \
                .execute().data or []
                
            paid_players = [p for p in all_records if p.get("status") == "confirmed" and p.get("payment_status") == "paid"]
            pending_players = [p for p in all_records if p.get("status") == "confirmed" and p.get("payment_status") == "pending"]
            
            paid_count = len(paid_players)
            total_inflow = paid_count * UNIT_PRICE
            pending_inflow = len(pending_players) * UNIT_PRICE
            total_expenses = COURT_COST + BALLS_COST + WATER_COST
            escrow_reserved = min(total_inflow, COURT_COST) if not COURT_IS_PAID else 0
            net_profit = total_inflow - total_expenses
            break_even_seats = max(1, int(-(-total_expenses // UNIT_PRICE)))
            
            st.markdown(f"""
            <div class="finance-card">
                <div style="font-weight:800; color:#38bdf8; font-size:0.95em; margin-bottom:8px;">📊 ملخص الجلسة ({db_session_key}):</div>
                <div class="stat-row"><span>💵 إجمالي المقبوض كاش (المدفوع):</span><b style="color:#22c55e;">{int(total_inflow)} ر.س</b></div>
                <div class="stat-row"><span>⏳ مبالغ معلقة (قيد التحويل):</span><b style="color:#fbbf24;">{int(pending_inflow)} ر.س</b></div>
                <div class="stat-row"><span>🏟️ تكلفة إيجار الملعب:</span><span>{int(COURT_COST)} ر.س ({'تم السداد ✅' if COURT_IS_PAID else 'معلق لم يسدد ⏳'})</span></div>
                <div class="stat-row"><span>🎾 تكلفة الكرات الجديدة:</span><span>{int(BALLS_COST)} ر.س</span></div>
                <div class="stat-row"><span>💧 تكلفة مياه الشرب:</span><span>{int(WATER_COST)} ر.س</span></div>
                <div class="stat-row"><span>🔒 أمانة الملعب المحجوزة (Escrow):</span><b style="color:#38bdf8;">{int(escrow_reserved)} ر.س</b></div>
                <div class="stat-row" style="border:none; margin-top:6px; font-size:1em;">
                    <span>🏆 صافي الربح الحقيقي:</span>
                    <b style="color:{'#22c55e' if net_profit >= 0 else '#ef4444'}; font-size:1.15em;">{int(net_profit)} ر.س</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not COURT_IS_PAID:
                if st.button("تأكيد سداد الملعب رسمياً 🏟️", use_container_width=True):
                    supabase.table("session_finance").upsert({"session_day": db_session_key, "court_paid": True}, on_conflict="session_day").execute()
                    st.rerun()
            else:
                if st.button("إلغاء وسم سداد الملعب ↩️", use_container_width=True):
                    supabase.table("session_finance").upsert({"session_day": db_session_key, "court_paid": False}, on_conflict="session_day").execute()
                    st.rerun()

        # 2. كشف اللاعبين وتمديد المهلة
        with tab2:
            st.markdown("#### 👥 المؤكدين في الملعب:")
            c_list, w_list = process_waterfall_and_roster(db_session_key)
            
            for row in c_list:
                c1, c2, c3, c4 = st.columns([2, 1.1, 1.1, 1.1])
                c1.write(f"**{row['name']}**\n`{row['phone']}`")
                
                if row['payment_status'] == 'paid':
                    c2.markdown("<span style='color:#22c55e; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
                else:
                    c2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                    if c3.button("تثبيت ✅", key=f"pay_btn_v5_{row['id']}"):
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                        st.rerun()
                        
                    # زر تمديد الـ 15 دقيقة إضافية
                    if c4.button("+15د ⏱️", key=f"extend_btn_v5_{row['id']}"):
                        current_exp = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00')) if row.get('expires_at') else datetime.now(timezone.utc)
                        new_exp = (current_exp + timedelta(minutes=15)).isoformat()
                        supabase.table("bookings").update({"expires_at": new_exp}).eq("id", row['id']).execute()
                        st.success(f"تم تمديد المهلة 15 دقيقة لـ {row['name']}!")
                        st.rerun()
                        
            st.markdown("---")
            st.markdown(f"#### ⏳ قائمة الانتظار ({len(w_list)} لاعبين):")
            if not w_list:
                st.info("لا يوجد لاعبين في قائمة الانتظار حالياً.")
            else:
                for idx, wp in enumerate(w_list, 1):
                    col_w1, col_w2, col_w3 = st.columns([2.5, 1.2, 1])
                    col_w1.write(f"**#{idx} - {wp['name']}**\n`{wp['phone']}`")
                    
                    if col_w2.button("تصعيد ⬆️", key=f"promo_v5_{wp['id']}"):
                        new_promo_exp = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                        supabase.table("bookings").update({
                            "status": "confirmed",
                            "payment_status": "pending",
                            "expires_at": new_promo_exp
                        }).eq("id", wp['id']).execute()
                        st.success(f"تم تصعيد {wp['name']} إلى الملعب!")
                        st.rerun()
                        
                    promo_wa = f"هلا كابتن {wp['name']} 🎾\nألف مبروك! توفر لك مقعد رسمي في تمرين بادل 99 ({display_session}) 🤩\nمهلتك 15 دقيقة لتأكيد التحويل ({int(UNIT_PRICE)} ر.س) وتثبيت المقعد.\nالآيبان: {IBAN_NUMBER}\nبانتظار إيصالك! 🔥"
                    p_url = f"https://wa.me/{wp['phone'].replace('05', '9665', 1)}?text={urllib.parse.quote(promo_wa)}"
                    col_w3.markdown(f'<a href="{p_url}" target="_blank" style="text-decoration:none; font-size:1.3em;">💬</a>', unsafe_allow_html=True)

        # 3. تعديل الأسعار اللحظي الفوري
        with tab3:
            st.markdown("#### 🛠️ تعديل الأسعار والتكاليف (ينعكس فوراً):")
            with st.form("settings_instant_form_v5"):
                new_court = st.number_input("تكلفة إيجار الملعب (ر.س):", value=int(COURT_COST), step=10)
                new_unit = st.number_input("سعر المقعد للاعب (ر.س):", value=int(UNIT_PRICE), step=5)
                new_balls = st.number_input("تكلفة علبة الكرات (ر.س):", value=int(BALLS_COST), step=5)
                new_water = st.number_input("تكلفة كرتون المياه (ر.س):", value=int(WATER_COST), step=5)
                
                st.markdown("---")
                new_iban = st.text_input("رقم الآيبان (IBAN):", value=IBAN_NUMBER)
                new_acc = st.text_input("اسم صاحب الحساب والبنك:", value=ACCOUNT_NAME)
                
                btn_save_instant = st.form_submit_button("تطبيق وتحديث الأسعار فوراً 💾", use_container_width=True)
                
                if btn_save_instant:
                    updated_dict = {
                        "session_day": db_session_key,
                        "court_cost": new_court,
                        "unit_price": new_unit,
                        "balls_cost": new_balls,
                        "water_cost": new_water,
                        "iban_number": new_iban.strip(),
                        "account_name": new_acc.strip(),
                        "court_paid": COURT_IS_PAID,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    st.session_state["override_fin"] = updated_dict
                    
                    try:
                        supabase.table("session_finance").upsert(updated_dict, on_conflict="session_day").execute()
                        st.success("✅ تم تحديث الأسعار والحساب فوراً في المنصة والسحابة!")
                    except Exception:
                        st.info("✅ تم تطبيق الأسعار الجديدة بنجاح للجلسة الحالية!")
                    st.rerun()
