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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الثوابت وقاعدة البيانات
# ==========================================
COURT_CAPACITY = 6
BASE_PRICE = 65
WHATSAPP_GROUP_LINK = "https://chat.whatsapp.com/JWihlgJeVIU40RhrzfEwnj?mode=gi_t"
APP_URL = "https://padel99.streamlit.app"  # استبدله برابط موقعك الفعلي إن وجد

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
# 3. الدوال وتدوير الحجز التلقائي
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

def get_next_session():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    
    # جدول التمارين: الأحد (6), الثلاثاء (1), الخميس (3)
    allowed_days = [6, 1, 3]
    
    target = now
    # تدوير مباشر للتمرين القادم بمجرد وصول الساعة 11:00 م
    if now.weekday() in allowed_days and (now.hour > 23 or (now.hour == 23 and now.minute >= 0)):
        target = now + timedelta(days=1)
        
    while target.weekday() not in allowed_days:
        target += timedelta(days=1)
        
    names_ar = {6: "الأحد", 1: "الثلاثاء", 3: "الخميس"}
    d_ar = names_ar[target.weekday()]
    label_ar = f"{d_ar} ({target.strftime('%d/%m')})"
    db_key = f"{d_ar} {target.strftime('%Y-%m-%d')}"
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
# 4. بناء الواجهة
# ==========================================
display_session, db_session_key = get_next_session()
confirmed_players, waitlist_players = get_session_bookings(db_session_key)
total_booked = len(confirmed_players)

st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session} • 6 لاعبين للملعب</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين واحصل على السابع مجاناً</div>", unsafe_allow_html=True)
st.caption(f"⏰ 9:30 م إلى 11:00 م | <b>المؤكدين: {total_booked}/6</b>", unsafe_allow_html=True)

tab_book, tab_cancel = st.tabs(["⚡ حجز مقعد", "❌ اعتذار"])

# --- تبويب الحجز الفردي والدعوة والتقييم ---
with tab_book:
    with st.form("booking_form", clear_on_submit=False):
        f_name = st.text_input("الاسم", key="input_name")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx", key="input_phone")
        f_level = st.selectbox("مستوى اللعب", ["متوسط", "متقدم", "مبتدئ"], key="input_level")
        
        btn_submit = st.form_submit_button("تأكيد الانضمام 🚀", use_container_width=True)

        if btn_submit:
            clean_name = f_name.strip()
            clean_phone = clean_sa_phone(f_phone)

            if not clean_name or len(clean_name) < 2:
                st.warning("فضلاً اكتب الاسم بشكل صحيح 🎾")
            elif not clean_phone:
                st.warning("رقم الجوال غير صحيح (تأكد يبدأ بـ 05) 📱")
            else:
                try:
                    existing = supabase.table("bookings").select("id").eq("phone", clean_phone).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                    
                    if existing.data and len(existing.data) > 0:
                        st.info("أنت مسجل مسبقاً في تمرين هذا اليوم يا كابتن! 🌟")
                    else:
                        conf_res = supabase.table("bookings").select("id").eq("session_day", db_session_key).eq("status", "confirmed").execute()
                        cur_conf = len(conf_res.data or [])
                        
                        p1_status = "confirmed" if cur_conf < COURT_CAPACITY else "waitlist"
                        supabase.table("bookings").insert({
                            "name": clean_name,
                            "phone": clean_phone,
                            "session_day": db_session_key,
                            "court": 1,
                            "level": f_level,
                            "status": p1_status,
                            "payment_status": "pending"
                        }).execute()

                        st.session_state["last_booking"] = {
                            "name": clean_name,
                            "phone": clean_phone,
                            "status": p1_status,
                            "session": display_session,
                            "is_new": True,
                            "rated": False
                        }
                        st.rerun()
                except Exception as err:
                    st.error(f"خطأ أثناء الحفظ: {err}")

    # بعد إتمام الحجز
    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        
        if lb["status"] == "confirmed":
            if lb.get("is_new", False):
                st.balloons()
                lb["is_new"] = False

            st.markdown(f"""
            <div class="thankyou-box">
                <div class="thankyou-title">✅ تم تأكيد مقعدك يا كابتن {lb['name']}</div>
                <div class="thankyou-sub">الموعد في <b>{lb['session']}</b>. نلتقي بالملعب!</div>
            </div>
            """, unsafe_allow_html=True)
            
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"

            st.markdown(f"""
            <div class="alrajhi-card">
                <div class="card-top">
                    <div class="bank-title">🏛️ مصرف الراجحي</div>
                    <div class="price-pill">{BASE_PRICE} ر.س (مقعد واحد)</div>
                </div>
                <div class="card-owner">فارس ربيع بن عواض العصيمي</div>
                <div style="font-size:0.75em; color:#94a3b8; text-align:center;">رقم الحساب:</div>
                <div class="copy-badge">{acc_raw}</div>
                <div style="font-size:0.75em; color:#94a3b8; text-align:center;">رقم الآيبان:</div>
                <div class="copy-badge">{iban_display}</div>
            </div>
            """, unsafe_allow_html=True)
            
            admin_msg = urllib.parse.quote(f"🎾 تأكيد حجز تمرين بادل 99\nالكابتن: {lb['name']}\nالمبلغ: {BASE_PRICE} ر.س\nمرفق الإشعار.")
            st.markdown(f'<a href="https://wa.me/966566261868?text={admin_msg}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل لتثبيت المقعد</a>', unsafe_allow_html=True)

            # زر دعوة الخوي ليسجل بنفسه
            st.markdown("---")
            st.markdown("#### 🎾 تبي خويك يسجل مقعده بنفسه؟")
            st.caption("أرسل له الدعوة عبر واتساب عشان يدخل ويسجل مقعده وتتحفظ نقاطه في القروب")
            
            invite_text = urllib.parse.quote(
                f"هلا يا كابتن! 🎾\n\n"
                f"أنا حجزت مقعدي في تمرين بادل 99، احجز مقعدك بنفسك من هنا:\n"
                f"{APP_URL}\n\n"
                f"وادخل قروب الواتساب عشان تحفظ نقاط تسجيلك:\n"
                f"{WHATSAPP_GROUP_LINK}\n\n"
                f"جهّز مضربك ونلتقي بالملعب! 🔥"
            )
            wa_share_url = f"https://api.whatsapp.com/send?text={invite_text}"
            st.markdown(f'<a href="{wa_share_url}" target="_blank" class="wa-btn" style="background:#0284c7;">📲 إرسال رابط الحجز والقروب لخويك</a>', unsafe_allow_html=True)

            # التقييم الصريح بالـ 5 نجوم فقط
            st.markdown("---")
            st.write("**⭐ تقييمك لتجربة الحجز والتنظيم:**")
            if not lb.get("rated", False):
                stars = st.feedback("stars", key="direct_feedback_stars")
                if stars is not None:
                    try:
                        supabase.table("session_feedback").insert({
                            "phone": lb["phone"],
                            "rating_stars": stars + 1,
                            "session_day": db_session_key
                        }).execute()
                        lb["rated"] = True
                        st.success("تم تسجيل تقييمك، شكراً لك! 🤍")
                    except Exception:
                        pass
            else:
                st.info("تم استلام تقييمك بنجاح 🌟")

        else:
            st.info("اكتملت المقاعد الأساسية! تم تسجيلك في قائمة الانتظار، وسيتم إبلاغك فور توفر مقعد 🎾")

# --- تبويب الاعتذار ---
with tab_cancel:
    with st.form("cancel_form", clear_on_submit=True):
        can_phone_raw = st.text_input("رقم الجوال المسجل")
        btn_cancel_sub = st.form_submit_button("إلغاء المقعد وإتاحته للبديل", use_container_width=True)

        if btn_cancel_sub:
            clean_cp = clean_sa_phone(can_phone_raw)
            if not clean_cp:
                st.error("أدخل رقم جوال صحيح.")
            else:
                try:
                    rec = supabase.table("bookings").select("*").eq("phone", clean_cp).eq("session_day", db_session_key).in_("status", ["confirmed", "waitlist"]).execute()
                    if rec.data and len(rec.data) > 0:
                        target = rec.data[0]
                        was_confirmed = target["status"] == "confirmed"
                        p_name = target["name"]
                        
                        supabase.table("bookings").update({"status": "cancelled"}).eq("id", target["id"]).execute()
                        
                        promoted_name = None
                        if was_confirmed:
                            w_player = supabase.table("bookings").select("*").eq("session_day", db_session_key).eq("status", "waitlist").order("id").limit(1).execute()
                            if w_player.data and len(w_player.data) > 0:
                                p_id = w_player.data[0]["id"]
                                promoted_name = w_player.data[0]["name"]
                                supabase.table("bookings").update({"status": "confirmed"}).eq("id", p_id).execute()
                        
                        st.success(f"تم إلغاء حجزك يا كابتن {p_name}.")
                        if promoted_name:
                            st.info(f"🔥 الكابتن **{promoted_name}** تأكد مقعدك بالملعب تلقائياً!")
                        
                        if "last_booking" in st.session_state:
                            del st.session_state["last_booking"]
                        st.rerun()
                    else:
                        st.error("لا يوجد حجز مسجل بهذا الرقم لتمرين اليوم.")
                except Exception as err:
                    st.error(f"حدث خطأ: {err}")

# ==========================================
# 5. تشكيلة الملعب الحية
# ==========================================
st.markdown("---")
slots_html = ""
for i in range(COURT_CAPACITY):
    if i < len(confirmed_players):
        p = confirmed_players[i]
        points = get_loyalty_score(p["phone"]) % 7
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
# 6. لوحة الإدارة
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
                kpi2.metric("المسددين", f"{len([r for r in today_records if r.get('payment_status') == 'paid'])}")
                kpi3.metric("الدخل المتوقع", f"{len(conf_list) * BASE_PRICE} ر.س")
                
                # قائمة القروب
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
                st.text_area("نسخ التشكيلة:", value=broadcast_txt, height=130)
                st.markdown(f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(broadcast_txt)}" target="_blank" class="wa-btn" style="background:#128C7E;">📤 إرسال التشكيلة للقروب</a>', unsafe_allow_html=True)
                
                # إدارة الدفع اليدوي
                st.markdown("---")
                for rec in today_records:
                    c_info, c_btn = st.columns([3, 1])
                    c_info.write(f"**{rec['name']}** ({rec['phone']})")
                    with c_btn:
                        if rec.get("payment_status") != "paid":
                            if st.button("تأكيد 💳", key=f"pay_{rec['id']}", use_container_width=True):
                                supabase.table("bookings").update({"payment_status": "paid"}).eq("id", rec["id"]).execute()
                                st.rerun()
                        else:
                            if st.button("إلغاء ↩️", key=f"unpay_{rec['id']}", use_container_width=True):
                                supabase.table("bookings").update({"payment_status": "pending"}).eq("id", rec["id"]).execute()
                                st.rerun()
                                
                # تدوير وأرشفة يدوية
                st.markdown("---")
                if st.button("أرشفة تمرين اليوم فوراً وفتح تمرين جديد 🔄", use_container_width=True):
                    supabase.table("bookings").update({"status": "archived"}).eq("session_day", db_session_key).execute()
                    st.success("تم تدوير الحجز للتمرين القادم بنجاح!")
                    st.rerun()

            except Exception as err:
                st.error(f"خطأ: {err}")
        else:
            st.error("رمز الدخول غير صحيح.")
