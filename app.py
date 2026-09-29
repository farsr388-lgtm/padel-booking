import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta
import math

# ==============================================================================
# 1. إعداد الصفحة والتنسيق البصري المتجاوب (Mobile-First CSS)
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
    max-width: 450px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
}

/* بطاقة الهيدر */
.hero-box {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 14px;
    text-align: center;
    margin-bottom: 10px;
}
.hero-title { font-size: 1.6em; font-weight: 900; color: #f8fafc; margin: 0; }
.hero-desc { color: #94a3b8; font-size: 0.85em; margin-top: 4px; }
.features-pill {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid #38bdf8;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78em;
    color: #38bdf8;
    margin: 6px 0;
    display: inline-block;
    font-weight: 700;
}

/* شبكة مقاعد الكورت */
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

/* بطاقات الحالة المتقدمة */
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
    padding: 6px 12px;
    display: inline-block;
    font-family: monospace;
    font-size: 1.15em;
    color: #38bdf8;
    font-weight: 800;
    margin: 6px 0;
}

/* لوحة المؤشرات المالية */
.finance-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 10px;
}
.stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.84em;
    padding: 6px 0;
    border-bottom: 1px solid #1e293b;
}

/* أزرار الإجراءات السريعة */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    color: #ffffff !important;
    font-size: 1.1em !important;
    font-weight: 800 !important;
    height: 50px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.35) !important;
}

.wa-btn {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 13px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 1em;
    text-decoration: none;
    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
    margin-top: 10px;
}

/* إخفاء حقل فخ الروبوتات */
.honeypot-field {
    opacity: 0;
    position: absolute;
    top: 0;
    left: 0;
    height: 0;
    width: 0;
    z-index: -1;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. حوكمة الربط السحابي (Cloud Database Resilience)
# ==============================================================================
@st.cache_resource
def init_supabase() -> Client:
    try:
        return create_client(
            st.secrets["SUPABASE_URL"].strip().rstrip('/'),
            st.secrets["SUPABASE_KEY"].strip()
        )
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        st.stop()

supabase = init_supabase()

# ==============================================================================
# 3. محرك الجدولة الزمنية الصارم (Deterministic Scheduling Engine)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))

def resolve_target_session() -> tuple[str, str, datetime]:
    """
    حساب الموعد القادم بدقة رياضية: الأحد، الثلاثاء، الخميس (الساعة 21:30 ت م).
    """
    now = datetime.now(KSA_TZ)
    # الأيام: 0: الإثنين, 1: الثلاثاء, 2: الأربعاء, 3: الخميس, 4: الجمعة, 5: السبت, 6: الأحد
    schedule_map = {
        0: (1, "الثلاثاء"),
        1: (0, "الثلاثاء"),
        2: (1, "الخميس"),
        3: (0, "الخميس"),
        4: (2, "الأحد"),
        5: (1, "الأحد"),
        6: (0, "الأحد")
    }
    
    offset_days, day_name = schedule_map[now.weekday()]
    candidate_dt = (now + timedelta(days=offset_days)).replace(hour=21, minute=30, second=0, microsecond=0)
    
    # إذا كان اليوم هو يوم التمرين وانتهى موعد الدخول (بعد 22:30)، ننتقل للتمرين التالي
    if offset_days == 0 and now >= candidate_dt + timedelta(hours=1):
        next_search = now + timedelta(days=1)
        next_offset, next_day_name = schedule_map[next_search.weekday()]
        candidate_dt = (next_search + timedelta(days=next_offset)).replace(hour=21, minute=30, second=0, microsecond=0)
        day_name = next_day_name

    display_label = f"{day_name} ({candidate_dt.strftime('%d/%m')})"
    db_key = f"{day_name} {candidate_dt.strftime('%Y-%m-%d')}"
    return display_label, db_key, candidate_dt

display_session, db_session_key, session_start_dt = resolve_target_session()

# ==============================================================================
# 4. محرك المالية والأسعار الفوري (Decision Support & Real-time Finance)
# ==============================================================================
COURT_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PIN_HASH = "9900"
PAYMENT_TIMEOUT_MINUTES = 15

def get_financial_ledger(session_key: str) -> dict:
    defaults = {
        "court_cost": 300.0,
        "unit_price": 65.0,
        "balls_cost": 35.0,
        "water_cost": 15.0,
        "court_paid": False,
        "iban_number": "SA9380000222608016013114",
        "account_name": "مصرف الراجحي | فارس ربيع العصيمي"
    }
    if "temp_fin_ledger" in st.session_state:
        return st.session_state["temp_fin_ledger"]
    try:
        res = supabase.table("session_finance").select("*").eq("session_day", session_key).execute()
        if res.data:
            return {**defaults, **res.data[0]}
    except Exception:
        pass
    return defaults

fin_settings = get_financial_ledger(db_session_key)
UNIT_PRICE = float(fin_settings["unit_price"])
COURT_COST = float(fin_settings["court_cost"])
BALLS_COST = float(fin_settings["balls_cost"])
WATER_COST = float(fin_settings["water_cost"])
COURT_IS_PAID = bool(fin_settings["court_paid"])
IBAN_NUMBER = str(fin_settings["iban_number"])
ACCOUNT_NAME = str(fin_settings["account_name"])

# ==============================================================================
# 5. منطق الشلال ومعالجة المقاعد وحماية التزامن (Waterfall & Integrity)
# ==============================================================================
def sync_roster_and_waterfall(session_key: str):
    """
    معالجة الإلغاء التلقائي للمتأخرين وتصعيد قائمة الانتظار لضمان إشغال المقاعد.
    """
    now_utc = datetime.now(timezone.utc)
    now_utc_str = now_utc.isoformat()
    
    try:
        response = supabase.table("bookings")\
            .select("*")\
            .eq("session_day", session_key)\
            .order("id")\
            .execute()
        records = response.data or []
    except Exception:
        return [], []

    active_confirmed = []
    waitlist = []

    for r in records:
        status = r.get("status")
        if status == "waitlist":
            waitlist.append(r)
        elif status == "confirmed":
            is_paid = r.get("payment_status") == "paid"
            exp_time = r.get("expires_at")
            is_expired = exp_time and exp_time <= now_utc_str
            
            # إلغاء المقعد المعلق بعد انقضاء المهلة
            if not is_paid and is_expired:
                supabase.table("bookings").update({
                    "status": "cancelled",
                    "player_note": "إلغاء تلقائي: انتهاء مهلة الـ 15 دقيقة"
                }).eq("id", r["id"]).execute()
            else:
                active_confirmed.append(r)

    # التصعيد التلقائي للشواغر
    available_slots = COURT_CAPACITY - len(active_confirmed)
    if available_slots > 0 and waitlist:
        promoted = waitlist[:available_slots]
        for p in promoted:
            new_exp = (now_utc + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES)).isoformat()
            supabase.table("bookings").update({
                "status": "confirmed",
                "payment_status": "pending",
                "expires_at": new_exp,
                "player_note": "تصعيد تلقائي من قائمة الانتظار"
            }).eq("id", p["id"]).execute()
            
            p["status"] = "confirmed"
            p["payment_status"] = "pending"
            p["expires_at"] = new_exp
            active_confirmed.append(p)
            waitlist.remove(p)

    return active_confirmed[:COURT_CAPACITY], waitlist

confirmed_roster, waitlist_roster = sync_roster_and_waterfall(db_session_key)
confirmed_count = len(confirmed_roster)
waitlist_count = len(waitlist_roster)
seats_remaining = max(0, COURT_CAPACITY - confirmed_count)

# ==============================================================================
# 6. الواجهة الرئيسية وشبكة الكورت
# ==============================================================================
cutoff_timestamp_ms = int(session_start_dt.astimezone(timezone.utc).timestamp() * 1000)

st.markdown(f"""
<div class="hero-box">
    <div class="hero-title">🎾 Padel 99</div>
    <div class="hero-desc">تمرين {display_session} • نظام أمريكانو تنافسي</div>
    <div class="features-pill">⚡ كرات جديدة • مياه مبردة • تدوير متكافئ</div>
    <div style="font-size:0.86em; color:#e2e8f0; margin-top:4px;">
        ⏰ 9:30 م - 11:30 م | كورت 1 ({COURT_CAPACITY} لاعبين) • 
        <b>{'متبقي ' + str(seats_remaining) + ' مقاعد فقط! 🔥' if seats_remaining > 0 else 'اكتملت المقاعد (متاح قائمة الانتظار ⏳)'}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# عداد الوقت التنازلي للتمرين
components.html(f"""
<div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 10px; padding: 7px; color: #f59e0b; font-size: 13px; font-weight: 700;">
    ⏳ متبقي على انطلاق التمرين: <span id="event_timer" style="font-family: monospace; font-size: 16px; color: #fbbf24; font-weight: 900;">--:--:--</span>
</div>
<script>
    var target = {cutoff_timestamp_ms};
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

# عرض بطاقات المقاعد
seats_ui = []
for i in range(COURT_CAPACITY):
    if i < confirmed_count:
        first_name = html.escape(confirmed_roster[i]['name'].split()[0])
        seats_ui.append(f'<div class="seat-card seat-taken">👤 {first_name} (محجوز)</div>')
    else:
        seats_ui.append('<div class="seat-card seat-empty">✨ مقعد شاغر</div>')

st.markdown(f"""
<div class="court-container">
    <div class="court-header">🏟️ كورت 1 ({confirmed_count}/{COURT_CAPACITY})</div>
    <div class="seats-grid">{''.join(seats_ui)}</div>
</div>
""", unsafe_allow_html=True)

# خطة تنظيم التمرين (نظام الأمريكانو)
with st.expander("📋 تفاصيل نظام التدوير والأمريكانو (120 دقيقة)"):
    st.markdown("""
    <div style="background: rgba(15, 23, 42, 0.7); border: 1px dashed #334155; border-radius: 10px; padding: 10px; font-size: 0.8em; color: #cbd5e1; line-height: 1.6;">
        • <b>مدة الجلسة:</b> ساعتان (120 دقيقة) مقسمة بالتساوي على 6 جولات.<br>
        • <b>الجهد البدني:</b> يلعب كل لاعب 4 جولات فعلية (72 دقيقة لعب عالي الكثافة).<br>
        • <b>الاسترجاع:</b> جولتان راحة (36 دقيقة) لإعادة الترطيب والتواصل الاجتماعي.<br>
        • <b>العدالة:</b> نظام تدوير الشركاء الرياضي لضمان التكافؤ التام بين جميع المشتركين.
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. معالجة تدفق الحجز والتحقق المنطقي المزدوج
# ==============================================================================
if "current_user_booking" in st.session_state:
    booking_meta = st.session_state["current_user_booking"]
    
    if booking_meta.get("is_waitlist", False):
        st.markdown(f"""
        <div class="status-card-waitlist">
            <h2 style="color:#fbbf24; margin:0 0 6px 0;">⏳ تم تسجيلك في قائمة الانتظار</h2>
            <div style="font-size:1.05em; color:#fef3c7; margin:6px 0;">
                ترتيبك الحالي: <b style="font-size:1.4em; color:#ffffff;">#{booking_meta.get('position', 1)}</b>
            </div>
            <div style="font-size:0.84em; color:#fde68a; line-height:1.6;">
                يراقب النظام سداد المقاعد آلياً؛ في حال تعثر سداد أي مقعد خلال مهلته، يتم تصعيدك تلقائياً للتشكيلة الأساسية وتفتح لك نافذة السداد.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_wait_text = f"هلا كابتن فارس 🎾\nأنا مسجل في انتظار بادل 99 ({display_session})\n👤 الاسم: {booking_meta['name']}\n🔢 ترتيبي: #{booking_meta.get('position', 1)}\nجاهز للتحويل وتأكيد المقعد فور توفره! 🔥"
        wa_wait_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_wait_text)}"
        st.markdown(f'<a href="{wa_wait_link}" target="_blank" class="wa-btn" style="background:#d97706;">📲 تأكيد وجودي بالانتظار عبر واتساب</a>', unsafe_allow_html=True)
    
    else:
        expire_ms = booking_meta.get("expire_timestamp", 0)
        memo_code = booking_meta.get("memo_code", "P99")
        
        st.markdown(f"""
        <div class="status-card-success">
            <h2 style="color:#22c55e; margin:0 0 4px 0;">🎉 تم حجز مقعدك المبدئي!</h2>
            <div style="font-size:1em; color:#e2e8f0; margin:6px 0;">
                المبلغ المطلوب للتحويل: <b style="color:#22c55e; font-size:1.35em;">{int(UNIT_PRICE)} ر.س</b>
            </div>
            <div style="font-size:0.85em; color:#94a3b8; margin-top:4px;">
                رمز الحجز المرجعي الخاص بك:
            </div>
            <div class="memo-tag">#{memo_code}</div>
            <div style="font-size:0.75em; color:#f87171;">(هام: اكتب الرمز أعلاه في خانة الملاحظات أثناء التحويل البنكي)</div>
        </div>
        """, unsafe_allow_html=True)
        
        # عداد الـ 15 دقيقة
        components.html(f"""
        <div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; border-radius: 14px; padding: 10px; color: #fca5a5; margin: 4px auto;">
            <div style="font-size: 13px; font-weight: 700; margin-bottom: 2px;">⏱️ مهلة سداد وتثبيت المقعد:</div>
            <div id="big_pay_timer" style="font-family: monospace; font-size: 34px; color: #ef4444; font-weight: 900; letter-spacing: 2px;">--:--</div>
            <div style="font-size: 11px; color: #f87171;">(بعد انتهاء العداد يلغى الحجز آلياً ويصعد اللاعب التالي بالانتظار)</div>
        </div>
        <script>
            var payTarget = {expire_ms};
            function runPaymentTimer() {{
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
            runPaymentTimer();
            setInterval(runPaymentTimer, 1000);
        </script>
        """, height=105)

        st.markdown(f"""
        <div style="background:#1e293b; border:1px solid #334155; border-radius:10px; padding:8px 12px; text-align:center; margin-top:8px;">
            <div style="font-size:0.8em; color:#94a3b8;">{ACCOUNT_NAME}</div>
            <div style="font-size:0.75em; color:#38bdf8; margin-top:2px;">انسخ رقم الآيبان للتحويل 👇</div>
        </div>
        """, unsafe_allow_html=True)
        st.code(IBAN_NUMBER, language=None)
        
        wa_confirm_text = f"هلا كابتن فارس 🎾\nحجزت مقعدي في تمرين بادل 99 ({display_session})\n👤 الكابتن: {booking_meta['name']}\n🔖 كود الحجز: #{memo_code}\n💵 المبلغ المحول: {int(UNIT_PRICE)} ر.س\n\nمرفق إيصال التحويل البنكي للتثبيت النهائي! 🔥"
        wa_confirm_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_confirm_text)}"
        st.markdown(f'<a href="{wa_confirm_link}" target="_blank" class="wa-btn">📲 إرسال الإيصال عبر واتساب وتثبيت المقعد</a>', unsafe_allow_html=True)

else:
    is_waitlist_mode = (seats_remaining == 0)
    btn_text = "التسجيل في قائمة الانتظار ⏳" if is_waitlist_mode else "تثبيت المقعد والانتقال للسداد 💸"
    
    if is_waitlist_mode:
        st.warning(f"⚠️ اكتملت المقاعد الـ 6 الأساسية. التسجيل متاح في قائمة الانتظار (يوجد {waitlist_count} لاعبين بالانتظار).")
        
    with st.form("booking_form_v6", clear_on_submit=False):
        form_name = st.text_input("اسم اللاعب", placeholder="اكتب اسمك الثنائي أو الثلاثي", key="player_name_input")
        form_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx", key="player_phone_input")
        form_level = st.selectbox(
            "مستوى اللعب", 
            ["🟢 متوسط • ثبات في التبادلات والتمركز", "🔵 متقدم • سرعة وتكتيك وقوة ضربات", "🟡 مبتدئ متمكن • إلمام بالقواعد والإرسال"],
            key="player_level_select"
        )
        # فخ برائحة العسل لمكافحة روبوتات السبام
        st.markdown('<div class="honeypot-field">', unsafe_allow_html=True)
        honeypot = st.text_input("hp_field", key="hp_field_key", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        submit_booking = st.form_submit_button(btn_text, use_container_width=True)

        if submit_booking:
            if honeypot:
                st.stop()  # استبعاد روبوتات الجمع العشوائي
                
            clean_name = form_name.strip()
            # توحيد الأرقام وتطهير المدخلات
            arabic_to_western = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
            clean_phone = re.sub(r'[\s\-\+]', '', form_phone.strip().translate(arabic_to_western))
            if clean_phone.startswith("966"):
                clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"):
                clean_phone = "0" + clean_phone
                
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05 ويتكون من 10 أرقام.")
            else:
                try:
                    # إعادة فحص السجلات لحظياً قبل إتمام المعاملة لمنع التصادم
                    active_c, active_w = sync_roster_and_waterfall(db_session_key)
                    
                    if any(x["phone"] == clean_phone for x in active_c):
                        st.warning("أنت مسجل بالفعل في التشكيلة الأساسية لهذا التمرين!")
                    elif any(x["phone"] == clean_phone for x in active_w):
                        st.warning("أنت مسجل مسبقاً في قائمة الانتظار!")
                    else:
                        memo_id = f"P99-{clean_phone[-4:]}"
                        now_utc = datetime.now(timezone.utc)
                        
                        # تحقق منطقي من الطاقة الاستيعابية
                        if len(active_c) < COURT_CAPACITY:
                            expire_at = now_utc + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES)
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": db_session_key,
                                "court": 1,
                                "level": form_level.split("•")[0].strip(),
                                "status": "confirmed",
                                "payment_status": "pending",
                                "expires_at": expire_at.isoformat(),
                                "hear_about": "DIRECT",
                                "player_note": f"MEMO:{memo_id}"
                            }).execute()
                            
                            st.session_state["current_user_booking"] = {
                                "name": clean_name,
                                "memo_code": memo_id,
                                "is_waitlist": False,
                                "expire_timestamp": int(expire_at.timestamp() * 1000)
                            }
                            st.rerun()
                        else:
                            # في حال اكتمال المقاعد أثناء إدخال البيانات، يوجه للانتظار تلقائياً
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": db_session_key,
                                "court": 1,
                                "level": form_level.split("•")[0].strip(),
                                "status": "waitlist",
                                "payment_status": "unpaid",
                                "hear_about": "WAITLIST",
                                "player_note": "انتظار"
                            }).execute()
                            
                            st.session_state["current_user_booking"] = {
                                "name": clean_name,
                                "is_waitlist": True,
                                "position": len(active_w) + 1
                            }
                            st.rerun()
                            
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة العملية: {ex}")

# ==============================================================================
# 8. لوحة الإدارة ونظام دعم القرار المالي (Decision Support System)
# ==============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة والتحكم المالي"):
    admin_pass = st.text_input("رمز الدخول (PIN):", type="password", key="admin_pin_input_master")
    
    if admin_pass and hmac.compare_digest(admin_pass.strip(), ADMIN_PIN_HASH):
        st.success("🔓 تم التحقق وفتح صلاحيات الإدارة.")
        tab_fin, tab_roster, tab_settings = st.tabs(["💰 المركز المالي", "👥 كشف اللاعبين", "🛠️ تعديل التكاليف"])
        
        # 1. المركز المالي ومؤشرات الأداء (KPIs)
        with tab_fin:
            records_res = supabase.table("bookings").select("id, name, phone, status, payment_status").eq("session_day", db_session_key).execute()
            records = records_res.data or []
            
            paid_players = [p for p in records if p.get("status") == "confirmed" and p.get("payment_status") == "paid"]
            pending_players = [p for p in records if p.get("status") == "confirmed" and p.get("payment_status") == "pending"]
            
            inflow_actual = len(paid_players) * UNIT_PRICE
            inflow_projected = len(pending_players) * UNIT_PRICE
            total_expenses = COURT_COST + BALLS_COST + WATER_COST
            escrow_obligation = min(inflow_actual, COURT_COST) if not COURT_IS_PAID else 0
            net_operating_profit = inflow_actual - total_expenses
            
            # حساب نقطة التعادل التشغيلي ومعدل الأمان
            break_even_players = math.ceil(total_expenses / UNIT_PRICE) if UNIT_PRICE > 0 else 0
            margin_of_safety_seats = COURT_CAPACITY - break_even_players
            
            st.markdown(f"""
            <div class="finance-card">
                <div style="font-weight:800; color:#38bdf8; font-size:0.95em; margin-bottom:8px;">📊 مؤشرات الجلسة ({db_session_key}):</div>
                <div class="stat-row"><span>💵 المقبوضات الفعلية (الكاش المحصل):</span><b style="color:#22c55e;">{int(inflow_actual)} ر.س</b></div>
                <div class="stat-row"><span>⏳ المقبوضات المتوقعة (قيد التأكيد):</span><b style="color:#fbbf24;">{int(inflow_projected)} ر.س</b></div>
                <div class="stat-row"><span>🏟️ إيجار الملعب:</span><span>{int(COURT_COST)} ر.س ({'مسدد ✅' if COURT_IS_PAID else 'مستحق ⏳'})</span></div>
                <div class="stat-row"><span>🎾 تكلفة الكرات الجديدة:</span><span>{int(BALLS_COST)} ر.س</span></div>
                <div class="stat-row"><span>💧 تكلفة المياه:</span><span>{int(WATER_COST)} ر.س</span></div>
                <div class="stat-row"><span>🔒 أمانة الملعب المحتجزة (Escrow):</span><b style="color:#38bdf8;">{int(escrow_obligation)} ر.س</b></div>
                <div class="stat-row"><span>🎯 نقطة التعادل (Break-even):</span><b>{break_even_players} مقاعد تغطي التكاليف</b></div>
                <div class="stat-row"><span>🛡️ هامش الأمان التشغيلي:</span><b>{margin_of_safety_seats} مقاعد أرباح خالصة</b></div>
                <div class="stat-row" style="border:none; margin-top:6px;">
                    <span style="font-size:1em;">🏆 صافي الربح التشغيلي المحقق:</span>
                    <b style="color:{'#22c55e' if net_operating_profit >= 0 else '#ef4444'}; font-size:1.15em;">{int(net_operating_profit)} ر.س</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not COURT_IS_PAID:
                if st.button("تأكيد سداد الملعب وإخلاء عهدة الأمانة 🏟️", use_container_width=True):
                    supabase.table("session_finance").upsert({"session_day": db_session_key, "court_paid": True}, on_conflict="session_day").execute()
                    st.rerun()
            else:
                if st.button("إلغاء وسم سداد الملعب ↩️", use_container_width=True):
                    supabase.table("session_finance").upsert({"session_day": db_session_key, "court_paid": False}, on_conflict="session_day").execute()
                    st.rerun()

        # 2. كشف اللاعبين والتحكم الإداري
        with tab_roster:
            st.markdown("#### 👥 التشكيلة الأساسية للكورت:")
            c_current, w_current = sync_roster_and_waterfall(db_session_key)
            
            for row in c_current:
                col1, col2, col3, col4 = st.columns([2, 1.1, 1.1, 1.1])
                col1.write(f"**{row['name']}**\n`{row['phone']}`")
                
                if row['payment_status'] == 'paid':
                    col2.markdown("<span style='color:#22c55e; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
                else:
                    col2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                    if col3.button("تأكيد ✅", key=f"pay_btn_{row['id']}"):
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                        st.rerun()
                        
                    if col4.button("+15د ⏱️", key=f"ext_btn_{row['id']}"):
                        base_t = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00')) if row.get('expires_at') else datetime.now(timezone.utc)
                        new_t = (base_t + timedelta(minutes=15)).isoformat()
                        supabase.table("bookings").update({"expires_at": new_t}).eq("id", row['id']).execute()
                        st.success(f"تم تمديد المهلة لـ {row['name']}!")
                        st.rerun()
                        
            st.markdown("---")
            st.markdown(f"#### ⏳ قائمة الانتظار ({len(w_current)} لاعبين):")
            if not w_current:
                st.info("لا توجد أسماء في قائمة الانتظار حالياً.")
            else:
                for idx, wp in enumerate(w_current, 1):
                    cw1, cw2, cw3 = st.columns([2.5, 1.2, 1])
                    cw1.write(f"**#{idx} - {wp['name']}**\n`{wp['phone']}`")
                    
                    if cw2.button("تصعيد ⬆️", key=f"promote_{wp['id']}"):
                        new_promo_exp = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                        supabase.table("bookings").update({
                            "status": "confirmed",
                            "payment_status": "pending",
                            "expires_at": new_promo_exp
                        }).eq("id", wp['id']).execute()
                        st.success(f"تم تصعيد {wp['name']} إلى الملعب!")
                        st.rerun()
                        
                    promo_wa_msg = f"هلا كابتن {wp['name']} 🎾\nألف مبروك! توفر مقعد لك في تمرين بادل 99 ({display_session}) 🤩\nأمامك 15 دقيقة لتحويل الرسوم ({int(UNIT_PRICE)} ر.س) لتثبيت الحجز.\nالآيبان: {IBAN_NUMBER}\nبانتظار إيصالك! 🔥"
                    promo_link = f"https://wa.me/{wp['phone'].replace('05', '9665', 1)}?text={urllib.parse.quote(promo_wa_msg)}"
                    cw3.markdown(f'<a href="{promo_link}" target="_blank" style="text-decoration:none; font-size:1.3em;">💬</a>', unsafe_allow_html=True)

        # 3. إعدادات التسعير المرن الفوري
        with tab_settings:
            st.markdown("#### 🛠️ تعديل الأسعار والتكاليف:")
            with st.form("admin_settings_form"):
                in_court = st.number_input("تكلفة إيجار الملعب (ر.س):", value=int(COURT_COST), step=10)
                in_unit = st.number_input("سعر المقعد للاعب (ر.س):", value=int(UNIT_PRICE), step=5)
                in_balls = st.number_input("تكلفة علبة الكرات (ر.س):", value=int(BALLS_COST), step=5)
                in_water = st.number_input("تكلفة كرتون المياه (ر.س):", value=int(WATER_COST), step=5)
                st.markdown("---")
                in_iban = st.text_input("رقم الآيبان (IBAN):", value=IBAN_NUMBER)
                in_acc = st.text_input("اسم الحساب والبنك:", value=ACCOUNT_NAME)
                
                save_settings = st.form_submit_button("حفظ وتحديث فوري 💾", use_container_width=True)
                
                if save_settings:
                    payload = {
                        "session_day": db_session_key,
                        "court_cost": in_court,
                        "unit_price": in_unit,
                        "balls_cost": in_balls,
                        "water_cost": in_water,
                        "iban_number": in_iban.strip(),
                        "account_name": in_acc.strip(),
                        "court_paid": COURT_IS_PAID,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    st.session_state["temp_fin_ledger"] = payload
                    try:
                        supabase.table("session_finance").upsert(payload, on_conflict="session_day").execute()
                        st.success("تم تحديث البيانات المالية وتطبيقها بنجاح!")
                    except Exception:
                        st.info("تم حفظ الإعدادات للجلسة الحالية محلياً!")
                    st.rerun()
