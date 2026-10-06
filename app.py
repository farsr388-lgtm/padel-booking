import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة والتصميم السريع
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | قطة عطور درعة",
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
    max-width: 420px !important; 
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
    border-radius: 14px;
    padding: 12px;
    text-align: center;
    margin-bottom: 8px;
}
.hero-title { font-size: 1.4em; font-weight: 900; color: #f8fafc; margin: 0; }
.offer-pill {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid #818cf8;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.8em;
    color: #c7d2fe;
    margin: 6px 0;
    display: inline-block;
    font-weight: 800;
}
.slots-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin: 8px 0;
}
.slot-card {
    border-radius: 8px;
    padding: 8px 4px;
    text-align: center;
    font-size: 0.78em;
    font-weight: 800;
    line-height: 1.35;
}
.slot-empty {
    background: rgba(30, 41, 59, 0.5);
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
    padding: 6px 10px;
    display: inline-block;
    font-family: monospace;
    font-size: 1em;
    color: #818cf8;
    font-weight: 800;
    margin: 4px 0;
}
.status-card-success {
    background: rgba(16, 185, 129, 0.12);
    border: 2px solid #10b981;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    margin-top: 8px;
}
.wa-btn {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 0.95em;
    text-decoration: none;
    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
    margin-top: 8px;
}
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 48px !important;
    border-radius: 10px !important;
    border: none !important;
    margin-top: 4px !important;
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
    st.error("تعذر الاتصال بقاعدة البيانات. تأكد من إعداد Secrets.")
    st.stop()

# ==============================================================================
# 3. إعدادات السلة والحسبة المالية المحدثة (RedBox: 25 ر.س)
# ==============================================================================
BASKET_ID = "MAQSOOM-DERAAH-01"
BASKET_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")

# قائمة مختصرة ومباشرة مع طابع العطر لتقليل التشتت
PERFUMES = {
    "عطر ليدر (Leader)": "جلود وأخشاب فاخرة • رسمي وفخم",
    "عطر بورموا (Pour Moi)": "فانيلا وعنبر دافئ • سويت وجذاب",
    "عطر لينك الأسود (Link Black)": "حمضيات وبرغموت • منعش واستخدام يومي",
    "عطر خواطر (Khawater)": "باتشولي وعود خفيف • كلاسيكي وثبات عالي",
    "عطر سول (Soul)": "هيل وصندل • شبابي وعصري",
    "عطر ميس درعة (Miss Deraah)": "ياسمين وباودر ناعم • هادئ ولطيف"
}

PERFUME_SHARE = 63.0             # قيمة العطر الصافية بالعرض
REDBOX_FEE = 25.0                # رسوم الخزانة الذكية المحدثة
TOTAL_SLOT_PRICE = PERFUME_SHARE + REDBOX_FEE  # 88.0 ر.س شامل كل شيء

IBAN_NUMBER = "SA9380000222608016013114"
ACCOUNT_NAME = "مصرف الراجحي | فارس ربيع العصيمي"

# ==============================================================================
# 4. محرك الشلال التلقائي (Waterfall Lifecycle)
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
                
                if not is_paid and is_expired:
                    supabase.table("bookings").update({
                        "status": "cancelled",
                        "player_note": "انتهاء مهلة السداد (15 دقيقة)"
                    }).eq("id", r["id"]).execute()
                else:
                    confirmed_active.append(r)
                    
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
# 5. الواجهة البصرية المباشرة
# ==============================================================================
st.markdown(f"""
<div class="hero-box">
    <div class="hero-title">🛍️ مَقسوم | قطة عطور درعة</div>
    <div class="offer-pill">💎 الإجمالي: 88 ر.س فقط (العطر: 63 + خزانة RedBox: 25)</div>
    <div style="font-size:0.82em; color:#cbd5e1; margin-top:2px;">
        قيمة العطر بالمتجر 210 ر.س • <b>متبقي {slots_left} مقاعد فقط وتكتمل السلة 🔥</b>
    </div>
</div>
""", unsafe_allow_html=True)

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
            '<span style="font-size:0.75em; color:#818cf8;">احجز الآن (88 ر.س)</span>'
            '</div>'
        )

cards_markup = "".join(slots_html)
st.markdown(f'<div class="slots-grid">{cards_markup}</div>', unsafe_allow_html=True)

# ==============================================================================
# 6. شاشة ما بعد الحجز والدفع
# ==============================================================================
if "deal_booked" in st.session_state:
    b = st.session_state["deal_booked"]
    
    if b.get("is_waitlist", False):
        st.warning(f"⏳ تم تسجيلك في قائمة الانتظار (ترتيبك: #{b.get('pos', 1)}). سنتواصل معك فور توفر مقعد.")
    else:
        target_epoch_ms = b.get("expire_timestamp", 0)
        memo_full_text = f"{b['memo_code']} | {b['phone']}"
        
        st.markdown(f"""
        <div class="status-card-success">
            <h3 style="color:#10b981; margin:0 0 4px 0;">🎉 تم حجز عطرك في السلة!</h3>
            <div style="font-size:1.05em; color:#f8fafc; margin:4px 0;">
                المبلغ المطلوب للسداد: <b style="color:#10b981; font-size:1.3em;">{int(TOTAL_SLOT_PRICE)} ر.س</b>
            </div>
            <div style="font-size:0.8em; color:#94a3b8;">انسخ الكود التالي وضعه في ملاحظة التحويل بالبنك:</div>
            <div class="memo-tag">{memo_full_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
        components.html(f"""
        <!DOCTYPE html>
        <div style="direction: rtl; text-align: center; font-family: -apple-system, sans-serif; background: rgba(239, 68, 68, 0.2); border: 1.5px solid #ef4444; border-radius: 10px; padding: 6px; color: #fca5a5; margin: 4px auto;">
            <span style="font-size: 12px; font-weight: 700;">⏱ مهلة تثبيت الحصة: </span>
            <span id="big_pay_timer" style="font-family: monospace; font-size: 22px; color: #ef4444; font-weight: 900;">--:--</span>
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
        """, height=50)
        
        st.caption(f"الحساب: {ACCOUNT_NAME}")
        st.code(IBAN_NUMBER, language=None)
        
        wa_msg = f"هلا كابتن 🛍️\nحجزت عطري في قطة درعة (88 ر.س):\n👤 الاسم: {b['name']}\n🧴 العطر: {b.get('perfume', '')}\n📦 خزانة RedBox: {b.get('redbox_loc', '')}\n🔖 كود التحويل: {memo_full_text}\n\nمرفق إيصال التحويل لتأكيد المقعد!"
        wa_url = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال الإيصال عبر واتساب</a>', unsafe_allow_html=True)

# ==============================================================================
# 7. نموذج الحجز المبسط (3 حقول فقط لتقليل الجهد)
# ==============================================================================
else:
    is_waitlist = (slots_left == 0)
    btn_text = "التسجيل في قائمة الانتظار ⏳" if is_waitlist else "تثبيت العطر (88 ر.س شامل RedBox) 🛍️️"
    
    with st.form("perfume_deal_form"):
        # حقل 1: اختيار العطر مع وصفه الفوري المباشر
        perfume_options = [f"{k} — ({v})" for k, v in PERFUMES.items()]
        f_perfume_raw = st.selectbox("1. اختر عطرك المفضل:", perfume_options)
        selected_perfume = f_perfume_raw.split(" — ")[0]
        
        # حقل 2: الاسم
        f_name = st.text_input("2. اسمك الكريم:", placeholder="الاسم الثنائي أو الثلاثي")
        
        # حقل 3: الجوال
        f_phone = st.text_input("3. رقم الجوال:", placeholder="05xxxxxxxx")
        
        # حقل 4: موقع الخزانة
        f_redbox = st.text_input("4. الحي أو موقع أقرب خزانة RedBox لك:", placeholder="مثال: حي الروضة / المرجان")
        
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
            elif not f_redbox.strip():
                st.error("فضلاً حدد اسم الحي أو موقع خزانة RedBox.")
            else:
                try:
                    c_active, w_active = process_basket_orders(BASKET_ID)
                    
                    if any(item["phone"] == clean_phone for item in c_active):
                        st.warning("أنت مسجل بالفعل في هذه السلة!")
                    elif any(item["phone"] == clean_phone for item in w_active):
                        st.warning("أنت مسجل مسبقاً في قائمة الانتظار!")
                    else:
                        memo_id = f"PRF-{clean_phone[-4:]}"
                        stored_note = f"PERFUME:{selected_perfume} | REDBOX:{f_redbox.strip()} | TOTAL:{int(TOTAL_SLOT_PRICE)}"
                        
                        if len(c_active) < BASKET_CAPACITY:
                            now_utc = datetime.now(timezone.utc)
                            expire_dt = now_utc + timedelta(minutes=15)
                            
                            supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": selected_perfume,
                                "status": "confirmed",
                                "payment_status": "pending",
                                "expires_at": expire_dt.isoformat(),
                                "hear_about": f_redbox.strip()[:25],
                                "player_note": stored_note
                            }).execute()
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": selected_perfume,
                                "redbox_loc": f_redbox.strip(),
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
                                "level": selected_perfume,
                                "status": "waitlist",
                                "payment_status": "unpaid",
                                "hear_about": f_redbox.strip()[:25],
                                "player_note": stored_note
                            }).execute()
                            
                            st.session_state["deal_booked"] = {
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": selected_perfume,
                                "redbox_loc": f_redbox.strip(),
                                "memo_code": memo_id,
                                "is_waitlist": True,
                                "pos": len(w_active) + 1
                            }
                            st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء معالجة الحجز: {ex}")

# ==============================================================================
# 8. لوحة الإدارة الآمنة
# ==============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ لوحة الإدارة"):
    admin_pin = st.text_input("رمز الدخول (Password):", type="password", key="admin_pwd_input")
    if admin_pin and hmac.compare_digest(admin_pin.strip(), ADMIN_PASSWORD_HASH):
        st.success("🔓 تم فتح لوحة التحكم.")
        c_list, _ = process_basket_orders(BASKET_ID)
        paid_orders = [o for o in c_list if o.get("payment_status") == "paid"]
        
        st.caption(f"المقاعد المسددة: {len(paid_orders)} / {BASKET_CAPACITY}")
        for row in c_list:
            col1, col2, col3 = st.columns([2.2, 1, 1])
            col1.write(f"**{row['name']}** - `{row.get('level', '-')}`\n`{row['phone']}`")
            if row['payment_status'] == 'paid':
                col2.markdown("<span style='color:#10b981; font-weight:700;'>مدفوع ✅</span>", unsafe_allow_html=True)
            else:
                col2.markdown("<span style='color:#fbbf24; font-weight:700;'>معلق ⏳</span>", unsafe_allow_html=True)
                if col3.button("تأكيد", key=f"pay_perf_{row['id']}"):
                    supabase.table("bookings").update({"payment_status": "paid"}).eq("id", row['id']).execute()
                    st.rerun()
