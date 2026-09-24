import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة والأنماط البصرية (Mobile-First Architecture)
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

/* بطاقة الكورت والمقاعد الستة */
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

/* بطاقات النظام المالي */
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
    padding: 4px 0;
    border-bottom: 1px solid #1e293b;
}

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
    st.error("تعذر الاتصال بالسحابة. يرجى التأكد من ضبط Secrets.")
    st.stop()

# ==============================================================================
# 3. محرك الجدولة واختيار الوقت الأفضل
# ==============================================================================
def resolve_next_session() -> tuple[str, str, datetime]:
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    # أفضل أوقات اللعب في جدة هي الفترات المسائية (أحد، ثلاثاء، خميس)
    weekday_offsets = {
        0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"),
        2: (1, "الخميس"),   3: (0, "الخميس"),
        4: (2, "الأحد"),    5: (1, "الأحد"),
        6: (0, "الأحد")
    }
    
    days_to_add, day_name = weekday_offsets.get(now.weekday(), (0, "الأحد"))
    
    # بعد الساعة 10:30 مساءً ينتهي تمرين اليوم وينتقل للتمرين القادم
    if days_to_add == 0 and (now.hour > 22 or (now.hour == 22 and now.minute >= 30)):
        next_dt = now + timedelta(days=1)
        days_to_add, day_name = weekday_offsets.get(next_dt.weekday(), (0, "الأحد"))
        days_to_add += 1
        
    target_date = now + timedelta(days=days_to_add)
    session_start_dt = target_date.replace(hour=21, minute=30, second=0, microsecond=0)
    
    return f"{day_name} ({target_date.strftime('%d/%m')})", f"{day_name} {target_date.strftime('%Y-%m-%d')}", session_start_dt

display_session, db_session_key, session_start_time = resolve_next_session()

# ==============================================================================
# 4. محرك المالية السحابية (قراءة وكتابة دائمة في Supabase)
# ==============================================================================
COURT_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PIN_HASH = "9900"

def get_or_create_financials(session_key: str) -> dict:
    """جلب الإعدادات المالية للجلسة من السحابة أو إنشاء سجل افتراضي."""
    defaults = {
        "session_day": session_key,
        "court_cost": 300,
        "unit_price": 65,
        "balls_cost": 35,
        "water_cost": 15,
        "court_paid": False,
        "iban_number": "SA9380000222608016013114",
        "account_name": "مصرف الراجحي | فارس ربيع العصيمي"
    }
    try:
        res = supabase.table("session_finance").select("*").eq("session_day", session_key).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        else:
            supabase.table("session_finance").insert(defaults).execute()
            return defaults
    except Exception:
        # وضع الحماية في حال لم ينشأ الجدول بعد
        return defaults

fin_data = get_or_create_financials(db_session_key)
UNIT_PRICE = float(fin_data.get("unit_price", 65))
COURT_COST = float(fin_data.get("court_cost", 300))
BALLS_COST = float(fin_data.get("balls_cost", 35))
WATER_COST = float(fin_data.get("water_cost", 15))
COURT_IS_PAID = bool(fin_data.get("court_paid", False))
IBAN_NUMBER = str(fin_data.get("iban_number", "SA9380000222608016013114"))
ACCOUNT_NAME = str(fin_data.get("account_name", "مصرف الراجحي | فارس ربيع العصيمي"))

# ==============================================================================
# 5. استرجاع الحجوزات الصالحة (معالجة Lazy Expiration)
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
# 6. واجهة المستخدم الرئيسية والعداد المباشر
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

# عداد تنازلي دقيق بالمللي ثانية
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

# عرض شبكة المقاعد
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

# ==============================================================================
# 7. شاشة الدفع أو نموذج الحجز
# ==============================================================================
if "booked" in st.session_state:
    b = st.session_state["booked"]
    target_epoch_ms = b.get("expire_timestamp", 0)
    
    st.markdown(f"""
    <div style="background:#0f172a; border:1.5px solid #38bdf8; border-radius:14px; padding:14px; text-align:center; margin-top:8px;">
        <h3 style="color:#22c55e; margin:0 0 4px 0;">✅ تم حجز مقعدك مؤقتاً!</h3>
        <div style="font-size:0.92em; color:#e2e8f0; margin:6px 0;">المبلغ المطلوب: <b style="color:#22c55e; font-size:1.2em;">{int(UNIT_PRICE)} ر.س</b></div>
    </div>
    """, unsafe_allow_html=True)
    
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

    st.markdown(f"""
    <div style="background:#1e293b; border:1px solid #334155; border-radius:10px; padding:8px 12px; text-align:center; margin-top:8px;">
        <div style="font-size:0.8em; color:#94a3b8;">{ACCOUNT_NAME}</div>
        <div style="font-size:0.75em; color:#38bdf8; margin-top:2px;">اضغط على الأيقونة لنسخ رقم الآيبان 👇</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.code(IBAN_NUMBER, language=None)
    
    wa_msg = f"هلا كابتن فارس 🎾\nأكدت حجزي في تمرين بادل 99 🤩\n\n👤 الكابتن: {b['name']}\n📅 تمرين: {display_session}\n💵 المبلغ المحول: {int(UNIT_PRICE)} ر.س\n\nمرفق إيصال التحويل لتثبيت المقعد! 🔥"
    wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال عبر واتساب وتأكيد المقعد</a>', unsafe_allow_html=True)

elif seats_left == 0:
    st.info("⚠️ المقاعد مكتملة بالكامل لتمرين اليوم.")
else:
    with st.form("main_booking_form_v3", clear_on_submit=True):
        f_name = st.text_input("اسم اللاعب", placeholder="اكتب اسمك الثلاثي أو الثنائي", key="f_name_input_v3")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx", key="f_phone_input_v3")
        f_level = st.selectbox(
            "مستوى اللعب", 
            ["🟢 متوسط • ثبات في التبادلات والتمركز", "🔵 متقدم • سرعة وتكتيك وقوة ضربات", "🟡 مبتدئ متمكن • معرفة بقواعد اللعب والإرسال"],
            key="f_level_input_v3"
        )
        # مصيدة البوتات (Invisible Honeypot)
        hp = st.text_input("hp", label_visibility="collapsed", key="f_hp_antispam")
        
        btn_submit = st.form_submit_button("تثبيت المقعد والانتقال للسداد 💸", use_container_width=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل اسمك ورقم جوال سعودي صحيح (05xxxxxxxx).")
            else:
                try:
                    current_active = get_active_session_bookings(db_session_key)
                    if any(item["phone"] == clean_phone for item in current_active):
                        st.warning("أنت مسجل بالفعل في هذا التمرين!")
                    elif len(current_active) >= COURT_CAPACITY:
                        st.error("عذراً، اكتملت المقاعد المتاحة للتو!")
                    else:
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
                            "player_note": ""
                        }).execute()
                        
                        st.session_state["booked"] = {
                            "name": clean_name,
                            "expire_timestamp": int(expire_dt.timestamp() * 1000)
                        }
                        st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {ex}")

# ==============================================================================
# 8. النظام المالي ولوحة التحكم السحابية المتقدمة
# ==============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
with st.expander("📊 النظام المالي ولوحة الإدارة السحابية"):
    admin_pin = st.text_input("رمز الدخول السري (PIN):", type="password", key="admin_pin_final_key")
    
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PIN_HASH):
        st.success("🔓 تم تسجيل الدخول بصلاحيات الإدارة والمالية.")
        
        tab1, tab2, tab3 = st.tabs(["💰 المركز المالي اللحظي", "👥 الحضور وتثبيت الدفع", "⚙️ تعديل التكاليف والحساب"])
        
        # 1. المركز المالي
        with tab1:
            all_records = supabase.table("bookings") \
                .select("id, name, phone, payment_status") \
                .eq("session_day", db_session_key) \
                .eq("status", "confirmed") \
                .execute().data or []
                
            paid_players = [p for p in all_records if p.get("payment_status") == "paid"]
            pending_players = [p for p in all_records if p.get("payment_status") == "pending"]
            
            paid_count = len(paid_players)
            total_inflow = paid_count * UNIT_PRICE
            pending_inflow = len(pending_players) * UNIT_PRICE
            total_expenses = COURT_COST + BALLS_COST + WATER_COST
            
            # محفظة الضمان للملعب
            escrow_reserved = min(total_inflow, COURT_COST) if not COURT_IS_PAID else 0
            
            # صافي الربح الحقيقي بعد كل المصروفات (ملعب + كور + موية)
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
                    <span>🏆 صافي الربح الحقيقي المحرر:</span>
                    <b style="color:{'#22c55e' if net_profit >= 0 else '#ef4444'}; font-size:1.15em;">{int(net_profit)} ر.س</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if paid_count >= break_even_seats:
                st.success(f"🎯 الجلسة حققت نقطة التعادل وتولد أرباحاً صافية (المقاعد المطلوبة: {break_even_seats}).")
            else:
                st.warning(f"⚠️ متبقي {break_even_seats - paid_count} مقاعد مدفوعة للوصول لنقطة التعادل وتغطية المصاريف.")
                
            # زر سداد الملعب
            if not COURT_IS_PAID:
                if st.button("تأكيد سداد الملعب رسميًا 🏟️", use_container_width=True):
                    supabase.table("session_finance").update({"court_paid": True}).eq("session_day", db_session_key).execute()
                    st.rerun()
            else:
                if st.button("إلغاء وسم سداد الملعب ↩️", use_container_width=True):
                    supabase.table("session_finance").update({"court_paid": False}).eq("session_day", db_session_key).execute()
                    st.rerun()

        # 2. كشف الحضور وتثبيت الدفع
        with tab2:
            st.write(f"إجمالي المسجلين: **{len(all_records)}/{COURT_CAPACITY}**")
            for row in all_records:
                c1, c2, c3 = st.columns([2, 1.2, 1.2])
                c1.write(f"**{row['name']}**\n`{row['phone']}`")
                if row['payment_status'] == 'paid':
                    c2.markdown("<span style='color:#22c55e; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
                else:
                    c2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                    if c3.button("تثبيت الدفع", key=f"pay_btn_fin_{row['id']}"):
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                        st.rerun()

        # 3. تعديل التكاليف والحساب السحابي الدائم
        with tab3:
            st.markdown("#### ⚙️ تعديل التكاليف والبيانات المالية (تُحفظ في السحابة):")
            with st.form("cloud_finance_update_form"):
                n_court = st.number_input("تكلفة الملعب الثابتة (ر.س):", value=int(COURT_COST), step=10)
                n_unit = st.number_input("سعر التذكرة للاعب (ر.س):", value=int(UNIT_PRICE), step=5)
                n_balls = st.number_input("تكلفة علبة الكرات (ر.س):", value=int(BALLS_COST), step=5)
                n_water = st.number_input("تكلفة كرتون المياه (ر.س):", value=int(WATER_COST), step=5)
                
                st.markdown("---")
                n_iban = st.text_input("رقم الآيبان (IBAN):", value=IBAN_NUMBER)
                n_acc = st.text_input("اسم البنك وصاحب الحساب:", value=ACCOUNT_NAME)
                
                btn_save = st.form_submit_button("حفظ التغييرات في السحابة 💾", use_container_width=True)
                if btn_save:
                    try:
                        supabase.table("session_finance").upsert({
                            "session_day": db_session_key,
                            "court_cost": n_court,
                            "unit_price": n_unit,
                            "balls_cost": n_balls,
                            "water_cost": n_water,
                            "iban_number": n_iban.strip(),
                            "account_name": n_acc.strip(),
                            "court_paid": COURT_IS_PAID
                        }).execute()
                        st.success("✅ تم حفظ وتحديث البيانات المالية في السحابة بنجاح!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"تعذر الحفظ: {err}").hero-box {
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

/* بطاقة الكورت والمقاعد الستة */
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

/* بطاقات النظام المالي */
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
    padding: 4px 0;
    border-bottom: 1px solid #1e293b;
}

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
    st.error("تعذر الاتصال بالسحابة. يرجى التأكد من ضبط Secrets.")
    st.stop()

# ==============================================================================
# 3. محرك الجدولة واختيار الوقت الأفضل
# ==============================================================================
def resolve_next_session() -> tuple[str, str, datetime]:
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    # أفضل أوقات اللعب في جدة هي الفترات المسائية (أحد، ثلاثاء، خميس)
    weekday_offsets = {
        0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"),
        2: (1, "الخميس"),   3: (0, "الخميس"),
        4: (2, "الأحد"),    5: (1, "الأحد"),
        6: (0, "الأحد")
    }
    
    days_to_add, day_name = weekday_offsets.get(now.weekday(), (0, "الأحد"))
    
    # بعد الساعة 10:30 مساءً ينتهي تمرين اليوم وينتقل للتمرين القادم
    if days_to_add == 0 and (now.hour > 22 or (now.hour == 22 and now.minute >= 30)):
        next_dt = now + timedelta(days=1)
        days_to_add, day_name = weekday_offsets.get(next_dt.weekday(), (0, "الأحد"))
        days_to_add += 1
        
    target_date = now + timedelta(days=days_to_add)
    session_start_dt = target_date.replace(hour=21, minute=30, second=0, microsecond=0)
    
    return f"{day_name} ({target_date.strftime('%d/%m')})", f"{day_name} {target_date.strftime('%Y-%m-%d')}", session_start_dt

display_session, db_session_key, session_start_time = resolve_next_session()

# ==============================================================================
# 4. محرك المالية السحابية (قراءة وكتابة دائمة في Supabase)
# ==============================================================================
COURT_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PIN_HASH = "9900"

def get_or_create_financials(session_key: str) -> dict:
    """جلب الإعدادات المالية للجلسة من السحابة أو إنشاء سجل افتراضي."""
    defaults = {
        "session_day": session_key,
        "court_cost": 300,
        "unit_price": 65,
        "balls_cost": 35,
        "water_cost": 15,
        "court_paid": False,
        "iban_number": "SA9380000222608016013114",
        "account_name": "مصرف الراجحي | فارس ربيع العصيمي"
    }
    try:
        res = supabase.table("session_finance").select("*").eq("session_day", session_key).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        else:
            supabase.table("session_finance").insert(defaults).execute()
            return defaults
    except Exception:
        # وضع الحماية في حال لم ينشأ الجدول بعد
        return defaults

fin_data = get_or_create_financials(db_session_key)
UNIT_PRICE = float(fin_data.get("unit_price", 65))
COURT_COST = float(fin_data.get("court_cost", 300))
BALLS_COST = float(fin_data.get("balls_cost", 35))
WATER_COST = float(fin_data.get("water_cost", 15))
COURT_IS_PAID = bool(fin_data.get("court_paid", False))
IBAN_NUMBER = str(fin_data.get("iban_number", "SA9380000222608016013114"))
ACCOUNT_NAME = str(fin_data.get("account_name", "مصرف الراجحي | فارس ربيع العصيمي"))

# ==============================================================================
# 5. استرجاع الحجوزات الصالحة (معالجة Lazy Expiration)
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
# 6. واجهة المستخدم الرئيسية والعداد المباشر
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

# عداد تنازلي دقيق بالمللي ثانية
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

# عرض شبكة المقاعد
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

# ==============================================================================
# 7. شاشة الدفع أو نموذج الحجز
# ==============================================================================
if "booked" in st.session_state:
    b = st.session_state["booked"]
    target_epoch_ms = b.get("expire_timestamp", 0)
    
    st.markdown(f"""
    <div style="background:#0f172a; border:1.5px solid #38bdf8; border-radius:14px; padding:14px; text-align:center; margin-top:8px;">
        <h3 style="color:#22c55e; margin:0 0 4px 0;">✅ تم حجز مقعدك مؤقتاً!</h3>
        <div style="font-size:0.92em; color:#e2e8f0; margin:6px 0;">المبلغ المطلوب: <b style="color:#22c55e; font-size:1.2em;">{int(UNIT_PRICE)} ر.س</b></div>
    </div>
    """, unsafe_allow_html=True)
    
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

    st.markdown(f"""
    <div style="background:#1e293b; border:1px solid #334155; border-radius:10px; padding:8px 12px; text-align:center; margin-top:8px;">
        <div style="font-size:0.8em; color:#94a3b8;">{ACCOUNT_NAME}</div>
        <div style="font-size:0.75em; color:#38bdf8; margin-top:2px;">اضغط على الأيقونة لنسخ رقم الآيبان 👇</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.code(IBAN_NUMBER, language=None)
    
    wa_msg = f"هلا كابتن فارس 🎾\nأكدت حجزي في تمرين بادل 99 🤩\n\n👤 الكابتن: {b['name']}\n📅 تمرين: {display_session}\n💵 المبلغ المحول: {int(UNIT_PRICE)} ر.س\n\nمرفق إيصال التحويل لتثبيت المقعد! 🔥"
    wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال عبر واتساب وتأكيد المقعد</a>', unsafe_allow_html=True)

elif seats_left == 0:
    st.info("⚠️ المقاعد مكتملة بالكامل لتمرين اليوم.")
else:
    with st.form("main_booking_form_v3", clear_on_submit=True):
        f_name = st.text_input("اسم اللاعب", placeholder="اكتب اسمك الثلاثي أو الثنائي", key="f_name_input_v3")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx", key="f_phone_input_v3")
        f_level = st.selectbox(
            "مستوى اللعب", 
            ["🟢 متوسط • ثبات في التبادلات والتمركز", "🔵 متقدم • سرعة وتكتيك وقوة ضربات", "🟡 مبتدئ متمكن • معرفة بقواعد اللعب والإرسال"],
            key="f_level_input_v3"
        )
        # مصيدة البوتات (Invisible Honeypot)
        hp = st.text_input("hp", label_visibility="collapsed", key="f_hp_antispam")
        
        btn_submit = st.form_submit_button("تثبيت المقعد والانتقال للسداد 💸", use_container_width=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل اسمك ورقم جوال سعودي صحيح (05xxxxxxxx).")
            else:
                try:
                    current_active = get_active_session_bookings(db_session_key)
                    if any(item["phone"] == clean_phone for item in current_active):
                        st.warning("أنت مسجل بالفعل في هذا التمرين!")
                    elif len(current_active) >= COURT_CAPACITY:
                        st.error("عذراً، اكتملت المقاعد المتاحة للتو!")
                    else:
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
                            "player_note": ""
                        }).execute()
                        
                        st.session_state["booked"] = {
                            "name": clean_name,
                            "expire_timestamp": int(expire_dt.timestamp() * 1000)
                        }
                        st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {ex}")

# ==============================================================================
# 8. النظام المالي ولوحة التحكم السحابية المتقدمة
# ==============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
with st.expander("📊 النظام المالي ولوحة الإدارة السحابية"):
    admin_pin = st.text_input("رمز الدخول السري (PIN):", type="password", key="admin_pin_final_key")
    
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PIN_HASH):
        st.success("🔓 تم تسجيل الدخول بصلاحيات الإدارة والمالية.")
        
        tab1, tab2, tab3 = st.tabs(["💰 المركز المالي اللحظي", "👥 الحضور وتثبيت الدفع", "⚙️ تعديل التكاليف والحساب"])
        
        # 1. المركز المالي
        with tab1:
            all_records = supabase.table("bookings") \
                .select("id, name, phone, payment_status") \
                .eq("session_day", db_session_key) \
                .eq("status", "confirmed") \
                .execute().data or []
                
            paid_players = [p for p in all_records if p.get("payment_status") == "paid"]
            pending_players = [p for p in all_records if p.get("payment_status") == "pending"]
            
            paid_count = len(paid_players)
            total_inflow = paid_count * UNIT_PRICE
            pending_inflow = len(pending_players) * UNIT_PRICE
            total_expenses = COURT_COST + BALLS_COST + WATER_COST
            
            # محفظة الضمان للملعب
            escrow_reserved = min(total_inflow, COURT_COST) if not COURT_IS_PAID else 0
            
            # صافي الربح الحقيقي بعد كل المصروفات (ملعب + كور + موية)
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
                    <span>🏆 صافي الربح الحقيقي المحرر:</span>
                    <b style="color:{'#22c55e' if net_profit >= 0 else '#ef4444'}; font-size:1.15em;">{int(net_profit)} ر.س</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if paid_count >= break_even_seats:
                st.success(f"🎯 الجلسة حققت نقطة التعادل وتولد أرباحاً صافية (المقاعد المطلوبة: {break_even_seats}).")
            else:
                st.warning(f"⚠️ متبقي {break_even_seats - paid_count} مقاعد مدفوعة للوصول لنقطة التعادل وتغطية المصاريف.")
                
            # زر سداد الملعب
            if not COURT_IS_PAID:
                if st.button("تأكيد سداد الملعب رسميًا 🏟️", use_container_width=True):
                    supabase.table("session_finance").update({"court_paid": True}).eq("session_day", db_session_key).execute()
                    st.rerun()
            else:
                if st.button("إلغاء وسم سداد الملعب ↩️", use_container_width=True):
                    supabase.table("session_finance").update({"court_paid": False}).eq("session_day", db_session_key).execute()
                    st.rerun()

        # 2. كشف الحضور وتثبيت الدفع
        with tab2:
            st.write(f"إجمالي المسجلين: **{len(all_records)}/{COURT_CAPACITY}**")
            for row in all_records:
                c1, c2, c3 = st.columns([2, 1.2, 1.2])
                c1.write(f"**{row['name']}**\n`{row['phone']}`")
                if row['payment_status'] == 'paid':
                    c2.markdown("<span style='color:#22c55e; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
                else:
                    c2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                    if c3.button("تثبيت الدفع", key=f"pay_btn_fin_{row['id']}"):
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                        st.rerun()

        # 3. تعديل التكاليف والحساب السحابي الدائم
        with tab3:
            st.markdown("#### ⚙️ تعديل التكاليف والبيانات المالية (تُحفظ في السحابة):")
            with st.form("cloud_finance_update_form"):
                n_court = st.number_input("تكلفة الملعب الثابتة (ر.س):", value=int(COURT_COST), step=10)
                n_unit = st.number_input("سعر التذكرة للاعب (ر.س):", value=int(UNIT_PRICE), step=5)
                n_balls = st.number_input("تكلفة علبة الكرات (ر.س):", value=int(BALLS_COST), step=5)
                n_water = st.number_input("تكلفة كرتون المياه (ر.س):", value=int(WATER_COST), step=5)
                
                st.markdown("---")
                n_iban = st.text_input("رقم الآيبان (IBAN):", value=IBAN_NUMBER)
                n_acc = st.text_input("اسم البنك وصاحب الحساب:", value=ACCOUNT_NAME)
                
                btn_save = st.form_submit_button("حفظ التغييرات في السحابة 💾", use_container_width=True)
                if btn_save:
                    try:
                        supabase.table("session_finance").upsert({
                            "session_day": db_session_key,
                            "court_cost": n_court,
                            "unit_price": n_unit,
                            "balls_cost": n_balls,
                            "water_cost": n_water,
                            "iban_number": n_iban.strip(),
                            "account_name": n_acc.strip(),
                            "court_paid": COURT_IS_PAID
                        }).execute()
                        st.success("✅ تم حفظ وتحديث البيانات المالية في السحابة بنجاح!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"تعذر الحفظ: {err}")
