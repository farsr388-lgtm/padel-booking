import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة وهوية المنصة السريعة
# ==============================================================================
st.set_page_config(
    page_title="التفكير التشاركي | عطور درعة الذهبية",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2rem !important; 
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
    padding: 14px;
    text-align: center;
    margin-bottom: 8px;
}
.hero-title { font-size: 1.45em; font-weight: 900; color: #f8fafc; margin: 0; }
.hero-desc { color: #a5b4fc; font-size: 0.82em; margin-top: 4px; }
.offer-pill {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid #818cf8;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 0.8em;
    color: #c7d2fe;
    margin: 6px 0;
    display: inline-block;
    font-weight: 800;
}
.perfume-info-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0;
    font-size: 0.83em;
    color: #cbd5e1;
    line-height: 1.6;
}
.perfume-tag {
    background: #4338ca;
    color: #ffffff;
    font-size: 0.72em;
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 4px;
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
    font-size: 0.88em;
    color: #a5b4fc;
    margin-bottom: 8px;
}
.slots-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.slot-card {
    border-radius: 10px;
    padding: 10px 6px;
    text-align: center;
    font-size: 0.8em;
    font-weight: 800;
    line-height: 1.35;
}
.slot-empty {
    background: rgba(30, 41, 59, 0.6);
    border: 1.5px dashed #6366f1;
    color: #c7d2fe;
}
.slot-taken {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #a7f3d0;
}
.memo-tag {
    background: #0b0f19;
    border: 1.5px dashed #818cf8;
    border-radius: 8px;
    padding: 8px 12px;
    display: inline-block;
    font-family: monospace;
    font-size: 1.05em;
    color: #818cf8;
    font-weight: 800;
    margin: 6px 0;
}
.status-card-success {
    background: rgba(16, 185, 129, 0.12);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 8px;
}
.status-card-waitlist {
    background: rgba(245, 158, 11, 0.12);
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
    font-size: 1em;
    text-decoration: none;
    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
    margin-top: 10px;
}
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 52px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35) !important;
}
div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ربط قاعدة البيانات السحابية (Supabase)
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
    st.error("تعذر الاتصال بقاعدة البيانات. يرجى مراجعة إعدادات Secrets في السحابة.")
    st.stop()

# ==============================================================================
# 3. كتالوج العطور الأكثر طلباً وقواعد التسعير التشاركي
# ==============================================================================
BASKET_ID = "DERAAH-NATIONAL-01"
BASKET_CAPACITY = 6  # سلة مزدوجة (3x2) لاختراق عتبة الشحن المجاني
ADMIN_PHONE = "966566261868"
ADMIN_PIN_HASH = "9900"

# كتالوج العطور المتكافئة سعرياً (210 ر.س بالمتجر) مع خصائصها لتسهيل اختيار العميل
PERFUMES_CATALOG = {
    "عطر ليدر (Leader)": {
        "tag": "الأكثر مبيعاً ورسمية 👑",
        "notes": "جلود فاخرة، أخشاب الأرز، توابل دافئة",
        "rating": "4.8/5 (تقييم ممتاز)",
        "vibe": "فخم للمناسبات والدوام الرسمي"
    },
    "عطر بورموا (Pour Moi)": {
        "tag": "أيقونة كلاسيكية دافئة ✨",
        "notes": "فانيلا فرنسية، عنبر، زهور بيضاء هادئة",
        "rating": "4.9/5 (الأعلى تقييماً)",
        "vibe": "سويت جذاب ومريح لجميع الأوقات"
    },
    "عطر لينك الأسود (Link Black)": {
        "tag": "العطر اليومي المنعش ⚡",
        "notes": "برغموت، حمضيات منعشة، مسك نقي",
        "rating": "4.7/5 (طلب متكرر)",
        "vibe": "صباحي، طاقة وانتعاش صيفي دائم"
    },
    "عطر خواطر (Khawater)": {
        "tag": "طابع شرقي مهيب 🪵",
        "notes": "باتشولي هادئ، نفحات عود خفيف، عنبر",
        "rating": "4.8/5 (طابع كلاسيكي)",
        "vibe": "ثبات وفوحان عالي للمجالس"
    },
    "عطر ميس درعة (Miss Deraah)": {
        "tag": "ناعم للجنسين / إهداء 🌸",
        "notes": "زهور الياسمين، فواكه حمراء، باودر ومسك",
        "rating": "4.8/5 (نعومة وأناقة)",
        "vibe": "هادئ، باودري، ومثالي كهدية فاخرة"
    },
    "عطر سول (Soul)": {
        "tag": "عصري وجذاب 🎯",
        "notes": "هيل، خزامى برية، خشب الصندل",
        "rating": "4.6/5 (شبابي حديث)",
        "vibe": "عصري، ملفت ومناسب للطلعات المسائية"
    }
}

# خيارات الاستلام
DELIVERY_OPTIONS = {
    "🤝 استلام شخصي - رد سي مول (مواقف بوابة 1)": 0.0,
    "📦 إيداع في أقرب خزانة RedBox ذكية بجدة": 15.0
}

# الحسبة الهندسية الدقيقة: (210 * 2 = 420) - 10% كود App10 = 378 ر.س ÷ 6 أشخاص = 63 ر.س
BASE_SLOT_PRICE = 63.0
IBAN_NUMBER = "SA9380000222608016013114"
ACCOUNT_NAME = "مصرف الراجحي | فارس ربيع العصيمي"

# ==============================================================================
# 4. محرك الشلال التلقائي وتصعيد الانتظار
# ==============================================================================
def process_basket_orders(session_key: str):
    now_utc = datetime.now(timezone.utc)
    now_utc_iso = now_utc.isoformat()
    
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
                is_paid = r.get("payment_status") == "paid"
                is_expired = r.get("expires_at") and r["expires_at"] <= now_utc_iso
                
                # إلغاء المقعد المعلق بعد 15 دقيقة
                if not is_paid and is_expired:
                    supabase.table("bookings").update({
                        "status": "cancelled",
                        "player_note": "انتهاء مهلة السداد (15 دقيقة)"
                    }).eq("id", r["id"]).execute()
                else:
                    confirmed_active.append(r)
                    
        # تصعيد فوري من الانتظار
        vacancies = BASKET_CAPACITY - len(confirmed_active)
        if vacancies > 0 and waitlist_records:
            to_promote = waitlist_records[:vacancies]
            for wr in to_promote:
                new_exp = (now_utc + timedelta(minutes=15)).isoformat()
                supabase.table("bookings").update({
                    "status": "confirmed",
                    "payment_status": "pending",
                    "expires_at": new_exp,
                    "player_note": "تصعيد تلقائي من الانتظار"
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
# 5. الواجهة الرئيسية
# ==============================================================================
st.markdown(f"""
<div class="hero-box">
    <div class="hero-title">🛍️ قطة عروض درعة الكبرى</div>
    <div class="hero-desc">عرض 1+2 مجاناً مكرر • سلة 6 عطور بأعلى نسبة خصم وتوفير</div>
    <div class="offer-pill">💎 قيمة عطرك: 63 ر.س فقط بدلاً من 210 ر.س (وفرت 70% صافي!)</div>
    <div style="font-size:0.82em; color:#cbd5e1; margin-top:4px;">
        📍 الاستلام المعتمد: <b>رد سي مول (جدة)</b> أو عبر <b>RedBox</b> • 
        <b>{'متبقي ' + str(slots_left) + ' مقاعد فقط وتكتمل السلة 🔥' if slots_left > 0 else 'السلة اكتملت (الانتظار متاح ⏳)'}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# بناء وعرض شبكة الحصص
slots_html = []
for i in range(BASKET_CAPACITY):
    if i < taken_count:
        item = confirmed_orders[i]
        c_name = html.escape(item['name'].split()[0])
        p_name = html.escape(item.get('level', 'عطر مختار'))
        status_txt = "تم الدفع ✅" if item.get('payment_status') == 'paid' else "مهلة سداد ⏳"
        slots_html.append(
            f'<div class="slot-card slot-taken">'
            f'🧴 <b>{c_name}</b><br>'
            f'<span style="font-size:0.82em; color:#f1f5f9;">{p_name}</span><br>'
            f'<span style="font-size:0.75em; color:#6ee7b7;">{status_txt}</span>'
            f'</div>'
        )
    else:
        slots_html.append(
            '<div class="slot-card slot-empty">'
            '✨ <b>حصة شاغرة</b><br>'
            '<span style="font-size:0.82em; color:#94a3b8;">اختر أي عطر ذهبي</span><br>'
            '<span style="font-size:0.75em; color:#818cf8;">احجز الآن (63 ر.س)</span>'
            '</div>'
        )

cards_markup = "".join(slots_html)
st.markdown(
    f'<div class="basket-container">'
    f'<div class="basket-header">🛒 سلة التجميع الحالية ({taken_count}/{BASKET_CAPACITY})</div>'
    f'<div class="slots-grid">{cards_markup}</div>'
    f'</div>',
    unsafe_allow_html=True
)

# ==============================================================================
# 6. شاشات ما بعد التسجيل والدفع
# ==============================================================================
if "deal_booked" in st.session_state:
    b = st.session_state["deal_booked"]
    
    if b.get("is_waitlist", False):
        st.markdown(f"""
        <div class="status-card-waitlist">
            <h3 style="color:#fbbf24; margin:0 0 6px 0;">⏳ مسجل في قائمة الانتظار للسلة القادمة</h3>
            <div style="font-size:1em; color:#fef3c7;">ترتيبك: <b style="font-size:1.3em;">#{b.get('pos', 1)}</b></div>
            <div style="font-size:0.82em; color:#fde68a; margin-top:4px;">
                في حال تخلف أي مشترك عن التحويل خلال 15 دقيقة، ستنتقل تلقائياً للحجز المباشر.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_wait_msg = f"هلا كابتن 🛍️\nأنا مسجل في انتظار سلة عطور درعة (63 ر.س)\n👤 الاسم: {b['name']}\n🧴 العطر: {b.get('perfume', '')}\n🔢 ترتيبي: #{b.get('pos', 1)}\nأول ما يتاح مقعد بلغني أحول فوراً!"
        wa_wait_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_wait_msg)}"
        st.markdown(f'<a href="{wa_wait_url}" target="_blank" class="wa-btn" style="background:#d97706;">📲 تأكيد وجودي بالانتظار عبر واتساب</a>', unsafe_allow_html=True)

    else:
        target_epoch_ms = b.get("expire_timestamp", 0)
        memo_full_text = f"{b['memo_code']} | {b['phone']}"
        total_price = b.get("total_price", BASE_SLOT_PRICE)
        
        st.markdown(f"""
        <div class="status-card-success">
            <h3 style="color:#10b981; margin:0 0 4px 0;">🎉 تم حجز عطرك في السلة!</h3>
            <div style="font-size:1.05em; color:#f8fafc; margin:6px 0;">
                المبلغ المطلوب للسداد: <b style="color:#10b981; font-size:1.35em;">{int(total_price)} ر.س</b>
            </div>
            <div style="font-size:0.82em; color:#94a3b8;">نص الملاحظة البنكية المطلوب نسخه عند التحويل:</div>
            <div class="memo-tag">{memo_full_text}</div>
            <div style="font-size:0.75em; color:#f87171;">(انسخ الكود وضعه في ملاحظات التحويل لمطابقة الحوالة فورياً)</div>
        </div>
        """, unsafe_allow_html=True)
        
        # عداد الـ 15 دقيقة المباشر
        components.html(f"""
        <!DOCTYPE html>
        <div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; border-radius: 12px; padding: 10px; color: #fca5a5; margin: 4px auto;">
            <div style="font-size: 13px; font-weight: 700;">⏱ مهلة تثبيت الحصة قبل التحويل للانتظار:</div>
            <div id="big_pay_timer" style="font-family: monospace; font-size: 32px; color: #ef4444; font-weight: 900;">--:--</div>
        </div>
        <script>
            var payTarget = {target_epoch_ms};
            function updatePayTimer() {{
                var diff = payTarget - new Date().getTime();
                var el = document.getElementById('big_pay_timer');
                if (!el) return;
                if (diff <= 0) {{
                    el.innerHTML = "00:00";
                    return;
                }}
                var m = Math.floor(diff / 60000);
                var s = Math.floor((diff % 60000) / 1000);
                el.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            }}
            updatePayTimer();
            setInterval(updatePayTimer, 1000);
        </script>
        """, height=95)
        
        st.caption(f"الحساب البنكي: {ACCOUNT_NAME}")
        st.code(IBAN_NUMBER, language=None)
        
        wa_msg = f"هلا كابتن 🛍️\nأكدت حجز عطري في قطة درعة الكبرى (63 ر.س):\n👤 الاسم: {b['name']}\n🧴 العطر: {b.get('perfume', '')}\n📍 الاستلام: {b.get('delivery', '')}\n🔖 كود التحويل: {memo_full_text}\n💵 المبلغ المحول: {int(total_price)} ر.س\n\nمرفق إيصال التحويل لتثبيت الحصة!"
        wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال وتأكيد الحجز عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 7. نموذج الاختيار الذكي والحجز
# ==============================================================================
else:
    is_waitlist = (slots_left == 0)
    btn_text = "الانضمام لقائمة انتظار السلة ⏳" if is_waitlist else "تثبيت العطر والانتقال للسداد (63 ر.س) 🛍️"
    
    if is_waitlist:
        st.warning(f"⚠️ اكتملت سلة الـ 6 عطور الحالية. التسجيل متاح في قائمة الانتظار لفتح سلة جديدة.")
        
    # استعراض تفاصيل العطر المختار بصرياً لضمان دقة قرار العميل دون تشتيت
    st.markdown("##### 1. استعرض واختر عطرك المفضل:")
    selected_perfume_name = st.selectbox("العطور الأكثر مبيعاً (المتوفرة بالعرض):", list(PERFUMES_CATALOG.keys()))
    perf_meta = PERFUMES_CATALOG[selected_perfume_name]
    
    st.markdown(f"""
    <div class="perfume-info-card">
        <span class="perfume-tag">{perf_meta['tag']}</span><br>
        • <b>المكونات والنوتات:</b> {perf_meta['notes']}<br>
        • <b>التقييم:</b> <span style="color:#fbbf24;">{perf_meta['rating']}</span> • <b>الطابع:</b> {perf_meta['vibe']}
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("perfume_deal_form"):
        st.markdown("##### 2. بيانات الحجز والاستلام:")
        f_name = st.text_input("الاسم الكريم", placeholder="اكتب اسمك الثنائي أو الثلاثي")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx")
        f_delivery = st.selectbox("طريقة ومكان الاستلام", list(DELIVERY_OPTIONS.keys()))
        
        chosen_fee = DELIVERY_OPTIONS[f_delivery]
        user_total = BASE_SLOT_PRICE + chosen_fee
        
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border-radius: 8px; padding: 10px; margin: 8px 0; font-size: 0.83em; color: #cbd5e1;">
            • السعر الأصلي بالمتجر: <del style="color:#94a3b8;">210 ر.س</del><br>
            • قيمة العطر بعد الخصم التشاركي (70%): <b style="color:#38bdf8;">{int(BASE_SLOT_PRICE)} ر.س</b><br>
            • رسوم الاستلام / التوصيل: <b>{int(chosen_fee)} ر.س</b><br>
            • <b>الإجمالي النهائي المطلوب: <span style="color:#10b981; font-size:1.15em;">{int(user_total)} ر.س</span></b>
        </div>
        """, unsafe_allow_html=True)
        
        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(btn_text, use_container_width=True)
        
        if submit_btn and not hp:
            clean_name = f_name.strip()
            raw_phone = f_phone.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
            clean_phone = re.sub(r'[\s\-\+]', '', raw_phone)
            if clean_phone.startswith("966"): clean_phone = "0" + clean_phone[3:]
            elif clean_phone.startswith("5"): clean_phone = "0" + clean_phone
            
            if len(clean_name) < 2 or not re.match(r"^05[0-9]{8}$", clean_phone):
                st.error("يرجى إدخال اسم صحيح ورقم جوال سعودي يبدأ بـ 05.")
            else:
                try:
                    c_active, w_active = process_basket_orders(BASKET_ID)
                    
                    if any(item["phone"] == clean_phone for item in c_active):
                        st.warning("أنت مشترك ومقعدك محجوز بالفعل في هذه السلة!")
                    elif any(item["phone"] == clean_phone for item in w_active):
                        st.warning("أنت مسجل مسبقاً في قائمة الانتظار!")
                    else:
                        memo_id = f"PRF-{clean_phone[-4:]}"
                        stored_note = f"PERFUME:{selected_perfume_name} | DELIV:{f_delivery} | TOTAL:{int(user_total)}"
                        
                        if len(c_active) < BASKET_CAPACITY:
                            now_utc = datetime.now(timezone.utc)
                            expire_dt = now_utc + timedelta(minutes=15)
                            
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": selected_perfume_name,
                                "status": "confirmed",
                                "payment_status": "pending",
                                "expires_at": expire_dt.isoformat(),
                                "hear_about": f_delivery[:25],
                                "player_note": stored_note
                            }).execute()
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": selected_perfume_name,
                                "delivery": f_delivery,
                                "total_price": user_total,
                                "memo_code": memo_id,
                                "is_waitlist": False,
                                "expire_timestamp": int(expire_dt.timestamp() * 1000)
                            }
                            st.rerun()
                        else:
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": selected_perfume_name,
                                "status": "waitlist",
                                "payment_status": "unpaid",
                                "hear_about": f_delivery[:25],
                                "player_note": stored_note
                            }).execute()
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": selected_perfume_name,
                                "delivery": f_delivery,
                                "total_price": user_total,
                                "memo_code": memo_id,
                                "is_waitlist": True,
                                "pos": len(w_active) + 1
                            }
                            st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الحجز: {ex}")

# ==============================================================================
# 8. لوحة الإدارة
# ==============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة وتنفيذ الطلب"):
    admin_pin = st.text_input("رمز الدخول السري (PIN):", type="password", key="admin_pin_perfume")
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PIN_HASH):
        st.success("🔓 تم فتح لوحة التحكم.")
        c_list, w_list = process_basket_orders(BASKET_ID)
        paid_orders = [o for o in c_list if o.get("payment_status") == "paid"]
        
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1f2937; border-radius:10px; padding:10px; margin-bottom:10px; font-size:0.85em;">
            • المقاعد المسددة: <b>{len(paid_orders)} / {BASKET_CAPACITY}</b><br>
            • حالة السلة: <b>{'جاهزة للتنفيذ المباشر من درعة ✅' if len(paid_orders) == BASKET_CAPACITY else 'بانتظار اكتمال التحويلات ⏳'}</b>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### 👥 المشتركون في السلة:")
        for row in c_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{row['name']}** - `{row.get('level', '-')}`\n`{row['phone']}`")
            if row['payment_status'] == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                if col3.button("تأكيد السداد", key=f"pay_perf_{row['id']}"):
                    supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                    st.rerun()
                    
        if len(paid_orders) == BASKET_CAPACITY:
            st.success("🎉 السلة مسددة 100%! نفذ الطلب عبر تطبيق درعة باستخدام كود App10 ليصلك مجاناً.")
