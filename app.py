import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة والتنسيق العام
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

/* بطاقة العنوان */
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

/* بطاقة الدفع */
.pay-box {
    background: #0f172a;
    border: 1.5px solid #38bdf8;
    border-radius: 16px;
    padding: 16px 14px;
    text-align: center;
    margin-top: 8px;
    margin-bottom: 10px;
}

/* زر الحجز السريع */
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

/* تخصيص مربع نسخ الآيبان السريع */
div[data-testid="stCodeBlock"] {
    direction: ltr !important;
    border-radius: 10px !important;
    border: 1px dashed #38bdf8 !important;
}

div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. الثوابت والاتصال السحابي (Supabase)
# ==============================================================================
COURT_CAPACITY = 6
PRICE_PER_SEAT = 69
IBAN_NUMBER = "SA9380000222608016013114"
ADMIN_PHONE = "966566261868"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"].strip().rstrip('/'),
        st.secrets["SUPABASE_KEY"].strip()
    )

try:
    supabase = get_supabase_client()
except Exception:
    st.error("تعذر الاتصال بقاعدة البيانات السحابية. يرجى مراجعة الإعدادات.")
    st.stop()

# ==============================================================================
# 3. محرك الجدولة الزمنية التلقائية
# ==============================================================================
def resolve_next_session() -> tuple[str, str]:
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    weekday_offsets = {
        0: (1, "الثلاثاء"), 1: (0, "الثلاثاء"),
        2: (1, "الخميس"),   3: (0, "الخميس"),
        4: (2, "الأحد"),    5: (1, "الأحد"),
        6: (0, "الأحد")
    }
    
    days_to_add, day_name = weekday_offsets.get(now.weekday(), (0, "الأحد"))
    
    # إذا انتهى تمرين اليوم (بعد 10:30 م)، ينتقل تلقائياً للتمرين القادم
    if days_to_add == 0 and now.hour >= 22 and now.minute >= 30:
        next_dt = now + timedelta(days=1)
        days_to_add, day_name = weekday_offsets.get(next_dt.weekday(), (0, "الأحد"))
        days_to_add += 1
        
    target_date = now + timedelta(days=days_to_add)
    return f"{day_name} ({target_date.strftime('%d/%m')})", f"{day_name} {target_date.strftime('%Y-%m-%d')}"

display_session, db_session_key = resolve_next_session()

# ==============================================================================
# 4. محرك قراءة المقاعد من السحابة وتصفية الحجوزات المنتهية
# ==============================================================================
def get_cloud_active_bookings(session_key: str) -> list:
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
            # فحص سريان الـ 15 دقيقة
            has_time_left = p.get("expires_at") and p["expires_at"] > now_utc_iso
            
            if is_paid or has_time_left:
                valid_players.append(p)
                
        return valid_players
    except Exception:
        return []

active_bookings = get_cloud_active_bookings(db_session_key)
confirmed_players = active_bookings[:COURT_CAPACITY]
booked_count = len(confirmed_players)
seats_left = max(0, COURT_CAPACITY - booked_count)

# رسم مؤشر النقاط للمقاعد
dots_html = "".join(['<div class="seat-dot dot-booked" title="محجوز"></div>' for _ in range(booked_count)])
dots_html += "".join(['<div class="seat-dot dot-free" title="متاح"></div>' for _ in range(seats_left)])

# ==============================================================================
# 5. عرض الواجهة
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
# 6. شاشة الحجز الناجح (العداد والآيبان بدون أخطاء تشويه)
# ==============================================================================
if "booked" in st.session_state:
    b = st.session_state["booked"]
    target_epoch_ms = b.get("expire_timestamp", 0)
    
    # بطاقة تفاصيل المبلغ
    st.markdown(f"""
<div class="pay-box">
    <h3 style="color:#22c55e; margin:0 0 6px 0;">✅ تم حجز مقعدك بنجاح!</h3>
    <div style="font-size:0.95em; color:#e2e8f0; margin:6px 0;">
        المبلغ المطلوب: <b style="color:#22c55e; font-size:1.25em;">{PRICE_PER_SEAT} ر.س</b>
    </div>
</div>
""", unsafe_allow_html=True)

    # تشغيل العداد داخل مكون معزول لضمان عدم حدوث تشويه في الصفحة
    components.html(f"""
    <!DOCTYPE html>
    <div style="direction: rtl; text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: rgba(239, 68, 68, 0.15); border: 1.5px solid #ef4444; border-radius: 12px; padding: 10px; color: #fca5a5; font-size: 14px; font-weight: 700;">
        ⏳ المقعد محجوز لك مؤقتاً: <span id="countdown" style="font-family: monospace; font-size: 20px; color: #f87171; font-weight: 900;">--:--</span>
    </div>
    <script>
        var targetTime = {target_epoch_ms};
        function updateTimer() {{
            var now = new Date().getTime();
            var distance = targetTime - now;
            var el = document.getElementById('countdown');
            if (!el) return;
            if (distance <= 0) {{
                el.innerHTML = "00:00";
                return;
            }}
            var m = Math.floor(distance / 60000);
            var s = Math.floor((distance % 60000) / 1000);
            el.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
        }}
        updateTimer();
        setInterval(updateTimer, 1000);
    </script>
    """, height=65)

    # بطاقة الحساب البنكي وزر النسخ المدمج الأصلي
    st.markdown("""
<div style="background:#1e293b; border:1px solid #334155; border-radius:10px; padding:8px 12px; text-align:center; margin-top:10px;">
    <div style="font-size:0.8em; color:#94a3b8;">مصرف الراجحي | فارس ربيع العصيمي</div>
    <div style="font-size:0.75em; color:#38bdf8; margin-top:2px;">اضغط على الأيقونة لنسخ رقم الآيبان مباشرة 👇</div>
</div>
""", unsafe_allow_html=True)
    
    st.code(IBAN_NUMBER, language=None)
    
    # رسالة الواتساب الجاهزة
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
    # نموذج الحجز
    with st.form("quick_booking_form", clear_on_submit=True):
        f_name = st.text_input("الاسم الكريم", placeholder="اكتب اسمك")
        f_phone = st.text_input("رقم الجوال", placeholder="05xxxxxxxx")
        f_level = st.selectbox("المستوى في اللعب", ["متوسط", "متقدم", "مبتدئ"])
        hp = st.text_input("hp", label_visibility="collapsed")
        
        btn_submit = st.form_submit_button("تأكيد الحجز فوراً ⚡", use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:0.75em; color:#64748b; margin-top:-4px;'>🛡️ الحجز مؤكد مؤقتاً، وسيتم تثبيته فور استلام الإيصال.</div>", unsafe_allow_html=True)

        if btn_submit and not hp:
            clean_name = f_name.strip()
            
            # توحيد صيغة رقم الجوال وتحويل الأرقام العربية إلى إنجليزية
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2:
                st.error("يرجى إدخال اسم صحيح.")
            elif not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("فضلاً أدخل رقم جوال سعودي صحيح (مثال: 05xxxxxxxx).")
            else:
                try:
                    # فحص لحظي دقيق من قاعدة البيانات السحابية
                    current_active = get_cloud_active_bookings(db_session_key)
                    
                    if any(item["phone"] == clean_phone for item in current_active):
                        st.warning("أنت مسجل بالفعل في هذا التمرين ومقعدك محجوز!")
                    elif len(current_active) >= COURT_CAPACITY:
                        st.error("عذراً، اكتملت المقاعد المتاحة للتو!")
                    else:
                        # احتساب وقت انتهاء الـ 15 دقيقة
                        now_utc = datetime.now(timezone.utc)
                        expire_dt = now_utc + timedelta(minutes=15)
                        expire_iso = expire_dt.isoformat()
                        expire_ms = int(expire_dt.timestamp() * 1000)
                        
                        # حفظ الحجز ورقم الهاتف في السحابة
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
                        
                        st.session_state["booked"] = {
                            "name": clean_name,
                            "expire_timestamp": expire_ms
                        }
                        st.rerun()
                except Exception:
                    st.error("حدث خطأ أثناء الاتصال بقاعدة البيانات، يرجى المحاولة ثانية.")
