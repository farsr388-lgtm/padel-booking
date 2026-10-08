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

# ==============================================================================
# 2. أنماط الواجهة الثنائية (محصنة برمجياً ومضبوطة المسافات)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.6rem !important; 
    padding-bottom: 2.2rem !important; 
    max-width: 420px !important; 
    margin: 0 auto; 
}

html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f1f5f9;
}

/* شبكة الاختيار الثنائية (A/B Columns Grid) بالأعلى */
div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
    margin-bottom: 8px !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1.5px solid #1f2937 !important;
    border-radius: 10px !important;
    padding: 10px 8px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.15s ease-in-out !important;
    display: flex !important;
    align-items: center !important;
    min-height: 48px !important;
    box-sizing: border-box !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] > label:hover {
    border-color: #334155 !important;
    background-color: #141e33 !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* استئصال اللون الأحمر من التحديدات */
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

/* خيارات الاستلام */
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    margin: 0 !important;
}

/* حقول الإدخال */
div[data-testid="stTextInput"] {
    margin-bottom: 8px !important;
}
input, textarea { 
    caret-color: #10b981 !important; 
    border-radius: 8px !important;
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* كرت استعراض العطر النشط */
.active-perfume-details {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 10px;
    margin: 4px 0 12px 0;
    display: flex;
    gap: 10px;
    align-items: center;
}
.perfume-img-container {
    width: 65px;
    height: 65px;
    border-radius: 8px;
    background: #0f172a;
    border: 1px solid #1e293b;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    flex-shrink: 0;
}
.perfume-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.perfume-info {
    flex: 1;
    font-size: 0.8em;
    line-height: 1.45;
    color: #cbd5e1;
}

/* الهيدر وقسم الشرح في الأسفل */
.store-header {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 14px;
    margin-top: 14px;
    margin-bottom: 10px;
    text-align: center;
}
.store-badge {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.76em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 6px;
}
.store-title { 
    font-size: 1.25em; 
    font-weight: 900; 
    color: #ffffff; 
    margin: 2px 0 6px 0; 
}
.store-desc { 
    font-size: 0.81em; 
    color: #94a3b8; 
    line-height: 1.5; 
    margin-bottom: 8px; 
}

/* شريط الأسعار بالأسفل */
.price-strip {
    background: #0b0f19;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 8px 12px;
    display: flex;
    justify-content: space-around;
    align-items: center;
}
.price-col { text-align: center; }
.price-now { font-size: 1.45em; font-weight: 900; color: #10b981; }
.price-old { font-size: 0.82em; color: #64748b; text-decoration: line-through; }
.price-lbl { font-size: 0.7em; color: #94a3b8; }

/* شاشة ما بعد الحجز */
.success-card {
    background: rgba(16, 185, 129, 0.1);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
    margin-top: 8px;
}
.notice-box {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 12px;
    font-size: 0.83em;
    color: #94a3b8;
    line-height: 1.6;
    margin: 10px 0;
    text-align: center;
}

/* الأزرار الأساسية */
div[data-testid="stFormSubmitButton"] > button {
    background: #10b981 !important;
    color: #022c22 !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 48px !important;
    border-radius: 10px !important;
    border: none !important;
    margin-top: 4px !important;
}
.wa-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 1em;
    text-decoration: none;
    margin-top: 8px;
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
# 3. الربط بقاعدة البيانات وتجهيز كتالوج نيوتن
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

BASKET_ID = "BLOM-NEWTON-JEDDAH-V4"
BASKET_CAPACITY = 4      # سلة 4 عطور لعرض (2+2 مجاناً)
UNIFIED_PRICE = 132      # السعر الموحد بعد تقاسم عرض بلوم
ADMIN_PHONE = "966566261868"

raw_secret = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")
ADMIN_PASSWORD_HASH = str(raw_secret).strip()

# كتالوج عطور نيوتن (6 عطور مقسمة على شبكة A/B)
PERFUMES = {
    "عطر روميو (Romeo)": {
        "tag": "رجالي فاخر",
        "rating": "4.8 ★",
        "desc": "جاذبية وأناقة رجولية فاخرة تبقى في الذاكرة",
        "notes": "باتشولي، فانيلا، ومسك نقي",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=260&q=80"
    },
    "عطر لونار (Lunar)": {
        "tag": "أناقة للجنسين",
        "rating": "4.9 ★",
        "desc": "رائحة فاخرة تخطف الأنظار بطابع غامض وجذاب",
        "notes": "باتشولي، عنب أسود، وعنبر دافئ",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=260&q=80"
    },
    "عطر اليسيوم (Elysium)": {
        "tag": "فخامة أنثوية",
        "rating": "4.9 ★",
        "desc": "رائحة راقية تمنحك جاذبية وحضوراً ملكياً",
        "notes": "عنبر ملكي، فانيلا ناعمة، ولافندر",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=260&q=80"
    },
    "عطر يوجا (Yoga)": {
        "tag": "هدوء وانسيابية",
        "rating": "4.8 ★",
        "desc": "رائحة هادئة تمنحك استرخاءً وأناقة طوال اليوم",
        "notes": "برغموت منعش، مسك نقي، ونرجس",
        "img": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=260&q=80"
    },
    "عطر لاروزيه (Larose)": {
        "tag": "الأعلى تقييماً",
        "rating": "5.0 ★",
        "desc": "أنوثة ساحرة وراقية تدوم طويلاً وتأسر الحواس",
        "notes": "فانيلا، زنبق أبيض، وياسمين مخملي",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=260&q=80"
    },
    "عطر هارت بيت (Heart Beat)": {
        "tag": "حيوية ورومانسية",
        "rating": "4.8 ★",
        "desc": "رائحة رومانسية تنبض بالحياة والبهجة",
        "notes": "كشمش أسود، مسك أبيض، وورد ناعم",
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
            .neq("status
