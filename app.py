import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة والتهيئة الأساسية
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | تقاسم عروض بلوم - نيوتن",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع تجربة المستخدم عبر Microsoft Clarity
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
    """تنظيف وتوحيد أرقام الجوال ومعالجة الأرقام العربية والرموز."""
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
# 2. هندسة أنماط الواجهة (CSS Engine & Defensive Layout)
# ==============================================================================
st.markdown("""
<style>
:root {
    color-scheme: dark;
    --primary: #10b981;
    --primary-glow: rgba(16, 185, 129, 0.4);
    --active-bg: #064e3b;
    --card-bg: #111827;
    --border-color: rgba(255, 255, 255, 0.12);
    --danger: #ef4444;
}

/* 1. إخفاء عناصر Streamlit الافتراضية وشعار التاج */
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

/* 2. استغلال كامل أبعاد شاشة الجوال ومنع الهوامش الزائدة */
.block-container {   
    padding-top: 0.2rem !important; 
    padding-bottom: 2rem !important; 
    padding-left: 8px !important;
    padding-right: 8px !important;
    max-width: 100% !important;
    margin: 0 auto !important;
}
@media (min-width: 480px) {
    .block-container {
        max-width: 425px !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
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

/* البطاقة العلوية وشريط الحصص */
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
    border: 1px solid rgba(16, 185, 129, 0.28);
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
    background: rgba(16, 185, 129, 0.18);
    border-color: var(--primary);
    color: var(--primary);
}
.slot-pill.current {
    border-color: var(--primary);
    color: #ffffff;
    background: var(--active-bg);
    box-shadow: 0 0 12px var(--primary-glow);
}
.slot-pill.available {
    color: #64748b;
    border-style: dashed;
}

/* العنوان المركزي في المنتصف */
.centered-section-title {
    text-align: center !important;
    font-size: 0.96em !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    margin-top: 10px !important;
    margin-bottom: 8px !important;
}

/* ==========================================================================
   3. حل مشكلة تشتت الحروف وضبط بطاقات العطور (3 يمين و 3 يسار)
   ========================================================================== */
div[data-testid="stRadio"] { width: 100% !important; }

div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 8px !important;
    width: 100% !important;
    margin-bottom: 10px !important;
    box-sizing: border-box !important;
}

div[data-testid="stRadio"]:not(:has(input[name*="delivery_mode"])) div[role="radiogroup"] > label {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    min-height: 48px !important;
    cursor: pointer !important;
    box-sizing: border-box !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
    margin: 0 !important;
}

/* إخفاء دوائر الراديو الافتراضية لمنع انهيار العرض */
div[data-testid="stRadio"] input[type="radio"] {
    position: absolute !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
}
div[data-testid="stRadio"] label > div:first-child:not(:only-child) {
    display: none !important;
}

/* النقطة الحمراء للخيارات غير المحددة */
div[data-testid="stRadio"] div[role="radiogroup"] > label::before {
    content: "" !important;
    display: inline-block !important;
    width: 14px !important;
    height: 14px !important;
    min-width: 14px !important;
    min-height: 14px !important;
    border-radius: 50% !important;
    border: 2px solid var(--danger) !important;
    background-color: rgba(239, 68, 68, 0.2) !important;
    margin-left: 10px !important;
    margin-right: 0 !important;
    flex-shrink: 0 !important;
    box-shadow: 0 0 6px rgba(239, 68, 68, 0.35) !important;
    transition: all 0.2s ease !important;
}

/* النقطة الزمردية والإضاءة الفاخرة عند التحديد */
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    background-color: var(--active-bg) !important;
    border: 2px solid var(--primary) !important;
    box-shadow: 0 0 14px var(--primary-glow) !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked)::before {
    border-color: var(--primary) !important;
    background-color: var(--primary) !important;
    box-shadow: 0 0 10px var(--primary) !important;
}

/* حماية النصوص العربية من الانهيار والالتفاف العمودي */
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span,
div[data-testid="stRadio"] label div {
    color: #cbd5e1 !important;
    font-size: 0.88em !important;
    font-weight: 700 !important;
    line-height: 1.3 !important;
    margin: 0 !important;
    padding: 0 !important;
    white-space: nowrap !important;
    word-break: keep-all !important;
}
div[data-testid="stRadio"] label:has(input:checked) p,
div[data-testid="stRadio"] label:has(input:checked) span {
    color: #ffffff !important;
    font-weight: 900 !important;
}

/* خيارات الاستلام والتسليم داخل النموذج */
form div[data-testid="stRadio"] div[role="radiogroup"],
div[data-testid="stForm"] div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    width: 100% !important;
    margin-top: 4px !important;
    margin-bottom: 8px !important;
}

form div[data-testid="stRadio"] div[role="radiogroup"] > label,
div[data-testid="stForm"] div[data-testid="stRadio"] div[role="radiogroup"] > label {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    min-height: 48px !important;
    cursor: pointer !important;
    box-sizing: border-box !important;
    width: 100% !important;
    margin: 0 !important;
}
div[data-testid="stForm"] div[data-testid="stRadio"] label p,
div[data-testid="stForm"] div[data-testid="stRadio"] label span {
    white-space: normal !important;
    font-size: 0.84em !important;
    line-height: 1.4 !important;
}

/* بطاقة معاينة العطر الفاخرة */
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

/* حقول الإدخال */
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
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3), 0 0 12px var(--primary-glow) !important;
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

/* زر التثبيت الأساسي */
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

/* أنيميشن الاهتزاز والوميض للتنبيه عند نقص البيانات */
@keyframes alertShake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-6px); }
    40%, 80% { transform: translateX(6px); }
}

.warning-pill-shake {
    background: rgba(239, 68, 68, 0.2) !important;
    border: 2px solid var(--danger) !important;
    color: #fecaca !important;
    padding: 12px 14px !important;
    border-radius: 10px !important;
    font-size: 0.88em !important;
    font-weight: 800 !important;
    margin-bottom: 12px !important;
    text-align: center !important;
    line-height: 1.4 !important;
    box-shadow: 0 0 18px rgba(239, 68, 68, 0.4) !important;
    animation: alertShake 0.45s ease-in-out !important;
}

/* بطاقة التقدير وقائمة الانتظار عند اكتمال الباقة */
.waitlist-card {
    background: rgba(16, 185, 129, 0.08) !important;
    border: 1.5px solid rgba(16, 185, 129, 0.4) !important;
    color: #f8fafc !important;
    padding: 14px 16px !important;
    border-radius: 10px !important;
    font-size: 0.88em !important;
    line-height: 1.6 !important;
    text-align: center !important;
    margin-bottom: 12px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35) !important;
}
.waitlist-card b {
    color: #10b981 !important;
    font-size: 1.05em !important;
    display: block;
    margin-bottom: 4px;
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
    box-shadow: 0 4px 14px var(--primary-glow);
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

/* مصيدة الروبوتات البرمجية الخفية */
div[data-testid="stTextInput"]:has(input[aria-label="hp"]),
input[aria-label="hp"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. إعداد الاتصال وكتالوج العطور الفاخرة
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

# الرابط الذكي المعتمد لبطاقات الواتساب
LIVE_APP_URL = "https://dub.sh/mqsoom"

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
# 5. الرأسية التسويقية (تحديث لحظي للحصص دون إعادة تحميل الصفحة)
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
        <div class="sub-headline">السعر بالتساوي بين 4 أشخاص ({UNIFIED_PRICE} ر.س للعبوة)</div>
        <div class="slots-container">
            {slots_markup}
        </div>
    </div>
    """, unsafe_allow_html=True)

render_live_slots()

# ==============================================================================
# 6. شاشة تأكيد الحصة (تخصيص الرسائل التفاعلية الذكية لكل عميل)
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(deal['name'])
    safe_perfume = html.escape(deal['perfume'])
    safe_delivery = html.escape(deal['delivery'])

    # حساب المقاعد المتبقية في هذه اللحظة تلقائياً
    fresh_list = get_confirmed_bookings(BASKET_ID)
    current_taken = len(fresh_list)
    remaining_seats = max(0, BASKET_CAPACITY - current_taken)

    # 1. نص المقاعد الذكي المحفّز
    if remaining_seats > 0:
        seats_status_msg = f"⏳ باقي {remaining_seats} وينقفل القروب ونطلب فوراً."
    else:
        seats_status_msg = "🔥 اكتملت الـ 4 مقاعد بالكامل وجاري تنفيذ الطلب!"

    # 2. تخصيص التعليمات بدقة حسب رغبة العميل
    if "توصيل" in deal['delivery']:
        delivery_instruction = "📍 موقع التوصيل: (برسل لك اللوكيشن في هذه المحادثة مباشرة)"
        card_delivery_note = "سنتواصل معك عبر الواتساب فور اكتمال الأربعة لتأكيد اللوكيشن والتوصيل."
    else:
        delivery_instruction = "📍 الاستلام: السلام مول (بوابة 5 و 6) - السبت بين المغرب والعشاء"
        card_delivery_note = "موعد الاستلام بالسلام مول: <b>السبت (المغرب إلى العشاء: 6:30م – 9:00م) عند بوابة 5 أو 6</b>."

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
        🤝 <b>الدفع يد بيد بعد المعاينة والفاتورة الأصلية</b><br>
        {card_delivery_note}
    </div>
    """, unsafe_allow_html=True)

    # رسالة الواتساب المخصصة للإدارة
    wa_admin_msg = (
        f"مرحباً 🌿\n"
        f"حجزت حصتي في تطبيق مَقسوم ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• {delivery_instruction}\n\n"
        f"{seats_status_msg}\n"
        f"بانتظار تأكيدك واستلام الفاتورة الأصلية وفحص العطر يد بيد."
    )
    admin_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_admin_msg)}"
    st.markdown(f'<a href="{admin_link}" target="_blank" class="wa-link-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

    # رسالة مشاركة العرض مع الأصدقاء
    share_msg = (
        f"يا غالي، داخلين في باقة عطور بلوم (عرض 2+2 مجاناً) نتقاسمها بين 4 بالتساوي.\n"
        f"العطر يطلع بـ {UNIFIED_PRICE} ر.س بدل {ORIGINAL_RETAIL} ر.س، والدفع يد بيد بعد فحص الفاتورة الأصلية في جدة.\n\n"
        f"حجزت حصتي وباقي مقاعد بسيطة، ادخل اختر عطرك وقفل الباقة معنا هنا:\n"
        f"{LIVE_APP_URL}"
    )
    share_link = f"https://wa.me/?text={urllib.parse.quote(share_msg)}"
    st.markdown(f'<a href="{share_link}" target="_blank" class="wa-share-btn">👥 شارك العرض مع خويك لتكتمل الباقة أسرع</a>', unsafe_allow_html=True)

    if st.button("تعديل الاختيار أو حجز مقعد آخر", use_container_width=True):
        del st.session_state["confirmed_deal"]
        st.rerun()

# ==============================================================================
# 7. النموذج: اختيار العطر أولاً ثم بيانات الاستلام مع التنبيه العلوي
# ==============================================================================
else:
    st.markdown('<div class="centered-section-title">اختر عطرك من باقة نيوتن</div>', unsafe_allow_html=True)

    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed"
    )

    p = PERFUMES[chosen_perfume]
    
    st.markdown(f"""
    <div class="sensory-card">
        <div class="sensory-top-row">
            <img src="{p['img']}" class="ingredient-thumb" alt="{p['ingredient_label']}" loading="eager" />
            <div class="sensory-details">
                <div class="sensory-name">{chosen_perfume} <span style="font-size:0.8em;color:#94a3b8;font-weight:500;">({p['en_name']})</span></div>
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

    with st.form("quick_order_form", clear_on_submit=False, enter_to_submit=False, border=False):
        st.markdown('<div class="centered-section-title" style="margin-top:0;">بيانات التأكيد والاستلام</div>', unsafe_allow_html=True)

        # الحاوية العلوية المخصصة لرسائل الخطأ وقائمة الانتظار مع التمرير التلقائي
        alert_placeholder = st.empty()

        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")

        st.markdown('<div class="centered-section-title" style="font-size:0.88em;margin-top:8px;margin-bottom:4px;">حدد طريقة وموعد الاستلام</div>', unsafe_allow_html=True)

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

        # مصيدة الروبوتات البرمجية
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت حصتك في العرض ({UNIFIED_PRICE} ر.س عند الاستلام)", use_container_width=True)

        if submit_btn and not hp:
            clean_name = f_name.strip()
            clean_phone = sanitize_phone_number(f_phone)

            fresh_bookings = get_confirmed_bookings(BASKET_ID)
            existing_booking = next((b for b in fresh_bookings if b.get('phone') == clean_phone), None)

            # 1. التحقق من صحة الاسم ورقم الجوال
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                alert_placeholder.markdown(
                    '<div id="form-top-alert" class="warning-pill-shake">'
                    '⚠️ يرجى التأكد من كتابة اسمك الكريم ورقم جوالك السعودي (05xxxxxxxx)'
                    '</div>',
                    unsafe_allow_html=True
                )
                components.html("""
                <script>
                    setTimeout(() => {
                        try {
                            const banner = window.parent.document.getElementById('form-top-alert');
                            if (banner) {
                                banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }
                        } catch(e) {}
                    }, 50);
                </script>
                """, height=0, width=0)

            # 2. في حال كان العميل مسجلاً مسبقاً بنفس الرقم
            elif existing_booking:
                st.session_state["confirmed_deal"] = {
                    "name": existing_booking.get("name"),
                    "phone": existing_booking.get("phone"),
                    "perfume": existing_booking.get("level"),
                    "delivery": existing_booking.get("hear_about", delivery_mode),
                    "price": UNIFIED_PRICE
                }
                st.rerun()

            # 3. في حال اكتمال الباقة: رسالة التقدير والاحترام الراقية بدلاً من الخطأ
            elif len(fresh_bookings) >= BASKET_CAPACITY:
                alert_placeholder.markdown(
                    '<div class="waitlist-card">'
                    '✨ <b>شكراً جزيلاً لثقتك واهتمامك يا غالي 🌿</b>'
                    'مقاعد هذه الباقة اكتملت للتو بالكامل، وسعداء جداً برغبتك معنا.<br>'
                    'سنبادر بالتواصل معك فوراً عبر الواتساب في حال توفر مقعد بديل أو مع إطلاق السلة القادمة مباشرة.'
                    '</div>',
                    unsafe_allow_html=True
                )
                components.html("""
                <script>
                    setTimeout(() => {
                        try {
                            const banner = window.parent.document.querySelector('.waitlist-card');
                            if (banner) {
                                banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }
                        } catch(e) {}
                    }, 50);
                </script>
                """, height=0, width=0)

            # 4. إتمام الحجز بنجاح
            else:
                if not supabase:
                    alert_placeholder.error("تعذر الاتصال بقاعدة البيانات. يرجى مراجعة إعدادات Secrets.")
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
                        alert_placeholder.error(f"تعذر إتمام التسجيل في السيرفر: {db_err}")

# ==============================================================================
# 8. لوحة الإدارة المقفلة بخوارزمية HMAC ضد هجمات التوقيت
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
