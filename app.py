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
    return "".join(line.strip() for line in raw.splitlines() if line.strip())

# ==============================================================================
# 2. أنماط واجهة المستخدم المتقدمة (Luxury Dark UI)
# ==============================================================================
st.markdown(clean_html("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container {   
    padding-top: 0.3rem !important; 
    padding-bottom: 2rem !important; 
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

.top-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
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
    font-size: 1.25em;
    font-weight: 900;
    color: #ffffff;
    margin: 0;
}
.sub-headline {
    font-size: 0.82em;
    font-weight: 700;
    color: #94a3b8 !important;
    margin: 3px 0 8px 0;
}

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
    font-size: 0.72em;
    font-weight: 700;
}
.slot-pill.taken {
    background: rgba(16, 185, 129, 0.12);
    border-color: #10b981;
    color: #10b981;
}
.slot-pill.current {
    border-color: #10b981;
    color: #10b981;
    background: rgba(16, 185, 129, 0.05);
    animation: pulse 2s infinite;
}
.slot-pill.available {
    color: #64748b;
    border-style: dashed;
}

div[data-testid="stRadio"]:not(:has(input[name*="delivery_choice"])) div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
}
div[data-testid="stRadio"]:not(:has(input[name*="delivery_choice"])) div[role="radiogroup"] > label {
    width: 100% !important;
    margin: 0 !important;
    background-color: #111827 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 8px !important;
    min-height: 42px !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
    font-size: 0.82em !important;
    box-sizing: border-box !important;
}
div[data-testid="stRadio"]:not(:has(input[name*="delivery_choice"])) div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
}

div[data-testid="stRadio"]:has(input[name*="delivery_choice"]) div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 5px !important;
    margin-bottom: 6px !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_choice"]) div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 8px 10px !important;
    font-size: 0.82em !important;
}

.sensory-card {
    background: #111827;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 6px;
    display: flex;
    flex-direction: column;
    gap: 3px;
}
.sensory-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.sensory-name { font-size: 0.9em; font-weight: 800; color: #ffffff; }
.sensory-tag { font-size: 0.72em; color: #10b981; font-weight: 700; }
.sensory-notes { font-size: 0.76em; color: #94a3b8; }
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

input, textarea { 
    caret-color: #10b981 !important; 
    border-radius: 6px !important; 
    font-size: 0.85em !important; 
    padding: 9px 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background-color: #111827 !important;
    color: #ffffff !important;
}
input:focus, textarea:focus { border-color: #10b981 !important; }

div[data-testid="stFormSubmitButton"] > button {
    background: #10b981 !important;
    color: #022c22 !important;
    font-size: 0.96em !important;
    font-weight: 800 !important;
    height: 46px !important;
    border-radius: 8px !important;
    border: none !important;
}

.notice-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px;
    font-size: 0.8em;
    color: #94a3b8;
    text-align: center;
    line-height: 1.5;
    margin: 6px 0;
}
.trust-strip {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 7px 8px;
    text-align: center;
    font-size: 0.73em;
    color: #94a3b8;
    margin: 5px 0 8px 0;
}
.wa-link-btn {
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
.wa-share-btn {
    display: block;
    background: #030712;
    border: 1px solid #10b981;
    color: #10b981 !important;
    text-align: center;
    padding: 11px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.88em;
    text-decoration: none;
    margin-top: 6px;
}
.warning-pill {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.25);
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
"""), unsafe_allow_html=True)

# ==============================================================================
# 3. إعداد الاتصال والثوابت التجارية
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
LIVE_APP_URL = "https://maqsoom-deals.streamlit.app"

PERFUMES = {
    "عطر روميو (Romeo)": {
        "tag": "رجالي فاخر • أصلي",
        "rating": "4.8 ★",
        "notes": "باتشولي، فانيلا، ومسك"
    },
    "عطر يوجا (Yoga)": {
        "tag": "هادئ ومنعش • أصلي",
        "rating": "4.8 ★",
        "notes": "برغموت، مسك نقي، ونرجس"
    },
    "عطر لونار (Lunar)": {
        "tag": "أناقة للجنسين • أصلي",
        "rating": "4.9 ★",
        "notes": "عنب أسود، باتشولي، وعنبر"
    },
    "عطر لاروزيه (Larose)": {
        "tag": "أنثوي ساحر • أصلي",
        "rating": "5.0 ★",
        "notes": "فانيلا، زنبق أبيض، وياسمين"
    },
    "عطر اليسيوم (Elysium)": {
        "tag": "فخامة ملكية • أصلي",
        "rating": "4.9 ★",
        "notes": "عنبر ملكي، فانيلا، ولافندر"
    },
    "عطر هارت بيت (Heart Beat)": {
        "tag": "حيوي ورومانسي • أصلي",
        "rating": "4.8 ★",
        "notes": "كشمش أسود، مسك، وورد"
    }
}

@st.cache_data(ttl=2)
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
# 4. الرأسية التسويقية ومزامنة المقاعد اللحظية
# ==============================================================================
@st.fragment(run_every="4s")
def render_live_slots():
    current_bookings = get_confirmed_bookings(BASKET_ID)
    taken_count = len(current_bookings)

    slots_markup = "".join([
        f'<div class="slot-pill taken">حصة {i} مكتملة ✓</div>' if i <= taken_count else
        '<div class="slot-pill current">حصتك الآن 🔥</div>' if i == taken_count + 1 else
        f'<div class="slot-pill available">متاح {i}</div>'
        for i in range(1, BASKET_CAPACITY + 1)
    ])

    st.markdown(clean_html(f"""
    <div class="top-card">
        <div class="brand-badge">قسم مشترياتك • عروض بلوم (2+2 مجاناً)</div>
        <div class="headline">تقاسم عروض بلوم Blom</div>
        <div class="sub-headline">تقاسم السعر أنت و 4 أشخاص بالتساوي</div>
        <div class="slots-container">
            {slots_markup}
        </div>
    </div>
    """), unsafe_allow_html=True)

render_live_slots()

# ==============================================================================
# 5. شاشة تأكيد الحصة (Viral Growth Loop)
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(deal['name'])
    safe_perfume = html.escape(deal['perfume'])
    safe_delivery = html.escape(deal['delivery'])

    components.html("""
    <script type="text/javascript">
        if (window.parent && window.parent.clarity) {
            window.parent.clarity('event', 'seat_booked');
        }
    </script>
    """, height=0, width=0)

    st.markdown(clean_html(f"""
    <div class="top-card" style="border-color:#10b981;">
        <div class="brand-badge">تم تأكيد حصتك بنجاح 🌿</div>
        <div class="headline" style="font-size:1.15em;">{safe_perfume}</div>
        <div class="sub-headline" style="color:#cbd5e1 !important;">طريقة الاستلام: {safe_delivery}</div>
        <div style="font-size:1.15em;font-weight:800;color:#ffffff;margin-top:5px;">
            المطلوب عند الاستلام: <span style="color:#10b981;">{UNIFIED_PRICE} ر.س فقط</span>
        </div>
    </div>
    <div class="notice-card">
        🤝 <b>الدفع يد بيد بعد المعاينة والفاتورة</b><br>
        سنتواصل معك عبر الواتساب فور اكتمال الأربعة لتأكيد موعد التسليم مباشرة.
    </div>
    """), unsafe_allow_html=True)

    delivery_note_text = "سأرسل اللوكيشن هنا في الواتساب" if "توصيل" in deal['delivery'] else "موعدنا في السلام مول"

    wa_admin_msg = (
        f"مرحباً 🌿\n"
        f"حجزت حصتي في تطبيق مَقسوم - مجموعة نيوتن ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• الاستلام: {deal['delivery']}\n"
        f"• الموقع: {delivery_note_text}\n\n"
        f"بانتظار اكتمال الباقة لاستلام الطلب مع الفاتورة الرسمية."
    )
    admin_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_admin_msg)}"
    st.markdown(f'<a href="{admin_link}" target="_blank" class="wa-link-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

    share_msg = (
        f"يا غالي، داخلين في باقة عطور بلوم (عرض 2+2 مجاناً) نتقاسمها سوا بالتساوي.\n"
        f"العطر يطلع بـ {UNIFIED_PRICE} ر.س بدل {ORIGINAL_RETAIL} ر.س، والدفع يد بيد بعد فحص الفاتورة الأصلية في جدة والتوصيل مجاني أول ما تكتمل.\n\n"
        f"حجزت حصتي وباقي مقاعد بسيطة، ادخل اختر عطرك وقفل الباقة معنا هنا:\n"
        f"{LIVE_APP_URL}"
    )
    share_link = f"https://wa.me/?text={urllib.parse.quote(share_msg)}"
    st.markdown(f'<a href="{share_link}" target="_blank" class="wa-share-btn">👥 شارك العرض مع خويك لتكتمل الباقة أسرع</a>', unsafe_allow_html=True)

    if st.button("تعديل الاختيار أو حجز مقعد آخر", use_container_width=True):
        del st.session_state["confirmed_deal"]
        st.rerun()

# ==============================================================================
# 6. النموذج واختيار العطر
# ==============================================================================
else:
    st.markdown("<div style='font-size:0.82em;font-weight:700;color:#cbd5e1;margin-bottom:4px;'>1. اختر عِطرك من مجموعة نيوتن (Newton):</div>", unsafe_allow_html=True)

    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed"
    )

    p = PERFUMES[chosen_perfume]
    st.markdown(clean_html(f"""
    <div class="sensory-card">
        <div class="sensory-header-row">
            <span class="sensory-name">{chosen_perfume}</span>
            <span class="sensory-tag">{p['rating']} • {p['tag']}</span>
        </div>
        <div class="sensory-notes">المكونات: {p['notes']}</div>
        <div class="price-chip">
            <span style="color:#cbd5e1;">السعر الفردي: <s style="color:#64748b;">{ORIGINAL_RETAIL} ر.س</s> ➔ <b style="color:#10b981;font-size:1.1em;">{UNIFIED_PRICE} ر.س</b></span>
            <span style="color:#10b981;">وفرت {SAVINGS_AMOUNT} ر.س (خصم 50%)</span>
        </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.82em;font-weight:700;color:#cbd5e1;margin-top:6px;margin-bottom:4px;'>2. حدد طريقة الاستلام:</div>", unsafe_allow_html=True)

    delivery_mode = st.radio(
        "طريقة الاستلام والدفع:",
        [
            f"استلام يد بيد (السلام مول) — {UNIFIED_PRICE} ر.س عند الاستلام",
            f"توصيل مجاني داخل جدة — {UNIFIED_PRICE} ر.س عند الاستلام"
        ],
        key="delivery_choice",
        label_visibility="collapsed"
    )

    if "توصيل" in delivery_mode:
        st.markdown("<div style='font-size:0.75em;color:#10b981;margin-bottom:6px;'>📍 اللوكيشن يتم إرساله مباشرة وسريعاً عبر الواتساب عند اكتمال الباقة.</div>", unsafe_allow_html=True)

    with st.form("quick_order_form"):
        st.markdown("<div style='font-size:0.82em;font-weight:700;color:#cbd5e1;margin-bottom:4px;'>بيانات التأكيد:</div>", unsafe_allow_html=True)

        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")

        st.markdown("""
        <div class="trust-strip">
            🛡️ فحص العطر والفاتورة الأصلية قبل الدفع يد بيد • لا يوجد أي تحويل مسبق
        </div>
        """, unsafe_allow_html=True)

        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت حصتك في العرض ({UNIFIED_PRICE} ر.س عند الاستلام)", use_container_width=True)

        if submit_btn and not hp:
            clean_name = f_name.strip()
            
            # توحيد الأرقام وتنقية أرقام الجوال العربية
            trans_table = str.maketrans("٠١٢٣٤٥٦٧٨٩", "01234
