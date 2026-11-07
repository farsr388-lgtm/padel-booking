from datetime import datetime
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. تهيئة الصفحة (خفيفة جداً ومناسبة للجوال بدون حشو أكواد)
# ==============================================================================
st.set_page_config(
    page_title="إدارة سكن العمليات الميدانية",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# رابط واتساب مباشر يفتح شاشة اختيار المحادثات بدون تحديد رقم مسبق
def make_wa_link(text: str) -> str:
    return f"https://api.whatsapp.com/send?text={urllib.parse.quote(text)}"

# ==============================================================================
# 2. قواعد البيانات السريعة في الجلسة (Session State)
# ==============================================================================
if "maintenance" not in st.session_state:
    st.session_state.maintenance = [
        {"الغرفة": "405", "العطل": "شفاط", "وقت البلاغ": "08:15 م", "التاريخ": "2026-11-07", "الحالة": "معلق", "وقت الإصلاح": "-"}
    ]

if "violations" not in st.session_state:
    st.session_state.violations = [
        {"الجهة / الغرفة": "غرفة 108", "نوع المخالفة": "سخان / هيتر", "عدد الإنذارات": 1, "الملاحظة": "تنبيه أول بسحب السخان", "الوقت": "09:30 م", "التاريخ": "2026-11-06"}
    ]

if "rounds" not in st.session_state:
    st.session_state.rounds = [
        {"الجولة": "جولة مسائية", "الأدوار": "الدور 1، الدور 2، الدور 3", "الوقت": "09:00 م", "التاريخ": "2026-11-07", "الملاحظة": "الممرات نظيفة والهدوء ممتاز"}
    ]

# ==============================================================================
# 3. ترويسة التطبيق وتوزيع التبويبات
# ==============================================================================
st.title("🏢 العمليات الميدانية للسكن")
st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d | %I:%M %p')}")

tab1, tab2, tab3, tab4 = st.tabs([
    "🛠️ الصيانة الفورية",
    "⚠️ كشف وتكرار المخالفات",
    "🚶 جولات الأدوار",
    "📊 التقرير القيادي والإكسل"
])

# ------------------------------------------------------------------------------
# 1. تبويب الصيانة (تسجيل سريع، واتساب بضغطة زر، وإغلاق)
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("🛠️ بلاغ عطل جديد")
    with st.form("form_repair", clear_on_submit=True):
        c1, c2 = st.columns([1, 1.2])
        room_in = c1.text_input("رقم الغرفة:", placeholder="مثال: 405")
        issue_in = c2.selectbox("نوع العطل:", ["شفاط 💨", "مكيف ❄️", "سباكة / شطاف 🚿", "كهرباء / إنارة 💡", "أخرى 📝"])
        notes_in = st.text_input("تفاصيل إضافية (اختياري):", placeholder="مثال: صوت عالي / توقف كامل...")
        submit_repair = st.form_submit_button("⚡ حفظ البلاغ", use_container_width=True)

        if submit_repair:
            if not room_in.strip():
                st.error("يرجى كتابة رقم الغرفة أولاً.")
            else:
                t_str = datetime.now().strftime("%I:%M %p")
                d_str = datetime.now().strftime("%Y-%m-%d")
                clean_issue = issue_in.split()[0] if "أخرى" not in issue_in else (notes_in.strip() or "صيانة عامة")
                
                st.session_state.maintenance.append({
                    "الغرفة": room_in.strip(),
                    "العطل": clean_issue,
                    "وقت البلاغ": t_str,
                    "التاريخ": d_str,
                    "الحالة": "معلق",
                    "وقت الإصلاح": "-"
                })
                st.success(f"تم تسجيل عطل ({clean_issue}) لغرفة {room_in} بنجاح!")

    # عرض البلاغات المعلقة مع زر واتساب مباشر وزر إنجاز
    st.markdown("#### ⏳ البلاغات الجارية والمعلقة:")
    pending_repairs = [r for r in st.session_state.maintenance if r["الحالة"] == "معلق"]
    
    if not pending_repairs:
        st.info("لا توجد بلاغات معلقة حالياً.")
    else:
        for idx, row in enumerate(pending_repairs):
            with st.container(border=True):
                st.markdown(f"**غرفة {row['الغرفة']}** — 🔧 {row['العطل']}")
                st.caption(f"⏰ مسجل الساعة: {row['وقت البلاغ']} بتاريخ {row['التاريخ']}")
                
                msg_repair = f"السلام عليكم،\nبلاغ صيانة عاجل بالسكن:\n- الغرفة: {row['الغرفة']}\n- العطل: {row['العطل']}\n- وقت البلاغ: {row['وقت البلاغ']}\nيرجى المباشرة والإفادة عند الإصلاح."
                
                b_col1, b_col2 = st.columns(2)
                b_col1.link_button("📲 إرسال بالواتساب", make_wa_link(msg_repair), use_container_width=True)
                
                if b_col2.button(f"✅ تم الإصلاح", key=f"fix_{idx}", use_container_width=True):
                    row["الحالة"] = "تم الإصلاح"
                    row["وقت الإصلاح"] = datetime.now().strftime("%I:%M %p")
                    st.rerun()

# ------------------------------------------------------------------------------
# 2. تبويب المخالفات والتكرار العادل (لا ظلم ولا نسيان)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("⚠️ رصد المخالفات وتنبيهات الغرف والعمال")
    with st.form("form_viol", clear_on_submit=True):
        c_v1, c_v2 = st.columns([1.2, 1])
        target_name = c_v1.text_input("رقم الغرفة أو الجهة:", placeholder="مثال: غرفة 108 أو عمال الدور 2")
        viol_type = c_v2.selectbox("نوع المخالفة:", ["سخان / هيتر طبخ ⚡", "إهمال نظافة / نفايات 🗑️", "طبخ في الغرفة 🍳", "إزعاج 📢", "أخرى 📝"])
        viol_desc = st.text_input("ملاحظات التنبيه الميداني:", placeholder="مثال: تم إعطاء تنبيه أولي وسحب الجهاز...")
        submit_viol = st.form_submit_button("⚡ حفظ المخالفة والتحقق من التكرار", use_container_width=True)

        if submit_viol:
            target_clean = target_name.strip()
            if not target_clean:
                st.error("يرجى كتابة رقم الغرفة أو الجهة المخالفة.")
            else:
                # حساب عدد التكرارات السابقة لنفس الجهة بدقة
                prev_times = sum(1 for v in st.session_state.violations if v["الجهة / الغرفة"] == target_clean)
                current_count = prev_times + 1
                t_now = datetime.now().strftime("%I:%M %p")
                d_now = datetime.now().strftime("%Y-%m-%d")

                st.session_state.violations.append({
                    "الجهة / الغرفة": target_clean,
                    "نوع المخالفة": viol_type.split()[0],
                    "عدد الإنذارات": current_count,
                    "الملاحظة": viol_desc.strip() or "تم رصد المخالفة وتوجيه التنبيه",
                    "الوقت": t_now,
                    "التاريخ": d_now
                })

                msg_viol = f"إشعار ضبط ومتابعة - سكن العمليات:\n- المخالف: {target_clean}\n- النوع: {viol_type.split()[0]}\n- الملاحظة: {viol_desc or 'تنبيه ميداني'}\n- عدد الإنذارات المسجلة: ({current_count})\n- التوقيت: {t_now} ({d_now})\nيرجى العلم ومتابعة السجل لتفادي التكرار."
                st.session_state["latest_viol_msg"] = msg_viol
                st.success(f"تم التوثيق: ({target_clean}) — إنذار رقم ({current_count})")

    if "latest_viol_msg" in st.session_state:
        st.link_button("📲 إرسال إشعار المخالفة فوراً عبر واتساب", make_wa_link(st.session_state["latest_viol_msg"]), use_container_width=True)

    st.markdown("#### 🔍 الغرف الأكثر تكراراً للمخالفات (لدعم القرار):")
    if st.session_state.violations:
        df_v = pd.DataFrame(st.session_state.violations)
        repeat_counts = df_v["الجهة / الغرفة"].value_counts()
        frequent = repeat_counts[repeat_counts >= 2]
        
        if not frequent.empty:
            for room, count in frequent.items():
                st.warning(f"⚠️ **{room}** تكررت عليها المخالفات **{count} مرات**. (تستوجب إجراء رسمي حاسم).")
        else:
            st.info("جميع الإنذارات الحالية فردية (مرة واحدة)، ولا توجد غرف مكررة حتى الآن.")
    else:
        st.info("سجل المخالفات نظيف.")

# ------------------------------------------------------------------------------
# 3. تبويب الجولات والأدوار المزارة
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("🚶 توثيق جولة تفتيش الأدوار")
    with st.form("form_round", clear_on_submit=True):
        floors_checked = st.multiselect(
            "الأدوار التي تم المرور عليها في هذه الجولة:",
            ["الدور الأرضي", "الدور 1", "الدور 2", "الدور 3", "الدور 4", "الدور 5"],
            default=["الدور 1", "الدور 2"]
        )
        round_note = st.text_input("ملاحظة الجولة العامة:", placeholder="مثال: تم إخلاء الممرات وهدوء تام...")
        submit_round = st.form_submit_button("⚡ حفظ الجولة", use_container_width=True)

        if submit_round:
            if not floors_checked:
                st.error("يرجى اختيار دور واحد على الأقل.")
            else:
                floors_str = "، ".join(floors_checked)
                t_r = datetime.now().strftime("%I:%M %p")
                d_r = datetime.now().strftime("%Y-%m-%d")
                
                st.session_state.rounds.append({
                    "الجولة": "جولة ميدانية",
                    "الأدوار": floors_str,
                    "الوقت": t_r,
                    "التاريخ": d_r,
                    "الملاحظة": round_note.strip() or "تم المرور والتأكد من انضباط السكن"
                })
                
                round_msg = f"محضر جولة ميدانية:\n- الأدوار المزارة: {floors_str}\n- التوقيت: {t_r} ({d_r})\n- الملاحظات: {round_note.strip() or 'الوضع منضبط وسليم'}"
                st.session_state["latest_round_msg"] = round_msg
                st.success("تم تسجيل الجولة بنجاح!")

    if "latest_round_msg" in st.session_state:
        st.link_button("📲 إرسال محضر الجولة عبر واتساب", make_wa_link(st.session_state["latest_round_msg"]), use_container_width=True)

    st.markdown("#### 🕒 سجل آخر الجولات والأدوار التي تمت زيارتها:")
    for r in reversed(st.session_state.rounds[-5:]):
        with st.container(border=True):
            st.markdown(f"**الأدوار:** {r['الأدوار']}")
            st.caption(f"⏰ {r['الوقت']} | 📅 {r['التاريخ']} — الملاحظة: {r['الملاحظة']}")

# ------------------------------------------------------------------------------
# 4. التقرير القيادي الشامل وكشف الإكسل التفاعلي (أعلى كفاءة وأقل جهد)
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("📊 ملخص الموقف اليومي وكشف الإكسل")

    # 1. إعداد التقرير النصي التلخيصي
    p_rep = [x for x in st.session_state.maintenance if x["الحالة"] == "معلق"]
    f_rep = [x for x in st.session_state.maintenance if x["الحالة"] == "تم الإصلاح"]
    v_all = st.session_state.violations
    last_r = st.session_state.rounds[-1] if st.session_state.rounds else None

    # الغرف الأكثر تكراراً
    freq_txt = "لا يوجد تكرار، جميع المخالفات فردية."
    if v_all:
        df_temp = pd.DataFrame(v_all)
        vc = df_temp["الجهة / الغرفة"].value_counts()
        high_v = vc[vc >= 2]
        if not high_v.empty:
            freq_txt = "، ".join([f"{k} ({v} مرات)" for k, v in high_v.items()])

    summary_text = f"""مساك الله بالخير،،
تقرير الموقف والعمليات الميدانية للسكن اليوم:

🛠️ الصيانة:
- البلاغات المعلقة: {len(p_rep)}
- تم إصلاحها اليوم: {len(f_rep)}

⚠️ المخالفات والتكرار (حفظاً للحقوق):
- إجمالي المخالفات المسجلة: {len(v_all)}
- الغرف المكررة: {freq_txt}

🚶 الجولة الميدانية:
- آخر أدوار تم تفتيشها: {last_r['الأدوار'] if last_r else 'لم تسجل بعد'}
- حالة السكن العامة: منضبط وتحت السيطرة الميدانية."""

    # صندوق عرض التقرير التفصيلي
    st.text_area("📝 التقرير الملخص لمتخذ القرار:", value=summary_text, height=210)
    st.link_button("📲 إرسال التقرير الشامل فوراً لأي شخص بالواتساب", make_wa_link(summary_text), use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📋 كشف الإكسل التفاعلي (Excel View):")
    
    view_type = st.radio("اختر الجدول المطلوب عرضه:", ["الصيانة", "المخالفات والإنذارات", "الجولات والأدوار"], horizontal=True)

    if view_type == "الصيانة":
        df_show = pd.DataFrame(st.session_state.maintenance)
    elif view_type == "المخالفات والإنذارات":
        df_show = pd.DataFrame(st.session_state.violations)
    else:
        df_show = pd.DataFrame(st.session_state.rounds)

    # عرض جدول إكسل تفاعلي منظم
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # زر تحميل الإكسل المباشر
    csv_bytes = df_show.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label=f"📥 تحميل كشف {view_type} بصيغة Excel (CSV)",
        data=csv_bytes,
        file_name=f"report_{view_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
