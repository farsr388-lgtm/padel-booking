import streamlit as st
from supabase import create_client, Client
import re
import urllib.parse
from datetime import datetime, timezone, timedelta

# 1. إعداد الصفحة
st.set_page_config(
    page_title="بادل 99 | Padel 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. الثوابت وقاعدة البيانات
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
    st.error("تعذر الاتصال بقاعدة البيانات.")
    st.stop()

# 3. الدوال المساعدة
def clean_sa_phone(raw):
    if not raw:
        return None
    p = str(raw).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")).strip()
    p = re.sub(r'[\s\-\(\)\+]', '', p)
    if p.startswith("966"):
        p = "0" + p[3:]
    elif p.startswith("5"):
        p = "0" + p
    return p if re.match(r"^05[0-9]{8}$", p) else None

def to_wa(p):
    return "966" + p[1:] if p and p.startswith("05") else p

def get_session():
    now = datetime.now(timezone(timedelta(hours=3)))
    allowed = [6, 1, 3]  # الأحد، الثلاثاء، الخميس
    target = now
    if now.weekday() in allowed and now.hour >= 23:
        target = now + timedelta(days=1)
    while target.weekday() not in allowed:
        target += timedelta(days=1)
    d_ar = {6: "الأحد", 1: "الثلاثاء", 3: "الخميس"}[target.weekday()]
    return f"{d_ar} ({target.strftime('%d/%m')})", f"{d_ar} {target.strftime('%Y-%m-%d')}"

session_label, session_key = get_session()

# جلب الحجوزات الحالية
try:
    res = supabase.table("bookings").select("name, phone, status").eq("session_day", session_key).in_("status", ["confirmed", "waitlist"]).order("id").execute()
    data = res.data or []
    confirmed = [d for d in data if d["status"] == "confirmed"][:COURT_CAPACITY]
except Exception:
    confirmed = []

# 4. الواجهة الرئيسية
st.title("🎾 بادل 99")
st.caption(f"تمرين **{session_label}** | 9:30 م - 11:00 م")
st.info(f"المقاعد المكتملة: **{len(confirmed)} / {COURT_CAPACITY}**")

# نموذج الحجز المباشر
with st.container(border=True):
    st.subheader("⚡ حجز مقعد سريع")
    u_name = st.text_input("اسمك الكريم", placeholder="مثال: فهد محمد")
    u_phone = st.text_input("رقم جوالك", placeholder="05xxxxxxxx")
    
    with st.expander("➕ تبي تحجز لخويك معك؟ (اختياري)"):
        f_name = st.text_input("اسم خويك", placeholder="اسم الصديق")
        f_phone = st.text_input("رقم جوال خويك", placeholder="05xxxxxxxx")

    btn_book = st.button("تأكيد وحجز المقعد 🚀", use_container_width=True, type="primary")

    if btn_book:
        c_name = u_name.strip()
        c_phone = clean_sa_phone(u_phone)
        c_fname = f_name.strip()
        c_fphone = clean_sa_phone(f_phone)
        has_friend = bool(c_fname and c_fphone)

        if not c_name or not c_phone:
            st.error("فضلاً اكتب اسمك ورقم جوالك بشكل صحيح (05xxxxxxxx).")
        elif f_name and not c_fphone:
            st.error("رقم جوال خويك غير صحيح.")
        else:
            try:
                chk = supabase.table("bookings").select("id").eq("phone", c_phone).eq("session_day", session_key).in_("status", ["confirmed", "waitlist"]).execute()
                if chk.data:
                    st.info("أنت مسجل معنا مسبقاً في تمرين اليوم! 🌟")
                else:
                    cur_count = len(confirmed)
                    s1 = "confirmed" if cur_count < COURT_CAPACITY else "waitlist"
                    supabase.table("bookings").insert({
                        "name": c_name, "phone": c_phone, "session_day": session_key,
                        "court": 1, "level": "متوسط", "status": s1, "payment_status": "pending"
                    }).execute()
                    
                    s2 = None
                    if has_friend:
                        cur_count += (1 if s1 == "confirmed" else 0)
                        s2 = "confirmed" if cur_count < COURT_CAPACITY else "waitlist"
                        supabase.table("bookings").insert({
                            "name": c_fname, "phone": c_fphone, "session_day": session_key,
                            "court": 1, "level": "متوسط", "status": s2, "payment_status": "pending"
                        }).execute()

                    st.session_state["last_booking"] = {
                        "name": c_name, "phone": c_phone, "status": s1,
                        "fname": c_fname if has_friend else None,
                        "fphone": c_fphone if has_friend else None,
                        "fstatus": s2, "rated": False
                    }
                    st.rerun()
            except Exception as err:
                st.error(f"حدث خطأ أثناء الحفظ: {err}")

# 5. نتيجة الحجز والدفع
if "last_booking" in st.session_state:
    b = st.session_state["last_booking"]
    has_f = bool(b.get("fname"))
    seats = (1 if b["status"] == "confirmed" else 0) + (1 if has_f and b["fstatus"] == "confirmed" else 0)
    total_price = seats * BASE_PRICE

    if seats > 0:
        st.balloons()
        st.success(f"✅ تم تأكيد حجزك بنجاح يا كابتن {b['name']}!")
        
        with st.container(border=True):
            st.markdown(f"**المبلغ المطلوب:** `{total_price} ر.س` ({seats} مقعد)")
            st.markdown("**مصرف الراجحي:** فارس ربيع بن عواض العصيمي")
            st.code("SA9380000222608016013114", language="text")
            st.caption("اضغط لنسخ الآيبان مباشرة")

        # رابط إشعار التحويل للإدارة
        msg_admin = urllib.parse.quote(f"🎾 تأكيد حجز بادل 99\nالاسم: {b['name']}\nالمقاعد: {seats}\nالمبلغ: {total_price} ر.س\nمرفق الإشعار.")
        st.link_button("📲 إرسال إشعار التحويل لتثبيت المقعد", f"https://wa.me/966566261868?text={msg_admin}", use_container_width=True)

        # رابط دعوة الخوي
        if has_f and b.get("fphone"):
            msg_friend = urllib.parse.quote(
                f"هلا يا كابتن {b['fname']}! 🎾\n"
                f"حجزت مقعدك وسجلتك معي في تمرين بادل 99.\n"
                f"انضم معنا للقروب من هذا الرابط عشان تحفظ نقاطك وتأكد حضورك:\n"
                f"{WHATSAPP_GROUP_LINK}\n\n"
                f"تنورنا ونلتقي بالتمرين! 🔥"
            )
            st.link_button("💬 أرسل لخويك: انضم للقروب واحفظ نقاطك", f"https://wa.me/{to_wa(b['fphone'])}?text={msg_friend}", use_container_width=True)

        # التقييم السريع بالنجوم
        st.write("---")
        st.write("⭐ **تقييمك لتجربة الحجز والتنظيم:**")
        if not b.get("rated", False):
            star = st.feedback("stars", key="quick_star_direct")
            if star is not None:
                try:
                    supabase.table("session_feedback").insert({
                        "phone": b["phone"],
                        "rating_stars": star + 1,
                        "session_day": session_key
                    }).execute()
                    b["rated"] = True
                    st.toast("شكراً على تقييمك! 🤍")
                except Exception:
                    pass
    else:
        st.warning("اكتملت المقاعد الأساسية! تم إدراجك في قائمة الانتظار.")

# 6. تشكيلة الملعب الحالية
st.write("---")
st.subheader("🏟️ تشكيلة تمرين اليوم")
cols = st.columns(2)
for i in range(COURT_CAPACITY):
    col = cols[i % 2]
    if i < len(confirmed):
        col.success(f"🎾 {confirmed[i]['name']}")
    else:
        col.info("مقعد شاغر ✨")

# 7. إلغاء الحجز
with st.expander("❌ تبي تعتذر عن التمرين؟"):
    c_phone_input = st.text_input("رقم جوالك المسجل للإلغاء")
    if st.button("تأكيد الاعتذار", use_container_width=True):
        clean_c = clean_sa_phone(c_phone_input)
        if clean_c:
            supabase.table("bookings").update({"status": "cancelled"}).eq("phone", clean_c).eq("session_day", session_key).execute()
            st.success("تم إلغاء الحجز وإتاحة المقعد للبديل.")
            st.rerun()
