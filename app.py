from datetime import datetime, timedelta, timezone
import hmac
import math
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعدادات السرعة القصوى وتوقيت جدة (تتحمل 470 نزيلاً بدون أي ثقل)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
now_ksa = datetime.now(KSA_TZ)
today_date = now_ksa.strftime("%Y-%m-%d")
now_time_str = now_ksa.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")

st.set_page_config(
    page_title="سكن جامعة 3 | الصيانة والعمليات",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# تصميم خفيف جداً وسريع التحميل (واجهة بديهية يفهمها طفل بعمر 6 سنوات)
st.markdown(
    """
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { max-width: 420px !important; padding-top: 0.6rem !important; padding-bottom: 2rem !important; }
html, body, [class*="css"] {
    direction: rtl; text-align: right;
    background-color: #0b0f19 !important; color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Cairo", sans-serif;
}
div.stButton > button {
    height: 60px !important; font-size: 1.08em !important; font-weight: 900 !important;
    border-radius: 12px !important; width: 100% !important; margin-bottom: 6px !important;
    background: #1e293b !important; color: #ffffff !important;
    border: 1.5px solid #10b981 !important;
}
div.stButton > button:active, div.stButton > button:hover {
    background: #10b981 !important; color: #022c22 !important;
}
.box { background: #111827; border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 12px; margin-bottom: 8px; }
.sla-banner { background: rgba(16,185,129,0.12); border: 1.5px solid #10b981; border-radius: 12px; padding: 10px; text-align: center; margin-bottom: 10px; }
.green { color: #6ee7b7; font-weight: 800; }
.yellow { color: #fcd34d; font-weight: 800; }
.red { color: #fca5a5; font-weight: 800; }
.wa-btn {
    display: block; background: #10b981 !important; color: #022c22 !important;
    text-align: center; padding: 14px; border-radius: 12px; font-weight: 900;
    font-size: 1.05em; text-decoration: none !important; margin-top: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 2. قاعدة البيانات المركزية المشتركة (@st.cache_resource) لجميع الـ 470 نزيلاً
# ==============================================================================
@st.cache_resource
def get_shared_db():
    return {
        "seq": 103,
        "round_note": "الممرات والسطح نظيفة والوضع مستقر",
        "repairs": [
            {"id": 101, "loc": "السطح", "item": "سباكة / صنبور", "time": "10:15 ص", "date": today_date, "status": "مفتوح"},
            {"id": 102, "loc": "غرفة 213", "item": "مكيف", "time": "09:30 ص", "date": today_date, "status": "تم الإصلاح"},
            {"id": 103, "loc": "غرفة 213", "item": "مكيف", "time": "11:00 ص", "date": today_date, "status": "مفتوح"},
        ],
        "violations": [
            {"loc": "غرفة 108", "type": "سخان طبخ", "count": 2, "time": "09:15 م"},
        ],
        "meals": [
            {
                "meal": "غداء",
                "official": "11:30 ص",
                "arrival": "12:23 م",
                "delay": 53,
                "deliv": 77,
                "coup": 42,
                "surp": 0,
                "actual": 77,
                "rec": 80,
                "date": today_date,
            }
        ],
    }


db = get_shared_db()

LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_WA = "966566261868"
ADMIN_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

# يدعم شريحة NFC واحدة الآن، ويدعم شرائح الأدوار مستقبلاً (?loc=floor1)
LOC_MAP = {
    "roof": "السطح",
    "floor1": "الدور 1",
    "floor2": "الدور 2",
    "floor3": "الدور 3",
    "floor4": "الدور 4",
}
url_loc = LOC_MAP.get(st.query_params.get("loc", ""), "")


def add_ticket(loc_name: str, issue_name: str):
    t_now = datetime.now(KSA_TZ).strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    db["seq"] += 1
    tid = db["seq"]
    db["repairs"].append({
        "id": tid,
        "loc": loc_name,
        "item": issue_name,
        "time": t_now,
        "date": today_date,
        "status": "مفتوح",
    })
    # تنظيف آلي للذاكرة عند تجاوز 150 سجلاً لضمان سرعة فائقة دائماً
    if len(db["repairs"]) > 150:
        db["repairs"] = db["repairs"][-150:]
    st.session_state["done_ticket"] = {"id": tid, "loc": loc_name, "item": issue_name, "time": t_now}


# ==============================================================================
# 3. الصفحة الرئيسية الافتراضية: الصيانة السريعة للعمال (عربي + أوردو + إنجليزي)
# تفتح فوراً عند لمس شريحة NFC بدون أي تعقيد
# ==============================================================================
st.markdown(
    f"""
    <div class="box" style="text-align:center;">
        <b style="font-size:1.15em;">🛠️ صيانة {LOCATION_TAG} | مرمت رپورٹ</b><br>
        <small style="color:#94a3b8;">اكتب رقم الغرفة واضغط زر العطل • کمرہ نمبر لکھیں اور بٹن دبائیں</small>
    </div>
    <div class="sla-banner">
        <b class="green">⏱️ مهلة الإصلاح: خلال 24 ساعة كحد أقصى (وإن شاء الله قبلها)</b><br>
        <small style="color:#e2e8f0;">
        إدارة السكن مهتمة بإصلاح عطل غرفتك بأسرع طريقة<br>
        سکن انتظامیہ آپ کا مسئلہ 24 گھنٹے سے پہلے حل کرنے کے لیے پوری طرح تیار ہے
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)

# شاشة التأكيد بعد الضغط (تمنع تكرار البلاغ وتطمئن العامل بمهلة الـ 24 ساعة)
if "done_ticket" in st.session_state:
    tk = st.session_state["done_ticket"]
    wa_worker = f"*{LOCATION_TAG} #{tk['id']}*\n{tk['loc']} - {tk['item']} ({tk['time']})"
    st.markdown(
        f"""
        <div class="box" style="border:2px solid #10b981; text-align:center; padding:20px;">
            <div style="font-size:2.4em;">✅</div>
            <h3 class="green" style="margin:4px 0;">تم التسجيل #{tk['id']}</h3>
            <b>{tk['loc']} — {tk['item']}</b><br>
            <p style="color:#cbd5e1; font-size:0.9em; margin-top:8px;">
                مهلة الإصلاح: <b>24 ساعة</b> (وإن شاء الله قبلها).<br>
                ان شاء اللہ 24 گھنٹے سے پہلے مرمت مکمل ہو جائے گی۔
            </p>
        </div>
        <a href="https://wa.me/{SUPERVISOR_WA}?text={urllib.parse.quote(wa_worker)}" target="_blank" class="wa-btn">
            📲 إرسال تأكيد واتساب للمشرف | واٹس ایپ بھیجیں
        </a>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🔄 تسجيل عطل آخر | نئی شکایت"):
        del st.session_state["done_ticket"]
        st.rerun()
else:
    room_in = st.text_input(
        "1️⃣ رقم الغرفة / کمرہ نمبر / Room No:",
        value=url_loc,
        placeholder="مثال: 213",
    )
    target_loc = f"غ {room_in.strip()}" if room_in.strip().isdigit() else (room_in.strip() or "عام")

    st.caption("2️⃣ اضغط زر العطل للإرسال الفوري / مسئلہ کا بٹن دبائیں:")

    if st.button("❄️ مكيف حار أو يقطر | اے سی خراب | AC"):
        if not room_in.strip():
            st.error("⚠️ اكتب رقم الغرفة / پہلے کمرہ نمبر لکھیں")
        else:
            add_ticket(target_loc, "مكيف")
            st.rerun()

    if st.button("🚰 سباكة وتهريب ماء | پانی لیکج | Water"):
        if not room_in.strip():
            st.error("⚠️ اكتب رقم الغرفة / پہلے کمرہ نمبر لکھیں")
        else:
            add_ticket(target_loc, "سباكة")
            st.rerun()

    if st.button("💡 كهرباء ولمبات | بجلی کا مسئلہ | Power"):
        if not room_in.strip():
            st.error("⚠️ اكتب رقم الغرفة / پہلے کمرہ نمبر لکھیں")
        else:
            add_ticket(target_loc, "كهرباء")
            st.rerun()

    if st.button("🧹 نظافة وحشرات | صفائی / کیڑے | Clean"):
        if not room_in.strip():
            st.error("⚠️ اكتب رقم الغرفة / پہلے کمرہ نمبر لکھیں")
        else:
            add_ticket(target_loc, "نظافة")
            st.rerun()

st.divider()

# ==============================================================================
# 4. بوابة المشرف الميداني (فارس العصيمي - الرمز 5050 في نفس الشاشة)
# ==============================================================================
with st.expander("🔐 لوحة المشرف الميداني (إدارة الوردية والتقارير)"):
    pin = st.text_input("رمز المشرف:", type="password", key="sup_pin")
    if hmac.compare_digest(pin.strip().encode(), ADMIN_PIN.encode()):
        # --- أ) الأداة الرقابية: نسبة الإنجاز SLA + كشف الغرف المكررة ---
        all_reps = db["repairs"]
        open_reps = [r for r in all_reps if r["status"] == "مفتوح"]
        fixed_reps = [r for r in all_reps if r["status"] == "تم الإصلاح"]
        sla_pct = round((len(fixed_reps) / len(all_reps) * 100)) if all_reps else 100

        loc_counts = pd.Series([r["loc"] for r in all_reps]).value_counts()
        repeat_locs = [f"{k} ({v})" for k, v in loc_counts[loc_counts >= 2].items()]
        repeat_str = "، ".join(repeat_locs) if repeat_locs else "لا يوجد"

        k1, k2, k3 = st.columns(3)
        k1.metric("معلق", len(open_reps))
        k2.metric("إنجاز المقاول", f"{sla_pct}%")
        k3.metric("غرف مكررة ⚠️", len(repeat_locs))
        if repeat_locs:
            st.warning(f"⚠️ تكرار أعطال (مراجعة المقاول): {repeat_str}")

        sub_maint, sub_meals, sub_wa = st.tabs([
            "🛠️ الصيانة والرصد",
            "🍱 الوجبات والتأخير",
            "📲 التقرير المختصر",
        ])

        # --- 1. إدارة الصيانة + تسجيل ما شفته بعينك ولم يسجله العمال ---
        with sub_maint:
            st.markdown("###### ➕ رصد المشرف المباشر (صيانة أو مخالفة):")
            c_m1, c_m2 = st.columns([1.3, 1.7])
            sup_loc = c_m1.text_input("الموقع/الغرفة:", placeholder="السطح أو 108")
            sup_item = c_m2.selectbox(
                "البند:",
                ["صنبور يبق ماء", "مكيف", "شطاف", "نظافة الجمعة/ممرات", "مخالفة سخان ⚡", "مخالفة نظافة 🗑️"],
            )
            if st.button("⚡ حفظ في السجل"):
                if sup_loc.strip():
                    floc = f"غ {sup_loc.strip()}" if sup_loc.strip().isdigit() else sup_loc.strip()
                    if "مخالفة" in sup_item:
                        cnt = sum(1 for v in db["violations"] if v["loc"] == floc) + 1
                        db["violations"].append({"loc": floc, "type": sup_item.replace("مخالفة ", ""), "count": cnt, "time": now_time_str})
                    else:
                        add_ticket(floc, sup_item)
                        if "done_ticket" in st.session_state:
                            del st.session_state["done_ticket"]
                    st.success("تم الحفظ!")
                    st.rerun()

            st.markdown("###### ⏳ المعلق حالياً (ضغطة للإغلاق):")
            for idx, r in enumerate(reversed(open_reps)):
                col1, col2 = st.columns([2.6, 1.4])
                col1.markdown(f"**#{r['id']} {r['loc']}**: {r['item']} <small>({r['time']})</small>", unsafe_allow_html=True)
                if col2.button("أُصلح ✓", key=f"fix_{r['id']}_{idx}"):
                    r["status"] = "تم الإصلاح"
                    st.rerun()

        # --- 2. تسجيل الوجبات بأسهل طريقة (مضبوط على تأخير غداء اليوم 53 دقيقة) ---
        with sub_meals:
            m_type = st.radio("الوجبة:", ["فطور (05:30 ص)", "غداء (11:30 ص)", "عشاء (05:30 م)"], index=1, horizontal=True)
            clean_m_name = m_type.split()[0]
            off_time = "05:30 ص" if clean_m_name == "فطور" else ("11:30 ص" if clean_m_name == "غداء" else "05:30 م")

            # إدخال دقائق التأخير بلمسة واحدة (مضبوط افتراضياً على 53 دقيقة لغداء اليوم)
            delay_m = st.number_input("⏱️ دقائق التأخير (0 = بالموعد):", min_value=0, max_value=240, value=53 if clean_m_name == "غداء" else 0)

            base_mins = 330 if clean_m_name == "فطور" else (690 if clean_m_name == "غداء" else 1050)
            arr_total = base_mins + int(delay_m)
            arr_h24 = (arr_total // 60) % 24
            arr_m = arr_total % 60
            arr_h12 = arr_h24 % 12 or 12
            arr_ampm = "م" if arr_h24 >= 12 else "ص"
            arr_str = f"{arr_h12:02d}:{arr_m:02d} {arr_ampm}"

            if delay_m == 0:
                st.markdown(f"<div class='box'><span class='green'>🟢 بالموعد ({arr_str})</span></div>", unsafe_allow_html=True)
            elif delay_m <= 15:
                st.markdown(f"<div class='box'><span class='yellow'>🟡 تأخير {delay_m} د (وصل {arr_str})</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='box'><span class='red'>🔴 تأخير {delay_m} د (وصل {arr_str} بدل {off_time})</span></div>", unsafe_allow_html=True)

            cm1, cm2, cm3 = st.columns(3)
            deliv = cm1.number_input("مستلم:", min_value=0, value=77)
            coup = cm2.number_input("كوبون:", min_value=0, value=42)
            surp = cm3.number_input("فائض:", min_value=0, value=0)

            actual = max(0, deliv - surp)
            rec = actual + (math.ceil(actual * 0.03) if actual > 0 else 0)

            if st.button("⚡ حفظ الوجبة"):
                db["meals"].append({
                    "meal": clean_m_name,
                    "official": off_time,
                    "arrival": arr_str,
                    "delay": int(delay_m),
                    "deliv": int(deliv),
                    "coup": int(coup),
                    "surp": int(surp),
                    "actual": int(actual),
                    "rec": int(rec),
                    "date": today_date,
                })
                st.success(f"تم حفظ {clean_m_name} (وصول {arr_str})!")
                st.rerun()

        # --- 3. التقرير المختصر الصافي (بدون أي عبارات زائدة أو حشو) ---
        with sub_wa:
            lm = db["meals"][-1]
            delay_label = (
                f"🟢 بالموعد ({lm['arrival']})"
                if lm["delay"] == 0
                else (
                    f"🟡 تأخير {lm['delay']} د ({lm['arrival']})"
                    if lm["delay"] <= 15
                    else f"🔴 تأخير {lm['delay']} د (وصل {lm['arrival']} بدل {lm['official']})"
                )
            )

            open_lines = "\n".join([f"• {r['loc']}: {r['item']}" for r in open_reps]) if open_reps else "• لا يوجد"
            fixed_lines = "\n".join([f"• {r['loc']}: {r['item']} ✓" for r in fixed_reps[-5:]]) if fixed_reps else "• لا يوجد"
            viol_lines = "\n".join([f"• {v['loc']}: {v['type']} ({v['count']})" for v in db["violations"][-4:]]) if db["violations"] else "• لا يوجد"

            short_report = f"""*{LOCATION_TAG} | {today_date}*
*المشرف: فارس العصيمي*

*🍱 {lm['meal']}:* {delay_label}
مستلم {lm['deliv']} | كوبون {lm['coup']} | فائض {lm['surp']} | فعلي {lm['actual']} | طلب قادم {lm['rec']}

*🛠️ صيانة (إنجاز {sla_pct}%):*
معلق ({len(open_reps)}):
{open_lines}
منجز ({len(fixed_reps)}):
{fixed_lines}
تكرار: {repeat_str}

*⚠️ مخالفات:*
{viol_lines}"""

            st.text_area("التقرير الصافي:", value=short_report, height=210)
            st.markdown(
                f'<a href="https://api.whatsapp.com/send?text={urllib.parse.quote(short_report)}" target="_blank" class="wa-btn">📲 إرسال للواتساب</a>',
                unsafe_allow_html=True,
            )

            st.download_button(
                "📥 إكسل الصيانة (CSV)",
                data=pd.DataFrame(db["repairs"]).to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Repairs_{today_date}.csv",
                use_container_width=True,
            )
            st.download_button(
                "📥 إكسل الوجبات (CSV)",
                data=pd.DataFrame(db["meals"]).to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Meals_{today_date}.csv",
                use_container_width=True,
            )
