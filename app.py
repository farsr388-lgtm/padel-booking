import pandas as pd
import streamlit as st
from datetime import datetime
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة وتصميم الجوال الميداني (Mobile-First Dashboard)
# ==============================================================================
st.set_page_config(
    page_title="المشرف الذكي | إدارة السكن والإعاشة",
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
# 2. الذاكرة التشغيلية وقواعد البيانات
# ==============================================================================
if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {"room": "104", "item": "مكيف", "desc": "تسريب ماء + تبريد ضعيف", "date": "2026-11-06", "status": "مفتوح"},
        {"room": "104", "item": "شطاف", "desc": "تهريب مستمر من الرأس", "date": "2026-11-07", "status": "مفتوح"},
        {"room": "212", "item": "فيش كهرباء", "desc": "محروق بسبب الطبخ", "date": "2026-11-07", "status": "مفتوح"},
        {"room": "301", "item": "سخان مياه", "desc": "محبس الأمان يقطر ماء حار", "date": "2026-11-07", "status": "مفتوح"},
    ]

if "rounds_db" not in st.session_state:
    st.session_state["rounds_db"] = []

# رقم مسؤول الصيانة للواتساب السريع
MAINTENANCE_CONTRACTOR_PHONE = "966500000000"

# ==============================================================================
# 3. الهيدر والتبويبات الميدانية
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
    "🚶 الجولات والأدوات",
    "📊 الأرشيف والتكاليف"
])

# ==============================================================================
# تبويب 1: محرك حساب الأكل بطريقة "العد العكسي" والتكلفة
# ==============================================================================
with tab_meals:
    st.markdown("##### ⏱️ حساب الوجبة في 60 ثانية (العد العكسي):")
    st.caption("لا تعد العمال؛ عدّ الفائض بالصواني والبونات بالصندوق فقط:")

    with st.form("reverse_meal_calc", clear_on_submit=False):
        c_period, c_cost = st.columns(2)
        with c_period:
            period = st.selectbox("الوجبة:", ["غداء (11:30 - 1:30)", "عشاء", "فطور"])
        with c_cost:
            meal_price = st.number_input("سعر الوجبة (ر.س):", value=12.0, step=1.0)

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            delivered_qty = st.number_input("الوجبات الموردة من المتعهد:", min_value=1, max_value=600, value=455)
        with col_in2:
            leftovers_qty = st.number_input("الفائض المتبقي بالصواني بعد انتهاء الوقت:", min_value=0, max_value=300, value=25)

        coupons_found = st.number_input("عدد البونات الموجودة داخل الصندوق:", min_value=0, max_value=600, value=415)
        notes = st.text_input("ملاحظة (مثال: تأخر الشفت / حالات مرضية):", placeholder="اختياري...")

        calc_btn = st.form_submit_button("📊 حساب الأثر المالي واعتماد السجل")

        # الحسابات الهندسية الفورية
        consumed_actual = delivered_qty - leftovers_qty
        leaked_meals = max(0, consumed_actual - coupons_found)
        waste_cost_sar = leftovers_qty * meal_price
        suggested_next_order = (delivered_qty - leftovers_qty) + math.ceil(consumed_actual * 0.03)

        if calc_btn:
            entry_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
            st.session_state["meals_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": entry_time,
                "period": period.split()[0],
                "delivered": int(delivered_qty),
                "consumed": int(consumed_actual),
                "leftovers": int(leftovers_qty),
                "coupons": int(coupons_found),
                "leaked": int(leaked_meals),
                "waste_cost": float(waste_cost_sar),
                "suggested_next": int(suggested_next_order),
                "notes": notes if notes else "سجل طبيعي"
            })
            st.success("تم الحفظ في الأرشيف المالي!")

    # عرض نتائج المعادلة للمشرف
    st.markdown("---")
    st.markdown("##### 📌 التحليل المالي والتشغيلي للدفعة الحالية:")
    
    r1, r2 = st.columns(2)
    r1.metric("المستهلك الفعلي", f"{consumed_actual} وجبة")
    r2.metric("التسريب بدون بون", f"{leaked_meals} وجبة", delta=f"-{leaked_meals}" if leaked_meals > 0 else "0", delta_color="inverse")

    r3, r4 = st.columns(2)
    r3.metric("الهدر المالي بالفائض", f"{waste_cost_sar:.0f} ر.س", delta="خسارة غير مستهلكة", delta_color="inverse")
    r4.metric("الطلبية المقترحة للغد", f"{suggested_next_order} وجبة", delta="توفير ذكي")

    st.info(f"💡 **توصية المشرف لطلبية الغد:** اطلب **{suggested_next_order} وجبة** بدلاً من {delivered_qty}، لتوفير **{delivered_qty - suggested_next_order} وجبة** في اليوم!")

# ==============================================================================
# تبويب 2: إدارة أعطال الغرف الأربعة (مكيف - شطاف - فيش - سخان)
# ==============================================================================
with tab_repairs:
    st.markdown("##### 🚨 تسجيل عطل محدد بالغرفة:")

    with st.form("add_room_issue", clear_on_submit=True):
        room_no = st.text_input("رقم الغرفة (مثلاً: 104):")
        item_type = st.selectbox("القطعة المتعطلة:", ["مكيف", "شطاف", "فيش كهرباء", "سخان مياه"])
        issue_detail = st.text_input("التفاصيل بدقة:", placeholder="مثال: الفيش محترق / الشطاف يسرب من اللي / المكيف ينقط")
        
        save_issue = st.form_submit_button("حفظ البلاغ في السجل")

        if save_issue:
            if not room_no.strip():
                st.error("الرجاء كتابة رقم الغرفة.")
            else:
                st.session_state["maintenance_db"].append({
                    "room": room_no.strip(),
                    "item": item_type,
                    "desc": issue_detail if issue_detail.strip() else "عطل معتاد",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "مفتوح"
                })
                st.success(f"تم إدراج بلاغ غرفة {room_no.strip()} ({item_type}) بنجاح.")

    st.markdown("---")
    st.markdown("##### 📋 قائمة الأعطال المفتوحة وكشف التكرار:")

    open_items = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    if open_items:
        df_m = pd.DataFrame(open_items)
        room_repeats = df_m["room"].value_counts()

        wa_summary_lines = ["*تقرير صيانة السكن اليومي - أعطال معلقة:*"]

        for idx, row in enumerate(open_items):
            r_id = row["room"]
            count = room_repeats.get(r_id, 1)
            repeat_tag = f"<span class='alert-tag'>⚠️ متكرر {count} مرات</span>" if count >= 2 else ""

            st.markdown(
                f"""
                <div class="stat-box">
                    <b>غرفة {row['room']}</b> — <span style="color:var(--primary); font-weight:800;">{row['item']}</span> {repeat_tag}<br>
                    <small style="color:#94a3b8;">{row['desc']} | تاريخ: {row['date']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            wa_summary_lines.append(f"• غرفة {row['room']}: {row['item']} ({row['desc']})")

            if st.button(f"تم إغلاق وإصلاح بلاغ غرفة {row['room']} ({row['item']})", key=f"fix_btn_{idx}"):
                row["status"] = "تم الإصلاح ✓"
                st.rerun()

        # زر الواتساب لإرسال القائمة دفعة واحدة لمقاول الصيانة
        wa_text = "\n".join(wa_summary_lines)
        wa_url = f"https://wa.me/{MAINTENANCE_CONTRACTOR_PHONE}?text={urllib.parse.quote(wa_text)}"
        st.markdown(
            f'<a href="{wa_url}" target="_blank" style="display:block; background:#10b981; color:#022c22; text-align:center; padding:12px; border-radius:10px; font-weight:900; text-decoration:none; margin-top:10px;">📲 إرسال قائمة البلاغات لمقاول الصيانة عبر واتساب</a>',
            unsafe_allow_html=True
        )
    else:
        st.info("لا توجد أعطال معلقة حالياً في السكن.")

# ==============================================================================
# تبويب 3: الجولات الميدانية والأدوات الـ 5
# ==============================================================================
with tab_rounds:
    st.markdown("##### 🚶 كشف الجولات اليومية والأدوات:")
    
    st.markdown("""
    **الأدوات الخمسة الإلزامية معك بالجولة:**
    * [x] **قلم فاحص كهرباء (Test Pen):** لفحص الأفياش في ثانية.
    * [x] **شريط لاصق عريض (Tagging Tape):** لكتابة العطل ولصقه على الباب.
    * [x] **شريط تفلون أبيض + جلد شطاف:** لإصلاح تهريب الشطافات فوراً.
    * [x] **مصباح يدوي / فلاش:** لفحص محابس السخانات ومناور الحمامات.
    * [x] **الجوال (الكاميرا):** توثيق كل عطل بالفيديو لإنهاء تهرب المقاول.
    """)
    st.divider()

    round_type = st.radio("نوع الجولة الحالية:", [
        "جولة الصباح (9:30 ص - 10:30 ص) • هدوء شفت الليل + نظافة الممرات",
        "جولة المساء (8:30 م - 9:15 م) • مطابقة إنجاز الصيانة + نظافة المطبخ"
    ])

    with st.form("round_log_form", clear_on_submit=True):
        corridor_clean = st.checkbox("نظافة الممرات والحمامات مطابقة للمعايير", value=True)
        heaters_safe = st.checkbox("فحص السخانات والأفياش (لا يوجد التماس أو تنقيط)", value=True)
        night_shift_quiet = st.checkbox("الهدوء التام في ممرات شفت الليل", value=True)
        supervisor_notes = st.text_input("ملاحظة سريعة للجولة:")
        
        save_round = st.form_submit_button("اعتماد الجولة في السجل")

        if save_round:
            st.session_state["rounds_db"].append({
                "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "round": round_type.split()[0],
                "cleaning": "سليم" if corridor_clean else "مخالفة نظافة",
                "heaters": "سليم" if heaters_safe else "يوجد خلل سخانات",
                "quiet": "ملتزمون" if night_shift_quiet else "يوجد إزعاج",
                "notes": supervisor_notes if supervisor_notes else "تمت الجولة بنجاح"
            })
            st.success("تم توثيق الجولة واعتمادها رسمياً.")

# ==============================================================================
# تبويب 4: الأرشيف الشامل وتصدير Excel بأقل التكاليف
# ==============================================================================
with tab_archive:
    st.markdown("##### 📥 تصدير تقارير الإدارة لإخلاء المسؤولية:")
    st.caption("ملفات جاهزة بصيغة Excel تحفظ كل ريال وكل بلاغ:")

    if st.session_state["meals_db"]:
        df_meals = pd.DataFrame(st.session_state["meals_db"])
        
        # ملخص مالي تراكمي
        total_waste_sar = df_meals["waste_cost"].sum()
        total_leaked_count = df_meals["leaked"].sum()

        st.markdown(f"""
        <div class="stat-box" style="border-color:var(--primary);">
            <b>الخلاصة المالية المحسوبة:</b><br>
            • إجمالي تكلفة الوجبات المهدورة بالفائض: <b style="color:#ef4444;">{total_waste_sar:.1f} ر.س</b><br>
            • إجمالي الوجبات المسربة بدون بون: <b>{total_leaked_count} وجبة</b>
        </div>
        """, unsafe_allow_html=True)

        csv_meals = df_meals.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📊 تحميل سجل الإعاشة والتكاليف اليومية (Excel)",
            data=csv_meals,
            file_name=f"Meals_Waste_Control_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    if st.session_state["maintenance_db"]:
        df_repairs = pd.DataFrame(st.session_state["maintenance_db"])
        csv_repairs = df_repairs.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="🛠️ تحميل تقرير صيانة الغرف والمكيفات (Excel)",
            data=csv_repairs,
            file_name=f"Rooms_Repairs_Log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    if st.session_state["rounds_db"]:
        df_rounds = pd.DataFrame(st.session_state["rounds_db"])
        csv_rounds = df_rounds.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="🚶 تحميل سجل الجولات والنظافة (Excel)",
            data=csv_rounds,
            file_name=f"Rounds_Log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
