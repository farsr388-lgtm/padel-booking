import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة وتنسيق الموبايل (CSS)
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

/* بطاقة الهيدر */
.hero-box {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 14px;
    text-align: center;
    margin-bottom: 8px;
}
.hero-title { font-size: 1.55em; font-weight: 900; color: #f8fafc; margin: 0; }
.hero-desc { color: #94a3b8; font-size: 0.82em; margin-top: 4px; }
.features-pill {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 0.78em;
    color: #38bdf8;
    margin: 6px 0;
    display: inline-block;
}

/* شبكة المقاعد الستة في الكورت */
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
    font-size: 0.8em;
    font-weight: 700;
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

/* بطاقة المؤشرات المالية للمنظم */
.metrics-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 8px;
}

/* أزرار الحجز */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
    color: #ffffff !important;
    font-size: 1.1em !important;
    font-weight: 800 !important;
    height: 50px !important;
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
    padding: 13px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 1em;
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
# 2. الثوابت الاقتصادية وإعداد اتصال قاعدة البيانات
# ==============================================================================
COURT_CAPACITY = 6          # سعة الملعب
FIXED_COURT_COST = 300      # تكلفة الملعب لساعتين
BREAK_EVEN_PLAYERS = 5      # نقطة التعادل
UNIT_PRICE = 65             # سعر المقعد
LOYALTY_LIABILITY = 9.29    # الالتزام المحاسبي للولاء (65 / 7)
IBAN_NUMBER = "SA9380000222608016013114"
ADMIN_PHONE = "966566261868"
ADMIN_PIN_HASH = "9900"     # رمز دخول لوحة المنظم

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"].strip().rstrip('/'),
        st.secrets["SUPABASE_KEY"].strip()
    )

try:
    supabase = get_supabase_client()
except Exception:
    st.error("تعذر الاتصال بقاعدة البيانات. يرجى التأكد من مفاتيح الربط في Secrets.")
    st.stop()

# ==============================================================================
# 3. محرك الجدولة الزمنية التلقائية
# ==============================================================================
def resolve_next_session() -> tuple[str, str, datetime]:
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    # جدول مواعيد التمارين (0: الإثنين, 1: الثلاثاء, 2: الأربعاء, 3: الخميس, 4: الجمعة, 5: السبت, 6: الأحد)
    weekday_offsets = {
        0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"),
        2: (1, "الخميس"),   3: (0, "الخميس"),
        4: (2, "الأحد"),    5: (1, "الأحد"),
        6: (0, "الأحد")
    }
    
    days_to_add, day_name = weekday_offsets.get(now.weekday(), (0, "الأحد"))
    
    # بعد الساعة 10:30 م في يوم التمرين ينتقل تلقائياً لليوم التالي
    if days_to_add == 0 and (now.hour > 22 or (now.hour == 22 and now.minute >= 30)):
        next_dt = now + timedelta(days=1)
        days_to_add, day_name = weekday_offsets.get(next_dt.weekday(), (0, "الأحد"))
        days_to_add += 1
        
    target_date = now + timedelta(days=days_to_add)
    session_start_dt = target_date.replace(hour=21, minute=30, second=0, microsecond=0)
    
    display_str = f"{day_name} ({target_date.strftime('%d/%m')})"
    db_key = f"{day_name} {target_date.strftime('%Y-%m-%d')}"
    
    return display_str, db_key, session_start_dt

display_session, db_session_key, session_start_time = resolve_next_session()

# ==============================================================================
# 4. محرك المقاعد الذكي (استخدام session_day الصريح)
# ==============================================================================
def get_active_session_bookings(session_key: str) -> list:
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    try:
        data = supabase.table("bookings") \
            .select("id, name, phone, level, status, payment_status, expires_at") \
            .eq("session_day", session_key) \
            .eq("status", "confirmed") \
            .order("id") \
            .execute().data or []
        
        valid = []
        for p in data:
            is_paid = p.get("payment_status") == "paid"
            has_time_left = p.get("expires_at") and p["expires_at"] > now_utc_iso
            if is_paid or has_time_left:
                valid.append(p)
        return valid
    except Exception:
        return []

active_bookings = get_active_session_bookings(db_session_key)
confirmed_players = active_bookings[:COURT_CAPACITY]
booked_count = len(confirmed_players)
seats_left = max(0, COURT_CAPACITY - booked_count)

# ==============================================================================
# 5. عرض الهيدر والعداد المباشر
# ==============================================================================
cutoff_epoch_ms = int(session_start_time.astimezone(timezone.utc).timestamp() * 1000)

st.markdown(f"""
<div class="hero-box">
    <div class="hero-title">🎾 Padel 99</div>
    <div class="hero-desc">تمرين {display_session} • تنظيم لعب متكامل وتنافسي</div>
    <div class="features-pill">⚡ كرات جديدة • مياه مبردة • تدوير عادل كل 15 دقيقة</div>
    <div style="font-size:0.84em; color:#e2e8f0; margin-top:4px;">
        ⏰ 9:30 م - 11:30 م | كورت 1 ({COURT_CAPACITY} مقاعد) • <b>متبقي {seats_left} مقاعد فقط! 🔥</b>
    </div>
</div>
""", unsafe_allow_html=True)

# عداد تنازلي دقيق بالـ JS بدون أخطاء Safari/Mobile
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

# ==============================================================================
# 6. بطاقة الكورت والمقاعد الستة
# ==============================================================================
seats_html = []
for i in range(COURT_CAPACITY):
    if i < booked_count:
        player_first_name = html.escape(confirmed_players[i]['name'].split()[0])
        seats_html.append(f'<div class="seat-card seat-taken">👤 {player_first_name} (محجوز)</div>')
    else:
        seats_html.append('<div class="seat-card seat-empty">✨ مقعد شاغر</div>')

st.markdown(f"""
<div class="court-container">
    <div class="court-header">🏟️ كورت 1 ({booked_count}/{COURT_CAPACITY})</div>
    <div class="seats-grid">
        {''.join(seats_html)}
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 7. شاشة الدفع بعد الحجز أو نموذج التسجيل
# ==============================================================================
if "booked" in st.session_state:
    b = st.session_state["booked"]
    target_epoch_ms = b.get("expire_timestamp", 0)
    
    st.markdown(f"""
    <div style="background:#0f172a; border:1.5px solid #38bdf8; border-radius:14px; padding:14px; text-align:center; margin-top:8px;">
        <h3 style="color:#22c55e; margin:0 0 4px 0;">✅ تم حجز مقعدك مؤقتاً!</h3>
        <div style="font-size:0.92em; color:#e2e8f0; margin:6px 0;">المبلغ المطلوب: <b style="color:#22c55e; font-size:1.2em;">{UNIT_PRICE} ر.س</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    # عداد الـ 15 دقيقة المتبقية للدفع
    components.html(f"""
    <!DOCTYPE html>
    <div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(239, 68, 68, 0.15); border: 1.2px solid #ef4444; border-radius: 10px; padding: 8px; color: #fca5a5; font-size: 13px; font-weight: 700;">
        ⏳ مهلة التحويل وتثبيت المقعد: <span id="pay_timer" style="font-family: monospace; font-size: 18px; color: #f87171; font-weight: 900;">--:--</span>
    </div>
    <script>
        var payTarget = {target_epoch_ms};
        function updatePayTimer() {{
            var diff = payTarget - new Date().getTime();
            var el = document.getElementById('pay_timer');
            if (!el) return;
            if (diff <= 0) {{
                el.innerHTML = "00:00 (انتهت المهلة)";
                return;
            }}
            var m = Math.floor(diff / 60000);
            var s = Math.floor((diff % 60000) / 1000);
            el.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
        }}
        updatePayTimer();
        setInterval(updatePayTimer, 1000);
    </script>
    """, height=52)

    st.markdown("""
    <div style="background:#1e293b; border:1px solid #334155; border-radius:10px; padding:8px 12px; text-align:center; margin-top:8px;">
        <div style="font-size:0.8em; color:#94a3b8;">مصرف الراجحي | فارس ربيع العصيمي</div>
        <div style="font-size:0.75em; color:#38bdf8; margin-top:2px;">اضغط على الأيقونة بالأسفل لنسخ الآيبان مباشرة 👇</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.code(IBAN_NUMBER, language=None)
    
    wa_msg = (
        f"هلا كابتن فارس 🎾\n"
        f"أكدت حجزي في تمرين بادل 99 🤩\n\n"
        f"👤 الكابتن: {b['name']}\n"
        f"📅 تمرين: {display_session}\n"
        f"💵 المبلغ المحول: {UNIT_PRICE} ر.س\n\n"
        f"مرفق إيصال التحويل لتثبيت المقعد! 🔥"
    )
    wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال عبر واتساب وتأكيد المقعد</a>', unsafe_allow_html=True)

elif seats_left == 0:
    st.info("⚠️ المقاعد مكتملة بالكامل لتمرين اليوم. تواصل عبر الواتساب للاستفسار عن أي شواغر طارئة.")
    wa_inq = f"مرحبا كابتن فارس، هل يوجد شاغر إضافي لتمرين {display_session}؟"
    wa_inq_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_inq)}"
    st.markdown(f'<a href="{wa_inq_url}" target="_blank" class="wa-btn" style="background:#0284c7;">💬 الاستفسار عن شواغر عبر واتساب</a>', unsafe_allow_html=True)

else:
    # نموذج الحجز المباشر (مع مفاتيح فريدة تمنع تكرار المعرفات)
    with st.form("main_booking_form_final", clear_on_submit=True):
        f_name = st.text_input("اسم اللاعب", placeholder="اكتب اسمك الثلاثي أو الثنائي", key="f_name_unique_key")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx", key="f_phone_unique_key")
        f_level = st.selectbox(
            "مستوى اللعب", 
            [
                "🟢 متوسط • ثبات في التبادلات والتمركز",
                "🔵 متقدم • سرعة وتكتيك وقوة ضربات",
                "🟡 مبتدئ متمكن • معرفة بقواعد اللعب والإرسال"
            ],
            key="f_level_unique_key"
        )
        hp = st.text_input("hp", label_visibility="collapsed", key="f_hp_bot_filter")
        
        btn_submit = st.form_submit_button("تثبيت المقعد والانتقال للسداد 💸", use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:0.75em; color:#64748b; margin-top:-4px;'>🛡️ المقعد يحجز مؤقتاً لمدة 15 دقيقة لإتمام السداد.</div>", unsafe_allow_html=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2:
                st.error("يرجى إدخال اسمك الكريم بشكل صحيح.")
            elif not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل رقم جوال سعودي صحيح (مثال: 05xxxxxxxx).")
            else:
                try:
                    current_active = get_active_session_bookings(db_session_key)
                    
                    if any(item["phone"] == clean_phone for item in current_active):
                        st.warning("أنت مسجل بالفعل في هذا التمرين ومقعدك محجوز!")
                    elif len(current_active) >= COURT_CAPACITY:
                        st.error("عذراً، اكتملت المقاعد المتاحة للتو!")
                    else:
                        now_utc = datetime.now(timezone.utc)
                        expire_dt = now_utc + timedelta(minutes=15)
                        expire_iso = expire_dt.isoformat()
                        expire_ms = int(expire_dt.timestamp() * 1000)
                        
                        # تم التأكد: استخدام session_day المتطابق مع Supabase
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": db_session_key,
                            "court": 1,
                            "level": f_level.split("•")[0].strip(),
                            "status": "confirmed",
                            "payment_status": "pending",
                            "expires_at": expire_iso,
                            "hear_about": "DIRECT",
                            "player_note": ""
                        }).execute()
                        
                        st.session_state["booked"] = {
                            "name": clean_name,
                            "expire_timestamp": expire_ms
                        }
                        st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {ex}")

# ==============================================================================
# 8. لوحة الإدارة والمؤشرات الاقتصادية الحية
# ==============================================================================
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة والمؤشرات الاقتصادية"):
    admin_pin = st.text_input("رمز الدخول الإداري:", type="password", key="admin_pin_input_panel")
    
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PIN_HASH):
        current_data = supabase.table("bookings") \
            .select("id, name, phone, payment_status") \
            .eq("session_day", db_session_key) \
            .eq("status", "confirmed") \
            .order("id") \
            .execute().data or []
            
        paid_players = [p for p in current_data if p.get("payment_status") == "paid"]
        paid_count = len(paid_players)
        
        # اقتصاديات الوحدة الحية
        total_collected = paid_count * UNIT_PRICE
        escrow_reserved = min(total_collected, FIXED_COURT_COST)
        net_profit = max(0, total_collected - FIXED_COURT_COST)
        total_liability = round(paid_count * LOYALTY_LIABILITY, 2)
        remaining_to_breakeven = max(0, BREAK_EVEN_PLAYERS - paid_count)
        
        st.markdown(f"""
        <div class="metrics-card">
            <div style="font-size:0.85em; color:#94a3b8; font-weight:700; margin-bottom:6px;">📈 المؤشرات الاقتصادية للجلسة:</div>
            <div style="font-size:0.82em; color:#e2e8f0; line-height:1.7;">
                • <b>المحصل الفعلي كاش:</b> <span style="color:#38bdf8;">{total_collected} ر.س</span><br>
                • <b>حساب الضمان للملعب (Escrow):</b> <span style="color:#fbbf24;">{escrow_reserved} / {FIXED_COURT_COST} ر.س</span><br>
                • <b>صافي الأرباح المحررة:</b> <span style="color:#22c55e; font-weight:800;">{net_profit} ر.س</span><br>
                • <b>مخصص الولاء المؤجل (IFRS 15):</b> <span style="color:#f87171;">{total_liability} ر.س</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if paid_count >= BREAK_EVEN_PLAYERS:
            st.success(f"✅ تم تجاوز نقطة التعادل ({paid_count} مدفوع). إقامة التمرين مؤكدة ومربحة.")
        else:
            st.warning(f"⚠️ وضع الحذر: متبقي {remaining_to_breakeven} لاعبين مدفوعين لتغطية إيجار الملعب (Stop-Loss).")
            
        st.write(f"👥 **كشف الحضور ({len(current_data)}/{COURT_CAPACITY}):**")
        for row in current_data:
            c1, c2, c3 = st.columns([2, 1.2, 1.2])
            c1.write(f"**{row['name']}**\n`{row['phone']}`")
            if row['payment_status'] == 'paid':
                c2.markdown("<span style='color:#22c55e; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                c2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                if c3.button("تثبيت ✅", key=f"admin_confirm_btn_{row['id']}"):
                    supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                    st.rerun()
