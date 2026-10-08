import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة وهوية المنصة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | تقاسم عروض بلوم - مجموعة نيوتن",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع Microsoft Clarity
components.html("""
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window.parent, window.parent.document, "clarity", "script", "ytjnujh8td");
</script>
""", height=0, width=0)

def clean_html(raw: str) -> str:
    return "".join(line.strip() for line in raw.splitlines() if line.strip())

# ==============================================================================
# 2. أنماط الواجهة (Dark Luxury + إعدام اللون الأحمر نهائياً)
# ==============================================================================
css_styles = clean_html("""
<style>
/* إخفاء الهيدر والفوتر وهوامش النظام الافتراضية */
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
    color: #f1f5f9;
}

/* بطاقة الهيدر العلوية */
.top-brand-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
    text-align: center;
}
.brand-badge {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 14px;
    padding: 3px 12px;
    font-size: 0.72em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 6px;
}
.brand-title {
    font-size: 1.25em;
    font-weight: 900;
    color: #ffffff;
    margin: 2px 0;
}
.brand-msg {
    font-size: 0.85em;
    font-weight: 600;
    color: #94a3b8 !important;
    margin-bottom: 10px;
}
.capacity-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78em;
    font-weight: 700;
    margin-bottom: 6px;
}
.progress-bar-bg {
    background: #030712;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    height: 8px;
    width: 100%;
    overflow: hidden;
}
.progress-bar-fill {
    background: linear-gradient(90deg, #059669, #10b981);
    height: 100%;
    border-radius: 6px;
    transition: width 0.4s ease-in-out;
}

/* شبكة اختيار العطور (Radio Grid) */
div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
    width: 100% !important;
    margin-bottom: 10px !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label {
    width: 100% !important;
    margin: 0 !important;
    background-color: #111827 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 10px 8px !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:hover {
    border-color: rgba(16, 185, 129, 0.3) !important;
    background-color: #152033 !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.12) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* استئصال أي نقط أو دوائر حمراء في Radio */
div[data-testid="stRadio"] div[role="radiogroup"] label div:first-child {
    border-color: #475569 !important;
    background-color: transparent !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child,
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] {
    border-color: #10b981 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] div,
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child div {
    background-color: #10b981 !important;
}

/* بطاقة تفاصيل العطر المختار الشاملة (بديل الصور الفني) */
.perfume-details-card {
    background: #111827;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
}
.perfume-details-card .title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.perfume-name {
    font-size: 1.05em;
    font-weight: 800;
    color: #ffffff;
}
.perfume-tag {
    color: #10b981;
    font-size: 0.8em;
    font-weight: 700;
}
.perfume-desc {
    font-size: 0.82em;
    color: #cbd5e1;
    line-height: 1.5;
    margin-bottom: 8px;
}
.perfume-specs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    background: rgba(0, 0, 0, 0.25);
    padding: 8px;
    border-radius: 6px;
    font-size: 0.76em;
    color: #94a3b8;
    margin-bottom: 8px;
}
.perfume-specs span b { color: #f1f5f9; }

.discount-chip {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 6px;
    padding: 6px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8em;
    font-weight: 700;
}

/* حقول الإدخال والنموذج */
form div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
    margin-top: 4px !important;
    margin-bottom: 8px !important;
}
form div[data-testid="stRadio"] div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    margin: 0 !important;
    font-size: 0.84em !important;
}

div[data-testid="stTextInput"] { margin-bottom: 6px !important; }
input, textarea { 
    caret-color: #10b981 !important; 
    border-radius: 8px !important; 
    font-size: 0.88em !important; 
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background-color: #111827 !important;
    color: #ffffff !important;
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within { 
    border-color: #10b981 !important; 
    box-shadow: 0 0 0 1px #10b981 !important; 
}

/* منع أي إطار أحمر عند أخطاء المتصفح الافتراضية */
div[data-baseweb="input"] {
    border-color: rgba(255, 255, 255, 0.12) !important;
}

/* زر التأكيد الأساسي */
div[data-testid="stFormSubmitButton"] > button {
    background: #10b981 !important;
    color: #022c22 !important;
    font-size: 0.95em !important;
    font-weight: 800 !important;
    height: 46px !important;
    border-radius: 8px !important;
    border: none !important;
    margin-top: 4px !important;
    transition: opacity 0.2s ease !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    opacity: 0.95 !important;
}

/* التنبيهات المخصصة */
.custom-alert {
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #fcd34d;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.82em;
    font-weight: 600;
    margin-bottom: 8px;
    text-align: right;
}
.success-card {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid #10b981;
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
    margin-top: 8px;
}
.notice-box {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 12px;
    font-size: 0.82em;
    color: #94a3b8;
    line-height: 1.6;
    margin: 10px 0;
    text-align: center;
}
.wa-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 12px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 0.95em;
    text-decoration: none;
    margin-top: 6px;
}

/* إخفاء مصيدة السبام */
div[data-testid="stTextInput"]:has(input[aria-label="hp"]),
input[aria-label="hp"] { 
    display: none !important; 
    opacity: 0 !important; 
    position: absolute !important; 
    left: -9999px !important; 
}
</style>
""")
st.markdown(css_styles, unsafe_allow_html=True)

# ==============================================================================
# 3. قاعدة البيانات وكتالوج النصوص الوصفية
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
            return None
        url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
        if url.endswith("/rest/v1"):
            url = url[:-8]
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception:
        return None

supabase = get_supabase_client()

BASKET_ID = "BLOM-NEWTON-JEDDAH-V10"
BASKET_CAPACITY = 4
UNIFIED_PRICE = 132
ORIGINAL_RETAIL = 265
SAVINGS_AMOUNT = ORIGINAL_RETAIL - UNIFIED_PRICE
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "")

PERFUMES = {
    "عطر روميو (Romeo)": {
        "tag": "رجالي شرقي فاخر",
        "rating": "4.8 ★",
        "scent_type": "خشبي - أروماتيك دافئ",
        "best_for": "المناسبات واللقاءات الرسمية المسائية",
        "notes": "افتتاحية من الهيل، قلب نابض بالباتشولي الإندونيسي، وقاعدة غنية بالفانيلا المعتقة والمسك.",
        "performance": "ثبات ممتاز 10-12 ساعة | فوحان قوي"
    },
    "عطر يوجا (Yoga)": {
        "tag": "هادئ ومنعش للجنسين",
        "rating": "4.8 ★",
        "scent_type": "حمضي - مسكي نقي",
        "best_for": "الاستخدام اليومي وساعات الصباح والدوام",
        "notes": "افتتاحية منعشة من البرغموت الإيطالي، نرجس أبيض في القلب، وقاعدة مسك قطني نظيف.",
        "performance": "ثبات 7-9 ساعات | فوحان ناعم ومريح"
    },
    "عطر لونار (Lunar)": {
        "tag": "غامض ومميز للجنسين",
        "rating": "4.9 ★",
        "scent_type": "فاكهي - عنبري فخم",
        "best_for": "الأجواء المعتدلة والخرجات المميزة",
        "notes": "ثمار العنب الأسود مع لمحات توتية، تتدرج إلى باتشولي عميق، وتستقر على عنبر دافئ وفخم.",
        "performance": "ثبات متوازن 9-11 ساعة | فوحان واسع الانتشار"
    },
    "عطر لاروزيه (Larose)": {
        "tag": "أنثوي ناعم وساحر",
        "rating": "5.0 ★",
        "scent_type": "زهري - بودري ناعم",
        "best_for": "الاستخدام اليومي والمناسبات الخاصة",
        "notes": "باقة من الياسمين الرقيق والزنبق، ممتزجة مع لمسة فانيلا خفيفة وقاعدة من خشب الصندل.",
        "performance": "ثبات 8-10 ساعات | فوحان زهري آسر"
    },
    "عطر اليسيوم (Elysium)": {
        "tag": "فخامة ملكية وهيبة",
        "rating": "4.9 ★",
        "scent_type": "عنبري - لافندر ملكي",
        "best_for": "الأعراس واللقاءات الكبرى والشتوية",
        "notes": "لافندر فرنسي مهدئ، يتبعه قلب من التوابل الدافئة، وقاعدة راسخة من العنبر الملكي والأخشاب.",
        "performance": "ثبات عالٍ يتجاوز 12 ساعة | فوحان بارز"
    },
    "عطر هارت بيت (Heart Beat)": {
        "tag": "حيوي وجذاب للجنسين",
        "rating": "4.8 ★",
        "scent_type": "زهري - خشبي رومانسي",
        "best_for": "الطلعات المسائية والسهرات الهادئة",
        "notes": "نفحات الكشمش الأسود المنعش ممزوجة ببتلات الورد الجوري، محمولة على مسك مخملي جذاب.",
        "performance": "ثبات 8-10 ساعات | فوحان جذاب وملفت"
    }
}

@st.cache_data(ttl=5)
def get_confirmed_bookings(basket_key: str):
    if not supabase:
        return []
    try:
        return supabase.table("bookings") \
            .select("*") \
            .eq("session_day", basket_key) \
            .neq("status", "cancelled") \
            .order("id") \
            .execute().data or []
    except Exception:
        return []

current_bookings = get_confirmed_bookings(BASKET_ID)
taken_count = len(current_bookings)
slots_left = max(0, BASKET_CAPACITY - taken_count)
progress_percent = int((taken_count / BASKET_CAPACITY) * 100)
status_badge = "متبقي مقعد 1 وتكتمل الباقة 🔥" if slots_left == 1 else f"متبقي {slots_left} مقاعد لاكتمال الباقة"

# ==============================================================================
# 4. واجهة المنصة العلوية
# ==============================================================================
header_html = clean_html(f"""
<div class="top-brand-card">
    <div class="brand-badge">تقاسم العرض الرسمي • باقة نيوتن</div>
    <div class="brand-title">تقاسم عروض بلوم (2 + 2 مجاناً)</div>
    <div class="brand-msg">السعر الأصلي 265 ر.س — احصل عليه بـ {UNIFIED_PRICE} ر.س فقط</div>
    <div class="capacity-row">
        <span style="color:#cbd5e1;">اكتمال باقة المجموعة (4 أشخاص)</span>
        <span style="color:#10b981;">{taken_count} من {BASKET_CAPACITY} مكتملة ({status_badge})</span>
    </div>
    <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width:{progress_percent}%;"></div>
    </div>
</div>
""")
st.markdown(header_html, unsafe_allow_html=True)

# ==============================================================================
# 5. شاشة ما بعد الحجز
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(deal['name'])
    safe_perfume = html.escape(deal['perfume'])
    safe_delivery = html.escape(deal['delivery'])
    
    success_html = clean_html(f"""
    <div class="success-card">
        <h3 style="color:#10b981;margin:0 0 6px 0;font-size:1.2em;">🎉 تم تثبيت حصتك في الباقة بنجاح</h3>
        <div style="font-size:0.92em;color:#e2e8f0;margin-bottom:2px;">العطر: <b>{safe_perfume}</b></div>
        <div style="font-size:0.84em;color:#94a3b8;margin-bottom:6px;">الاستلام: <b>{safe_delivery}</b></div>
        <div style="font-size:1.1em;color:#ffffff;">
            المبلغ المطلوب عند الاستلام: <b style="color:#10b981;">{UNIFIED_PRICE} ر.س</b>
        </div>
    </div>
    <div class="notice-box">
        🤝 <b>الدفع عند الاستلام يد بيد</b><br>
        سنتواصل معك عبر الواتساب فور اكتمال الباقة لتأكيد موعد التسليم وتزويدك بنسخة الفاتورة.
    </div>
    """)
    st.markdown(success_html, unsafe_allow_html=True)
    
    wa_msg = (
        f"مرحباً يا غالي 🌿\n"
        f"سجلت طلبي في تقاسم عرض بلوم - مجموعة نيوتن ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• الاستلام: {deal['delivery']}\n\n"
        f"أرجو تأكيد المقعد واستكمال الباقة."
    )
    wa_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 6. النموذج وشبكة العطور المتقابلة
# ==============================================================================
else:
    st.markdown("<div style='font-size:0.86em;font-weight:800;color:#ffffff;text-align:right;margin-bottom:6px;'>1. حدد عِطرك من مجموعة نيوتن:</div>", unsafe_allow_html=True)
    
    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed"
    )
    
    p = PERFUMES[chosen_perfume]
    preview_html = clean_html(f"""
    <div class="perfume-details-card">
        <div class="title-row">
            <span class="perfume-name">{chosen_perfume}</span>
            <span class="perfume-tag">{p['rating']} • {p['tag']}</span>
        </div>
        <div class="perfume-desc">
            <b>التركيبة العطرية:</b> {p['notes']}
        </div>
        <div class="perfume-specs">
            <span>الخط: <b>{p['scent_type']}</b></span>
            <span>الاستخدام: <b>{p['best_for']}</b></span>
            <span style="grid-column: span 2;">الأداء: <b>{p['performance']}</b></span>
        </div>
        <div class="discount-chip">
            <span style="color:#cbd5e1;">السعر الفردي: <s style="color:#64748b;">{ORIGINAL_RETAIL} ر.س</s> ➔ <b style="color:#10b981;font-size:1.1em;">{UNIFIED_PRICE} ر.س</b></span>
            <span style="color:#10b981;">وفرت {SAVINGS_AMOUNT} ر.س (50% خصم)</span>
        </div>
    </div>
    """)
    st.markdown(preview_html, unsafe_allow_html=True)
    
    with st.form("quick_order_form"):
        st.markdown("<div style='font-size:0.86em;font-weight:800;color:#ffffff;text-align:right;margin-bottom:6px;'>2. بيانات التأكيد والاستلام:</div>", unsafe_allow_html=True)
        
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
        
        delivery_mode = st.radio(
            "طريقة الاستلام والدفع:",
            [
                f"استلام يد بيد (السلام مول) — {UNIFIED_PRICE} ر.س عند الاستلام",
                f"توصيل مجاني داخل جدة — {UNIFIED_PRICE} ر.س عند الاستلام"
            ]
        )
        
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت حصتك في العرض ({UNIFIED_PRICE} ر.س عند الاستلام)", use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.markdown('<div class="custom-alert">⚠️ يرجى التأكد من كتابة الاسم ورقم جوال سعودي يبدأ بـ 05 ويتكون من 10 أرقام.</div>', unsafe_allow_html=True)
            else:
                fresh_bookings = get_confirmed_bookings(BASKET_ID)
                if len(fresh_bookings) >= BASKET_CAPACITY:
                    st.markdown('<div class="custom-alert">🔔 اكتملت هذه الباقة بالكامل، انتظر لحظات لفتح باقة جديدة.</div>', unsafe_allow_html=True)
                else:
                    try:
                        client_note = f"BLOM_NEWTON | {chosen_perfume} | {delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"
                        
                        if supabase:
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": chosen_perfume,
                                "status": "confirmed",
                                "payment_status": "pending",
                                "hear_about": delivery_mode[:30],
                                "player_note": client_note
                            }).execute()
                        
                        st.cache_data.clear()
                        st.session_state["confirmed_deal"] = {
                            "name": clean_name,
                            "phone": clean_phone,
                            "perfume": chosen_perfume,
                            "delivery": delivery_mode,
                            "price": UNIFIED_PRICE
                        }
                        st.rerun()
                    except Exception:
                        st.markdown('<div class="custom-alert">⚠️ تعذر الاتصال بالنظام حالياً، يرجى المحاولة بعد لحظات.</div>', unsafe_allow_html=True)

# ==============================================================================
# 7. بوابة المشرف المعزولة
# ==============================================================================
query_params = st.query_params
if query_params.get("manage") == "faris":
    st.markdown("---")
    st.subheader("⚙️ بوابة الإدارة والمتابعة")
    admin_pin = st.text_input("رمز المرور:", type="password", key="admin_isolated_key")
    
    if admin_pin and ADMIN_PASSWORD_HASH and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        st.success("تم الدخول بنجاح.")
        
        with st.form("manual_add_admin_form"):
            st.markdown("##### ➕ إضافة حصة يدوية:")
            m_name = st.text_input("الاسم:")
            m_phone = st.text_input("الجوال:")
            m_perf = st.selectbox("العطر:", list(PERFUMES.keys()))
            m_paid = st.checkbox("مدفوع ومؤكد ✅", value=True)
            
            if st.form_submit_button("تأكيد الإضافة"):
                if m_name and m_phone and supabase:
                    st_p = "paid" if m_paid else "pending"
                    supabase.table("bookings").insert({
                        "name": m_name.strip(),
                        "phone": m_phone.strip(),
                        "session_day": BASKET_ID,
                        "court": 1,
                        "level": m_perf,
                        "status": "confirmed",
                        "payment_status": st_p,
                        "hear_about": "إضافة يدوية",
                        "player_note": f"MANUAL | {m_perf} | PRICE:{UNIFIED_PRICE}"
                    }).execute()
                    st.cache_data.clear()
                    st.success("تمت الإضافة بنجاح.")
                    st.rerun()
        
        st.markdown("##### 👥 الحصص الحالية:")
        bookings_list = get_confirmed_bookings(BASKET_ID)
        for b in bookings_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{b.get('name')}** - `{b.get('level', '-')}`\n`{b.get('phone')}`")
            if b.get('payment_status') == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#38bdf8; font-weight:700;'>محجوز 🔒</span>", unsafe_allow_html=True)
                if col3.button("اعتماد دفع", key=f"pay_adm_{b.get('id')}"):
                    if supabase:
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", b.get('id')).execute()
                    st.cache_data.clear()
                    st.rerun()
