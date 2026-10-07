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
    page_title="مَقسوم جدة | قطة عطور درعة",
    page_icon="🧴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# حقن مباشر في جذر الصفحة لتغيير هوية Streamlit وقتل اللون الأحمر تماماً + Clarity
components.html("""
<script type="text/javascript">
    // 1. تتبع Clarity
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window.parent, window.parent.document, "clarity", "script", "ytjnujh8td");

    // 2. فرض اللون الأخضر على جذر محرك Streamlit بالكامل
    try {
        var doc = window.parent.document;
        var styleEl = doc.getElementById('force-emerald-theme');
        if (!styleEl) {
            styleEl = doc.createElement('style');
            styleEl.id = 'force-emerald-theme';
            styleEl.innerHTML = `
                :root {
                    --primary-color: #10b981 !important;
                }
                /* استئصال الإطار الأحمر وظل التركيز من القوائم */
                div[data-baseweb="select"] * {
                    border-color: #334155 !important;
                    box-shadow: none !important;
                }
                div[data-baseweb="select"]:focus-within *,
                div[data-baseweb="select"]:hover *,
                div[data-baseweb="select"][aria-expanded="true"] * {
                    border-color: #10b981 !important;
                    box-shadow: 0 0 0 1px #10b981 !important;
                    outline: none !important;
                }
                /* أزرار الراديو */
                div[data-testid="stRadio"] div[role="radiogroup"] label div:first-child {
                    border-color: #475569 !important;
                }
                div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] {
                    border-color: #10b981 !important;
                }
                div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] div {
                    background-color: #10b981 !important;
                }
            `;
            doc.head.appendChild(styleEl);
        }
    } catch (e) {
        console.error("Theme injection error:", e);
    }
</script>
""", height=0, width=0)

# ==============================================================================
# 2. أنماط CSS التكميلية
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

html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f1f5f9;
}

/* القائمة المنسدلة (تنسيق مخصص ضد الأحمر) */
div[data-baseweb="select"] > div {
    background-color: #111827 !important;
    border-color: #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"]:focus-within > div,
div[data-baseweb="select"] > div:hover {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}
div[data-baseweb="select"] svg { fill: #10b981 !important; }

/* حقول الإدخال */
input, textarea { 
    caret-color: #10b981 !important; 
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
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
.store-title { font-size: 1.35em; font-weight: 900; color: #ffffff; margin: 4px 0; }
.store-desc { font-size: 0.84em; color: #94a3b8; line-height: 1.5; margin-bottom: 10px; }

/* شريط الأسعار الصريح */
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

.official-verify {
    background: rgba(56, 189, 248, 0.06);
    border: 1px dashed rgba(56, 189, 248, 0.3);
    border-radius: 10px;
    padding: 10px;
    margin: 10px 0;
    text-align: center;
    font-size: 0.82em;
    line-height: 1.5;
}
.official-verify a {
    color: #38bdf8 !important;
    font-weight: 800;
    text-decoration: underline;
}

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
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    padding: 2px 7px;
    border-radius: 6px;
    font-size: 0.78em;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 4px;
}

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
# 3. الربط بقاعدة البيانات والكتالوج
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
        "rating": "4.9 ★ (1,380 تقييم)",
        "desc": "طابع فخم ورسمي للمناسبات والدوام (يشبه خط كريد أفينتوس)",
        "notes": "أناناس مدخن، برغموت، وأخشاب فاخرة",
        "official_url": "https://deraahstore.com/ar-sa/leader-men-edp/p-101110101010-388",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=250&q=80"
    },
    "عطر لينك الأسود (Link Black) 100مل": {
        "tag": "رقم 1 الأكثر مبيعاً",
        "rating": "4.8 ★ (2,450 تقييم)",
        "desc": "رائحة انتعاش ونظافة يومية فواحة تدوم طويلاً",
        "notes": "حمضيات منعشة، ياسمين، ومسك نقي",
        "official_url": "https://deraahstore.com/ar-sa/link-black-men-edp/p-101110101010-385",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=250&q=80"
    },
    "عطر بورموا (Pour Moi) 100مل": {
        "tag": "خيار ناعم ومريح",
        "rating": "4.9 ★ (890 تقييم)",
        "desc": "طابع سويت هادئ وراقي جداً وملائم للإهداء",
        "notes": "فواكه ناعمة، ياسمين أبيض، فانيلا فرنسية",
        "official_url": "https://deraahstore.com/ar-sa/pour-moi-women-edp/p-101110101010-410",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=250&q=80"
    },
    "عطر خواطر (Khawater) 100مل": {
        "tag": "طابع شرقي كلاسيكي",
        "rating": "4.7 ★ (620 تقييم)",
        "desc": "ثبات وفوحان عالي بلمسة بخور أنيقة للمجالس",
        "notes": "بخور خفيف، باتشولي دافئ، وعنبر",
        "official_url": "https://deraahstore.com/ar-sa/khawater-unisex-edp/p-101110101010-415",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=250&q=80"
    },
    "عطر سول (Soul) 100مل": {
        "tag": "شبابي وعصري",
        "rating": "4.8 ★ (510 تقييم)",
        "desc": "عطر مناسب للطلعات واللقاءات المسائية",
        "notes": "هيل عطري، لافندر هادئ، وخشب الصندل",
        "official_url": "https://deraahstore.com/ar-sa/soul-men-edp/p-101110101010-420",
        "img": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=250&q=80"
    },
    "عطر ميس درعة (Miss Deraah) 100مل": {
        "tag": "بودري وزهري ناعم",
        "rating": "4.9 ★ (740 تقييم)",
        "desc": "ناعم وأنيق ومثالي للإهداء للأهل",
        "notes": "زهور الياسمين، باودر ومسك مخملي",
        "official_url": "https://deraahstore.com/ar-sa/miss-deraah-women-edp/p-101110101010-430",
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
# 4. الواجهة البصرية
# ==============================================================================
st.markdown(f"""
<div class="store-header">
    <div class="store-badge">تنسيق شراء تشاركي بجدة • 3 مقاعد فقط</div>
    <div class="store-title">قطّة عطور درعة (1+2 مجاناً)</div>
    <div class="store-desc">
        نقتسم عرض درعة بين 3 أشخاص؛ نشتري السلة سوا من فرع درعة بالأندلس مول، 
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

# بطاقة الشفافية
st.markdown("""
<div class="official-verify">
    🔎 <b>للشفافية الكاملة وتأكيد الأسعار الأصلية والعرض:</b><br>
    <a href="https://deraahstore.com" target="_blank">اضغط هنا لفتح موقع درعة الرسمي والتأكد من سعر العطر الفردي والعروض ↗</a>
</div>
""", unsafe_allow_html=True)

# مؤشر اكتمال السلة
progress_percent = int((taken_count / BASKET_CAPACITY) * 100)
status_badge = f"متبقي شخص واحد فقط وتكتمل القطة ونشتريها 🔥" if slots_left == 1 else f"متبقي {slots_left} أشخاص لاكتمال القطة"

st.markdown(f"""
<div style="background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 12px 14px; margin: 12px 0;">
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.82em; font-weight: 700;">
        <span style="color: #cbd5e1;">اكتمال السلة الحالية (3 أشخاص)</span>
        <span style="color: #10b981;">حجز {taken_count} من {BASKET_CAPACITY}</span>
    </div>
    <div style="background: #1f2937; border-radius: 6px; height: 8px; width: 100%; margin-top: 8px; overflow: hidden;">
        <div style="background: #10b981; height: 100%; width: {progress_percent}%; border-radius: 6px;"></div>
    </div>
    <div style="font-size: 0.78em; color: #94a3b8; margin-top: 6px;">
        ⚡ <b>{status_badge}</b> من فرع الأندلس مول.
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
# ==============================================================================
else:
    st.markdown("##### 1. اختر عِطرك المفضل:")
    
    chosen_perfume = st.selectbox(
        "اختر العطر:",
        list(PERFUMES.keys()),
        label_visibility="collapsed"
    )
    
    p = PERFUMES[chosen_perfume]
    
    st.markdown(f"""
    <div class="perfume-box">
        <img class="perfume-img" src="{p['img']}" alt="{chosen_perfume}">
        <div class="perfume-info">
            <span class="rating-pill">{p['rating']}</span>
            <span style="color:#38bdf8; font-weight:700; margin-right:4px;">★ {p['tag']}</span><br>
            <b>الطابع:</b> {p['desc']}<br>
            <span style="color:#94a3b8; font-size:0.9em;"><b>المكونات:</b> {p['notes']}</span><br>
            <a href="{p['official_url']}" target="_blank" style="color:#38bdf8; font-size:0.85em; text-decoration:underline;">عرض العطر في موقع درعة الرسمي ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("simple_checkout_form"):
        st.markdown("##### 2. طريقة الاستلام وبياناتك:")
        
        delivery_mode = st.radio(
            "طريقة الاستلام والدفع:",
            [
                "استلام يد بيد (الأندلس مول) — 63 ر.س عند الاستلام",
                "خزانة RedBox بجدة (+25 ر.س) — 88 ر.س"
            ]
        )
        
        is_redbox = "RedBox" in delivery_mode
        active_price = 88 if is_redbox else 63
        
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
        
        f_district = ""
        if is_redbox:
            f_district = st.text_input("الحي لأقرب خزانة RedBox بجدة:", placeholder="مثال: الروضة، الزهراء، السامر...")
            
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت المقعد (الدفع {active_price} ر.س عند الاستلام)", use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05.")
            elif is_redbox and not f_district.strip():
                st.error("فضلاً حدد اسم الحي لاستلام RedBox.")
            elif slots_left == 0:
                st.warning("السلة الحالية اكتملت تماماً، جاري فتح سلة جديدة قريباً.")
            else:
                try:
                    delivery_str = f"RedBox ({f_district.strip()})" if is_redbox else "الأندلس مول (يد بيد)"
                    note = f"PERFUME:{chosen_perfume} | METHOD:{delivery_str} | PRICE:{active_price} | PHONE:{clean_phone}"
                    
                    if supabase:
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": BASKET_ID,
                            "court": 1,
                            "level": chosen_perfume,
                            "status": "confirmed",
                            "payment_status": "pending",
                            "hear_about": delivery_str[:25],
                            "player_note": note
                        }).execute()
                    
                    st.cache_data.clear()
                    
                    st.session_state["confirmed_deal"] = {
                        "name": clean_name,
                        "phone": clean_phone,
                        "perfume": chosen_perfume,
                        "delivery": delivery_str,
                        "price": active_price
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
            st.markdown("##### ➕ إضافة مقعد يدوياً:")
            m_name = st.text_input("الاسم:")
            m_phone = st.text_input("الجوال:")
            m_perf = st.selectbox("العطر:", list(PERFUMES.keys()))
            m_paid = st.checkbox("مدفوع ومؤكد ✅", value=True)
            
            if st.form_submit_button("تثبيت المقعد بالسلة"):
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
                        "player_note": f"MANUAL | {m_perf}"
                    }).execute()
                    st.cache_data.clear()
                    st.success("تم تثبيت المقعد!")
                    st.rerun()
        
        st.markdown("##### 👥 مقاعد السلة المسجلة:")
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
