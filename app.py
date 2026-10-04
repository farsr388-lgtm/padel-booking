import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import hashlib
import urllib.parse
import requests
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة وهوية العرض المتجاوبة للجوال
# ==============================================================================
st.set_page_config(
    page_title="قطة عطور درعة | العرض الذهبي 2+2",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.6rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 440px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
}
.hero-box {
    background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
    border: 1px solid #4338ca;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-bottom: 10px;
}
.hero-title { font-size: 1.45em; font-weight: 900; color: #f8fafc; margin: 0; }
.hero-desc { color: #a5b4fc; font-size: 0.85em; margin-top: 4px; }
.offer-pill {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid #818cf8;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.82em;
    color: #c7d2fe;
    margin: 8px 0;
    display: inline-block;
    font-weight: 700;
}
.basket-container {
    background: #0f172a;
    border: 1.5px solid #312e81;
    border-radius: 14px;
    padding: 12px;
    margin: 8px 0;
}
.basket-header {
    text-align: center;
    font-weight: 800;
    font-size: 0.9em;
    color: #a5b4fc;
    margin-bottom: 10px;
}
.slots-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.slot-card {
    border-radius: 10px;
    padding: 10px 8px;
    text-align: center;
    font-size: 0.82em;
    font-weight: 800;
    line-height: 1.4;
}
.slot-empty {
    background: rgba(30, 41, 59, 0.5);
    border: 1.5px dashed #6366f1;
    color: #c7d2fe;
}
.slot-taken {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid #10b981;
    color: #a7f3d0;
}
.status-card-success {
    background: rgba(16, 185, 129, 0.1);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 8px;
}
.status-card-waitlist {
    background: rgba(245, 158, 11, 0.1);
    border: 2px solid #d97706;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 8px;
}
.wa-btn {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 14px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 0.95em;
    text-decoration: none;
    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.3);
    margin-top: 10px;
}
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 50px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
}
div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. الثوابت الاقتصادية ومعايير المنظومة
# ==============================================================================
BASKET_ID = "DERAAH-GOLD-01"
BASKET_CAPACITY = 4
HOLD_MINUTES = 30                    # مهلة سداد عادلة وعملية
BASE_PERFUME_PRICE = 105.0           # 210 ر.س ÷ 2 (نصف القيمة تماماً)
ADMIN_PHONE = "966566261868"
IBAN_NUMBER = "SA9380000222608016013114"
ACCOUNT_NAME = "مصرف الراجحي | فارس ربيع العصيمي"

# تشفير الرمز السري 9900 بـ SHA-256
ADMIN_PIN_HASH = hashlib.sha256("9900".encode()).hexdigest()

# العطور ذات السعر الرسمي الموحد (210 ر.س) لضمان دقة العرض وتفادي فرق الكاشير
GOLD_TIER_PERFUMES = [
    "عطر ليدر (Leader - 100ml)",
    "عطر بورموا (Pour Moi - 100ml)",
    "عطر لينك الأسود (Link Black - 100ml)",
    "عطر خواطر (Khawater - 100ml)",
    "عطر سول (Soul - 100ml)",
    "عطر ميس درعة (Miss Deraah - 100ml)"
]

DELIVERY_OPTIONS = {
    "🤝 استلام شخصي - رد سي مول (مواقف بوابة 1 بجدة)": 0.0,
    "📦 خزانة RedBox الذكية (أي فرع بجدة)": 15.0
}

# ==============================================================================
# 3. محرك الربط بقاعدة البيانات وتخزين الملفات المشفر
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
    st.error("تعذر الاتصال بالسحابة. يرجى مراجعة إعدادات Secrets.")
    st.stop()

# ==============================================================================
# 4. الدوال المساعدة: النسخ، التحقق، الروابط الموقعة، وتيليجرام
# ==============================================================================
def validate_saudi_phone(raw_phone: str):
    """تدقيق وتنقية رقم الجوال السعودي لحظياً مع توحيد الصيغة"""
    if not raw_phone:
        return False, "", "أدخل رقم الجوال (05xxxxxxxx)", ""
    
    cleaned = raw_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    cleaned = re.sub(r'[\s\-\+\(\)]', '', cleaned)
    
    if cleaned.startswith("00966"): cleaned = "0" + cleaned[5:]
    elif cleaned.startswith("966"): cleaned = "0" + cleaned[3:]
    elif cleaned.startswith("5"): cleaned = "0" + cleaned

    if not cleaned.isdigit():
        return False, cleaned, "⚠️ أرقام فقط بدون حروف أو رموز", ""
    if not cleaned.startswith("05"):
        return False, cleaned, "⚠️ يجب أن يبدأ الرقم بـ 05", ""
    
    count = len(cleaned)
    if count < 10:
        return False, cleaned, f"⏳ متبقي {10 - count} أرقام", ""
    elif count > 10:
        return False, cleaned, f"⚠️ الرقم أطول من اللازم ({count} خانات)", ""
    
    formatted = f"{cleaned[:3]} {cleaned[3:6]} {cleaned[6:]}"
    return True, cleaned, "✅ رقم الجوال صحيح ومعتمد", formatted

def render_copy_card(title: str, text_value: str, button_label: str = "نسخ", card_id: str = "copy_box"):
    """بطاقة نسخ بنقرة واحدة متوافقة مع متصفحات الجوال وتطبيقات التواصل"""
    safe_text = html.escape(text_value)
    html_code = f"""
    <!DOCTYPE html>
    <div style="direction: rtl; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a; border: 1.5px solid #312e81; border-radius: 12px;
                padding: 10px 14px; margin: 6px 0; display: flex; align-items: center; justify-content: space-between;">
        <div style="overflow: hidden; text-overflow: ellipsis; padding-left: 8px;">
            <div style="font-size: 11px; color: #94a3b8; font-weight: 600; margin-bottom: 2px;">{title}</div>
            <div id="target_{card_id}" style="font-family: monospace; font-size: 14.5px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;">{safe_text}</div>
        </div>
        <button id="btn_{card_id}" onclick="execCopy_{card_id}()" 
                style="background: #4f46e5; color: #ffffff; border: none; border-radius: 8px;
                       padding: 8px 12px; font-size: 12px; font-weight: 700; cursor: pointer;
                       transition: all 0.2s ease; white-space: nowrap; outline: none; min-width: 80px;">
            📋 {button_label}
        </button>
    </div>
    <script>
    function execCopy_{card_id}() {{
        var t = "{safe_text}";
        navigator.clipboard.writeText(t).then(function() {{
            var b = document.getElementById("btn_{card_id}");
            b.innerHTML = "تم النسخ ✅";
            b.style.background = "#10b981";
            setTimeout(function() {{ b.innerHTML = "📋 {button_label}"; b.style.background = "#4f46e5"; }}, 2200);
        }}).catch(function(err) {{
            var el = document.createElement("input");
            el.value = t;
            document.body.appendChild(el);
            el.select();
            document.execCommand("copy");
            document.body.removeChild(el);
            var b = document.getElementById("btn_{card_id}");
            b.innerHTML = "تم النسخ ✅";
            b.style.background = "#10b981";
            setTimeout(function() {{ b.innerHTML = "📋 {button_label}"; b.style.background = "#4f46e5"; }}, 2200);
        }});
    }}
    </script>
    """
    components.html(html_code, height=72)

def upload_receipt_to_supabase(uploaded_file, phone: str) -> str:
    """رفع الإيصال إلى Bucket خاص وحفظ مسار الكائن فقط لحماية الخصوصية"""
    try:
        ext = uploaded_file.name.split(".")[-1].lower()
        ts = int(datetime.now(timezone.utc).timestamp())
        file_path = f"receipt_{phone}_{ts}.{ext}"
        
        supabase.storage.from_("receipts").upload(
            path=file_path,
            file=uploaded_file.getvalue(),
            file_options={"content-type": uploaded_file.type or "image/jpeg", "upsert": "true"}
        )
        return file_path
    except Exception as e:
        st.error(f"تعذر حفظ الملف سحابياً: {e}")
        return ""

def generate_admin_signed_url(file_path: str, expires_in_seconds: int = 1800) -> str:
    """توليد رابط مؤقت مشفر (Signed URL) صالح للمعاينة من قبل الإدارة فقط"""
    try:
        res = supabase.storage.from_("receipts").create_signed_url(file_path, expires_in_seconds)
        if isinstance(res, dict):
            return res.get("signedURL") or res.get("signed_url") or ""
        return getattr(res, "signed_url", "")
    except Exception:
        return ""

def send_telegram_alert(customer_name: str, phone: str, perfume: str, total_price: float, signed_url: str):
    """إشعار فوري بحساب الأدمن في تيليجرام فور إرفاق الإيصال"""
    token = st.secrets.get("TELEGRAM_BOT_TOKEN")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    
    msg = (
        f"🚨 <b>إشعار سداد جديد في سلة العطور!</b>\n\n"
        f"👤 <b>العميل:</b> {customer_name}\n"
        f"📱 <b>الجوال:</b> <code>{phone}</code>\n"
        f"🧴 <b>العطر:</b> {perfume}\n"
        f"💵 <b>المبلغ:</b> {int(total_price)} ر.س\n\n"
        f"🔗 <a href='{signed_url}'>اضغط هنا لمعاينة الإيصال مباشرة</a>\n"
        f"⏳ <i>الرابط مؤمن وصالح لمدة 30 دقيقة.</i>"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
            timeout=5
        )
        return True
    except Exception:
        return False

# ==============================================================================
# 5. محرك الشلال التلقائي وحفظ الحصص (Waterfall Engine)
# ==============================================================================
def process_basket_orders(session_key: str):
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()
    
    try:
        all_records = supabase.table("bookings") \
            .select("*") \
            .eq("session_day", session_key) \
            .order("id") \
            .execute().data or []
            
        confirmed_active = []
        waitlist_records = []
        
        for r in all_records:
            if r.get("status") == "waitlist":
                waitlist_records.append(r)
            elif r.get("status") == "confirmed":
                is_settled = r.get("payment_status") in ["paid", "under_review"]
                is_expired = r.get("expires_at") and r["expires_at"] <= now_iso
                
                # إلغاء المقاعد المعلقة التي تجاوزت المهلة الزمنية
                if not is_settled and is_expired:
                    supabase.table("bookings").update({
                        "status": "cancelled",
                        "player_note": f"انتهاء مهلة السداد ({HOLD_MINUTES} دقيقة)"
                    }).eq("id", r["id"]).execute()
                else:
                    confirmed_active.append(r)
                    
        # ترقية الانتظار تلقائياً للشواغر المتاحة
        vacancies = BASKET_CAPACITY - len(confirmed_active)
        if vacancies > 0 and waitlist_records:
            to_promote = waitlist_records[:vacancies]
            for wr in to_promote:
                new_exp = (now_utc + timedelta(minutes=HOLD_MINUTES)).isoformat()
                supabase.table("bookings").update({
                    "status": "confirmed",
                    "payment_status": "pending",
                    "expires_at": new_exp,
                    "player_note": "ترقية تلقائية من قائمة الانتظار"
                }).eq("id", wr["id"]).execute()
                
                wr["status"] = "confirmed"
                wr["payment_status"] = "pending"
                wr["expires_at"] = new_exp
                confirmed_active.append(wr)
                waitlist_records.remove(wr)
                
        return confirmed_active[:BASKET_CAPACITY], waitlist_records
    except Exception:
        return [], []

confirmed_orders, waitlist_orders = process_basket_orders(BASKET_ID)
taken_count = len(confirmed_orders)
slots_left = max(0, BASKET_CAPACITY - taken_count)

# ==============================================================================
# 6. استعادة الجلسة عند تحديث الصفحة عبر الرابط (State Persistence)
# ==============================================================================
if "deal_booked" not in st.session_state:
    qp_phone = st.query_params.get("phone", None)
    if qp_phone:
        matched = [x for x in confirmed_orders if x["phone"] == qp_phone]
        if matched:
            rec = matched[0]
            exp_ts = 0
            if rec.get("expires_at"):
                exp_ts = int(datetime.fromisoformat(rec["expires_at"]).timestamp() * 1000)
            
            p_note = rec.get("player_note") or ""
            r_match = re.search(r"RECEIPT_PATH:([^\s|]+)", p_note)
            
            st.session_state["deal_booked"] = {
                "name": rec["name"],
                "phone": rec["phone"],
                "perfume": rec.get("level", ""),
                "memo_code": f"PRF-{rec['phone'][-4:]}",
                "is_waitlist": False,
                "expire_timestamp": exp_ts,
                "total_price": BASE_PERFUME_PRICE,
                "has_receipt": bool(r_match),
                "is_paid": rec.get("payment_status") == "paid"
            }

# ==============================================================================
# 7. واجهة العرض واستعراض مقاعد السلة
# ==============================================================================
st.markdown(f"""
<div class="hero-box">
    <div class="hero-title">🛍️ قطة عطور درعة (عرض 2+2)</div>
    <div class="hero-desc">الفئة الذهبية الموحدة • احصل على عطرك بـ 50% من سعره الرسمي</div>
    <div class="offer-pill">💎 قيمة العطر: 105 ر.س فقط (السعر بالفرع: 210 ر.س)</div>
    <div style="font-size:0.83em; color:#cbd5e1; margin-top:4px;">
        📍 الاستلام: <b>رد سي مول (بوابة 1)</b> أو <b>خزائن RedBox بجدة</b> • 
        <b>{'متبقي ' + str(slots_left) + ' عطور لاكتمال السلة 🔥' if slots_left > 0 else 'اكتملت السلة الحالية (متاح بالانتظار ⏳)'}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# استعراض بطاقات العطور الأربعة
slots_html = []
for i in range(BASKET_CAPACITY):
    if i < taken_count:
        item = confirmed_orders[i]
        c_name = html.escape(item['name'].split()[0])
        p_name = html.escape(item.get('level', 'عطر مختار'))
        p_stat = item.get('payment_status')
        if p_stat == 'paid':
            status_txt, s_color = "تم السداد ✅", "#34d399"
        elif p_stat == 'under_review':
            status_txt, s_color = "مراجعة الإيصال 🔍", "#38bdf8"
        else:
            status_txt, s_color = "مهلة سداد ⏳", "#fbbf24"

        slots_html.append(f"""
        <div class="slot-card slot-taken">
            🧴 <b>{c_name}</b><br>
            <span style="font-size:0.8em; color:#f1f5f9;">{p_name}</span><br>
            <span style="font-size:0.75em; color:{s_color};">{status_txt}</span>
        </div>
        """)
    else:
        slots_html.append("""
        <div class="slot-card slot-empty">
            ✨ <b>حصة شاغرة</b><br>
            <span style="font-size:0.8em; color:#94a3b8;">خصم 50% قطعي</span><br>
            <span style="font-size:0.75em; color:#818cf8;">احجز الآن</span>
        </div>
        """)

st.markdown(f"""
<div class="basket-container">
    <div class="basket-header">🛒 سلة الشراء الجماعي الحالية ({taken_count}/{BASKET_CAPACITY})</div>
    <div class="slots-grid">{''.join(slots_html)}</div>
</div>
""", unsafe_allow_html=True)

with st.expander("⚖️ الضمانات وشفافية الشراء"):
    st.markdown("""
    * **الفاتورة الرسمية:** يتم تصوير فاتورة شركة درعة وتزويد المشتركين بها فور إتمام الشراء من المعرض.
    * **الأصالة الكاملة:** الشراء يتم مباشرة من الفرع الرسمي لدرعة في رد سي مول بجدة.
    * **ضمان الاسترداد:** في حال عدم اكتمال السلة خلال 24 ساعة، يُعاد المبلغ فوراً لنفس الحساب البنكي المحول منه.
    """)

# ==============================================================================
# 8. شاشات ما بعد التسجيل، الرفع، والتحويل
# ==============================================================================
if "deal_booked" in st.session_state:
    b = st.session_state["deal_booked"]
    
    if b.get("is_waitlist", False):
        st.markdown(f"""
        <div class="status-card-waitlist">
            <h3 style="color:#fbbf24; margin:0 0 6px 0;">⏳ مسجل في قائمة الانتظار للسلة القادمة</h3>
            <div style="font-size:1em; color:#fef3c7;">ترتيبك: <b style="font-size:1.3em;">#{b.get('pos', 1)}</b></div>
            <div style="font-size:0.84em; color:#fde68a; margin-top:4px;">
                سيتم تصعيد مقعدك تلقائياً فور فتح سلة جديدة أو تعثر سداد أي مشترك.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_wait_msg = f"مرحباً 🛍️\nأنا مسجل في قائمة انتظار سلة عطور درعة الذهبية:\n👤 الاسم: {b['name']}\n🧴 العطر: {b.get('perfume', '')}\n🔢 الترتيب: #{b.get('pos', 1)}"
        wa_wait_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_wait_msg)}"
        st.markdown(f'<a href="{wa_wait_url}" target="_blank" class="wa-btn" style="background:#d97706;">📲 تأكيد وجودي بالانتظار عبر واتساب</a>', unsafe_allow_html=True)

    else:
        target_epoch_ms = b.get("expire_timestamp", 0)
        memo_full_text = f"{b['memo_code']} | {b['phone']}"
        total_price = b.get("total_price", BASE_PERFUME_PRICE)
        
        st.markdown(f"""
        <div class="status-card-success">
            <h3 style="color:#10b981; margin:0 0 4px 0;">🎉 تم حجز مقعدك في السلة!</h3>
            <div style="font-size:1.05em; color:#f8fafc; margin:6px 0;">
                المبلغ المطلوب تحويله: <b style="color:#10b981; font-size:1.4em;">{int(total_price)} ر.س</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # عداد مهلة السداد
        components.html(f"""
        <!DOCTYPE html>
        <div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(239, 68, 68, 0.15); border: 1.5px solid #ef4444; border-radius: 12px; padding: 10px; color: #fca5a5; margin: 4px auto;">
            <div style="font-size: 13px; font-weight: 700;">⏱ الوقت المتبقي لتثبيت الحصة بالسداد:</div>
            <div id="pay_timer" style="font-family: monospace; font-size: 32px; color: #ef4444; font-weight: 900;">--:--</div>
        </div>
        <script>
            var target = {target_epoch_ms};
            function update() {{
                var diff = target - new Date().getTime();
                var el = document.getElementById('pay_timer');
                if (!el) return;
                if (diff <= 0) {{ el.innerHTML = "00:00"; return; }}
                var m = Math.floor(diff / 60000);
                var s = Math.floor((diff % 60000) / 1000);
                el.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            }}
            update();
            setInterval(update, 1000);
        </script>
        """, height=92)
        
        st.caption(f"الحساب المعتمد: {ACCOUNT_NAME}")
        render_copy_card("رقم الحساب الدولي (IBAN)", IBAN_NUMBER, "نسخ الآيبان", "iban_box")
        render_copy_card("الملاحظة البنكية المطلوبة بالحوالة", memo_full_text, "نسخ الكود", "memo_box")
        
        st.markdown("---")
        st.markdown("##### 📤 إرفاق إيصال التحويل البنكي")
        
        receipt_file = st.file_uploader(
            "ارفع صورة الحوالة أو لقطة الشاشة",
            type=["png", "jpg", "jpeg"],
            help="الحد الأقصى 5 ميجابايت",
            key="receipt_uploader"
        )
        
        if receipt_file:
            st.image(receipt_file, caption="معاينة الإيصال المرفق", use_container_width=True)
            if st.button("اعتماد وإرسال الإيصال سحابياً 🚀", use_container_width=True):
                with st.spinner("جاري تأمين الإيصال وتنبيه الإدارة..."):
                    f_path = upload_receipt_to_supabase(receipt_file, b["phone"])
                    if f_path:
                        supabase.table("bookings").update({
                            "payment_status": "under_review",
                            "player_note": f"PERFUME:{b.get('perfume')} | TOTAL:{int(total_price)} | RECEIPT_PATH:{f_path}"
                        }).eq("phone", b["phone"]).eq("session_day", BASKET_ID).execute()
                        
                        signed_view_url = generate_admin_signed_url(f_path, expires_in_seconds=1800)
                        send_telegram_alert(
                            customer_name=b["name"],
                            phone=b["phone"],
                            perfume=b.get("perfume", "غير محدد"),
                            total_price=total_price,
                            signed_url=signed_view_url
                        )
                        st.success("✅ تم استلام الإيصال وإشعار الإدارة بنجاح لمراجعته!")
                        st.balloons()
        
        wa_msg = f"مرحباً 🛍️\nحجزت مقعدي في سلة درعة:\n👤 الاسم: {b['name']}\n🧴 العطر: {b.get('perfume', '')}\n🔖 الكود: {memo_full_text}\n💵 المبلغ: {int(total_price)} ر.س"
        wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 بديل: إرسال الإيصال عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 9. نموذج الحجز والانضمام للسلة
# ==============================================================================
else:
    is_waitlist = (slots_left == 0)
    btn_text = "الانضمام لقائمة الانتظار ⏳" if is_waitlist else "تثبيت العطر والانتقال للسداد 🛍️"
    
    if is_waitlist:
        st.warning(f"⚠️ السلة الحالية مكتملة ({BASKET_CAPACITY}/{BASKET_CAPACITY}). يمكنك الحجز في قائمة الانتظار.")
        
    with st.form("perfume_form"):
        f_name = st.text_input("الاسم الكريم", placeholder="الاسم الثنائي أو الثلاثي")
        f_phone_raw = st.text_input("رقم الجوال", placeholder="05xxxxxxxx", help="يقبل أرقام الجوال السعودية")
        
        is_phone_valid, clean_phone, phone_msg, phone_formatted = validate_saudi_phone(f_phone_raw)
        if f_phone_raw.strip():
            if is_phone_valid:
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; 
                            border-radius: 8px; padding: 6px 12px; font-size: 0.82em; color: #a7f3d0; margin-top: -8px; margin-bottom: 10px;">
                    {phone_msg} • <b>{phone_formatted}</b>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid #ef4444; 
                            border-radius: 8px; padding: 6px 12px; font-size: 0.82em; color: #fca5a5; margin-top: -8px; margin-bottom: 10px;">
                    {phone_msg}
                </div>
                """, unsafe_allow_html=True)

        f_perfume = st.selectbox("اختر عطرك الذهبي (السعر الرسمي 210 ر.س)", GOLD_TIER_PERFUMES)
        f_delivery = st.selectbox("طريقة ومكان الاستلام", list(DELIVERY_OPTIONS.keys()))
        
        redbox_loc = ""
        if "RedBox" in f_delivery:
            redbox_loc = st.text_input("الحي المفضل لخزانة RedBox بجدة", placeholder="مثال: حي الروضة / المرجان")
            
        fee = DELIVERY_OPTIONS[f_delivery]
        total = BASE_PERFUME_PRICE + fee
        
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border-radius: 8px; padding: 12px; margin: 10px 0; font-size: 0.84em; color: #cbd5e1;">
            • قيمة العطر بعد التخفيض: <b>{int(BASE_PERFUME_PRICE)} ر.س</b><br>
            • رسوم الخدمة / التوصيل: <b>{int(fee)} ر.س</b><br>
            • <b>الإجمالي المطلوب: <span style="color:#10b981; font-size:1.15em;">{int(total)} ر.س</span></b>
        </div>
        """, unsafe_allow_html=True)
        
        hp = st.text_input("hp", label_visibility="collapsed")
        
        can_submit = len(f_name.strip()) >= 2 and is_phone_valid
        submit_btn = st.form_submit_button(btn_text, use_container_width=True, disabled=not can_submit)
        
        if submit_btn and not hp:
            if "RedBox" in f_delivery and len(redbox_loc.strip()) < 3:
                st.error("يرجى كتابة الحي المفضل لاستلام شحنة RedBox.")
            else:
                try:
                    c_now, w_now = process_basket_orders(BASKET_ID)
                    
                    if any(x["phone"] == clean_phone for x in c_now):
                        st.warning("أنت مشترك ومقعدك محجوز بالفعل في هذه السلة!")
                        st.query_params["phone"] = clean_phone
                        st.rerun()
                    elif any(x["phone"] == clean_phone for x in w_now):
                        st.warning("أنت مسجل مسبقاً في قائمة الانتظار!")
                    else:
                        memo_id = f"PRF-{clean_phone[-4:]}"
                        delivery_info = f"{f_delivery} ({redbox_loc.strip()})" if redbox_loc else f_delivery
                        meta_note = f"PERFUME:{f_perfume} | DELIV:{delivery_info} | TOTAL:{int(total)}"
                        now_utc = datetime.now(timezone.utc)
                        
                        if len(c_now) < BASKET_CAPACITY:
                            exp_dt = now_utc + timedelta(minutes=HOLD_MINUTES)
                            supabase.table("bookings").insert({
                                "name": f_name.strip(),
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": f_perfume,
                                "status": "confirmed",
                                "payment_status": "pending",
                                "expires_at": exp_dt.isoformat(),
                                "hear_about": delivery_info[:40],
                                "player_note": meta_note
                            }).execute()
                            
                            st.query_params["phone"] = clean_phone
                            st.session_state["deal_booked"] = {
                                "name": f_name.strip(),
                                "phone": clean_phone,
                                "perfume": f_perfume,
                                "total_price": total,
                                "memo_code": memo_id,
                                "is_waitlist": False,
                                "expire_timestamp": int(exp_dt.timestamp() * 1000)
                            }
                            st.rerun()
                        else:
                            supabase.table("bookings").insert({
                                "name": f_name.strip(),
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": f_perfume,
                                "status": "waitlist",
                                "payment_status": "unpaid",
                                "hear_about": delivery_info[:40],
                                "player_note": meta_note
                            }).execute()
                            
                            st.session_state["deal_booked"] = {
                                "name": f_name.strip(),
                                "phone": clean_phone,
                                "perfume": f_perfume,
                                "total_price": total,
                                "memo_code": memo_id,
                                "is_waitlist": True,
                                "pos": len(w_now) + 1
                            }
                            st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {ex}")

# ==============================================================================
# 10. لوحة الإدارة لمتابعة الإيصالات واعتماد المشتريات
# ==============================================================================
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة إدارة السلة والمطابقة"):
    admin_pin = st.text_input("رمز الدخول (PIN):", type="password", key="admin_pin")
    if admin_pin:
        entered_hash = hashlib.sha256(admin_pin.strip().encode()).hexdigest()
        if hmac.compare_digest(entered_hash, ADMIN_PIN_HASH):
            st.success("تم تأكيد الصلاحية الإدارية.")
            c_adm, w_adm = process_basket_orders(BASKET_ID)
            paid_count = sum(1 for x in c_adm if x.get("payment_status") == "paid")
            
            st.write(f"المسددين المؤكدين: **{paid_count} / {BASKET_CAPACITY}**")
            
            for row in c_adm:
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{row['name']}** - `{row.get('level', '-')}`\n`{row['phone']}`")
                
                stat = row.get("payment_status")
                if stat == "paid":
                    c2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ومؤكد ✅</span>", unsafe_allow_html=True)
                elif stat == "under_review":
                    c2.markdown("<span style='color:#38bdf8; font-weight:700;'>إيصال مرفوع 🔍</span>", unsafe_allow_html=True)
                else:
                    c2.markdown("<span style='color:#fbbf24; font-weight:700;'>مهلة سداد ⏳</span>", unsafe_allow_html=True)

                with c3:
                    p_note = row.get("player_note") or ""
                    r_path_match = re.search(r"RECEIPT_PATH:([^\s|]+)", p_note)
                    if r_path_match:
                        signed_url = generate_admin_signed_url(r_path_match.group(1), expires_in_seconds=1800)
                        if signed_url:
                            st.markdown(f'<a href="{signed_url}" target="_blank" style="font-size:0.8em; color:#818cf8; text-decoration:none; display:block; margin-bottom:4px;">👁️ الإيصال</a>', unsafe_allow_html=True)
                    
                    if stat != "paid":
                        if st.button("اعتماد", key=f"adm_pay_{row['id']}"):
                            supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                            st.rerun()
