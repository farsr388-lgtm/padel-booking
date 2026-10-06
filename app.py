import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone

# ==============================================================================
# 1. إعداد الصفحة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم جدة | قطة عطور درعة (3 مقاعد)",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع Clarity
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
# 2. التنسيق البصري (CSS)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 440px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f1f5f9;
}

.hero-box {
    background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
    border: 1px solid #3b82f6;
    border-radius: 16px;
    padding: 16px 14px;
    text-align: center;
    margin-bottom: 10px;
}
.urgent-pill {
    background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
    color: #ffffff;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.8em;
    font-weight: 900;
    display: inline-block;
    margin-bottom: 6px;
}
.hero-title { font-size: 1.45em; font-weight: 900; color: #ffffff; margin: 4px 0; }
.hero-desc { font-size: 0.84em; color: #cbd5e1; line-height: 1.6; margin-bottom: 8px; }

.price-breakdown {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-top: 6px;
}
.price-item { text-align: center; }
.price-item .val { font-size: 1.35em; font-weight: 900; color: #10b981; }
.price-item .lbl { font-size: 0.72em; color: #94a3b8; }
.price-divider { color: #475569; font-weight: 300; font-size: 1.2em; }

/* بطاقات المقاعد الـ 3 */
.slots-container {
    display: flex;
    gap: 8px;
    margin: 10px 0;
}
.slot-card-3 {
    flex: 1;
    border-radius: 12px;
    padding: 12px 6px;
    text-align: center;
    font-size: 0.8em;
    line-height: 1.4;
}
.slot-empty {
    background: rgba(30, 41, 59, 0.4);
    border: 1.5px dashed #475569;
    color: #94a3b8;
}
.slot-taken {
    background: rgba(16, 185, 129, 0.12);
    border: 1.5px solid #10b981;
    color: #f1f5f9;
}

/* بطاقة العطر البصرية مع الصورة والوصف الدقيق */
.perfume-visual-card {
    background: #111827;
    border: 1.5px solid #4f46e5;
    border-radius: 14px;
    padding: 12px;
    margin: 8px 0 14px 0;
    display: flex;
    gap: 12px;
    align-items: center;
}
.perfume-img {
    width: 85px;
    height: 85px;
    border-radius: 10px;
    object-fit: contain;
    background: #1e293b;
    padding: 4px;
}
.perfume-text {
    flex: 1;
    font-size: 0.82em;
    line-height: 1.5;
    color: #e2e8f0;
}
.perfume-badge {
    display: inline-block;
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 1px 6px;
    font-size: 0.72em;
    font-weight: 800;
    margin-bottom: 4px;
}

.status-card-success {
    background: rgba(16, 185, 129, 0.12);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 18px 14px;
    text-align: center;
    margin-top: 8px;
}
.safe-badge {
    background: #0f172a;
    border: 1px solid #10b981;
    border-radius: 10px;
    padding: 12px;
    margin: 10px 0;
    text-align: center;
    font-size: 0.88em;
    color: #a7f3d0;
    line-height: 1.6;
}
.wa-btn {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 15px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 1.05em;
    text-decoration: none;
    box-shadow: 0 4px 16px rgba(37, 211, 102, 0.35);
    margin-top: 12px;
}
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: #042f2e !important;
    font-size: 1.05em !important;
    font-weight: 900 !important;
    height: 52px !important;
    border-radius: 10px !important;
    border: none !important;
    margin-top: 6px !important;
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
# 3. الاتصال بقاعدة البيانات
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    if url.endswith("/rest/v1"):
        url = url[:-8]
    return create_client(url, st.secrets["SUPABASE_KEY"].strip())

try:
    supabase = get_supabase_client()
except Exception:
    st.error("تعذر الاتصال بقاعدة البيانات.")
    st.stop()

# ==============================================================================
# 4. إعدادات السلة وكتالوج العطور بالصور والتوصيف العملي
# ==============================================================================
BASKET_ID = "MAQSOOM-JEDDAH-BASKET-01"
BASKET_CAPACITY = 3
ADMIN_PHONE = "966566261868"
ADMIN_LOCAL_PHONE = "0566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")

PERFUMES_CATALOG = {
    "عطر ليدر (Leader) - 100 مل": {
        "badge": "⭐ الأكثر طلباً ومحاكاة لـ كريد أفينتوس",
        "vibe": "فخم، رسمي، وهيبة للدوام والمناسبات",
        "notes": "أناناس مدخن، برغموت، وأخشاب فاخرة",
        "img": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=300&q=80"
    },
    "عطر لينك الأسود (Link Black) - 100 مل": {
        "badge": "👑 رقم 1 الأكثر مبيعاً في تاريخ درعة",
        "vibe": "انتعاش، نظافة، وطاقة صباحية تدوم طويلاً",
        "notes": "حمضيات منعشة، ياسمين، ومسك نقي",
        "img": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=300&q=80"
    },
    "عطر بورموا (Pour Moi) - 100 مل": {
        "badge": "💖 الأكثر مبيعاً للإهداء والذوق الناعم",
        "vibe": "سويت جذاب ومريح جداً للجنسين",
        "notes": "فواكه ناعمة، ياسمين أبيض، فانيلا فرنسية",
        "img": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?auto=format&fit=crop&w=300&q=80"
    },
    "عطر خواطر (Khawater) - 100 مل": {
        "badge": "🪵 طابع شرقي كلاسيكي ومجالس",
        "vibe": "ثبات قوي وفخامة للمناسبات الشتوية والمجالس",
        "notes": "بخور خفيف، باتشولي دافئ، وقاعدة عنبرية",
        "img": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=300&q=80"
    },
    "عطر سول (Soul) - 100 مل": {
        "badge": "⚡ شبابي عصري وملفت",
        "vibe": "عطر طلعات وكافيهات وسهرات شبابية",
        "notes": "هيل عطري، خزامى هادئة، وخشب الصندل",
        "img": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=300&q=80"
    },
    "عطر ميس درعة (Miss Deraah) - 100 مل": {
        "badge": "🌸 أنيق وناعم وفاتن",
        "vibe": "بودري هادئ وزهور راقية مناسب للإهداء",
        "notes": "زهور الياسمين، باودر ومسك مخملي",
        "img": "https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=300&q=80"
    }
}

IBAN_NUMBER = "SA9380000222608016013114"
ACCOUNT_NAME = "فارس ربيع بن عواض العصيمي"

def get_basket_records(basket_key: str):
    try:
        return supabase.table("bookings") \
            .select("*") \
            .eq("session_day", basket_key) \
            .neq("status", "cancelled") \
            .order("id") \
            .execute().data or []
    except Exception:
        return []

confirmed_orders = get_basket_records(BASKET_ID)
taken_count = len(confirmed_orders)
slots_left = max(0, BASKET_CAPACITY - taken_count)

# ==============================================================================
# 5. الواجهة البصرية المباشرة
# ==============================================================================
st.markdown(f"""
<div class="hero-box">
    <div class="urgent-pill">🔥 متبقي مقعد واحد فقط وتكتمل السلة الأولى!</div>
    <div class="hero-title">قطّة عطور درعة (1+2 مجاناً) بجدة</div>
    <div class="hero-desc">
        نقتسم عرض درعة الكبرى بين <b>3 أشخاص فقط</b>؛ نشتري السلة سوا بفاتورة رسمية من فرع درعة بالأندلس مول، 
        وعِطرك الأصلي 100مل يطلع عليك بـ <b>63 ر.س فقط</b> (بدل 210 ر.س).
    </div>
    <div class="price-breakdown">
        <div class="price-item">
            <div style="font-size:0.85em; color:#94a3b8; text-decoration:line-through;">210 ر.س</div>
            <div class="val">63 ر.س</div>
            <div class="lbl">استلام الأندلس مول (مجاناً)</div>
        </div>
        <div class="price-divider">أو</div>
        <div class="price-item">
            <div style="font-size:0.85em; color:#94a3b8; text-decoration:line-through;">235 ر.س</div>
            <div class="val" style="color:#38bdf8;">88 ر.س</div>
            <div class="lbl">عبر خزانة RedBox (+25)</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# عرض المقاعد الثلاثة
st.markdown(f"<div style='font-weight:800; font-size:0.9em; margin: 4px 0 8px 0;'>🛒 مقاعد السلة الأولى ({taken_count}/{BASKET_CAPACITY}):</div>", unsafe_allow_html=True)

slots_html = []
for i in range(BASKET_CAPACITY):
    if i < taken_count:
        item = confirmed_orders[i]
        c_name = html.escape(item['name'].split()[0])
        p_name = html.escape(item.get('level', 'عطر محجوز'))
        is_paid = item.get('payment_status') == 'paid'
        status_txt = "مدفوع ومؤكد ✅" if is_paid else "مقعد محجوز 🔒"
        slots_html.append(
            f'<div class="slot-card-3 slot-taken">'
            f'🧴 <b>{c_name}</b><br>'
            f'<span style="font-size:0.82em; color:#cbd5e1;">{p_name}</span><br>'
            f'<span style="font-size:0.75em; color:{"#34d399" if is_paid else "#38bdf8"};">{status_txt}</span>'
            f'</div>'
        )
    else:
        slots_html.append(
            f'<div class="slot-card-3 slot-empty">'
            f'✨ <b>المقعد الأخير #{i+1}</b><br>'
            f'<span style="font-size:0.8em; color:#94a3b8;">متاح الآن</span><br>'
            f'<span style="font-size:0.75em; color:#10b981; font-weight:800;">63 ر.س فقط</span>'
            f'</div>'
        )

cards_markup = "".join(slots_html)
st.markdown(f'<div class="slots-container">{cards_markup}</div>', unsafe_allow_html=True)

# ==============================================================================
# 6. شاشة ما بعد الحجز
# ==============================================================================
if "deal_booked" in st.session_state:
    b = st.session_state["deal_booked"]
    
    st.markdown(f"""
    <div class="status-card-success">
        <h3 style="color:#10b981; margin:0 0 4px 0; font-size:1.3em;">🎉 تم تثبيت مقعدك بالسلة!</h3>
        <div style="font-size:0.95em; color:#cbd5e1; margin:4px 0;">
            العطر المحجوز: <b style="color:#ffffff;">{b['perfume']}</b>
        </div>
        <div style="font-size:0.88em; color:#94a3b8;">
            طريقة الاستلام: <b style="color:#38bdf8;">{b['delivery']}</b>
        </div>
        <div style="font-size:1.1em; color:#ffffff; margin-top:8px;">
            المبلغ المستحق: <b style="color:#10b981; font-size:1.3em;">{int(b['price'])} ر.س</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if b.get("is_cod", False):
        st.markdown("""
        <div class="safe-badge">
            🤝 <b>تم اختيار: الدفع عند الاستلام يد بيد بالأندلس مول</b><br>
            ما يحتاج تحول أي ريال الآن! سنتواصل معك عبر الواتساب فور استلام العطور من المعرض مع الفاتورة الرسمية.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="safe-badge">
            💳 <b>بيانات التحويل البنكي (لتثبيت المقعد):</b><br>
            • رقم الجوال عبر خدمة "سريع": <b>{ADMIN_LOCAL_PHONE}</b><br>
            • الآيبان (الراجحي): <b>{ACCOUNT_NAME}</b>
        </div>
        """, unsafe_allow_html=True)
        st.code(IBAN_NUMBER, language=None)

    wa_msg = (
        f"مرحباً يا غالي 🛍️\n"
        f"حجزت المقعد الأخير في سلة درعة (3 عطور):\n\n"
        f"👤 الاسم: {b['name']}\n"
        f"📱 الجوال: {b['phone']}\n"
        f"🧴 العطر: {b['perfume']}\n"
        f"📍 الاستلام: {b['delivery']}\n"
        f"💵 المبلغ: {int(b['price'])} ر.س\n\n"
        f"أرسل هذه الرسالة لتأكيد التواصل عبر الواتساب!"
    )
    wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 تأكيد الحجز والتواصل عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 7. نموذج الانضمام للسلة واختيار العطر المرئي
# ==============================================================================
else:
    st.markdown("##### 1. اختر عِطرك المفضل (أو انظر الصورة والمواصفات):")
    
    chosen_perfume = st.selectbox(
        "العطور المتاحة:",
        list(PERFUMES_CATALOG.keys()),
        label_visibility="collapsed"
    )
    
    p_info = PERFUMES_CATALOG[chosen_perfume]
    
    # بطاقة مرئية مباشرة بالصورة والتوصيف لحسم قرار المشتري
    st.markdown(f"""
    <div class="perfume-visual-card">
        <img class="perfume-img" src="{p_info['img']}" alt="{chosen_perfume}">
        <div class="perfume-text">
            <span class="perfume-badge">{p_info['badge']}</span><br>
            <b>الرائحة والطابع:</b> {p_info['vibe']}<br>
            <span style="color:#94a3b8; font-size:0.9em;"><b>المكونات:</b> {p_info['notes']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("perfume_deal_form"):
        st.markdown("##### 2. بيانات الحجز والاستلام:")
        
        f_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        f_phone = st.text_input("رقم الجوال للتواصل:", placeholder="05xxxxxxxx")
        
        f_delivery = st.radio(
            "طريقة الاستلام والدفع المفضلة:",
            [
                "استلام الأندلس مول — والدفع يد بيد عند الاستلام (63 ر.س)",
                "استلام الأندلس مول — تحويل بنكي مسبق (63 ر.س)",
                "توصيل لخزانة RedBox بجدة — تحويل مسبق (88 ر.س)"
            ]
        )
        
        is_redbox = "RedBox" in f_delivery
        is_cod = "يد بيد" in f_delivery
        active_price = 88.0 if is_redbox else 63.0
        
        f_loc = ""
        if is_redbox:
            f_loc = st.text_input("الحي لأقرب خزانة RedBox بجدة:", placeholder="مثال: الروضة، الزهراء، الصفا...")
            
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(f"تثبيت المقعد الأخير في السلة ({int(active_price)} ر.س)", use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال يبدأ بـ 05.")
            elif is_redbox and not f_loc.strip():
                st.error("فضلاً حدد اسم الحي لاستلام RedBox.")
            elif slots_left == 0:
                st.warning("السلة الأولى اكتملت! جاري فتح السلة الثانية فوراً.")
            else:
                try:
                    delivery_str = f"RedBox ({f_loc.strip()})" if is_redbox else ("يد بيد بالأندلس مول" if is_cod else "الأندلس مول")
                    note = f"PERFUME:{chosen_perfume} | METHOD:{delivery_str} | PRICE:{int(active_price)} | PHONE:{clean_phone}"
                    
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
                    
                    st.session_state["deal_booked"] = {
                        "name": clean_name,
                        "phone": clean_phone,
                        "perfume": chosen_perfume,
                        "delivery": delivery_str,
                        "price": active_price,
                        "is_cod": is_cod
                    }
                    st.rerun()
                except Exception as ex:
                    st.error(f"تعذر إتمام الحجز: {ex}")

# ==============================================================================
# 8. لوحة الإدارة
# ==============================================================================
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة"):
    admin_pin = st.text_input("رمز الدخول:", type="password", key="admin_pwd_input")
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        st.success("🔓 تم فتح لوحة التحكم.")
        
        with st.form("manual_booking_form"):
            st.markdown("##### ➕ إضافة مقعد يدوياً بالسلة:")
            m_name = st.text_input("الاسم:", placeholder="مثال: فارس أو اسم المحول")
            m_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
            m_perf = st.selectbox("العطر:", list(PERFUMES_CATALOG.keys()))
            m_del = st.selectbox("طريقة الاستلام:", ["الأندلس مول (يد بيد)", "خزانة RedBox"])
            m_paid = st.checkbox("مدفوع ومؤكد ✅", value=True)
            
            if st.form_submit_button("تثبيت المقعد بالسلة فوراً"):
                if m_name and m_phone:
                    st_p = "paid" if m_paid else "pending"
                    supabase.table("bookings").insert({
                        "name": m_name.strip(),
                        "phone": m_phone.strip(),
                        "session_day": BASKET_ID,
                        "court": 1,
                        "level": m_perf,
                        "status": "confirmed",
                        "payment_status": st_p,
                        "hear_about": m_del[:25],
                        "player_note": f"MANUAL | {m_del}"
                    }).execute()
                    st.success("تم تثبيت المقعد!")
                    st.rerun()
                else:
                    st.error("يرجى إدخال الاسم ورقم الجوال.")

        st.markdown("---")
        st.markdown("##### 👥 متابعة وإدارة مقاعد السلة:")
        c_list = get_basket_records(BASKET_ID)
        for row in c_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{row['name']}** - `{row.get('level', '-')}`\n`{row.get('hear_about', '-')}`\n`{row['phone']}`")
            if row['payment_status'] == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#38bdf8; font-weight:700;'>محجوز 🔒</span>", unsafe_allow_html=True)
                if col3.button("اعتماد دفع", key=f"pay_perf_{row['id']}"):
                    supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                    st.rerun()
