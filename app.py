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
    page_title="مَقسوم | تقاسم عروض بلوم - نيوتن",
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
    """تنظيف تام للنصوص البرمجية لمنع ثغرة الـ Markdown Indentation."""
    return "".join(line.strip() for line in raw.splitlines() if line.strip())

# ==============================================================================
# 2. أنماط الواجهة (Minimal Dark Luxury - بدون أي لون أحمر)
# ==============================================================================
css_styles = clean_html("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.3rem !important; 
    padding-bottom: 1.5rem !important; 
    max-width: 410px !important; 
    margin: 0 auto; 
}

html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f8fafc;
}

/* بطاقة الهيدر العلوية */
.top-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 8px;
    text-align: center;
}
.brand-badge {
    color: #10b981;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.72em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 4px;
}
.headline {
    font-size: 1.2em;
    font-weight: 900;
    color: #ffffff;
    margin: 0;
}
.sub-headline {
    font-size: 0.8em;
    color: #94a3b8;
    margin: 2px 0 8px 0;
}

/* شبكة الحصص الأربعة */
.slots-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    margin-bottom: 4px;
}
.slot-pill {
    background: #030712;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 6px 2px;
    text-align: center;
    font-size: 0.7em;
    font-weight: 700;
}
.slot-pill.taken {
    background: rgba(16, 185, 129, 0.12);
    border-color: #10b981;
    color: #10b981;
}
.slot-pill.available {
    color: #64748b;
    border-style: dashed;
}

/* شبكة أزرار الاختيار المتقابلة */
div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label {
    width: 100% !important;
    margin: 0 !important;
    background-color: #111827 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 7px 8px !important;
    min-height: 40px !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
    font-size: 0.8em !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:hover {
    border-color: rgba(16, 185, 129, 0.3) !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
}

/* إزالة اللون الأحمر تماماً من دوائر الراديو */
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

/* بطاقة استعراض العطر الحسي الفاخر */
.sensory-card {
    background: #111827;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 12px;
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}
.sensory-badge-icon {
    width: 60px;
    height: 60px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8em;
    background: #030712;
    border: 1px solid rgba(255, 255, 255, 0.08);
    flex-shrink: 0;
}
.sensory-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.sensory-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.sensory-name {
    font-size: 0.9em;
    font-weight: 800;
    color: #ffffff;
}
.sensory-tag {
    font-size: 0.72em;
    color: #10b981;
    font-weight: 700;
}
.sensory-notes {
    font-size: 0.76em;
    color: #94a3b8;
    line-height: 1.3;
}
.price-chip {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 6px;
    padding: 5px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.76em;
    font-weight: 700;
    margin-top: 4px;
}

/* النموذج والمدخلات */
form div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
    margin: 4px 0 6px 0 !important;
}
form div[data-testid="stRadio"] div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 6px !important;
    padding: 6px 10px !important;
    margin: 0 !important;
    font-size: 0.8em !important;
}

div[data-testid="stTextInput"] { margin-bottom: 4px !important; }
input, textarea { 
    caret-color: #10b981 !important; 
    border-radius: 6px !important; 
    font-size: 0.84em !important; 
    padding: 8px 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background-color: #111827 !important;
    color: #ffffff !important;
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within { 
    border-color: #10b981 !important; 
    box-shadow: 0 0 0 1px #10b981 !important; 
}
div[data-baseweb="input"] { border-color: rgba(255, 255, 255, 0.1) !important; }

div[data-testid="stFormSubmitButton"] > button {
    background: #10b981 !important;
    color: #022c22 !important;
    font-size: 0.9em !important;
    font-weight: 800 !important;
    height: 42px !important;
    border-radius: 6px !important;
    border: none !important;
    margin-top: 4px !important;
}

.notice-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 8px;
    font-size: 0.78em;
    color: #94a3b8;
    text-align: center;
    line-height: 1.4;
    margin: 6px 0;
}
.wa-link-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.9em;
    text-decoration: none;
    margin-top: 6px;
}
.warning-pill {
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.25);
    color: #fcd34d;
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 0.78em;
    font-weight: 600;
    margin-bottom: 6px;
}

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
# 3. إدارة قاعدة البيانات والكتالوج الحسي
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

# كتالوج العطور الحسي المعزول عن مشاكل الشبكات وروابط الصور الخارجية
PERFUMES = {
    "عطر يوجا (Yoga)": {
        "tag": "هادئ ومنعش • أصلي",
        "icon": "🍋",
        "notes": "برغموت إيطالي • نرجس ندي • مسك قطني نظيف"
    },
    "عطر هارت بيت (Heart Beat)": {
        "tag": "الأكثر طلباً • أصلي",
        "icon": "🌹",
        "notes": "كشمش أسود • ورد جوري مخملي • مسك جذاب"
    },
    "عطر روميو (Romeo)": {
        "tag": "رجالي فاخر • أصلي",
        "icon": "🪵",
        "notes": "حبوب هيل • باتشولي إندونيسي • فانيلا معتقة"
    },
    "عطر لونار (Lunar)": {
        "tag": "غامض ومميز • أصلي",
        "icon": "🌊",
        "notes": "عنب أسود • عنبر بحري عميق • لمسات خشبية"
    },
    "عطر لاروزيه (Larose)": {
        "tag": "أنثوي ساحر • أصلي",
        "icon": "🌸",
        "notes": "ياسمين رقيق • زنبق أبيض • أخشاب صندل ناعمة"
    },
    "عطر اليسيوم (Elysium)": {
        "tag": "فخامة ملكية • أصلي",
        "icon": "👑",
        "notes": "لافندر فرنسي • توابل دافئة • عنبر ملكي فاخر"
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

# شريط مقاعد الحصص التفاعلي
slots_html = "".join([
    f'<div class="slot-pill taken">حصة {i} مكتملة ✓</div>' if i <= taken_count else
    '<div class="slot-pill" style="border-color:#10b981; color:#10b981; background:rgba(16,185,129,0.05);">حصتك الآن 🔥</div>' if i == taken_count + 1 else
    f'<div class="slot-pill available">متاح {i}</div>'
    for i in range(1, BASKET_CAPACITY + 1)
])

# ==============================================================================
# 4. الرأسية التسويقية
# ==============================================================================
header_markup = clean_html(f"""
<div class="top-card">
    <div class="brand-badge">تطبيق مَقسوم • عرض بلوم (2+2 مجاناً)</div>
    <div class="headline">نفس الجودة. نصف السعر.</div>
    <div class="sub-headline">عطرك بـ {UNIFIED_PRICE} ر.س بدلاً من {ORIGINAL_RETAIL} ر.س (مقسوم بالتساوي)</div>
    <div class="slots-container">
        {slots_html}
    </div>
</div>
""")
st.markdown(header_markup, unsafe_allow_html=True)

# ==============================================================================
# 5. شاشة تأكيد الحصة
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(deal['name'])
    safe_perfume = html.escape(deal['perfume'])
    safe_delivery = html.escape(deal['delivery'])
    
    confirm_markup = clean_html(f"""
    <div class="top-card" style="border-color:#10b981;">
        <div class="brand-badge">تم تأكيد حصتك في الباقة</div>
        <div class="headline" style="font-size:1.1em;">{safe_perfume}</div>
        <div class="sub-headline">{safe_delivery}</div>
        <div style="font-size:1.15em;font-weight:800;color:#ffffff;margin-top:4px;">
            المطلوب عند الاستلام: <span style="color:#10b981;">{UNIFIED_PRICE} ر.س</span>
        </div>
    </div>
    <div class="notice-card">
        🤝 <b>الدفع عند الاستلام يد بيد</b><br>
        سنتواصل معك عبر الواتساب فور اكتمال الباقة وتجهيز طلبك مع الفاتورة.
    </div>
    """)
    st.markdown(confirm_markup, unsafe_allow_html=True)
    
    wa_msg = (
        f"مرحباً 🌿\n"
        f"سجلت اهتمامي في تطبيق مَقسوم - مجموعة نيوتن ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• الاستلام: {deal['delivery']}\n\n"
        f"بانتظار اكتمال الباقة لتأكيد موعد التسليم."
    )
    wa_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-link-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 6. النموذج واختيار العطر
# ==============================================================================
else:
    st.markdown("<div style='font-size:0.8em;font-weight:700;color:#94a3b8;margin-bottom:4px;'>1. حدد عِطرك من مجموعة نيوتن:</div>", unsafe_allow_html=True)
    
    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed"
    )
    
    p = PERFUMES[chosen_perfume]
    
    sensory_markup = clean_html(f"""
    <div class="sensory-card">
        <div class="sensory-badge-icon">{p['icon']}</div>
        <div class="sensory-content">
            <div class="sensory-title-row">
                <span class="sensory-name">{chosen_perfume}</span>
                <span class="sensory-tag">{p['tag']}</span>
            </div>
            <div class="sensory-notes">{p['notes']}</div>
            <div class="price-chip">
                <span style="color:#cbd5e1;">السعر الفردي: <s style="color:#64748b;">{ORIGINAL_RETAIL} ر.س</s> ➔ <b style="color:#10b981;">{UNIFIED_PRICE} ر.س</b></span>
                <span style="color:#10b981;">وفرت {SAVINGS_AMOUNT} ر.س</span>
            </div>
        </div>
    </div>
    """)
    st.markdown(sensory_markup, unsafe_allow_html=True)
    
    with st.form("quick_order_form"):
        st.markdown("<div style='font-size:0.8em;font-weight:700;color:#94a3b8;margin-bottom:4px;'>2. بيانات التأكيد والاستلام:</div>", unsafe_allow_html=True)
        
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
        
        delivery_mode = st.radio(
            "طريقة الاستلام والدفع:",
            [
                f"استلام يد بيد (السلام مول) — {UNIFIED_PRICE} ر.س",
                f"توصيل داخل جدة — {UNIFIED_PRICE} ر.س"
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
                st.markdown('<div class="warning-pill">⚠️ يرجى التأكد من كتابة الاسم ورقم جوال يبدأ بـ 05.</div>', unsafe_allow_html=True)
            else:
                try:
                    if supabase:
                        client_note = f"BLOM_NEWTON | {chosen_perfume} | {delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"
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
                except Exception:
                    pass
                
                st.session_state["confirmed_deal"] = {
                    "name": clean_name,
                    "phone": clean_phone,
                    "perfume": chosen_perfume,
                    "delivery": delivery_mode,
                    "price": UNIFIED_PRICE
                }
                st.rerun()

# ==============================================================================
# 7. بوابة المشرف المعزولة
# ==============================================================================
query_params = st.query_params
if query_params.get("manage") == "faris":
    st.markdown("---")
    st.caption("لوحة التحكم")
    admin_pin = st.text_input("رمز الدخول:", type="password", key="adm_key")
    
    if admin_pin and ADMIN_PASSWORD_HASH and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        bookings_list = get_confirmed_bookings(BASKET_ID)
        for b in bookings_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{b.get('name')}** - `{b.get('level', '-')}`\n`{b.get('phone')}`")
            if b.get('payment_status') == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#71717a;'>محجوز</span>", unsafe_allow_html=True)
                if col3.button("اعتماد", key=f"pay_{b.get('id')}"):
                    if supabase:
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", b.get('id')).execute()
                    st.cache_data.clear()
                    st.rerun()
