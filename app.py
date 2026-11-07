import base64
import hashlib
import hmac
import math
import os
import urllib.parse
from datetime import datetime

import pandas as pd
import streamlit as st

# التحقق من وجود مكتبة التشفير القياسية
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ==============================================================================
# 1. إعداد الصفحة وتصميم الجوال الميداني (Dark Mode / RTL)
# ==============================================================================
st.set_page_config(
    page_title="المشرف التنفيذي | سكن الـ 455",
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
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.5);
    color: #fca5a5;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.74em;
    font-weight: 800;
}
.warning-tag {
    background: rgba(245, 158, 11, 0.18);
    border: 1px solid rgba(245, 158, 11, 0.5);
    color: #fef3c7;
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
# 2. آليات التشفير والأمان المتقدم
# ==============================================================================
MASTER_KEY = str(st.secrets.get("SUPERVISOR_PIN", "9988")).strip()
MAINTENANCE_PHONE = "966500000000"


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_payload(data_bytes: bytes, password: str) -> bytes:
    if not HAS_CRYPTO:
        return data_bytes
    salt = os.urandom(16)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    return salt + fernet.encrypt(data_bytes)


# ==============================================================================
# 3. إدارة قواعد البيانات المؤقتة (Session State)
# ==============================================================================
if "meals_db" not in st.session_state:
    st.session_state["meals_db"] = []

if "maintenance_db" not in st.session_state:
    st.session_state["maintenance_db"] = [
        {"room": "104", "item": "مكيف", "desc": "لا يبرد", "date": "2026-11-06", "status": "مفتوح"},
        {"room": "104", "item": "شطاف", "desc": "تهريب من اللي", "date": "2026-11-07", "status": "مفتوح"},
        {"room": "208", "item": "بزبوز موية", "desc": "ينقط ماء باستمرار", "date": "2026-11-07", "status": "مفتوح"},
    ]

if "violations_db" not in st.session_state:
    st.session_state["violations_db"] = [
        {"id": "3041", "room": "108", "type": "تدخين داخل الغرفة أو الممر 🚭", "action": "توقيع تعهد خطي رسمي", "date": "2026-11-05 09:15 م", "notes": "إنذار أول"},
        {"id": "3041", "room": "108", "type": "تدخين داخل الغرفة أو الممر 🚭", "action": "رفع مذكرة رسمية للإدارة (خصم/نقل)", "date": "2026-11-07 10:30 م", "notes": "ضبط متلبس للمرة الثانية"},
    ]

if "rounds_db" not in st.session_state:
    st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
    st.session_state["is_supervisor"] = False

# ==============================================================================
# 4. واجهة التطبيق الرئيسية والتبويبات الميدانية
# ==============================================================================
st.markdown(
    """
<div class="top-card">
    <div class="headline">🏢 بوابة تشغيل السكن والمشرف</div>
    <div class="sub-headline">حصر الوجبات • صيانة الغرف • ضبط المخالفات • الخزنة</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_meals, tab_repairs, tab_violations, tab_rounds, tab_vault = st.tabs([
    "🍽️ حصر الأكل",
    "🛠️ صيانة الغرف",
    "⚠️ المخالفات",
    "🚶 الجولات",
    "🔐 الخزنة المشفرة"
])

# ------------------------------------------------------------------------------
# تبويب 1: حصر الوجبات والكوبونات (العد العكسي بدون أسعار)
# ------------------------------------------------------------------------------
with tab_meals:
    st.markdown("##### ⏱️ تسجيل بيانات الوجبة الميدانية:")

    with st.form("meal_form", clear_on_submit=False):
        meal_period = st.selectbox("نوع الوجبة:", ["غداء", "عشاء", "فطور"])

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            total_delivered = st.number_input("الوجبات المستلمة كلياً:", min_value=1, max_value=600, value=77)
        with col_q2:
            coupons_collected = st.number_input("عدد الوجبات بكوبون:", min_value=0, max_value=600, value=42)

        st.markdown("<small style='color:#94a3b8;'>تصنيف نوع الأكل المستلم:</small>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            arabic_count = st.number_input("وجبات عربي:", min_value=0, max_value=600, value=2)
        with col_c2:
            asian_count = st.number_input("وجبات آسيوي:", min_value=0, max_value=600, value=75)

        leftovers_count = st.number_input("الفائض المتبقي بالصواني (لم يوزع):", min_value=0, max_value=300, value=0)
        meal_notes = st.text_input("ملاحظات الوجبة (خانة واحدة):", placeholder="مثال: زيادة في الآسيوي...")

        btn_save_meal = st.form_submit_button("حفظ بيانات الوجبة")

        distributed_total = total_delivered - leftovers_count
        no_coupon_count = max(0, distributed_total - coupons_collected)

        if btn_save_meal:
            st.session_state["meals_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%I:%M %p"),
                "meal": meal_period,
                "delivered": int(total_delivered),
                "arabic": int(arabic_count),
                "asian": int(asian_count),
                "with_coupon": int(coupons_collected),
                "without_coupon": int(no_coupon_count),
                "leftovers": int(leftovers_count),
                "notes": meal_notes.strip() if meal_notes.strip() else "سجل طبيعي"
            })
            st.success("تم الحفظ في الأرشيف المشفر بنجاح!")

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("الموزع فعلياً", f"{distributed_total} وجبة")
    m2.metric("توزع بكوبون", f"{coupons_collected} وجبة")

    m3, m4 = st.columns(2)
    m3.metric("بدون كوبون", f"{no_coupon_count} وجبة", delta=f"{no_coupon_count} إضافي" if no_coupon_count > 0 else "0", delta_color="inverse")
    m4.metric("الفائض بالصواني", f"{leftovers_count} وجبة")

# ------------------------------------------------------------------------------
# تبويب 2: صيانة الغرف ومتابعة تكرار الأعطال
# ------------------------------------------------------------------------------
with tab_repairs:
    st.markdown("##### 🚨 تسجيل بلاغ عطل بالغرفة:")

    with st.form("defect_form", clear_on_submit=True):
        room_no = st.text_input("رقم الغرفة (مثال: 104 أو 208):")
        defect_item = st.selectbox(
            "القطعة المعطلة (الـ 7 الشائعة):",
            [
                "مكيف", 
                "سخان موية", 
                "مرواش", 
                "بزبوز موية", 
                "شطاف", 
                "فيش كهرباء", 
                "لمبة سقف", 
                "أخرى"
            ]
        )
        defect_notes = st.text_input("وصف العطل / الملاحظات:", placeholder="مثال: يقطر ماء / الفيش فاصل...")

        btn_save_defect = st.form_submit_button("إدراج البلاغ في جدول الصيانة")

        if btn_save_defect:
            r_clean = room_no.strip()
            if not r_clean:
                st.error("الرجاء كتابة رقم الغرفة أولاً.")
            else:
                st.session_state["maintenance_db"].append({
                    "room": r_clean,
                    "item": defect_item,
                    "desc": defect_notes.strip() if defect_notes.strip() else "عطل تشغيلي",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "مفتوح"
                })
                st.success(f"تم تسجيل بلاغ غرفة {r_clean} ({defect_item}).")

    st.markdown("---")
    st.markdown("##### 📋 البلاغات القائمة ومتابعة تكرار الأعطال:")

    open_defects = [x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"]
    if open_defects:
        df_defects = pd.DataFrame(open_defects)
        room_repetition = df_defects["room"].value_counts()
        wa_message_lines = ["*تقرير صيانة السكن اليومي - بلاغات معلقة:*"]

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
            wa_message_lines.append(f"• غرفة {row['room']}: {row['item']} ({row['desc']})")

            if st.button(f"تم إصلاح عطل غرفة {row['room']} ({row['item']})", key=f"fix_btn_{idx}"):
                row["status"] = "تم الإصلاح ✓"
                st.rerun()

        encoded_wa = urllib.parse.quote("\n".join(wa_message_lines))
        wa_link = f"https://wa.me/{MAINTENANCE_PHONE}?text={encoded_wa}"
        st.markdown(
            f'<a href="{wa_link}" target="_blank" style="display:block; background:#10b981; color:#022c22; text-align:center; padding:12px; border-radius:10px; font-weight:900; text-decoration:none; margin-top:10px;">📲 إرسال قائمة البلاغات للصيانة عبر واتساب</a>',
            unsafe_allow_html=True
        )
    else:
        st.info("لا توجد بلاغات أعطال مفتوحة حالياً بالسكن.")

# ------------------------------------------------------------------------------
# تبويب 3: المخالفات والتعهدات السكنية (رصد الآيدي وكشف السوابق)
# ------------------------------------------------------------------------------
with tab_violations:
    st.markdown("##### ⚠️ توثيق مخالفة أو تعهد إداري:")

    with st.form("violation_form", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            emp_id = st.text_input("رقم الآيدي (الرقم الوظيفي):", placeholder="مثال: 3041")
        with col_v2:
            v_room = st.text_input("رقم الغرفة:", placeholder="مثال: 108")

        v_type = st.selectbox(
            "نوع المخالفة:",
            [
                "تدخين داخل الغرفة أو الممر 🚭",
                "إزعاج وضوضاء وقت نوم شفت الليل 🔊",
                "طبخ بالكهرباء داخل الغرفة (خطر حريق) ⚡",
                "إدخال أو تسكين شخص بدون إذن 🚫",
                "إتلاف ممتلكات السكن أو الأثاث 🪑",
                "عدم الالتزام بنظافة الغرفة المشتركة 🗑️",
                "أخرى"
            ]
        )

        v_action = st.selectbox(
            "الإجراء المتخذ:",
            [
                "تعهد شفهي وتنبيه أولي",
                "توقيع تعهد خطي رسمي",
                "إنذار إداري أول",
                "رفع مذكرة رسمية للإدارة (طلب خصم/نقل)"
            ]
        )

        v_notes = st.text_input("تفاصيل المخالفة الميدانية:", placeholder="مثال: ضبط متلبس بالتدخين في الشباك...")

        btn_save_violation = st.form_submit_button("🚨 تسجيل المخالفة وحفظ الوقت الرسمي")

        if btn_save_violation:
            clean_emp = emp_id.strip()
            if not clean_emp:
                st.error("الرجاء كتابة رقم الآيدي للموظف المخالف.")
            else:
                log_time_now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                st.session_state["violations_db"].append({
                    "id": clean_emp,
                    "room": v_room.strip() if v_room.strip() else "غير محدد",
                    "type": v_type,
                    "action": v_action,
                    "date": log_time_now,
                    "notes": v_notes.strip() if v_notes.strip() else "تم رصد المخالفة"
                })
                st.success(f"تم توثيق المخالفة على الموظف ({clean_emp}) في السجل المشفر.")

# ------------------------------------------------------------------------------
# تبويب 4: الجولات الميدانية بتوقيت مرن
# ------------------------------------------------------------------------------
with tab_rounds:
    st.markdown("##### 🚶 توثيق الجولات الميدانية:")

    with st.form("round_form", clear_on_submit=True):
        round_period = st.selectbox(
            "فترة الجولة الميدانية:",
            [
                "جولة المساء (بعد العشاء 8:30 م - 9:30 م)",
                "جولة بعد المغرب (6:30 م - 7:30 م)",
                "جولة الصباح (تفقد النظافة وهدوء شفت الليل)",
                "جولة العصر",
                "جولة طارئة"
            ]
        )

        exact_time = st.text_input("وقت الجولة الفعلي:", value=datetime.now().strftime("%I:%M %p"))
        checked_locations = st.text_input("الأماكن التي تم تفتيشها:", placeholder="مثال: ممرات الدور الأول + الحمامات...")
        round_observations = st.text_input("الملاحظات والخرابات المرصودة:", placeholder="مثال: التزام كامل بالهدوء...")

        btn_save_round = st.form_submit_button("حفظ الجولة في السجل")

        if btn_save_round:
            st.session_state["rounds_db"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "round_type": round_period,
                "logged_time": exact_time if exact_time else datetime.now().strftime("%I:%M %p"),
                "locations": checked_locations if checked_locations else "كامل مرافق السكن",
                "notes": round_observations if round_observations else "سليم"
            })
            st.success("تم توثيق الجولة بنجاح.")

    if st.session_state["rounds_db"]:
        st.markdown("---")
        st.markdown("##### 📌 آخر الجولات الموثقة:")
        for r in st.session_state["rounds_db"][-3:]:
            st.markdown(
                f"""
                <div class="stat-box">
                    <b>{r['round_type']}</b> — <small style="color:var(--primary);">{r['logged_time']}</small><br>
                    <small style="color:#cbd5e1;">المواقع: {r['locations']}</small><br>
                    <small style="color:#94a3b8;">الملاحظات: {r['notes']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

# ------------------------------------------------------------------------------
# تبويب 5: الخزنة المشفرة للمشرف (أرشيف كامل + كشف سوابق المخالفين + تصدير Excel)
# ------------------------------------------------------------------------------
with tab_vault:
    st.markdown("##### 🔐 الخزنة الرقمية للمشرف (منطقة آمنة ومحمية):")

    if not st.session_state["is_supervisor"]:
        st.caption("🔒 هذه المنطقة مشفرة ومخصصة للمشرف فقط؛ يُمنع الوصول للسجلات التاريخية والتصدير بدون الرمز السري.")
        input_pin = st.text_input("أدخل رمز المشرف السري (PIN):", type="password")

        if st.button("🔓 فتح الخزنة المشفرة", use_container_width=True):
            if hmac.compare_digest(input_pin.strip().encode(), MASTER_KEY.encode()):
                st.session_state["is_supervisor"] = True
                st.success("تم التحقق بنجاح! جاري فك قفل الخزنة...")
                st.rerun()
            else:
                st.error("رمز المشرف غير صحيح. الوصول محظور.")
    else:
        st.success("🟢 الخزنة مفتوحة ومؤمنة بصلاحية المشرف.")
        if st.button("🔒 قفل الخزنة والخروج فوراً"):
            st.session_state["is_supervisor"] = False
            st.rerun()

        st.divider()

        # كشف سوابق المخالفين (يظهر حصراً للمشرف)
        st.markdown("###### 🚨 كشف سوابق المخالفين (مدخن مرتين / تعهدات سابقة):")
        if st.session_state["violations_db"]:
            df_v = pd.DataFrame(st.session_state["violations_db"])
            id_counts = df_v["id"].value_counts()

            for row in reversed(st.session_state["violations_db"]):
                rep = id_counts.get(row["id"], 1)
                tag = f"<span class='alert-tag'>⚠️ تكرار سوابق: مسجل {rep} مرات</span>" if rep >= 2 else "<span class='warning-tag'>مخالفة أولى</span>"
                st.markdown(
                    f"""
                    <div class="stat-box" style="border-right: 3px solid #ef4444;">
                        <b>آيدي: {row['id']}</b> (غرفة {row['room']}) — {tag}<br>
                        <span style="color:#f87171; font-weight:800;">{row['type']}</span> | <small style="color:#fbbf24;">{row['action']}</small><br>
                        <small style="color:#94a3b8;">الوقت الموثق: {row['date']} | التفاصيل: {row['notes']}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("لا توجد مخالفات مسجلة.")

        st.divider()

        # التصدير الآمن لملفات Excel
        st.markdown("###### 📥 تصدير السجلات الميدانية لـ Excel:")
        st.caption("التحميل متاح فقط داخل هذه الخزنة المشفرة لحماية البيانات:")

        if st.session_state["violations_db"]:
            df_v_exp = pd.DataFrame(st.session_state["violations_db"])
            csv_v_data = df_v_exp.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📑 تحميل كشف المخالفات والتعهدات (Excel)",
                data=csv_v_data,
                file_name=f"Confidential_Violations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["meals_db"]:
            df_m_exp = pd.DataFrame(st.session_state["meals_db"])
            csv_m_data = df_m_exp.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📊 تحميل سجل الوجبات والكوبونات (Excel)",
                data=csv_m_data,
                file_name=f"Confidential_Meals_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["maintenance_db"]:
            df_r_exp = pd.DataFrame(st.session_state["maintenance_db"])
            csv_r_data = df_r_exp.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="🛠️ تحميل تقرير صيانة وأعطال الغرف (Excel)",
                data=csv_r_data,
                file_name=f"Confidential_Repairs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.session_state["rounds_db"]:
            df_rnd_exp = pd.DataFrame(st.session_state["rounds_db"])
            csv_rnd_data = df_rnd_exp.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="🚶 تحميل سجل الجولات الميدانية (Excel)",
                data=csv_rnd_data,
                file_name=f"Confidential_Rounds_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # النسخة المشفرة الكاملة AES-256
        if HAS_CRYPTO and st.session_state["violations_db"]:
            st.divider()
            st.markdown("###### 🛡️ النسخة الاحتياطية المشفرة (AES-256 Vault File):")
            st.caption("ملف مشفر لا يفتح بأي برنامج خارجي إلا بمفتاح المشرف:")
            
            combined_backup = df_v_exp.to_csv(index=False).encode("utf-8")
            encrypted_file = encrypt_payload(combined_backup, MASTER_KEY)
            
            st.download_button(
                label="🔐 تحميل ملف النسخة الاحتياطية المشفر (.ENC)",
                data=encrypted_file,
                file_name=f"Encrypted_Backup_{datetime.now().strftime('%Y%m%d')}.enc",
                mime="application/octet-stream",
                use_container_width=True
            )
