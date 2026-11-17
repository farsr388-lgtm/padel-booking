from datetime import datetime, timedelta, timezone
import hmac
import math
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعدادات السرعة القصوى وتوقيت جدة (تتحمل 470 نزيلاً بصفر ثقل)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
now_ksa = datetime.now(KSA_TZ)
today_date = now_ksa.strftime("%Y-%m-%d")
now_time_str = now_ksa.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")

st.set_page_config(
    page_title="Housing 3 | Maintenance & Ops",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# تصميم خفيف جداً: أزرار مربعة (2x2) + لون قرمزي هادئ مريح للعين بدل الأحمر المرعب
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
    height: 92px !important; font-size: 1.05em !important; font-weight: 900 !important;
    border-radius: 16px !important; width: 100% !important; margin-bottom: 8px !important;
    background: #161f30 !important; color: #f8fafc !important;
    border: 1.5px solid rgba(16, 185, 129, 0.45) !important;
    white-space: pre-line !important; line-height: 1.4 !important;
}
div.stButton > button:active, div.stButton > button:hover {
    background: #10b981 !important; color: #022c22 !important;
}
.box { background: #111827; border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 12px; margin-bottom: 8px; }
.sla-banner { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.5); border-radius: 12px; padding: 10px; text-align: center; margin-bottom: 10px; }
.crimson-box { background: rgba(190, 18, 60, 0.14); border: 1px solid rgba(244, 63, 94, 0.4); border-radius: 12px; padding: 12px; margin-bottom: 8px; color: #fda4af; }
.green { color: #6ee7b7; font-weight: 800; }
.yellow { color: #fcd34d; font-weight: 800; }
.crimson { color: #fda4af; font-weight: 800; }
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
# 2. قاعدة البيانات المشتركة + محرك إدارة المخاطر (منع التكرار واستنتاج الدور)
# ==============================================================================
@st.cache_resource
def get_shared_db():
    return {
        "seq": 103,
        "round_note": "الممرات والسطح نظيفة والوضع مستقر",
        "repairs": [
            {"id": 101, "loc": "السطح", "item": "سباكة", "time": "10:15 ص", "date": today_date, "status": "مفتوح", "pings": 1},
            {"id": 102, "loc": "غ 213 (د2)", "item": "مكيف", "time": "09:30 ص", "date": today_date, "status": "تم الإصلاح", "pings": 1},
            {"id": 103, "loc": "غ 213 (د2)", "item": "مكيف", "time": "11:00 ص", "date": today_date, "status": "مفتوح", "pings": 1},
        ],
        "violations": [
            {"loc": "غ 108 (د1)", "type": "سخان طبخ", "count": 2, "time": "09:15 م"},
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


def format_room_and_floor(raw_txt: str) -> str:
    """استنتاج رقم الدور تلقائياً بمجرد كتابة رقم الغرفة (مثال: 213 -> غ 213 (د2))."""
    clean = raw_txt.strip()
    if clean.isdigit():
        if len(clean) == 3:
            return f"غ {clean} (د{clean[0]})"
        return f"غ {clean}"
    return clean or "عام"


def register_or_deduplicate_ticket(raw_room: str, issue_ar: str):
    """إدارة المخاطر: منع تكرار البلاغ لنفس الغرفة والعطل لحماية السيرفر."""
    loc_formatted = format_room_and_floor(raw_room)
    t_now = datetime.now(KSA_TZ).strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")

    # فحص هل يوجد بلاغ مفتوح لنفس الغرفة ونفس العطل؟
    for r in db["repairs"]:
        if r["loc"] == loc_formatted and r["item"] == issue_ar and r["status"] == "مفتوح":
            r["pings"] = r.get("pings", 1) + 1
            st.session_state["done_ticket"] = {
                "id": r["id"],
                "loc": r["loc"],
                "item": r["item"],
                "time": r["time"],
                "is_duplicate": True,
            }
            return

    # إذا لم يكن مكرراً، يسجل بلاغاً جديداً
    db["seq"] += 1
    tid = db["seq"]
    db["repairs"].append({
        "id": tid,
        "loc": loc_formatted,
        "item": issue_ar,
        "time": t_now,
        "date": today_date,
        "status": "مفتوح",
        "pings": 1,
    })
    if len(db["repairs"]) > 150:
        db["repairs"] = db["repairs"][-150:]

    st.session_state["done_ticket"] = {
        "id": tid,
        "loc": loc_formatted,
        "item": issue_ar,
        "time": t_now,
        "is_duplicate": False,
    }


# ==============================================================================
# 3. واجهة العمال (English + Urdu فقط | شبكة مربعة 2x2 | منع التكرار التلقائي)
# ==============================================================================
st.markdown(
    """
    <div class="box" style="text-align:center;">
        <b style="font-size:1.12em;">🛠️ Maintenance Report | مرمت رپورٹ</b><br>
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
    wa_worker = f"*{LOCATION_TAG} #{tk['id']}*\n{tk['loc']} - {tk['item']} ({tk['time']})"

    if tk.get("is_duplicate"):
        # شاشة إدارة المخاطر: تطمئن العامل أن البلاغ مسجل مسبقاً وقيد التنفيذ دون إضافة حمل على السيرفر
        st.markdown(
            f"""
            <div class="crimson-box" style="text-align:center; padding:18px;">
                <div style="font-size:2.2em;">⏳</div>
                <h3 class="crimson" style="margin:4px 0;">Already Under Progress #{tk['id']}</h3>
                <b style="color:#ffffff;">یہ شکایت پہلے سے درج ہے اور کارروائی جاری ہے</b><br>
                <p style="color:#e2e8f0; font-size:0.9em; margin-top:8px;">
                    📍 <b>{tk['loc']}</b> ({tk['item']})<br>
                    ⏰ Logged at / وقتِ اندراج: <b>{tk['time']}</b><br>
                    Will be completed within 24h • 24 گھنٹے سے پہلے مکمل ہو جائے گی
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
                <h3 class="green" style="margin:4px 0;">Request Received #{tk['id']}</h3>
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

    if room_in.strip():
        detected_preview = format_room_and_floor(room_in)
        st.caption(f"📍 Auto-Detected / خودکار منزل: **{detected_preview}**")

    # شبكة مربعة 2x2 باللغتين الإنجليزية والأوردو فقط لتوفير المساحة
    sq_col1, sq_col2 = st.columns(2)
    with sq_col1:
        if st.button("❄️ AC Issue\nاے سی خراب"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_or_deduplicate_ticket(room_in, "مكيف")
                st.rerun()

        if st.button("💡 Electricity\nبجلی کا مسئلہ"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_or_deduplicate_ticket(room_in, "كهرباء")
                st.rerun()

    with sq_col2:
        if st.button("🚰 Water Leak\nپانی لیکج"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_or_deduplicate_ticket(room_in, "سباكة")
                st.rerun()

        if st.button("🧹 Clean / Pests\nصفائی / کیڑے"):
            if not room_in.strip():
                st.warning("⚠️ Enter Room No / کمرہ نمبر لکھیں")
            else:
                register_or_deduplicate_ticket(room_in, "نظافة")
                st.rerun()

st.divider()

# ==============================================================================
# 4. بوابة المشرف الميداني (فارس العصيمي - الرمز 5050)
# ==============================================================================
with st.expander("🔐 لوحة المشرف الميداني (إدارة الوردية والتقارير)"):
    pin = st.text_input("رمز المشرف:", type="password", key="sup_pin")
    if hmac.compare_digest(pin.strip().encode(), ADMIN_PIN.encode()):
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
        k3.metric("تكرار صيانة", len(repeat_locs))
        if repeat_locs:
            st.markdown(f"<div class='crimson-box'>🔍 <b>تكرار أعطال (مراجعة المقاول):</b> {repeat_str}</div>", unsafe_allow_html=True)

        sub_maint, sub_meals, sub_wa = st.tabs([
            "🛠️ الصيانة والرصد",
            "🍱 الوجبات والتأخير",
            "📲 التقرير المختصر",
        ])

        # --- 1. إدارة الصيانة + رصد المشرف المباشر ---
        with sub_maint:
            st.markdown("###### ➕ رصد المشرف المباشر (يكتشف الدور تلقائياً):")
            c_m1, c_m2 = st.columns([1.3, 1.7])
            sup_loc = c_m1.text_input("الغرفة/الموقع:", placeholder="213 أو السطح")
            sup_item = c_m2.selectbox(
                "البند:",
                ["صنبور يبق ماء", "مكيف", "شطاف", "نظافة الجمعة/ممرات", "مخالفة سخان ⚡", "مخالفة نظافة 🗑️"],
            )
            if st.button("⚡ حفظ في السجل"):
                if sup_loc.strip():
                    floc = format_room_and_floor(sup_loc)
                    if "مخالفة" in sup_item:
                        cnt = sum(1 for v in db["violations"] if v["loc"] == floc) + 1
                        db["violations"].append({"loc": floc, "type": sup_item.replace("مخالفة ", ""), "count": cnt, "time": now_time_str})
                    else:
                        register_or_deduplicate_ticket(sup_loc, sup_item)
                        if "done_ticket" in st.session_state:
                            del st.session_state["done_ticket"]
                    st.success(f"تم الحفظ ({floc})!")
                    st.rerun()

            st.markdown("###### ⏳ قيد التنفيذ حالياً (ضغطة للإغلاق):")
            for idx, r in enumerate(reversed(open_reps)):
                col1, col2 = st.columns([2.6, 1.4])
                ping_badge = f" • استعجال ({r.get('pings', 1)})" if r.get("pings", 1) > 1 else ""
                col1.markdown(
                    f"**#{r['id']} {r['loc']}**: {r['item']} <small>({r['time']}{ping_badge})</small>",
                    unsafe_allow_html=True,
                )
                if col2.button("أُصلح ✓", key=f"fix_{r['id']}_{idx}"):
                    r["status"] = "تم الإصلاح"
                    st.rerun()

        # --- 2. تسجيل الوجبات بألوان هادئة (تأخير الغداء 53 دقيقة) ---
        with sub_meals:
            m_type = st.radio("الوجبة:", ["فطور (05:30 ص)", "غداء (11:30 ص)", "عشاء (05:30 م)"], index=1, horizontal=True)
            clean_m_name = m_type.split()[0]
            off_time = "05:30 ص" if clean_m_name == "فطور" else ("11:30 ص" if clean_m_name == "غداء" else "05:30 م")

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
                st.markdown(f"<div class='crimson-box'>🟣 تأخير {delay_m} د (وصل {arr_str} بدل {off_time})</div>", unsafe_allow_html=True)

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

        # --- 3. التقرير المختصر الصافي ---
        with sub_wa:
            lm = db["meals"][-1]
            delay_label = (
                f"🟢 بالموعد ({lm['arrival']})"
                if lm["delay"] == 0
                else (
                    f"🟡 تأخير {lm['delay']} د ({lm['arrival']})"
                    if lm["delay"] <= 15
                    else f"🟣 تأخير {lm['delay']} د (وصل {lm['arrival']} بدل {lm['official']})"
                )
            )

            open_lines = "\n".join([f"• #{r['id']} {r['loc']}: {r['item']} ({r['time']})" for r in open_reps]) if open_reps else "• لا يوجد"
            fixed_lines = "\n".join([f"• #{r['id']} {r['loc']}: {r['item']} ✓" for r in fixed_reps[-5:]]) if fixed_reps else "• لا يوجد"
            viol_lines = "\n".join([f"• {v['loc']}: {v['type']} ({v['count']})" for v in db["violations"][-4:]]) if db["violations"] else "• لا يوجد"

            short_report = f"""*{LOCATION_TAG} | {today_date}*
*المشرف: فارس العصيمي*

*🍱 {lm['meal']}:* {delay_label}
مستلم {lm['deliv']} | كوبون {lm['coup']} | فائض {lm['surp']} | فعلي {lm['actual']} | طلب قادم {lm['rec']}

*🛠️ صيانة (إنجاز {sla_pct}%):*
قيد التنفيذ ({len(open_reps)}):
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
