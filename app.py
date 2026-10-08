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
    page_title="مَقسوم | Blom Newton Collection",
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

# دالة هندسية لحماية الـ HTML من خطأ المسافات البادئة في ستريمليت
def clean_html(raw: str) -> str:
    return "".join(line.strip() for line in raw.splitlines() if line.strip())

# ==============================================================================
# 2. تحديد اللغة (العربية / English)
# ==============================================================================
if "lang" not in st.session_state:
    st.session_state["lang"] = "ar"

col_spacer, col_lang = st.columns([3, 1.3])
with col_lang:
    lang_toggle = st.radio(
        "Lang",
        ["العربية", "English"],
        index=0 if st.session_state["lang"] == "ar" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="lang_toggle_btn"
    )
    st.session_state["lang"] = "ar" if lang_toggle == "العربية" else "en"

is_ar = (st.session_state["lang"] == "ar")
dir_css = "rtl" if is_ar else "ltr"
align_css = "right" if is_ar else "left"

# ==============================================================================
# 3. أنماط الواجهة الثنائية (Two-Tone System & 3v3 Grid)
# ==============================================================================
css_styles = clean_html(f"""
<style>
header[data-testid="stHeader"], #MainMenu, footer {{ display: none !important; }}

.block-container {{ 
    padding-top: 0.3rem !important; 
    padding-bottom: 1.5rem !important; 
    max-width: 420px !important; 
    margin: 0 auto; 
}}

html, body, [class*="css"] {{ 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: {dir_css}; 
    text-align: {align_css}; 
    background-color: #0b0f19;
    color: #f1f5f9;
}}

/* محول اللغة */
div[data-testid="stRadio"]:has(input[name*="lang_toggle_btn"]) > div[role="radiogroup"] {{
    display: flex !important;
    gap: 3px !important;
    background: #111827 !important;
    padding: 2px !important;
    border-radius: 8px !important;
    border: 1px solid #1f2937 !important;
}}
div[data-testid="stRadio"]:has(input[name*="lang_toggle_btn"]) label {{
    padding: 2px 7px !important;
    font-size: 0.7em !important;
    border-radius: 5px !important;
    border: none !important;
    background: transparent !important;
}}
div[data-testid="stRadio"]:has(input[name*="lang_toggle_btn"]) label:has(input:checked) {{
    background: #10b981 !important;
    color: #022c22 !important;
    font-weight: 800 !important;
}}

/* -------------------------------------------------------------------------- */
/* الصندوق العلوي المدمج (العنوان + سعة السلة بالأعلى بدون صندوق السعر القديم)   */
/* -------------------------------------------------------------------------- */
.top-brand-card {{
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
    text-align: center;
}}
.brand-badge {{
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 14px;
    padding: 2px 10px;
    font-size: 0.72em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 4px;
}}
.brand-title {{
    font-size: 1.22em;
    font-weight: 900;
    color: #ffffff;
    margin: 2px 0;
}}
.brand-msg {{
    font-size: 0.86em;
    font-weight: 700;
    color: #ffffff !important;
    margin-bottom: 10px;
}}
.capacity-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.76em;
    font-weight: 700;
    margin-bottom: 4px;
}}
.progress-bar-bg {{
    background: #0b0f19;
    border: 1px solid #1f2937;
    border-radius: 6px;
    height: 7px;
    width: 100%;
    overflow: hidden;
    margin-bottom: 4px;
}}
.progress-bar-fill {{
    background: #10b981;
    height: 100%;
    border-radius: 6px;
}}

/* -------------------------------------------------------------------------- */
/* شبكة العطور الستة: عمودان متقابلان (3 ضد 3) جنباً إلى جنب                    */
/* -------------------------------------------------------------------------- */
div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]):not(:has(input[name*="lang_toggle_btn"])) div[role="radiogroup"] {{
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
}}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]):not(:has(input[name*="lang_toggle_btn"])) div[role="radiogroup"] > label {{
    width: 100% !important;
    margin: 0 !important;
    background-color: #111827 !important;
    border: 1.5px solid #1f2937 !important;
    border-radius: 8px !important;
    padding: 8px 6px !important;
    min-height: 42px !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    transition: all 0.15s ease-in-out !important;
}}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]):not(:has(input[name*="lang_toggle_btn"])) div[role="radiogroup"] > label:hover {{
    border-color: #334155 !important;
    background-color: #141e33 !important;
}}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]):not(:has(input[name*="lang_toggle_btn"])) div[role="radiogroup"] > label:has(input:checked) {{
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.12) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}}

/* استئصال اللون الأحمر من التحديدات */
div[data-testid="stRadio"] div[role="radiogroup"] label div:first-child {{
    border-color: #475569 !important;
    background-color: transparent !important;
}}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child,
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] {{
    border-color: #10b981 !important;
}}
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] div,
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child div {{
    background-color: #10b981 !important;
}}

/* -------------------------------------------------------------------------- */
/* كرت العطر المختار مع السعر المباشر والخصم                                  */
/* -------------------------------------------------------------------------- */
.selected-perfume-panel {{
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 8px 10px;
    margin-bottom: 6px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}}
.perfume-flex-row {{
    display: flex;
    gap: 10px;
    align-items: center;
}}
.perfume-thumb {{
    width: 62px;
    height: 62px;
    border-radius: 8px;
    background: #0f172a;
    border: 1px solid #1e293b;
    object-fit: cover;
    flex-shrink: 0;
}}
.perfume-meta {{
    flex: 1;
    font-size: 0.78em;
    line-height: 1.4;
    color: #cbd5e1;
}}
.discount-chip {{
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 6px;
    padding: 5px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.74em;
    font-weight: 700;
}}

/* خيارات الاستلام ونموذج الطلب */
div[data-testid="stForm"] div[data-testid="stRadio"] div[role="radiogroup"] {{
    display: flex !important;
    flex-direction: column !important;
    gap: 5px !important;
    margin-bottom: 6px !important;
}}
div[data-testid="stForm"] div[data-testid="stRadio"] div[role="radiogroup"] > label {{
    background-color: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 8px !important;
    padding: 7px 10px !important;
    margin: 0 !important;
    font-size: 0.82em !important;
}}
div[data-testid="stTextInput"] {{ margin-bottom: 5px !important; }}
input, textarea {{ 
    caret-color: #10b981 !important; 
    border-radius: 8px !important;
    font-size: 0.88em !important;
}}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within {{
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}}
div[data-testid="stFormSubmitButton"] > button {{
    background: #10b981 !important;
    color: #022c22 !important;
    font-size: 1em !important;
    font-weight: 800 !important;
    height: 45px !important;
    border-radius: 8px !important;
    border: none !important;
    margin-top: 2px !important;
}}
.success-card {{
    background: rgba(16, 185, 129, 0.1);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
    margin-top: 8px;
}}
.notice-box {{
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 10px;
    font-size: 0.8em;
    color: #94a3b8;
    line-height: 1.5;
    margin: 8px 0;
    text-align: center;
}}
.wa-btn {{
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
}}
div[data-testid="stTextInput"]:has(input[aria-label="hp"]),
input[aria-label="hp"] {{ 
    display: none !important; 
    opacity: 0 !important;
    position: absolute !important;
    left: -9999px !important;
}}
</style>
""")
st.markdown(css_styles, unsafe_allow_html=True)

# ==============================================================================
# 4. الربط بقاعدة البيانات والكتالوج والترجمات
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
        if url.endswith("/rest/v1"):
            url = url[:-8]
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception:
        return None

supabase = get_supabase_client()

BASKET_ID = "BLOM-NEWTON-JEDDAH-V8"
BASKET_CAPACITY = 4
UNIFIED_PRICE = 132
ORIGINAL_RETAIL = 265
SAVINGS_AMOUNT = ORIGINAL_RETAIL - UNIFIED_PRICE
ADMIN_PHONE = "966566261868"

raw_secret = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")
ADMIN_PASSWORD_HASH = str(raw_secret).strip()

TEXTS = {
    "ar": {
        "badge": "قسم مشترياتك • تقاسم العرض معنا",
        "title": "تقاسم عروض بلوم (2+2 مجاناً)",
        "msg": "تقاسم السعر أنت و 4 أشخاص",
        "capacity_title": "اكتمال باقة نيوتن (4 أشخاص)",
        "left_single": "متبقي مقعد 1 وتكتمل الباقة 🔥",
        "left_multi": "متبقي {n} مقاعد لاكتمال الباقة",
        "currency": "ر.س",
        "step1": "1. اختر عِطرك من مجموعة نيوتن (Newton):",
        "step2": "2. طريقة الاستلام وبياناتك:",
        "opt_mall": f"استلام يد بيد (السلام مول) — {UNIFIED_PRICE} ر.س عند الاستلام",
        "opt_deliv": f"توصيل مجاني داخل جدة — {UNIFIED_PRICE} ر.س عند الاستلام",
        "name_lbl": "الاسم الكريم:",
        "name_ph": "الاسم الثنائي",
        "phone_lbl": "رقم الجوال:",
        "phone_ph": "05xxxxxxxx",
        "btn_submit": f"تثبيت حصتك في العرض ({UNIFIED_PRICE} ر.س عند الاستلام)",
        "err_fields": "يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05.",
        "err_full": "اكتملت الباقة الحالية تماماً، جاري فتح باقة جديدة.",
        "saved_txt": f"وفرت {SAVINGS_AMOUNT} ر.س (خصم 50%)",
        "val_txt": "قيمة العطر:",
        "success_h": "🎉 تم تثبيت حصتك بنجاح!",
        "success_perf": "العطر:",
        "success_deliv": "الاستلام:",
        "success_due": "المطلوب عند الاستلام:",
        "cod_box": "🤝 <b>الدفع عند الاستلام يد بيد</b><br>سنتواصل معك عبر الواتساب فور اكتمال الباقة وتجهيز عِطرك مع الفاتورة.",
        "wa_btn": "📲 تأكيد الحجز والتواصل عبر واتساب",
        "wa_msg_pre": "مرحباً يا غالي 🌿\nسجلت اهتمامي في تقاسم عرض بلوم - مجموعة نيوتن"
    },
    "en": {
        "badge": "Group Buying • Split Deals Together",
        "title": "Blom Perfumes Offer (Buy 2 Get 2 Free)",
        "msg": "Split the cost among 4 people",
        "capacity_title": "Newton Bundle Status (4 Persons)",
        "left_single": "1 spot remaining to complete bundle 🔥",
        "left_multi": "{n} spots remaining to complete bundle",
        "currency": "SAR",
        "step1": "1. Select your Newton fragrance directly:",
        "step2": "2. Delivery & Contact Details:",
        "opt_mall": f"Handover at Al Salam Mall — {UNIFIED_PRICE} SAR on Delivery",
        "opt_deliv": f"Free Delivery in Jeddah — {UNIFIED_PRICE} SAR on Delivery",
        "name_lbl": "Full Name:",
        "name_ph": "Full Name",
        "phone_lbl": "Mobile Number:",
        "phone_ph": "05xxxxxxxx",
        "btn_submit": f"Confirm Your Share ({UNIFIED_PRICE} SAR Cash on Delivery)",
        "err_fields": "Please enter a valid name and Saudi mobile number starting with 05.",
        "err_full": "This bundle is now full! A new bundle will open shortly.",
        "saved_txt": f"You saved {SAVINGS_AMOUNT} SAR (50% Off)",
        "val_txt": "Retail Value:",
        "success_h": "🎉 Your share has been confirmed!",
        "success_perf": "Perfume:",
        "success_deliv": "Delivery:",
        "success_due": "Amount due on delivery:",
        "cod_box": "🤝 <b>Cash on Delivery (In-Person)</b><br>We will message you via WhatsApp once the bundle completes to coordinate delivery with official invoice.",
        "wa_btn": "📲 Confirm via WhatsApp",
        "wa_msg_pre": "Hello 🌿\nI have reserved my spot for Blom Newton offer"
    }
}

t = TEXTS["ar"] if is_ar else TEXTS["en"]

# ترتيب العطور الستة لتظهر متقابلة 3 في اليمين و 3 في اليسار
PERFUMES = {
    # صف 1: روميو (يمين) مقابل يوجا (يسار)
    "عطر روميو (Romeo)": {
        "name": "عطر روميو (Romeo)" if is_ar else "Romeo Perfume",
        "tag": "رجالي فاخر" if is_ar else "Luxury Men's",
        "rating": "4.8 ★",
        "desc": "جاذبية وأناقة رجولية فاخرة" if is_ar else "Masculine luxury allure",
        "notes": "باتشولي، فانيلا، ومسك" if is_ar else "Patchouli, Vanilla, Musk",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=260&q=80"
    },
    "عطر يوجا (Yoga)": {
        "name": "عطر يوجا (Yoga)" if is_ar else "Yoga Perfume",
        "tag": "هدوء وانسيابية" if is_ar else "Calm & Smooth",
        "rating": "4.8 ★",
        "desc": "رائحة هادئة تمنحك استرخاءً وأناقة" if is_ar else "Calming and serene daily scent",
        "notes": "برغموت، مسك نقي، ونرجس" if is_ar else "Bergamot, Pure Musk, Narcissus",
        "img": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=260&q=80"
    },
    # صف 2: لونار (يمين) مقابل لاروزيه (يسار)
    "عطر لونار (Lunar)": {
        "name": "عطر لونار (Lunar)" if is_ar else "Lunar Perfume",
        "tag": "أناقة للجنسين" if is_ar else "Unisex Mystique",
        "rating": "4.9 ★",
        "desc": "رائحة فاخرة بطابع غامض وجذاب" if is_ar else "Enigmatic, sophisticated aroma",
        "notes": "باتشولي، عنب أسود، وعنبر" if is_ar else "Patchouli, Blackcurrant, Amber",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=260&q=80"
    },
    "عطر لاروزيه (Larose)": {
        "name": "عطر لاروزيه (Larose)" if is_ar else "Larose Perfume",
        "tag": "الأعلى تقييماً" if is_ar else "Top Rated",
        "rating": "5.0 ★",
        "desc": "أنوثة ساحرة تدوم طويلاً" if is_ar else "Charming and lasting feminine notes",
        "notes": "فانيلا، زنبق أبيض، وياسمين" if is_ar else "Vanilla, White Lily, Jasmine",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=260&q=80"
    },
    # صف 3: اليسيوم (يمين) مقابل هارت بيت (يسار)
    "عطر اليسيوم (Elysium)": {
        "name": "عطر اليسيوم (Elysium)" if is_ar else "Elysium Perfume",
        "tag": "فخامة أنثوية" if is_ar else "Feminine Luxury",
        "rating": "4.9 ★",
        "desc": "رائحة راقية تمنحك حضوراً ملكياً" if is_ar else "Refined scent with royal allure",
        "notes": "عنبر ملكي، فانيلا، ولافندر" if is_ar else "Royal Amber, Vanilla, Lavender",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=260&q=80"
    },
    "عطر هارت بيت (Heart Beat)": {
        "name": "عطر هارت بيت (Heart Beat)" if is_ar else "Heart Beat Perfume",
        "tag": "حيوية ورومانسية" if is_ar else "Vibrant Romantic",
        "rating": "4.8 ★",
        "desc": "رائحة رومانسية تنبض بالبهجة" if is_ar else "Romantic scent full of vitality",
        "notes": "كشمش أسود، مسك، وورد" if is_ar else "Blackcurrant, Musk, Rose",
        "img": "https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=260&q=80"
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

if slots_left == 1:
    status_badge = t["left_single"]
else:
    status_badge = t["left_multi"].format(n=slots_left)

# ==============================================================================
# 5. الصندوق العلوي: سعة السلة بالأعلى وحذف صندوق الأسعار
# ==============================================================================
header_html = clean_html(f"""
<div class="top-brand-card">
    <div class="brand-badge">{t["badge"]}</div>
    <div class="brand-title">{t["title"]}</div>
    <div class="brand-msg">{t["msg"]}</div>
    <div class="capacity-row">
        <span style="color:#cbd5e1;">{t["capacity_title"]}</span>
        <span style="color:#10b981;">{taken_count}/{BASKET_CAPACITY} ({status_badge})</span>
    </div>
    <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width:{progress_percent}%;"></div>
    </div>
</div>
""")
st.markdown(header_html, unsafe_allow_html=True)

# ==============================================================================
# 6. شاشة ما بعد الحجز
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    success_html = clean_html(f"""
    <div class="success-card">
        <h3 style="color:#10b981;margin:0 0 4px 0;font-size:1.2em;">{t["success_h"]}</h3>
        <div style="font-size:0.9em;color:#e2e8f0;">{t["success_perf"]} <b>{deal["perfume"]}</b></div>
        <div style="font-size:0.84em;color:#94a3b8;">{t["success_deliv"]} <b>{deal["delivery"]}</b></div>
        <div style="font-size:1.15em;color:#ffffff;margin-top:4px;">
            {t["success_due"]} <b style="color:#10b981;">{UNIFIED_PRICE} {t["currency"]}</b>
        </div>
    </div>
    <div class="notice-box">{t["cod_box"]}</div>
    """)
    st.markdown(success_html, unsafe_allow_html=True)
    
    wa_msg = (
        f"{t['wa_msg_pre']} ({UNIFIED_PRICE} {t['currency']}):\n\n"
        f"• Name: {deal['name']}\n"
        f"• Phone: {deal['phone']}\n"
        f"• Fragrance: {deal['perfume']}\n"
        f"• Delivery: {deal['delivery']}\n\n"
        f"Sent to confirm via WhatsApp!"
    )
    wa_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-btn">{t["wa_btn"]}</a>', unsafe_allow_html=True)

# ==============================================================================
# 7. النموذج وشبكة العطور المتقابلة (3 ضد 3) والأسعار مع العطر
# ==============================================================================
else:
    st.markdown(f"<div style='font-size:0.86em;font-weight:800;color:#ffffff;text-align:{align_css};margin-bottom:5px;'>{t['step1']}</div>", unsafe_allow_html=True)
    
    perfume_keys = list(PERFUMES.keys())
    perfume_labels = {k: PERFUMES[k]["name"] for k in perfume_keys}
    
    chosen_key = st.radio(
        "Select Perfume:",
        options=perfume_keys,
        format_func=lambda x: perfume_labels[x],
        label_visibility="collapsed"
    )
    
    # بطاقة العطر متضمنة السعر الفردي، سعر العرض، وشارة الخصم
    p = PERFUMES[chosen_key]
    preview_html = clean_html(f"""
    <div class="selected-perfume-panel">
        <div class="perfume-flex-row">
            <img class="perfume-thumb" src="{p["img"]}" alt="{p["name"]}">
            <div class="perfume-meta">
                <span style="color:#10b981;font-weight:800;">{p["rating"]} • {p["tag"]}</span><br>
                <b>{p["desc"]}</b><br>
                <span style="color:#94a3b8;">{p["notes"]}</span>
            </div>
        </div>
        <div class="discount-chip">
            <span style="color:#cbd5e1;">{t["val_txt"]} <s style="color:#64748b;">{ORIGINAL_RETAIL} {t["currency"]}</s> ➔ <b style="color:#10b981;font-size:1.15em;">{UNIFIED_PRICE} {t["currency"]}</b></span>
            <span style="color:#10b981;">{t["saved_txt"]}</span>
        </div>
    </div>
    """)
    st.markdown(preview_html, unsafe_allow_html=True)
    
    with st.form("quick_order_form"):
        st.markdown(f"<div style='font-size:0.86em;font-weight:800;color:#ffffff;text-align:{align_css};margin-bottom:4px;'>{t['step2']}</div>", unsafe_allow_html=True)
        
        delivery_mode = st.radio(
            "Delivery Option:",
            [t["opt_mall"], t["opt_deliv"]]
        )
        
        f_name = st.text_input(t["name_lbl"], placeholder=t["name_ph"])
        f_phone = st.text_input(t["phone_lbl"], placeholder=t["phone_ph"])
        
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(t["btn_submit"], use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error(t["err_fields"])
            elif slots_left == 0:
                st.warning(t["err_full"])
            else:
                try:
                    lang_tag = "AR" if is_ar else "EN"
                    client_note = f"BLOM_NEWTON | {p['name']} | {delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone} | LANG:{lang_tag}"
                    
                    if supabase:
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": BASKET_ID,
                            "court": 1,
                            "level": p['name'],
                            "status": "confirmed",
                            "payment_status": "pending",
                            "hear_about": delivery_mode[:25],
                            "player_note": client_note
                        }).execute()
                    
                    st.cache_data.clear()
                    st.session_state["confirmed_deal"] = {
                        "name": clean_name,
                        "phone": clean_phone,
                        "perfume": p['name'],
                        "delivery": delivery_mode,
                        "price": UNIFIED_PRICE
                    }
                    st.rerun()
                except Exception:
                    st.error("Error processing booking. Please try again.")

# ==============================================================================
# 8. بوابة المشرف المعزولة (سرية: ?manage=faris فقط)
# ==============================================================================
query_params = st.query_params
if query_params.get("manage") == "faris":
    st.markdown("---")
    st.subheader("⚙️ Admin Portal")
    admin_pin = st.text_input("PIN:", type="password", key="admin_isolated_key")
    
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        st.success("Admin authorized.")
        
        with st.form("manual_add_admin_form"):
            st.markdown("##### ➕ Add Seat Manually:")
            m_name = st.text_input("Name:")
            m_phone = st.text_input("Phone:")
            m_perf = st.selectbox("Fragrance:", [PERFUMES[k]["name"] for k in PERFUMES])
            m_paid = st.checkbox("Paid & Confirmed ✅", value=True)
            
            if st.form_submit_button("Confirm Spot"):
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
                        "hear_about": "Admin Manual",
                        "player_note": f"MANUAL | {m_perf} | PRICE:{UNIFIED_PRICE}"
                    }).execute()
                    st.cache_data.clear()
                    st.success("Seat recorded!")
                    st.rerun()
        
        st.markdown("##### 👥 Active Bundle Bookings:")
        bookings_list = get_confirmed_bookings(BASKET_ID)
        for b in bookings_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{b.get('name')}** - `{b.get('level', '-')}`\n`{b.get('phone')}`")
            if b.get('payment_status') == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>Paid ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#38bdf8; font-weight:700;'>Reserved 🔒</span>", unsafe_allow_html=True)
                if col3.button("Mark Paid", key=f"pay_adm_{b.get('id')}"):
                    if supabase:
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", b.get('id')).execute()
                    st.cache_data.clear()
                    st.rerun()

