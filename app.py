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
# 2. تصميم شبكة مربعة 2x2 حقيقية على الجوال + لون قرمزي هادئ
# ==============================================================================
st.markdown(
    """
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container {
    max-width: 420px !important;
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
/* إجبار الأعمدة على البقاء بجانب بعضها على شاشة الجوال لتكوين شبكة مربعة 2x2 */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 10px !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    flex: 1 1 48% !important;
    width: 48% !important;
    min-width: 0 !important;
}
div.stButton > button {
    height: 96px !important;
    font-size: 1.02em !important;
    font-weight: 900 !important;
    border-radius: 16px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(16, 185, 129, 0.5) !important;
    white-space: pre-line !important;
    line-height: 1.45 !important;
    padding: 8px !important;
}
div.stButton > button:active, div.stButton > button:hover {
    background: #10b981 !important;
    color: #022c22 !important;
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
.yellow { color: #fcd34d; font-weight: 800; }
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
# 3. قاعدة البيانات المشتركة (بدون أرقام طلبات وبدون أدوار — رقم الغرفة فقط)
# ==============================================================================
@st.cache_resource
def get_shared_db():
    return {
        "repairs": [
            {"loc": "السطح", "item": "سباكة", "time": "10:15 ص", "status": "مفتوح", "pings": 1, "photo": None},
            {"loc": "غرفة 213", "item": "مكيف AC", "time": "11:00 ص", "status": "مفتوح", "pings": 1, "photo": None},
            {"loc": "غرفة 104", "item": "كهربائي / فيش", "time": "09:30 ص", "status": "تم الإصلاح", "pings": 1, "photo": None},
        ],
        "violations": [
            {"loc": "غرفة 108", "type": "سخان طبخ", "count": 2, "time": "09:15 م"},
        ],
        "meals": [
            {
                "meal": "غداء",
                "arrival": "12:23 م",
                "delay": 53,
                "deliv": 77,
                "has_surplus": "لا",
                "surp": 0,
            }
        ],
    }


db = get_shared_db()

LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_WA = "966566261868"
ADMIN_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()


def format_room_only(raw_txt: str) -> str:
    """كتابة رقم الغرفة فقط بدون دور وبدون رقم طلب."""
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
# 4. واجهة العمال السريعة (English + Urdu | شبكة مربعة 2x2 | كاميرا خفيفة)
# ==============================================================================
st.markdown(
    """
    <div class="box" style="text-align:center;">
        <b style="font-size:1.1em;">🛠️ Maintenance | مرمت رپورٹ</b><br>
        <small style="color:#94a3b8;">Enter Room No & Tap Box • کمرہ نمبر لکھیں اور بٹن دبائیں</small>
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
    photo_note = "\n📷 مرفق صورة العطل" if tk.get("has_photo") else ""
    wa_worker = f"*{LOCATION_TAG}*\n{tk['loc']} — {tk['item']} ({tk['time']}){photo_note}"

    if tk.get("is_duplicate"):
        st.markdown(
            f"""
            <div class="crimson-box" style="text-align:center; padding:18px;">
                <div style="font-size:2.2em;">⏳</div>
                <h3 class="crimson" style="margin:4px 0;">Already Logged</h3>
                <b style="color:#ffffff;">یہ شکایت پہلے سے درج ہے اور کارروائی جاری ہے</b><br>
                <p style="color:#e2e8f0; font-size:0.9em; margin-top:8px;">
                    📍 <b>{tk['loc']}</b> ({tk['item']})<br>
                    ⏰ Time / وقت: <b>{tk['time']}</b><br>
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

    # زر كاميرا الجوال الخفيف (يفتح الكاميرا مباشرة عند اللمس دون إثقال السيرفر)
    cam_file = st.file_uploader(
        "📷 Photo (Optional) / تصویر (اختیاری):",
        type=["jpg", "jpeg", "png"],
    )
    cam_bytes = cam_file.getvalue() if cam_file else None

    # شبكة مربعة 2x2 حقيقية بجانب بعضها للوصول السريع بالإبهام
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        if st.button("🔌 Electric / Socket\nبجلی / ساکٹ"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_ticket(room_in, "كهربائي / فيش", cam_bytes)
                st.rerun()

    with row1_c2:
        if st.button("❄️ AC Issue\nاے سی خراب"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_ticket(room_in, "مكيف AC", cam_bytes)
                st.rerun()

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        if st.button("🚰 Plumber\nپلمبر / پانی"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_ticket(room_in, "سباكة", cam_bytes)
                st.rerun()

    with row2_c2:
        if st.button("🧹 Clean / Pests\nصفائی / کیڑے"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_ticket(room_in, "نظافة / حشرات", cam_bytes)
                st.rerun()

st.divider()

# ==============================================================================
# 5. بوابة المشرف الميداني (فارس العصيمي - الرمز 5050)
# ==============================================================================
with st.expander("🔐 لوحة المشرف الميداني"):
    pin = st.text_input("رمز المشرف:", type="password", key="sup_pin")
    if hmac.compare_digest(pin.strip().encode(), ADMIN_PIN.encode()):
        all_reps = db["repairs"]
        open_reps = [r for r in all_reps if r["status"] == "مفتوح"]
        fixed_reps = [r for r in all_reps if r["status"] == "تم الإصلاح"]

        sub_maint, sub_meals, sub_wa = st.tabs([
            "🛠️ الصيانة",
            "🍱 الوجبات",
            "📲 التقرير",
        ])

        # --- 1. الصيانة والصور ---
        with sub_maint:
            st.markdown("###### ➕ رصد سريع (غرفة أو موقع):")
            c_m1, c_m2 = st.columns(2)
            sup_loc = c_m1.text_input("رقم الغرفة:", placeholder="213")
            sup_item = c_m2.selectbox(
                "البند:",
                ["كهربائي / فيش", "مكيف AC", "سباكة", "نظافة", "مخالفة سخان ⚡"],
            )
            sup_photo = st.file_uploader("📷 صورة العطل:", type=["jpg", "jpeg", "png"], key="sup_cam")
            if st.button("⚡ حفظ"):
                if sup_loc.strip():
                    floc = format_room_only(sup_loc)
                    if "مخالفة" in sup_item:
                        cnt = sum(1 for v in db["violations"] if v["loc"] == floc) + 1
                        db["violations"].append({"loc": floc, "type": "سخان طبخ", "count": cnt, "time": now_time_str})
                    else:
                        register_ticket(sup_loc, sup_item, sup_photo.getvalue() if sup_photo else None)
                        if "done_ticket" in st.session_state:
                            del st.session_state["done_ticket"]
                    st.rerun()

            st.markdown("###### ⏳ قيد التنفيذ:")
            for idx, r in enumerate(reversed(open_reps)):
                col1, col2 = st.columns([2.6, 1.4])
                img_tag = " 📷" if r.get("photo") else ""
                col1.markdown(
                    f"**{r['loc']}**: {r['item']}{img_tag} <small>({r['time']})</small>",
                    unsafe_allow_html=True,
                )
                if r.get("photo"):
                    with st.expander(f"🖼️ صورة {r['loc']}"):
                        st.image(r["photo"], use_container_width=True)
                if col2.button("أُصلح ✓", key=f"fix_{idx}_{r['loc']}_{r['item']}"):
                    r["status"] = "تم الإصلاح"
                    st.rerun()

        # --- 2. الوجبات: 3 خانات فقط + ساعة الآيفون الدوارة + التركيز على الفائض بدون اقتراحات ---
        with sub_meals:
            m_type = st.radio("الوجبة:", ["فطور", "غداء", "عشاء"], index=1, horizontal=True)

            # ساعة الآيفون الدوارة (بدون أزرار + و -)
            default_t = time(5, 30) if m_type == "فطور" else (time(12, 23) if m_type == "غداء" else time(17, 30))
            arr_t = st.time_input("⏰ وقت وصول الأكل (اسحب الساعة):", value=default_t)

            # حساب التأخير بالدقائق تلقائياً مقارنة بالوقت الرسمي
            official_mins = (5 * 60 + 30) if m_type == "فطور" else ((11 * 60 + 30) if m_type == "غداء" else (17 * 60 + 30))
            actual_mins = arr_t.hour * 60 + arr_t.minute
            delay_m = max(0, actual_mins - official_mins)

            h12 = arr_t.hour % 12 or 12
            ampm = "م" if arr_t.hour >= 12 else "ص"
            arr_str = f"{h12:02d}:{arr_t.minute:02d} {ampm}"

            if delay_m == 0:
                st.markdown(f"<div class='box'><span class='green'>🟢 وصل في الموعد ({arr_str})</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='crimson-box'>🟣 تأخير <b>{delay_m} دقيقة</b> (وصل {arr_str})</div>", unsafe_allow_html=True)

            # أسئلة العدد والفائض فقط (بدون أي اقتراحات)
            deliv_cnt = st.text_input("كم العدد المستلم؟", value="77")
            has_surp = st.radio("هل يوجد فائض؟", ["لا", "نعم"], horizontal=True)
            surp_cnt = st.text_input("كم الفائض؟", value="0") if has_surp == "نعم" else "0"

            if st.button("⚡ حفظ الوجبة"):
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

        # --- 3. التقرير المختصر الصافي (بدون تاريخ، بدون رقم طلب، بدون اقتراحات) ---
        with sub_wa:
            lm = db["meals"][-1]
            delay_txt = f"في الموعد ({lm['arrival']})" if lm["delay"] == 0 else f"تأخير {lm['delay']} دقيقة (وصل {lm['arrival']})"

            open_lines = "\n".join([f"• {r['loc']}: {r['item']}{' [مرفق صورة]' if r.get('photo') else ''}" for r in open_reps]) if open_reps else "• لا يوجد"
            fixed_lines = "\n".join([f"• {r['loc']}: {r['item']} ✓" for r in fixed_reps[-5:]]) if fixed_reps else "• لا يوجد"
            viol_lines = "\n".join([f"• {v['loc']}: {v['type']} ({v['count']})" for v in db["violations"][-4:]]) if db["violations"] else "• لا يوجد"

            short_report = f"""*{LOCATION_TAG}*
*المشرف: فارس العصيمي*

*🍱 {lm['meal']}:* {delay_txt}
• العدد: {lm['deliv']}
• هل يوجد فائض: {lm['has_surplus']}
• كم الفائض: {lm['surp']}

*🛠️ الصيانة:*
قيد التنفيذ:
{open_lines}
تم الإصلاح:
{fixed_lines}

*⚠️ المخالفات:*
{viol_lines}"""

            st.text_area("التقرير:", value=short_report, height=220)
            st.markdown(
                f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(short_report)}" target="_blank" class="wa-btn">📲 إرسال للواتساب</a>',
                unsafe_allow_html=True,
            )

            clean_repairs = [{k: v for k, v in r.items() if k != "photo"} for r in db["repairs"]]
            st.download_button(
                "📥 إكسل الصيانة",
                data=pd.DataFrame(clean_repairs).to_csv(index=False).encode("utf-8-sig"),
                file_name="Repairs.csv",
                use_container_width=True,
            )
            st.download_button(
                "📥 إكسل الوجبات",
                data=pd.DataFrame(db["meals"]).to_csv(index=False).encode("utf-8-sig"),
                file_name="Meals.csv",
                use_container_width=True,
            )
