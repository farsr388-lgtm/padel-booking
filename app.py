import streamlit as st
from supabase import create_client, Client
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة والتصميم المبسط
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
# 2. الثوابت وقاعدة البيانات
# ==========================================
COURT_CAPACITY = 6
BASE_PRICE = 65
WHATSAPP_GROUP_LINK = "https://chat.whatsapp.com/JWihlgJeVIU40RhrzfEwnj?mode=gi_t"

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

# ==========================================
# 3. الدوال المساعدة
# ==========================================
def clean_sa_phone(raw_phone):
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

def to_wa_format(phone_05):
    if phone_05 and phone_05.startswith("05"):
        return "966" + phone_05[1:]
    return phone_05

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
        res = supabase.table("bookings").select("session_day").eq("phone", phone).in_("status", ["confirmed", "archived"]).execute()
        return len(set(d["session_day"] for d in (res.data or [])))
    except Exception:
        return 0

# ==========================================
# 4. واجهة التطبيق
# ==========================================
display_session, db_session_key = get_next_session()
confirmed_players, waitlist_players = get_session_bookings(db_session_key)
total_booked = len(confirmed_players)

st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session} • 6 لاعبين للملعب</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين واحصل على السابع مجاناً</div>", unsafe_allow_html=True)
st.caption(f"⏰ 9:30 م إلى 11:00 م | <b>المؤكدين: {total_booked}/6</b>", unsafe_allow_html=True)

tab_book, tab_rate, tab_cancel = st.tabs(["⚡ حجز مقعد", "⭐ تقييم التمرين", "❌ اعتذار"])

# --- 1. تبويب الحجز والدعوة ---
with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        f_name = st.text_input("الاسم الثلاثي", key="input_name")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx", key="input_phone")
        f_level = st.selectbox("مستوى اللعب", ["متوسط", "متقدم", "مبتدئ"], key="input_level")
        
        st.markdown("---")
        add_friend = st.checkbox("🎾 احجز مقعد إضافي لخويك معك", key="input_add_friend")
        f_friend_name = ""
        f_friend_phone = ""
        f_friend_level = "متوسط"
        
        if add_friend:
            st.info("💡 **سجّل جوال خويك لحفظ نقاطه!**")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                f_friend_name = st.text_input("اسم خويك", key="input_fname")
            with col_f2:
                f_friend_level = st.selectbox("مستوى خويك", ["متوسط", "متقدم", "مبتدئ"], key="input_flevel")
            f_friend_phone = st.text_input("رقم جوال خويك (05xxxxxxxx)", placeholder="05xxxxxxxx", key="input_fphone")

        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button("تأكيد الانضمام 🚀", use_container_width=True)

        if btn_submit:
            if honeypot_val:
                st.error("طلب آلي مرفوض.")
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_sa_phone(f_phone)
            clean_fname = f_friend_name.strip()
            clean_fphone = clean_sa_phone(f_friend_phone)

            if not clean_name or len(clean_name) < 2:
                st.warning("يا كابتن، فضلاً اكتب اسمك بشكل صحيح 🎾")
            elif not clean_phone:
                st.warning("تأكد من رقم جوالك (يبدأ بـ 05 ومكون من 10 أرقام) 📱")
            elif add_friend and (len(clean_fname) < 2 or not clean_fphone):
                st.warning("فضلاً اكتب اسم ورقم جوال خويك الصحيح ✨")
            elif add_friend and clean_fphone == clean_phone:
                st.warning("سجّل رقم جوال خويك الخاص مو نفس رقمك لحفظ نقاطه 🎁")
            else:
                try:
                    existing = supabase.table("bookings").select("id").eq("phone", clean_phone).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                    
                    if existing.data and len(existing.data) > 0:
                        st.info("أنت مسجل مسبقاً في تمرين اليوم يا كابتن! 🌟")
                    else:
                        conf_res = supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "confirmed").execute()
                        cur_conf_count = len(conf_res.data or [])
                        
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

                        p2_status = None
                        if add_friend:
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
                            "friend_phone": clean_fphone if add_friend else None,
                            "friend_status": p2_status,
                            "session": display_session,
                            "is_new": True
                        }
                        st.rerun()
                except Exception as err:
                    st.error(f"حصل خطأ أثناء الحفظ: {err}")

    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        has_friend = lb.get("friend_name") is not None
        
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

            conf_msg = f"تم تأكيد حجزك وحجز خويك ({lb['friend_name']})!" if (has_friend and lb['friend_status'] == 'confirmed') else "تم تأكيد حجزك بنجاح!"

            st.markdown(f"""
            <div class="thankyou-box">
                <div class="thankyou-title">✅ {conf_msg} يا كابتن {lb['name']}</div>
                <div class="thankyou-sub">الموعد في <b>{lb['session']}</b>. نلتقي بالملعب!</div>
            </div>
            """, unsafe_allow_html=True)
            
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=SA9380000222608016013114&color=000000&bgcolor=ffffff"

            st.markdown(f"""
            <div class="alrajhi-card">
                <div class="card-top">
                    <div class="bank-title">🏛️ مصرف الراجحي</div>
                    <div class="price-pill">{total_price} ر.س ({confirmed_seats} مقعد)</div>
                </div>
                <div style="text-align:center;"><div class="qr-container"><img src="{qr_url}" alt="QR" /></div></div>
                <div class="card-owner">فارس ربيع بن عواض العصيمي</div>
                <div style="font-size:0.75em; color:#94a3b8; text-align:center;">رقم الحساب:</div>
                <div class="copy-badge">{acc_raw}</div>
                <div style="font-size:0.75em; color:#94a3b8; text-align:center;">رقم الآيبان:</div>
                <div class="copy-badge">{iban_display}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # زر إشعار التحويل المالي للإدارة
            admin_msg = urllib.parse.quote(
                f"🎾 *تأكيد حجز تمرين بادل 99*\n\n"
                f"👤 *الكابتن:* {lb['name']}\n"
                f"🎟️ *المقاعد:* {confirmed_seats}\n"
                f"💰 *المبلغ:* {total_price} ر.س\n"
                f"📎 مرفق إشعار التحويل."
            )
            st.markdown(f'<a href="https://wa.me/966566261868?text={admin_msg}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل للإدارة</a>', unsafe_allow_html=True)

            # زر إرسال الرابط وحفظ النقاط إلى الخوي
            if has_friend and lb.get("friend_phone"):
                wa_friend_phone = to_wa_format(lb["friend_phone"])
                friend_invite_text = urllib.parse.quote(
                    "هلا يا كابتن! 🎾\n\n"
                    "شكراً لك، تم تسجيلك معنا وسجلت رقمك عشان ما تضيع عليك نقاط التمرين.\n"
                    "هذا رابط قروب الواتساب الخاص بالتمارين، ادخل منه عشان تحفظ نقاطك ونلعب سوا:\n"
                    f"{WHATSAPP_GROUP_LINK}\n\n"
                    "الله يحييك وتنورنا في بادل 99 🔥"
                )
                friend_wa_url = f"https://wa.me/{wa_friend_phone}?text={friend_invite_text}"
                st.markdown(f'<a href="{friend_wa_url}" target="_blank" class="wa-btn" style="background:#0284c7; margin-top:8px;">🎁 إرسال رابط القروب وتثبيت النقاط لخويك</a>', unsafe_allow_html=True)

        else:
            st.info("الملعب مكتمل! تم تسجيلكم في قائمة الانتظار، وعند توفر مقعد سنبلغكم فوراً 🎾")

# --- 2. تبويب التقييم الصريح (5 نجوم فقط) ---
with tab_rate:
    st.markdown("### كيف كان تمرين اليوم؟ 🎾")
    stars_rating = st.feedback("stars")

    if st.button("إرسال التقييم ⭐", use_container_width=True):
        if stars_rating is None:
            st.warning("فضلاً حدد التقييم بالنجوم أولاً يا كابتن")
        else:
            try:
                score = stars_rating + 1
                supabase.table("session_feedback").insert({
                    "rating_stars": score,
                    "session_day": db_session_key
                }).execute()
                st.success(f"وصل تقييمك ({score}/5)، يعطيك العافية ونشوفك التمرين الجاي! 🤍")
            except Exception as err:
                st.error(f"حدث خطأ أثناء حفظ التقييم: {err}")

# --- 3. تبويب الاعتذار والإلغاء ---
with tab_cancel:
    with st.form("cancel_form", clear_on_submit=True):
        can_phone_raw = st.text_input("رقم الجوال المسجل")
        btn_cancel_sub = st.form_submit_button("إلغاء المقعد وإتاحته للبديل", use_container_width=True)

        if btn_cancel_sub:
            clean_cp = clean_sa_phone(can_phone_raw)
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
                        
                        st.success(f"خيرها بغيرها يا كابتن {player_name}! 🤍 مقعدك صار متاح للبديل.")
                        if promoted_name:
                            st.info(f"🔥 الكابتن **{promoted_name}** تأكد مقعدك بالملعب تلقائياً!")
                        
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
    if i < len(confirmed_players):
        p = confirmed_players[i]
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

st.markdown(f'<div class="padel-court"><div class="court-title">🏟️ كورت 1 ({len(confirmed_players)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>', unsafe_allow_html=True)

if waitlist_players:
    st.caption("📋 **قائمة الانتظار:** " + " • ".join([f"#{idx+1} {w['name']}" for idx, w in enumerate(waitlist_players)]))

# ==========================================
# 6. لوحة الإدارة المبسطة
# ==========================================
with st.expander("⚙️ لوحة الإدارة والتحكم", expanded=False):
    pin_input = st.text_input("رمز الإدارة المشفر:", type="password")
    
    if pin_input:
        ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        clean_pin = str(pin_input).translate(ar_digits).strip()
        admin_pass = st.secrets.get("ADMIN_SECRET", "Padel99#Master@2026")
        
        if hmac.compare_digest(clean_pin, admin_pass):
            st.success("أهلاً يا كابتن 👑")
            try:
                res_today = supabase.table("bookings").select("*").eq("session_day", db_session_key).order("id").execute()
                today_records = res_today.data or []
                conf_list = [r for r in today_records if r["status"] == "confirmed"]
                
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("المؤكدين", f"{len(conf_list)}/{COURT_CAPACITY}")
                kpi2.metric("تم سدادهم", f"{len([r for r in today_records if r.get('payment_status') == 'paid'])}")
                kpi3.metric("الدخل المتوقع", f"{len(conf_list) * BASE_PRICE} ر.س")
                
                # قائمة النسخ للقروب
                st.markdown("---")
                list_lines = [
                    f"🎾 *تشكيلة تمرين {display_session}*",
                    "⏰ الوقت: 9:30 م إلى 11:00 م | كورت 1",
                    "━━━━━━━━━━━━━━"
                ]
                for idx in range(COURT_CAPACITY):
                    if idx < len(conf_list):
                        cp = conf_list[idx]
                        p_mark = "✅" if cp.get("payment_status") == "paid" else "⏳"
                        list_lines.append(f"{idx+1}. {cp['name']} {p_mark}")
                    else:
                        list_lines.append(f"{idx+1}. مقعد شاغر ✨")
                        
                broadcast_txt = "\n".join(list_lines)
                st.text_area("نسخ التشكيلة:", value=broadcast_txt, height=150)
                st.markdown(f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(broadcast_txt)}" target="_blank" class="wa-btn" style="background:#128C7E;">📤 إرسال التشكيلة للقروب</a>', unsafe_allow_html=True)
                
                # إدارة الدفع
                st.markdown("---")
                for rec in today_records:
                    c_info, c_btn = st.columns([3, 1])
                    c_info.write(f"**{rec['name']}** ({rec['phone']}) - {'✅ مؤكد' if rec['status'] == 'confirmed' else '⏳ احتياط'}")
                    with c_btn:
                        if rec.get("payment_status") != "paid":
                            if st.button("تأكيد 💳", key=f"pay_{rec['id']}", use_container_width=True):
                                supabase.table("bookings").update({"payment_status": "paid"}).eq("id", rec["id"]).execute()
                                st.rerun()
                        else:
                            if st.button("إلغاء ↩️", key=f"unpay_{rec['id']}", use_container_width=True):
                                supabase.table("bookings").update({"payment_status": "pending"}).eq("id", rec["id"]).execute()
                                st.rerun()
                                
            except Exception as err:
                st.error(f"خطأ: {err}")
        else:
            st.error("رمز الدخول غير صحيح.")
