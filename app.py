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
# 2. أنماط الواجهة الثنائية فائقة الخفة (Zero-Red & Clean CSS)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.8rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 420px !important; 
    margin: 0 auto; 
}

/* نمط ألوان هادئ وخفيف على الأجهزة: أسود كربوني + زمردي */
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f1f5f9;
}

/* القضاء الصارم على أي ظل أو إطار أحمر في القوائم */
div[data-baseweb="select"] {
    border-radius: 10px !important;
}
div[data-baseweb="select"] > div {
    background-color: #111827 !important;
    border: 1px solid #1f2937 !important;
    color: #f1f5f9 !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}
div[data-baseweb="select"]:focus-within > div,
div[data-baseweb="select"] > div:hover,
div[data-baseweb="select"] > div:focus {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
    outline: none !important;
}
div[data-baseweb="select"] svg { 
    fill: #10b981 !important; 
}

/* خيارات أزرار الراديو */
div[data-testid="stRadio"] div[role="radiogroup"] label div:first-child {
    border-color: #334155 !important;
    background-color: transparent !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child,
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] {
    border-color: #10b981 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] div {
    background-color: #10b981 !important;
}

/* حقول الإدخال */
input, textarea { 
    caret-color: #10b981 !important; 
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* كرت المتجر الرئيسي */
.store-header {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 12px;
    text-align: center;
}
.store-badge {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 8px;
}
.store-title { 
    font-size: 1.3em; 
    font-weight: 900; 
    color: #ffffff; 
    margin: 4px 0; 
}
.store-desc { 
    font-size: 0.84em; 
    color: #94a3b8; 
    line-height: 1.6; 
    margin-bottom: 12px; 
}

/* شريط السعر الموحد المستوحى من تطبيقات المتاجر الكبرى */
.price-strip {
    background: #0b0f19;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-around;
    align-items: center;
}
.price-col { text-align: center; }
.price-now { font-size: 1.45em; font-weight: 900; color: #10b981; }
.price-old { font-size: 0.85em; color: #64748b; text-decoration: line-through; }
.price-lbl { font-size: 0.72em; color: #94a3b8; }

/* بطاقة استعراض عطر نيوتن */
.perfume-box {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0 14px 0;
    display: flex;
    gap: 12px;
    align-items: center;
}
.perfume-img {
    width: 80px;
    height: 80px;
    border-radius: 8px;
    object-fit: cover;
    background: #1e293b;
}
.perfume-info {
    flex: 1;
    font-size: 0.82em;
    line-height: 1.5;
    color: #cbd5e1;
}
.rating-pill {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.78em;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 4px;
}

/* شاشة بعد تأكيد الحجز */
.success-card {
    background: rgba(16, 185, 129, 0.1);
    border: 1.5px solid #10b981;
    border-radius: 14px;
    padding: 18px 14px;
    text-align: center;
    margin-top: 10px;
}
.notice-box {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 12px;
    font-size: 0.85em;
    color: #94a3b8;
    line-height: 1.6;
    margin: 12px 0;
    text-align: center;
}

/* زر الحجز السريع */
div[data-testid="stFormSubmitButton"] > button {
    background: #10b981 !important;
    color: #022c22 !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 50px !important;
    border-radius: 10px !important;
    border: none !important;
    margin-top: 4px !important;
}
.wa-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 14px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 1em;
    text-decoration: none;
    margin-top: 10px;
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
# 3. الربط بقاعدة البيانات وتجهيز كتالوج مجموعة نيوتن (Newton)
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

BASKET_ID = "BLOM-NEWTON-JEDDAH-01"
BASKET_CAPACITY = 3
UNIFIED_PRICE = 65  # السعر الموحد المعتمد
ADMIN_PHONE = "966566261868"

raw_secret = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")
ADMIN_PASSWORD_HASH = str(raw_secret).strip()

# كتالوج مجموعة نيوتن الرسمية من بلوم (Newton by Bloom)
PERFUMES = {
    "عطر نيوتن جرافيتي (Newton Gravity) 100مل": {
        "tag": "الأكثر طلباً ومبيعاً",
        "rating": "4.9 ★ (الأعلى تقييماً)",
        "desc": "طابع فخم وجذاب يجمع الأخشاب والعنبر والروائح الجلدية الدافئة",
        "notes": "عنبر ملكي، أخشاب الأرز، توابل دافئة، ولمسة جلدية",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=250&q=80"
    },
    "عطر نيوتن إلكتريك (Newton Electric) 100مل": {
        "tag": "انتعاش يومي فوّاح",
        "rating": "4.8 ★ (خيار الدوام والصيف)",
        "desc": "انتعاش عصري بطابع حمضي منعش يمنح حضوراً ونظافة طوال اليوم",
        "notes": "برغموت إيطالي، لافندر ناعم، ونسيم بحري منعش",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=250&q=80"
    },
    "عطر نيوتن كوانتم (Newton Quantum) 100مل": {
        "tag": "راقي وهادئ (سويت ناعم)",
        "rating": "4.9 ★ (ملائم للإهداء)",
        "desc": "طابع مخملي ناعم يجمع الفواكه الفاخرة مع المسك والفانيلا الفرنسية",
        "notes": "فواكه ناعمة، ياسمين أبيض، فانيلا، ومسك نقي",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=250&q=80"
    },
    "عطر نيوتن موشن (Newton Motion) 100مل": {
        "tag": "طابع شرقي كلاسيكي",
        "rating": "4.7 ★ (ثبات وفوحان عالي)",
        "desc": "عطر شرقي دافئ ومثالي للطلعات والمناسبات المسائية الفخمة",
        "notes": "باتشولي، هيل عطري، بخور ناعم، وخشب الصندل",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=250&q=80"
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

# ==============================================================================
# 4. الواجهة البصرية المباشرة
# ==============================================================================
st.markdown(f"""
<div class="store-header">
    <div class="store-badge">قسم مشترياتك • تقاسم العرض معنا</div>
    <div class="store-title">تقاسم عروض بلوم Blom (مجموعة نيوتن)</div>
    <div class="store-desc">
        نحن نجمع لكم اهتماماتكم في نفس العرض مع أشخاص مختلفين؛ نتقاسم باقة نيوتن سوا بسعر التكلفة، 
        وعِطرك الأصلي 100مل يطلع عليك بسعر موحد وثابت:
    </div>
    <div class="price-strip">
        <div class="price-col">
            <div class="price-now">{UNIFIED_PRICE} ر.س</div>
            <div class="price-lbl">سعر حصتك الموحد</div>
        </div>
        <div style="color:#1f2937; font-size:1.2em;">|</div>
        <div class="price-col">
            <div class="price-old">195 ر.س</div>
            <div class="price-lbl">سعر العطر منفرداً</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# مؤشر سعة السلة
progress_percent = int((taken_count / BASKET_CAPACITY) * 100)
status_badge = f"متبقي عطر واحد وتكتمل الباقة ونطلبها فوراً 🔥" if slots_left == 1 else f"متبقي {slots_left} عطور لاكتمال الباقة"

st.markdown(f"""
