from datetime import datetime, time, timedelta, timezone
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعدادات السرعة القصوى وتوقيت جدة (مخصص للآيباد والميدان)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
now_ksa = datetime.now(KSA_TZ)
today_date = now_ksa.strftime("%Y-%m-%d")
now_time_str = now_ksa.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")

st.set_page_config(
    page_title="Housing 3 | Supervisor Ops",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 2. تصميم واجهة الإبهام (أزرار متجاورة ومرنة للسرعة القصوى)
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
/* إجبار الأزرار على التجاور لتسهيل الاستخدام بالإبهام */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    flex: 1 1 48% !important;
    width: 48% !important;
    min-width: 0 !important;
}
div.stButton > button {
    height: 72px !important;
    font-size: 1.02em !important;
    font-weight: 900 !important;
    border-radius: 14px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(16, 185, 129, 0.5) !important;
    white-space: pre-line !important;
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
# 3. قاعدة البيانات المركزية المشتركة
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
SUPERVISOR_NAME = "فارس العصيمي"
SUPERVISOR_WA = "966566261868"
ADMIN_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()


def format_room_only(raw_txt: str) -> str:
    clean = raw_txt.strip()
    if clean.isdigit():
        return f"غرفة {clean}"
    return clean or "عام"


def register_ticket(raw_room: str, issue_label: str, photo_data=None):
    loc_clean = format_room_only(raw_room)
    t_now = datetime.now(KSA_TZ).strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")

    # إدارة المخاطر: منع التكرار لنفس الغرفة والعطل
    for r in db["repairs"]:
        if r["loc"] == loc_clean and r["item"] == issue_label and r["status"] == "مفتوح":
            r["pings"] = r.get("pings", 1) + 1
            if photo_data and not r.get("photo"):
                r["photo"] = photo_data
            st.session_state["done_ticket"] = {
                "loc": r["loc"],
                "item": r["item"],
                "time": r["time"],
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
        "is_duplicate": False,
    }


# ==============================================================================
# 4. واجهة التشغيل الخاصة بك على الآيباد (تسجيل سريع بالأزرار المتجاورة)
# ==============================================================================
st.markdown(
    f"""
    <div class="box" style="text-align:center;">
        <b style="font-size:1.15em;">🛠️ لوحة عمليات {LOCATION_TAG}</b><br>
        <small style="color:#94a3b8;">المشرف: {SUPERVISOR_NAME} • سجّل البلاغات وجولاتك فوراً</small>
    </div>
    """,
    unsafe_allow_html=True,
)

if "done_ticket" in st.session_state:
    tk = st.session_state["done_ticket"]
    if tk.get("is_duplicate"):
        st.markdown(
            f"""
            <div class="crimson-box" style="text-align:center; padding:16px;">
                <div style="font-size:2em;">⏳</div>
                <h3 class="crimson" style="margin:4px 0;">تنبيه: البلاغ مكرر وقيد التنفيذ</h3>
                <p style="font-size:0.95em; margin-top:6px;">
                    📍 <b>{tk['loc']}</b> ({tk['item']}) مسجل مسبقاً الساعة {tk['time']}<br>
                    تم زيادة عداد الاستعجال على المقاول تلقائياً.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="box" style="border:1.5px solid #10b981; text-align:center; padding:16px;">
                <div style="font-size:2em;">✅</div>
                <h3 class="green" style="margin:4px 0;">تم تسجيل البلاغ بنجاح</h3>
                <p style="font-size:0.95em; margin-top:6px;">
                    📍 <b>{tk['loc']}</b> — 🔧 <b>{tk['item']}</b> (⏰ {tk['time']})<br>
                    مهلة الإصلاح: 24 ساعة كحد أقصى.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("🔄 تسجيل بلاغ آخر"):
        del st.session_state["done_ticket"]
        st.rerun()
else:
    # الترتيب الجديد: 1. رقم الغرفة ⬅️ 2. اختيار العطل ⬅️ 3. إرفاق صورة (في النهاية)
    room_in = st.text_input("1️⃣ رقم الغرفة أو الموقع:", placeholder="مثال: 213 أو السطح")

    st.caption("2️⃣ اختر نوع العطل بضغطة زر متجاورة:")

    # أزرار متجاورة 2x2 لتسهيل الضغط بالإبهام
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        btn_elec = st.button("🔌 كهربائي / فيش")
        btn_plumb = st.button("🚰 سباكة / صنبور")
    with col_a2:
        btn_ac = st.button("❄️ مكيف AC")
        btn_clean = st.button("🧹 نظافة / حشرات")

    # 3. إرفاق صورة العطل (في النهاية اختيارياً)
    cam_file = st.file_uploader("3️⃣ إرفاق صورة العطل (اختياري):", type=["jpg", "jpeg", "png"])
    cam_bytes = cam_file.getvalue() if cam_file else None

    if btn_elec:
        if not room_in.strip():
            st.warning("⚠️ الرجاء كتابة رقم الغرفة أو الموقع أولاً.")
        else:
            register_ticket(room_in, "كهربائي / فيش", cam_bytes)
            st.rerun()

    if btn_ac:
        if not room_in.strip():
            st.warning("⚠️ الرجاء كتابة رقم الغرفة أو الموقع أولاً.")
        else:
            register_ticket(room_in, "مكيف AC", cam_bytes)
            st.rerun()

    if btn_plumb:
        if not room_in.strip():
            st.warning("⚠️ الرجاء كتابة رقم الغرفة أو الموقع أولاً.")
        else:
            register_ticket(room_in, "سباكة", cam_bytes)
            st.rerun()

    if btn_clean:
        if not room_in.strip():
            st.warning("⚠️ الرجاء كتابة رقم الغرفة أو الموقع أولاً.")
        else:
            register_ticket(room_in, "نظافة / حشرات", cam_bytes)
            st.rerun()

st.divider()

# ==============================================================================
# 5. لوحة المشرف الكاملة (إدارة الصيانة، الوجبات بحساب التأخير > 30 دقيقة، والتقرير المختصر بـ 3 نقرات)
# ==============================================================================
with st.expander("🔐 لوحة التحكم والتقارير (رمز: 5050)"):
    pin = st.text_input("رمز المشرف:", type="password", key="sup_pin")
    if hmac.compare_digest(pin.strip().encode(), ADMIN_PIN.encode()):
        open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
        fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]

        sub_maint, sub_meals, sub_wa = st.tabs([
            "🛠️ الصيانة والنظافة",
            "🍱 الوجبات والتأخير",
            "📲 التقرير الصافي",
        ])

        # --- 1. إدارة الصيانة والنظافة ---
        with sub_maint:
            st.markdown("###### 🧹 حالة النظافة العامة:")
            clean_choice = st.radio(
                "اختر تشيك النظافة:",
                [
                    "تشيك كامل 100% ✓",
                    "الممرات والسطح نظيفة 100% ✓",
                    "حملة نظافة الجمعة مكتملة 100% ✓",
                    "تحتاج متابعة",
                ],
                index=0,
                horizontal=True,
            )
            db["cleaning_status"] = clean_choice

            st.markdown("###### ⏳ البلاغات المعلقة (قيد التنفيذ):")
            if open_reps:
                for idx, r in enumerate(reversed(open_reps)):
                    col1, col2 = st.columns([2.5, 1.3])
                    img_badge = " 📷" if r.get("photo") else ""
                    ping_note = f" (استعجال {r.get('pings', 1)})" if r.get("pings", 1) > 1 else ""
                    col1.markdown(f"**{r['loc']}**: {r['item']}{img_badge}{ping_note}")
                    if col2.button("تم الإصلاح ✓", key=f"fix_{idx}_{r['loc']}_{r['item']}"):
                        r["status"] = "تم الإصلاح"
                        st.rerun()
                    if r.get("photo"):
                        with st.expander(f"معاينة صورة {r['loc']}"):
                            st.image(r["photo"], use_container_width=True)
            else:
                st.success("لا توجد بلاغات صيانة معلقة.")

            st.markdown("###### ➕ إضافة مخالفة يدوية:")
            v_loc = st.text_input("رقم الغرفة للمخالفة:", placeholder="مثال: 108")
            v_type = st.radio("نوع المخالفة:", ["سخان طبخ", "إهمال نظافة"], horizontal=True)
            if st.button("⚡ تسجيل المخالفة"):
                if v_loc.strip():
                    floc = format_room_only(v_loc)
                    cnt = sum(1 for v in db["violations"] if v["loc"] == floc) + 1
                    db["violations"].append({"loc": floc, "type": v_type, "count": cnt, "time": now_time_str})
                    st.success("تم تسجيل المخالفة!")
                    st.rerun()

        # --- 2. الوجبات (حساب التأخير الذكي: أكثر من 30 دقيقة يحسب، أقل لا) ---
        with sub_meals:
            m_type = st.radio("الوجبة:", ["فطور", "غداء", "عشاء"], index=1, horizontal=True)

            default_t = time(5, 30) if m_type == "فطور" else (time(11, 30) if m_type == "غداء" else time(17, 30))
            arr_t = st.time_input("⏰ وقت وصول الوجبة الفعلي:", value=default_t)

            official_mins = (5 * 60 + 30) if m_type == "فطور" else ((11 * 60 + 30) if m_type == "غداء" else (17 * 60 + 30))
            actual_mins = arr_t.hour * 60 + arr_t.minute
            raw_delay = actual_mins - official_mins

            # شرط الـ 30 دقيقة: إذا كان التأخير أقل من أو يساوي 30 دقيقة، يعتبر منضبطاً (صفر تأخير مؤثر)
            delay_m = raw_delay if raw_delay > 30 else 0

            h12 = arr_t.hour % 12 or 12
            ampm = "م" if arr_t.hour >= 12 else "ص"
            arr_str = f"{h12:02d}:{arr_t.minute:02d} {ampm}"

            if delay_m == 0:
                st.markdown(f"<div class='box'><span class='green'>🟢 منضبط (وصل {arr_str} - التأخير أقل من 30 دقيقة)</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='crimson-box'>🟣 تأخير مؤثر: <b>{delay_m} دقيقة</b> (وصل {arr_str})</div>", unsafe_allow_html=True)

            deliv_cnt = st.text_input("العدد المستلم:", value="77")
            has_surp = st.radio("هل يوجد فائض؟", ["لا", "نعم"], horizontal=True)
            surp_cnt = st.text_input("كم الفائض؟", value="0") if has_surp == "نعم" else "0"

            if st.button("⚡ حفظ بيان الوجبة"):
                db["meals"].append({
                    "meal": m_type,
                    "arrival": arr_str,
                    "delay": delay_m,
                    "deliv": deliv_cnt.strip() or "0",
                    "has_surplus": has_surp,
                    "surp": surp_cnt.strip() or "0",
                })
                st.success(f"تم حفظ بيانات وجبة {m_type}!")
                st.rerun()

        # --- 3. التقرير المختصر الصافي (3 إلى 4 نقرات للإرسال) ---
        with sub_wa:
            lm = db["meals"][-1] if db["meals"] else {"meal": m_type, "arrival": arr_str, "delay": delay_m, "deliv": deliv_cnt, "has_surplus": has_surp, "surp": surp_cnt}
            delay_txt = f"في الموعد ({lm['arrival']})" if lm["delay"] == 0 else f"تأخير مؤثر {lm['delay']} دقيقة (وصل {lm['arrival']})"

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

            st.text_area("معاينة التقرير الصافي:", value=short_report, height=220)
            st.markdown(
                f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(short_report)}" target="_blank" class="wa-btn">📲 إرسال التقرير للواتساب</a>',
                unsafe_allow_html=True,
            )

            st.markdown("---")
            if st.button("🗑️ تصفير السجل وبدء يوم جديد"):
                db["repairs"].clear()
                db["violations"].clear()
                db["meals"].clear()
                db["cleaning_status"] = "تشيك كامل 100% ✓"
                if "done_ticket" in st.session_state:
                    del st.session_state["done_ticket"]
                st.success("تم مسح السجل بنجاح!")
                st.rerun()
