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
    page_title="مَقسوم جدة | قطة عطور درعة",
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
# 3. أنماط الواجهة (CSS محسّن مع لافتات الندرة والموقع)
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

/* شريط التنبيه العلوي العاجل */
.urgent-banner {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(185, 28, 28, 0.4) 100%);
    border: 1px solid #ef4444;
    border-radius: 12px;
    padding: 8px 12px;
    text-align: center;
    font-size: 0.82em;
    font-weight: 800;
    color: #fecaca;
    margin-bottom: 10px;
}

/* بطاقة الهيدر الرئيسية */
.hero-box {
    background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
    border: 1px solid #4338ca;
    border-radius: 16px;
    padding: 16px 14px;
    text-align: center;
    margin-bottom: 12px;
    box-shadow: 0 8px 24px rgba(67, 56, 202, 0.2);
}
.location-badge {
    background: rgba(14, 165, 233, 0.2);
    color: #38bdf8;
    border: 1px solid #0284c7;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78em;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 6px;
}
.hero-title { font-size: 1.45em; font-weight: 900; color: #ffffff; margin: 0 0 6px 0; }
.hero-desc { font-size: 0.85em; color: #cbd5e1; line-height: 1.5; margin-bottom: 10px; }

/* بطاقة الأسعار الواضحة */
.price-breakdown {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-top: 10px;
}
.price-item { text-align: center; }
.price-item .val { font-size: 1.25em; font-weight: 900; color: #38bdf8; }
.price-item .lbl { font-size: 0.72em; color: #94a3b8; }
.price-divider { color: #475569; font-weight: 300; font-size: 1.3em; }

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

/* صندوق الضمان المالي */
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

/* بطاقات المقاعد */
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
div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
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
    st.error("تعذر الاتصال بقاعدة البيانات. تأكد من إعداد Secrets.")
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
    log_event("page_view", "زيارة جديدة - جدة")
    st.session_state["page_view_logged"] = True

# ==============================================================================
# 6. كتالوج العطور والتسعير
# ==============================================================================
BASKET_ID = "MAQSOOM-JEDDAH-01"
BASKET_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")

PERFUMES_CATALOG = {
    "عطر ليدر (Leader)": {
        "store_price": 210,
        "share_price": 63,
        "notes": "جلود فاخرة، أخشاب الأرز، وتوابل دافئة",
        "character": "فخم ورسمي جداً للمناسبات وساعات الدوام"
    },
    "عطر بورموا (Pour Moi)": {
        "store_price": 210,
        "share_price": 63,
        "notes": "فانيلا فرنسية، عنبر ناعم، وزهور بيضاء",
        "character": "سويت جذاب ومريح للاستخدام اليومي"
    },
    "عطر لينك الأسود (Link Black)": {
        "store_price": 210,
        "share_price": 63,
        "notes": "برغموت إيطالي، حمضيات فواحة، مسك نقي",
        "character": "منعش، فواح، ويعطيك طاقة صباحية متجددة"
    },
    "عطر خواطر (Khawater)": {
        "store_price": 210,
        "share_price": 63,
        "notes": "باتشولي هادئ، نفحات عود خفيف، وقاعدة عنبرية",
        "character": "طابع شرقي كلاسيكي بثبات وفوحان عالي للمجالس"
    },
    "عطر سول (Soul)": {
        "store_price": 210,
        "share_price": 63,
        "notes": "هيل عطري، خزامى برية، وخشب الصندل الدافئ",
        "character": "عصري وشبابي ملفت للطلعات واللقاءات"
    },
    "عطر ميس درعة (Miss Deraah)": {
        "store_price": 210,
        "share_price": 63,
        "notes": "زهور الياسمين، فواكه حمراء، بودرة ومسك ناعم",
        "character": "ناعم وهادئ، خيار أنيق وراقي جداً"
    }
}

PERFUME_SHARE = 63.0             # قيمة العطر الصافية داخل السلة
REDBOX_FEE = 25.0                # رسوم خزانة RedBox بجدة
TOTAL_SLOT_PRICE = PERFUME_SHARE + REDBOX_FEE  # 88 ر.س الإجمالي الشامل

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
# شريط انتهاء العرض العاجل
st.markdown("""
<div class="urgent-banner">
    ⏳ <b>تنبيه:</b> متبقي <b>4 أيام فقط</b> على انتهاء عرض درعة الكبرى وإغلاق السلة!
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero-box">
    <div class="location-badge">📍 حصرياً لمدينة جدة • خزانة RedBox</div>
    <div class="hero-title">قطّة عطور درعة (1+2 مجاناً)</div>
    <div class="hero-desc">
        نجمّع 6 مشترين من <b>جدة</b> للاستفادة من عرض درعة الكبرى بأعلى نسبة توفير؛ عِطرك الأصلي بسعر الجملة الصافي.
    </div>
    <div class="price-breakdown">
        <div class="price-item">
            <div class="val">63 ر.س</div>
            <div class="lbl">العطر (بدل 210)</div>
        </div>
        <div class="price-divider">+</div>
        <div class="price-item">
            <div class="val">25 ر.س</div>
            <div class="lbl">خزانة RedBox بجدة</div>
        </div>
        <div class="price-divider">=</div>
        <div class="price-item">
            <div class="val" style="color:#10b981;">88 ر.س</div>
            <div class="lbl">الإجمالي الشامل</div>
        </div>
    </div>
</div>

<div class="steps-container">
    <div class="step-item active"><b>1. اختر عطرك</b><br>من التشكيلة الذهبية</div>
    <div class="step-item"><b>2. حوّل حصتك</b><br>تثبيت المقعد (88 ر.س)</div>
    <div class="step-item"><b>3. استلم بجدة</b><br>عبر أقرب خزانة لك</div>
</div>

<div class="guarantee-box">
    🛡️ <b>ضمان الأمان والاسترجاع 100%:</b><br>
    إذا لم تكتمل المقاعد الستة خلال <b>24 ساعة</b>، يُسترد كامل المبلغ إلى حسابك البنكي تلقائياً وبشكل فوري دون أي خصومات.
</div>
""", unsafe_allow_html=True)

# بطاقات المقاعد
st.markdown(f"<div style='font-weight:800; font-size:0.9em; margin: 4px 0 8px 0;'>🛒 مقاعد سلة جدة ({taken_count}/{BASKET_CAPACITY}) — متبقي {slots_left} فقط:</div>", unsafe_allow_html=True)

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
            f'<span style="font-size:0.72em; color:#818cf8;">88 ر.س شامل RedBox</span>'
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
        
        st.markdown(f"""
        <div class="status-card-success">
            <h3 style="color:#10b981; margin:0 0 6px 0; font-size:1.3em;">🎉 تم تثبيت مقعدك مبدئياً!</h3>
            <div style="font-size:0.95em; color:#cbd5e1; margin:4px 0;">
                العطر المحجوز: <b style="color:#ffffff;">{b.get('perfume', '')}</b>
            </div>
            <div style="font-size:1.05em; color:#f8fafc; margin:6px 0;">
                المبلغ المطلوب تحويله: <b style="color:#10b981; font-size:1.35em;">{int(TOTAL_SLOT_PRICE)} ر.س</b>
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

        st.markdown("""
        <div class="alert-instruction">
            ⚠️ <b>خطوة تثبيت المقعد:</b><br>
            قم بتحويل (88 ر.س) للحساب أدناه مع كتابة كود الحجز في الملاحظات، ثم أرسل الإشعار عبر الواتساب لاعتماده فوراً. 
            <i>(إذا لم تكتمل السلة، يُسترد المبلغ تلقائياً خلال 24 ساعة)</i>.
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
            f"📍 حي الاستلام بجدة: {b.get('redbox_loc', '')}\n"
            f"💵 المبلغ: {int(TOTAL_SLOT_PRICE)} ر.س\n\n"
            f"مرفق إشعار التحويل البنكي لتأكيد المقعد!"
        )
        wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتأكيد المقعد عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 10. نموذج الحجز واختيار العطر
# ==============================================================================
else:
    is_waitlist = (slots_left == 0)
    btn_text = "انضم لقائمة الانتظار ⏳" if is_waitlist else "تثبيت المقعد (88 ر.س شامل التوصيل بجدة) 🛍️️"
    
    st.markdown("##### 1. اختر عطرك المفضل:")
    
    perfume_display_options = [
        f"{name} — [وفرت {data['store_price'] - data['share_price']} ر.س]"
        for name, data in PERFUMES_CATALOG.items()
    ]
    
    chosen_perfume_str = st.selectbox(
        "العطور المشمولة:",
        perfume_display_options,
        label_visibility="collapsed"
    )
    
    chosen_perfume_name = chosen_perfume_str.split(" — ")[0]
    perfume_info = PERFUMES_CATALOG[chosen_perfume_name]
    
    if "last_selected_perfume" not in st.session_state or st.session_state["last_selected_perfume"] != chosen_perfume_name:
        st.session_state["last_selected_perfume"] = chosen_perfume_name
        log_event("perfume_selected", chosen_perfume_name)
    
    st.markdown(f"""
    <div class="perfume-details-card">
        🌿 <b>النوتات العطرية:</b> {perfume_info['notes']}<br>
        🎯 <b>الطابع والمناسبة:</b> {perfume_info['character']}<br>
        💰 <b>الحسبة:</b> سعر المعرض {perfume_info['store_price']} ر.س ➔ سعر حصتك <b>{perfume_info['share_price']} ر.س فقط</b>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("perfume_deal_form"):
        st.markdown("##### 2. بيانات المستلم (جدة فقط):")
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال لتلقي كود استلام RedBox:", placeholder="05xxxxxxxx")
        f_redbox = st.text_input("الحي السكني بجدة (لأقرب خزانة RedBox):", placeholder="مثال: الروضة، الزهراء، الصفا، السامر...")
        
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(btn_text, use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05.")
            elif not f_redbox.strip():
                st.error("فضلاً حدد اسم الحي في جدة لتحديد أقرب خزانة RedBox.")
            else:
                try:
                    c_active, w_active = process_basket_orders(BASKET_ID)
                    
                    if any(item["phone"] == clean_phone for item in c_active):
                        st.warning("أنت مسجل بالفعل في هذه السلة!")
                    elif any(item["phone"] == clean_phone for item in w_active):
                        st.warning("أنت مسجل مسبقاً في قائمة الانتظار!")
                    else:
                        memo_id = f"PRF-{clean_phone[-4:]}"
                        stored_note = f"PERFUME:{chosen_perfume_name} | REDBOX_JEDDAH:{f_redbox.strip()} | PHONE:{clean_phone}"
                        
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
                                "hear_about": f"JEDDAH: {f_redbox.strip()[:20]}",
                                "player_note": stored_note
                            }).execute()
                            
                            log_event("slot_booked_pending", f"{chosen_perfume_name} | {clean_phone}")
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": chosen_perfume_name,
                                "redbox_loc": f_redbox.strip(),
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
                                "hear_about": f"JEDDAH: {f_redbox.strip()[:20]}",
                                "player_note": stored_note
                            }).execute()
                            
                            log_event("waitlist_joined", clean_phone)
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": chosen_perfume_name,
                                "redbox_loc": f_redbox.strip(),
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
            col1.write(f"**{row['name']}** - `{row.get('level', '-')}`\n`{row['phone']}`")
            if row['payment_status'] == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                if col3.button("اعتماد", key=f"pay_perf_{row['id']}"):
                    supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                    log_event("payment_confirmed_admin", row['phone'])
                    st.rerun()
