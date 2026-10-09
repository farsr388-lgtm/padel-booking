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
# 2. أنماط الواجهة (ألوان تحديد ساطعة وعالية التباين)
# ==============================================================================
st.markdown("""
<style>
:root {
    color-scheme: dark;
    --primary: #10b981;
    --active-bg: #064e3b;
    --card-bg: #111827;
    --border-color: rgba(255, 255, 255, 0.15);
}

/* إخفاء واجهات Streamlit التلقائية وشعار التاج */
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

/* ضبط مقاس الجوال من الحافة للحافة */
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
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.35);
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

/* شريط الحصص */
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
    background: rgba(16, 185, 129, 0.2);
    border-color: var(--primary);
    color: var(--primary);
}
.slot-pill.current {
    border-color: var(--primary);
    color: #ffffff;
    background: var(--active-bg);
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}
.slot-pill.available {
    color: #64748b;
    border-style: dashed;
}

/* ==========================================================================
   أزرار العطور: واضحة، مركزية، ولون تحديد فاقع جداً
   ========================================================================== */
div[data-testid="stRadio"] label div:first-child:not(:last-child),
div[data-testid="stRadio"] input[type="radio"] + div {
    display: none !important;
}

div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
    width: 100% !important;
    margin-bottom: 8px !important;
}
div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] > label {
    width: 100% !important;
    margin: 0 !important;
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 10px !important;
    padding: 12px 6px !important;
    min-height: 46px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    cursor: pointer !important;
    font-size: 0.88em !important;
    font-weight: 700 !important;
    box-sizing: border-box !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    color: #cbd5e1 !important;
}
/* اللون الفاقع والمضيء عند اختيار العطر */
div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] > label:has(input:checked) {
    border: 2px solid var(--primary) !important;
    background-color: var(--active-bg) !important;
    box-shadow: 0 0 0 1px var(--primary), 0 0 16px rgba(16, 185, 129, 0.45) !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    transform: scale(1.02) !important;
}

/* بطاقة معاينة العطر الحسي */
.sensory-card {
    background: var(--card-bg);
    border: 1.5px solid rgba(16, 185, 129, 0.4);
    border-radius: 12px;
    padding: 11px 13px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
}
.sensory-top-row {
    display: flex;
    align-items: center;
    gap: 12px;
}
.ingredient-thumb {
    width: 66px;
    height: 66px;
    border-radius: 10px;
    object-fit: cover;
    background-color: #030712;
    border: 2px solid var(--primary);
    flex-shrink: 0;
}
.sensory-details {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.sensory-name { font-size: 0.98em; font-weight: 900; color: #ffffff; }
.sensory-tag { font-size: 0.74em; color: var(--primary); font-weight: 800; }
.sensory-notes { font-size: 0.77em; color: #94a3b8; line-height: 1.35; }

.price-chip {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 8px;
    padding: 7px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78em;
    font-weight: 700;
}

/* ==========================================================================
   أزرار الاستلام والتسليم: لون فاقع وتأكيد صريح
   ========================================================================== */
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    width: 100% !important;
    margin-top: 4px !important;
    margin-bottom: 8px !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label {
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    font-size: 0.84em !important;
    cursor: pointer !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    box-sizing: border-box !important;
    color: #cbd5e1 !important;
}
/* اللون الساطع عند اختيار الاستلام */
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label:has(input:checked) {
    border: 2px solid var(--primary) !important;
    background-color: var(--active-bg) !important;
    box-shadow: 0 0 0 1px var(--primary), 0 4px 14px rgba(16, 185, 129, 0.35) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label::after {
    content: "✓ تم الاختيار" !important;
    display: none !important;
    font-size: 0.74em !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    background: var(--primary) !important;
    border-radius: 6px !important;
    padding: 3px 9px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4) !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) div[role="radiogroup"] > label:has(input:checked)::after {
    display: block !important;
}

/* حقول الإدخال: توهج واضح عند الكتابة */
div[data-testid="stTextInput"] * { outline: none !important; }
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stTextInputRootElement"],
div[data-testid="stTextInputRootElement"] > div,
.stTextInput div[data-baseweb="input"] {
    border: 1.5px solid var(--border-color) !important;
    background-color: var(--card-bg) !important;
    border-radius: 8px !important;
}
div[data-testid="stTextInput"]:focus-within div[data-baseweb="input"],
div[data-testid="stTextInput"] input:focus,
.stTextInput input:focus {
    border: 2px solid var(--primary) !important;
    background-color: #062b23 !important;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3), 0 0 12px rgba(16, 185, 129, 0.4) !important;
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
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35) !important;
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
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
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
# 3. إعداد الاتصال وكتالوج العطور (عربي واضح + إنجليزي فخم بالمعاينة)
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

# أسماء عربية صافية للأزرار، مع بيان الاسم الإنجليزي في بطاقة العطر
PERFUMES = {
    "عطر روميو": {
        "en_name": "Romeo",
        "tag": "رجالي فاخر • الأكثر طلباً 🔥",
        "notes": "باتشولي نقي، فانيلا، ومسك فاخر",
        "ingredient_label": "خلاصة الباتشولي الطبيعي",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=180&q=80"
    },
    "عطر يوجا": {
        "en_name": "Yoga",
        "tag": "هادئ ومنعش • فوّاح",
        "notes": "برغموت إيطالي، مسك نقي، ونرجس",
        "ingredient_label": "البرغموت الإيطالي النقي",
        "img": "https://images.unsplash.com/photo-1582281298055-e25b84a30b0b?auto=format&fit=crop&w=180&q=80"
    },
    "عطر لونار": {
        "en_name": "Lunar",
        "tag": "أناقة للجنسين • ثبات عالي",
        "notes": "عنب أسود، باتشولي، وعنبر دافئ",
        "ingredient_label": "راتنج العنبر الطبيعي الفاخر",
        "img": "https://images.unsplash.com/photo-1509783236416-c9ad59bae472?auto=format&fit=crop&w=180&q=80"
    },
    "عطر لاروزيه": {
        "en_name": "Larose",
        "tag": "أنثوي ساحر • ناعم وجذاب",
        "notes": "فانيلا فرنسية، زنبق أبيض، وياسمين",
        "ingredient_label": "بتلات الياسمين الأبيض",
        "img": "https://images.unsplash.com/photo-1596438459194-f275f413d6ff?auto=format&fit=crop&w=180&q=80"
    },
    "عطر إليسيوم": {
        "en_name": "Elysium",
        "tag": "فخامة ملكية • للمناسبات",
        "notes": "عنبر ملكي، فانيلا، ولافندر بارد",
        "ingredient_label": "زهور الخزامى واللافندر النقي",
        "img": "https://images.unsplash.com/photo-1528722828814-77b9b83aafb2?auto=format&fit=crop&w=180&q=80"
    },
    "عطر هارت بيت": {
        "en_name": "Heart Beat",
        "tag": "حيوي ورومانسي • جذاب",
        "notes": "كشمش أسود، مسك أبيض، وورد مخملي",
        "ingredient_label": "الكشمش الأسود والورد المخملي",
        "img": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=180&q=80"
    }
