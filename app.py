from datetime import datetime
import hmac
import math
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (RTL / Dark Mode / 430px)
# ==============================================================================
st.set_page_config(
    page_title="سكن جامعة 3 | عمليات المشرف",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
    color-scheme: dark;
    --primary: #10b981;
    --card-bg: #111827;
    --border-color: rgba(255, 255, 255, 0.12);
}
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 430px !important; 
    margin: 0 auto !important;
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19 !important; 
    color: #f8fafc !important; 
}
.header-card { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 12px; 
    padding: 12px; 
    margin-bottom: 10px; 
    text-align: center; 
}
.headline { font-size: 1.15em; font-weight: 900; color: #ffffff; margin: 0; }
.sub-headline { font-size: 0.8em; font-weight: 700; color: #94a3b8; margin-top: 3px; }
div[data-testid="stFormSubmitButton"] > button, div.stButton > button { 
    background: var(--primary) !important; 
    color: #022c22 !important; 
    font-weight: 900 !important; 
    height: 46px !important; 
    border-radius: 10px !important; 
    width: 100% !important; 
    border: none !important; 
    font-size: 1.02em !important; 
}
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9px;
    padding: 10px 12px;
    margin-bottom: 7px;
}
.sla-green {
    background: rgba(16, 185, 129, 0.18);
    border: 1.5px solid #10b981;
    color: #6ee7b7;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.sla-yellow {
    background: rgba(245, 158, 11, 0.18);
    border: 1.5px solid #f59e0b;
    color: #fcd34d;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.sla-red {
    background: rgba(239, 68, 68, 0.22);
    border: 1.5px solid #ef4444;
    color: #fca5a5;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.badge-green {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #6ee7b7;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76em;
    font-weight: 800;
}
.badge-yellow {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid rgba(245, 158, 11, 0.6);
    color: #fcd34d;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76em;
    font-weight: 800;
}
.badge-red {
    background: rgba(239, 68, 68, 0.25);
    border: 1px solid rgba(239, 68, 68, 0.6);
    color: #fca5a5;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76em;
    font-weight: 800;
}
.wa-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 10px;
    font-weight: 900;
    font-size: 1.02em;
    text-decoration: none !important;
    margin-top: 8px;
    margin-bottom: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت وقواعد بيانات الوردية (سكن جامعة 3 فقط)
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

now = datetime.now()
now_str = now.strftime("%Y-%m-%d | %I:%M %p")
now_minutes = now.hour * 60 + now.minute
is_friday = now.weekday() == 4

if "morning_round_note" not in st.session_state:
    st.session_state["morning_round_note"] = (
        "تم التفتيش الصباحي، الممرات نظيفة، والوضع العام منضبط"
    )

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {
            "location": "السطح",
            "item": "صنبور / بزبوز موية",
            "desc": "تهريب شديد ويبق موية بقوة",
            "time": "10:15 ص",
            "status": "مفتوح",
            "closed_at": None,
            "photo": None,
        },
        {
            "location": "غرفة 104",
            "item": "مكيف",
            "desc": "تنقيط ماء وتجمع أوساخ تحت الوحدة",
            "time": "09:30 ص",
            "status": "مفتوح",
            "closed_at": None,
            "photo": None,
        },
    ]

if "violations_db" not in st.session_state:
    st.session_state["violations_db"] = [
        {
            "location": "غرفة 108",
            "type": "سخان / هيتر طبخ",
            "desc": "تشغيل هيتر طبخ على الأرض (خطر حريق)",
            "count": 2,
            "time": "09:15 م",
            "photo": None,
        }
    ]

if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

# ==============================================================================
# 3. محرك مواعيد الأكل الرسمية وحساب التأخير
# ==============================================================================
MEAL_SPECS = {
    "فطور": {"target_mins": 330, "official_str": "05:30 ص", "def_h": 5, "def_m": 30, "def_ampm": 0},
    "غداء": {"target_mins": 690, "official_str": "11:30 ص", "def_h": 11, "def_m": 30, "def_ampm": 0},
    "عشاء": {"target_mins": 1050, "official_str": "05:30 م", "def_h": 5, "def_m": 30, "def_ampm": 1},
}

if now_minutes < 570:
    default_meal_idx = 0
elif now_minutes < 990:
    default_meal_idx = 1
else:
    default_meal_idx = 2

# ==============================================================================
# 4. الترويسة والتبويبات الـ 3 المختصرة (انكماش وتركيز 100%)
# ==============================================================================
st.markdown(
    f"""
<div class="header-card">
    <div class="headline">🏢 عمليات {LOCATION_TAG}</div>
    <div class="sub-headline">المشرف: {SUPERVISOR_NAME} • الرقابة الميدانية المباشرة</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_meals, tab_field, tab_report = st.tabs([
    "🍽️ 1. الأكل وموعد وصوله",
    "🛠️ 2. الصيانة والمخالفات",
    "📲 3. تقرير الواتساب والخزنة",
])

# ------------------------------------------------------------------------------
# التبويب 1: الأكل وموعد وصوله (ساعة الجوال ص/م + ألوان التأخير + الكميات)
# ------------------------------------------------------------------------------
with tab_meals:
    m_choice = st.selectbox(
        "🍲 اختر الوجبة:",
        ["فطور", "غداء", "عشاء"],
        index=default_meal_idx,
    )
    spec = MEAL_SPECS[m_choice]

    st.markdown(f"##### ⏰ متى وصلت وجبة ({m_choice})؟ (الموعد الرسمي: {spec['official_str']})")

    t_col1, t_col2, t_col3 = st.columns([1.2, 1.2, 1.6])
    hours_list = list(range(1, 13))
    mins_list = list(range(0, 60))

    with t_col1:
        arr_hour = st.selectbox("الساعة:", hours_list, index=hours_list.index(spec["def_h"]), key=f"h_{m_choice}")
    with t_col2:
        arr_min = st.selectbox("الدقيقة:", mins_list, index=mins_list.index(spec["def_m"]), format_func=lambda x: f"{x:02d}", key=f"m_{m_choice}")
    with t_col3:
        arr_ampm = st.radio("الفترة:", ["ص (صباحاً 🌅)", "م (مساءً 🌙)"], index=spec["def_ampm"], key=f"ampm_{m_choice}")

    is_pm = "م" in arr_ampm.split()[0]
    hour_24 = (0 if arr_hour == 12 else arr_hour) if not is_pm else (12 if arr_hour == 12 else arr_hour + 12)
    short_ampm = "م" if is_pm else "ص"

    arrival_total_mins = hour_24 * 60 + arr_min
    arrival_formatted = f"{arr_hour:02d}:{arr_min:02d} {short_ampm}"
    delay_minutes = arrival_total_mins - spec["target_mins"]

    # إشارات الألوان حسب التأخير
    if delay_minutes <= 0:
        sla_box_class = "sla-green"
        sla_title = "🟢 وصل في الموعد (التزام ممتاز)"
        sla_detail = f"وصلت الوجبة الساعة <b>{arrival_formatted}</b> في وقتها المحدد دون تأخير."
        sla_report_tag = f"🟢 منضبط (وصل {arrival_formatted})"
    elif 1 <= delay_minutes <= 15:
        sla_box_class = "sla-yellow"
        sla_title = f"🟡 تأخير جزئي ({delay_minutes} دقيقة) - تنبيه للمتعهد"
        sla_detail = f"الموعد الرسمي <b>{spec['official_str']}</b> ووصلت الساعة <b>{arrival_formatted}</b> (تأخير {delay_minutes} د)."
        sla_report_tag = f"🟡 متأخر {delay_minutes} دقيقة (وصل {arrival_formatted} بدل {spec['official_str']})"
    else:
        sla_box_class = "sla-red"
        sla_title = f"🔴 تأخير حرج ({delay_minutes} دقيقة) - يرفع للإدارة"
        sla_detail = f"الموعد الرسمي <b>{spec['official_str']}</b> ووصلت الساعة <b>{arrival_formatted}</b>. تأخير ({delay_minutes} د) يرفع للإدارة لمحاسبة المتعهد."
        sla_report_tag = f"🔴 تأخير حرج {delay_minutes} دقيقة (وصل {arrival_formatted} بدل {spec['official_str']})"

    st.markdown(
        f"""
        <div class="{sla_box_class}">
            <div style="font-weight:900; font-size:1.02em; margin-bottom:3px;">{sla_title}</div>
            <div style="font-size:0.86em;">{sla_detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### 📊 حصر الكميات:")
    c1, c2, c3 = st.columns(3)
    with c1:
        d_in = st.number_input("المستلم (جات):", min_value=0, max_value=600, value=77)
    with c2:
        c_in = st.number_input("بكوبون:", min_value=0, max_value=600, value=42)
    with c3:
        s_in = st.number_input("الفائض بالصواني:", min_value=0, max_value=600, value=0)

    actual_used = max(0, d_in - s_in)
    without_coup = max(0, actual_used - c_in)
    next_order_rec = actual_used + (math.ceil(actual_used * 0.03) if actual_used > 0 else 0)

    meal_note = st.text_input("ملاحظة على الوجبة (اختياري):", placeholder="مثال: سليم / نقص خبز / وصلت باردة...")

    if st.button("⚡ حفظ الوجبة وموعد وصولها"):
        st.session_state["meals_db"].append({
            "meal": m_choice,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "official_time": spec["official_str"],
            "arrival_time": arrival_formatted,
            "delay_mins": max(0, int(delay_minutes)),
            "sla_status": sla_title,
            "sla_report_tag": sla_report_tag,
            "delivered": int(d_in),
            "coupons": int(c_in),
            "surplus": int(s_in),
            "distributed": int(actual_used),
            "no_coupon": int(without_coup),
            "recommended": int(next_order_rec),
            "note": meal_note.strip() if meal_note.strip() else "سليم",
        })
        st.success(f"تم حفظ وجبة {m_choice} (وصول: {arrival_formatted})!")

    k1, k2 = st.columns(2)
    k1.metric("المستهلك الفعلي", f"{actual_used} شخص")
    k2.metric("صرف بدون كوبون", f"{without_coup} وجبة")
    st.info(f"💡 **التوصية للوجبة القادمة:** طلب **{next_order_rec} وجبة** لمنع هدر **{max(0, d_in - next_order_rec)} وجبة**.")

# ------------------------------------------------------------------------------
# التبويب 2: الصيانة والمخالفات والجولة الصباحية
# ------------------------------------------------------------------------------
with tab_field:
    with st.expander("🚶 1. جولة الصباح وحملة نظافة الجمعة", expanded=False):
        round_type = st.radio(
            "الجولة:",
            [
                "جولة الصباح اليومية (09:30 ص)",
                "حملة نظافة الجمعة الصباح 🧹 (غسيل ممرات وتفتيش السطح والسباكة)",
                "جولة المساء (08:30 م)",
            ],
            index=1 if is_friday and now.hour < 12 else 0,
        )
        r_note_in = st.text_input("ملاحظة الجولة:", value=st.session_state["morning_round_note"])
        if st.button("⚡ اعتماد الجولة"):
            st.session_state["morning_round_note"] = f"[{round_type}] {r_note_in}"
            st.success("تم حفظ الجولة!")

    with st.expander("🛠️ 2. تسجيل عطل صيانة أو سباكة (السطح / الغرف)", expanded=True):
        with st.form("form_maint", clear_on_submit=True):
            m_loc = st.text_input("📍 الموقع (رقم غرفة مثل 104 أو اسم مثل: السطح، الممر):", placeholder="مثال: السطح أو 104")
            m_item = st.selectbox(
                "🔧 العطل:",
                [
                    "صنبور / بزبوز موية 🚰 (تهريب / يبق موية)",
                    "مكيف ❄️ (تنقيط ماء / تبريد ضعيف)",
                    "شطاف 🚿 (تهريب / كسر)",
                    "سخان موية 🔥",
                    "نظافة ومخلفات 🗑️",
                    "أخرى 🛠️",
                ],
            )
            m_desc = st.text_input("👁️ الشرح الميداني:", placeholder="مثال: الصنبور مكسور ويبق موية بقوة...")
            m_photo = st.file_uploader("📷 صورة العطل (اختياري):", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("⚡ حفظ بلاغ الصيانة"):
                c_loc = m_loc.strip()
                final_loc = f"غرفة {c_loc}" if c_loc.isdigit() else c_loc
                if c_loc:
                    st.session_state["maintenance_db"].append({
                        "location": final_loc,
                        "item": m_item.split()[0] + " " + m_item.split()[1],
                        "desc": m_desc.strip() if m_desc.strip() else "تم الرصد بالوردية",
                        "time": datetime.now().strftime("%I:%M %p"),
                        "status": "مفتوح",
                        "closed_at": None,
                        "photo": m_photo.getvalue() if m_photo else None,
                    })
                    st.success(f"تم تسجيل بلاغ ({final_loc})!")
                    st.rerun()
                else:
                    st.error("اكتب الموقع أولاً.")

    with st.expander("⚠️ 3. رصد مخالفة غرفة (سخان / نظافة)", expanded=False):
        with st.form("form_viol", clear_on_submit=True):
            v_loc = st.text_input("رقم الغرفة أو الموقع:", placeholder="مثال: 108")
            v_type = st.radio("المخالفة:", ["سخان / هيتر طبخ ⚡", "إهمال نظافة ونفايات 🗑️", "هدر مياه 🚰"], horizontal=True)
            v_desc = st.text_input("التفاصيل:", placeholder="تشغيل هيتر طبخ على الفرش...")
            v_photo = st.file_uploader("📷 صورة الإثبات:", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("⚡ حفظ المخالفة"):
                cv = v_loc.strip()
                fv = f"غرفة {cv}" if cv.isdigit() else cv
                ct = v_type.split()[0]
                if cv:
                    rep_cnt = sum(1 for x in st.session_state["violations_db"] if x.get("location") == fv and ct in x.get("type", "")) + 1
                    st.session_state["violations_db"].append({
                        "location": fv,
                        "type": ct,
                        "desc": v_desc.strip() if v_desc.strip() else "مخالفة تعليمات السكن",
                        "count": rep_cnt,
                        "time": datetime.now().strftime("%I:%M %p"),
                        "photo": v_photo.getvalue() if v_photo else None,
                    })
                    st.success(f"تم رصد مخالفة {fv} — المرة الـ ({rep_cnt})!")
                    st.rerun()
                else:
                    st.error("اكتب رقم الغرفة.")

    st.markdown("---")
    st.markdown("##### 📋 الأعطال المفتوحة (اضغط للإغلاق عند الإصلاح):")
    open_list = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    if open_list:
        for i, r in enumerate(open_list):
            col_a, col_b = st.columns([2.6, 1.4])
            with col_a:
                st.markdown(f"<b>📍 {r['location']}</b>: {r['item']}<br><small style='color:#cbd5e1;'>{r['desc']} ({r['time']})</small>", unsafe_allow_html=True)
                if r.get("photo"):
                    with st.expander("🖼️ عرض الصورة"):
                        st.image(r["photo"], use_container_width=True)
            with col_b:
                if st.button("تم إصلاحه ✓", key=f"fix_{i}"):
                    r["status"] = "تم الإصلاح"
                    r["closed_at"] = datetime.now().strftime("%I:%M %p")
                    st.rerun()
    else:
        st.info("لا توجد أعطال معلقة حالياً.")

# ------------------------------------------------------------------------------
# التبويب 3: تقرير الواتساب الفوري (بدون أرقام) + الخزنة (5050)
# ------------------------------------------------------------------------------
with tab_report:
    st.markdown("##### 📲 تقرير الوردية الميداني (جاهز للإرسال):")

    last_m = st.session_state["meals_db"][-1] if st.session_state["meals_db"] else {
        "meal": m_choice,
        "official_time": spec["official_str"],
        "arrival_time": arrival_formatted,
        "sla_report_tag": sla_report_tag,
        "delivered": int(d_in),
        "coupons": int(c_in),
        "surplus": int(s_in),
        "distributed": int(actual_used),
        "recommended": int(next_order_rec),
        "note": meal_note.strip() if meal_note.strip() else "سليم",
    }

    open_m = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    fixed_m = [x for x in st.session_state["maintenance_db"] if x["status"] == "تم الإصلاح"]

    open_txt = "\n".join([f"  • {x['location']}: {x['item']} ({x['desc']})" for x in open_m]) if open_m else "  • لا توجد أعطال معلقة."
    fixed_txt = "\n".join([f"  • {x['location']}: تم إصلاح {x['item']} ({x.get('closed_at', 'اليوم')})" for x in fixed_m]) if fixed_m else "  • لا توجد صيانات مغلقة اليوم."
    viol_txt = "\n".join([f"  • {v['location']}: {v['type']} (المرة {v['count']}) - {v['desc']}" for v in st.session_state["violations_db"][-4:]]) if st.session_state["violations_db"] else "  • السجل نظيف."

    wa_report = f"""*تقرير الوردية الميداني - {LOCATION_TAG}*
*التاريخ:* {now_str} | *المشرف:* {SUPERVISOR_NAME}
-------------------------------------------
*1️⃣ الجولة التفتيشية والنظافة:*
• {st.session_state['morning_round_note']}

*2️⃣ الإعاشة وموعد التوريد [{last_m['meal']}]:*
• الموعد الرسمي: {last_m['official_time']} | الوصول الفعلي: {last_m['arrival_time']}
• حالة الموعد: {last_m['sla_report_tag']}
• الكميات: المستلم: {last_m['delivered']} | بكوبون: {last_m['coupons']} | الفائض: {last_m['surplus']}
• المستهلك الفعلي: {last_m['distributed']} شخص | ملاحظة: {last_m.get('note', 'سليم')}
💡 *التوصية للوجبة القادمة:* طلب ({last_m['recommended']} وجبة) لمنع الهدر.

*3️⃣ الصيانة والسباكة:*
- المعلق ({len(open_m)}):
{open_txt}
- المنجز ({len(fixed_m)}):
{fixed_txt}

*4️⃣ المخالفات والسلامة:*
{viol_txt}

الوضع العام بالسكن: منضبط وتحت السيطرة.
-------------------------------------------"""

    st.text_area("معاينة التقرير:", value=wa_report, height=260)

    wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_report)}"
    st.markdown(
        f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال التقرير عبر واتساب (اختر الشخص أو القروب من جوالك)</a>',
        unsafe_allow_html=True,
    )

    st.divider()
    with st.expander("🔐 الخزنة وتصدير الإكسل الرسمي (الرمز: 5050)"):
        pin_in = st.text_input("أدخل رمز المشرف:", type="password")
        if hmac.compare_digest(pin_in.strip().encode(), PERMANENT_PIN.encode()):
            st.success("🟢 الخزنة مفتوحة!")
            if st.session_state["meals_db"]:
                st.download_button(
                    "📥 تحميل سجل الإعاشة ومواعيد الوصول (Excel)",
                    data=pd.DataFrame(st.session_state["meals_db"]).to_csv(index=False).encode("utf-8-sig"),
                    file_name="Meals_SLA_Log.csv",
                    use_container_width=True,
                )
            clean_m = [{k: v for k, v in r.items() if k != "photo"} for r in st.session_state["maintenance_db"]]
            st.download_button(
                "📥 تحميل سجل الصيانة (Excel)",
                data=pd.DataFrame(clean_m).to_csv(index=False).encode("utf-8-sig"),
                file_name="Maintenance_Log.csv",
                use_container_width=True,
            )
            clean_v = [{k: v for k, v in r.items() if k != "photo"} for r in st.session_state["violations_db"]]
            st.download_button(
                "📥 تحميل سجل المخالفات (Excel)",
                data=pd.DataFrame(clean_v).to_csv(index=False).encode("utf-8-sig"),
                file_name="Violations_Log.csv",
                use_container_width=True,
            )
        elif pin_in:
            st.error("الرمز غير صحيح.")
