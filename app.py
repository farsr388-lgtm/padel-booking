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

# ==============================================================================
# 2. أنماط الواجهة (Minimal Dark Luxury - بدون أي لون أحمر)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.2rem !important; 
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

/* شبكة مقاعد الحصص الأربعة التفاعلية */
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

/* أزرار اختيار العطور في شبكة متقابلة 2x3 */
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

/* بطاقة الحصة المتغيرة غير التقليدية */
.bottle-showcase-card {
    background: #111827;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 12px;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}
.bottle-svg-wrapper {
    width: 66px;
    height: 80px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, rgba(16,185,129,0.08) 0%, rgba(11,15,25,0.9) 70%);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}
.bottle-details {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.bottle-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.bottle-name {
    font-size: 0.9em;
    font-weight: 800;
    color: #ffffff;
}
.bottle-tag {
    font-size: 0.72em;
    color: #10b981;
    font-weight: 700;
}
.bottle-notes {
    font-size: 0.76em;
    color: #94a3b8;
    line-height: 1.3;
}
.price-chip {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 6px;
    padding: 4px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.76em;
    font-weight: 700;
    margin-top: 2px;
}

/* النموذج */
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
""", unsafe_allow_html=True)

# ==============================================================================
# 3. إعداد الاتصال والكتالوج التفاعلي
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

def get_bottle_svg(accent_color: str, glow_color: str) -> str:
    """توليد مجسم هندسي دقيق لزجاجة نيوتن مع الغطاء الذهبي المشجر."""
    return f"""
    <svg width="50" height="74" viewBox="0 0 100 150" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="capGold" x1="0" y1="0" x2="100" y2="0" gradientUnits="userSpaceOnUse">
                <stop stop-color="#CA8A04"/>
                <stop offset="0.5" stop-color="#FDE047"/>
                <stop offset="1" stop-color="#A16207"/>
            </linearGradient>
            <linearGradient id="liquidGrad" x1="50" y1="50" x2="50" y2="140" gradientUnits="userSpaceOnUse">
                <stop stop-color="{accent_color}" stop-opacity="0.25"/>
                <stop offset="1" stop-color="{glow_color}" stop-opacity="0.85"/>
            </linearGradient>
        </defs>
        <!-- غطاء نيوتن المضلع الفاخر -->
        <path d="M35 10 H65 V34 H35 Z" fill="url(#capGold)" rx="2"/>
        <line x1="42" y1="12" x2="42" y2="32" stroke="#78350F" stroke-width="1.5" stroke-dasharray="2 2"/>
        <line x1="50" y1="12" x2="50" y2="32" stroke="#78350F" stroke-width="1.5" stroke-dasharray="2 2"/>
        <line x1="58" y1="12" x2="58" y2="32" stroke="#78350F" stroke-width="1.5" stroke-dasharray="2 2"/>
        <rect x="42" y="34" width="16" height="6" fill="#D97706"/>
        
        <!-- جسم الزجاجة المنحوت -->
        <path d="M26 44 C26 40 40 40 50 40 C60 40 74 40 74 44 L84 68 C86 74 86 130 80 142 C74 146 62 148 50 148 C38 148 26 146 20 142 C14 130 14 74 16 68 Z" 
              fill="url(#liquidGrad)" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
        
        <!-- حواف التضليع الكريستالي -->
        <path d="M30 65 L50 90 L70 65" stroke="rgba(255,255,255,0.3)" stroke-width="1.5" fill="none"/>
        <path d="M25 90 L50 118 L75 90" stroke="rgba(255,255,255,0.25)" stroke-width="1.5" fill="none"/>
        <rect x="36" y="86" width="28" height="20" rx="2" fill="rgba(15,23,42,0.85)" stroke="#F59E0B" stroke-width="0.8"/>
        <line x1="40" y1="96" x2="60" y2="96" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    """

# كتالوج العطور مع طابع وألوان الهوية الحسية
PERFUMES = {
    "عطر يوجا (Yoga)": {
        "tag": "هادئ ومنعش • أصلي",
        "notes": "برغموت إيطالي • نرجس • مسك قطني نظيف",
        "accent": "#10B981",
        "glow": "#059669"
    },
    "عطر هارت بيت (Heart Beat)": {
        "tag": "الأكثر طلباً • أصلي",
        "notes": "كشمش أسود • ورد جوري • مسك مخملي",
        "accent": "#F43F5E",
        "glow": "#BE123C"
    },
    "عطر روميو (Romeo)": {
        "tag": "رجالي فاخر • أصلي",
        "notes": "هيل • باتشولي إندونيسي • فانيلا معتقة",
        "accent": "#D97706",
        "glow": "#78350F"
    },
    "عطر لونار (Lunar)": {
        "tag": "غامض ومميز • أصلي",
        "notes": "عنب أسود • باتشولي عميق • عنبر دافئ",
        "accent": "#38BDF8",
        "glow": "#1D4ED8"
    },
    "عطر لاروزيه (Larose)": {
        "tag": "أنثوي ساحر • أصلي",
        "notes": "ياسمين رقيق • زنبق • لمسة صندل",
        "accent": "#F472B6",
        "glow": "#9D174D"
    },
    "عطر اليسيوم (Elysium)": {
        "tag": "فخامة ملكية • أصلي",
        "notes": "لافندر فرنسي • توابل دافئة • عنبر ملكي",
        "accent": "#FBBF24",
        "glow": "#B45309"
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

# توليد حبات الحصص التفاعلية
slots_html = ""
for i in range(1, BASKET_CAPACITY + 1):
    if i <= taken_count:
        slots_html += f'<div class="slot-pill taken">حصة {i} مكتملة ✓</div>'
    elif i == taken_count + 1:
        slots_html += f'<div class="slot-pill" style="border-color:#10b981; color:#10b981; background:rgba(16,185,129,0.05);">حصتك الآن 🔥</div>'
    else:
        slots_html += f'<div class="slot-pill available">متاح {i}</div>'

# ==============================================================================
# 4. الرأسية التسويقية ومقاعد الحصص
# ==============================================================================
st.markdown(f"""
<div class="top-card">
    <div class="brand-badge">تطبيق مَقسوم • عرض بلوم (2+2 مجاناً)</div>
    <div class="headline">نفس الجودة. نصف السعر.</div>
    <div class="sub-headline">عطرك بـ {UNIFIED_PRICE} ر.س بدلاً من {ORIGINAL_RETAIL} ر.س (مقسوم بالتساوي)</div>
    <div class="slots-container">
        {slots_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. شاشة تأكيد الحصة
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(deal['name'])
    safe_perfume = html.escape(deal['perfume'])
    safe_delivery = html.escape(deal['delivery'])
    
    st.markdown(f"""
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
    """, unsafe_allow_html=True)
    
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
    svg_code = get_bottle_svg(p["accent"], p["glow"])
    
    st.markdown(f"""
    <div class="bottle-showcase-card">
        <div class="bottle-svg-wrapper">
            {svg_code}
        </div>
        <div class="bottle-details">
            <div class="bottle-title-row">
                <span class="bottle-name">{chosen_perfume}</span>
                <span class="bottle-tag">{p['tag']}</span>
            </div>
            <div class="bottle-notes">{p['notes']}</div>
            <div class="price-chip">
                <span style="color:#cbd5e1;">السعر الفردي: <s style="color:#64748b;">{ORIGINAL_RETAIL} ر.س</s> ➔ <b style="color:#10b981;">{UNIFIED_PRICE} ر.س</b></span>
                <span style="color:#10b981;">وفرت {SAVINGS_AMOUNT} ر.س</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
