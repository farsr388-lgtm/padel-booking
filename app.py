import math
import re
import urllib.parse
from datetime import datetime
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الصفحة وضبط الواجهة للجوال
# ==============================================================================
st.set_page_config(
    page_title="المشرف الذكي | سكن الـ 455",
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
    background: rgba(239, 68, 68, 0.18);
    border: 1px solid rgba(239, 68, 68, 0.45);
    color: #fca5a5;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.76em;
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
# 2. إدارة الحالة التشغيلية (Session State)
# ==============================================================================
if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {"room": "104", "item": "مكيف", "desc": "تسريب ماء مستمر", "date": "2026-11-06", "status": "مفتوح"},
        {"room": "104", "item": "شطاف", "desc": "تهريب مياه من اللي", "date": "2026-11-07", "status": "مفتوح"},
        {"room": "212", "item": "فيش كهرباء", "desc": "فيش مفصول", "date": "2026-11-07", "status": "مفتوح"},
    ]

if "rounds_db" not in st.session_state:
    st.session_state["rounds_db"] = []

MAINTENANCE_PHONE = "966500000000"

# ==============================================================================
# 3. واجهة المستخدم الرئيسية
# ==============================================================================
st.markdown(
    """
<div class="top-card">
    <div class="headline">🏢 نظام تشغيل سكن الـ 455 موظفاً</div>
    <div class="sub-headline">العد العكسي للإعاشة • صيانة الغرف • أرشيف Excel</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_meals, tab_repairs, tab_rounds, tab_archive = st.tabs([
    "🍽️ العد العكسي للأكل",
    "🛠️ أعطال الغرف",
    "🚶 الجولات الميدانية",
    "📊 الأرشيف والتكاليف"
])

# ------------------------------------------------------------------------------
# تبويب 1: العد العكسي للإعاشة (حساب الهدر والتسريب وتوفير الميزانية)
# ------------------------------------------------------------------------------
with tab_meals:
    st.markdown("##### ⏱️ الحساب العكسي للوجبة:")
    
    with st.form("reverse_meal_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            period = st.selectbox("الفترة:", ["غداء (11:30 - 1:30)", "عشاء (مساء)", "فطور (صباح)"])
        with c2:
            meal_price = st.number_input("سعر الوجبة التقديري (ر.س):", value=12.0, step=0.5)

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            delivered = st.number_input("المستلم من المتعهد:", min_value=1, max_value=600, value=455)
        with col_in2:
            leftovers = st.number_input("الفائض بالصواني بعد الإغلاق:", min_value=0, max_value=300, value=20)

        coupons = st.number_input("عدد البونات داخل الصندوق:", min_value=0, max_value=600, value=420)
        meal_notes = st.text_input("ملاحظات (شفت ليل / حالات مرضية):", placeholder="اختياري...")

        submitted = st.form_submit_button("📊 حساب الأثر المالي واعتماد السجل")

        # معالجة منطقية آمنة داخل النطاق
        actual_eaten = delivered - leftovers
        unauthorized_meals = max(0, actual_eaten - coupons)
        waste_cost = leftovers * meal_price
        
        # معادلة الأمان: المستهلك الفعلي + 3% هامش طوارئ مجبورة للأعلى
        safety_margin = math.ceil(actual_eaten * 0.03)
        suggested_order = actual_eaten + safety_margin

        if submitted:
            st.session_state["meals_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%I:%M %p"),
                "period": period.split()[0],
                "delivered": int(delivered),
                "consumed": int(actual_eaten),
                "leftovers": int(leftovers),
                "coupons": int(coupons),
                "unauthorized": int(unauthorized_meals),
                "waste_sar": float(waste_cost),
                "suggested_order": int(suggested_order),
                "notes": meal_notes if meal_notes else "لا يوجد"
            })
            st.success("تم الحفظ في الأرشيف المالي بنجاح.")

    # المؤشرات التحليلية الفورية
    st.markdown("---")
    st.markdown("##### 📌 قراءة المؤشرات الحالية:")
    
    m1, m2 = st.columns(2)
    m1.metric("المستهلك الفعلي", f"{actual_eaten} وجبة")
    m2.metric("التسريب بدون بون", f"{unauthorized_meals} وجبة", delta=f"-{unauthorized_meals}" if unauthorized_meals > 0 else "0", delta_color="inverse")

    m3, m4 = st.columns(2)
    m3.metric("تكلفة الفائض غير المستهلك", f"{waste_cost:.0f} ر.س", delta="هدر مالي", delta_color="inverse")
    m4.metric("الطلبية المقترحة للغد", f"{suggested_order} وجبة", delta="توفير ذكي")

    st.info(f"💡 **توصية الغد:** اطلب **{suggested_order} وجبة** بدلاً من {delivered} لتوفير **{delivered - suggested_order} وجبة**.")

# ------------------------------------------------------------------------------
# تبويب 2: أعطال الغرف الأكثر تكراراً (مكيف - شطاف - فيش - سخان)
# ------------------------------------------------------------------------------
with tab_repairs:
    st.markdown("##### 🚨 تسجيل بلاغ صيانة للغرفة:")

    with st.form("repair_entry_form", clear_on_submit=True):
        room_input = st.text_input("رقم الغرفة:")
        broken_category = st.selectbox("العطل المحدد:", ["مكيف", "شطاف", "فيش كهرباء", "سخان مياه"])
        desc_input = st.text_input("وصف العطل:", placeholder="مثال: المكيف يقطر ماء داخل الغرفة / الفيش محروق")

        btn_repair = st.form_submit_button("حفظ البلاغ بالسجل")

        if btn_repair:
            r_clean = room_input.strip()
            if not r_clean:
                st.error("الرجاء تحديد رقم الغرفة.")
            else:
                st.session_state["maintenance_db"].append({
                    "room": r_clean,
                    "item": broken_category,
                    "desc": desc_input if desc_input.strip() else "عطل تشغيلي معتاد",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "مفتوح"
                })
                st.success(f"تم إدراج بلاغ غرفة {r_clean} بنجاح.")

    st.markdown("---")
    st.markdown("##### 📋 البلاغات المفتوحة ومؤشر التكرار:")

    open_repairs = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    if open_repairs:
        df_rep = pd.DataFrame(open_repairs)
        room_counts = df_rep["room"].value_counts()
        wa_lines = ["*تقرير صيانة السكن اليومي - بلاغات معلقة:*"]

        for idx, row in enumerate(open_repairs):
            r_id = row["room"]
            repeats = room_counts.get(r_id, 1)
            alert_badge = f"<span class='alert-tag'>⚠️ متكرر {repeats} مرات</span>" if repeats >= 2 else ""

            st.markdown(
                f"""
                <div class="stat-box">
                    <b>غرفة {row['room']}</b> — <span style="color:var(--primary); font-weight:800;">{row['item']}</span> {alert_badge}<br>
                    <small style="color:#94a3b8;">{row['desc']} | تاريخ: {row['date']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
            wa_lines.append(f"• غرفة {row['room']}: {row['item']} ({row['desc']})")

            if st.button(f"تم إصلاح بلاغ غرفة {row['room']} ({row['item']})", key=f"close_rep_{idx}"):
                row["status"] = "تم الإصلاح ✓"
                st.rerun()

        wa_encoded = urllib.parse.quote("\n".join(wa_lines))
        wa_target = f"https://wa.me/{MAINTENANCE_PHONE}?text={wa_encoded}"
        st.markdown(
            f'<a href="{wa_target}" target="_blank" style="display:block; background:#10b981; color:#022c22; text-align:center; padding:12px; border-radius:10px; font-weight:900; text-decoration:none; margin-top:10px;">📲 إرسال البلاغات دفعة واحدة لمقاول الصيانة عبر واتساب</a>',
            unsafe_allow_html=True
        )
    else:
        st.info("لا توجد بلاغات صيانة معلقة حالياً.")

# ------------------------------------------------------------------------------
# تبويب 3: الجولات الميدانية التفتيشية
# ------------------------------------------------------------------------------
with tab_rounds:
    st.markdown("##### 🚶 توثيق الجولات والتفتيش:")
    
    st.markdown("""
    **حقيبة الجولة (الأدوات الـ 5):**
    * [x] قلم فاحص كهرباء (Test Pen)
    * [x] شريط لاصق عريض (Tagging Tape)
    * [x] شريط تفلون أبيض + جلد شطاف احتياطية
    * [x] مصباح يدوي صغير
    * [x] كاميرا الجوال (توثيق فيديو 3 ثوانٍ)
    """)
    st.divider()

    round_name = st.radio("الجولة:", [
        "جولة الصباح (9:30 ص) • نظافة الممرات + هدوء شفت الليل",
        "جولة المساء (8:30 م) • تدقيق إنجاز الصيانة + نظافة المطبخ"
    ])

    with st.form("round_form", clear_on_submit=True):
        chk_clean = st.checkbox("نظافة الممرات والحمامات مطابقة", value=True)
        chk_heaters = st.checkbox("فحص السخانات والأفياش سليم", value=True)
        chk_quiet = st.checkbox("الهدوء التام بممرات شفت الليل", value=True)
        r_notes = st.text_input("ملاحظات الجولة:")

        btn_round = st.form_submit_button("اعتماد الجولة في السجل")

        if btn_round:
            st.session_state["rounds_db"].append({
                "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "round": round_name.split()[0],
                "cleaning": "سليم" if chk_clean else "مخالف",
                "heaters": "سليم" if chk_heaters else "خلل",
                "quiet": "ملتزمون" if chk_quiet else "إزعاج",
                "notes": r_notes if r_notes else "تمت بنجاح"
            })
            st.success("تم توثيق الجولة رسمياً.")

# ------------------------------------------------------------------------------
# تبويب 4: الأرشيف وتصدير Excel (إخلاء مسؤولية المشرف)
# ------------------------------------------------------------------------------
with tab_archive:
    st.markdown("##### 📥 تصدير البيانات إلى Excel:")

    if st.session_state["meals_db"]:
        df_m_export = pd.DataFrame(st.session_state["meals_db"])
        total_lost_sar = df_m_export["waste_sar"].sum()
        total_leaked = df_m_export["unauthorized"].sum()

        st.markdown(f"""
        <div class="stat-box" style="border-color:var(--primary);">
            <b>الخلاصة المالية التراكمية:</b><br>
            • إجمالي الهدر المالي بالفائض: <b style="color:#ef4444;">{total_lost_sar:.1f} ر.س</b><br>
            • إجمالي الوجبات المصروفة بدون بون: <b>{total_leaked} وجبة</b>
        </div>
        """, unsafe_allow_html=True)

        csv_meals = df_m_export.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📊 تحميل سجل الإعاشة والتكاليف (Excel)",
            data=csv_meals,
            file_name=f"Meals_Archive_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    if st.session_state["maintenance_db"]:
        df_r_export = pd.DataFrame(st.session_state["maintenance_db"])
        csv_rep = df_r_export.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="🛠️ تحميل تقرير الصيانة والغرف (Excel)",
            data=csv_rep,
            file_name=f"Repairs_Archive_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    if st.session_state["rounds_db"]:
        df_rnd_export = pd.DataFrame(st.session_state["rounds_db"])
        csv_rnd = df_rnd_export.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="🚶 تحميل سجل الجولات والنظافة (Excel)",
            data=csv_rnd,
            file_name=f"Rounds_Archive_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
