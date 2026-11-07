import hmac
import math
import urllib.parse
from datetime import datetime
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (RTL / Dark Mode)
# ==============================================================================
st.set_page_config(
    page_title="سكن جامعة 3 | العمليات الميدانية",
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
    padding-top: 0.4rem !important; 
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
    padding: 10px 14px; 
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
.done-tag {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #6ee7b7;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76em;
    font-weight: 800;
}
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
}
.wa-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 900;
    text-decoration: none !important;
    margin-top: 6px;
    margin-bottom: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت العامة وقاعدة البيانات والاتصال
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

if "contacts" not in st.session_state:
    st.session_state["contacts"] = {
        "المدير عمر": "966500000000",
        "المشرف الزميل": "966550000000",
        "مقاول الصيانة": "966520000000",
        "متعهد الإعاشة": "966530000000",
    }

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {
            "room": "405",
            "item": "شفاط",
            "opened_at": "08:15 م",
            "date": "2026-11-07",
            "closed_at": None,
            "status": "مفتوح",
        }
    ]

if "violations_db" not in st.session_state:
    st.session_state["violations_db"] = []

if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

if "last_action_wa" not in st.session_state:
    st.session_state["last_action_wa"] = {}

if "is_supervisor" not in st.session_state:
    st.session_state["is_supervisor"] = False

# ==============================================================================
# 3. مكون برمجي مدمج للإرسال اللحظي عبر واتساب (Reusable Component)
# ==============================================================================
def render_instant_whatsapp_box(message_text: str, default_contact: str, key_suffix: str):
    """صندوق تفاعلي سريع يولد رابط الواتساب مباشرة للمستلم المطلوب"""
    st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
    st.markdown("📲 **إرسال البلاغ مباشرة عبر واتساب:**")
    
    contacts = st.session_state["contacts"]
    contact_list = list(contacts.keys()) + ["رقم مخصص (يدوي)"]
    
    def_idx = contact_list.index(default_contact) if default_contact in contact_list else 0
    
    c_sel, c_num = st.columns([1.2, 1])
    with c_sel:
        recipient = st.selectbox(
            "المستلم:",
            contact_list,
            index=def_idx,
            key=f"recip_{key_suffix}"
        )
        
    if recipient == "رقم مخصص (يدوي)":
        with c_num:
            phone_to_use = st.text_input("أدخل الرقم:", placeholder="9665xxxxxxxx", key=f"custom_{key_suffix}")
    else:
        phone_to_use = contacts.get(recipient, "")
        with c_num:
            st.text_input("الرقم:", value=phone_to_use, disabled=True, key=f"dis_{key_suffix}")

    st.text_area("نص الرسالة التلقائي:", value=message_text, height=110, key=f"txt_{key_suffix}")

    if phone_to_use and phone_to_use.strip():
        encoded = urllib.parse.quote(message_text)
        wa_link = f"https://wa.me/{phone_to_use.strip()}?text={encoded}"
        st.markdown(
            f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 إرسال فوري إلى {recipient} الآن</a>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("يرجى إدخال رقم هاتف صالح للإرسال.")
    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 4. التوقيت وترويسة التطبيق
# ==============================================================================
now = datetime.now()
now_minutes = now.hour * 60 + now.minute

if now_minutes < 570:
    auto_meal_idx = 0
elif now_minutes < 990:
    auto_meal_idx = 1
else:
    auto_meal_idx = 2

st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 إدارة {LOCATION_TAG}</div>
    <div class="sub-headline">العمليات الميدانية • التوثيق الآني • مركز الإرسال الفوري</div>
</div>
""",
    unsafe_allow_html=True,
)

c_head1, c_head2 = st.columns([2, 1])
with c_head1:
    st.caption(f"📅 اليوم: {now.strftime('%Y-%m-%d | %I:%M %p')}")
with c_head2:
    if st.button("🔄 تحديث الشاشة", use_container_width=True):
        st.rerun()

tab_repairs, tab_meals, tab_viol, tab_summary, tab_vault = st.tabs(
    [
        "🛠️ الصيانة الفورية",
        "🍽️ الإعاشة والقرار",
        "⚠️ المخالفات والنظافة",
        "📋 تقرير آخر اليوم",
        "🔐 الأدمن والأرقام",
    ]
)

# ------------------------------------------------------------------------------
# 1. تبويب الصيانة: بلاغ فوري (شفاط، مكيف...) + إغلاق بلمسة + واتساب فوري
# ------------------------------------------------------------------------------
with tab_repairs:
    st.markdown("##### 🛠️ تسجيل بلاغ عطل / صيانة جديد:")

    with st.form("repair_instant_form", clear_on_submit=False):
        c_r1, c_r2 = st.columns([1, 1.3])
        with c_r1:
            r_room = st.text_input("رقم الغرفة:", placeholder="مثال: 405")
        with c_r2:
            r_item = st.selectbox(
                "نوع العطل:",
                ["شفاط 💨", "مكيف ❄️", "شطاف / سباكة 🚿", "كهرباء / إنارة 💡", "أخرى 📝"],
            )

        other_text = ""
        if "أخرى" in r_item:
            other_text = st.text_input("حدد العطل بالتفصيل:", placeholder="مثال: قفل الباب / ماس كهربائي...")

        btn_submit_repair = st.form_submit_button("⚡ حفظ البلاغ وتجهيز رسالة الواتساب")

        if btn_submit_repair:
            clean_room = r_room.strip()
            chosen_item = other_text.strip() if ("أخرى" in r_item and other_text.strip()) else r_item.split()[0]

            if not clean_room:
                st.error("يرجى كتابة رقم الغرفة.")
            else:
                log_time = datetime.now().strftime("%I:%M %p")
                log_date = datetime.now().strftime("%Y-%m-%d")

                st.session_state["maintenance_db"].append({
                    "room": clean_room,
                    "item": chosen_item,
                    "opened_at": log_time,
                    "date": log_date,
                    "closed_at": None,
                    "status": "مفتوح",
                })

                # تجهيز رسالة الواتساب الفورية للبلاغ
                msg = f"""السلام عليكم ورحمة الله،،
بلاغ صيانة عاجل - {LOCATION_TAG}:

🛠️ العطل: {chosen_item}
🚪 رقم الغرفة: {clean_room}
⏰ توقيت البلاغ: {log_time}
📅 التاريخ: {log_date}

يرجى المعالجة السريعة والإفادة فور الإصلاح."""

                st.session_state["last_action_wa"]["repair_open"] = {
                    "msg": msg,
                    "default_to": "مقاول الصيانة",
                }
                st.success(f"تم حفظ بلاغ {chosen_item} غرفة {clean_room} بنجاح!")

    # إظهار صندوق الواتساب المباشر للبلاغ المسجل للتو
    if "repair_open" in st.session_state["last_action_wa"]:
        data = st.session_state["last_action_wa"]["repair_open"]
        render_instant_whatsapp_box(data["msg"], data["default_to"], key_suffix="rep_open")

    st.markdown("---")
    st.markdown("##### 📋 بلاغات الصيانة المعلقة:")

    open_items = [x for x in st.session_state["maintenance_db"] if x.get("status") == "مفتوح"]
    if open_items:
        for idx, row in enumerate(open_items):
            r_num = row.get("room")
            r_it = row.get("item")
            r_op = row.get("opened_at")
            r_dt = row.get("date")

            st.markdown(
                f"""
                <div class="stat-box">
                    <b>غرفة {r_num}</b> — <span style="color:var(--primary); font-weight:800;">{r_it}</span><br>
                    <small style="color:#94a3b8;">📅 التاريخ: {r_dt} | ⏰ وقت التسجيل: {r_op}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_btn1, c_btn2 = st.columns([1.2, 1])
            with c_btn1:
                if st.button(f"✅ تم إصلاح {r_it} (غرفة {r_num})", key=f"done_{idx}"):
                    row["status"] = "تم الإصلاح"
                    row["closed_at"] = datetime.now().strftime("%I:%M %p")
                    
                    # إشعار الإنجاز الفوري عبر الواتساب
                    done_msg = f"""السلام عليكم ورحمة الله،،
إشعار إنجاز صيانة - {LOCATION_TAG}:

✅ تم الانتهاء من إصلاح: {r_it}
🚪 رقم الغرفة: {r_num}
⏰ وقت البلاغ: {row['opened_at']}
🕒 وقت الإنجاز الفعلي: {row['closed_at']} ({row['date']})

الحالة: تم الإصلاح والفحص بنجاح."""
                    
                    st.session_state["last_action_wa"]["repair_done"] = {
                        "msg": done_msg,
                        "default_to": "المدير عمر",
                    }
                    st.rerun()

            with c_btn2:
                # تذكير سريع بمتابعة هذا العطل المحدد
                remind_msg = f"تذكير صيانة: نرجو سرعة التوجه لغرفة {r_num} لإصلاح ({r_it}) المسجل منذ الساعة {r_op}."
                enc_remind = urllib.parse.quote(remind_msg)
                phone_mnt = st.session_state["contacts"].get("مقاول الصيانة", "")
                st.markdown(f'<a href="https://wa.me/{phone_mnt}?text={enc_remind}" target="_blank" style="font-size:0.85em; color:#38bdf8;">📲 تذكير المقاول</a>', unsafe_allow_html=True)

    else:
        st.info("لا توجد بلاغات صيانة معلقة حالياً.")

    # إذا تم إغلاق بلاغ تظهر رسالة الإنجاز المباشرة
    if "repair_done" in st.session_state["last_action_wa"]:
        st.markdown("###### 🚀 إرسال إشعار الإنجاز:")
        d_data = st.session_state["last_action_wa"]["repair_done"]
        render_instant_whatsapp_box(d_data["msg"], d_data["default_to"], key_suffix="rep_done")

# ------------------------------------------------------------------------------
# 2. تبويب الإعاشة: توثيق الحصص + قرار الطلبية + إرسال فوري لمسؤول الإعاشة
# ------------------------------------------------------------------------------
with tab_meals:
    st.markdown("##### 🍽️ توثيق الوجبة والقرار التشغيلي:")

    with st.form("meal_entry_form", clear_on_submit=False):
        meal_chosen = st.selectbox(
            "نوع الوجبة:",
            ["فطور 🌅 (05:30 ص - 07:00 ص)", "غداء ☀️ (11:30 ص - 02:30 م)", "عشاء 🌙 (05:30 م - 09:00 م)"],
            index=auto_meal_idx,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            deliv = st.number_input("الوجبات الموردة:", min_value=0, max_value=800, value=77)
        with c2:
            coups = st.number_input("المستلم بكوبون:", min_value=0, max_value=800, value=42)
        with c3:
            surp = st.number_input("الفائض بالصواني:", min_value=0, max_value=800, value=0)

        notes = st.text_input("ملاحظات الجودة / المورد:", placeholder="الوجبة ممتازة / تأخر 15 دقيقة...")

        btn_save_meal = st.form_submit_button("⚡ حفظ الوجبة وتوليد رسالة الواتساب")

        actual_distributed = max(0, deliv - surp)
        no_coupon_count = max(0, actual_distributed - coups)
        buffer_calc = math.ceil(actual_distributed * 0.03) if actual_distributed > 0 else 0
        recommended_order = actual_distributed + buffer_calc

        meal_name = meal_chosen.split()[0]
        cur_time = datetime.now().strftime("%I:%M %p")
        cur_date = datetime.now().strftime("%Y-%m-%d")

        if btn_save_meal:
            st.session_state["meals_db"].append({
                "meal_type": meal_name,
                "date": cur_date,
                "time": cur_time,
                "delivered": int(deliv),
                "coupons": int(coups),
                "surplus": int(surp),
                "distributed": int(actual_distributed),
                "recommended": int(recommended_order),
                "notes": notes.strip() if notes.strip() else "سليم ومطابق",
            })

            meal_msg = f"""السلام عليكم ورحمة الله،،
محضر الإعاشة والقرار التشغيلي - {LOCATION_TAG}:

🍽️ الوجبة: {meal_name}
📅 التاريخ: {cur_date} | ⏰ التوقيت: {cur_time}
📦 الكمية الموردة: {deliv}
🎟️ المصروف بكوبون: {coups}
⚠️ المصروف بدون كوبون: {no_coupon_count}
🍲 الفائض المتبقي: {surp}
👥 المستهلك الفعلي: {actual_distributed} شخص.

💡 قرار وتوصية الطلبية القادمة: {recommended_order} وجبة (تغطي كافة الأفراد مع 3% طوارئ لتفادي الهدر).
📝 الملاحظات: {notes.strip() if notes.strip() else 'الوضع سليم'}"""

            st.session_state["last_action_wa"]["meal"] = {
                "msg": meal_msg,
                "default_to": "متعهد الإعاشة",
            }
            st.success(f"تم اعتماد وجبة {meal_name} بنجاح!")

    m1, m2 = st.columns(2)
    m1.metric("المستهلك الفعلي", f"{actual_distributed} وجبة")
    m2.metric("الطلبية المقترحة القادمة", f"{recommended_order} وجبة")

    if "meal" in st.session_state["last_action_wa"]:
        m_data = st.session_state["last_action_wa"]["meal"]
        render_instant_whatsapp_box(m_data["msg"], m_data["default_to"], key_suffix="meal_box")

# ------------------------------------------------------------------------------
# 3. تبويب المخالفات والنظافة: رصد مخالفات العمال، الطبخ، والسخانات
# ------------------------------------------------------------------------------
with tab_viol:
    st.markdown("##### ⚠️ رصد مخالفة (عمال / غرف / نظافة / طبخ):")

    with st.form("viol_full_form", clear_on_submit=False):
        v_target_type = st.radio(
            "الجهة المخالفة:",
            ["عمال النظافة / المتعهد 🧹", "غرفة طالب / ساكن 🚪"],
            horizontal=True
        )

        c_v1, c_v2 = st.columns([1, 1.2])
        with c_v1:
            target_id = st.text_input("رقم الغرفة / اسم العامل أو الموقع:", placeholder="مثال: ممر الدور 2 / غرفة 108")
        with c_v2:
            v_category = st.selectbox(
                "نوع المخالفة:",
                [
                    "عدم نظافة وإهمال الممرات 🗑️",
                    "طبخ في غير الأماكن المخصصة / هيتر 🍳",
                    "استخدام سخان مخالف ⚡",
                    "تأخر عمال النظافة عن الموعد ⏰",
                    "إزعاج ومخالفة الهدوء 📢",
                    "أخرى 📝",
                ]
            )

        v_desc = st.text_input("تفاصيل المخالفة والإجراء الميداني المتخذ:", placeholder="مثال: رصد نفايات متراكمة / تشغيل هيتر...")

        btn_viol_save = st.form_submit_button("⚡ توثيق المخالفة وتجهيز الرسالة")

        if btn_viol_save:
            c_target = target_id.strip() if target_id.strip() else "غير محدد"
            c_cat = v_category.split()[0] + " " + v_category.split()[1]
            t_now = datetime.now().strftime("%I:%M %p")
            d_now = datetime.now().strftime("%Y-%m-%d")

            past_count = sum(
                1 for x in st.session_state["violations_db"]
                if x.get("target") == c_target and x.get("category") == c_cat
            )
            current_count = past_count + 1

            st.session_state["violations_db"].append({
                "target_type": v_target_type,
                "target": c_target,
                "category": c_cat,
                "desc": v_desc.strip() if v_desc.strip() else "تم رصد المخالفة وضبطها ميدانياً",
                "count": current_count,
                "time": t_now,
                "date": d_now,
            })

            viol_msg = f"""إشعار ضبط مخالفة ميدانية - {LOCATION_TAG}:

⚠️ المخالفة: {c_cat}
📍 الجهة / الموقع: {c_target} ({v_target_type})
🔢 التكرار: المرة الـ ({current_count})
📝 التفاصيل: {v_desc.strip() if v_desc.strip() else 'مخالفة للتعليمات'}
⏰ التوقيت: {t_now} | {d_now}

يرجى اتخاذ الإجراء النظامي بحق المخالفين."""

            default_to = "المدير عمر" if "غرفة" in v_target_type else "المشرف الزميل"
            st.session_state["last_action_wa"]["viol"] = {
                "msg": viol_msg,
                "default_to": default_to,
            }
            st.success(f"تم توثيق المخالفة بحق ({c_target}) للمرة الـ {current_count}!")

    if "viol" in st.session_state["last_action_wa"]:
        v_data = st.session_state["last_action_wa"]["viol"]
        render_instant_whatsapp_box(v_data["msg"], v_data["default_to"], key_suffix="viol_box")

    st.markdown("---")
    st.markdown("##### 📋 كشف المخالفات المسجلة اليوم:")
    if st.session_state["violations_db"]:
        for v in reversed(st.session_state["violations_db"][-4:]):
            c_num = v.get("count", 1)
            t_c = "alert-tag" if c_num > 1 else "done-tag"
            st.markdown(
                f"""
                <div class="stat-box" style="border-right: 3px solid #ef4444;">
                    <b>{v.get('target', '')}</b> — <span style="color:#f87171; font-weight:800;">{v.get('category', '')}</span> 
                    <span class='{t_c}'>تكرار {c_num}</span><br>
                    <small style="color:#cbd5e1;">التفاصيل: {v.get('desc', '')}</small><br>
                    <small style="color:#94a3b8;">📅 {v.get('date', '')} | ⏰ {v.get('time', '')}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("سجل المخالفات نظيف.")

# ------------------------------------------------------------------------------
# 4. تبويب تقرير آخر اليوم: تقرير الموقف الشامل لتسليم الوردية
# ------------------------------------------------------------------------------
with tab_summary:
    st.markdown("##### 📋 تقرير الموقف اليومي الشامل (تسليم الوردية):")
    st.caption("تقرير يجمع كافة أحداث الصيانة، الإعاشة، والمخالفات لإرساله للمدير أو المشرف المستلم بلمسة واحدة:")

    today_str = datetime.now().strftime("%Y-%m-%d | %I:%M %p")
    last_meal = st.session_state["meals_db"][-1] if st.session_state["meals_db"] else {
        "meal_type": "عشاء", "time": "08:30 م", "delivered": 77, "coupons": 42, "distributed": 77, "recommended": 77
    }

    open_reps = [x for x in st.session_state["maintenance_db"] if x.get("status") == "مفتوح"]
    done_reps = [x for x in st.session_state["maintenance_db"] if x.get("status") == "تم الإصلاح"]

    open_m_txt = "\n".join([f"  • غرفة {x.get('room')}: {x.get('item')} (مسجل: {x.get('opened_at')})" for x in open_reps]) if open_reps else "  • لا توجد أعطال معلقة."
    done_m_txt = "\n".join([f"  • تم إصلاح {x.get('item')} غرفة {x.get('room')} ({x.get('closed_at')})" for x in done_reps]) if done_reps else "  • لا توجد أعمال مصلحة اليوم."

    all_v = st.session_state["violations_db"]
    v_txt = "\n".join([f"  • {x.get('target')}: {x.get('category')} (تكرار {x.get('count')}) [{x.get('time')}]" for x in all_v[-4:]]) if all_v else "  • الوضع منضبط ولا توجد مخالفات."

    full_daily_report = f"""مساك الله بالخير،،
تقرير الموقف والعمليات المعتمد - {LOCATION_TAG}
التاريخ: {today_str}

1️⃣ الإعاشة والوجبات [{last_meal.get('meal_type')}]:
- وقت الصرف: {last_meal.get('time')}
- المورد: {last_meal.get('delivered')} | المصروف بكوبون: {last_meal.get('coupons')}
- المستهلك الفعلي: {last_meal.get('distributed')} شخص.
💡 التوصية التشغيلية للطلبية القادمة: {last_meal.get('recommended')} وجبة.

2️⃣ الصيانة ({len(open_reps)} معلق / {len(done_reps)} تم إنجازه):
- المعلق حالياً:
{open_m_txt}
- ما تم إنجازه:
{done_m_txt}

3️⃣ النظافة والمخالفات المرصودة:
{v_txt}

الوضع العام بالسكن: منضبط وتحت السيطرة الميدانية الكاملة."""

    render_instant_whatsapp_box(full_daily_report, default_contact="المدير عمر", key_suffix="daily_final")

# ------------------------------------------------------------------------------
# 5. تبويب الأدمن والخزنة وإدارة الأرقام
# ------------------------------------------------------------------------------
with tab_vault:
    st.markdown("##### 🔐 إعدادات أرقام التواصل والأدمن:")

    if not st.session_state["is_supervisor"]:
        pin_in = st.text_input("أدخل رمز المشرف:", type="password")
        if st.button("🔓 فتح الإعدادات", use_container_width=True):
            if hmac.compare_digest(pin_in.strip().encode(), PERMANENT_PIN.encode()):
                st.session_state["is_supervisor"] = True
                st.rerun()
            else:
                st.error("الرمز غير صحيح.")
    else:
        st.success("🟢 لوحة الأدمن مفتوحة.")
        if st.button("🔒 قفل اللوحة"):
            st.session_state["is_supervisor"] = False
            st.rerun()

        st.divider()
        st.markdown("###### ⚙️ تحديث أرقام الواتساب في النظام:")
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            u_mgr = st.text_input("رقم المدير عمر:", value=st.session_state["contacts"].get("المدير عمر", ""))
            u_sup = st.text_input("رقم المشرف الزميل:", value=st.session_state["contacts"].get("المشرف الزميل", ""))
        with c_p2:
            u_mnt = st.text_input("رقم مقاول الصيانة:", value=st.session_state["contacts"].get("مقاول الصيانة", ""))
            u_cat = st.text_input("رقم متعهد الإعاشة:", value=st.session_state["contacts"].get("متعهد الإعاشة", ""))

        if st.button("💾 حفظ الأرقام الجديدة"):
            st.session_state["contacts"]["المدير عمر"] = u_mgr.strip()
            st.session_state["contacts"]["المشرف الزميل"] = u_sup.strip()
            st.session_state["contacts"]["مقاول الصيانة"] = u_mnt.strip()
            st.session_state["contacts"]["متعهد الإعاشة"] = u_cat.strip()
            st.success("تم تحديث جهات الاتصال بنجاح!")
            st.rerun()

        st.divider()
        st.markdown("###### 📥 تنزيل السجلات:")
        if st.session_state["maintenance_db"]:
            df_m = pd.DataFrame(st.session_state["maintenance_db"])
            st.download_button(
                "تحميل سجل الصيانة (Excel/CSV)",
                df_m.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"repairs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
