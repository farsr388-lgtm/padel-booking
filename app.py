import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة والبيئة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم جدة | قطة عطور درعة",
    page_icon="🧴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع الجلسات والخرائط الحرارية (Microsoft Clarity)
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
# 2. أنماط الواجهة (CSS احترافي خالي من الأحمر + انتقال سلس للمقاعد)
# ==============================================================================
st.markdown("""
<style>
/* تفعيل النزول الانسيابي عند الضغط على المقاعد */
html {
    scroll-behavior: smooth;
}

/* إخفاء القوائم الافتراضية لستريمليت */
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.8rem !important; 
    padding-bottom: 2.5rem !important; 
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

/* اقتلاع اللون الأحمر نهائياً من حقول الإدخال */
input, textarea, select { 
    caret-color: #10b981 !important; 
}
input:focus, textarea:focus, select:focus, 
div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* ضبط أزرار الراديو باللون الأخضر المريح */
div[role="radiogroup"] label div:first-child { 
    border-color: #10b981 !important; 
}
div[role="radiogroup"] label div:first-child div { 
    background-color: #10b981 !important; 
}

/* بطاقة الهيدر العلوية */
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
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 6px;
}
.store-title { 
    font-size: 1.35em; 
    font-weight: 900; 
    color: #ffffff; 
    margin: 4px 0; 
}
.store-desc { 
    font-size: 0.84em; 
    color: #94a3b8; 
    line-height: 1.5; 
    margin-bottom: 10px; 
}

/* شريط السعر الصريح */
.price-strip {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-around;
    align-items: center;
}
.price-col { text-align: center; }
.price-now { font-size: 1.4em; font-weight: 900; color: #10b981; }
.price-old { font-size: 0.85em; color: #64748b; text-decoration: line-through; }
.price-lbl { font-size: 0.7em; color: #94a3b8; }

/* كروت المقاعد الثلاثة */
.seats-wrapper {
    display: flex;
    gap: 8px;
    margin: 12px 0;
}
.seat-card {
    flex: 1;
    border-radius: 10px;
    padding: 10px 4px;
    text-align: center;
    font-size: 0.78em;
    line-height: 1.4;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.seat-occupied {
    background: rgba(16, 185, 129, 0.1);
    border: 1.5px solid #10b981;
    color: #f1f5f9;
    pointer-events: none;
}
.seat-available {
    background: rgba(30, 41, 59, 0.5);
    border: 1.5px dashed #10b981;
    color: #94a3b8;
    cursor: pointer;
}
.seat-available:hover {
    transform: translateY(-2px);
    background: rgba(16, 185, 129, 0.08);
}

/* كرت العطر */
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
    width: 75px;
    height: 75px;
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

/* شاشة بعد الحجز */
.success-card {
    background: rgba(16, 185, 129, 0.1);
    border: 1.5px solid #10b981;
    border-radius: 14px;
    padding: 18px 14px;
    text-align: center;
    margin-top: 10px;
}
.notice-box {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 12px;
    font-size: 0.85em;
    color: #94a3b8;
    line-height: 1.6;
    margin: 12px 0;
    text-align: center;
}

/* زر الحجز الأساسي */
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
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 14px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 1em;
    text-decoration: none;
    margin-top: 10px;
}

/* إخفاء حقل الحماية ضد البوتات */
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
# 3. الربط بقاعدة البيانات وتجهيز الكتالوج
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

BASKET_ID = "MAQSOOM-JEDDAH-BASKET-01"
BASKET_CAPACITY = 3
ADMIN_PHONE = "966566261868"

raw_secret = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")
ADMIN_PASSWORD_HASH = str(raw_secret).strip()

PERFUMES = {
    "عطر ليدر (Leader) 100مل": {
        "tag": "الأكثر طلباً ورسمية",
        "desc": "طابع فخم ورسمي للمناسبات والدوام (يشبه خط كريد أفينتوس)",
        "notes": "أناناس مدخن، برغموت، وأخشاب فاخرة",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=250&q=80"
    },
    "عطر لينك الأسود (Link Black) 100مل": {
        "tag": "رقم 1 الأكثر مبيعاً",
        "desc": "رائحة انتعاش ونظافة يومية فواحة تدوم طويلاً",
        "notes": "حمضيات منعشة، ياسمين، ومسك نقي",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=250&q=80"
    },
    "عطر بورموا (Pour Moi) 100مل": {
        "tag": "خيار ناعم ومريح",
        "desc": "طابع سويت هادئ وراقي جداً وملائم للإهداء",
        "notes": "فواكه ناعمة، ياسمين أبيض، فانيلا فرنسية",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=250&q=80"
    },
    "عطر خواطر (Khawater) 100مل": {
        "tag": "طابع شرقي كلاسيكي",
        "desc": "ثبات وفوحان عالي بلمسة بخور أنيقة للمجالس",
        "notes": "بخور خفيف، باتشولي دافئ، وعنبر",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=250&q=80"
    },
    "عطر سول (Soul) 100مل": {
        "tag": "شبابي وعصري",
        "desc": "عطر مناسب للطلعات واللقاءات المسائية",
        "notes": "هيل عطري، لافندر هادئ، وخشب الصندل",
        "img": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=250&q=80"
    },
    "عطر ميس درعة (Miss Deraah) 100مل": {
        "tag": "بودري وزهري ناعم",
        "desc": "ناعم وأنيق ومثالي للإهداء للأهل",
        "notes": "زهور الياسمين، باودر ومسك مخملي",
        "img": "https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=250&q=80"
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
# 4. الواجهة الرئيسية
# ==============================================================================
st.markdown(f"""
<div class="store-header">
    <div class="store-badge">تنسيق شراء تشاركي بجدة • 3 مقاعد فقط</div>
    <div class="store-title">قطّة عطور درعة (1+2 مجاناً)</div>
    <div class="store-desc">
        نقتسم عرض درعة الكبرى بين 3 أشخاص؛ نشتري السلة سوا من فرع درعة بالأندلس مول، 
        وعِطرك الأصلي 100مل يطلع عليك بسعر التكلفة الصافي:
    </div>
    <div class="price-strip">
        <div class="price-col">
            <div class="price-now">63 ر.س</div>
            <div class="price-lbl">سعر حصتك بالقطة</div>
        </div>
        <div style="color:#334155; font-size:1.2em;">|</div>
        <div class="price-col">
            <div class="price-old">210 ر.س</div>
            <div class="price-lbl">سعره الفردي بالمعرض</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# المقاعد الثلاثة مع تحويل المقاعد المتاحة لأزرار انتقال فورية
st.markdown(f"<div style='font-size:0.85em; font-weight:700; color:#cbd5e1; margin-bottom:4px;'>حالة السلة الحالية (متبقي {slots_left} مقاعد):</div>", unsafe_allow_html=True)

slots_html = []
for i in range(BASKET_CAPACITY):
    if i < taken_count:
        item = current_bookings[i]
        c_name = html.escape(item.get('name', 'مشترك').split()[0])
        p_name = html.escape(item.get('level', 'عطر محجوز'))
        slots_html.append(
            f'<div class="seat-card seat-occupied">'
            f'🧴 <b>{c_name}</b><br>'
            f'<span style="color:#94a3b8; font-size:0.85em;">{p_name}</span><br>'
            f'<span style="color:#34d399; font-weight:700;">محجوز ✅</span>'
            f'</div>'
        )
    else:
        label_text = "المقعد الأخير 🔥" if slots_left == 1 else f"مقعد متاح #{i+1}"
        slots_html.append(
            f'<a href="#order_section" style="text-decoration:none; flex:1; display:flex;">'
            f'<div class="seat-card seat-available" style="width:100%;">'
            f'✨ <b>{label_text}</b><br>'
            f'<span style="color:#10b981; font-weight:700; font-size:0.82em;">احجز الآن 👇</span><br>'
            f'<span style="color:#38bdf8; font-weight:700;">63 ر.س</span>'
            f'</div>'
            f'</a>'
        )

st.markdown(f'<div class="seats-wrapper">{"".join(slots_html)}</div>', unsafe_allow_html=True)

# ==============================================================================
# 5. شاشة ما بعد الحجز
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    
    st.markdown(f"""
    <div class="success-card">
        <h3 style="color:#10b981; margin:0 0 6px 0; font-size:1.3em;">🎉 تم تثبيت مقعدك بنجاح!</h3>
        <div style="font-size:0.95em; color:#e2e8f0; margin:4px 0;">
            العطر: <b>{deal['perfume']}</b>
        </div>
        <div style="font-size:0.88em; color:#94a3b8; margin:2px 0;">
            طريقة الاستلام: <b>{deal['delivery']}</b>
        </div>
        <div style="font-size:1.2em; color:#ffffff; margin-top:8px;">
            المبلغ المطلوب عند الاستلام: <b style="color:#10b981;">{deal['price']} ر.س فقط</b>
        </div>
    </div>
    
    <div class="notice-box">
        🤝 <b>الدفع عند الاستلام يد بيد بالأندلس مول</b><br>
        لا يلزمك تحويل أي مبلغ الآن. سنتواصل معك عبر الواتساب فور شراء السلة لتنسيق اللقاء واستلام عِطرك مع الفاتورة الرسمية.
    </div>
    """, unsafe_allow_html=True)
    
    wa_msg = (
        f"مرحباً يا غالي 🛍️\n"
        f"حجزت مقعدي في سلة درعة ({deal['price']} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• الاستلام: {deal['delivery']}\n\n"
        f"أرسل هذه الرسالة لتأكيد التواصل عبر الواتساب!"
    )
    wa_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 6. نموذج الحجز
