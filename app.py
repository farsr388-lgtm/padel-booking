import pandas as pd
import streamlit as st
from datetime import datetime, time

# ==============================================================================
# 1. إعداد الصفحة وتنسيق شاشة الجوال الميداني
# ==============================================================================
st.set_page_config(
    page_title="مشرف السكن | إدارة الوجبات وبلاغات الطوارئ",
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
.top-card { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 12px; 
    padding: 12px 14px; 
    margin-bottom: 8px; 
    text-align: center; 
}
.headline { font-size: 1.18em; font-weight: 900; color: #ffffff; margin: 0; }
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
.urgent-tag {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #fca5a5;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75em;
    font-weight: 800;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. قواعد البيانات اللحظية (جلسة العمل الحالية)
# ==============================================================================
if "daily_meals" not in st.session_state:
    st.session_state["daily_meals"] = []

if "emergency_tickets" not in st.session_state:
    st.session_state["emergency_tickets"] = []

if "delivered_target" not in st.session_state:
    st.session_state["delivered_target"] = 455

# ==============================================================================
# 3. الهيدر والمؤشر الزمني لنافذة الوجبات (11:30 إلى 1:30)
# ==============================================================================
now_time = datetime.now().time()
window_start = time(11, 30)
window_end = time(13, 30)
is_window_open = window_start <= now_time <= window_end

status_badge = "🟢 نافذة الوجبات مفتوحة الآن (11:30 - 1:30)" if is_window_open else "⚪ خارج وقت التوزيع الرسمي (11:30 - 1:30)"

st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 بوابة تشغيل السكن الميدانية</div>
    <div class="sub-headline">{status_badge}</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_meals, tab_emergency, tab_export = st.tabs(["🍽️ صرف الوجبات", "🚨 طوارئ ونظافة", "📊 التقرير المرفوع"])

# ==============================================================================
# تبويب 1: صرف الوجبات الميداني (11:30 - 1:30)
# ==============================================================================
with tab_meals:
    st.markdown("##### ⏱️ تسجيل استلام وجبة بالبوابة:")

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        st.session_state["delivered_target"] = st.number_input(
            "إجمالي الوجبات الموردة اليوم:", 
            value=st.session_state["delivered_target"], 
            step=5
        )
    with col_cfg2:
        taken_total = sum(m["qty"] for m in st.session_state["daily_meals"])
        rem_meals = max(0, st.session_state["delivered_target"] - taken_total)
        st.metric("الوجبات المتبقية بالمطبخ", f"{rem_meals} وجبة")

    with st.form("fast_meal_entry", clear_on_submit=True):
        worker_id = st.text_input("رقم الموظف الوظيفي أو اسمه:")
        c_type, c_coupon = st.columns(2)
        with c_type:
            meal_kind = st.selectbox("نوع الوجبة:", ["آسيوي", "عربي"])
        with c_coupon:
            coupon_check = st.radio("وسيلة الاستلام:", ["ببون معتمد ✓", "بدون بون (استثناء)"], horizontal=True)

        m_qty = st.number_input("العدد المستلم:", min_value=1, max_value=5, value=1)
        
        submit_meal = st.form_submit_button("تسجيل الصرف فوراً")

        if submit_meal:
            w_clean = worker_id.strip()
            if not w_clean:
                st.error("الرجاء إدخال رقم الموظف أو اسمه.")
            else:
                # التحقق من عدم التكرار لنفس الموظف
                already_served = [m for m in st.session_state["daily_meals"] if m["worker"].lower() == w_clean.lower()]
                if already_served:
                    st.warning(f"⚠️ الموظف ({w_clean}) مسجل استلامه سابقاً في سجل اليوم!")

                reg_time_str = datetime.now().strftime("%I:%M %p")
                in_slot = "داخل النافذة الرسمية" if is_window_open else "خارج وقت النافذة"

                st.session_state["daily_meals"].append({
                    "worker": w_clean,
                    "meal": meal_kind,
                    "coupon": coupon_check,
                    "qty": int(m_qty),
                    "time": reg_time_str,
                    "window_status": in_slot
                })
                st.success(f"تم تسجيل {m_qty} وجبة ({meal_kind}) للموظف ({w_clean}).")

    st.markdown("---")
    st.markdown("##### 📋 إحصائيات الدفعة الحالية:")
    coupon_count = sum(m["qty"] for m in st.session_state["daily_meals"] if "ببون" in m["coupon"])
    no_coupon_count = sum(m["qty"] for m in st.session_state["daily_meals"] if "بدون" in m["coupon"])
    
    m_c1, m_c2 = st.columns(2)
    m_c1.metric("المصروف ببون", f"{coupon_count}")
    m_c2.metric("المصروف بدون بون", f"{no_coupon_count}")

# ==============================================================================
# تبويب 2: بلاغات الطوارئ ونظافة السكن
# ==============================================================================
with tab_emergency:
    st.markdown("##### 🚨 تسجيل بلاغ عاجل داخل السكن:")

    with st.form("emergency_entry", clear_on_submit=True):
        location = st.text_input("موقع البلاغ (رقم الغرفة / الممر / دورة المياه):")
        incident_type = st.selectbox("نوع الحالة الطارئة:", [
            "تسريب مياه حاد / طفح مجاري",
            "نظافة عاجلة (انسكاب / قمامة متكدسة)",
            "مكيف متوقف نهائياً (حرج)",
            "انقطاع مياه السخان / تماس كهرباء",
            "كسر قفل باب / شباك"
        ])
        priority = st.radio("درجة الأهمية:", ["🔴 طارئ فوري (يتطلب تدخل عاجل)", "🟡 متابعة صيانة عادية"], horizontal=True)
        incident_desc = st.text_input("وصف المشكلة بإيجاز:", placeholder="مثال: تسريب مياه من لي الحمام بالغرفة 204")

        submit_ticket = st.form_submit_button("رفع البلاغ والمطالبة بالصيانة")

        if submit_ticket:
            if not location.strip():
                st.error("الرجاء كتابة رقم الغرفة أو الموقع بدقة.")
            else:
                ticket_id = len(st.session_state["emergency_tickets"]) + 1
                st.session_state["emergency_tickets"].append({
                    "id": ticket_id,
                    "location": location.strip(),
                    "type": incident_type,
                    "priority": priority,
                    "desc": incident_desc if incident_desc.strip() else "لا يوجد وصف إضافي",
                    "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                    "status": "مفتوح (بانتظار الصيانة/النظافة)"
                })
                st.success(f"تم تسجيل البلاغ رقم #{ticket_id} بنجاح.")

    st.markdown("---")
    st.markdown("##### 📌 البلاغات القائمة للمتابعة:")
    open_tickets = [t for t in st.session_state["emergency_tickets"] if "مفتوح" in t["status"]]
    
    if not open_tickets:
        st.info("لا توجد بلاغات طوارئ أو نظافة معلقة حالياً.")
    else:
        for t in open_tickets:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.09); border-radius:8px; padding:10px; margin-bottom:8px;">
                        <b>بلاغ #{t['id']} — {t['location']}</b> <span class="urgent-tag">{t['type']}</span><br>
                        <small style="color:#94a3b8;">الوقت: {t['time']} | {t['desc']}</small>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                if st.button(f"اعتماد إنجاز البلاغ #{t['id']}", key=f"close_{t['id']}"):
                    t["status"] = "تم الحل والنظافة ✓"
                    st.rerun()

# ==============================================================================
# تبويب 3: التقرير التشغيلي المرفوع للإدارة الكبيرة (Export to Excel)
# ==============================================================================
with tab_export:
    st.markdown("##### 📤 التقرير الميداني لإخلاء المسؤولية:")
    st.caption("هذا التقرير يثبت التوزيع الفعلي خلال نافذة (11:30 - 1:30) ويوثق البلاغات وسرعة إغلاقها:")

    if st.session_state["daily_meals"]:
        df_meals = pd.DataFrame(st.session_state["daily_meals"])
        csv_meals = df_meals.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📊 تحميل تقرير الوجبات المستلمة (Excel/CSV)",
            data=csv_meals,
            file_name=f"Meals_Housing_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.caption("لم يتم تسجيل أي وجبات اليوم بعد.")

    if st.session_state["emergency_tickets"]:
        df_tickets = pd.DataFrame(st.session_state["emergency_tickets"])
        csv_tickets = df_tickets.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="🚨 تحميل تقرير طوارئ النظافة والصيانة (Excel/CSV)",
            data=csv_tickets,
            file_name=f"Emergency_Housing_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.caption("لا توجد بلاغات طوارئ مسجلة للتصدير.")
