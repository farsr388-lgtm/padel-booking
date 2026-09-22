import streamlit as st
import io
import csv
import re
import hmac
import time
import html
import urllib.parse
from datetime import datetime, timezone, timedelta, time as dtime, date
from supabase import create_client, Client

# ==========================================
# 1. إعداد الاتصال السحابي (Supabase Client)
# ==========================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your-anon-key")

@st.cache_resource
def init_supabase() -> Client:
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات السحابية: {e}")
        return None

supabase = init_supabase()

# ==========================================
# 2. الهوية البصرية وإعدادات الشاشة
# ==========================================
st.set_page_config(
    page_title="Padel 99 | بادل 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

LANG = {
    "ar": {
        "dir": "rtl",
        "align": "right",
        "brand": "Padel 99.",
        "hero_sub": "تمرين {}. تجربة لعب متكاملة بتنظيم احترافي.",
        "value_banner": "⚡ كرات جديدة تفتح أمامك • مياه مبردة • تدوير عادل 15 دقيقة",
        "guarantee_badge": "🛡️ نضمن لك توازناً ومتعة تنافسية، أو مقعدك القادم علينا.",
        "time_str": "⏰ ٩:٣٠ م – ١١:٠٠ م | كورت 1 (6 مقاعد)",
        "court1": "🏟️ كورت 1",
        "tab_book": "⚡ حجز مقعد",
        "tab_system": "📋 خطة التدوير والميدان",
        "tab_rules": "📜 سياسة الإلغاء والمهلة",
        "tab_cancel": "❌ اعتذار",
        "name_lbl": "اسم اللاعب",
        "phone_lbl": "رقم الجوال (05xxxxxxxx)",
        "level_lbl": "مستوى اللعب",
        "levels": [
            "🟢 متوسط • ثبات في التبادلات والتمركز",
            "🔥 متقدم • سرعة وتكتيك وقوة ضربات",
            "⚪ مبتدئ • بداية التعلّم والشغف"
        ],
        "btn_book": "تثبيت المقعد والانتقال للسداد 🚀",
        "err_fields": "فضلاً أدخل الاسم ورقم جوال سعودي يبدأ بـ 05 ويتكون من 10 أرقام.",
        "err_duplicate": "أنت مسجل بالفعل في تمرين هذا اليوم.",
        "err_spam": "تم رفض العملية للاشتباه في نشاط آلي.",
        "succ_book_title": "✅ تم حجز مقعدك بنجاح يا كابتن {}!",
        "succ_book_desc": "مقعدك في <b>{}</b> متاح مؤقتاً لمدة 15 دقيقة لتأكيد التحويل البنكي.",
        "succ_wait": "اكتملت المقاعد الأساسية. تم تسجيلك في المرتبة #{} في قائمة الاحتياط.",
        "cancel_phone": "رقم الجوال المسجل:",
        "cancel_reason": "سبب الاعتذار:",
        "reasons": [
            "تعارض مفاجئ في المواعيد",
            "إجهاد بدني أو إصابة",
            "ظرف شخصي طارئ",
            "صعوبة في المواصلات"
        ],
        "btn_cancel": "تأكيد الإلغاء وإتاحة المقعد للاحتياط",
        "succ_cancel": "تم قبول اعتذارك يا كابتن {}. نراك في التمرين القادم.",
        "err_cancel": "لا يوجد حجز مؤكد مرتبط بهذا الرقم اليوم.",
        "admin_pin": "رمز الإدارة السري المشفر:",
        "export_btn": "📥 تصدير السجل (Excel/CSV)",
        "timer_prefix": "⏳ متبقي على إغلاق الحجز:",
        "timer_closed": "🔒 أُغلق حجز هذا التمرين تلقائياً"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "brand": "Padel 99.",
        "hero_sub": "{} Session. Pure padel, zero hassle.",
        "value_banner": "⚡ Fresh Balls • Chilled Water • 15m Fair Rotation",
        "guarantee_badge": "🛡️ Competitive & balanced matches guaranteed, or next session on us.",
        "time_str": "⏰ 9:30 PM – 11:00 PM | Court 1 (6 Slots Only)",
        "court1": "🏟️ Court 1",
        "tab_book": "⚡ Reserve Spot",
        "tab_system": "📋 Court Dynamics",
        "tab_rules": "📜 Policy & Payment Window",
        "tab_cancel": "❌ Cancel",
        "name_lbl": "Player Name",
        "phone_lbl": "Mobile (05xxxxxxxx)",
        "level_lbl": "Skill Level",
        "levels": [
            "🟢 Intermediate • Steady rallies & positioning",
            "🔥 Advanced • Tactical pace & power",
            "⚪ Beginner • Starting out & eager to learn"
        ],
        "btn_book": "Reserve & Proceed to Payment 🚀",
        "err_fields": "Enter a valid name and Saudi mobile (05xxxxxxxx).",
        "err_duplicate": "You have an active booking for this session.",
        "err_spam": "Rejected due to automated activity.",
        "succ_book_title": "✅ Spot Reserved for Captain {}!",
        "succ_book_desc": "Your slot for <b>{}</b> is held for 15 mins pending payment confirmation.",
        "succ_wait": "Main roster full. You are #{} on the waitlist.",
        "cancel_phone": "Registered Mobile:",
        "cancel_reason": "Reason:",
        "reasons": [
            "Schedule conflict",
            "Fatigue or injury",
            "Personal emergency",
            "Transportation issue"
        ],
        "btn_cancel": "Release Spot to Waitlist",
        "succ_cancel": "Cancelled for Captain {}. See you next time.",
        "err_cancel": "No active booking found for this number today.",
        "admin_pin": "Manager Passcode:",
        "export_btn": "📥 Export Timesheet (Excel/CSV)",
        "timer_prefix": "⏳ Registration Closes In:",
        "timer_closed": "🔒 Session Registration Closed"
    }
}

col_lang1, col_lang2 = st.columns([5, 1])
with col_lang2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# ==========================================
# 3. واجهة وتنسيقات CSS المتطورة (Apple Minimalist)
# ==========================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
* {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}
.block-container {{ padding: 0.8rem 0.5rem 1.2rem 0.5rem !important; max-width: 580px !important; }}
.stAppHeader {{ display: none; }}

.hero-header {{ font-size: 1.7em; font-weight: 900; letter-spacing: -0.5px; color: #f4f4f5; margin: 0; }}
.hero-sub {{ font-size: 0.88em; color: #a1a1aa; margin-bottom: 6px; }}
.value-pill {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 5px 8px; font-size: 0.75em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }}
.guarantee-badge {{ background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; padding: 5px 8px; text-align: center; color: #6ee7b7; font-weight: 700; font-size: 0.75em; margin-bottom: 8px; }}

.countdown-box {{
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.25);
    border-radius: 8px;
    padding: 8px 12px;
    margin: 6px 0 10px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.82em;
    color: #fbbf24;
}}

.thankyou-box {{
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 78, 59, 0.25) 100%);
    border: 1.5px solid #10b981;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 10px 0;
    text-align: center;
}}
.thankyou-title {{ color: #34d399; font-size: 1.05em; font-weight: 800; margin-bottom: 4px; }}
.thankyou-sub {{ color: #e2e8f0; font-size: 0.84em; }}

.info-card {{
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 14px;
    padding: 14px;
    margin: 8px 0;
}}
.info-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 0.82em;
    color: #e2e8f0;
    line-height: 1.4;
}}
.info-row:last-child {{ margin-bottom: 0; }}

.alrajhi-card {{
    background: #111418;
    border: 1.5px solid #2d3748;
    border-radius: 18px;
    padding: 16px;
    margin: 12px 0;
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    color: #ffffff;
}}
.card-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 8px;
    margin-bottom: 12px;
}}
.price-pill {{ background: #10b981; color: #022c22; padding: 3px 10px; border-radius: 20px; font-weight: 900; font-size: 0.85em; }}
.qr-container {{ background: #ffffff; padding: 10px; border-radius: 12px; display: inline-block; margin: 4px auto 10px auto; }}
.qr-container img {{ display: block; width: 130px; height: 130px; }}
.card-owner {{ font-size: 1.1em; font-weight: 800; color: #f8fafc; margin-bottom: 10px; text-align: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.12); padding-bottom: 8px; }}
.copy-badge {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 10px;
    font-family: monospace;
    font-size: 0.90em;
    color: #38bdf8;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 8px;
}}

.wa-action-btn {{
    display: block;
    width: 100%;
    background: linear-gradient(180deg, #25D366 0%, #1da851 100%);
    color: white !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 800;
    text-decoration: none;
    margin-top: 8px;
    font-size: 0.92em;
    box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
}}

.wa-community-btn {{
    display: block;
    width: 100%;
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid #3b82f6;
    color: #93c5fd !important;
    text-align: center;
    padding: 10px;
    border-radius: 10px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 8px;
    font-size: 0.85em;
}}

.padel-court {{ background: radial-gradient(circle, #064e3b 0%, #022c22 100%); border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 12px; padding: 12px; margin-bottom: 6px; }}
.court-title {{ text-align: center; color: #a7f3d0; font-weight: 800; font-size: 0.95em; margin-bottom: 10px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 6px; }}
.court-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.slot-box {{ background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 8px 6px; text-align: center; min-height: 52px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
.slot-occupied {{ color: #f4f4f5; font-weight: 700; font-size: 0.84em; line-height: 1.2; word-break: break-word; }}
.slot-meta {{ display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.70em; margin-top: 4px; flex-wrap: wrap; }}
.slot-empty {{ color: #52525b; font-size: 0.78em; }}
.badge-level {{ background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 4px; border-radius: 3px; font-size: 0.70em; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.15); }}
.badge-status {{ background-color: rgba(16, 185, 129, 0.2); color: #6ee7b7; padding: 1px 4px; border-radius: 3px; font-size: 0.68em; font-weight: 700; }}

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. محرك التوقيت والتحقق الأمني
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

def check_active_booking(phone, s_date: date):
    if not supabase:
        return False
    try:
        res = supabase.table("bookings").select("id").eq("player_phone", phone).eq("session_date", s_date.isoformat()).in_("status", ["confirmed", "waitlist"]).execute()
        return len(res.data) > 0
    except Exception:
        return False

def verify_admin_security(input_pin):
    now = time.time()
    if "admin_attempts" not in st.session_state:
        st.session_state["admin_attempts"] = 0
    if "admin_lockout_until" not in st.session_state:
        st.session_state["admin_lockout_until"] = 0
        
    if now < st.session_state["admin_lockout_until"]:
        rem = int(st.session_state["admin_lockout_until"] - now)
        st.error(f"🔒 لوحة الإدارة مقفلة حمايةً للنظام. انتظر: {rem // 60}:{rem % 60:02d} دقيقة.")
        return False

    if not input_pin:
        return False

    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    p = str(input_pin).translate(ar_digits).strip()
    
    master_secret = st.secrets.get("ADMIN_PASSWORD", None) or st.secrets.get("ADMIN_PIN", "Padel99#Master@2026")
    target_secret = str(master_secret).translate(ar_digits).strip()

    if hmac.compare_digest(p, target_secret):
        st.session_state["admin_attempts"] = 0
        return True
    else:
        st.session_state["admin_attempts"] += 1
        if st.session_state["admin_attempts"] >= 3:
            st.session_state["admin_lockout_until"] = now + 600
            st.error("🚨 تم قفل اللوحة لمدة 10 دقائق بعد 3 محاولات خاطئة.")
        else:
            left = 3 - st.session_state["admin_attempts"]
            st.error(f"رمز غير صحيح. المحاولات المتبقية: {left}")
        return False

def get_next_session(cutoff_minutes_before: int = 60):
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    SESSION_DAYS = {
        6: ("الأحد", "Sunday"),
        1: ("الثلاثاء", "Tuesday"),
        3: ("الخميس", "Thursday")
    }
    
    start_hour, start_min = 21, 30
    total_cutoff_min = (start_hour * 60 + start_min) - cutoff_minutes_before
    cutoff_time = dtime(total_cutoff_min // 60, total_cutoff_min % 60)

    today_weekday = now.weekday()
    is_session_today = today_weekday in SESSION_DAYS
    is_before_cutoff = now.time() < cutoff_time

    if is_session_today and is_before_cutoff:
        days_to_add = 0
    else:
        days_to_add = 1
        while (today_weekday + days_to_add) % 7 not in SESSION_DAYS:
            days_to_add += 1

    target_datetime = now + timedelta(days=days_to_add)
    target_weekday = target_datetime.weekday()
    d_ar, d_en = SESSION_DAYS[target_weekday]
    
    date_str = target_datetime.strftime("%d/%m")
    label_ar = f"{d_ar} ({date_str})"
    label_en = f"{d_en} ({date_str})"
    session_target_date = target_datetime.date()
    
    cutoff_dt = target_datetime.replace(
        hour=cutoff_time.hour, minute=cutoff_time.minute, second=0, microsecond=0
    )
    
    return label_ar, label_en, session_target_date, cutoff_dt

def render_session_countdown(cutoff_dt: datetime, lang_dict: dict):
    cutoff_iso = cutoff_dt.isoformat()
    txt_prefix = lang_dict["timer_prefix"]
    txt_closed = lang_dict["timer_closed"]
    
    countdown_html = f"""
    <div id="countdown-card" class="countdown-box">
        <span style="font-weight: 600;">{txt_prefix}</span>
        <span id="timer-display" style="font-family: ui-monospace, SFMono-Regular, monospace; font-weight: 800; letter-spacing: 0.5px; color: #fef3c7;">--:--:--</span>
    </div>

    <script>
    (function() {{
        const targetDate = new Date("{cutoff_iso}").getTime();
        
        function updateTimer() {{
            const now = new Date().getTime();
            const diff = targetDate - now;
            const timerElem = document.getElementById("timer-display");
            const cardElem = document.getElementById("countdown-card");

            if (!timerElem || !cardElem) return;

            if (diff <= 0) {{
                cardElem.style.background = "rgba(239, 68, 68, 0.08)";
                cardElem.style.borderColor = "rgba(239, 68, 68, 0.25)";
                cardElem.style.color = "#f87171";
                cardElem.innerHTML = "<span>{txt_closed}</span>";
                clearInterval(interval);
                return;
            }}

            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            const pad = (n) => n < 10 ? '0' + n : n;
            timerElem.innerText = pad(hours) + "h " + pad(minutes) + "m " + pad(seconds) + "s";
        }}

        updateTimer();
        const interval = setInterval(updateTimer, 1000);
    }})();
    </script>
    """
    st.markdown(countdown_html, unsafe_allow_html=True)

# استدعاء الجلسة الحالية
sess_ar, sess_en, session_date_obj, session_cutoff_dt = get_next_session()
display_session = sess_ar if l_code == "ar" else sess_en
COURT_CAPACITY = 6

# جلب بيانات الملعب والاحتياط من Supabase باستخدام تاريخ نقي (ISO DATE)
c1 = []
waitlist = []
if supabase:
    try:
        res_c1 = supabase.table("bookings").select("*").eq("session_date", session_date_obj.isoformat()).eq("court_number", 1).eq("status", "confirmed").order("id").limit(6).execute()
        c1 = res_c1.data if res_c1.data else []

        res_wait = supabase.table("bookings").select("*").eq("session_date", session_date_obj.isoformat()).eq("status", "waitlist").order("id").execute()
        waitlist = res_wait.data if res_wait.data else []
    except Exception:
        st.warning("جاري مزامنة السجلات السحابية...")

total_booked = len(c1)
remaining_slots = max(0, COURT_CAPACITY - total_booked)

# ==========================================
# 5. واجهة المستخدم والتسجيل المباشر
# ==========================================
st.markdown(f"<div class='hero-header'>{t['brand']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>{t['hero_sub'].format(display_session)}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='value-pill'>{t['value_banner']}</div>", unsafe_allow_html=True)
st.markdown(f'<div class="guarantee-badge">{t["guarantee_badge"]}</div>', unsafe_allow_html=True)

if remaining_slots > 0:
    st.caption(f"{t['time_str']} • <b style='color:#34d399;'>متبقي {remaining_slots} مقاعد فقط! 🔥</b>", unsafe_allow_html=True)
else:
    st.caption(f"{t['time_str']} • <b style='color:#f87171;'>اكتملت المقاعد الأساسية (قائمة الاحتياط متاحة)</b>", unsafe_allow_html=True)

render_session_countdown(session_cutoff_dt, t)

tab_book, tab_system, tab_rules, tab_cancel = st.tabs([t["tab_book"], t["tab_system"], t["tab_rules"], t["tab_cancel"]])

with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([3, 2])
        with c_in1:
            f_name = st.text_input(t["name_lbl"])
        with c_in2:
            f_phone = st.text_input(t["phone_lbl"], placeholder="05xxxxxxxx")
        
        f_level_raw = st.selectbox(t["level_lbl"], t["levels"])
        f_level = "متوسط" if ("متوسط" in f_level_raw or "Intermediate" in f_level_raw) else ("متقدم" if ("متقدم" in f_level_raw or "Advanced" in f_level_raw) else "مبتدئ")
        
        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button(t["btn_book"])

        if btn_submit:
            if honeypot_val:
                st.error(t["err_spam"])
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 2 or not clean_phone:
                st.error(t["err_fields"])
            elif check_active_booking(clean_phone, session_date_obj):
                st.warning(t["err_duplicate"])
            else:
                try:
                    # فحص عدد المقاعد لحظياً قبل الإدخال لمنع التضارب
                    res_count = supabase.table("bookings").select("id", count="exact").eq("session_date", session_date_obj.isoformat()).eq("court_number", 1).eq("status", "confirmed").execute()
                    cur_c1 = len(res_count.data) if res_count.data else 0

                    status_val = 'confirmed' if cur_c1 < COURT_CAPACITY else 'waitlist'

                    supabase.table("bookings").insert({
                        "player_name": clean_name,
                        "player_phone": clean_phone,
                        "session_date": session_date_obj.isoformat(),
                        "court_number": 1,
                        "player_level": f_level,
                        "status": status_val,
                        "payment_status": "pending",
                        "attendance": "unknown"
                    }).execute()

                    wait_pos = None
                    if status_val == 'waitlist':
                        res_wait_count = supabase.table("bookings").select("id", count="exact").eq("session_date", session_date_obj.isoformat()).eq("status", "waitlist").execute()
                        wait_pos = len(res_wait_count.data) if res_wait_count.data else 1

                    st.session_state["last_booking"] = {
                        "name": clean_name,
                        "phone": clean_phone,
                        "status": status_val,
                        "wait_pos": wait_pos,
                        "session": display_session,
                        "is_new": True
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ أثناء حفظ الحجز: {e}")

    # تفاصيل الدفع بعد التسجيل
    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        escaped_user_name = html.escape(lb["name"])
        
        if lb["status"] == "confirmed":
            if lb.get("is_new", False):
                st.balloons()
                lb["is_new"] = False

            thank_html = f"""
            <div class="thankyou-box">
                <div class="thankyou-title">{t["succ_book_title"].format(escaped_user_name)}</div>
                <div class="thankyou-sub">{t["succ_book_desc"].format(lb["session"])}</div>
            </div>
            """
            st.markdown(thank_html, unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={iban_raw}&color=000000&bgcolor=ffffff"

            card_html = f"""
<div class="alrajhi-card">
    <div class="card-top">
        <div style="font-weight:800; font-size:0.95em;">🏛️ مصرف الراجحي</div>
        <div class="price-pill">65 ر.س</div>
    </div>
    <div style="text-align:center;">
        <div class="qr-container">
            <img src="{qr_url}" alt="Al Rajhi QR" />
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
    <div style="margin-top: 8px; padding: 8px 10px; background: rgba(56, 189, 248, 0.08); border-radius: 8px; border: 1px dashed rgba(56, 189, 248, 0.3); display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 0.74em; color: #cbd5e1;">💡 <b>لحفظ المستفيد في تطبيق بنكك:</b></div>
        <div class="copy-badge" style="margin-bottom:0; padding:4px 8px; font-size:0.82em;" onclick="navigator.clipboard.writeText('بادل 99'); alert('تم نسخ اسم المستفيد: بادل 99 📋');">
            <span>بادل 99</span>
            <span>📋</span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:0.72em; color:#64748b; margin-top:8px;">
        <span>سويفت: <b>RJHISARI</b></span>
        <span>⚡ تحويل فوري</span>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            wa_msg = f"🎾 تأكيد حجز مقعد | بادل 99\n\nالكابتن: {lb['name']}\nالتمرين: {lb['session']} (كورت 1)\nالمبلغ: 65 ر.س\n\nمرفق إشعار التحويل البنكي لحساب كابتن فارس العصيمي لتثبيت الحجز النهائي."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-action-btn">📲 إرسال إشعار التحويل وتثبيت المقعد (خلال مهلة 15 دقيقة)</a>', unsafe_allow_html=True)
            
            # رابط مجتمع بادل 99 على واتساب
            wa_group_url = "https://chat.whatsapp.com/YOUR_COMMUNITY_LINK"
            st.markdown(f'<a href="{wa_group_url}" target="_blank" class="wa-community-btn">👥 انضم إلى مجتمع بادل 99 (أولوية التسجيل والتحديات)</a>', unsafe_allow_html=True)
        else:
            st.info(t["succ_wait"].format(lb.get("wait_pos", 1)))

# قسم خطة التمرين والميدان
with tab_system:
    st.markdown("""
    <div class="info-card">
        <div class="info-row">
            <span style="font-size:1.3em;">🔄</span>
            <div><b>نظام التدوير العادل (Americano Style):</b> 6 لاعبين على الملعب؛ 4 يلعبون شوطين (أو 15 دقيقة) و2 يستريحون، مما يضمن لعب الجميع مع وضد بعضهم بعدالة ودون انتظار طويل.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">🎾</span>
            <div><b>كرات جديدة تفتح أمامك:</b> نلعب بعلبة كرات جديدة مضغوطة تُفتح أمام الجميع في بداية التمرين لضمان سرعة الارتداد ودقة الضربات.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">🧊</span>
            <div><b>الضيافة والترطيب:</b> كرتون مياه باردة متاح بجانب الملعب طوال فترة التمرين.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab_rules:
    st.markdown("""
    <div class="info-card">
        <div class="info-row">
            <span style="font-size:1.3em;">⏱️</span>
            <div><b>قبل 4 ساعات من التمرين:</b> استرجاع كامل للمبلغ أو ترحيله تلقائياً لتمرينك القادم دون أي خصم.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">⚠️</span>
            <div><b>أقل من 4 ساعات:</b> يُسترجع المبلغ فوراً بمجرد تأكيد وتسكين لاعب بديل من قائمة الاحتياط.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">⏳</span>
            <div><b>مهلة الـ 15 دقيقة (Anti-Ghost):</b> إرسال إشعار التحويل مطلوب خلال 15 دقيقة من الحجز؛ بعدها يُتاح المقعد للاعب التالي في القائمة تلقائياً.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input(t["cancel_phone"])
        can_reason = st.selectbox(t["cancel_reason"], t["reasons"])
        btn_cancel_sub = st.form_submit_button(t["btn_cancel"])

        if btn_cancel_sub:
            clean_cp = clean_and_validate_sa_phone(can_phone_raw)
            if not clean_cp:
                st.error(t["err_fields"])
            else:
                try:
                    res_target = supabase.table("bookings").select("*").eq("player_phone", clean_cp).eq("session_date", session_date_obj.isoformat()).in_("status", ["confirmed", "waitlist"]).execute()
                    target_rows = res_target.data if res_target.data else []

                    if target_rows:
                        target = target_rows[0]
                        # تحديث حالة الإلغاء وحفظ السبب داخل نفس الجدول
                        supabase.table("bookings").update({
                            "status": "cancelled",
                            "cancellation_reason": can_reason,
                            "cancelled_at": datetime.now(timezone.utc).isoformat()
                        }).eq("id", target["id"]).execute()

                        # تصعيد اللاعب الأول من الاحتياط إن كان الملغي مؤكداً
                        if target["status"] == 'confirmed':
                            res_wait_first = supabase.table("bookings").select("*").eq("session_date", session_date_obj.isoformat()).eq("status", "waitlist").order("id").limit(1).execute()
                            wait_players = res_wait_first.data if res_wait_first.data else []
                            if wait_players:
                                wp = wait_players[0]
                                supabase.table("bookings").update({"status": "confirmed", "court_number": 1}).eq("id", wp["id"]).execute()
                        
                        st.success(t["succ_cancel"].format(html.escape(target["player_name"])))
                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error(t["err_cancel"])
                except Exception as e:
                    st.error(f"خطأ أثناء معالجة الإلغاء: {e}")

# ==========================================
# 6. التشكيلة المباشرة (Social Proof)
# ==========================================
st.markdown("---")

def get_level_badge(lvl):
    if lvl == "متقدم":
        return "🔥 متقدم"
    elif lvl == "مبتدئ":
        return "⚪ مبتدئ"
    return "🟢 متوسط"

def render_single_court_roster(title, players):
    slots_html = ""
    for i in range(COURT_CAPACITY):
        if i < len(players):
            p = players[i]
            p_name = html.escape(p.get("player_name", ""))
            p_level = html.escape(p.get("player_level", "متوسط"))
            pay_status = p.get("payment_status", "pending")
            status_text = "مؤكد ✅" if pay_status == "paid" else "بانتظار السداد ⏳"
            lvl_badge = get_level_badge(p_level)
            
            slots_html += f'''<div class="slot-box">
                <div class="slot-occupied">🎾 {p_name}</div>
                <div class="slot-meta">
                    <span class="badge-level">{lvl_badge}</span>
                    <span class="badge-status">{status_text}</span>
                </div>
            </div>'''
        else:
            slots_html += f'<div class="slot-box"><div class="slot-empty">مقعد شاغر ✨</div></div>'
            
    return f'<div class="padel-court"><div class="court-title">{title} ({len(players)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>'

st.markdown(render_single_court_roster(t["court1"], c1), unsafe_allow_html=True)

if waitlist:
    safe_waitlist = [f"{idx+1}. {html.escape(w.get('player_name', ''))}" for idx, w in enumerate(waitlist)]
    st.caption("📋 **أولوية الاحتياط:** " + " • ".join(safe_waitlist))

# ==========================================
# 7. لوحة الإدارة وتصدير البيانات
# ==========================================
with st.expander("⚙️ لوحة الإدارة والبيانات", expanded=False):
    pin_input = st.text_input(t["admin_pin"], type="password")
    
    if verify_admin_security(pin_input):
        st.success("تم تأكيد الصلاحيات 👑")
        
        try:
            res_canc = supabase.table("bookings").select("cancellation_reason").eq("status", "cancelled").execute()
            canc_data = res_canc.data if res_canc.data else []
            reason_counts = {}
            for item in canc_data:
                r = item.get("cancellation_reason") or "غير محدد"
                reason_counts[r] = reason_counts.get(r, 0) + 1
            
            if reason_counts:
                st.markdown("#### 📊 أسباب الاعتذار الميدانية:")
                for r, cnt in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
                    st.caption(f"• **{html.escape(r)}:** {cnt} لاعبين")
        except Exception:
            pass

        try:
            res_all = supabase.table("bookings").select("*").order("session_date", desc=True).order("id", desc=False).execute()
            raw_data = res_all.data if res_all.data else []

            if raw_data:
                csv_buf = io.StringIO()
                csv_buf.write('\ufeff')
                writer = csv.writer(csv_buf)
                writer.writerow(["تاريخ التمرين", "رقم الكورت", "اسم اللاعب", "رقم الجوال", "المستوى", "الحالة", "حالة الدفع", "سبب الإلغاء", "وقت التسجيل"])
                for row in raw_data:
                    writer.writerow([
                        row.get("session_date"),
                        row.get("court_number"),
                        row.get("player_name"),
                        row.get("player_phone"),
                        row.get("player_level"),
                        row.get("status"),
                        row.get("payment_status"),
                        row.get("cancellation_reason"),
                        row.get("created_at")
                    ])
                    
                st.download_button(
                    t["export_btn"],
                    csv_buf.getvalue().encode('utf-8-sig'),
                    f"padel99_master_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        except Exception as e:
            st.error(f"خطأ في لوحة الإدارة: {e}")
LANG = {
    "ar": {
        "dir": "rtl",
        "align": "right",
        "brand": "Padel 99.",
        "hero_sub": "تمرين {}. متعة اللعب بأعلى معايير التنظيم.",
        "contrast_banner": "⚡ كرات جديدة كلياً • ماء مبرد • تدوير عادل 15 دقيقة",
        "promo_badge": "✨ العب 6 تمارين والسابع مجاناً بالكامل",
        "price_tag": "65 ر.س",
        "time_str": "⏰ ٩:٣٠ م – ١١:٠٠ م | كورت 1 (6 مقاعد)",
        "court1": "🏟️ كورت 1",
        "tab_book": "⚡ حجز مقعد",
        "tab_system": "📋 خطة التمرين والتدوير",
        "tab_rules": "📜 القواعد والاسترجاع",
        "tab_cancel": "❌ اعتذار",
        "name_lbl": "الاسم الثلاثي أو المستعار",
        "phone_lbl": "رقم الجوال (05xxxxxxxx)",
        "level_lbl": "مستوى اللعب",
        "levels": [
            "🟢 متوسط • تبادل مستمر وثبات تكتيكي",
            "🔥 متقدم • سرعة وقوة ودقة",
            "⚪ مبتدئ • بداية التعلّم والضربات الأساسية"
        ],
        "btn_book": "تأكيد المقعد والانتقال للسداد 🚀",
        "err_fields": "يرجى إدخال اسم صحيح ورقم جوال يبدأ بـ 05 ويتكون من 10 أرقام.",
        "err_duplicate": "أنت مسجل بالفعل في تمرين اليوم.",
        "err_spam": "تم حظر العملية لاشتباه بنشاط آلي.",
        "succ_book_title": "✅ تم تثبيت المقعد المبدئي يا كابتن {}!",
        "succ_book_desc": "مقعدك في <b>{}</b> متاح مؤقتاً. يرجى إتمام التحويل لتأكيد القائمة النهائية.",
        "succ_wait": "اكتملت المقاعد الأساسية. تم تسجيلك في المرتبة #{} في قائمة الاحتياط.",
        "cancel_phone": "رقم الجوال المسجل:",
        "cancel_reason": "سبب الاعتذار:",
        "reasons": [
            "تعارض مفاجئ في المواعيد",
            "إجهاد بدني أو إصابة رياضية",
            "ظرف شخصي طارئ",
            "صعوبة في المواصلات"
        ],
        "btn_cancel": "إلغاء المقعد وإتاحته للبديل",
        "succ_cancel": "تم قبول اعتذارك يا كابتن {}. نراك في التمرين القادم.",
        "err_cancel": "لا يوجد حجز مسجل مرتبط بهذا الرقم اليوم.",
        "admin_pin": "رمز الإدارة السري المشفر:",
        "export_btn": "📥 تصدير السجل (Excel/CSV)",
        "timer_prefix": "⏳ متبقي على إغلاق الحجز:",
        "timer_closed": "🔒 أُغلق حجز هذا التمرين تلقائياً"
    },
    "en": {
        "dir": "ltr",
        "align": "left",
        "brand": "Padel 99.",
        "hero_sub": "{} Session. Pure padel, zero hassle.",
        "contrast_banner": "⚡ Fresh Balls • Chilled Water • 15m Fair Rotation",
        "promo_badge": "✨ Play 6 sessions, get the 7th on us.",
        "price_tag": "65 SAR",
        "time_str": "⏰ 9:30 PM – 11:00 PM | Court 1 (6 Slots)",
        "court1": "🏟️ Court 1",
        "tab_book": "⚡ Reserve Spot",
        "tab_system": "📋 Rotation System",
        "tab_rules": "📜 Rules & Policy",
        "tab_cancel": "❌ Cancel",
        "name_lbl": "Player Name",
        "phone_lbl": "Mobile (05xxxxxxxx)",
        "level_lbl": "Skill Level",
        "levels": [
            "🟢 Intermediate • Steady rallies",
            "🔥 Advanced • High pace & tactical",
            "⚪ Beginner • Fundamentals & fun"
        ],
        "btn_book": "Reserve & Proceed to Payment 🚀",
        "err_fields": "Enter a valid name and a 10-digit Saudi phone starting with 05.",
        "err_duplicate": "You have an active booking for today.",
        "err_spam": "Rejected due to automated activity.",
        "succ_book_title": "✅ Spot Reserved for Captain {}!",
        "succ_book_desc": "Your slot for <b>{}</b> is temporarily held. Transfer to lock it in.",
        "succ_wait": "Main roster is full. You are #{} on the waitlist.",
        "cancel_phone": "Registered Mobile:",
        "cancel_reason": "Cancellation Reason:",
        "reasons": [
            "Schedule conflict",
            "Physical fatigue or injury",
            "Personal emergency",
            "Transportation issue"
        ],
        "btn_cancel": "Release Spot to Waitlist",
        "succ_cancel": "Reservation cancelled for {}. See you next time.",
        "err_cancel": "No active booking found for this number today.",
        "admin_pin": "Manager Master PIN:",
        "export_btn": "📥 Export Timesheet (Excel/CSV)",
        "timer_prefix": "⏳ Registration Closes In:",
        "timer_closed": "🔒 Session Closed"
    }
}

col_lang1, col_lang2 = st.columns([5, 1])
with col_lang2:
    curr_lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")
l_code = "ar" if curr_lang == "العربية" else "en"
t = LANG[l_code]

# ==========================================
# 3. أنماط CSS المتقدمة (Apple Dark Modern)
# ==========================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
* {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Cairo', sans-serif; direction: {t['dir']}; text-align: {t['align']}; }}
.block-container {{ padding: 0.8rem 0.5rem 1.2rem 0.5rem !important; max-width: 580px !important; }}
.stAppHeader {{ display: none; }}

.hero-header {{ font-size: 1.7em; font-weight: 900; letter-spacing: -0.5px; color: #f4f4f5; margin: 0; }}
.hero-sub {{ font-size: 0.88em; color: #a1a1aa; margin-bottom: 6px; }}
.contrast-pill {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 5px 8px; font-size: 0.75em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }}
.promo-badge {{ background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.75em; margin-bottom: 6px; }}

.countdown-box {{
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.25);
    border-radius: 8px;
    padding: 8px 12px;
    margin: 6px 0 10px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.82em;
    color: #fbbf24;
}}

.thankyou-box {{
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 78, 59, 0.25) 100%);
    border: 1.5px solid #10b981;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 10px 0;
    text-align: center;
}}
.thankyou-title {{ color: #34d399; font-size: 1.05em; font-weight: 800; margin-bottom: 4px; }}
.thankyou-sub {{ color: #e2e8f0; font-size: 0.84em; }}

.info-card {{
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 14px;
    padding: 14px;
    margin: 8px 0;
}}
.info-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 0.82em;
    color: #e2e8f0;
    line-height: 1.4;
}}
.info-row:last-child {{ margin-bottom: 0; }}

.alrajhi-card {{
    background: #111418;
    border: 1.5px solid #2d3748;
    border-radius: 18px;
    padding: 16px;
    margin: 12px 0;
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    color: #ffffff;
}}
.card-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 8px;
    margin-bottom: 12px;
}}
.price-pill {{ background: #10b981; color: #022c22; padding: 3px 10px; border-radius: 20px; font-weight: 900; font-size: 0.85em; }}
.qr-container {{ background: #ffffff; padding: 10px; border-radius: 12px; display: inline-block; margin: 4px auto 10px auto; }}
.qr-container img {{ display: block; width: 130px; height: 130px; }}
.card-owner {{ font-size: 1.1em; font-weight: 800; color: #f8fafc; margin-bottom: 10px; text-align: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.12); padding-bottom: 8px; }}
.copy-badge {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 10px;
    font-family: monospace;
    font-size: 0.90em;
    color: #38bdf8;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 8px;
}}

.wa-action-btn {{
    display: block;
    width: 100%;
    background: linear-gradient(180deg, #25D366 0%, #1da851 100%);
    color: white !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 800;
    text-decoration: none;
    margin-top: 8px;
    font-size: 0.92em;
    box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
}}

.wa-community-btn {{
    display: block;
    width: 100%;
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid #3b82f6;
    color: #93c5fd !important;
    text-align: center;
    padding: 10px;
    border-radius: 10px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 8px;
    font-size: 0.85em;
}}

.padel-court {{ background: radial-gradient(circle, #064e3b 0%, #022c22 100%); border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 12px; padding: 12px; margin-bottom: 6px; }}
.court-title {{ text-align: center; color: #a7f3d0; font-weight: 800; font-size: 0.95em; margin-bottom: 10px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 6px; }}
.court-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.slot-box {{ background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 8px 6px; text-align: center; min-height: 52px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
.slot-occupied {{ color: #f4f4f5; font-weight: 700; font-size: 0.84em; line-height: 1.2; word-break: break-word; }}
.slot-meta {{ display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.70em; margin-top: 4px; flex-wrap: wrap; }}
.slot-empty {{ color: #52525b; font-size: 0.78em; }}
.badge-loyalty {{ background-color: #1e3a8a; color: #93c5fd; padding: 1px 4px; border-radius: 3px; font-size: 0.72em; font-weight: 700; }}
.badge-level {{ background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 4px; border-radius: 3px; font-size: 0.70em; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.15); }}

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. محرك التوقيت والتحقق
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
    if not supabase:
        return False
    res = supabase.table("bookings").select("id").eq("phone", phone).eq("session_day", session_key).in_("status", ["confirmed", "waitlist"]).execute()
    return len(res.data) > 0

def get_loyalty_score(norm_phone):
    if not supabase:
        return 0
    res = supabase.table("bookings").select("session_day").eq("phone", norm_phone).eq("status", "confirmed").execute()
    if not res.data:
        return 0
    unique_sessions = set(item["session_day"] for item in res.data)
    return len(unique_sessions)

def verify_admin_security(input_pin):
    now = time.time()
    if "admin_attempts" not in st.session_state:
        st.session_state["admin_attempts"] = 0
    if "admin_lockout_until" not in st.session_state:
        st.session_state["admin_lockout_until"] = 0
        
    if now < st.session_state["admin_lockout_until"]:
        rem = int(st.session_state["admin_lockout_until"] - now)
        st.error(f"🔒 لوحة الإدارة مقفلة مؤقتاً لحمايتها. انتظر: {rem // 60}:{rem % 60:02d} دقيقة.")
        return False

    if not input_pin:
        return False

    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    p = str(input_pin).translate(ar_digits).strip()
    
    master_secret = st.secrets.get("ADMIN_PASSWORD", None) or st.secrets.get("ADMIN_PIN", "Padel99#Master@2026")
    target_secret = str(master_secret).translate(ar_digits).strip()

    if hmac.compare_digest(p, target_secret):
        st.session_state["admin_attempts"] = 0
        return True
    else:
        st.session_state["admin_attempts"] += 1
        if st.session_state["admin_attempts"] >= 3:
            st.session_state["admin_lockout_until"] = now + 600
            st.error("🚨 تم حظر المحاولات لمدة 10 دقائق بعد 3 محاولات غير صحيحة.")
        else:
            left = 3 - st.session_state["admin_attempts"]
            st.error(f"رمز غير صحيح. المتبقي: {left} محاولات.")
        return False

def get_next_session(cutoff_minutes_before: int = 60):
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    SESSION_DAYS = {
        6: ("الأحد", "Sunday"),
        1: ("الثلاثاء", "Tuesday"),
        3: ("الخميس", "Thursday")
    }
    
    start_hour, start_min = 21, 30
    total_cutoff_min = (start_hour * 60 + start_min) - cutoff_minutes_before
    cutoff_time = dtime(total_cutoff_min // 60, total_cutoff_min % 60)

    today_weekday = now.weekday()
    is_session_today = today_weekday in SESSION_DAYS
    is_before_cutoff = now.time() < cutoff_time

    if is_session_today and is_before_cutoff:
        days_to_add = 0
    else:
        days_to_add = 1
        while (today_weekday + days_to_add) % 7 not in SESSION_DAYS:
            days_to_add += 1

    target_date = now + timedelta(days=days_to_add)
    target_weekday = target_date.weekday()
    d_ar, d_en = SESSION_DAYS[target_weekday]
    
    date_str = target_date.strftime("%d/%m")
    label_ar = f"{d_ar} ({date_str})"
    label_en = f"{d_en} ({date_str})"
    db_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"
    
    cutoff_dt = target_date.replace(
        hour=cutoff_time.hour, minute=cutoff_time.minute, second=0, microsecond=0
    )
    
    return label_ar, label_en, db_key, cutoff_dt

def render_session_countdown(cutoff_dt: datetime, lang_dict: dict):
    cutoff_iso = cutoff_dt.isoformat()
    txt_prefix = lang_dict["timer_prefix"]
    txt_closed = lang_dict["timer_closed"]
    
    countdown_html = f"""
    <div id="countdown-card" class="countdown-box">
        <span style="font-weight: 600;">{txt_prefix}</span>
        <span id="timer-display" style="font-family: ui-monospace, SFMono-Regular, monospace; font-weight: 800; letter-spacing: 0.5px; color: #fef3c7;">--:--:--</span>
    </div>

    <script>
    (function() {{
        const targetDate = new Date("{cutoff_iso}").getTime();
        
        function updateTimer() {{
            const now = new Date().getTime();
            const diff = targetDate - now;
            const timerElem = document.getElementById("timer-display");
            const cardElem = document.getElementById("countdown-card");

            if (!timerElem || !cardElem) return;

            if (diff <= 0) {{
                cardElem.style.background = "rgba(239, 68, 68, 0.08)";
                cardElem.style.borderColor = "rgba(239, 68, 68, 0.25)";
                cardElem.style.color = "#f87171";
                cardElem.innerHTML = "<span>{txt_closed}</span>";
                clearInterval(interval);
                return;
            }}

            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            const pad = (n) => n < 10 ? '0' + n : n;
            timerElem.innerText = pad(hours) + "h " + pad(minutes) + "m " + pad(seconds) + "s";
        }}

        updateTimer();
        const interval = setInterval(updateTimer, 1000);
    }})();
    </script>
    """
    st.markdown(countdown_html, unsafe_allow_html=True)

# استدعاء الجلسة الحالية
sess_ar, sess_en, db_session_key, session_cutoff_dt = get_next_session()
display_session = sess_ar if l_code == "ar" else sess_en
COURT_CAPACITY = 6

# جلب البيانات الحالية من Supabase
c1 = []
waitlist = []
if supabase:
    try:
        res_c1 = supabase.table("bookings").select("*").eq("session_day", db_session_key).eq("court", 1).eq("status", "confirmed").order("id").limit(6).execute()
        c1 = res_c1.data if res_c1.data else []

        res_wait = supabase.table("bookings").select("*").eq("session_day", db_session_key).eq("status", "waitlist").order("id").execute()
        waitlist = res_wait.data if res_wait.data else []
    except Exception as e:
        st.warning("جاري مزامنة السجلات السحابية...")

total_booked = len(c1)
remaining_slots = max(0, COURT_CAPACITY - total_booked)

# ==========================================
# 5. واجهة العرض والتسجيل
# ==========================================
st.markdown(f"<div class='hero-header'>{t['brand']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>{t['hero_sub'].format(display_session)}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='contrast-pill'>{t['contrast_banner']}</div>", unsafe_allow_html=True)
st.markdown(f'<div class="promo-badge">{t["promo_badge"]}</div>', unsafe_allow_html=True)

if remaining_slots > 0:
    st.caption(f"{t['time_str']} • <b style='color:#34d399;'>متبقي {remaining_slots} مقاعد فقط! 🔥</b>", unsafe_allow_html=True)
else:
    st.caption(f"{t['time_str']} • <b style='color:#f87171;'>اكتملت المقاعد الأساسية (قائمة الاحتياط مفتوحة)</b>", unsafe_allow_html=True)

render_session_countdown(session_cutoff_dt, t)

tab_book, tab_system, tab_rules, tab_cancel = st.tabs([t["tab_book"], t["tab_system"], t["tab_rules"], t["tab_cancel"]])

with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([3, 2])
        with c_in1:
            f_name = st.text_input(t["name_lbl"])
        with c_in2:
            f_phone = st.text_input(t["phone_lbl"], placeholder="05xxxxxxxx")
        
        f_level_raw = st.selectbox(t["level_lbl"], t["levels"])
        f_level = "متوسط" if ("متوسط" in f_level_raw or "Intermediate" in f_level_raw) else ("متقدم" if ("متقدم" in f_level_raw or "Advanced" in f_level_raw) else "مبتدئ")
        
        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button(t["btn_book"])

        if btn_submit:
            if honeypot_val:
                st.error(t["err_spam"])
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 2 or not clean_phone:
                st.error(t["err_fields"])
            elif check_active_booking(clean_phone, db_session_key):
                st.warning(t["err_duplicate"])
            else:
                try:
                    res_count = supabase.table("bookings").select("id", count="exact").eq("session_day", db_session_key).eq("court", 1).eq("status", "confirmed").execute()
                    cur_c1 = len(res_count.data) if res_count.data else 0

                    status_val = 'confirmed' if cur_c1 < COURT_CAPACITY else 'waitlist'

                    supabase.table("bookings").insert({
                        "name": clean_name,
                        "phone": clean_phone,
                        "session_day": db_session_key,
                        "court": 1,
                        "level": f_level,
                        "status": status_val,
                        "payment_status": "pending",
                        "attendance": "unknown"
                    }).execute()

                    wait_pos = None
                    if status_val == 'waitlist':
                        res_wait_count = supabase.table("bookings").select("id", count="exact").eq("session_day", db_session_key).eq("status", "waitlist").execute()
                        wait_pos = len(res_wait_count.data) if res_wait_count.data else 1

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
                except Exception as e:
                    st.error(f"حدث خطأ أثناء حفظ الحجز: {e}")

    # صندوق السداد الفوري والتأكيد
    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        escaped_user_name = html.escape(lb["name"])
        
        if lb["status"] == "confirmed":
            if lb.get("is_new", False):
                st.balloons()
                lb["is_new"] = False

            thank_html = f"""
            <div class="thankyou-box">
                <div class="thankyou-title">{t["succ_book_title"].format(escaped_user_name)}</div>
                <div class="thankyou-sub">{t["succ_book_desc"].format(lb["session"])}</div>
            </div>
            """
            st.markdown(thank_html, unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={iban_raw}&color=000000&bgcolor=ffffff"

            card_html = f"""
<div class="alrajhi-card">
    <div class="card-top">
        <div style="font-weight:800; font-size:0.95em;">🏛️ مصرف الراجحي</div>
        <div class="price-pill">65 ر.س</div>
    </div>
    <div style="text-align:center;">
        <div class="qr-container">
            <img src="{qr_url}" alt="Al Rajhi QR" />
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
    <div style="margin-top: 8px; padding: 8px 10px; background: rgba(56, 189, 248, 0.08); border-radius: 8px; border: 1px dashed rgba(56, 189, 248, 0.3); display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 0.74em; color: #cbd5e1;">💡 <b>لحفظ المستفيد في تطبيق بنكك:</b></div>
        <div class="copy-badge" style="margin-bottom:0; padding:4px 8px; font-size:0.82em;" onclick="navigator.clipboard.writeText('بادل 99'); alert('تم نسخ اسم المستفيد: بادل 99 📋');">
            <span>بادل 99</span>
            <span>📋</span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:0.72em; color:#64748b; margin-top:8px;">
        <span>سويفت: <b>RJHISARI</b></span>
        <span>⚡ تحويل فوري</span>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            wa_msg = f"🎾 تأكيد حجز ومقعد | بادل 99\n\nالكابتن: {lb['name']}\nالتمرين: {lb['session']} (كورت 1)\nالمبلغ: 65 ر.س\n\nمرفق إشعار التحويل البنكي لحساب كابتن فارس العصيمي. نلتقي في الملعب."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-action-btn">📲 إرسال إشعار التحويل وتثبيت المقعد نهائياً (خلال 15 دقيقة)</a>', unsafe_allow_html=True)
            
            # حلقة المجتمع المستدام (Community Loop)
            wa_group_url = "https://chat.whatsapp.com/YOUR_GROUP_LINK"
            st.markdown(f'<a href="{wa_group_url}" target="_blank" class="wa-community-btn">👥 انضم إلى مجتمع بادل 99 السري (أولوية الحجز والتحديات)</a>', unsafe_allow_html=True)
        else:
            st.info(t["succ_wait"].format(lb.get("wait_pos", 1)))

# قسم خطة التمرين ونظام التدوير (Americano System)
with tab_system:
    st.markdown("""
    <div class="info-card">
        <div class="info-row">
            <span style="font-size:1.3em;">🔄</span>
            <div><b>نظام التدوير (Rotation):</b> 6 لاعبين على الملعب؛ 4 يلعبون شوطين (أو 15 دقيقة) و2 يستريحون، مما يضمن أن يلعب الجميع مع وضد بعضهم بعدالة تامة.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">🎾</span>
            <div><b>كرات جديدة تفتح أمامكم:</b> نضمن علبة كرات جديدة مضغوطة بالكامل لكل تمرين لضمان سرعة اللعب ونقاء التبادلات.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">🧊</span>
            <div><b>الضيافة والترطيب:</b> مياه باردة متوفرة بجانب الملعب طوال فترة التمرين.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab_rules:
    st.markdown("""
    <div class="info-card">
        <div class="info-row">
            <span style="font-size:1.3em;">⏱️</span>
            <div><b>قبل 4 ساعات من التمرين:</b> استرجاع كامل للمبلغ أو ترحيله تلقائياً لتمرينك القادم دون أي خصم.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">⚠️</span>
            <div><b>أقل من 4 ساعات:</b> يُسترجع المبلغ فوراً بمجرد تأكيد حجز لاعب بديل من قائمة الاحتياط.</div>
        </div>
        <div class="info-row">
            <span style="font-size:1.3em;">⏳</span>
            <div><b>مهلة الـ 15 دقيقة:</b> يرجى إرسال إشعار التحويل عبر الواتساب لتفادي إتاحة المقعد للاحتياط.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab_cancel:
    with st.form("cancel_form"):
        can_phone_raw = st.text_input(t["cancel_phone"])
        can_reason = st.selectbox(t["cancel_reason"], t["reasons"])
        btn_cancel_sub = st.form_submit_button(t["btn_cancel"])

        if btn_cancel_sub:
            clean_cp = clean_and_validate_sa_phone(can_phone_raw)
            if not clean_cp:
                st.error(t["err_fields"])
            else:
                try:
                    res_target = supabase.table("bookings").select("*").eq("phone", clean_cp).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                    target_rows = res_target.data if res_target.data else []

                    if target_rows:
                        target = target_rows[0]
                        supabase.table("bookings").update({"status": "cancelled"}).eq("id", target["id"]).execute()

                        supabase.table("cancellations").insert({
                            "player_name": target["name"],
                            "player_phone": clean_cp,
                            "session_day": db_session_key,
                            "court": target["court"],
                            "reason": can_reason
                        }).execute()

                        if target["status"] == 'confirmed':
                            res_wait_first = supabase.table("bookings").select("*").eq("session_day", db_session_key).eq("status", "waitlist").order("id").limit(1).execute()
                            wait_players = res_wait_first.data if res_wait_first.data else []
                            if wait_players:
                                wp = wait_players[0]
                                supabase.table("bookings").update({"status": "confirmed", "court": 1}).eq("id", wp["id"]).execute()
                        
                        st.success(t["succ_cancel"].format(html.escape(target["name"])))
                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error(t["err_cancel"])
                except Exception as e:
                    st.error(f"خطأ أثناء معالجة الإلغاء: {e}")

# ==========================================
# 6. تشكيلة الملعب المباشرة (Social Proof)
# ==========================================
st.markdown("---")

def get_level_badge(lvl):
    if lvl == "متقدم":
        return "🔥 متقدم"
    elif lvl == "مبتدئ":
        return "⚪ مبتدئ"
    return "🟢 متوسط"

def render_single_court_roster(title, players):
    slots_html = ""
    for i in range(COURT_CAPACITY):
        if i < len(players):
            p = players[i]
            p_name = html.escape(p.get("name", ""))
            p_level = html.escape(p.get("level", "متوسط"))
            p_phone = p.get("phone", "")
            
            loyalty_count = get_loyalty_score(p_phone)
            points = loyalty_count % 7
            pts_badge = f"⭐ {points}/6" if points < 6 else "🎁 مجاني!"
            pay_icon = "✅" if p.get("payment_status") == "paid" else "⏳"
            lvl_badge = get_level_badge(p_level)
            
            slots_html += f'''<div class="slot-box">
                <div class="slot-occupied">🎾 {p_name}</div>
                <div class="slot-meta">
                    <span class="badge-level">{lvl_badge}</span>
                    <span class="badge-loyalty">{pts_badge}</span>
                    <span>{pay_icon}</span>
                </div>
            </div>'''
        else:
            slots_html += f'<div class="slot-box"><div class="slot-empty">مقعد شاغر ✨</div></div>'
            
    return f'<div class="padel-court"><div class="court-title">{title} ({len(players)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>'

st.markdown(render_single_court_roster(t["court1"], c1), unsafe_allow_html=True)

if waitlist:
    safe_waitlist = [f"{idx+1}. {html.escape(w.get('name', ''))}" for idx, w in enumerate(waitlist)]
    st.caption("📋 **أولوية الاحتياط:** " + " • ".join(safe_waitlist))

# ==========================================
# 7. لوحة الإدارة وتصدير البيانات
# ==========================================
with st.expander("⚙️ لوحة الإدارة والبيانات", expanded=False):
    pin_input = st.text_input(t["admin_pin"], type="password")
    
    if verify_admin_security(pin_input):
        st.success("تم التحقق بنجاح 👑")
        
        try:
            res_canc = supabase.table("cancellations").select("reason").execute()
            canc_data = res_canc.data if res_canc.data else []
            reason_counts = {}
            for item in canc_data:
                r = item.get("reason", "أخرى")
                reason_counts[r] = reason_counts.get(r, 0) + 1
            
            if reason_counts:
                st.markdown("#### 📊 أسباب الاعتذار:")
                for r, cnt in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
                    st.caption(f"• **{html.escape(r)}:** {cnt} لاعبين")
        except Exception:
            pass

        try:
            res_all = supabase.table("bookings").select("*").order("session_day", desc=True).order("id", desc=False).execute()
            raw_data = res_all.data if res_all.data else []

            if raw_data:
                csv_buf = io.StringIO()
                csv_buf.write('\ufeff')
                writer = csv.writer(csv_buf)
                writer.writerow(["تاريخ التمرين", "الملعب", "اسم اللاعب", "رقم الجوال", "المستوى", "حالة الدفع", "الحضور الفعلي", "وقت التسجيل"])
                for row in raw_data:
                    writer.writerow([
                        row.get("session_day"),
                        row.get("court"),
                        row.get("name"),
                        row.get("phone"),
                        row.get("level"),
                        row.get("payment_status"),
                        row.get("attendance"),
                        row.get("created_at")
                    ])
                    
                st.download_button(
                    t["export_btn"],
                    csv_buf.getvalue().encode('utf-8-sig'),
                    f"padel_data_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        except Exception as e:
            st.error(f"خطأ في لوحة الإدارة: {e}")
