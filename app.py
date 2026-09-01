import streamlit as st
from supabase import create_client, Client
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة والتصميم المبسط والخفيف
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
    padding-top: 0.5rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 100% !important; 
}

html, body, p, div, span, label, input, select, button, .stMarkdown {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Geeza Pro", Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
}

.hero-header { font-size: 1.6em; font-weight: 800; color: #f8fafc; margin: 0; }
.hero-sub { font-size: 0.9em; color: #94a3b8; margin-bottom: 6px; }
.promo-badge { background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.78em; margin-bottom: 6px; }

.thankyou-box {
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid #10b981;
    border-radius: 10px;
    padding: 12px;
    margin: 8px 0;
    text-align: center;
}
.thankyou-title { color: #34d399; font-size: 1em; font-weight: 700; }
.thankyou-sub { color: #e2e8f0; font-size: 0.85em; }

.alrajhi-card {
    background: #111418;
    border: 1.5px solid #2d3748;
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0;
    color: #ffffff;
}
.card-top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 5px; margin-bottom: 8px; }
.bank-title { font-size: 0.9em; font-weight: 700; color: #f8fafc; }
.price-pill { background: #10b981; color: #022c22; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.85em; }
.qr-container { background: #ffffff; padding: 6px; border-radius: 8px; display: inline-block; margin: 4px auto; }
.qr-container img { display: block; width: 110px; height: 110px; }
.card-owner { font-size: 0.95em; font-weight: 700; color: #f8fafc; text-align: center; margin: 6px 0; }
.copy-badge {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    font-family: monospace;
    font-size: 0.85em;
    color: #38bdf8;
    margin-bottom: 5px;
    text-align: center;
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
    font-size: 0.9em;
}

.padel-court { background: #064e3b; border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 10px; padding: 8px; margin: 10px 0; }
.court-title { text-align: center; color: #a7f3d0; font-weight: 700; font-size: 0.85em; margin-bottom: 6px; }
.court-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.slot-box { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 6px 4px; text-align: center; }
.slot-occupied { color: #f4f4f5; font-weight: 600; font-size: 0.8em; }
.slot-meta { display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.7em; margin-top: 3px; }
.slot-empty { color: #64748b; font-size: 0.75em; }
.badge-loyalty { background-color: #1e3a8a; color: #93c5fd; padding: 1px 4px; border-radius: 3px; font-weight: 600; }

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ربط قاعدة البيانات السحابية (Supabase)
# ==========================================
COURT_CAPACITY = 6
BASE_PRICE = 65

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

# ==========================================
# 4. بناء الواجهة
# ==========================================
display_session, db_session_key = get_next_session()
c1, waitlist = get_session_bookings(db_session_key)
total_booked = len(c1)

st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session} • 6 لاعبين للملعب</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين واحصل على السابع مجاناً</div>", unsafe_allow_html=True)
st.caption(f"⏰ 9:30 م إلى 11:00 م | <b>المؤكدين: {total_booked}/6</b>", unsafe_allow_html=True)

tab_book, tab_rules, tab_cancel = st.tabs(["⚡ حجز مقعد", "📜 القواعد", "❌ اعتذار"])

# --- تبويب الحجز ---
with tab_book:
    with st.form("booking_form", clear_on_submit=True):
        f_name = st.text_input("الاسم الثلاثي")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx")
        f_level = st.selectbox("مستوى اللعب", ["متوسط", "متقدم", "مبتدئ"])
        
        # خيار إضافة الصديق
        st.markdown("---")
        add_friend = st.checkbox("🎾 احجز مقعد إضافي لخويك معك")
        f_friend_name = ""
        f_friend_phone = ""
        f_friend_level = "متوسط"
        
        if add_friend:
            st.info("💡 **سجّل جوال خويك عشان ما تضيع عليه نقاط الولاء!** كل تمرين يسجله باسمه يقرّبه من تمرين الـ 7 المجاني 🎁")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                f_friend_name = st.text_input("اسم خويك")
            with col_f2:
                f_friend_level = st.selectbox("مستوى خويك", ["متوسط", "متقدم", "مبتدئ"], key="friend_level")
            f_friend_phone = st.text_input("رقم جوال خويك (05xxxxxxxx)", placeholder="05xxxxxxxx")

        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button("تأكيد الانضمام 🚀", use_container_width=True)

        if btn_submit:
            if honeypot_val:
                st.error("تم رفض الطلب للاشتباه في نشاط آلي.")
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            friend_valid = True
            clean_fname = f_friend_name.strip()
            clean_fphone = clean_and_validate_sa_phone(f_friend_phone)

            if add_friend:
                if len(clean_fname) < 2 or not clean_fphone:
                    friend_valid = False
                elif clean_fphone == clean_phone:
                    st.error("يجب إدخال رقم جوال مختلف لخويك لاحتساب نقاط الولاء له.")
                    friend_valid = False

            if len(clean_name) < 2 or not clean_phone:
                st.error("فضلاً أدخل اسمك ورقم جوال صحيح يبدأ بـ 05.")
            elif add_friend and not friend_valid:
                st.error("فضلاً أدخل اسم خويك ورقم جواله بشكل صحيح.")
            else:
                try:
                    # التحقق من وجود حجز مسبق للاعب الأساسي
                    existing = supabase.table("bookings").select("id").eq("phone", clean_phone).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                    
                    if existing.data and len(existing.data) > 0:
                        st.warning("أنت مسجل بالفعل في تمرين اليوم.")
                    else:
                        conf_res = supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "confirmed").execute()
                        cur_conf_count = len(conf_res.data or [])
                        
                        # تحديد حالة اللاعب الأساسي
                        p1_status = "confirmed" if cur_conf_count < COURT_CAPACITY else "waitlist"
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": db_session_key,
                            "court": 1,
                            "level": f_level,
                            "status": p1_status,
                            "payment_status": "pending"
                        }).execute()

                        # تحديد حالة المرافق
                        p2_status = None
                        if add_friend:
                            # إذا حجز الأساسي مقعد مؤكد يرتفع العدد بواحد
                            slots_after_p1 = cur_conf_count + (1 if p1_status == "confirmed" else 0)
                            p2_status = "confirmed" if slots_after_p1 < COURT_CAPACITY else "waitlist"
                            
                            supabase.table("bookings").insert({
                                "name": clean_fname,
                                "phone": clean_fphone,
                                "session_day": db_session_key,
                                "court": 1,
                                "level": f_friend_level,
                                "status": p2_status,
                                "payment_status": "pending"
                            }).execute()

                        st.session_state["last_booking"] = {
                            "name": clean_name,
                            "phone": clean_phone,
                            "status": p1_status,
                            "friend_name": clean_fname if add_friend else None,
                            "friend_status": p2_status,
                            "session": display_session,
                            "is_new": True
                        }
                        st.rerun()
                except Exception as err:
                    st.error(f"حدث خطأ أثناء إتمام الحجز: {err}")

    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        has_friend = lb.get("friend_name") is not None
        
        # حساب السعر الإجمالي فقط للمقاعد المؤكدة
        confirmed_seats = 0
        if lb["status"] == "confirmed":
            confirmed_seats += 1
        if has_friend and lb["friend_status"] == "confirmed":
            confirmed_seats += 1
            
        total_price = confirmed_seats * BASE_PRICE

        if confirmed_seats > 0:
            if lb.get("is_new", False):
                st.balloons()
                lb["is_new"] = False

            if has_friend:
                if lb["status"] == "confirmed" and lb["friend_status"] == "confirmed":
                    conf_text = f"تم تأكيد حجزك وحجز خويك ({lb['friend_name']}) بنجاح!"
                else:
                    conf_text = f"تم تأكيد حجزك، بينما تم إدراج خويك ({lb['friend_name']}) في قائمة الانتظار لاكتمال المقاعد."
            else:
                conf_text = "تم تأكيد حجزك بنجاح!"

            st.markdown(f"""
            <div class="thankyou-box">
                <div class="thankyou-title">✅ {conf_text} يا كابتن {lb['name']}</div>
                <div class="thankyou-sub">تم حجز المقاعد في <b>{lb['session']}</b>. نلتقي في الملعب!</div>
            </div>
            """, unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={iban_raw}&color=000000&bgcolor=ffffff"

            card_html = f"""
            <div class="alrajhi-card">
                <div class="card-top">
                    <div class="bank-title">🏛️ مصرف الراجحي</div>
                    <div class="price-pill">{total_price} ر.س ({confirmed_seats} مقعد)</div>
                </div>
                <div style="text-align:center;">
                    <div class="qr-container">
                        <img src="{qr_url}" alt="QR" />
                    </div>
                </div>
                <div class="card-owner">فارس ربيع بن عواض العصيمي</div>
                <div style="font-size:0.75em; color:#94a3b8; margin-bottom:2px; text-align:center;">رقم الحساب:</div>
                <div class="copy-badge">{acc_raw}</div>
                <div style="font-size:0.75em; color:#94a3b8; margin-bottom:2px; text-align:center;">رقم الآيبان:</div>
                <div class="copy-badge">{iban_display}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            extra_msg = f" وخويي: {lb['friend_name']}" if (has_friend and lb['friend_status'] == 'confirmed') else ""
            wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {lb['name']}{extra_msg}\nالتمرين: {lb['session']} (كورت 1)\nالمقاعد المؤكدة: {confirmed_seats}\nالمبلغ الإجمالي: {total_price} ر.س\n\nمرفق إشعار التحويل البنكي لحساب كابتن فارس العصيمي."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتثبيت المقاعد</a>', unsafe_allow_html=True)
        else:
            st.info("اكتملت المقاعد الأساسية للتمرين بالكامل. تم تسجيلك (أنت وخويك) في قائمة الاحتياط وسيتم التواصل معكم فور توفر مقعد.")

# --- تبويب القواعد ---
with tab_rules:
    st.markdown("""
    <div style="background:#18181b; border:1px solid #27272a; border-radius:10px; padding:10px; margin:8px 0; font-size:0.85em; color:#e2e8f0; line-height:1.5;">
        <div style="margin-bottom:8px;">⏱️ <b>قبل 4 ساعات:</b> استرجاع كامل أو ترحيل فوري لتمرينك القادم.</div>
        <div style="margin-bottom:8px;">⚠️ <b>أقل من 4 ساعات:</b> يُسترجع المبلغ فور تأكيد لاعب بديل من قائمة الانتظار.</div>
        <div>⚡ <b>تأكيد فوري:</b> أرسل إشعار التحويل خلال 15 دقيقة لضمان تثبيت مقعدك.</div>
    </div>
    """, unsafe_allow_html=True)

# --- تبويب الاعتذار والإلغاء ---
with tab_cancel:
    with st.form("cancel_form", clear_on_submit=True):
        can_phone_raw = st.text_input("رقم الجوال المسجل")
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
# 5. تشكيلة الملعب الحية
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
        slots_html += f'''<div class="slot-box">
            <div class="slot-occupied">🎾 {p["name"]}</div>
            <div class="slot-meta">
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
# 6. لوحة الإدارة المبسطة
# ==========================================
with st.expander("⚙️ لوحة الإدارة", expanded=False):
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
                    c_kpi1.metric("إجمالي الحجوزات", conf_count)
                    c_kpi2.metric("المؤكد دفعهم", f"{paid_count * 65} ر.س")
                    
                    st.markdown("---")
                    if st.button("تصفير تمرين اليوم فقط 🔄", use_container_width=True):
                        supabase.table("bookings").delete().eq("session_day", db_session_key).execute()
                        st.success("تم تصفير تمرين اليوم بنجاح!")
                        st.rerun()
            except Exception as err:
                st.error(f"خطأ: {err}")
        else:
            st.error("رمز الدخول غير صحيح.")
