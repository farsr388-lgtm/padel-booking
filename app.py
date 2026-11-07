import base64
import hmac
import os
import urllib.parse
from datetime import datetime

import pandas as pd
import streamlit as st

# استيراد مكتبة التشفير مع دعم البديل الآمن
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ==============================================================================
# 1. إعداد الصفحة وتصميم الجوال الميداني
# ==============================================================================
st.set_page_config(
    page_title="المشرف السريع | سكن الـ 455",
    page_icon="⚡",
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
.sub-headline { font-size: 0.82em; font-weight: 700; color: #94a3b8; margin-top: 3px; }
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
.warning-live {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.82em;
    font-weight: 800;
    margin-bottom: 10px;
    text-align: center;
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
# 2. إعدادات الأمان وقواعد البيانات
# ==============================================================================
MASTER_KEY = str(st.secrets.get("SUPERVISOR_PIN", "9988")).strip()
MAINTENANCE_PHONE = "966500000000"

if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {"room": "104", "item": "مكيف ❄️", "desc": "لا يبرد", "date": "2026-11-06", "status": "مفتوح"},
        {"room": "104", "item": "شطاف 🚿", "desc": "تهريب من اللي", "date": "2026-11-07", "status": "مفتوح"},
    ]

if "violations_db" not in st.session_state:
    st.session_state["violations_db"] = [
        {"id": "3041", "room": "108", "type": "تدخين داخل السكن 🚭", "action": "تعهد خطي", "date": "2026-11-05 09:15 م", "notes": "إنذار أول"},
        {"id": "3041", "room": "108", "type": "تدخين داخل السكن 🚭", "action": "رفع للإدارة (خصم)", "date": "2026-11-07 10:30 م", "notes": "ضبط متلبس للمرة الثانية"},
    ]

if "rounds_db" not in st.session_state:
    st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
    st.session_state["is_supervisor"] = False

# التعرف التلقائي على الوجبة الحالية حسب ساعة اليوم
curr_hour = datetime.now().hour
if 5 <= curr_hour < 11:
    auto_meal = "فطور"
elif 11 <= curr_hour < 16:
    auto_meal = "غداء"
else:
    auto_meal = "عشاء"

# ==============================================================================
# 3. واجهة التطبيق الرئيسية
# ==============================================================================
st.markdown(
    """
<div class="top-card">
    <div class="headline">⚡ المشرف الميداني السريع</div>
    <div class="sub-headline">تسجيل الوجبات • بلاغات الصيانة • رصد السوابق في ثوانٍ</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_meals, tab_repairs, tab_violations, tab_rounds, tab_vault = st.tabs([
    "🍽️ إقفال وجبة",
    "🛠️ بلاغ صيانة",
    "⚠️ مخالفة موظف",
    "🚶 جولة سريعة",
    "🔐 الخزنة"
])

# ------------------------------------------------------------------------------
# خطوة 1 مبسطة: إقفال الوجبة (كشف الوقت آلياً وحساب الآسيوي تلقائياً)
# ------------------------------------------------------------------------------
with tab_meals:
    st.markdown("##### ⏱️ إقفال الوجبة الحاليّة:")

    with st.form("quick_meal_form", clear_on_submit=False):
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            meal_period = st.selectbox("الوجبة المكتشفة:", ["غداء", "عشاء", "فطور"], index=["غداء", "عشاء", "فطور"].index(auto_meal))
        with c_p2:
            total_delivered = st.number_input("إجمالي المستلم:", min_value=1, max_value=600, value=77)

        c_q1, c_q2 = st.columns(2)
        with c_q1:
            coupons_collected = st.number_input("المصروف بكوبون:", min_value=0, max_value=600, value=42)
        with c_q2:
            leftovers_count = st.number_input("الفائض بالصواني:", min_value=0, max_value=300, value=0)

        arabic_count = st.number_input("عدد الوجبات العربي:", min_value=0, max_value=600, value=2)
        asian_auto = max(0, total_delivered - arabic_count)
        st.caption(f"💡 المحسوب تلقائياً كوجبات آسيوي: **{asian_auto} وجبة**")

        meal_notes = st.text_input("ملاحظة سريعة (اختياري):", placeholder="سجل طبيعي...")

        btn_save_meal = st.form_submit_button("⚡ حفظ الوجبة في ثانية")

        distributed_total = total_delivered - leftovers_count
        no_coupon_count = max(0, distributed_total - coupons_collected)

        if btn_save_meal:
            st.session_state["meals_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%I:%M %p"),
                "meal": meal_period,
                "delivered": int(total_delivered),
                "arabic": int(arabic_count),
                "asian": int(asian_auto),
                "with_coupon": int(coupons_collected),
                "without_coupon": int(no_coupon_count),
                "leftovers": int(leftovers_count),
                "notes": meal_notes.strip() if meal_notes.strip() else "سجل طبيعي"
            })
            st.success(f"تم إقفال وجبة {meal_period} بنجاح!")

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("الموزع فعلياً", f"{distributed_total} وجبة")
    m2.metric("توزع بكوبون", f"{coupons_collected} وجبة")

    m3, m4 = st.columns(2)
    m3.metric("بدون كوبون", f"{no_coupon_count} وجبة", delta=f"{no_coupon_count} إضافي" if no_coupon_count > 0 else "0", delta_color="inverse")
    m4.metric("الفائض بالصواني", f"{leftovers_count} وجبة")

# ------------------------------------------------------------------------------
# خطوة 2 مبسطة: بلاغ صيانة سريع بالأزرار (Chips)
# ------------------------------------------------------------------------------
with tab_repairs:
    st.markdown("##### 🚨 تسجيل بلاغ عطل فوري:")

    with st.form("quick_defect_form", clear_on_submit=True):
        room_no = st.text_input("رقم الغرفة (مثال: 104):")
        
        # أزرار سريعة للأعطال الـ 7 الشائعة
        defect_item = st.radio(
            "اختر القطعة بلمسة واحدة:",
            ["مكيف ❄️", "شطاف 🚿", "فيش كهرباء ⚡", "سخان موية 🔥", "بزبوز 🚰", "مرواش 🚿", "لمبة سقف 💡"],
            horizontal=True
        )

        defect_notes = st.text_input("تفاصيل العطل:", placeholder="مثال: يقطر ماء / محروق...")
        btn_save_defect = st.form_submit_button("⚡ إدراج البلاغ فوراً")

        if btn_save_defect:
            r_clean = room_no.strip()
            if not r_clean:
                st.error("الرجاء كتابة رقم الغرفة.")
            else:
                st.session_state["maintenance_db"].append({
                    "room": r_clean,
                    "item": defect_item,
                    "desc": defect_notes.strip() if defect_notes.strip() else "عطل تشغيلي",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "مفتوح"
                })
                st.success(f"تم تسجيل بلاغ غرفة {r_clean} بنجاح.")

    st.markdown("---")
    open_defects = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    if open_defects:
        df_def = pd.DataFrame(open_defects)
        room_repetition = df_def["room"].value_counts()
        wa_lines = ["*تقرير صيانة السكن المفتوحة:*"]

        for idx, row in enumerate(open_defects):
            r_num = row["room"]
            repeats = room_repetition.get(r_num, 1)
            repeat_badge = f"<span class='alert-tag'>تكرر {repeats} مرات</span>" if repeats >= 2 else ""

            st.markdown(
                f"""
                <div class="stat-box">
                    <b>غرفة {row['room']}</b> — <span style="color:var(--primary); font-weight:800;">{row['item']}</span> {repeat_badge}<br>
                    <small style="color:#94a3b8;">{row['desc']} | تاريخ: {row['date']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
            wa_lines.append(f"• غرفة {row['room']}: {row['item']} ({row['desc']})")

            if st.button(f"تم إصلاح بلاغ غرفة {row['room']} ({row['item']})", key=f"fix_btn_{idx}"):
                row["status"] = "تم الإصلاح ✓"
                st.rerun()

        encoded_wa = urllib.parse.quote("\n".join(wa_lines))
        wa_link = f"https://wa.me/{MAINTENANCE_PHONE}?text={encoded_wa}"
        st.markdown(
            f'<a href="{wa_link}" target="_blank" style="display:block; background:#10b981; color:#022c22; text-align:center; padding:12px; border-radius:10px; font-weight:900; text-decoration:none; margin-top:10px;">📲 إرسال البلاغات للصيانة عبر واتساب</a>',
            unsafe_allow_html=True
        )
    else:
        st.info("لا توجد بلاغات أعطال مفتوحة حالياً بالسكن.")

# ------------------------------------------------------------------------------
# خطوة 3 مبسطة: المخالفات مع كشف لحظي للسوابق بمجرد كتابة الآيدي
# ------------------------------------------------------------------------------
with tab_violations:
    st.markdown("##### ⚠️ تسجيل مخالفة موظف:")

    emp_id_input = st.text_input("أدخل رقم الآيدي للتحقق الفوري من السوابق:", key="live_emp_check")

    # كشف فوري للسوابق بمجرد كتابة الرقم (قبل الضغط على الحفظ)
    if emp_id_input.strip():
        past_records = [v for v in st.session_state["violations_db"] if v["id"] == emp_id_input.strip()]
        if past_records:
            st.markdown(
                f"""
                <div class="warning-live">
                    ⚠️ تنبيه: الموظف مسجل لديه ({len(past_records)}) مخالفات سابقة!<br>
                    آخرها: {past_records[-1]['type']} بتاريخ {past_records[-1]['date']}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.caption("✅ سجل الموظف نظيف ولا توجد سوابق مسجلة.")

    with st.form("quick_violation_form", clear_on_submit=True):
        v_room = st.text_input("رقم الغرفة:")
        
        v_type = st.radio(
            "نوع المخالفة السريعة:",
            [
                "تدخين داخل السكن 🚭",
                "إزعاج وقت نوم شفت الليل 🔊",
                "طبخ كهرباء بالغرفة ⚡",
                "أخرى"
            ],
            horizontal=True
        )

        v_action = st.selectbox(
            "الإجراء المتخذ:",
            ["توقيع تعهد خطي رسمي", "تعهد شفهي", "رفع مذكرة للإدارة (خصم/نقل)", "إنذار أول"]
        )

        v_notes = st.text_input("تفاصيل المخالفة (اختياري):", placeholder="مثال: ضبط متلبس بالتدخين في الشباك...")

        btn_save_violation = st.form_submit_button("🚨 اعتماد المخالفة وتثبيت الوقت")

        if btn_save_violation:
            clean_emp = emp_id_input.strip()
            if not clean_emp:
                st.error("الرجاء كتابة رقم الآيدي أولاً.")
            else:
                st.session_state["violations_db"].append({
                    "id": clean_emp,
                    "room": v_room.strip() if v_room.strip() else "غير محدد",
                    "type": v_type,
                    "action": v_action,
                    "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                    "notes": v_notes.strip() if v_notes.strip() else "تم رصد المخالفة"
                })
                st.success(f"تم توثيق المخالفة على الموظف ({clean_emp}) رسمياً.")
                st.rerun()

# ------------------------------------------------------------------------------
# تبويب 4: الجولات الميدانية بتوثيق سريع
# ------------------------------------------------------------------------------
with tab_rounds:
    st.markdown("##### 🚶 توثيق جولة سريعة:")

    with st.form("round_form", clear_on_submit=True):
        round_period = st.selectbox(
            "فترة الجولة:",
            [
                "جولة المساء (بعد العشاء 8:30 م - 9:30 م)",
                "جولة بعد المغرب (6:30 م - 7:30 م)",
                "جولة الصباح (تفقد النظافة والهدوء)",
                "جولة العصر",
                "جولة طارئة"
            ]
        )
        r_notes = st.text_input("ملاحظة الجولة:", placeholder="مثال: التزام كامل بالهدوء...")
        btn_save_round = st.form_submit_button("⚡ حفظ الجولة")

        if btn_save_round:
            st.session_state["rounds_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "round_type": round_period,
                "logged_time": datetime.now().strftime("%I:%M %p"),
                "notes": r_notes if r_notes else "سليم"
            })
            st.success("تم توثيق الجولة.")

    if st.session_state["rounds_db"]:
        st.markdown("---")
        for r in st.session_state["rounds_db"][-2:]:
            st.markdown(
                f"""
                <div class="stat-box">
                    <b>{r['round_type']}</b> — <small style="color:var(--primary);">{r['logged_time']}</small><br>
                    <small style="color:#94a3b8;">الملاحظات: {r['notes']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

# ------------------------------------------------------------------------------
# تبويب 5: الخزنة المشفرة للمشرف وتصدير Excel
# ------------------------------------------------------------------------------
with tab_vault:
    st.markdown("##### 🔐 الخزنة الرقمية للمشرف:")

    if not st.session_state["is_supervisor"]:
        st.caption("🔒 أدخل رمز المشرف السري (PIN) لاستعراض السجلات وتنزيل التقارير:")
        input_pin = st.text_input("رمز المشرف:", type="password")

        if st.button("🔓 فتح الخزنة المشفرة", use_container_width=True):
            if hmac.compare_digest(input_pin.strip().encode(), MASTER_KEY.encode()):
                st.session_state["is_supervisor"] = True
                st.success("تم فتح الخزنة!")
                st.rerun()
            else:
                st.error("رمز المشرف غير صحيح.")
    else:
        st.success("🟢 الخزنة مفتوحة.")
        if st.button("🔒 قفل الخزنة فوراً"):
            st.session_state["is_supervisor"] = False
            st.rerun()

        st.divider()
        st.markdown("###### 📥 تصدير السجلات الميدانية لـ Excel:")

        if st.session_state["violations_db"]:
            df_v_exp = pd.DataFrame(st.session_state["violations_db"])
            st.download_button(
                label="📑 تحميل كشف المخالفات (Excel)",
                data=df_v_exp.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Violations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["meals_db"]:
            df_m_exp = pd.DataFrame(st.session_state["meals_db"])
            st.download_button(
                label="📊 تحميل سجل الوجبات (Excel)",
                data=df_m_exp.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Meals_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["maintenance_db"]:
            df_r_exp = pd.DataFrame(st.session_state["maintenance_db"])
            st.download_button(
                label="🛠️ تحميل تقرير الصيانة (Excel)",
                data=df_r_exp.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Repairs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
