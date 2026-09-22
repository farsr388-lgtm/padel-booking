import streamlit as st
from supabase import create_client, Client
import re
import html
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة والتصميم الموجه للموبايل (Mobile-First CSS)
# ==============================================================================
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
    padding-top: 1rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 430px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
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

.price-tag-hero {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid #3b82f6;
    border-radius: 8px;
    padding: 6px 14px;
    margin-top: 10px;
    display: inline-block;
    font-size: 0.9em;
    color: #e2e8f0;
}
.old-price { text-decoration: line-through; color: #94a3b8; margin-left: 6px; }
.new-price { color: #22c55e; font-weight: 800; font-size: 1.15em; }

/* مؤشر المقاعد الحية */
.seats-tracker {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin: 12px 0 6px 0;
}
.seat-dot { width: 14px; height: 14px; border-radius: 50%; }
.dot-booked { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.6); }
.dot-free { background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6); }

.roster-box {
    background: rgba(15, 23, 42, 0.6);
    border: 1px dashed #334155;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 12px;
    font-size: 0.85em;
    color: #cbd5e1;
    line-height: 1.6;
}

/* بطاقة الدفع والعداد */
.pay-box {
    background: #0f172a;
    border: 1.5px solid #38bdf8;
    border-radius: 16px;
    padding: 18px 14px;
    text-align: center;
    margin-top: 8px;
}
.timer-container {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    border-radius: 10px;
    padding: 9px;
    margin: 12px 0;
    color: #fca5a5;
    font-size: 0.88em;
    font-weight: 700;
}
.timer-digits {
    font-family: monospace;
    font-size: 1.3em;
    color: #f87171;
    letter-spacing: 1px;
}

.iban-copy-card {
    background: #1e293b;
    border: 1.5px dashed #38bdf8;
    border-radius: 10px;
    padding: 12px;
    margin: 12px 0;
    cursor: pointer;
    user-select: none;
}
.iban-number {
    font-family: monospace;
    font-size: 1.05em;
    color: #ffffff;
    font-weight: 800;
    direction: ltr;
    display: inline-block;
}

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

/* إخفاء حقل الحماية من البوتات */
div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. الثوابت وإعداد اتصال قاعدة البيانات
# ==============================================================================
COURT_CAPACITY = 6
PRICE_PER_SEAT = 69
IBAN_CLEAN = "SA9380000222608016013114"
IBAN_DISPLAY = "SA93 8000 0222 6080 1601 3114"
ADMIN_PHONE = "966566261868"

@st.cache_resource
def get_supabase_client() -> Client:
    """إنشاء اتصال مفرد ومستقر بقاعدة البيانات."""
    return create_client(
        st.secrets["SUPABASE_URL"].strip().rstrip('/'),
        st.secrets["SUPABASE_KEY"].strip()
    )

try:
    supabase = get_supabase_client()
except Exception:
    st.error("تعذر الاتصال بالخادم. يرجى المحاولة لاحقاً.")
    st.stop()

# ==============================================================================
# 3. محرك الجدولة التلقائية للتمرين
# ==============================================================================
def resolve_next_session() -> tuple[str, str]:
    """تحديد أقرب موعد تمرين تلقائياً (أحد، ثلاثاء، خميس)."""
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    weekday_offsets = {
        0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"),
        2: (1, "الخميس"),   3: (0, "الخميس"),
        4: (2, "الأحد"),    5: (1, "الأحد"),
        6: (0, "الأحد")
    }
    
    days_to_add, day_name = weekday_offsets.get(now.weekday(), (0, "الأحد"))
    
    # إذا انتهى تمرين اليوم (بعد 10:30 م)، ينتقل تلقائياً للتمرين التالي
    if days_to_add == 0 and now.hour >= 22 and now.minute >= 30:
        next_dt = now + timedelta(days=1)
        days_to_add, day_name = weekday_offsets.get(next_dt.weekday(), (0, "الأحد"))
        days_to_add += 1
        
    target_date = now + timedelta(days=days_to_add)
    return f"{day_name} ({target_date.strftime('%d/%m')})", f"{day_name} {target_date.strftime('%Y-%m-%d')}"

display_session, db_session_key = resolve_next_session()

# ==============================================================================
# 4. محرك استرجاع المقاعد الذكي (Lazy Expiration / TTL Logic)
# ==============================================================================
def get_valid_active_bookings(session_key: str) -> list:
    """
    يسترجع الحجوزات الصالحة فقط:
    1. الحجوزات المؤكدة والمدفوعة.
    2. الحجوزات المعلقة التي لم تنتهِ مهلة الـ 15 دقيقة المحددة لها.
    (أي حجز معلق مرت عليه 15 دقيقة يتم تحرير مقعده تلقائياً أمام الجميع).
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    try:
        data = supabase.table("bookings") \
            .select("id, name, phone, level, status, payment_status, expires_at") \
            .eq("session_day", session_key) \
            .eq("status", "confirmed") \
            .order("id") \
            .execute().data or []
        
        valid_players = []
        for p in data:
            is_paid = p.get("payment_status") == "paid"
            # فحص سريان الـ 15 دقيقة للحجوزات المعلقة
            has_time_left = p.get("expires_at") and p["expires_at"] > now_utc_iso
            
            if is_paid or has_time_left:
                valid_players.append(p)
                
        return valid_players
    except Exception:
        return []

active_bookings = get_valid_active_bookings(db_session_key)
confirmed_players = active_bookings[:COURT_CAPACITY]
booked_count = len(confirmed_players)
seats_left = max(0, COURT_CAPACITY - booked_count)

# رسم مؤشر المقاعد
dots_html = "".join(['<div class="seat-dot dot-booked" title="محجوز"></div>' for _ in range(booked_count)])
dots_html += "".join(['<div class="seat-dot dot-free" title="متاح"></div>' for _ in range(seats_left)])

# ==============================================================================
# 5. عرض الواجهة العلوية
# ==============================================================================
st.markdown(f"""
<div class="hero-card">
    <div class="hero-title">🎾 بادل 99</div>
    <div class="hero-sub">تمرين {display_session} • 9:30 م إلى 11:00 م</div>
    <div class="price-tag-hero">
        سعر المقعد: <span class="old-price">89 ر.س</span> 👈 <span class="new-price">{PRICE_PER_SEAT} ر.س</span>
    </div>
    <div class="seats-tracker">{dots_html}</div>
    <div style="font-size:0.85em; color:#38bdf8; font-weight:700; margin-top:6px;">
        {'⚡ متبقي ' + str(seats_left) + ' مقاعد فقط' if seats_left > 0 else '⚠️ اكتملت المقاعد لهذا التمرين'}
    </div>
</div>
""", unsafe_allow_html=True)

if confirmed_players:
    sanitized_names = [f"<b>{html.escape(p['name'].split()[0])}</b> ({html.escape(p.get('level', 'متوسط'))})" for p in confirmed_players]
    st.markdown(f'<div class="roster-box">👥 <b>المحجوز لهم بالملعب:</b> {" • ".join(sanitized_names)}</div>', unsafe_allow_html=True)

# ==============================================================================
# 6. شاشة الحجز وشاشة الدفع مع العداد
# ==============================================================================
if "booked" in st.session_state:
    b = st.session_state["booked"]
    target_epoch_ms = b.get("expire_timestamp", 0)
    
    # عداد تنازلي متصل بالوقت الحقيقي عبر المتصفح
    timer_script = f"""
    <div class="timer-container" id="timer-box">
        ⏳ المقعد محجوز لك مؤقتاً: <span id="countdown" class="timer-digits">--:--</span>
    </div>
    <script>
    (function() {{
        var targetTime = {target_epoch_ms};
        function updateTimer() {{
            var now = new Date().getTime();
            var distance = targetTime - now;
            var countdownElem = document.getElementById('countdown');
            var timerBox = document.getElementById('timer-box');
            
            if (!countdownElem) return;

            if (distance <= 0) {{
                countdownElem.innerHTML = "00:00";
                if (timerBox) {{
                    timerBox.style.background = "rgba(239, 68, 68, 0.3)";
                    timerBox.innerHTML = "⚠️ انتهت مهلة الـ 15 دقيقة! يرجى إرسال الإيصال بالواتساب فوراً لضمان عدم إلغاء المقعد.";
                }}
                return;
            }}
            
            var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((distance % (1000 * 60)) / 1000);
            
            var minStr = (minutes < 10 ? "0" : "") + minutes;
            var secStr = (seconds < 10 ? "0" : "") + seconds;
            countdownElem.innerHTML = minStr + ":" + secStr;
        }}
        updateTimer();
        setInterval(updateTimer, 1000);
    }})();
    </script>
    """
    
    st.markdown(f"""
    <div class="pay-box">
        <h3 style="color:#22c55e; margin:0 0 4px 0;">✅ تم حجز مقعدك بنجاح!</h3>
        {timer_script}
        <div style="font-size:0.95em; color:#e2e8f0; margin:10px 0;">
            المبلغ المطلوب: <b style="color:#22c55e; font-size:1.25em;">{PRICE_PER_SEAT} ر.س</b>
        </div>
        
        <div class="iban-copy-card" onclick="
            navigator.clipboard.writeText('{IBAN_CLEAN}');
            var badge = document.getElementById('copy-status');
            badge.innerHTML = '✅ تم نسخ الآيبان بنجاح!';
            badge.style.color = '#34d399';
            setTimeout(function(){{
                badge.innerHTML = '📋 اضغط لنسخ رقم الآيبان';
                badge.style.color = '#38bdf8';
            }}, 2000);
        ">
            <div style="font-size:0.75em; color:#94a3b8; margin-bottom:3px;">مصرف الراجحي | فارس ربيع العصيمي</div>
            <div class="iban-number">{IBAN_DISPLAY}</div>
            <div id="copy-status" style="font-size:0.8em; color:#38bdf8; font-weight:700; margin-top:5px;">📋 اضغط لنسخ رقم الآيبان</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    wa_msg = (
        f"هلا كابتن فارس 🎾\n"
        f"أكدت حجزي في تمرين بادل 99 🤩\n\n"
        f"👤 الكابتن: {b['name']}\n"
        f"📅 تمرين: {display_session}\n"
        f"💵 المبلغ المحول: {PRICE_PER_SEAT} ر.س\n\n"
        f"مرفق إيصال التحويل، ونشوفكم في الملعب! 🔥"
    )
    wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال وتثبيت المقعد</a>', unsafe_allow_html=True)

elif seats_left == 0:
    st.info("⚠️ المقاعد مكتملة بالكامل لتمرين اليوم. تواصل عبر الواتساب للاستفسار عن أي شواغر طارئة.")
    wa_inq = f"مرحبا كابتن فارس، هل يوجد شاغر إضافي لتمرين {display_session}؟"
    wa_inq_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_inq)}"
    st.markdown(f'<a href="{wa_inq_url}" target="_blank" class="wa-btn" style="background:#0284c7;">💬 الاستفسار عن شواغر عبر واتساب</a>', unsafe_allow_html=True)

else:
    with st.form("quick_booking_form", clear_on_submit=True):
        f_name = st.text_input("الاسم الكريم", placeholder="اكتب اسمك")
        f_phone = st.text_input("رقم الجوال", placeholder="05xxxxxxxx")
        f_level = st.selectbox("المستوى في اللعب", ["متوسط", "متقدم", "مبتدئ"])
        
        # حقل صائد البوتات (Honeypot)
        hp = st.text_input("hp", label_visibility="collapsed")
        
        btn_submit = st.form_submit_button("تأكيد الحجز فوراً ⚡", use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:0.75em; color:#64748b; margin-top:-4px;'>🛡️ الحجز مؤكد مؤقتاً، وسيتم تثبيته فور استلام الإيصال.</div>", unsafe_allow_html=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            
            # توحيد صيغة رقم الجوال
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            # التحقق المنطقي من البيانات
            if len(clean_name) < 2:
                st.error("يرجى إدخال اسم صحيح.")
            elif not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل رقم جوال سعودي صحيح (مثال: 05xxxxxxxx).")
            else:
                try:
                    # فحص لحظي مباشر للمقاعد الصالحة لمنع التضارب (Atomic Race Condition Check)
                    current_active = get_valid_active_bookings(db_session_key)
                    
                    if any(item["phone"] == clean_phone for item in current_active):
                        st.warning("أنت مسجل بالفعل في هذا التمرين ومقعدك محجوز!")
                    elif len(current_active) >= COURT_CAPACITY:
                        st.error("عذراً، اكتملت المقاعد المتاحة للتو!")
                    else:
                        # احتساب وقت انتهاء الـ 15 دقيقة بدقة (UTC)
                        now_utc = datetime.now(timezone.utc)
                        expire_dt = now_utc + timedelta(minutes=15)
                        expire_iso = expire_dt.isoformat()
                        expire_ms = int(expire_dt.timestamp() * 1000)
                        
                        # إدراج الحجز في Supabase
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": db_session_key,
                            "court": 1,
                            "level": f_level,
                            "status": "confirmed",
                            "payment_status": "pending",
                            "expires_at": expire_iso,
                            "hear_about": "DIRECT",
                            "player_note": ""
                        }).execute()
                        
                        # حفظ الحالة لإظهار العداد التنازلي فوراً
                        st.session_state["booked"] = {
                            "name": clean_name,
                            "expire_timestamp": expire_ms
                        }
                        st.rerun()
                except Exception:
                    st.error("حدث خطأ أثناء معالجة الطلب، يرجى المحاولة ثانية.")
