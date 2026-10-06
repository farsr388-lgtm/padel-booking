import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import uuid
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة وهوية المنصة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم جدة | قطة عطور درعة (خصم 70%)",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. تتبع الجلسات والخرائط الحرارية (Microsoft Clarity)
# ==============================================================================
components.html("""
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window.parent, window.parent.document, "clarity", "script", "ytjnujh8td");
</script>
""", height=0, width=0)

# ==============================================================================
# 3. أنماط الواجهة (CSS محسّن مع بطاقات التوفير)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 440px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f1f5f9;
}

/* شارة الخصم الفائقة */
.discount-pill {
    background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
    color: #ffffff;
    border-radius: 30px;
    padding: 6px 16px;
    font-size: 0.85em;
    font-weight: 900;
    display: inline-block;
    box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
    margin-bottom: 8px;
    letter-spacing: 0.5px;
}

/* بطاقة الهيدر الرئيسية */
.hero-box {
    background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
    border: 1px solid #4338ca;
    border-radius: 16px;
    padding: 16px 14px;
    text-align: center;
    margin-bottom: 10px;
    box-shadow: 0 8px 24px rgba(67, 56, 202, 0.2);
}
.location-badge {
    background: rgba(14, 165, 233, 0.2);
    color: #38bdf8;
    border: 1px solid #0284c7;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.76em;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 6px;
}
.hero-title { font-size: 1.45em; font-weight: 900; color: #ffffff; margin: 0 0 4px 0; }
.hero-desc { font-size: 0.85em; color: #cbd5e1; line-height: 1.5; margin-bottom: 8px; }

/* تسعير ومقارنة السعر */
.price-breakdown {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-top: 8px;
}
.price-item { text-align: center; }
.price-item .val { font-size: 1.3em; font-weight: 900; color: #10b981; }
.price-item .lbl { font-size: 0.72em; color: #94a3b8; }
.price-divider { color: #475569; font-weight: 300; font-size: 1.2em; }

/* شريط الخطوات الثلاث */
.steps-container {
    display: flex;
    justify-content: space-between;
    gap: 6px;
    margin: 10px 0;
}
.step-item {
    flex: 1;
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px 4px;
    text-align: center;
    font-size: 0.74em;
    color: #cbd5e1;
    line-height: 1.3;
}
.step-item.active {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.15);
    color: #e0e7ff;
    font-weight: 800;
}

/* صندوق الضمان */
.guarantee-box {
    background: rgba(16, 185, 129, 0.08);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 0.82em;
    color: #a7f3d0;
    line-height: 1.5;
    margin-bottom: 12px;
    text-align: center;
}

/* شبكة المقاعد */
.slots-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 10px 0;
}
.slot-card {
    border-radius: 10px;
    padding: 10px 6px;
    text-align: center;
    font-size: 0.8em;
    line-height: 1.4;
}
.slot-empty {
    background: rgba(30, 41, 59, 0.4);
    border: 1.5px dashed #475569;
    color: #94a3b8;
}
.slot-taken {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid #10b981;
    color: #f1f5f9;
}

/* تفاصيل العطر */
.perfume-details-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1.5px solid #4f46e5;
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0 14px 0;
    font-size: 0.84em;
    line-height: 1.6;
    color: #e2e8f0;
}
.perfume-details-card b { color: #818cf8; }

/* شاشة بعد الحجز */
.status-card-success {
    background: rgba(16, 185, 129, 0.12);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 18px 14px;
    text-align: center;
    margin-top: 8px;
}
.big-code-box {
    background: #0f172a;
    border: 2px solid #38bdf8;
    border-radius: 12px;
    padding: 12px;
    margin: 10px 0;
    text-align: center;
}
.big-code-title { font-size: 0.82em; color: #94a3b8; margin-bottom: 2px; }
.big-code-val {
    font-family: monospace;
    font-size: 1.65em;
    font-weight: 900;
    color: #38bdf8;
    letter-spacing: 2px;
}
.alert-instruction {
    background: rgba(245, 158, 11, 0.12);
    border: 1.5px solid #f59e0b;
    border-radius: 12px;
    padding: 12px;
    margin: 12px 0;
    font-size: 0.86em;
    line-height: 1.6;
    color: #fef3c7;
    text-align: right;
}
.wa-btn {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 15px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 1.05em;
    text-decoration: none;
    box-shadow: 0 4px 16px rgba(37, 211, 102, 0.35);
    margin-top: 12px;
}
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 52px !important;
    border-radius: 10px !important;
    border: none !important;
    margin-top: 6px !important;
}
/* إخفاء حقل Honeypot تماماً */
div[data-testid="stTextInput"]:has(input[aria-label="hp"]),
input[aria-label="hp"] { 
    display: none !important; 
    opacity: 0 !important;
    position: absolute !important;
    left: -9999px !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. ربط قاعدة البيانات السحابية (Supabase)
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    if url.endswith("/rest/v1"):
        url = url[:-8]
    return create_client(url, st.secrets["SUPABASE_KEY"].strip())

try:
    supabase = get_supabase_client()
except Exception:
    st.error("تعذر الاتصال بقاعدة البيانات. يرجى مراجعة Secrets.")
    st.stop()

# ==============================================================================
# 5. محرك تتبع سلوك المستخدم
# ==============================================================================
if "session_uuid" not in st.session_state:
    st.session_state["session_uuid"] = str(uuid.uuid4())[:8]

def log_event(event_name: str, meta: str = ""):
    try:
        supabase.table("site_analytics").insert({
            "session_id": st.session_state["session_uuid"],
            "event_name": event_name,
            "metadata": meta
        }).execute()
    except Exception:
        pass

if "page_view_logged" not in st.session_state:
    log_event("page_view", "زيارة سلة جدة (الأندلس)")
    st.session_state["page_view_logged"] = True

# ==============================================================================
# 6. إعدادات الحملة وكتالوج العطور
# ==============================================================================
BASKET_ID = "MAQSOOM-JEDDAH-01"
BASKET_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")

# توقيت نهاية العرض (4 أيام ثابتة من انطلاق الحملة)
CAMPAIGN_END_EPOCH = int((datetime.now(timezone.utc) + timedelta(days=4)).timestamp() * 1000)

PERFUMES_CATALOG = {
    "عطر ليدر (Leader) 100مل": {
        "store_price": 210,
        "share_price": 63,
        "notes": "جلود فاخرة، أخشاب الأرز، وتوابل دافئة",
        "character": "فخم ورسمي جداً للمناسبات وساعات الدوام"
    },
    "عطر بورموا (Pour Moi) 100مل": {
        "store_price": 210,
        "share_price": 63,
        "notes": "فانيلا فرنسية، عنبر ناعم، وزهور بيضاء",
        "character": "سويت جذاب ومريح للاستخدام اليومي"
    },
    "عطر لينك الأسود (Link Black) 100مل": {
        "store_price": 210,
        "share_price": 63,
        "notes": "برغموت إيطالي، حمضيات فواحة، مسك نقي",
        "character": "منعش، فواح، ويعطيك طاقة صباحية متجددة"
    },
    "عطر خواطر (Khawater) 100مل": {
        "store_price": 210,
        "share_price": 63,
        "notes": "باتشولي هادئ، نفحات عود خفيف، وقاعدة عنبرية",
        "character": "طابع شرقي كلاسيكي بثبات وفوحان عالي للمجالس"
    },
    "عطر سول (Soul) 100مل": {
        "store_price": 210,
        "share_price": 63,
        "notes": "هيل عطري، خزامى برية، وخشب الصندل الدافئ",
        "character": "عصري وشبابي ملفت للطلعات واللقاءات"
    },
    "عطر ميس درعة (Miss Deraah) 100مل": {
        "store_price": 210,
        "share_price": 63,
        "notes": "زهور الياسمين، فواكه حمراء، بودرة ومسك ناعم",
        "character": "ناعم وهادئ، خيار أنيق وراقي جداً"
    }
}

IBAN_NUMBER = "SA9380000222608016013114"
ACCOUNT_NAME = "مصرف الراجحي | فارس ربيع العصيمي"

# ==============================================================================
# 7. إدارة المقاعد وتدوير الحجوزات
# ==============================================================================
def process_basket_orders(session_key: str):
    now_utc = datetime.now(timezone.utc)
    now_utc_iso = now_utc.isoformat()
    
    try:
        all_records = supabase.table("bookings") \
            .select("*") \
            .eq("session_day", session_key) \
            .order("id") \
            .execute().data or []
            
        confirmed_active = []
        waitlist_records = []
        
        for r in all_records:
            if r.get("status") == "waitlist":
                waitlist_records.append(r)
            elif r.get("status") == "confirmed":
                is_paid = r.get("payment_status") == "paid"
                is_expired = r.get("expires_at") and r["expires_at"] <= now_utc_iso
                
                if not is_paid and is_expired:
                    supabase.table("bookings").update({
                        "status": "cancelled",
                        "player_note": "انتهاء مهلة السداد (15 دقيقة)"
                    }).eq("id", r["id"]).execute()
                    log_event("expired_unpaid", f"User: {r['phone']}")
                else:
                    confirmed_active.append(r)
                    
        vacancies = BASKET_CAPACITY - len(confirmed_active)
        if vacancies > 0 and waitlist_records:
            to_promote = waitlist_records[:vacancies]
            for wr in to_promote:
                new_exp = (now_utc + timedelta(minutes=15)).isoformat()
                supabase.table("bookings").update({
                    "status": "confirmed",
                    "payment_status": "pending",
                    "expires_at": new_exp,
                    "player_note": "تصعيد تلقائي من الانتظار"
                }).eq("id", wr["id"]).execute()
                
                wr["status"] = "confirmed"
                wr["payment_status"] = "pending"
                wr["expires_at"] = new_exp
                confirmed_active.append(wr)
                waitlist_records.remove(wr)
                
        return confirmed_active[:BASKET_CAPACITY], waitlist_records
    except Exception:
        return [], []

confirmed_orders, waitlist_orders = process_basket_orders(BASKET_ID)
taken_count = len(confirmed_orders)
slots_left = max(0, BASKET_CAPACITY - taken_count)

# ==============================================================================
# 8. الواجهة البصرية المباشرة
# ==============================================================================
# عداد تنازلي حي متزامن
components.html(f"""
<!DOCTYPE html>
<div style="direction: rtl; text-align: center; font-family: -apple-system, 'Cairo', sans-serif; background: linear-gradient(90deg, #1e1b4b, #312e81); border: 1px solid #818cf8; border-radius: 12px; padding: 10px; color: #ffffff; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);">
    <div style="font-size: 13px; font-weight: 800; color: #cbd5e1; margin-bottom: 4px;">
        ⏳ متبقي على انتهاء عرض درعة الكبرى وإغلاق السلة:
    </div>
    <div id="offer_countdown" style="font-family: monospace; font-size: 22px; font-weight: 900; color: #38bdf8; letter-spacing: 1px;">
        جاري الحساب...
    </div>
</div>
<script>
    var targetDate = {CAMPAIGN_END_EPOCH};
    function updateCountdown() {{
        var now = new Date().getTime();
        var diff = targetDate - now;
        if (diff <= 0) {{
            document.getElementById('offer_countdown').innerHTML = "انتهى العرض!";
            return;
        }}
        var days = Math.floor(diff / (1000 * 60 * 60 * 24));
        var hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((diff % (1000 * 60)) / 1000);
        document.getElementById('offer_countdown').innerHTML = 
            days + " يوم و " + (hours < 10 ? "0" : "") + hours + ":" + (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
    }}
    updateCountdown();
    setInterval(updateCountdown, 1000);
</script>
""", height=75)

st.markdown(f"""
<div class="hero-box">
    <div class="discount-pill">🔥 خصم 70% صافي • وفّرت 147 ر.س</div><br>
    <div class="location-badge">📍 حصرياً لمدينة جدة • استلام مجاني بالأندلس مول</div>
    <div class="hero-title">قطّة عطور درعة (1+2 مجاناً)</div>
    <div class="hero-desc">
        نجمّع 6 مشترين من <b>جدة</b> لاقتناص عرض درعة الكبرى؛ كل شخص يدفع <b>30% فقط</b> من قيمة عِطره الأصلي 100مل ويوفر 70% كاش.
    </div>
    <div class="price-breakdown">
        <div class="price-item">
            <div style="font-size:0.85em; color:#94a3b8; text-decoration:line-through;">210 ر.س</div>
            <div class="val">63 ر.س</div>
            <div class="lbl">استلام مجاني (الأندلس مول)</div>
        </div>
        <div class="price-divider">أو</div>
        <div class="price-item">
            <div style="font-size:0.85em; color:#94a3b8; text-decoration:line-through;">235 ر.س</div>
            <div class="val" style="color:#38bdf8;">88 ر.س</div>
            <div class="lbl">عبر خزانة RedBox (+25)</div>
        </div>
    </div>
</div>

<div class="steps-container">
    <div class="step-item active"><b>1. اختر عِطرك</b><br>وفر 147 ر.س</div>
    <div class="step-item"><b>2. حدد الاستلام</b><br>الأندلس أو RedBox</div>
    <div class="step-item"><b>3. حوّل واستلم</b><br>تثبيت المقعد فوراً</div>
</div>

<div class="guarantee-box">
    🛡️ <b>ضمان الأمان والاسترجاع 100%:</b><br>
    إذا لم تكتمل المقاعد الستة خلال <b>24 ساعة</b>، يُسترد كامل المبلغ إلى حسابك البنكي تلقائياً وفوراً دون أي خصم.
</div>
""", unsafe_allow_html=True)

# بطاقات المقاعد
st.markdown(f"<div style='font-weight:800; font-size:0.9em; margin: 4px 0 8px 0;'>🛒 مقاعد سلة جدة ({taken_count}/{BASKET_CAPACITY}) — متبقي {slots_left} مقاعد فقط:</div>", unsafe_allow_html=True)

slots_html = []
for i in range(BASKET_CAPACITY):
    if i < taken_count:
        item = confirmed_orders[i]
        c_name = html.escape(item['name'].split()[0])
        p_name = html.escape(item.get('level', 'عطر محجوز'))
        is_paid = item.get('payment_status') == 'paid'
        status_txt = "تم التأكيد ✅" if is_paid else "بانتظار التحويل ⏳"
        slots_html.append(
            f'<div class="slot-card slot-taken">'
            f'🧴 <b>{c_name}</b><br>'
            f'<span style="font-size:0.82em; color:#cbd5e1;">{p_name}</span><br>'
            f'<span style="font-size:0.75em; color:{"#34d399" if is_paid else "#fbbf24"};">{status_txt}</span>'
            f'</div>'
        )
    else:
        slots_html.append(
            f'<div class="slot-card slot-empty">'
            f'✨ <b>مقعد #{i+1} شاغر</b><br>'
            f'<span style="font-size:0.8em; color:#94a3b8;">متاح للحجز</span><br>'
            f'<span style="font-size:0.72em; color:#818cf8;">وفر 70% كاش</span>'
            f'</div>'
        )

cards_markup = "".join(slots_html)
st.markdown(f'<div class="slots-grid">{cards_markup}</div>', unsafe_allow_html=True)

# ==============================================================================
# 9. شاشة ما بعد الحجز والدفع
# ==============================================================================
if "deal_booked" in st.session_state:
    b = st.session_state["deal_booked"]
    
    if b.get("is_waitlist", False):
        st.warning(f"⏳ تم تسجيلك في قائمة الانتظار لجدة (ترتيبك: #{b.get('pos', 1)}). سنتواصل معك فور توفر مقعد.")
    else:
        target_epoch_ms = b.get("expire_timestamp", 0)
        memo_code = b['memo_code']
        customer_phone = b['phone']
        total_to_pay = b.get('price', 63)
        delivery_choice = b.get('delivery_type', 'استلام يدوي (الأندلس مول)')
        
        st.markdown(f"""
        <div class="status-card-success">
            <h3 style="color:#10b981; margin:0 0 6px 0; font-size:1.3em;">🎉 تم تثبيت مقعدك مبدئياً!</h3>
            <div style="font-size:0.95em; color:#cbd5e1; margin:4px 0;">
                العطر المحجوز: <b style="color:#ffffff;">{b.get('perfume', '')}</b>
            </div>
            <div style="font-size:0.9em; color:#94a3b8; margin:2px 0;">
                طريقة الاستلام: <b style="color:#38bdf8;">{delivery_choice}</b>
            </div>
            <div style="font-size:1.05em; color:#f8fafc; margin:6px 0;">
                المبلغ المطلوب تحويله: <b style="color:#10b981; font-size:1.4em;">{int(total_to_pay)} ر.س فقط</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="big-code-box">
            <div class="big-code-title">🔑 كود الحجز المرجعي الخاص بك:</div>
            <div class="big-code-val">#{memo_code}</div>
            <div style="font-size:0.75em; color:#38bdf8;">(انسخ الكود وضعه في ملاحظات التحويل البنكي)</div>
        </div>
        """, unsafe_allow_html=True)
        st.code(memo_code, language=None)

        st.markdown(f"""
        <div class="alert-instruction">
            ⚠️ <b>خطوة تثبيت المقعد:</b><br>
            قم بتحويل <b>({int(total_to_pay)} ر.س)</b> للحساب أدناه مع كتابة كود الحجز في الملاحظات، ثم أرسل الإشعار عبر الواتساب لاعتماده فوراً. 
            <i>(لو لم تكتمل السلة، يُسترد المبلغ تلقائياً لحسابك خلال 24 ساعة)</i>.
        </div>
        """, unsafe_allow_html=True)
        
        components.html(f"""
        <!DOCTYPE html>
        <div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(239, 68, 68, 0.15); border: 1.5px solid #ef4444; border-radius: 10px; padding: 6px; color: #fca5a5; margin: 4px auto;">
            <span style="font-size: 13px; font-weight: 800;">⏱️ مهلة تثبيت الحصة عبر التحويل: </span>
            <span id="big_pay_timer" style="font-family: monospace; font-size: 20px; color: #ef4444; font-weight: 900;">--:--</span>
        </div>
        <script>
            var payTarget = {target_epoch_ms};
            function updatePayTimer() {{
                var diff = payTarget - new Date().getTime();
                var el = document.getElementById('big_pay_timer');
                if (!el) return;
                if (diff <= 0) {{
                    el.innerHTML = "00:00";
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
        
        st.markdown(f"##### 💳 الحساب البنكي المعتمد ({ACCOUNT_NAME}):")
        st.code(IBAN_NUMBER, language=None)
        
        wa_msg = (
            f"مرحباً يا غالي 🛍️\n"
            f"حجزت مقعدي في سلة عطور درعة (جدة):\n\n"
            f"👤 الاسم: {b['name']}\n"
            f"📱 الجوال: {customer_phone}\n"
            f"🔖 كود الحجز: #{memo_code}\n"
            f"🧴 العطر: {b.get('perfume', '')}\n"
            f"📍 الاستلام: {delivery_choice}\n"
            f"💵 المبلغ: {int(total_to_pay)} ر.س\n\n"
            f"مرفق إشعار التحويل البنكي لتأكيد المقعد!"
        )
        wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتأكيد المقعد عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 10. نموذج الحجز واختيار العطر وطريقة الاستلام (تم إصلاح واستكمال السطر المنقطع)
# ==============================================================================
else:
    is_waitlist = (slots_left == 0)
    
    st.markdown("##### 1. اختر عِطرك من العرض (خصم 70%):")
    
    perfume_display_options = [
        f"{name} — [وفرت 147 ر.س]"
        for name, data in PERFUMES_CATALOG.items()
    ]
    
    chosen_perfume_str = st.selectbox(
        "العطور المشمولة:",
        perfume_display_options,
        label_visibility="collapsed"
    )
    
    chosen_perfume_name = chosen_perfume_str.split(" — ")[0]
    perfume_info = PERFUMES_CATALOG[chosen_perfume_name]
    
    # اكتمال السطر المنقطع سابقاً
    if "last_selected_perfume" not in st.session_state or st.session_state["last_selected_perfume"] != chosen_perfume_name:
        st.session_state["last_selected_perfume"] = chosen_perfume_name
        log_event("perfume_selected", chosen_perfume_name)
    
    st.markdown(f"""
    <div class="perfume-details-card">
        🌿 <b>النوتات العطرية:</b> {perfume_info['notes']}<br>
        🎯 <b>الطابع والمناسبة:</b> {perfume_info['character']}<br>
        💰 <b>الحسبة:</b> سعر المعرض {perfume_info['store_price']} ر.س ➔ سعرك بالقطة <b>{perfume_info['share_price']} ر.س فقط</b> (وفرت 70% كاش!)
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("perfume_deal_form"):
        st.markdown("##### 2. طريقة الاستلام وبياناتك:")
        
        delivery_mode = st.radio(
            "حدد طريقة الاستلام المفضلة بجدة:",
            [
                "استلام يدوي مجاناً (الأندلس مول) — 63 ر.س فقط",
                "خزانة RedBox الذكية (+25 ر.س) — 88 ر.س شامل التوصيل"
            ]
        )
        
        is_redbox_selected = "RedBox" in delivery_mode
        active_price = 88.0 if is_redbox_selected else 63.0
        
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
        
        f_loc = ""
        if is_redbox_selected:
            f_loc = st.text_input("الحي المفضل لخزانة RedBox بجدة:", placeholder="مثال: الروضة، الزهراء، الصفا...")
        
        btn_caption = f"تثبيت المقعد ({int(active_price)} ر.س) 🛍️" if not is_waitlist else "انضم لقائمة الانتظار ⏳"
        
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(btn_caption, use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05.")
            elif is_redbox_selected and not f_loc.strip():
                st.error("فضلاً حدد اسم الحي لاستلام شحنة RedBox.")
            else:
                try:
                    c_active, w_active = process_basket_orders(BASKET_ID)
                    
                    if any(item["phone"] == clean_phone for item in c_active):
                        st.warning("أنت مسجل ومقعدك محجوز بالفعل في هذه السلة!")
                    elif any(item["phone"] == clean_phone for item in w_active):
                        st.warning("أنت مسجل مسبقاً في قائمة الانتظار!")
                    else:
                        memo_id = f"PRF-{clean_phone[-4:]}"
                        delivery_str = f"RedBox ({f_loc.strip()})" if is_redbox_selected else "استلام الأندلس مول"
                        stored_note = f"PERFUME:{chosen_perfume_name} | METHOD:{delivery_str} | PRICE:{int(active_price)} | PHONE:{clean_phone}"
                        
                        if len(c_active) < BASKET_CAPACITY:
                            now_utc = datetime.now(timezone.utc)
                            expire_dt = now_utc + timedelta(minutes=15)
                            
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": chosen_perfume_name,
                                "status": "confirmed",
                                "payment_status": "pending",
                                "expires_at": expire_dt.isoformat(),
                                "hear_about": delivery_str[:25],
                                "player_note": stored_note
                            }).execute()
                            
                            log_event("slot_booked_pending", f"{chosen_perfume_name} | {active_price} SAR | {clean_phone}")
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": chosen_perfume_name,
                                "delivery_type": delivery_str,
                                "price": active_price,
                                "memo_code": memo_id,
                                "is_waitlist": False,
                                "expire_timestamp": int(expire_dt.timestamp() * 1000)
                            }
                            st.rerun()
                        else:
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": chosen_perfume_name,
                                "status": "waitlist",
                                "payment_status": "unpaid",
                                "hear_about": delivery_str[:25],
                                "player_note": stored_note
                            }).execute()
                            
                            log_event("waitlist_joined", clean_phone)
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": chosen_perfume_name,
                                "delivery_type": delivery_str,
                                "price": active_price,
                                "memo_code": memo_id,
                                "is_waitlist": True,
                                "pos": len(w_active) + 1
                            }
                            st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {ex}")

# ==============================================================================
# 11. لوحة الإدارة وقمع التحويل (Admin Funnel)
# ==============================================================================
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة وقمع التحويل"):
    admin_pin = st.text_input("رمز الدخول الإداري:", type="password", key="admin_pwd_input")
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        st.success("🔓 تم فتح لوحة التحكم.")
        
        try:
            logs = supabase.table("site_analytics").select("*").execute().data or []
            total_views = len([l for l in logs if l["event_name"] == "page_view"])
            perf_clicks = len([l for l in logs if l["event_name"] == "perfume_selected"])
            
            all_b = supabase.table("bookings").select("*").eq("session_day", BASKET_ID).execute().data or []
            total_registered = len(all_b)
            paid_count = len([b for b in all_b if b.get("payment_status") == "paid"])
            expired_unpaid = len([b for b in all_b if b.get("status") == "cancelled"])
            
            st.markdown("### 📊 قمع تحويل العملاء (جدة):")
            c1, c2, c3 = st.columns(3)
            c1.metric("👀 الزيارات", total_views)
            c2.metric("🧴 تصفح العطور", perf_clicks)
            c3.metric("📝 الحجوزات", total_registered)
            
            c4, c5 = st.columns(2)
            c4.metric("✅ تأكيد الدفع", paid_count)
            c5.metric("⏳ تسرب دون تحويل", expired_unpaid)
            
            if total_registered > 0:
                drop_rate = (expired_unpaid / total_registered) * 100
                st.caption(f"📉 نسبة التسرب بعد الحجز: **{drop_rate:.1f}%**")
                
        except Exception:
            st.warning("تعذر تحميل أرقام التحليلات حالياً.")
            
        st.markdown("---")
        st.markdown("##### 👥 متابعة سلة جدة الحالية:")
        c_list, _ = process_basket_orders(BASKET_ID)
        for row in c_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{row['name']}** - `{row.get('level', '-')}`\n`{row.get('hear_about', '-')}`\n`{row['phone']}`")
            if row['payment_status'] == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                if col3.button("اعتماد", key=f"pay_perf_{row['id']}"):
                    supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                    log_event("payment_confirmed_admin", row['phone'])
                    st.rerun()
