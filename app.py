import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import uuid
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة وهوية المتجر
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | عطور درعة (شراء جماعي)",
    page_icon="🧴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع الجلسات (Microsoft Clarity)
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
# 2. أنماط واجهة متجر حديث وبسيط (Minimalist E-Commerce UI)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 1rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 430px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f17;
    color: #e2e8f0;
}

/* بطاقة المنتج الرئيسية */
.product-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 12px;
}
.brand-label {
    font-size: 0.75em;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
}
.product-title {
    font-size: 1.35em;
    font-weight: 800;
    color: #f8fafc;
    margin: 4px 0 8px 0;
}
.pricing-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin: 10px 0;
}
.current-price {
    font-size: 1.6em;
    font-weight: 900;
    color: #10b981;
}
.original-price {
    font-size: 0.95em;
    color: #64748b;
    text-decoration: line-through;
}
.discount-tag {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid #059669;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75em;
    font-weight: 800;
}

/* شريط اكتمال الدفعة */
.pool-status-box {
    background: #161e2e;
    border: 1px solid #283548;
    border-radius: 10px;
    padding: 12px;
    margin: 12px 0;
}
.progress-bar-bg {
    background: #2d3748;
    border-radius: 6px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin-top: 8px;
}
.progress-bar-fill {
    background: linear-gradient(90deg, #6366f1, #10b981);
    height: 100%;
    border-radius: 6px;
}

/* بطاقة المواصفات المختصرة */
.specs-box {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid #283548;
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.82em;
    line-height: 1.6;
    color: #cbd5e1;
    margin: 8px 0 14px 0;
}

/* شاشة تأكيد الطلب */
.invoice-card {
    background: #111827;
    border: 1px solid #10b981;
    border-radius: 14px;
    padding: 18px 14px;
    text-align: center;
    margin-top: 10px;
}
.bank-details-box {
    background: #161e2e;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px;
    margin: 12px 0;
    text-align: right;
    font-size: 0.85em;
    line-height: 1.7;
}

/* الأزرار ونماذج الإدخال */
div[data-testid="stFormSubmitButton"] > button {
    background: #10b981 !important;
    color: #042f2e !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 50px !important;
    border-radius: 10px !important;
    border: none !important;
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

/* إخفاء حقل Honeypot */
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
    st.error("الخدمة قيد التحديث المؤقت.")
    st.stop()

# ==============================================================================
# 4. إعدادات السلة والمنتجات
# ==============================================================================
BASKET_ID = "MAQSOOM-JEDDAH-01"
BASKET_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_LOCAL_PHONE = "0566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")

PERFUMES = {
    "عطر ليدر (Leader) - 100 مل": {
        "notes": "جلود فاخرة، أخشاب الأرز، توابل دافئة",
        "char": "رسمي وفخم للمناسبات والدوام"
    },
    "عطر بورموا (Pour Moi) - 100 مل": {
        "notes": "فانيلا فرنسية، عنبر ناعم، زهور بيضاء",
        "char": "سويت جذاب وهادئ للاستخدام اليومي"
    },
    "عطر لينك الأسود (Link Black) - 100 مل": {
        "notes": "برغموت إيطالي، حمضيات فواحة، مسك نقي",
        "char": "منعش وفواح لليوم والصباح"
    },
    "عطر خواطر (Khawater) - 100 مل": {
        "notes": "باتشولي، نفحات عود هادئة، قاعدة عنبرية",
        "char": "طابع شرقي كلاسيكي بثبات عالي"
    },
    "عطر سول (Soul) - 100 مل": {
        "notes": "هيل عطري، لافندر، خشب الصندل",
        "char": "شبابي وعصري للطلعات واللقاءات"
    },
    "عطر ميس درعة (Miss Deraah) - 100 مل": {
        "notes": "زهور الياسمين، فواكه، باودر ومسك ناعم",
        "char": "ناعم وأنيق خيار ملائم للإهداء"
    }
}

IBAN_NUMBER = "SA9380000222608016013114"
ACCOUNT_NAME = "فارس ربيع بن عواض العصيمي"

# ==============================================================================
# 5. معالجة المقاعد والدفع
# ==============================================================================
def get_basket_status():
    now_utc = datetime.now(timezone.utc).isoformat()
    try:
        records = supabase.table("bookings") \
            .select("*") \
            .eq("session_day", BASKET_ID) \
            .order("id") \
            .execute().data or []
            
        confirmed = []
        for r in records:
            if r.get("status") == "confirmed":
                # إلغاء الحجز تلقائياً بعد 45 دقيقة بدون سداد
                if r.get("payment_status") != "paid" and r.get("expires_at") and r["expires_at"] <= now_utc:
                    supabase.table("bookings").update({"status": "cancelled"}).eq("id", r["id"]).execute()
                else:
                    confirmed.append(r)
        return confirmed[:BASKET_CAPACITY]
    except Exception:
        return []

confirmed_orders = get_basket_status()
taken = len(confirmed_orders)
available = max(0, BASKET_CAPACITY - taken)
progress_pct = int((taken / BASKET_CAPACITY) * 100)

# ==============================================================================
# 6. واجهة المتجر (Clean Product Page)
# ==============================================================================
if "order_placed" in st.session_state:
    # ------------------ شاشة تأكيد الطلب والدفع ------------------
    order = st.session_state["order_placed"]
    
    st.markdown(f"""
    <div class="invoice-card">
        <div style="font-size:0.85em; color:#10b981; font-weight:800;">تم حجز حصتك في الدفعة بنجاح</div>
        <div style="font-size:1.3em; font-weight:900; color:#ffffff; margin:6px 0;">{order['perfume']}</div>
        <div style="font-size:0.85em; color:#94a3b8;">طريقة الاستلام: {order['delivery']}</div>
        <div style="font-size:2em; font-weight:900; color:#10b981; margin:10px 0;">{order['price']} ر.س</div>
    </div>
    
    <div class="bank-details-box">
        <b>بيانات التحويل لإتمام وتأكيد الحصة:</b><br>
        • التحويل السريع (سريع): <b>{ADMIN_LOCAL_PHONE}</b><br>
        • الآيبان (مصرف الراجحي): <b>{ACCOUNT_NAME}</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.code(IBAN_NUMBER, language=None)
    st.caption("🔒 ضمان الدفعة: في حال لم تكتمل حصص السلة خلال 24 ساعة، يُعاد المبلغ تلقائياً لحسابك البنكي.")
    
    wa_msg = (
        f"مرحباً، تم حجز عطر في مقسوم:\n"
        f"• الاسم: {order['name']}\n"
        f"• العطر: {order['perfume']}\n"
        f"• الاستلام: {order['delivery']}\n"
        f"• المبلغ: {order['price']} ر.س\n\n"
        f"مرفق إشعار التحويل البنكي."
    )
    wa_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-btn">إرسال إشعار التحويل عبر واتساب</a>', unsafe_allow_html=True)

else:
    # ------------------ صفحة الشراء المباشرة ------------------
    st.markdown(f"""
    <div class="product-card">
        <div class="brand-label">درعة للعطور • جدة</div>
        <div class="product-title">شراء جماعي: عطور درعة الأصلية (100 مل)</div>
        <div class="pricing-row">
            <span class="current-price">63 ر.س</span>
            <span class="original-price">210 ر.س</span>
            <span class="discount-tag">خصم 70% بالجملة</span>
        </div>
        <div style="font-size:0.82em; color:#94a3b8; line-height:1.5;">
            تجميع 6 مشترين لاقتناص عرض درعة الكبرى وتقسيم الفاتورة بالتساوي؛ عِطرك المفضل بسعر التكلفة الصافي.
        </div>
    </div>

    <div class="pool-status-box">
        <div style="display:flex; justify-content:space-between; font-size:0.82em; font-weight:700;">
            <span>سلة الشراء الحالية</span>
            <span style="color:#10b981;">حُجز {taken} من {BASKET_CAPACITY} عطور</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {progress_pct}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # اختيار العطر
    selected_perfume = st.selectbox(
        "اختر عِطرك من المجموعة الذهبية:",
        list(PERFUMES.keys())
    )
    p_data = PERFUMES[selected_perfume]
    
    st.markdown(f"""
    <div class="specs-box">
        <b>النوتات:</b> {p_data['notes']}<br>
        <b>الاستخدام:</b> {p_data['char']}
    </div>
    """, unsafe_allow_html=True)

    # نموذج الطلب السريع
    with st.form("checkout_form"):
        st.markdown("##### تفاصيل المستلم والاستلام:")
        
        c_name = st.text_input("الاسم الكريم:", placeholder="الاسم الثنائي")
        c_phone = st.text_input("رقم الجوال:", placeholder="05xxxxxxxx")
        
        c_delivery = st.radio(
            "طريقة الاستلام (جدة):",
            [
                "استلام يدوي مجاناً (الأندلس مول) — 63 ر.س",
                "خزانة RedBox الذكية (+25 ر.س) — 88 ر.س"
            ]
        )
        
        is_redbox = "RedBox" in c_delivery
        final_price = 88 if is_redbox else 63
        
        c_district = ""
        if is_redbox:
            c_district = st.text_input("الحي لأقرب خزانة RedBox:", placeholder="مثال: الروضة، الزهراء، السامر")

        hp = st.text_input("hp", label_visibility="collapsed")
        submit = st.form_submit_button(f"تأكيد حجز العطر ({final_price} ر.س)", use_container_width=True)

        if submit and not hp:
            clean_name = c_name.strip()
            clean_phone = re.sub(r'[\s\-\+]', '', c_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05.")
            elif is_redbox and not c_district.strip():
                st.error("فضلاً حدد اسم الحي لاستلام RedBox.")
            elif available == 0:
                st.warning("السلة الحالية مكتملة، جاري فتح سلة جديدة قريباً.")
            else:
                try:
                    exp_dt = (datetime.now(timezone.utc) + timedelta(minutes=45)).isoformat()
                    delivery_method = f"RedBox ({c_district.strip()})" if is_redbox else "استلام الأندلس مول"
                    
                    supabase.table("bookings").insert({
                        "name": clean_name,
                        "phone": clean_phone,
                        "session_day": BASKET_ID,
                        "court": 1,
                        "level": selected_perfume,
                        "status": "confirmed",
                        "payment_status": "pending",
                        "expires_at": exp_dt,
                        "hear_about": delivery_method[:25],
                        "player_note": f"PRICE:{final_price} | METHOD:{delivery_method}"
                    }).execute()
                    
                    st.session_state["order_placed"] = {
                        "name": clean_name,
                        "phone": clean_phone,
                        "perfume": selected_perfume,
                        "delivery": delivery_method,
                        "price": final_price
                    }
                    st.rerun()
                except Exception as e:
                    st.error("حدث خطأ تقني، يرجى المحاولة لاحقاً.")

# ==============================================================================
# 7. لوحة التحكم (مخفية ومقتضبة للمشرف)
# ==============================================================================
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
with st.expander("لوحة الإدارة"):
    pwd = st.text_input("رمز المشرف:", type="password")
    if pwd and hmac.compare_digest(pwd.strip(), ADMIN_PASSWORD_HASH):
        orders = get_basket_status()
        st.write(f"المحجوز حالياً: {len(orders)} / {BASKET_CAPACITY}")
        for o in orders:
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"**{o['name']}** ({o['level']})\n`{o['phone']}`")
            if o['payment_status'] == 'paid':
                col2.success("مدفوع")
            else:
                col2.warning("معلق")
                if col3.button("اعتماد", key=f"btn_{o['id']}"):
                    supabase.table("bookings").update({"payment_status": "paid"}).eq("id", o["id"]).execute()
                    st.rerun()
