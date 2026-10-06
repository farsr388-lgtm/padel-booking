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
    page_icon="🛍️️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع الجلسات ونشاط الزوار
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
# 2. أنماط الواجهة (CSS محسّن وسريع)
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

.status-card-success {
    background: rgba(16, 185, 129, 0.12);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 18px 14px;
    text-align: center;
    margin-top: 8px;
}
.pay-amount-box {
    background: #0f172a;
    border: 2px solid #10b981;
    border-radius: 12px;
    padding: 14px 10px;
    margin: 10px 0;
    text-align: center;
}
.pay-amount-val {
    font-family: monospace;
    font-size: 2.1em;
    font-weight: 900;
    color: #10b981;
}
.pay-method-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid #475569;
    border-radius: 10px;
    padding: 10px;
    margin: 8px 0;
    text-align: right;
    font-size: 0.85em;
    line-height: 1.6;
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
# 3. الاتصال بقاعدة البيانات
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
    st.error("تعذر الاتصال بقاعدة البيانات. تأكد من إعداد Secrets.")
    st.stop()

# ==============================================================================
# 4. إعدادات الحملة وكتالوج العطور
# ==============================================================================
BASKET_ID = "MAQSOOM-JEDDAH-01"
BASKET_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_LOCAL_PHONE = "0566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")

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
ACCOUNT_NAME = "فارس ربيع بن عواض العصيمي"
BANK_NAME = "مصرف الراجحي"

# ==============================================================================
# 5. إدارة المقاعد وتدوير الحجوزات
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
                        "player_note": "انتهاء مهلة السداد (45 دقيقة)"
                    }).eq("id", r["id"]).execute()
                else:
                    confirmed_active.append(r)
                    
        vacancies = BASKET_CAPACITY - len(confirmed_active)
        if vacancies > 0 and waitlist_records:
            to_promote = waitlist_records[:vacancies]
            for wr in to_promote:
                new_exp = (now_utc + timedelta(minutes=45)).isoformat()
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
# 6. الواجهة البصرية المباشرة
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
        نجمّع 6 مشترين من <b>جدة</b> لاقتناص عرض درعة الكبرى؛ تدفع <b>30% فقط</b> من قيمة عِطرك الأصلي 100مل وتوفر 70% كاش.
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

<div class="guarantee-box">
    🛡️ <b>ضمان الأمان والاسترجاع 100%:</b><br>
    إذا لم تكتمل المقاعد الستة خلال <b>24 ساعة</b>، يُسترد كامل المبلغ إلى حسابك البنكي فوراً وتلقائياً دون أي خصم.
</div>
""", unsafe_allow_html=True)

# بطاقات المقاعد الستة
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
# 7. شاشة ما بعد الحجز والدفع
# ==============================================================================
if "deal_booked" in st.session_state:
    b = st.session_state["deal_booked"]
    
    if b.get("is_waitlist", False):
        st.warning(f"⏳ تم تسجيلك في قائمة الانتظار لجد
