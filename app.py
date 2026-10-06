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
        st.warning(f"⏳ تم تسجيلك في قائمة الانتظار لجدة (ترتيبك: #{b.get('pos', 1)}). سنتواصل معك فور توفر مقعد.")
    else:
        target_epoch_ms = b.get("expire_timestamp", 0)
        customer_phone = b['phone']
        exact_price = b.get('price', 63.0)
        delivery_choice = b.get('delivery_type', 'استلام يدوي (الأندلس مول)')
        sender_account = b.get('sender_bank', 'غير محدد')
        
        st.markdown(f"""
        <div class="status-card-success">
            <h3 style="color:#10b981; margin:0 0 4px 0; font-size:1.3em;">🎉 تم حجز مقعدك بنجاح!</h3>
            <div style="font-size:0.95em; color:#cbd5e1; margin:4px 0;">
                العطر المحجوز: <b style="color:#ffffff;">{b.get('perfume', '')}</b>
            </div>
            <div style="font-size:0.88em; color:#94a3b8; margin:2px 0;">
                طريقة الاستلام: <b style="color:#38bdf8;">{delivery_choice}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="pay-amount-box">
            <div style="font-size:0.85em; color:#94a3b8; margin-bottom:4px;">المبلغ المطلوب تحويله لتأكيد مقعدك:</div>
            <div class="pay-amount-val">{int(exact_price)} ر.س</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="pay-method-card">
            ⚡ <b>خيار 1: التحويل السريع برقم الجوال (سريع):</b><br>
            • رقم الجوال: <b style="color:#38bdf8; font-family:monospace; font-size:1.1em;">{ADMIN_LOCAL_PHONE}</b><br>
            • المستفيد: <b>{ACCOUNT_NAME}</b>
        </div>
        <div class="pay-method-card">
            🏦 <b>خيار 2: التحويل عبر الآيبان ({BANK_NAME}):</b><br>
            • المستفيد: <b>{ACCOUNT_NAME}</b>
        </div>
        """, unsafe_allow_html=True)
        st.code(IBAN_NUMBER, language=None)
        
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
        
        wa_msg = (
            f"مرحباً يا غالي 🛍️\n"
            f"حجزت مقعدي في سلة درعة (جدة):\n\n"
            f"👤 الاسم: {b['name']}\n"
            f"📱 الجوال: {customer_phone}\n"
            f"🧴 العطر: {b.get('perfume', '')}\n"
            f"📍 الاستلام: {delivery_choice}\n"
            f"💵 المبلغ المحول: {int(exact_price)} ر.س\n\n"
            f"مرفق إشعار التحويل لتأكيد المقعد بالسلة!"
        )
        wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتأكيد المقعد عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 8. نموذج الحجز واختيار العطر
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
        f_bank_sender = st.text_input("اسم صاحب الحساب اللي بتحول منه (لتأكيد فوري):", placeholder="اسم المحول البنكي")
        
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
                        delivery_str = f"RedBox ({f_loc.strip()})" if is_redbox_selected else "استلام الأندلس مول"
                        sender_str = f_bank_sender.strip() if f_bank_sender.strip() else "غير محدد"
                        stored_note = f"PERFUME:{chosen_perfume_name} | METHOD:{delivery_str} | PRICE:{int(active_price)} | SENDER:{sender_str} | PHONE:{clean_phone}"
                        
                        if len(c_active) < BASKET_CAPACITY:
                            now_utc = datetime.now(timezone.utc)
                            expire_dt = now_utc + timedelta(minutes=45)
                            
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
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": chosen_perfume_name,
                                "delivery_type": delivery_str,
                                "price": active_price,
                                "sender_bank": sender_str,
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
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": chosen_perfume_name,
                                "delivery_type": delivery_str,
                                "price": active_price,
                                "sender_bank": sender_str,
                                "is_waitlist": True,
                                "pos": len(w_active) + 1
                            }
                            st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {ex}")

# ==============================================================================
# 9. لوحة الإدارة (مع ميزة إضافة الحجوزات اليدوية مباشرة)
# ==============================================================================
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة"):
    admin_pin = st.text_input("رمز الدخول الإداري:", type="password", key="admin_pwd_input")
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        st.success("🔓 تم فتح لوحة التحكم.")
        
        # نموذج إضافة حجز يدوي مباشر
        with st.form("manual_booking_form"):
            st.markdown("##### ➕ إضافة مقعد يدوياً (حجزك الشخصي أو حوالة بنكية):")
            m_name = st.text_input("الاسم:", placeholder="مثال: فارس العصيمي أو اسم المحول")
            m_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
            m_perf = st.selectbox("العطر المختار:", list(PERFUMES_CATALOG.keys()))
            m_del = st.selectbox("طريقة الاستلام:", ["استلام الأندلس مول", "خزانة RedBox"])
            m_paid = st.checkbox("الحوالة مستلمة (مدفوع ومؤكد ✅)", value=True)
            
            if st.form_submit_button("تثبيت المقعد بالسلة فوراً"):
                if m_name and m_phone:
                    st_p = "paid" if m_paid else "pending"
                    note = f"PERFUME:{m_perf} | METHOD:{m_del} | SENDER:يدوي | PHONE:{m_phone}"
                    supabase.table("bookings").insert({
                        "name": m_name.strip(),
                        "phone": m_phone.strip(),
                        "session_day": BASKET_ID,
                        "court": 1,
                        "level": m_perf,
                        "status": "confirmed",
                        "payment_status": st_p,
                        "hear_about": m_del[:25],
                        "player_note": note
                    }).execute()
                    st.success("تم تثبيت المقعد بنجاح بالسلة!")
                    st.rerun()
                else:
                    st.error("يرجى كتابة الاسم ورقم الجوال.")

        st.markdown("---")
        st.markdown("##### 👥 متابعة واعتماد مقاعد السلة:")
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
                    st.rerun()
