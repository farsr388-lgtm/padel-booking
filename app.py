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

# نموذج الحجز برقم الجوال فقط
with st.container(border=True):
    st.subheader("⚡ حجز مقعد سريع")
    u_phone = st.text_input("رقم جوالك", placeholder="05xxxxxxxx")
    
    with st.expander("➕ تبي تحجز لخويك معك؟ (اختياري)"):
        f_phone = st.text_input("رقم جوال خويك", placeholder="05xxxxxxxx")

    btn_book = st.button("تأكيد وحجز المقعد 🚀", use_container_width=True, type="primary")

    if btn_book:
        c_phone = clean_sa_phone(u_phone)
        c_fphone = clean_sa_phone(f_phone)
        has_friend = bool(c_fphone)

        if not c_phone:
            st.error("فضلاً أدخل رقم جوال صحيح (يبدأ بـ 05).")
        elif f_phone and not c_fphone:
            st.error("رقم جوال خويك غير صحيح.")
        elif has_friend and c_phone == c_fphone:
            st.error("سجّل رقم جوال مختلف لخويك.")
        else:
            try:
                # التحقق من عدم التسجيل المسبق في نفس التمرين
                chk = supabase.table("bookings").select("id").eq("phone", c_phone).eq("session_day", session_key).in_("status", ["confirmed", "waitlist"]).execute()
                if chk.data:
                    st.info("أنت مسجل معنا مسبقاً في تمرين اليوم! 🌟")
                else:
                    # استرجاع الاسم إن وُجد من سجل قديم أو اعتماده كـ "لاعب 05xxx"
                    prev_p1 = supabase.table("bookings").select("name").eq("phone", c_phone).neq("name", "").limit(1).execute()
                    p1_name = prev_p1.data[0]["name"] if prev_p1.data and prev_p1.data[0].get("name") else f"لاعب {c_phone[-4:]}"

                    cur_count = len(confirmed)
                    s1 = "confirmed" if cur_count < COURT_CAPACITY else "waitlist"
                    supabase.table("bookings").insert({
                        "name": p1_name, "phone": c_phone, "session_day": session_key,
                        "court": 1, "level": "متوسط", "status": s1, "payment_status": "pending"
                    }).execute()
                    
                    s2 = None
                    p2_name = None
                    if has_friend:
                        prev_p2 = supabase.table("bookings").select("name").eq("phone", c_fphone).neq("name", "").limit(1).execute()
                        p2_name = prev_p2.data[0]["name"] if prev_p2.data and prev_p2.data[0].get("name") else f"خوي {c_fphone[-4:]}"

                        cur_count += (1 if s1 == "confirmed" else 0)
                        s2 = "confirmed" if cur_count < COURT_CAPACITY else "waitlist"
                        supabase.table("bookings").insert({
                            "name": p2_name, "phone": c_fphone, "session_day": session_key,
                            "court": 1, "level": "متوسط", "status": s2, "payment_status": "pending"
                        }).execute()

                    st.session_state["last_booking"] = {
                        "name": p1_name, "phone": c_phone, "status": s1,
                        "fname": p2_name, "fphone": c_fphone, "fstatus": s2,
                        "rated": False
                    }
                    st.rerun()
            except Exception as err:
                st.error(f"حدث خطأ أثناء الحفظ: {err}")

# 5. نتيجة الحجز والدفع
if "last_booking" in st.session_state:
    b = st.session_state["last_booking"]
    has_f = bool(b.get("fphone"))
    seats = (1 if b["status"] == "confirmed" else 0) + (1 if has_f and b["fstatus"] == "confirmed" else 0)
    total_price = seats * BASE_PRICE

    if seats > 0:
        st.balloons()
        st.success(f"✅ تم تأكيد الحجز بنجاح يا كابتن ({b['phone']})!")
        
        with st.container(border=True):
            st.markdown(f"**المبلغ المطلوب:** `{total_price} ر.س` ({seats} مقعد)")
            st.markdown("**مصرف الراجحي:** فارس ربيع بن عواض العصيمي")
            st.code("SA9380000222608016013114", language="text")
            st.caption("اضغط لنسخ الآيبان مباشرة")

        # إشعار التحويل للإدارة
        msg_admin = urllib.parse.quote(f"🎾 تأكيد حجز بادل 99\nالجوال: {b['phone']}\nالمقاعد: {seats}\nالمبلغ: {total_price} ر.س\nمرفق الإشعار.")
        st.link_button("📲 إرسال إشعار التحويل لتثبيت المقعد", f"https://wa.me/966566261868?text={msg_admin}", use_container_width=True)

        # رابط دعوة الخوي
        if has_f and b.get("fphone"):
            msg_friend = urllib.parse.quote(
                f"هلا يا كابتن! 🎾\n"
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
        display_label = confirmed[i]["name"] if confirmed[i].get("name") else confirmed[i]["phone"]
        col.success(f"🎾 {display_label}")
    else:
        col.info("مقعد شاغر ✨")

# 7. إلغاء الحجز
with st.expander("❌ تبي تعتذر عن التمرين؟"):
    c_phone_input = st.text_input("رقم جوالك للإلغاء")
    if st.button("تأكيد الاعتذار", use_container_width=True):
        clean_c = clean_sa_phone(c_phone_input)
        if clean_c:
            supabase.table("bookings").update({"status": "cancelled"}).eq("phone", clean_c).eq("session_day", session_key).execute()
            st.success("تم إلغاء الحجز وإتاحة المقعد للبديل.")
            st.rerun()
