import hmac
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني فائق السرعة
# ==============================================================================
st.set_page_config(
    page_title="المشرف فارس العصيمي | سكن جامعة 3",
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
    padding-top: 0.4rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 420px !important; 
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
    padding: 10px 14px; 
    margin-bottom: 8px; 
    text-align: center; 
}
.headline { font-size: 1.15em; font-weight: 900; color: #ffffff; margin: 0; }
.sub-headline { font-size: 0.82em; font-weight: 700; color: #94a3b8; margin-top: 3px; }
.badge-admin {
    display: inline-block;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: var(--primary);
    padding: 2px 8px;
    border-radius: 16px;
    font-size: 0.72em;
    font-weight: 800;
}
div[data-testid="stFormSubmitButton"] > button { 
    background: var(--primary) !important; 
    color: #022c22 !important; 
    font-weight: 900 !important; 
    height: 48px !important; 
    border-radius: 10px !important; 
    width: 100% !important; 
    border: none !important; 
    font-size: 1.05em !important;
}
.alert-tag {
    background: rgba(239, 68, 68, 0.25);
    border: 1px solid rgba(239, 68, 68, 0.6);
    color: #fca5a5;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.78em;
    font-weight: 900;
}
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت الرسمية والرمز الدائم (5050)
# ==============================================================================
SUPERVISOR_NAME = "فارس العصيمي"
MANAGER_NAME = "عمر"
LOCATION_TAG = "سكن جامعة 3"
MOTTO = "إصرار"
MAINTENANCE_PHONE = "966500000000"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

# ==============================================================================
# 3. قواعد البيانات المؤقتة
# ==============================================================================
if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {"room": "104", "item": "مكيف ❄️", "date": "2026-11-06", "status": "مفتوح"},
        {"room": "104", "item": "شطاف 🚿", "date": "2026-11-07", "status": "مفتوح"},
    ]

if "violations_db" not in st.session_state:
    st.session_state["violations_db"] = [
        {"room": "108", "type": "سخان ⚡", "count": 1, "date": "2026-11-05 09:15 م"},
        {"room": "108", "type": "سخان ⚡", "count": 2, "date": "2026-11-07 10:30 م"},
    ]

if "rounds_db" not in st.session_state:
    st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
    st.session_state["is_supervisor"] = False

# ==============================================================================
# 4. الترويسة الميدانية
# ==============================================================================
st.markdown(
    f"""
<div class="top-card">
    <div class="headline">⚡ إدارة {LOCATION_TAG}</div>
    <div class="sub-headline">المشرف: <b>{SUPERVISOR_NAME}</b> | المدير: <b>{MANAGER_NAME}</b></div>
    <span class="badge-admin">شعار: {MOTTO}</span>
</div>
""",
    unsafe_allow_html=True,
)

tab_viol, tab_meals, tab_repairs, tab_rounds, tab_vault = st.tabs([
    "⚠️ المخالفات",
    "🍽️ الأكل",
    "🛠️ الصيانة",
    "🚶 الجولات",
    "🔐 الخزنة"
])

# ------------------------------------------------------------------------------
# 1. المخالفات: رقم الغرفة + سخان/نظافة + حساب "المرة الكم" آلياً فوراً
# ------------------------------------------------------------------------------
with tab_viol:
    st.markdown("##### ⚠️ تسجيل مخالفة غرفة:")

    with st.form("quick_viol_form", clear_on_submit=True):
        v_room = st.text_input("رقم الغرفة:", placeholder="مثال: 104")

        v_type = st.radio(
            "نوع المخالفة:",
            ["سخان ⚡", "نظافة 🗑️"],
            horizontal=True
        )

        btn_save_viol = st.form_submit_button("⚡ حفظ المخالفة")

        if btn_save_viol:
            clean_r = v_room.strip()
            if not clean_r:
                st.error("أدخل رقم الغرفة أولاً.")
            else:
                # حساب آلي: المرة الكم لهذه الغرفة ونفس المخالفة
                past_times = sum(
                    1 for v in st.session_state["violations_db"]
                    if v["room"] == clean_r and v["type"] == v_type
                )
                current_count = past_times + 1

                log_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                st.session_state["violations_db"].append({
                    "room": clean_r,
                    "type": v_type,
                    "count": current_count,
                    "date": log_time,
                    "supervisor": SUPERVISOR_NAME
                })
                st.success(f"تم تسجيل: غرفة {clean_r} ({v_type}) — للمرة الـ ({current_count}) بنجاح!")

    st.markdown("---")
    st.markdown("##### 📋 آخر المخالفات المرصودة بالسكن:")
    if st.session_state["violations_db"]:
        for row in reversed(st.session_state["violations_db"][-4:]):
            count_num = row.get("count", 1)
            badge_color = "alert-tag" if count_num >= 2 else "badge-admin"
            st.markdown(
                f"""
                <div class="stat-box" style="border-right: 3px solid #ef4444;">
                    <b>غرفة {row['room']}</b> — <span style="color:#f87171; font-weight:800;">{row['type']}</span> 
                    <span class='{badge_color}'>المرة الـ {count_num}</span><br>
                    <small style="color:#94a3b8;">التوقيت: {row['date']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("لا توجد مخالفات مسجلة.")

# ------------------------------------------------------------------------------
# 2. الأكل: كم وجبة جات + كوبون + فائض (بأقل إدخال)
# ------------------------------------------------------------------------------
with tab_meals:
    st.markdown("##### 🍽️ حصر وجبة اليوم:")

    with st.form("quick_meal_form", clear_on_submit=False):
        c_in1, c_in2, c_in3 = st.columns(3)
        with c_in1:
            delivered = st.number_input("جات:", min_value=0, max_value=600, value=77)
        with c_in2:
            coupons = st.number_input("كوبون:", min_value=0, max_value=600, value=42)
        with c_in3:
            surplus = st.number_input("فائض:", min_value=0, max_value=600, value=0)

        btn_save_meal = st.form_submit_button("⚡ حفظ الوجبة")

        distributed = max(0, delivered - surplus)
        no_coupon = max(0, distributed - coupons)

        if btn_save_meal:
            st.session_state["meals_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%I:%M %p"),
                "delivered": int(delivered),
                "coupons": int(coupons),
                "surplus": int(surplus),
                "distributed": int(distributed),
                "no_coupon": int(no_coupon),
                "supervisor": SUPERVISOR_NAME
            })
            st.success("تم حفظ الأكل بنجاح!")

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("الموزع فعلياً", f"{distributed} وجبة")
    m2.metric("بدون كوبون", f"{no_coupon} وجبة", delta=f"{no_coupon}" if no_coupon > 0 else "0", delta_color="inverse")

# ------------------------------------------------------------------------------
# 3. الصيانة: رقم الغرفة + مكيف / شطاف / أخرى
# ------------------------------------------------------------------------------
with tab_repairs:
    st.markdown("##### 🛠️ بلاغ صيانة سريع:")

    with st.form("quick_repair_form", clear_on_submit=True):
        rep_room = st.text_input("رقم الغرفة:", placeholder="مثال: 204")
        
        rep_item = st.radio(
            "القطعة:",
            ["مكيف ❄️", "شطاف 🚿", "أخرى 🛠️"],
            horizontal=True
        )

        other_text = ""
        if "أخرى" in rep_item:
            other_text = st.text_input("اكتب العطل:", placeholder="مثال: لمبة / فيش...")

        btn_save_rep = st.form_submit_button("⚡ إدراج البلاغ")

        if btn_save_rep:
            clean_rr = rep_room.strip()
            final_item = other_text.strip() if ("أخرى" in rep_item and other_text.strip()) else rep_item

            if not clean_rr:
                st.error("أدخل رقم الغرفة.")
            else:
                st.session_state["maintenance_db"].append({
                    "room": clean_rr,
                    "item": final_item,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "مفتوح"
                })
                st.success(f"تم إدراج بلاغ غرفة {clean_rr} ({final_item}).")

    st.markdown("---")
    open_reps = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    if open_reps:
        df_r = pd.DataFrame(open_reps)
        room_reps = df_r["room"].value_counts()
        wa_lines = [f"*بلاغات صيانة {LOCATION_TAG} - المشرف {SUPERVISOR_NAME}:*"]

        for idx, row in enumerate(open_reps):
            r_id = row["room"]
            repeats = room_reps.get(r_id, 1)
            repeat_tag = f"<span class='alert-tag'>تكرر {repeats} مرات</span>" if repeats >= 2 else ""

            st.markdown(
                f"""
                <div class="stat-box">
                    <b>غرفة {row['room']}</b> — <span style="color:var(--primary); font-weight:800;">{row['item']}</span> {repeat_tag}
                </div>
                """,
                unsafe_allow_html=True
            )
            wa_lines.append(f"• غرفة {row['room']}: {row['item']}")

            if st.button(f"تم إصلاح غرفة {row['room']} ({row['item']})", key=f"rep_btn_{idx}"):
                row["status"] = "تم الإصلاح ✓"
                st.rerun()

        encoded_wa = urllib.parse.quote("\n".join(wa_lines))
        wa_link = f"https://wa.me/{MAINTENANCE_PHONE}?text={encoded_wa}"
        st.markdown(
            f'<a href="{wa_link}" target="_blank" style="display:block; background:#10b981; color:#022c22; text-align:center; padding:12px; border-radius:10px; font-weight:900; text-decoration:none; margin-top:8px;">📲 إرسال البلاغات للواتساب دفعة واحدة</a>',
            unsafe_allow_html=True
        )
    else:
        st.info("لا توجد بلاغات معلقة.")

# ------------------------------------------------------------------------------
# 4. الجولات: صباح (09:30 ص) وليل (08:30 م) بلمسة واحدة
# ------------------------------------------------------------------------------
with tab_rounds:
    st.markdown("##### 🚶 توثيق الجولة:")

    current_hr = datetime.now().hour
    best_round_index = 0 if current_hr < 14 else 1

    selected_round = st.radio(
        "اختر الجولة المعتمدة:",
        ["جولة الصباح (09:30 ص)", "جولة الليل (08:30 م)"],
        index=best_round_index,
        horizontal=True
    )

    if st.button("⚡ اعتماد الجولة بنجاح", use_container_width=True):
        st.session_state["rounds_db"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%I:%M %p"),
            "round": selected_round,
            "status": "تمت بنجاح وتفقد السكن سليم",
            "supervisor": SUPERVISOR_NAME
        })
        st.success(f"تم توثيق {selected_round} رسمياً.")

    if st.session_state["rounds_db"]:
        st.markdown("---")
        for r in st.session_state["rounds_db"][-2:]:
            st.markdown(
                f"""
                <div class="stat-box">
                    <b>{r['round']}</b> — <small style="color:var(--primary);">{r['time']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

# ------------------------------------------------------------------------------
# 5. الخزنة المشفرة وتصدير Excel للمدير عمر بالرمز الثابت (5050)
# ------------------------------------------------------------------------------
with tab_vault:
    st.markdown("##### 🔐 الخزنة الرقمية للمشرف فارس العصيمي:")

    if not st.session_state["is_supervisor"]:
        input_code = st.text_input("أدخل رمز المشرف:", type="password")

        if st.button("🔓 فتح الخزنة", use_container_width=True):
            if hmac.compare_digest(input_code.strip().encode(), PERMANENT_PIN.encode()):
                st.session_state["is_supervisor"] = True
                st.rerun()
            else:
                st.error("رمز المشرف غير صحيح.")
    else:
        st.success(f"🟢 مرحباً يا أبو ربيع ({SUPERVISOR_NAME}) - الخزنة مؤمنة.")
        if st.button("🔒 قفل الخزنة"):
            st.session_state["is_supervisor"] = False
            st.rerun()

        st.divider()
        st.markdown(f"###### 📥 تصدير السجلات المعتمدة للإدارة (المدير: {MANAGER_NAME}):")

        if st.session_state["violations_db"]:
            df_v = pd.DataFrame(st.session_state["violations_db"])
            st.download_button(
                label="⚠️ تحميل سجل المخالفات (الغرف والتكرار) - Excel",
                data=df_v.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Violations_{LOCATION_TAG}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["meals_db"]:
            df_m = pd.DataFrame(st.session_state["meals_db"])
            st.download_button(
                label="📊
