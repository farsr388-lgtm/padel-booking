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
# 2. أنماط الواجهة الثنائية (Two-Tone System)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.6rem !important; 
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

/* تحويل خيارات الراديو إلى كروت نشطة باللمس المباشر */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1.5px solid #1f2937 !important;
    border-radius: 12px !important;
    padding: 11px 13px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.15s ease-in-out !important;
    display: flex !important;
    align-items: center !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    border-color: #334155 !important;
    background-color: #141e33 !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.08) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* منع اللون الأحمر في دوائر التحديد */
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

/* حقول الإدخال */
input, textarea { 
    caret-color: #10b981 !important; 
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* الهيدر العلوي */
.store-header {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
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
    margin-bottom: 6px;
}
.store-title { 
    font-size: 1.3em; 
    font-weight: 900; 
    color: #ffffff; 
    margin: 2px 0 6px 0; 
}
.store-desc { 
    font-size: 0.82em; 
    color: #94a3b8; 
    line-height: 1.5; 
    margin-bottom: 10px; 
}

/* شريط السعر البارز */
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
.price-now { font-size: 1.55em; font-weight: 900; color: #10b981; }
.price-old { font-size: 0.85em; color: #64748b; text-decoration: line-through; }
.price-lbl { font-size: 0.72em; color: #94a3b8; margin-top: 1px; }

/* كرت تفاصيل العطر المختار */
.active-perfume-details {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0 14px 0;
    display: flex;
    gap: 12px;
    align-items: center;
}
.perfume-img-container {
    width: 80px;
    height: 80px;
    border-radius: 10px;
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
    font-size: 0.82em;
    line-height: 1.5;
    color: #cbd5e1;
}

/* بطاقة ما بعد الحجز */
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

/* أزرار الإرسال */
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

BASKET_ID = "BLOM-NEWTON-JEDDAH-FINAL"
BASKET_CAPACITY = 4      # سلة 4 عطور لاقتسام عرض (2+2 مجاناً)
UNIFIED_PRICE = 132      # السعر الموحد بعد تقاسم عرض بلوم
ADMIN_PHONE = "966566261868"

raw_secret = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")
ADMIN_PASSWORD_HASH = str(raw_secret).strip()

# كتالوج عطور مجموعة نيوتن الرسمية
PERFUMES = {
    "عطر روميو (Romeo) 100مل": {
        "tag": "رجالي فاخر ومميز",
        "rating": "4.8 ★ (3 تقييمات)",
        "desc": "رائحة رجولية فاخرة تمنحك جاذبية أنيقة تبقى في الذاكرة",
        "notes": "باتشولي، فانيلا، ومسك نقي",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=260&q=80"
    },
    "عطر لونار (Lunar) 100مل": {
        "tag": "أناقة غامضة وجاذبية",
        "rating": "4.9 ★ (تقييمان)",
        "desc": "رائحة فاخرة تخطف الأنظار بطابع غامض وجذاب للجنسين",
        "notes": "باتشولي، عنب أسود، وعنبر دافئ",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=260&q=80"
    },
    "عطر اليسيوم (Elysium) 100مل": {
        "tag": "فخامة ورقي أنثوي",
        "rating": "4.9 ★ (6 تقييمات)",
        "desc": "رائحة راقية تمنحك جاذبية فاخرة وحضوراً ملكياً",
        "notes": "عنبر ملكي، فانيلا ناعمة، ولافندر",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=260&q=80"
    },
    "عطر يوجا (Yoga) 100مل": {
        "tag": "هدوء وانسيابية ناعمة",
        "rating": "4.8 ★ (7 تقييمات)",
        "desc": "رائحة هادئة وناعمة تمنحك استرخاءً وأناقة طوال اليوم",
        "notes": "برغموت منعش، مسك نقي، ونرجس",
        "img": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=260&q=80"
    },
    "عطر لاروزيه (Larose) 100مل": {
        "tag": "الأعلى تقييماً بمجموعة نيوتن",
        "rating": "5.0 ★ (20 تقييم)",
        "desc": "أنوثة ساحرة وراقية تدوم طويلاً وتأسر الحواس",
        "notes": "فانيلا، زنبق أبيض، وياسمين مخملي",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=260&q=80"
    },
    "عطر هارت بيت (Heart Beat) 100مل": {
        "tag": "أنوثة حيوية ورومانسية",
        "rating": "4.8 ★ (5 تقييمات)",
        "desc": "رائحة رومانسية تنبض بالحياة والبهجة اليومية",
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
    <div class="store-title">تقاسم عروض بلوم Blom (2+2 مجاناً)</div>
    <div class="store-desc">
        نجمع اهتماماتكم في نفس العرض مع أشخاص مختلفين؛ نتقاسم باقة نيوتن (4 عطور) بسعر التكلفة، 
        وعِطرك الأصلي 100مل يطلع عليك بنصف قيمته بسعر موحد وثابت:
    </div>
    <div class="price-strip">
        <div class="price-col">
            <div class="price-now">{UNIFIED_PRICE} ر.س</div>
            <div class="price-lbl">سعر حصتك بالعرض</div>
        </div>
        <div style="color:#1f2937; font-size:1.2em;">|</div>
        <div class="price-col">
            <div class="price-old">265 ر.س</div>
            <div class="price-lbl">سعره الفردي بمتجر بلوم</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# مؤشر سعة السلة
progress_percent = int((taken_count / BASKET_CAPACITY) * 100)
status_badge = f"متبقي عطر واحد وتكتمل الباقة ونطلبها فوراً 🔥" if slots_left == 1 else f"متبقي {slots_left} عطور لاكتمال الباقة"

st.markdown(f"""
<div style="background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 12px 14px; margin: 12px 0;">
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.82em; font-weight: 700;">
        <span style="color: #cbd5e1;">اكتمال باقة نيوتن الحالية (4 أشخاص)</span>
        <span style="color: #10b981;">حجز {taken_count} من {BASKET_CAPACITY}</span>
    </div>
    <div style="background: #0b0f19; border-radius: 6px; height: 8px; width: 100%; margin-top: 8px; overflow: hidden; border: 1px solid #1f2937;">
        <div style="background: #10b981; height: 100%; width: {progress_percent}%; border-radius: 6px;"></div>
    </div>
    <div style="font-size: 0.78em; color: #94a3b8; margin-top: 6px;">
        🌿 <b>{status_badge}</b>.
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
        <h3 style="color:#10b981; margin:0 0 6px 0; font-size:1.3em;">🎉 تم تثبيت حصتك في العرض بنجاح!</h3>
        <div style="font-size:0.95em; color:#e2e8f0; margin:4px 0;">
            العطر المختار: <b>{deal['perfume']}</b>
        </div>
        <div style="font-size:0.88em; color:#94a3b8; margin:2px 0;">
            طريقة الاستلام: <b>{deal['delivery']}</b>
        </div>
        <div style="font-size:1.25em; color:#ffffff; margin-top:8px;">
            المبلغ المطلوب عند الاستلام: <b style="color:#10b981;">{UNIFIED_PRICE} ر.س فقط</b>
        </div>
    </div>
    
    <div class="notice-box">
        🤝 <b>الدفع عند الاستلام يد بيد</b><br>
        لا يلزمك تحويل أي مبلغ مسبقاً. سنتواصل معك عبر الواتساب فور اكتمال الباقة لتنسيق الاستلام مع الفاتورة الرسمية.
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
# 6. مسار الاختيار النشط والطلب السريع
# ==============================================================================
else:
    st.markdown("<div style='font-size: 0.9em; font-weight: 800; color: #f1f5f9; margin-bottom: 6px;'>1. المس العطر لاختياره مباشرة:</div>", unsafe_allow_html=True)
    
    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed"
    )
    
    p = PERFUMES[chosen_perfume]
    st.markdown(f"""
    <div class="active-perfume-details">
        <div class="perfume-img-container">
            <img class="perfume-img" src="{p['img']}" alt="{chosen_perfume}">
        </div>
        <div class="perfume-info">
            <span style="color:#10b981; font-weight:800;">{p['rating']} • {p['tag']}</span><br>
            <b>الطابع:</b> {p['desc']}<br>
            <span style="color:#94a3b8; font-size:0.9em;"><b>المكونات:</b> {p['notes']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("simple_checkout_form"):
        st.markdown("<div style='font-size: 0.9em; font-weight: 800; color: #f1f5f9; margin-bottom: 6px;'>2. طريقة الاستلام والبيانات:</div>", unsafe_allow_html=True)
        
        delivery_mode = st.radio(
            "طريقة الاستلام والدفع:",
            [
                f"استلام يد بيد (السلام مول) — {UNIFIED_PRICE} ر.س عند الاستلام",
                f"توصيل مجاني داخل جدة — {UNIFIED_PRICE} ر.س عند الاستلام"
            ]
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
                st.error("يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05.")
            elif slots_left == 0:
                st.warning("الباقة الحالية اكتملت تماماً، جاري فتح باقة جديدة قريباً.")
            else:
                try:
                    note = f"PERFUME:{chosen_perfume} | METHOD:{delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"
                    
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
                            "player_note": note
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
# 7. بوابة الإدارة المعزولة كلياً (سرية: ?manage=faris فقط)
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
