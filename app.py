import streamlit as st
from supabase import create_client, Client
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة والتصميم
# ==========================================
st.set_page_config(
    page_title="بادل 99 | Padel 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.block-container { 
    padding-top: 0.4rem !important; 
    padding-bottom: 1.5rem !important; 
    padding-left: 0.5rem !important; 
    padding-right: 0.5rem !important; 
    max-width: 100% !important; 
}

html, body, p, div, span, label, input, select, button, .stMarkdown {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Geeza Pro", Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
    box-sizing: border-box;
}

.hero-header { font-size: 1.55em; font-weight: 800; color: #f8fafc; margin: 0; line-height: 1.2; }
.hero-sub { font-size: 0.85em; color: #94a3b8; margin: 2px 0 6px 0; }
.contrast-pill { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 4px 8px; font-size: 0.74em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }
.promo-badge { background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.74em; margin-bottom: 4px; }

.thankyou-box {
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid #10b981;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0;
    text-align: center;
}
.thankyou-title { color: #34d399; font-size: 0.95em; font-weight: 700; margin-bottom: 2px; }
.thankyou-sub { color: #e2e8f0; font-size: 0.8em; }

.discount-receipt {
    background: rgba(59, 130, 246, 0.1);
    border: 1px dashed #3b82f6;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 6px 0;
    font-size: 0.82em;
    color: #93c5fd;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.alrajhi-card {
    background: #111418;
    border: 1.5px solid #2d3748;
    border-radius: 14px;
    padding: 12px;
    margin: 8px 0;
    color: #ffffff;
}
.card-top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 5px; margin-bottom: 8px; }
.bank-title { font-size: 0.9em; font-weight: 700; color: #f8fafc; }
.price-pill { background: #10b981; color: #022c22; padding: 2px 7px; border-radius: 12px; font-weight: 700; font-size: 0.8em; }
.qr-container { background: #ffffff; padding: 6px; border-radius: 8px; display: inline-block; margin: 2px auto 6px auto; }
.qr-container img { display: block; width: 115px; height: 115px; }
.card-owner { font-size: 1em; font-weight: 700; color: #f8fafc; margin-bottom: 6px; text-align: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.12); padding-bottom: 5px; }
.copy-badge {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    font-family: monospace;
    font-size: 0.84em;
    color: #38bdf8;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 5px;
}

.wa-btn {
    display: block;
    width: 100%;
    background: #25D366;
    color: white !important;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 6px;
    font-size: 0.88em;
}

.support-btn {
    display: block;
    width: 100%;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #cbd5e1 !important;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    margin-top: 10px;
    font-size: 0.8em;
}

.padel-court { background: #064e3b; border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 10px; padding: 8px; margin: 8px 0; }
.court-title { text-align: center; color: #a7f3d0; font-weight: 700; font-size: 0.85em; margin-bottom: 6px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 3px; }
.court-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.slot-box { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 5px 3px; text-align: center; min-height: 44px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.slot-occupied { color: #f4f4f5; font-weight: 600; font-size: 0.78em; line-height: 1.2; }
.slot-meta { display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 0.65em; margin-top: 2px; flex-wrap: wrap; }
.slot-empty { color: #64748b; font-size: 0.72em; }
.badge-loyalty { background-color: #1e3a8a; color: #93c5fd; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 600; }
.badge-level { background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 500; }

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ربط قاعدة البيانات السحابية (Supabase)
# ==========================================
COURT_CAPACITY = 6
BASE_PRICE = 65

# قائمة كوبونات الخصم النشطة
PROMO_CODES = {
    "PADEL99": {"type": "fixed", "val": 15, "desc": "خصم ترويجي 15 ر.س"},
    "HERO": {"type": "fixed", "val": 20, "desc": "خصم أبطال البادل 20 ر.س"},
    "FREE": {"type": "percent", "val": 100, "desc": "حجز مجاني بالكامل 100%"}
}

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

def get_session_bookings(db_session_key):
    try:
        res = supabase.table("bookings").select("*").eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).order("id").execute()
        data = res.data or []
        confirmed = [d for d in data if d["status"] == "confirmed"][:COURT_CAPACITY]
        waitlist = [d for d in data if d["status"] == "waitlist"]
        return confirmed, waitlist
    except Exception:
        return [], []

def get_loyalty_score(phone):
    try:
        res = supabase.table("bookings").select("session_day").eq("phone", phone).eq("status", "confirmed").execute()
        return len(set(d["session_day"] for d in (res.data or [])))
    except Exception:
        return 0

# ==========================================
# 3. المنطق ودوال المعالجة
# ==========================================
def clean_and_validate_sa_phone(raw_phone):
    if not raw_phone:
        return None
    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    p = str(raw_phone).translate(ar_digits).strip()
    p = re.sub(r'[\s\-\(\)\+]', '', p)
    if p.startswith("966"):
        p = "0" + p[3:]
    elif p.startswith("5"):
        p = "0" + p
    if re.match(r"^05[0-9]{8}$", p):
        return p
    return None

def get_next_session():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    weekday = now.weekday()

    schedule = {
        6: (0, "الأحد"),
        0: (1, "الثلاثاء"),
        1: (0, "الثلاثاء"),
        2: (1, "الخميس"),
        3: (0, "الخميس"),
        4: (2, "الأحد"),
        5: (1, "الأحد")
    }
    
    days_to_add, d_ar = schedule.get(weekday, (0, "الأحد"))
    target_date = now + timedelta(days=days_to_add)
    label_ar = f"{d_ar} ({target_date.strftime('%d/%m')})"
    db_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"
    return label_ar, db_key

def get_level_badge(lvl):
    if lvl in ["Advanced", "متقدم"]:
        return "🔥 متقدم"
    elif lvl in ["Beginner", "مبتدئ"]:
        return "⚪ مبتدئ"
    return "🟢 متوسط"

def calculate_discount(code, total_amount):
    if not code:
        return 0, None
    clean_code = code.strip().upper()
    if clean_code in PROMO_CODES:
        rule = PROMO_CODES[clean_code]
        if rule["type"] == "fixed":
            disc = min(rule["val"], total_amount)
        else:
            disc = int(total_amount * (rule["val"] / 100))
        return disc, rule["desc"]
    return 0, None

# ==========================================
# 4. بناء الواجهة
# ==========================================
display_session, db_session_key = get_next_session()
c1, waitlist = get_session_bookings(db_session_key)
total_booked = len(c1)

st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session}. متعة اللعب، بتنظيم أبسط.</div>", unsafe_allow_html=True)
st.markdown("<div class='contrast-pill'>⚡ حجز فوري • 6 لاعبين للملعب • السابع علينا.</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين واحصل على السابع مجاناً</div>", unsafe_allow_html=True)
st.caption(f"⏰ 9:30 م إلى 11:00 م | كورت 1 • <b>المؤكدين: {total_booked}/6</b>", unsafe_allow_html=True)

tab_book, tab_rules, tab_cancel = st.tabs(["⚡ حجز مقعد", "📜 القواعد", "❌ اعتذار"])

# --- تبويب الحجز ---
with tab_book:
    with st.form("booking_form", clear_on_submit=True):
        st.markdown("##### 👤 بياناتك الأساسية")
        f_name = st.text_input("الاسم الثلاثي")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx")
        f_level_raw = st.selectbox("مستوى اللعب", [
            "🟢 متوسط - تبادل وثبات",
            "🔥 متقدم - سرعة وتكتيك",
            "⚪ مبتدئ - انطلاقة وتعلّم"
        ])
        f_level = "متوسط" if "متوسط" in f_level_raw else ("متقدم" if "متقدم" in f_level_raw else "مبتدئ")
        
        # خيار حجز الصديق
        st.markdown("---")
        add_friend = st.checkbox("🎾 احجز مقعد إضافي لخويك معك")
        f_friend_name = ""
        f_friend_phone = ""
        
        if add_friend:
            st.info("💡 **سجّل جوال خويك عشان ما تضيع عليه نقاط الولاء!** كل تمرين يسجله باسمه يقرّبه من تمرين الـ 7 المجاني 🎁")
            f_friend_name = st.text_input("اسم خويك")
            f_friend_phone = st.text_input("رقم جوال خويك (05xxxxxxxx)", placeholder="05xxxxxxxx")
        
        # كود الخصم
        st.markdown("---")
        f_promo = st.text_input("🎟️ كود الخصم (إن وجد):", placeholder="مثلاً: PADEL99").strip().upper()

        with st.expander("💡 استبيان سريع (اختياري)", expanded=False):
            f_source = st.selectbox("كيف سمعت عن بادل 99؟", ["قروب واتساب", "توصية من صديق", "منصة إكس أو تيك توك", "أخرى"])
            f_note = st.text_input("ملاحظة أو اقتراح لتمرين اليوم:", placeholder="مثلاً: تفضيل كور معينة أو وقت...")

        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button("تأكيد الانضمام 🚀", use_container_width=True)

        if btn_submit:
            if honeypot_val:
                st.error("تم رفض الطلب للاشتباه في نشاط آلي.")
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            # التحقق من بيانات الصديق
            friend_valid = True
            clean_fname = f_friend_name.strip()
            clean_fphone = clean_and_validate_sa_phone(f_friend_phone)

            if add_friend:
                if len(clean_fname) < 2 or not clean_fphone:
                    friend_valid = False
                elif clean_fphone == clean_phone:
                    st.error("يجب إدخال رقم جوال مختلف لخويك لاحتساب نقاط الولاء له بشكل منفصل.")
                    friend_valid = False

            if len(clean_name) < 2 or not clean_phone:
                st.error("فضلاً أدخل اسمك ورقم جوال صحيح يبدأ بـ 05.")
            elif add_friend and not friend_valid:
                st.error("فضلاً أدخل اسم خويك ورقم جواله بشكل صحيح.")
            else:
                try:
                    existing = supabase.table("bookings").select("id").eq("phone", clean_phone).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                    
                    if existing.data and len(existing.data) > 0:
                        st.warning("أنت مسجل بالفعل في تمرين اليوم.")
                    else:
                        conf_res = supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "confirmed").execute()
                        cur_conf_count = len(conf_res.data or [])
                        
                        # حساب المبالغ والخصم
                        num_seats = 2 if add_friend else 1
                        subtotal = num_seats * BASE_PRICE
                        disc_amount, disc_desc = calculate_discount(f_promo, subtotal)
                        final_total = max(0, subtotal - disc_amount)

                        # تسجيل اللاعب الأساسي
                        p1_status = "confirmed" if cur_conf_count < COURT_CAPACITY else "waitlist"
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": db_session_key,
                            "court": 1,
                            "level": f_level,
                            "status": p1_status,
                            "payment_status": "paid" if final_total == 0 else "pending",
                            "hear_about": f_source,
                            "player_note": f"{f_note} | كود: {f_promo}" if f_promo else f_note
                        }).execute()

                        # تسجيل المرافق إن وجد
                        p2_status = None
                        if add_friend:
                            new_count = cur_conf_count + 1
                            p2_status = "confirmed" if new_count < COURT_CAPACITY else "waitlist"
                            supabase.table("bookings").insert({
                                "name": clean_fname,
                                "phone": clean_fphone,
                                "session_day": db_session_key,
                                "court": 1,
                                "level": f_level,
                                "status": p2_status,
                                "payment_status": "paid" if final_total == 0 else "pending",
                                "hear_about": f"مع {clean_name}",
                                "player_note": f"حجز مرافق مع {clean_name} | كود: {f_promo}" if f_promo else f"حجز مرافق مع {clean_name}"
                            }).execute()

                        st.session_state["last_booking"] = {
                            "name": clean_name,
                            "phone": clean_phone,
                            "status": p1_status,
                            "friend_name": clean_fname if add_friend else None,
                            "friend_status": p2_status,
                            "subtotal": subtotal,
                            "disc_amount": disc_amount,
                            "disc_desc": disc_desc,
                            "final_total": final_total,
                            "promo_code": f_promo,
                            "session": display_session,
                            "is_new": True
                        }
                        st.rerun()
                except Exception as err:
                    st.error(f"حدث خطأ أثناء إتمام الحجز: {err}")

    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        has_friend = lb.get("friend_name") is not None
        
        if lb["status"] == "confirmed":
            if lb.get("is_new", False):
                st.balloons()
                lb["is_new"] = False

            conf_text = f"تم تأكيد حجزك وحجز خويك ({lb['friend_name']}) بنجاح!" if has_friend and lb["friend_status"] == "confirmed" else "تم تأكيد حجزك بنجاح!"

            st.markdown(f"""
            <div class="thankyou-box">
                <div class="thankyou-title">✅ {conf_text} يا كابتن {lb['name']}</div>
                <div class="thankyou-sub">تم حجز المقاعد في <b>{lb['session']}</b>. نلتقي في الملعب!</div>
            </div>
            """, unsafe_allow_html=True)
            
            # توضيح تفاصيل الخصم للمستفيدين
            if lb.get("disc_amount", 0) > 0:
                beneficiaries = f"{lb['name']} + {lb['friend_name']}" if has_friend else lb['name']
                st.markdown(f"""
                <div class="discount-receipt">
                    <div>🎟️ <b>كود: {lb['promo_code']}</b> ({lb['disc_desc']})<br><small style="color:#cbd5e1;">المستفيدين: {beneficiaries}</small></div>
                    <div style="text-align:left;">
                        <span style="text-decoration: line-through; color:#94a3b8; font-size:0.85em;">{lb['subtotal']} ر.س</span><br>
                        <b style="color:#34d399; font-size:1.1em;">{lb['final_total']} ر.س</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # بطاقة الدفع (تظهر فقط إذا كان هناك مبلغ مستحق)
            if lb["final_total"] > 0:
                iban_raw = "SA9380000222608016013114"
                iban_display = "SA93 8000 0222 6080 1601 3114"
                acc_raw = "222000010006086013114"
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={iban_raw}&color=000000&bgcolor=ffffff"

                card_html = f"""
                <div class="alrajhi-card">
                    <div class="card-top">
                        <div class="bank-title">🏛️ مصرف الراجحي</div>
                        <div class="price-pill">{lb['final_total']} ر.س</div>
                    </div>
                    <div style="text-align:center;">
                        <div class="qr-container">
                            <img src="{qr_url}" alt="QR" />
                        </div>
                    </div>
                    <div class="card-owner">فارس ربيع بن عواض العصيمي</div>
                    <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الحساب:</div>
                    <div class="copy-badge">
                        <span>{acc_raw}</span>
                    </div>
                    <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الآيبان:</div>
                    <div class="copy-badge">
                        <span>{iban_display}</span>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                extra_msg = f" وخويي: {lb['friend_name']}" if has_friend else ""
                promo_info = f"\nكود الخصم: {lb['promo_code']} (وفرت {lb['disc_amount']} ر.س)" if lb.get("disc_amount", 0) > 0 else ""
                wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {lb['name']}{extra_msg}\nالتمرين: {lb['session']} (كورت 1){promo_info}\nالمبلغ المطلوب: {lb['final_total']} ر.س\n\nمرفق إشعار التحويل لحساب كابتن فارس العصيمي."
                wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتثبيت المقاعد</a>', unsafe_allow_html=True)
            else:
                st.success("🎉 تم تطبيق خصم مجاني بالكامل! مقعدك مؤكد دون الحاجة لتحويل بنكي.")
        else:
            st.info("اكتملت المقاعد الأساسية للتمرين. تم تسجيلك في قائمة الاحتياط وسيتواصل معك المنظم فور توفر مقعد.")

# --- تبويب القواعد ---
with tab_rules:
    st.markdown("""
    <div style="background:#18181b; border:1px solid #27272a; border-radius:10px; padding:10px; margin:8px 0; font-size:0.82em; color:#e2e8f0; line-height:1.4;">
        <div style="margin-bottom:8px;">⏱️ <b>قبل 4 ساعات:</b> استرجاع كامل أو ترحيل فوري لتمرينك القادم.</div>
        <div style="margin-bottom:8px;">⚠️ <b>أقل من 4 ساعات:</b> يُسترجع المبلغ فور تأكيد لاعب بديل من قائمة الانتظار.</div>
        <div>⚡ <b>تأكيد فوري:</b> أرسل إشعار التحويل خلال 15 دقيقة لضمان تثبيت مقعدك.</div>
    </div>
    """, unsafe_allow_html=True)

# --- تبويب الاعتذار والإلغاء ---
with tab_cancel:
    with st.form("cancel_form", clear_on_submit=True):
        can_phone_raw = st.text_input("رقم الجوال المسجل")
        can_reason = st.selectbox("سبب الاعتذار", [
            "تعارض في المواعيد أو انشغال طارئ",
            "إجهاد بدني أو إصابة",
            "ظرف عائلي طارئ",
            "صعوبة في المواصلات"
        ])
        btn_cancel_sub = st.form_submit_button("إلغاء المقعد وإتاحته للبديل", use_container_width=True)

        if btn_cancel_sub:
            clean_cp = clean_and_validate_sa_phone(can_phone_raw)
            if not clean_cp:
                st.error("فضلاً أدخل رقم جوال صحيح.")
            else:
                try:
                    rec = supabase.table("bookings").select("*").eq("phone", clean_cp).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                    
                    if rec.data and len(rec.data) > 0:
                        target = rec.data[0]
                        was_confirmed = target["status"] == "confirmed"
                        player_name = target["name"]
                        
                        supabase.table("bookings").update({"status": "cancelled"}).eq("id", target["id"]).execute()
                        
                        promoted_name = None
                        if was_confirmed:
                            w_player = supabase.table("bookings").select("*").eq("session_day", db_session_key).eq("status", "waitlist").order("id").limit(1).execute()
                            if w_player.data and len(w_player.data) > 0:
                                p_id = w_player.data[0]["id"]
                                promoted_name = w_player.data[0]["name"]
                                supabase.table("bookings").update({"status": "confirmed"}).eq("id", p_id).execute()
                        
                        st.success(f"تم إلغاء الحجز بنجاح يا كابتن {player_name}.")
                        if promoted_name:
                            st.info(f"⚡ تم تصعيد الكابتن **{promoted_name}** من قائمة الانتظار للملعب مباشرة!")
                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error("لا يوجد حجز نشط مرتبط بهذا الرقم لتمرين اليوم.")
                except Exception as err:
                    st.error(f"حدث خطأ أثناء الإلغاء: {err}")

# ==========================================
# 5. تشكيلة الملعب
# ==========================================
st.markdown("---")
slots_html = ""
for i in range(COURT_CAPACITY):
    if i < len(c1):
        p = c1[i]
        loyalty_val = get_loyalty_score(p["phone"])
        points = (loyalty_val % 7)
        pts_badge = f"⭐ {points}/6" if points < 6 else "🎁 مجاني!"
        pay_icon = "✅" if p.get("payment_status") == "paid" else "⏳"
        lvl_badge = get_level_badge(p.get("level", "متوسط"))
        slots_html += f'''<div class="slot-box">
            <div class="slot-occupied">🎾 {p["name"]}</div>
            <div class="slot-meta">
                <span class="badge-level">{lvl_badge}</span>
                <span class="badge-loyalty">{pts_badge}</span>
                <span>{pay_icon}</span>
            </div>
        </div>'''
    else:
        slots_html += '<div class="slot-box"><div class="slot-empty">مقعد شاغر ✨</div></div>'

st.markdown(f'<div class="padel-court"><div class="court-title">🏟️ كورت 1 ({len(c1)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>', unsafe_allow_html=True)

if waitlist:
    st.caption("📋 **قائمة الانتظار النشطة:** " + " • ".join([f"#{idx+1} {w['name']}" for idx, w in enumerate(waitlist)]))

# ==========================================
# 6. الدعم والمساعدة
# ==========================================
support_msg = "مرحباً كابتن فارس، عندي استفسار بخصوص حجز بادل 99."
support_url = f"https://wa.me/966566261868?text={urllib.parse.quote(support_msg)}"
st.markdown(f'<a href="{support_url}" target="_blank" class="support-btn">💬 تواجه مشكلة؟ تواصل مباشرة عبر واتساب</a>', unsafe_allow_html=True)

# ==========================================
# 7. لوحة الإدارة والتحليلات
# ==========================================
with st.expander("⚙️ لوحة الإدارة والتحليلات", expanded=False):
    pin_input = st.text_input("رمز الإدارة المشفر:", type="password")
    
    if pin_input:
        ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        p = str(pin_input).translate(ar_digits).strip()
        
        if hmac.compare_digest(p, "Padel99#Master@2026"):
            st.success("تم تأكيد الهوية 👑")
            try:
                all_res = supabase.table("bookings").select("*").order("id", desc=True).execute()
                records = all_res.data or []
                
                if records:
                    conf_count = len([r for r in records if r["status"] == "confirmed"])
                    paid_count = len([r for r in records if r["payment_status"] == "paid"])
                    
                    c_kpi1, c_kpi2 = st.columns(2)
                    c_kpi1.metric("إجمالي الحجوزات السحابية", conf_count)
                    c_kpi2.metric("المؤكد دفعهم", f"{paid_count * 65} ر.س")
                    
                    st.markdown("---")
                    st.markdown("##### 🗑️ إدارة البيانات:")
                    col_reset1, col_reset2 = st.columns(2)
                    with col_reset1:
                        if st.button("تصفير تمرين اليوم فقط 🔄", use_container_width=True):
                            supabase.table("bookings").delete().eq("session_day", db_session_key).execute()
                            st.success("تم تصفير تمرين اليوم بنجاح!")
                            st.rerun()
                    with col_reset2:
                        if st.button("تصفير قاعدة البيانات بالكامل ⚠️", use_container_width=True):
                            supabase.table("bookings").delete().neq("id", 0).execute()
                            st.success("تم تفريغ السجل السحابي بالكامل!")
                            st.rerun()
            except Exception as err:
                st.error(f"خطأ في لوحة التحكم: {err}")
        else:
            st.error("رمز الدخول غير صحيح.")
