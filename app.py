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
# 2. أنماط الواجهة فائقة الدمج (Two-Tone System & Zero Margins)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 1.5rem !important; 
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

/* -------------------------------------------------------------------------- */
/* الصندوق العلوي المدمج (العنوان + العداد + السعر في مربع واحد)              */
/* -------------------------------------------------------------------------- */
.compact-header {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
    text-align: center;
}
.header-badge {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 14px;
    padding: 2px 10px;
    font-size: 0.72em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 4px;
}
.header-title {
    font-size: 1.22em;
    font-weight: 900;
    color: #ffffff;
    margin: 2px 0;
}
.header-msg {
    font-size: 0.85em;
    font-weight: 700;
    color: #ffffff !important;
    margin-bottom: 8px;
}

/* شريط السعة الداخلي */
.capacity-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.76em;
    font-weight: 700;
    margin-bottom: 4px;
}
.progress-bar-bg {
    background: #0b0f19;
    border: 1px solid #1f2937;
    border-radius: 6px;
    height: 7px;
    width: 100%;
    overflow: hidden;
    margin-bottom: 8px;
}
.progress-bar-fill {
    background: #10b981;
    height: 100%;
    border-radius: 6px;
}

/* شريط الأسعار داخل المربع نفسه */
.integrated-price {
    background: #0b0f19;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 6px 10px;
    display: flex;
    justify-content: space-around;
    align-items: center;
}
.price-box-item { text-align: center; }
.price-val-now { font-size: 1.25em; font-weight: 900; color: #10b981; }
.price-val-old { font-size: 0.8em; color: #64748b; text-decoration: line-through; }
.price-tag-lbl { font-size: 0.68em; color: #94a3b8; }

/* -------------------------------------------------------------------------- */
/* شبكة العطور الستة: جهتان متقابلتان (3 ضد 3)                                 */
/* -------------------------------------------------------------------------- */
div[data-testid="stRadio"]:has(input[name*="perfume_picker"]) > div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
    margin-bottom: 6px !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_picker"]) > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 8px !important;
    padding: 8px 6px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.15s ease-in-out !important;
    display: flex !important;
    align-items: center !important;
    min-height: 40px !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_picker"]) > div[role="radiogroup"] > label:hover {
    border-color: #334155 !important;
    background-color: #141e33 !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_picker"]) > div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.12) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* التحديد الزمردي الصافي ضد الأحمر */
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

/* -------------------------------------------------------------------------- */
/* كرت تفاصيل وصورة العطر مع خانة الخصم المباشر                               */
/* -------------------------------------------------------------------------- */
.selected-perfume-panel {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 8px 10px;
    margin-bottom: 6px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.perfume-flex-row {
    display: flex;
    gap: 10px;
    align-items: center;
}
.perfume-thumb {
    width: 62px;
    height: 62px;
    border-radius: 8px;
    background: #0f172a;
    border: 1px solid #1e293b;
    object-fit: cover;
    flex-shrink: 0;
}
.perfume-meta {
    flex: 1;
    font-size: 0.78em;
    line-height: 1.4;
    color: #cbd5e1;
}

/* كرت الخصم والتوفير تحت الصورة */
.discount-chip {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 6px;
    padding: 5px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.74em;
    font-weight: 700;
}

/* -------------------------------------------------------------------------- */
/* خيارات الاستلام ونموذج الطلب بمسافات مضغوطة للغاية                         */
/* -------------------------------------------------------------------------- */
div[data-testid="stRadio"]:has(input[name*="delivery_choice"]) > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 5px !important;
    margin-bottom: 6px !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_choice"]) > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 8px !important;
    padding: 7px 10px !important;
    margin: 0 !important;
    font-size: 0.82em !important;
}

div[data-testid="stTextInput"] {
    margin-bottom: 5px !important;
}
input, textarea { 
    caret-color: #10b981 !important; 
    border-radius: 8px !important;
    font-size: 0.88em !important;
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* زر الحجز الرئيسي */
div[data-testid="stFormSubmitButton"] > button {
    background: #10b981 !important;
    color: #022c22 !important;
    font-size: 1em !important;
    font-weight: 800 !important;
    height: 45px !important;
    border-radius: 8px !important;
    border: none !important;
    margin-top: 2px !important;
}

/* كرت التأكيد بعد الحجز */
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
    border-radius: 8px;
    padding: 10px;
    font-size: 0.8em;
    color: #94a3b8;
    line-height: 1.5;
    margin: 8px 0;
    text-align: center;
}
.wa-btn {
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

BASKET_ID = "BLOM-NEWTON-JEDDAH-V5"
BASKET_CAPACITY = 4      # سلة 4 عطور لاقتسام عرض (2+2 مجاناً)
UNIFIED_PRICE = 132      # السعر الموحد بعد تقاسم عرض بلوم
ORIGINAL_RETAIL = 265    # السعر الفردي بموقع بلوم
SAVINGS_AMOUNT = ORIGINAL_RETAIL - UNIFIED_PRICE  # 133 ر.س
ADMIN_PHONE = "966566261868"

raw_secret = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")
ADMIN_PASSWORD_HASH = str(raw_secret).strip()

# الستة عطور مرتبة بدقة: 3 في الجهة A مقابل 3 في الجهة B
PERFUMES = {
    # الجهة A
    "عطر روميو (Romeo)": {
        "tag": "رجالي فاخر",
        "rating": "4.8 ★",
        "desc": "جاذبية وأناقة رجولية فاخرة",
        "notes": "باتشولي، فانيلا، ومسك",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=260&q=80"
    },
    # الجهة B
    "عطر يوجا (Yoga)": {
        "tag": "هدوء وانسيابية",
        "rating": "4.8 ★",
        "desc": "رائحة هادئة تمنحك استرخاءً وأناقة",
        "notes": "برغموت، مسك نقي، ونرجس",
        "img": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=260&q=80"
    },
    # الجهة A
    "عطر لونار (Lunar)": {
        "tag": "أناقة للجنسين",
        "rating": "4.9 ★",
        "desc": "رائحة فاخرة بطابع غامض وجذاب",
        "notes": "باتشولي، عنب أسود، وعنبر",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=260&q=80"
    },
    # الجهة B
    "عطر لاروزيه (Larose)": {
        "tag": "الأعلى تقييماً",
        "rating": "5.0 ★",
        "desc": "أنوثة ساحرة تدوم طويلاً",
        "notes": "فانيلا، زنبق أبيض، وياسمين",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=260&q=80"
    },
    # الجهة A
    "عطر اليسيوم (Elysium)": {
        "tag": "فخامة أنثوية",
        "rating": "4.9 ★",
        "desc": "رائحة راقية تمنحك حضوراً ملكياً",
        "notes": "عنبر ملكي، فانيلا، ولافندر",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=260&q=80"
    },
    # الجهة B
    "عطر هارت بيت (Heart Beat)": {
        "tag": "حيوية ورومانسية",
        "rating": "4.8 ★",
        "desc": "رائحة رومانسية تنبض بالبهجة",
        "notes": "كشمش أسود، مسك، وورد",
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
            .neq("status", "cancelled") \
            .order("id") \
            .execute().data or []
    except Exception:
        return []

current_bookings = get_confirmed_bookings(BASKET_ID)
taken_count = len(current_bookings)
slots_left = max(0, BASKET_CAPACITY - taken_count)
progress_percent = int((taken_count / BASKET_CAPACITY) * 100)
status_badge = f"متبقي مقعد 1 وتكتمل الباقة 🔥" if slots_left == 1 else f"متبقي {slots_left} مقاعد لاكتمال الباقة"

# ==============================================================================
# 4. الصندوق العلوي الموحد (العنوان + العداد + السعر معاً)
# ==============================================================================
st.markdown(f"""
<div class="compact-header">
    <div class="header-badge">قسم مشترياتك • تقاسم العرض معنا</div>
    <div class="header-title">تقاسم عروض بلوم (2+2 مجاناً)</div>
    <div class="header-msg">تقاسم السعر أنت و 4 أشخاص</div>
    
    <div class="capacity-row">
        <span style="color: #cbd5e1;">اكتمال باقة نيوتن (4 أشخاص)</span>
        <span style="color: #10b981;">حجز {taken_count} من {BASKET_CAPACITY} ({status_badge})</span>
    </div>
    <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width: {progress_percent}%;"></div>
    </div>
    
    <div class="integrated-price">
        <div class="price-box-item">
            <div class="price-val-now">{UNIFIED_PRICE} ر.س</div>
            <div class="price-tag-lbl">سعر حصتك بالعرض</div>
        </div>
        <div style="color: #1f2937; font-size: 1.1em;">|</div>
        <div class="price-box-item">
            <div class="price-val-old">{ORIGINAL_RETAIL} ر.س</div>
            <div class="price-tag-lbl">السعر الفردي ببلوم</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. شاشة ما بعد الحجز
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    st.markdown(f"""
    <div class="success-card">
        <h3 style="color:#10b981; margin:0 0 4px 0; font-size:1.2em;">🎉 تم تثبيت حصتك بنجاح!</h3>
        <div style="font-size:0.9em; color:#e2e8f0;">العطر: <b>{deal['perfume']}</b></div>
        <div style="font-size:0.84em; color:#94a3b8;">الاستلام: <b>{deal['delivery']}</b></div>
        <div style="font-size:1.15em; color:#ffffff; margin-top:4px;">
            المطلوب عند الاستلام: <b style="color:#10b981;">{UNIFIED_PRICE} ر.س فقط</b>
        </div>
    </div>
    <div class="notice-box">
        🤝 <b>الدفع عند الاستلام يد بيد</b><br>
        سنتواصل معك عبر الواتساب فور اكتمال الباقة وتجهيز عِطرك مع الفاتورة.
    </div>
    """, unsafe_allow_html=True)
    
    wa_msg = (
        f"مرحباً يا غالي 🌿\n"
        f"سجلت اهتمامي في تقاسم عرض بلوم - مجموعة نيوتن ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal['name']}\n"
        f"• الجوال: {deal['phone']}\n"
        f"• العطر: {deal['perfume']}\n"
        f"• الاستلام: {deal['delivery']}\n\n"
        f"أرسل هذه الرسالة لتأكيد التواصل عبر الواتساب!"
    )
    wa_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 6. النموذج السريع وشبكة العطور المتقابلة
# ==============================================================================
else:
    # عنوان الاختيار على اليمين مباشرة
    st.markdown("<div style='font-size:0.86em; font-weight:800; color:#ffffff; text-align:right; margin-bottom:5px;'>1. المس العطر لاختياره مباشرة:</div>", unsafe_allow_html=True)
    
    # شبكة العطور الستة (3 في الجهة A مقابل 3 في الجهة B)
    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed",
        key="perfume_picker"
    )
    
    # بطاقة تفاصيل العطر المختار مع عرض الخصم تحت الصورة مباشرة
    p = PERFUMES[chosen_perfume]
    st.markdown(f"""
    <div class="selected-perfume-panel">
        <div class="perfume-flex-row">
            <img class="perfume-thumb" src="{p['img']}" alt="{chosen_perfume}">
            <div class="perfume-meta">
                <span style="color:#10b981; font-weight:800;">{p['rating']} • {p['tag']}</span><br>
                <b>الطابع:</b> {p['desc']}<br>
                <span style="color:#94a3b8;"><b>المكونات:</b> {p['notes']}</span>
            </div>
        </div>
        <div class="discount-chip">
            <span style="color:#cbd5e1;">قيمة العطر: <s style="color:#64748b;">{ORIGINAL_RETAIL} ر.س</s> ➔ <b style="color:#ffffff;">{UNIFIED_PRICE} ر.س</b></span>
            <span style="color:#10b981;">وفرت {SAVINGS_AMOUNT} ر.س (خصم 50%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # نموذج البيانات مدمج ومضغوط المسافات
    with st.form("quick_order_form"):
        st.markdown("<div style='font-size:0.86em; font-weight:800; color:#ffffff; text-align:right; margin-bottom:4px;'>2. طريقة الاستلام والبيانات:</div>", unsafe_allow_html=True)
        
        delivery_mode = st.radio(
            "طريقة الاستلام والدفع:",
            [
                f"استلام يد بيد (السلام مول) — {UNIFIED_PRICE} ر.س عند الاستلام",
                f"توصيل مجاني داخل جدة — {UNIFIED_PRICE} ر.س عند الاستلام"
            ],
            key="delivery_choice"
        )
        
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
        
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت حصتك في العرض ({UNIFIED_PRICE} ر.س عند الاستلام)", use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال يبدأ بـ 05.")
            elif slots_left == 0:
                st.warning("اكتملت الباقة الحالية تماماً، جاري فتح باقة جديدة.")
            else:
                try:
                    client_note = f"BLOM_NEWTON | {chosen_perfume} | {delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"
                    
                    if supabase:
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": BASKET_ID,
                            "court": 1,
                            "level": chosen_perfume,
                            "status": "confirmed",
                            "payment_status": "pending",
                            "hear_about": delivery_mode[:25],
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
                except Exception:
                    st.error("تعذر إتمام الحجز حالياً، يرجى المحاولة لاحقاً.")

# ==============================================================================
# 7. بوابة المشرف المعزولة كلياً (سرية: ?manage=faris فقط)
# ==============================================================================
query_params = st.query_params
if query_params.get("manage") == "faris":
    st.markdown("---")
    st.subheader("⚙️ بوابة المشرف المعزولة")
    admin_pin = st.text_input("رمز المرور:", type="password", key="admin_isolated_key")
    
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        st.success("تم تأكيد هوية المشرف.")
        
        with st.form("manual_add_admin_form"):
            st.markdown("##### ➕ إضافة حصة يدوياً:")
            m_name = st.text_input("الاسم:")
            m_phone = st.text_input("الجوال:")
            m_perf = st.selectbox("العطر:", list(PERFUMES.keys()))
            m_paid = st.checkbox("مدفوع ومؤكد ✅", value=True)
            
            if st.form_submit_button("تثبيت الحصة بالباقة"):
                if m_name and m_phone and supabase:
                    st_p = "paid" if m_paid else "pending"
                    supabase.table("bookings").insert({
                        "name": m_name.strip(),
                        "phone": m_phone.strip(),
                        "session_day": BASKET_ID,
                        "court": 1,
                        "level": m_perf,
                        "status": "confirmed",
                        "payment_status": st_p,
                        "hear_about": "إضافة يدوية",
                        "player_note": f"MANUAL | {m_perf} | PRICE:{UNIFIED_PRICE}"
                    }).execute()
                    st.cache_data.clear()
                    st.success("تم تثبيت الحصة!")
                    st.rerun()
        
        st.markdown("##### 👥 حصص الباقة المسجلة:")
        bookings_list = get_confirmed_bookings(BASKET_ID)
        for b in bookings_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{b.get('name')}** - `{b.get('level', '-')}`\n`{b.get('phone')}`")
            if b.get('payment_status') == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#38bdf8; font-weight:700;'>محجوز 🔒</span>", unsafe_allow_html=True)
                if col3.button("اعتماد دفع", key=f"pay_adm_{b.get('id')}"):
                    if supabase:
                        supabase.table("bookings").update({"payment_status": "paid"}).eq("id", b.get('id')).execute()
                    st.cache_data.clear()
                    st.rerun()
