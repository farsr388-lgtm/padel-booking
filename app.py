from datetime import datetime, time, timedelta, timezone
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعدادات السرعة القصوى وتوقيت جدة (تتحمل 470 نزيلاً بصفر ثقل)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
now_ksa = datetime.now(KSA_TZ)
now_time_str = now_ksa.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")

st.set_page_config(
    page_title="Housing 3 | Maintenance",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 2. تصميم منطقة إصبع الإبهام (One-Thumb Zone) + لون قرمزي هادئ ومريح
# ==============================================================================
st.markdown(
    """
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container {
    max-width: 400px !important;
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
    margin: 0 auto !important;
}
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
    background-color: #0b0f19 !important;
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Cairo", sans-serif;
}
/* أزرار مصممة تحت إصبع الإبهام مباشرة بدون تشتت */
div.stButton > button {
    height: 60px !important;
    font-size: 1.04em !important;
    font-weight: 900 !important;
    border-radius: 14px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(16, 185, 129, 0.5) !important;
}
div.stButton > button:active, div.stButton > button:hover {
    background: #10b981 !important;
    color: #022c22 !important;
}
/* إبقاء زر الإغلاق السريع بجانب اسم الغرفة في نفس السطر للمشرف */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
}
.box {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 12px;
    margin-bottom: 8px;
}
.sla-banner {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 12px;
    padding: 9px;
    text-align: center;
    margin-bottom: 10px;
}
.crimson-box {
    background: rgba(190, 18, 60, 0.14);
    border: 1px solid rgba(244, 63, 94, 0.4);
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 8px;
    color: #fda4af;
}
.green { color: #6ee7b7; font-weight: 800; }
.crimson { color: #fda4af; font-weight: 800; }
.wa-btn {
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 14px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 1.05em;
    text-decoration: none !important;
    margin-top: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. قاعدة البيانات مصفرة ونظيفة تماماً للبدء من الآن (Zero Old Data)
# ==============================================================================
@st.cache_resource
def get_shared_db():
    return {
        "cleaning_status": "تشيك كامل 100% ✓",
        "repairs": [],
        "violations": [],
        "meals": [],
    }


db = get_shared_db()

LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_WA = "966566261868"
ADMIN_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()


def format_room_only(raw_txt: str) -> str:
    clean = raw_txt.strip()
    if clean.isdigit():
        return f"غرفة {clean}"
    return clean or "عام"


def register_ticket(raw_room: str, issue_label: str, photo_data=None):
    """إدارة المخاطر: منع تكرار نفس العطل لنفس الغرفة لحماية السيرفر."""
    loc_clean = format_room_only(raw_room)
    t_now = datetime.now(KSA_TZ).strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")

    for r in db["repairs"]:
        if r["loc"] == loc_clean and r["item"] == issue_label and r["status"] == "مفتوح":
            r["pings"] = r.get("pings", 1) + 1
            if photo_data and not r.get("photo"):
                r["photo"] = photo_data
            st.session_state["done_ticket"] = {
                "loc": r["loc"],
                "item": r["item"],
                "time": r["time"],
                "has_photo": bool(r.get("photo")),
                "is_duplicate": True,
            }
            return

    db["repairs"].append({
        "loc": loc_clean,
        "item": issue_label,
        "time": t_now,
        "status": "مفتوح",
        "pings": 1,
        "photo": photo_data,
    })
    if len(db["repairs"]) > 150:
        db["repairs"] = db["repairs"][-150:]

    st.session_state["done_ticket"] = {
        "loc": loc_clean,
        "item": issue_label,
        "time": t_now,
        "has_photo": bool(photo_data),
        "is_duplicate": False,
    }


# ==============================================================================
# 4. واجهة العمال (بإصبع الإبهام الواحد تحت بعضها | English + Urdu فقط)
# ==============================================================================
st.markdown(
    """
    <div class="box" style="text-align:center;">
        <b style="font-size:1.1em;">🛠️ Maintenance | مرمت رپورٹ</b><br>
        <small style="color:#94a3b8;">Enter Room No & Tap Button • کمرہ نمبر لکھیں اور بٹن دبائیں</small>
    </div>
    <div class="sla-banner">
        <b class="green">⏱️ Repair within 24 Hours | 24 گھنٹے میں مرمت</b><br>
        <small style="color:#cbd5e1;">
        Management is committed to fixing your issue ASAP<br>
        سکن انتظامیہ آپ کا مسئلہ جلد از جلد حل کرنے کے لیے کوشاں ہے
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)

if "done_ticket" in st.session_state:
    tk = st.session_state["done_ticket"]
    photo_note = "\n📷 مرفق صورة" if tk.get("has_photo") else ""
    wa_worker = f"*{LOCATION_TAG}*\n{tk['loc']} — {tk['item']} ({tk['time']}){photo_note}"

    if tk.get("is_duplicate"):
        st.markdown(
            f"""
            <div class="crimson-box" style="text-align:center; padding:18px;">
                <div style="font-size:2.2em;">⏳</div>
                <h3 class="crimson" style="margin:4px 0;">Already Under Progress</h3>
                <b style="color:#ffffff;">یہ شکایت پہلے سے درج ہے اور کارروائی جاری ہے</b><br>
                <p style="color:#e2e8f0; font-size:0.9em; margin-top:8px;">
                    📍 <b>{tk['loc']}</b> ({tk['item']}) — ⏰ <b>{tk['time']}</b><br>
                    Will be fixed within 24h • 24 گھنٹے سے پہلے مکمل ہو جائے گی
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="box" style="border:1.5px solid #10b981; text-align:center; padding:18px;">
                <div style="font-size:2.2em;">✅</div>
                <h3 class="green" style="margin:4px 0;">Request Received</h3>
                <b style="color:#ffffff;">شکایت درج کر لی گئی ہے</b><br>
                <p style="color:#cbd5e1; font-size:0.9em; margin-top:8px;">
                    📍 <b>{tk['loc']}</b> ({tk['item']}) — ⏰ <b>{tk['time']}</b><br>
                    Repair within <b>24 Hours</b> • 24 گھنٹے کے اندر مرمت
                </p>
            </div>
            <a href="https://wa.me/{SUPERVISOR_WA}?text={urllib.parse.quote(wa_worker)}" target="_blank" class="wa-btn">
                📲 Send WhatsApp | واٹس ایپ بھیجیں
            </a>
            """,
            unsafe_allow_html=True,
        )

    if st.button("🔄 Back / واپس جائیں"):
        del st.session_state["done_ticket"]
        st.rerun()
else:
    room_in = st.text_input(
        "🔢 Room No / کمرہ نمبر:",
        placeholder="e.g. 213",
    )

    cam_file = st.file_uploader(
        "📷 Photo (Optional) / تصویر (اختیاری):",
        type=["jpg", "jpeg", "png"],
    )
    cam_bytes = cam_file.getvalue() if cam_file else None

    # مرتبة تحت بعضها لتكون قريبة جداً من إصبع الإبهام الواحد
    if st.button("🔌 Electric / Socket | بجلی / ساکٹ"):
        if not room_in.strip():
            st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
        else:
            register_ticket(room_in, "كهربائي / فيش", cam_bytes)
            st.rerun()

    if st.button("❄️ AC Issue | اے سی خراب"):
        if not room_in.strip():
            st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
        else:
            register_ticket(room_in, "مكيف AC", cam_bytes)
            st.rerun()

    if st.button("🚰 Plumber | پلمبر / پانی"):
        if not room_in.strip():
            st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
        else:
            register_ticket(room_in, "سباكة", cam_bytes)
            st.rerun()

    if st.button("🧹 Clean / Pests | صفائی / کیڑے"):
        if not room_in.strip():
            st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
        else:
            register_ticket(room_in, "نظافة / حشرات", cam_bytes)
            st.rerun()

st.divider()

# ==============================================================================
# 5. لوحة المشرف الميداني (كل الأزرار قريبة من الإبهام + ملاحظات جاهزة + تصفير)
# ==============================================================================
with st.expander("🔐 لوحة المشرف الميداني"):
    pin = st.text_input("رمز المشرف:", type="password", key="sup_pin")
    if hmac.compare_digest(pin.strip().encode(), ADMIN_PIN.encode()):
        open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
        fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]

        # --- أ) تشيك النظافة الجاهز بالنظام بلمسة إصبع واحدة ---
        st.markdown("###### 🧹 1. تشيك النظافة (مسجل جاهز بالنظام):")
        clean_choice = st.radio(
            "حالة النظافة اليوم:",
            [
                "تشيك كامل 100% ✓",
                "الممرات والسطح نظيفة 100% ✓",
                "حملة نظافة الجمعة مكتملة 100% ✓",
                "تحتاج متابعة في بعض الأدوار",
            ],
            index=0,
        )
        db["cleaning_status"] = clean_choice

        st.markdown("---")

        # --- ب) الصيانة والمخالفات (كل شيء جنب زر الحفظ مباشرة) ---
        st.markdown("###### 🛠️ 2. تسجيل سريع (عطل أو مخالفة):")
        sup_loc = st.text_input("رقم الغرفة أو الموقع:", placeholder="مثال: 213 أو السطح")
        sup_item = st.radio(
            "اختر البند بلمسة واحدة:",
            [
                "كهربائي / فيش 🔌",
                "مكيف AC ❄️",
                "سباكة / صنبور 🚰",
                "مخالفة سخان ⚡",
                "مخالفة نظافة 🗑️",
            ],
            horizontal=True,
        )
        if st.button("⚡ إضافة للسجل"):
            if sup_loc.strip():
                floc = format_room_only(sup_loc)
                clean_lbl = sup_item.rsplit(" ", 1)[0]
                if "مخالفة" in sup_item:
                    db["violations"].append({
                        "loc": floc,
                        "type": clean_lbl.replace("مخالفة ", ""),
                        "time": now_time_str,
                    })
                else:
                    register_ticket(sup_loc, clean_lbl)
                    if "done_ticket" in st.session_state:
                        del st.session_state["done_ticket"]
                st.success(f"تم تسجيل ({floc} - {clean_lbl})!")
                st.rerun()

        if open_reps:
            st.markdown("###### ⏳ قيد التنفيذ (الزر جنب الغرفة مباشرة):")
            for idx, r in enumerate(reversed(open_reps)):
                c1, c2 = st.columns([2.4, 1.2])
                img_icon = " 📷" if r.get("photo") else ""
                c1.markdown(f"**{r['loc']}** — {r['item']}{img_icon}")
                if c2.button("تم ✓", key=f"done_{idx}_{r['loc']}_{r['item']}"):
                    r["status"] = "تم الإصلاح"
                    st.rerun()
                if r.get("photo"):
                    with st.expander(f"صورة {r['loc']}"):
                        st.image(r["photo"], use_container_width=True)

        st.markdown("---")

        # --- ج) الوجبات (3 خانات + ساعة الآيفون الدوارة + الفائض فقط) ---
        st.markdown("###### 🍱 3. الوجبة ووقت الوصول:")
        m_type = st.radio("الوجبة:", ["فطور", "غداء", "عشاء"], index=1, horizontal=True)

        default_t = time(5, 30) if m_type == "فطور" else (time(11, 30) if m_type == "غداء" else time(17, 30))
        arr_t = st.time_input("⏰ وقت الوصول (اسحب الساعة):", value=default_t)

        official_mins = (5 * 60 + 30) if m_type == "فطور" else ((11 * 60 + 30) if m_type == "غداء" else (17 * 60 + 30))
        actual_mins = arr_t.hour * 60 + arr_t.minute
        delay_m = max(0, actual_mins - official_mins)

        h12 = arr_t.hour % 12 or 12
        ampm = "م" if arr_t.hour >= 12 else "ص"
        arr_str = f"{h12:02d}:{arr_t.minute:02d} {ampm}"

        if delay_m == 0:
            st.markdown(f"<div class='box'><span class='green'>🟢 بالموعد ({arr_str})</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='crimson-box'>🟣 تأخير <b>{delay_m} دقيقة</b> (وصل {arr_str})</div>", unsafe_allow_html=True)

        deliv_cnt = st.text_input("كم العدد؟", value="77")
        has_surp = st.radio("هل يوجد فائض؟", ["لا", "نعم"], horizontal=True)
        surp_cnt = st.text_input("كم الفائض؟", value="0") if has_surp == "نعم" else "0"

        if st.button("⚡ اعتماد الوجبة"):
            db["meals"].append({
                "meal": m_type,
                "arrival": arr_str,
                "delay": delay_m,
                "deliv": deliv_cnt.strip() or "0",
                "has_surplus": has_surp,
                "surp": surp_cnt.strip() or "0",
            })
            st.success(f"تم حفظ {m_type}!")
            st.rerun()

        st.markdown("---")

        # --- د) التقرير المختصر والواضح (النظافة 100% + كم مخالفة اليوم + الوجبة + الصيانة) ---
        st.markdown("###### 📲 4. التقرير المختصر الجاهز:")
        if db["meals"]:
            lm = db["meals"][-1]
        else:
            lm = {
                "meal": m_type,
                "arrival": arr_str,
                "delay": delay_m,
                "deliv": deliv_cnt.strip() or "77",
                "has_surplus": has_surp,
                "surp": surp_cnt.strip() or "0",
            }

        delay_txt = f"في الموعد ({lm['arrival']})" if lm["delay"] == 0 else f"تأخير {lm['delay']} دقيقة (وصل {lm['arrival']})"
        open_lines = "\n".join([f"• {r['loc']}: {r['item']}" for r in open_reps]) if open_reps else "• لا يوجد"
        fixed_lines = "\n".join([f"• {r['loc']}: {r['item']} ✓" for r in fixed_reps]) if fixed_reps else "• لا يوجد"

        viol_count = len(db["violations"])
        viol_lines = "\n".join([f"• {v['loc']}: {v['type']}" for v in db["violations"]]) if viol_count > 0 else "• لا يوجد (0)"

        short_report = f"""*{LOCATION_TAG}*
*المشرف: فارس العصيمي*

*🧹 النظافة:* {db['cleaning_status']}

*🍱 {lm['meal']}:* {delay_txt}
• العدد: {lm['deliv']}
• هل يوجد فائض: {lm['has_surplus']}
• كم الفائض: {lm['surp']}

*🛠️ الصيانة:*
قيد التنفيذ ({len(open_reps)}):
{open_lines}
تم الإصلاح ({len(fixed_reps)}):
{fixed_lines}

*⚠️ المخالفات اليوم ({viol_count}):*
{viol_lines}"""

        st.text_area("معاينة التقرير:", value=short_report, height=230)
        st.markdown(
            f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(short_report)}" target="_blank" class="wa-btn">📲 إرسال للواتساب</a>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        # زر تصفير وبدء يوم جديد بلمسة واحدة
        if st.button("🗑️ تصفير السجل بالكامل وبدء يوم جديد"):
            db["repairs"].clear()
            db["violations"].clear()
            db["meals"].clear()
            db["cleaning_status"] = "تشيك كامل 100% ✓"
            if "done_ticket" in st.session_state:
                del st.session_state["done_ticket"]
            st.success("تم مسح جميع البيانات القديمة وبدء سجل نظيف!")
            st.rerun()
