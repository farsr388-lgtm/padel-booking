import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة والتهيئة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | عروض بلوم نيوتن",
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

def sanitize_phone_number(raw_input: str) -> str:
    """تنظيف وتحويل أرقام الجوال بدقة عالية."""
    if not raw_input:
        return ""
    table = str.maketrans(
        "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9",
        "01234567890123456789"
    )
    cleaned = re.sub(r'[\s\-\+]', '', raw_input.strip().translate(table))
    if cleaned.startswith("966"):
        cleaned = "0" + cleaned[3:]
    elif cleaned.startswith("5"):
        cleaned = "0" + cleaned
    return cleaned

# ==============================================================================
# 2. أنماط الواجهة (متوافقة كلياً مع سفاري وكروم والوضع الليلي)
# ==============================================================================
st.markdown("""
<style>
:root {
    color-scheme: dark;
    --primary: #10b981;
    --card-bg: #111827;
    --border-color: rgba(255, 255, 255, 0.14);
}

/* إخفاء واجهات وعناصر Streamlit التلقائية وشعار التاج */
header[data-testid="stHeader"], 
#MainMenu, 
footer,
div[data-testid="stStatusWidget"],
.stDeployButton,
[data-testid="stToolbar"],
div[class*="viewerBadge"],
[class*="manageApp"],
div[data-testid="stDecoration"],
[data-testid="InputInstructions"],
[data-testid="stWidgetInstructions"] { 
    display: none !important; 
}

/* ضبط أبعاد الجوال 100% بدون فراغات جانبية */
.block-container {   
    padding-top: 0.3rem !important; 
    padding-bottom: 2rem !important; 
    padding-left: 10px !important;
    padding-right: 10px !important;
    max-width: 100% !important;
    margin: 0 auto !important;
}
@media (min-width: 480px) {
    .block-container {
        max-width: 420px !important;
    }
}

html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19 !important;
    color: #f8fafc !important;
    -webkit-tap-highlight-color: transparent;
}

/* بطاقة الهيدر العلوية */
.top-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
    text-align: center;
    width: 100%;
    box-sizing: border-box;
}
.brand-badge {
    color: var(--primary);
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.74em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 4px;
}
.headline {
    font-size: 1.25em;
    font-weight: 900;
    color: #ffffff;
    margin: 0;
}
.sub-headline {
    font-size: 0.82em;
    font-weight: 700;
    color: #94a3b8;
    margin: 3px 0 8px 0;
}

/* شريط الحصص الأربعة */
.slots-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 5px;
}
.slot-pill {
    background: #030712;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 7px 2px;
    text-align: center;
    font-size: 0.72em;
    font-weight: 700;
}
.slot-pill.taken {
    background: rgba(16, 185, 129, 0.15);
    border-color: var(--primary);
    color: var(--primary);
}
.slot-pill.current {
    border-color: var(--primary);
    color: var(--primary);
    background: rgba(16, 185, 129, 0.08);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}
.slot-pill.available {
    color: #64748b;
    border-style: dashed;
}

/* ==========================================================================
   إلغاء دوائر الراديو الافتراضية وتحويلها لبطاقات متناسقة ومركزية
   ========================================================================== */
div[data-testid="stRadio"] label div:first-child:not(:last-child),
div[data-testid="stRadio"] input[type="radio"] + div {
    display: none !important;
}

/* شبكة أزرار العطور (موزعة في المنتصف) */
div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
}
div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] > label {
    width: 100% !important;
    margin: 0 !important;
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 10px 6px !important;
    min-height: 44px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    cursor: pointer !important;
    font-size: 0.82em !important;
    font-weight: 600 !important;
    box-sizing: border-box !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] > label:has(input:checked) {
    border-color: var(--primary) !important;
    background-color: rgba(16, 185, 129, 0.16) !important;
    box-shadow: 0 0 0 1px var(--primary) !important;
    color: var(--primary) !important;
    font-weight: 800 !important;
}

/* بطاقة معاينة العطر الحسي */
.sensory-card {
    background: var(--card-bg);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
}
.sensory-top-row {
    display: flex;
    align-items: center;
    gap: 12px;
}
.ingredient-thumb {
    width: 64px;
    height: 64px;
    border-radius: 10px;
    object-fit: cover;
    background-color: #030712;
    border: 2px solid rgba(16, 185, 129, 0.5);
    flex-shrink: 0;
}
.sensory-details {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.sensory-name { font-size: 0.95em; font-weight: 800; color: #ffffff; }
.sensory-tag { font-size: 0.74em; color: var(--primary); font-weight: 700; }
.sensory-notes { font-size: 0.76em; color: #94a3b8; line-height: 1.35; }

.price-chip {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 8px;
    padding: 7px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78em;
    font-weight: 700;
}

/* ==========================================================================
   خيارات الاستلام والتسليم داخل الفورم تحت الاسم والجوال
   ========================================================================== */
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 7px !important;
    width: 100% !important;
    margin-top: 4px !important;
    margin-bottom: 6px !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label {
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 11px 12px !important;
    font-size: 0.82em !important;
    cursor: pointer !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label:has(input:checked) {
    border-color: var(--primary) !important;
    background-color: rgba(16, 185, 129, 0.16) !important;
    box-shadow: 0 0 0 1px var(--primary) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label::after {
    content: "✓ محدد" !important;
    display: none !important;
    font-size: 0.72em !important;
    font-weight: 800 !important;
    color: var(--primary) !important;
    background: rgba(16, 185, 129, 0.2) !important;
    border: 1px solid rgba(16, 185, 129, 0.4) !important;
    border-radius: 6px !important;
    padding: 2px 7px !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label:has(input:checked)::after {
    display: block !important;
}

/* حقول الإدخال */
div[data-testid="stTextInput"] * { outline: none !important; }
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stTextInputRootElement"],
div[data-testid="stTextInputRootElement"] > div,
.stTextInput div[data-baseweb="input"] {
    border-color: var(--border-color) !important;
    background-color: var(--card-bg) !important;
    border-radius: 8px !important;
}
div[data-testid="stTextInput"]:focus-within div[data-baseweb="input"],
div[data-testid="stTextInput"] input:focus,
.stTextInput input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 1px var(--primary), 0 0 10px rgba(16, 185, 129, 0.25) !important;
}
input, textarea { 
    caret-color: var(--primary) !important; 
    border-radius: 8px !important; 
    font-size: 0.88em !important; 
    padding: 10px 12px !important;
    border: none !important;
    background-color: transparent !important;
    color: #ffffff !important;
}
input::placeholder { color: #64748b !important; }

/* زر التأكيد الكبير */
div[data-testid="stFormSubmitButton"] > button {
    background: var(--primary) !important;
    color: #022c22 !important;
    font-size: 0.98em !important;
    font-weight: 900 !important;
    height: 48px !important;
    border-radius: 10px !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
    width: 100% !important;
    margin-top: 6px !important;
}

.notice-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 11px;
    font-size: 0.82em;
    color: #94a3b8;
    text-align: center;
    line-height: 1.5;
    margin: 6px 0;
}
.wa-link-btn {
    display: block;
    background: var(--primary);
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 0.96em;
    text-decoration: none;
    margin-top: 6px;
}
.wa-share-btn {
    display: block;
    background: #030712;
    border: 1.5px solid var(--primary);
    color: var(--primary) !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 0.9em;
    text-decoration: none;
    margin-top: 6px;
}
.warning-pill {
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #fca5a5;
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 0.78em;
    font-weight: 600;
    margin-bottom: 6px;
}

div[data-testid="stTextInput"]:has(input[aria-label="hp"]),
input[aria-label="hp"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. إعداد الاتصال وكتالوج المكونات الفاخرة
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip('/')
        if url.endswith("/rest/v1"):
            url = url[:-8]
        key = str(st.secrets.get("SUPABASE_KEY", "")).strip()
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None

supabase = get_supabase_client()

BASKET_ID = "BLOM-NEWTON-JEDDAH-V13"
BASKET_CAPACITY = 4
UNIFIED_PRICE = 132
ORIGINAL_RETAIL = 265
SAVINGS_AMOUNT = ORIGINAL_RETAIL - UNIFIED_PRICE
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD = str(st.secrets.get("ADMIN_PASSWORD", "")).strip()
LIVE_APP_URL = "https://dub.sh/mqsoom"

PERFUMES = {
    "عطر روميو (Romeo)": {
        "tag": "رجالي فاخر • الأكثر طلباً 🔥",
        "notes": "باتشولي نقي، فانيلا، ومسك فاخر",
        "ingredient_label": "خلاصة الباتشولي الطبيعي",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=180&q=80"
    },
    "عطر يوجا (Yoga)": {
        "tag": "هادئ ومنعش • فوّاح",
        "notes": "برغموت إيطالي، مسك نقي، ونرجس",
        "ingredient_label": "البرغموت الإيطالي النقي",
        "img": "https://images.unsplash.com/photo-1582281298055-e25b84a30b0b?auto=format&fit=crop&w=180&q=80"
    },
    "عطر لونار (Lunar)": {
        "tag": "أناقة للجنسين • ثبات عالي",
        "notes": "عنب أسود، باتشولي، وعنبر دافئ",
        "ingredient_label": "راتنج العنبر الطبيعي الفاخر",
        "img": "https://images.unsplash.com/photo-1509783236416-c9ad59bae472?auto=format&fit=crop&w=180&q=80"
    },
    "عطر لاروزيه (Larose)": {
        "tag": "أنثوي ساحر • ناعم وجذاب",
        "notes": "فانيلا فرنسية، زنبق أبيض، وياسمين",
        "ingredient_label": "بتلات الياسمين الأبيض",
        "img": "https://images.unsplash.com/photo-1596438459194-f275f413d6ff?auto=format&fit=crop&w=180&q=80"
    },
    "عطر اليسيوم (Elysium)": {
        "tag": "فخامة ملكية • للمناسبات",
        "notes": "عنبر ملكي، فانيلا، ولافندر بارد",
        "ingredient_label": "زهور الخزامى واللافندر النقي",
        "img": "https://images.unsplash.com/photo-1528722828814-77b9b83aafb2?auto=format&fit=crop&w=180&q=80"
    },
    "عطر هارت بيت (Heart Beat)": {
        "tag": "حيوي ورومانسي • جذاب",
        "notes": "كشمش أسود، مسك أبيض، وورد مخملي",
        "ingredient_label": "الكشمش الأسود والورد المخملي",
        "img": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=180&q=80"
    }
}

@st.cache_data(ttl=3)
def get_confirmed_bookings(basket_key: str):
    if not supabase:
        return []
    try:
        res = supabase.table("bookings") \
            .select("*") \
            .eq("session_day", basket_key) \
            .neq("status", "cancelled") \
            .order("id") \
            .execute()
        return res.data or []
    except Exception:
        return []

# ==============================================================================
# 4. الرأسية التسويقية (تحديث لحظي للحصص)
# ==============================================================================
@st.fragment(run_every="6s")
def render_live_slots():
    current_bookings = get_confirmed_bookings(BASKET_ID)
    taken_count = len(current_bookings)

    slots_markup = "".join([
        f'<div class="slot-pill taken">حصة {i} مكتملة ✓</div>' if i <= taken_count else
        '<div class="slot-pill current">حصتك الآن 🔥</div>' if i == taken_count + 1 else
        f'<div class="slot-pill available">متاح {i}</div>'
        for i in range(1, BASKET_CAPACITY + 1)
    ])

    st.markdown(f"""
    <div class="top-card">
        <div class="brand-badge">قسم مشترياتك • عروض بلوم (2+2 مجاناً)</div>
        <div class="headline">تقاسم عروض بلوم Blom</div>
        <div class="sub-headline">السعر بالتساوي بين 4 أشخاص (132 ر.س للعبوة)</div>
        <div class="slots-container">
            {slots_markup}
        </div>
    </div>
    """, unsafe_allow_html=True)

render_live_slots()

# ==============================================================================
# 5. شاشة تأكيد الحصة (بعد الحجز)
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(deal['name'])
    safe_perfume = html.escape(deal['perfume'])
    safe_delivery = html.escape(deal['delivery'])

    st.markdown(f"""
    <div class="top-card" style="border-color:var(--primary);">
        <div class="brand-badge">تم تأكيد حصتك بنجاح 🌿</div>
        <div class="headline" style="font-size:1.15em;">{safe_perfume}</div>
        <div class="sub-headline" style="color:#cbd5e1 !important;">{safe_delivery}</div>
        <div style="font-size:1.15em;font-weight:800;color:#ffffff;margin-top:5px;">
            المطلوب عند الاستلام: <span style="color:var(--primary);">{UNIFIED_PRICE} ر.س فقط</span>
        </div>
    </div>
    <div class="notice-card">
        🤝 <b>الدفع يد بيد بعد المعاينة والفاتورة</b><br>
        التسليم: <b>السبت (المغرب إلى العشاء) عند بوابة 5 أو 6 بالسلام مول</b>.<br>
        سنتواصل معك عبر الواتساب فور اكتمال الأربعة لتأكيد الاستلام.
    </div>
    """, unsafe_allow_html=True)

    location_detail = "سأرسل اللوكيشن في الواتساب" if "توصيل" in deal['delivery'] else "السبت (المغرب-العشاء) عند بوابة 5 أو 6 بالسلام مول"

    wa_admin_msg = (
        f"مرحباً 🌿\n"
        f"حجزت حصتي في تطبيق مَقسوم - مجموعة نيوتن ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• طريقة الاستلام: {deal['delivery']}\n"
        f"• موعد ونقطة الاستلام: {location_detail}\n\n"
        f"بانتظار اكتمال الباقة لاستلام العطر مع الفاتورة الأصلية وفحصه يد بيد."
    )
    admin_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_admin_msg)}"
    st.markdown(f'<a href="{admin_link}" target="_blank" class="wa-link-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

    share_msg = (
        f"يا غالي، داخلين في باقة عطور بلوم (عرض 2+2 مجاناً) نتقاسمها بين 4 بالتساوي.\n"
        f"العطر يطلع بـ {UNIFIED_PRICE} ر.س بدل {ORIGINAL_RETAIL} ر.س، والدفع يد بيد بعد فحص الفاتورة الأصلية (التسليم السبت بالسلام مول بوابة 5 و 6 أو توصيل مجاني).\n\n"
        f"حجزت حصتي وباقي مقاعد بسيطة، ادخل اختر عطرك وقفل الباقة معنا هنا:\n"
        f"{LIVE_APP_URL}"
    )
    share_link = f"https://wa.me/?text={urllib.parse.quote(share_msg)}"
    st.markdown(f'<a href="{share_link}" target="_blank" class="wa-share-btn">👥 شارك العرض مع خويك لتكتمل الباقة أسرع</a>', unsafe_allow_html=True)

    if st.button("تعديل الاختيار أو حجز مقعد آخر", use_container_width=True):
        del st.session_state["confirmed_deal"]
        st.rerun()

# ==============================================================================
# 6. النموذج: اختيار العطر أولاً ثم بيانات الحجز والاستلام تحته
# ==============================================================================
else:
    st.markdown("<div style='font-size:0.84em;font-weight:700;color:#cbd5e1;margin-bottom:6px;'>1. اختر عِطرك من باقة نيوتن:</div>", unsafe_allow_html=True)

    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed"
    )

    p = PERFUMES[chosen_perfume]
    
    # بطاقة العطر المركزة والموجزة
    st.markdown(f"""
    <div class="sensory-card">
        <div class="sensory-top-row">
            <img src="{p['img']}" class="ingredient-thumb" alt="{p['ingredient_label']}" loading="eager" />
            <div class="sensory-details">
                <div class="sensory-name">{chosen_perfume}</div>
                <div class="sensory-tag">🌿 {p['ingredient_label']}</div>
                <div class="sensory-notes">المكونات: {p['notes']}</div>
            </div>
        </div>
        <div class="price-chip">
            <span style="color:#cbd5e1;">السعر الفردي: <s style="color:#64748b;">{ORIGINAL_RETAIL} ر.س</s> ➔ <b style="color:var(--primary);font-size:1.15em;">{UNIFIED_PRICE} ر.س</b></span>
            <span style="color:var(--primary);font-weight:800;">وفرت {SAVINGS_AMOUNT} ر.س (خصم 50%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # فورم الحجز: الاسم والجوال ثم الاستلام تحتهما مباشرة
    with st.form("quick_order_form", clear_on_submit=False, enter_to_submit=False, border=False):
        st.markdown("<div style='font-size:0.84em;font-weight:700;color:#cbd5e1;margin-bottom:4px;'>2. بيانات الحجز والتسليم:</div>", unsafe_allow_html=True)

        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")

        st.markdown("<div style='font-size:0.84em;font-weight:700;color:#cbd5e1;margin-top:6px;margin-bottom:2px;'>طريقة الاستلام:</div>", unsafe_allow_html=True)

        # خيارات الاستلام منقولة هنا تحت الاسم والجوال
        delivery_mode = st.radio(
            "طريقة وموعد الاستلام:",
            [
                f"السلام مول (بوابة 5 و 6) • السبت (المغرب إلى العشاء) — {UNIFIED_PRICE} ر.س",
                f"توصيل مجاني داخل أحياء جدة — {UNIFIED_PRICE} ر.س"
            ],
            key="delivery_mode",
            label_visibility="collapsed"
        )

        st.markdown("""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:6px;padding:7px;text-align:center;font-size:0.73em;color:#94a3b8;margin:8px 0;">
            🛡️ أصلي 100% • فحص العطر والفاتورة الأصلية قبل الدفع يد بيد
        </div>
        """, unsafe_allow_html=True)

        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت حصتك في العرض ({UNIFIED_PRICE} ر.س عند الاستلام)", use_container_width=True)

        if submit_btn and not hp:
            clean_name = f_name.strip()
            clean_phone = sanitize_phone_number(f_phone)

            fresh_bookings = get_confirmed_bookings(BASKET_ID)
            existing_booking = next((b for b in fresh_bookings if b.get('phone') == clean_phone), None)

            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.markdown('<div class="warning-pill">⚠️ يرجى التأكد من كتابة الاسم الثنائي ورقم جوال سعودي يبدأ بـ 05.</div>', unsafe_allow_html=True)
            elif existing_booking:
                st.session_state["confirmed_deal"] = {
                    "name": existing_booking.get("name"),
                    "phone": existing_booking.get("phone"),
                    "perfume": existing_booking.get("level"),
                    "delivery": existing_booking.get("hear_about", delivery_mode),
                    "price": UNIFIED_PRICE
                }
                st.rerun()
            elif len(fresh_bookings) >= BASKET_CAPACITY:
                st.markdown('<div class="warning-pill">⚠️ اكتملت هذه الباقة للتو بالكامل! جاري تجهيز باقة جديدة.</div>', unsafe_allow_html=True)
            else:
                if not supabase:
                    st.error("تعذر الاتصال بقاعدة البيانات. يرجى مراجعة إعدادات Secrets.")
                else:
                    try:
                        client_note = f"BLOM_NEWTON | {chosen_perfume} | {delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"
                        
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": BASKET_ID,
                            "court": 1,
                            "level": chosen_perfume,
                            "status": "confirmed",
                            "payment_status": "pending",
                            "hear_about": delivery_mode[:50],
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
                    except Exception as db_err:
                        st.error(f"تعذر إتمام التسجيل في السيرفر: {db_err}")

# ==============================================================================
# 7. لوحة المشرف المقفلة أمنياً
# ==============================================================================
if st.query_params.get("manage") == "faris":
    st.markdown("---")
    st.caption("لوحة الإدارة والتحليلات السريعة")
    admin_pin = st.text_input("رمز الدخول السري:", type="password", key="adm_key")

    input_pin_str = str(admin_pin or "").strip()
    target_pwd_str = str(ADMIN_PASSWORD or "").strip()

    if input_pin_str and target_pwd_str and hmac.compare_digest(input_pin_str, target_pwd_str):
        bookings_list = get_confirmed_bookings(BASKET_ID)
        total_count = len(bookings_list)
        paid_count = sum(1 for b in bookings_list if b.get('payment_status') == 'paid')
        total_val = total_count * UNIFIED_PRICE

        k1, k2, k3 = st.columns(3)
        k1.metric("المقاعد المحجوزة", f"{total_count} / {BASKET_CAPACITY}")
        k2.metric("المحصل (مدفوع)", f"{paid_count * UNIFIED_PRICE} ر.س")
        k3.metric("إجمالي السلة", f"{total_val} ر.س")

        st.markdown("##### قائمة المشتركين:")
        for b in bookings_list:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{b.get('name')}** | `{b.get('phone')}`\nالعطر: **{b.get('level')}**\nالتسليم: `{b.get('hear_about')}`")
            with c2:
                if b.get('payment_status') == 'paid':
                    st.markdown("<span style='color:var(--primary); font-weight:700;'>مدفوع ✓</span>", unsafe_allow_html=True)
                else:
                    if st.button("اعتماد دفع", key=f"pay_{b.get('id')}"):
                        if supabase:
                            supabase.table("bookings").update({"payment_status": "paid"}).eq("id", b.get('id')).execute()
                        st.cache_data.clear()
                        st.rerun()

                if st.button("إلغاء المقعد", key=f"cancel_{b.get('id')}"):
                    if supabase:
                        supabase.table("bookings").update({"status": "cancelled"}).eq("id", b.get('id')).execute()
                    st.cache_data.clear()
                    st.rerun()
            st.divider()
    elif input_pin_str:
        st.error("رمز الدخول غير صحيح.")
