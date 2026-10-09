import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة وتتبع الجلسات
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | تقاسم عروض بلوم - نيوتن",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع Microsoft Clarity الأساسي
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
    """تجريد المسافات البادئة لحماية المحرك من الانهيار النصي."""
    return "".join(line.strip() for line in raw.splitlines() if line.strip())

# ==============================================================================
# 2. أنماط الواجهة (Minimal Dark Luxury - خالية من الإطارات الحمراء والتعقيد)
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
    font-size: 1.22em;
    font-weight: 900;
    color: #ffffff;
    margin: 0;
}
.sub-headline {
    font-size: 0.82em;
    font-weight: 700;
    color: #ffffff !important;
    margin: 2px 0 8px 0;
}

/* شريط الحصص الأربعة */
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

/* شبكة العطور المتقابلة (3 في اليمين ضد 3 في اليسار) */
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
    box-sizing: border-box !important;
    transition: all 0.15s ease-in-out !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:hover {
    border-color: rgba(16, 185, 129, 0.3) !important;
    background-color: #141e33 !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* حماية المؤشر من أي وميض أحمر */
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

/* بطاقة العطر بدون صور وبمكونات مختصرة وسعر مباشر */
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
.sensory-name {
    font-size: 0.88em;
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
}
.price-chip {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 6px;
    padding: 5px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.75em;
    font-weight: 700;
    margin-top: 3px;
}

/* النموذج وحقول الإدخال */
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
    font-size: 0.95em !important;
    font-weight: 800 !important;
    height: 44px !important;
    border-radius: 8px !important;
    border: none !important;
    margin-top: 4px !important;
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
    padding: 6px 8px;
    text-align: center;
    font-size: 0.72em;
    color: #94a3b8;
    margin: 4px 0 6px 0;
}
.wa-link-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 11px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 0.92em;
    text-decoration: none;
    margin-top: 6px;
}
.wa-share-btn {
    display: block;
    background: #030712;
    border: 1px solid #10b981;
    color: #10b981 !important;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.85em;
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

/* مصيدة البوتات الخفية */
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
# 3. إدارة قاعدة البيانات والكتالوج المختصر
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

BASKET_ID = "BLOM-NEWTON-JEDDAH-V11"
BASKET_CAPACITY = 4
UNIFIED_PRICE = 132
ORIGINAL_RETAIL = 265
SAVINGS_AMOUNT = ORIGINAL_RETAIL - UNIFIED_PRICE
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "")
LIVE_APP_URL = "https://maqsoom-deals.streamlit.app"

# كتالوج مختصر بدون صور وبنوتات سريعة (3 يمين مقابل 3 يسار)
PERFUMES = {
    # صف 1: روميو مقابل يوجا
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
    # صف 2: لونار مقابل لاروزيه
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
    # صف 3: اليسيوم مقابل هارت بيت
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

@st.cache_data(ttl=3)
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
remaining_spots = max(0, BASKET_CAPACITY - taken_count)

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
    <div class="brand-badge">قسم مشترياتك • عروض بلوم (2+2 مجاناً)</div>
    <div class="headline">تقاسم عروض بلوم Blom</div>
    <div class="sub-headline">تقاسم السعر أنت و 4 أشخاص</div>
    <div class="slots-container">
        {slots_html}
    </div>
</div>
""")
st.markdown(header_markup, unsafe_allow_html=True)

# ==============================================================================
# 5. شاشة تأكيد الحصة (مع إرسال حدث Clarity وتفعيل الحلقة الفيروسية)
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(deal['name'])
    safe_perfume = html.escape(deal['perfume'])
    safe_delivery = html.escape(deal['delivery'])
    
    # إرسال حدث تحويل مخصص لـ Clarity لفلترة المشترين الحقيقيين فقط
    components.html("""
    <script type="text/javascript">
        if (window.parent && window.parent.clarity) {
            window.parent.clarity('event', 'seat_booked');
        }
    </script>
    """, height=0, width=0)
    
    confirm_markup = clean_html(f"""
    <div class="top-card" style="border-color:#10b981;">
        <div class="brand-badge">تم تأكيد حصتك بنجاح 🌿</div>
        <div class="headline" style="font-size:1.1em;">{safe_perfume}</div>
        <div class="sub-headline" style="color:#cbd5e1 !important;">طريقة الاستلام: {safe_delivery}</div>
        <div style="font-size:1.15em;font-weight:800;color:#ffffff;margin-top:4px;">
            المطلوب عند الاستلام: <span style="color:#10b981;">{UNIFIED_PRICE} ر.س فقط</span>
        </div>
    </div>
    <div class="notice-card">
        🤝 <b>الدفع يد بيد بعد المعاينة والفاتورة</b><br>
        سنتواصل معك عبر الواتساب فور اكتمال الأربعة لتأكيد موعد التسليم مباشرة.
    </div>
    """)
    st.markdown(confirm_markup, unsafe_allow_html=True)
    
    wa_admin_msg = (
        f"مرحباً 🌿\n"
        f"حجزت حصتي في تطبيق مَقسوم - مجموعة نيوتن ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• الاستلام: {deal['delivery']}\n\n"
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
    
    sensory_markup = clean_html(f"""
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
    """)
    st.markdown(sensory_markup, unsafe_allow_html=True)
    
    with st.form("quick_order_form"):
        st.markdown("<div style='font-size:0.82em;font-weight:700;color:#cbd5e1;margin-bottom:4px;'>2. بياناتك وطريقة الاستلام:</div>", unsafe_allow_html=True)
        
        # 1. الاسم الكريم
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        
        # 2. رقم الجوال
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
        
        # 3. خيارات الاستلام تحتهما مباشرة
        delivery_mode = st.radio(
            "طريقة الاستلام والدفع:",
            [
                f"استلام يد بيد (السلام مول) — {UNIFIED_PRICE} ر.س عند الاستلام",
                f"توصيل مجاني داخل جدة — {UNIFIED_PRICE} ر.س عند الاستلام"
            ]
        )
        
        # 4. الحي (حل النقطة العمياء لتفادي ملاحقة العميل على العنوان)
        f_district = st.text_input("الحي السكني داخل جدة (في حال التوصيل):", placeholder="مثال: الروضة، الصفا، السامر")
        
        st.markdown("""
        <div class="trust-strip">
            🛡️ فحص العطر والفاتورة الأصلية قبل الدفع يد بيد • لا يوجد أي تحويل مسبق
        </div>
        """, unsafe_allow_html=True)
        
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت حصتك في العرض ({UNIFIED_PRICE} ر.س عند الاستلام)", use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            clean_district = f_district.strip() if f_district else "غير محدد"
            
            # فحص فوري ومباشر من قاعدة البيانات لمنع تضارب الحجز
            fresh_bookings = get_confirmed_bookings(BASKET_ID)
            existing_booking = next((b for b in fresh_bookings if b.get('phone') == clean_phone), None)
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.markdown('<div class="warning-pill">⚠️ يرجى التأكد من كتابة الاسم الثنائي ورقم جوال سعودي يبدأ بـ 05.</div>', unsafe_allow_html=True)
            elif existing_booking:
                # استرجاع حجز العميل مباشرة لمنع التكرار وحل مشكلة تحديث الصفحة
                st.session_state["confirmed_deal"] = {
                    "name": existing_booking.get("name"),
                    "phone": existing_booking.get("phone"),
                    "perfume": existing_booking.get("level"),
                    "delivery": existing_booking.get("hear_about", delivery_mode),
                    "price": UNIFIED_PRICE
                }
                st.rerun()
            elif len(fresh_bookings) >= BASKET_CAPACITY:
                st.markdown('<div class="warning-pill">⚠️ اكتملت الباقة الحالية بالكامل! جاري فتح باقة جديدة قريباً.</div>', unsafe_allow_html=True)
            else:
                try:
                    delivery_full = f"{delivery_mode} | الحي: {clean_district}"
                    client_note = f"BLOM_NEWTON | {chosen_perfume} | {delivery_full} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"
                    
                    if supabase:
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": BASKET_ID,
                            "court": 1,
                            "level": chosen_perfume,
                            "status": "confirmed",
                            "payment_status": "pending",
                            "hear_about": delivery_full[:40],
                            "player_note": client_note
                        }).execute()
                        st.cache_data.clear()
                except Exception:
                    pass
                
                st.session_state["confirmed_deal"] = {
                    "name": clean_name,
                    "phone": clean_phone,
                    "perfume": chosen_perfume,
                    "delivery": f"{delivery_mode} ({clean_district})",
                    "price": UNIFIED_PRICE
                }
                st.rerun()

# ==============================================================================
# 7. لوحة المشرف والتحليلات (Admin & Analytics Console)
# ==============================================================================
query_params = st.query_params
if query_params.get("manage") == "faris":
    st.markdown("---")
    st.caption("لوحة الإدارة والتحليلات السريعة")
    admin_pin = st.text_input("رمز الدخول السري:", type="password", key="adm_key")
    
    if admin_pin and ADMIN_PASSWORD_HASH and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        bookings_list = get_confirmed_bookings(BASKET_ID)
        total_count = len(bookings_list)
        paid_count = sum(1 for b in bookings_list if b.get('payment_status') == 'paid')
        total_val = total_count * UNIFIED_PRICE
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("المقاعد المحجوزة", f"{total_count} / {BASKET_CAPACITY}")
        kpi2.metric("المحصل (مدفوع)", f"{paid_count * UNIFIED_PRICE} ر.س")
        kpi3.metric("إجمالي السلة", f"{total_val} ر.س")
        
        st.markdown("##### قائمة المشتركين:")
        for b in bookings_list:
            card_col, action_col = st.columns([3, 1])
            with card_col:
                st.write(f"**{b.get('name')}** | `{b.get('phone')}`\nالعطر: **{b.get('level')}**\nالتسليم: `{b.get('hear_about')}`")
            with action_col:
                if b.get('payment_status') == 'paid':
                    st.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✓</span>", unsafe_allow_html=True)
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
