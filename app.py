import base64
import hmac
import os
import urllib.parse
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الصفحة وتصميم الجوال الميداني (RTL / Dark Mode)
# ==============================================================================
st.set_page_config(
    page_title="المشرف فارس العصيمي | سكن جامعة 3",
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
    max-width: 440px !important; 
    margin: 0 auto !important;
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19 !important; 
    color: #f8fafc !important; 
}
.top-card { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 12px; 
    padding: 12px 14px; 
    margin-bottom: 8px; 
    text-align: center; 
}
.headline { font-size: 1.15em; font-weight: 900; color: #ffffff; margin: 0; }
.sub-headline { font-size: 0.82em; font-weight: 700; color: #94a3b8; margin-top: 4px; }
.badge-admin {
    display: inline-block;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: var(--primary);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75em;
    font-weight: 800;
    margin-top: 4px;
}
div[data-testid="stFormSubmitButton"] > button { 
    background: var(--primary) !important; 
    color: #022c22 !important; 
    font-weight: 900 !important; 
    height: 48px !important; 
    border-radius: 10px !important; 
    width: 100% !important; 
    border: none !important; 
}
.alert-tag {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.5);
    color: #fca5a5;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.74em;
    font-weight: 800;
}
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت الرسمية والرمز السري الدائم
# ==============================================================================
SUPERVISOR_NAME = "فارس العصيمي"
MANAGER_NAME = "عمر"
LOCATION_TAG = "سكن جامعة 3"
MOTTO = "إصرار"
MAINTENANCE_PHONE = "966500000000"

# الرمز السري الدائم والثابت (يمكن تعديل 5050 لأي رقم تريده)
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

# ==============================================================================
# 3. درع الأمان (حظر 10 دقائق عند 3 محاولات خاطئة لمنع التطفل)
# ==============================================================================
if "failed_attempts" not in st.session_state:
    st.session_state["failed_attempts"] = 0
if "lockout_until" not in st.session_state:
    st.session_state["lockout_until"] = None

def is_system_locked() -> bool:
    if st.session_state["lockout_until"]:
        if datetime.now() < st.session_state["lockout_until"]:
            return True
        else:
            st.session_state["lockout_until"] = None
            st.session_state["failed_attempts"] = 0
    return False

# ==============================================================================
# 4. قواعد البيانات المؤقتة (Session State)
# ==============================================================================
if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {"room": "104", "item": "مكيف ❄️", "desc": "لا يبرد", "date": "2026-11-06", "status": "مفتوح"},
        {"room": "104", "item": "شطاف 🚿", "desc": "تهريب من اللي", "date": "2026-11-07", "status": "مفتوح"},
    ]

if "violations_db" not in st.session_state:
    st.session_state["violations_db"] = [
        {"id": "3041", "room": "108", "type": "تعهد إداري 📝", "notes": "إنذار أول للموظف", "date": "2026-11-05 09:15 م"},
    ]

if "rounds_db" not in st.session_state:
    st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
    st.session_state["is_supervisor"] = False

# ==============================================================================
# 5. الترويسة الرسمية
# ==============================================================================
st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 بوابة تشغيل {LOCATION_TAG}</div>
    <div class="sub-headline">المشرف: <b>{SUPERVISOR_NAME}</b> | المدير: <b>{MANAGER_NAME}</b></div>
    <div><span class="badge-admin">شعار العمل: {MOTTO} ⚡</span></div>
</div>
""",
    unsafe_allow_html=True,
)

tab_meals, tab_repairs, tab_violations, tab_rounds, tab_vault = st.tabs([
    "🍽️ الأكل",
    "🛠️ الصيانة",
    "⚠️ المخالفات",
    "🚶 الجولات",
    "🔐 الخزنة"
])

# ------------------------------------------------------------------------------
# 1. تبويب الأكل: الكوبون والفائض فقط
# ------------------------------------------------------------------------------
with tab_meals:
    st.markdown("##### ⏱️ حصر الأكل (كوبون وفائض فقط):")

    with st.form("meal_form_direct", clear_on_submit=False):
        coupons_count = st.number_input("عدد الكوبونات المستلمة:", min_value=0, max_value=600, value=42)
        surplus_count = st.number_input("الفائض المتبقي بالصواني:", min_value=0, max_value=600, value=0)
        meal_note = st.text_input("ملاحظة (اختياري):", placeholder="سجل طبيعي...")

        btn_save_meal = st.form_submit_button("حفظ بيانات الوجبة")

        if btn_save_meal:
            st.session_state["meals_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%I:%M %p"),
                "coupons": int(coupons_count),
                "surplus": int(surplus_count),
                "location": LOCATION_TAG,
                "supervisor": SUPERVISOR_NAME,
                "notes": meal_note.strip() if meal_note.strip() else "سليم"
            })
            st.success("تم تسجيل بيانات الوجبة بنجاح!")

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("المصروف بكوبون", f"{coupons_count} وجبة")
    m2.metric("الفائض بالصواني", f"{surplus_count} وجبة")

# ------------------------------------------------------------------------------
# 2. تبويب الصيانة: مكيف، شطاف، أو أخرى
# ------------------------------------------------------------------------------
with tab_repairs:
    st.markdown("##### 🚨 تسجيل بلاغ صيانة:")

    with st.form("defect_form_direct", clear_on_submit=True):
        room_no = st.text_input("رقم الغرفة (مثال: 104):")
        
        defect_choice = st.radio(
            "اختر العطل:",
            ["مكيف ❄️", "شطاف 🚿", "أخرى 🛠️"],
            horizontal=True
        )

        custom_defect = ""
        if "أخرى" in defect_choice:
            custom_defect = st.text_input("اكتب العطل الآخر بيدك:", placeholder="مثال: فيش كهرباء / سخان / لمبة...")

        defect_desc = st.text_input("وصف العطل:", placeholder="مثال: يقطر ماء / مفصول...")
        btn_save_defect = st.form_submit_button("إدراج البلاغ")

        if btn_save_defect:
            r_clean = room_no.strip()
            final_item = custom_defect.strip() if ("أخرى" in defect_choice and custom_defect.strip()) else defect_choice

            if not r_clean:
                st.error("الرجاء كتابة رقم الغرفة أولاً.")
            else:
                st.session_state["maintenance_db"].append({
                    "room": r_clean,
                    "item": final_item,
                    "desc": defect_desc.strip() if defect_desc.strip() else "عطل تشغيلي",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "مفتوح",
                    "supervisor": SUPERVISOR_NAME
                })
                st.success(f"تم تسجيل بلاغ غرفة {r_clean} ({final_item}).")

    st.markdown("---")
    open_defects = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    if open_defects:
        df_def = pd.DataFrame(open_defects)
        room_reps = df_def["room"].value_counts()
        wa_lines = [f"*تقرير صيانة {LOCATION_TAG} - المشرف {SUPERVISOR_NAME}:*"]

        for idx, row in enumerate(open_defects):
            r_num = row["room"]
            repeats = room_reps.get(r_num, 1)
            repeat_tag = f"<span class='alert-tag'>تكرر {repeats} مرات</span>" if repeats >= 2 else ""

            st.markdown(
                f"""
                <div class="stat-box">
                    <b>غرفة {row['room']}</b> — <span style="color:var(--primary); font-weight:800;">{row['item']}</span> {repeat_tag}<br>
                    <small style="color:#94a3b8;">{row['desc']} | التاريخ: {row['date']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
            wa_lines.append(f"• غرفة {row['room']}: {row['item']} ({row['desc']})")

            if st.button(f"تم إصلاح عطل غرفة {row['room']} ({row['item']})", key=f"fix_btn_{idx}"):
                row["status"] = "تم الإصلاح ✓"
                st.rerun()

        encoded_wa = urllib.parse.quote("\n".join(wa_lines))
        wa_link = f"https://wa.me/{MAINTENANCE_PHONE}?text={encoded_wa}"
        st.markdown(
            f'<a href="{wa_link}" target="_blank" style="display:block; background:#10b981; color:#022c22; text-align:center; padding:12px; border-radius:10px; font-weight:900; text-decoration:none; margin-top:10px;">📲 إرسال البلاغات للصيانة عبر واتساب</a>',
            unsafe_allow_html=True
        )
    else:
        st.info("لا توجد بلاغات صيانة معلقة.")

# ------------------------------------------------------------------------------
# 3. تبويب المخالفات: سخان، تعهد، أو أخرى (دخان وغيره)
# ------------------------------------------------------------------------------
with tab_violations:
    st.markdown("##### ⚠️ توثيق مخالفة أو تعهد:")

    with st.form("violation_form_direct", clear_on_submit=True):
        emp_id = st.text_input("رقم الآيدي (الرقم الوظيفي):", placeholder="مثال: 3041")
        v_room = st.text_input("رقم الغرفة:")

        v_type_choice = st.radio(
            "نوع المخالفة:",
            ["سخان موية / طبخ سخان ⚡", "تعهد إداري 📝", "أخرى ⚠️"],
            horizontal=True
        )

        custom_v_type = ""
        if "أخرى" in v_type_choice:
            custom_v_type = st.text_input("اكتب نوع المخالفة الأخرى بيدك (دخان / إزعاج / غيره):", placeholder="مثال: تدخين بالغرفة...")

        v_details = st.text_input("تفاصيل المخالفة:", placeholder="ملاحظة سريعة...")
        btn_save_viol = st.form_submit_button("تسجيل المخالفة في السجل")

        if btn_save_viol:
            clean_id = emp_id.strip()
            final_viol = custom_v_type.strip() if ("أخرى" in v_type_choice and custom_v_type.strip()) else v_type_choice

            if not clean_id:
                st.error("الرجاء كتابة رقم الآيدي أولاً.")
            else:
                st.session_state["violations_db"].append({
                    "id": clean_id,
                    "room": v_room.strip() if v_room.strip() else "غير محدد",
                    "type": final_viol,
                    "notes": v_details.strip() if v_details.strip() else "تم رصد المخالفة",
                    "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                    "supervisor": SUPERVISOR_NAME
                })
                st.success(f"تم توثيق المخالفة على الموظف ({clean_id}) بنجاح.")

    st.markdown("---")
    st.markdown("##### 📋 سجل المخالفين وكشف السوابق:")
    if st.session_state["violations_db"]:
        df_v = pd.DataFrame(st.session_state["violations_db"])
        id_counts = df_v["id"].value_counts()

        for row in reversed(st.session_state["violations_db"][-4:]):
            rep = id_counts.get(row["id"], 1)
            repeat_badge = f"<span class='alert-tag'>⚠️ سوابق: مسجل {rep} مرات</span>" if rep >= 2 else ""

            st.markdown(
                f"""
                <div class="stat-box" style="border-right: 3px solid #ef4444;">
                    <b>آيدي: {row['id']}</b> (غرفة {row['room']}) {repeat_badge}<br>
                    <span style="color:#f87171; font-weight:800;">{row['type']}</span><br>
                    <small style="color:#94a3b8;">{row['date']} | {row['notes']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("سجل المخالفات نظيف.")

# ------------------------------------------------------------------------------
# 4. تبويب الجولات: جولة صباح (09:30 ص) وجولة ليل (08:30 م)
# ------------------------------------------------------------------------------
with tab_rounds:
    st.markdown("##### 🚶 توثيق الجولتين الميدانيتين:")

    current_hr = datetime.now().hour
    best_round_index = 0 if current_hr < 14 else 1

    with st.form("round_form_direct", clear_on_submit=True):
        selected_round = st.radio(
            "اختر الجولة المعتمدة:",
            ["جولة الصباح (09:30 ص) • نظافة وهدوء شفت الليل", "جولة الليل (08:30 م) • بعد توزيع العشاء والصيانة"],
            index=best_round_index
        )

        r_note = st.text_input("ملاحظات الجولة الميدانية:", placeholder="مثال: التزام كامل بالهدوء والنظافة...")
        btn_save_round = st.form_submit_button("حفظ الجولة")

        if btn_save_round:
            st.session_state["rounds_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%I:%M %p"),
                "round": selected_round.split()[0] + " " + selected_round.split()[1],
                "notes": r_note.strip() if r_note.strip() else "تمت الجولة والسكن هادئ",
                "supervisor": SUPERVISOR_NAME
            })
            st.success("تم توثيق الجولة بنجاح.")

    if st.session_state["rounds_db"]:
        st.markdown("---")
        for r in st.session_state["rounds_db"][-3:]:
            st.markdown(
                f"""
                <div class="stat-box">
                    <b>{r['round']}</b> — <small style="color:var(--primary);">{r['time']}</small><br>
                    <small style="color:#94a3b8;">الملاحظات: {r['notes']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

# ------------------------------------------------------------------------------
# 5. الخزنة الرقمية بالرمز الدائم الثابت (5050)
# ------------------------------------------------------------------------------
with tab_vault:
    st.markdown("##### 🔐 الخزنة الرقمية للمشرف فارس العصيمي:")

    if is_system_locked():
        rem_sec = int((st.session_state["lockout_until"] - datetime.now()).total_seconds())
        st.error(f"⛔ تم إغلاق الخزنة أمنياً بسبب 3 محاولات خاطئة. يرجى الانتظار: {rem_sec} ثانية.")
    elif not st.session_state["is_supervisor"]:
        st.caption("🔒 منطقة آمنة ومشفرة. أدخل رمز المشرف الدائم لفتح السجلات والتقارير:")
        input_code = st.text_input("أدخل رمز المشرف:", type="password")

        if st.button("🔓 فتح الخزنة", use_container_width=True):
            # التحقق بالزمن الثابت مع الرمز الدائم
            if hmac.compare_digest(input_code.strip().encode(), PERMANENT_PIN.encode()):
                st.session_state["is_supervisor"] = True
                st.session_state["failed_attempts"] = 0
                st.rerun()
            else:
                st.session_state["failed_attempts"] += 1
                rem_tries = 3 - st.session_state["failed_attempts"]

                if rem_tries <= 0:
                    st.session_state["lockout_until"] = datetime.now() + timedelta(minutes=10)
                    st.error("🚨 تم حظر النظام لمدة 10 دقائق بعد 3 محاولات خاطئة.")
                    st.rerun()
                else:
                    st.error(f"الرمز غير صحيح! متبقي لديك ({rem_tries}) محاولات قبل الإغلاق الأمني.")
    else:
        st.success(f"🟢 مرحباً يا أبو ربيع ({SUPERVISOR_NAME}) - الخزنة مؤمنة بالكامل.")
        if st.button("🔒 قفل الخزنة والخروج"):
            st.session_state["is_supervisor"] = False
            st.rerun()

        st.divider()

        # محرك البحث الميداني
        st.markdown("###### 🔍 البحث الميداني السريع:")
        search_query = st.text_input("ابحث برقم الآيدي أو الغرفة:", placeholder="مثال: 3041 أو 104...")

        if search_query.strip():
            sq = search_query.strip().lower()
            matching_viol = [v for v in st.session_state["violations_db"] if sq in v.get("id", "").lower() or sq in v.get("room", "").lower()]
            matching_rep = [m for m in st.session_state["maintenance_db"] if sq in m.get("room", "").lower() or sq in m.get("item", "").lower()]

            st.write(f"نتائج البحث عن ({search_query}):")
            for mv in matching_viol:
                st.info(f"⚠️ مخالفة آيدي {mv['id']} (غرفة {mv['room']}): {mv['type']} - {mv['notes']}")
            for mr in matching_rep:
                st.warning(f"🛠️ صيانة غرفة {mr['room']}: {mr['item']} - {mr['desc']} ({mr['status']})")

        st.divider()

        # تصدير ملفات Excel النظيفة والمعتمدة للمدير عمر
        st.markdown(f"###### 📥 تصدير السجلات المعتمدة للإدارة (المدير: {MANAGER_NAME}):")

        if st.session_state["meals_db"]:
            df_m = pd.DataFrame(st.session_state["meals_db"])
            st.download_button(
                label="📊 تحميل كشف الوجبات (الكوبون والفائض) - Excel",
                data=df_m.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Meals_{LOCATION_TAG}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["maintenance_db"]:
            df_r = pd.DataFrame(st.session_state["maintenance_db"])
            st.download_button(
                label="🛠️ تحميل تقرير الصيانة (مكيفات وشطافات) - Excel",
                data=df_r.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Repairs_{LOCATION_TAG}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["violations_db"]:
            df_v = pd.DataFrame(st.session_state["violations_db"])
            st.download_button(
                label="⚠️ تحميل كشف المخالفات والتعهدات - Excel",
                data=df_v.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Violations_{LOCATION_TAG}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
