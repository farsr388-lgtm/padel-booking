from datetime import datetime
import urllib.parse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="سكن 3 | جولات المياه والسباكة",
    page_icon="🚰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

def make_wa_url(text: str) -> str:
    """رابط واتساب مباشر يفتح محادثاتك لاختيار أي مستلم بلمسة واحدة"""
    return f"https://api.whatsapp.com/send?text={urllib.parse.quote(text)}"

# قاعدة البيانات الحية لجولات السباكة وهدر المياه
if "water_db" not in st.session_state:
    st.session_state.water_db = [
        {
            "التاريخ": "2026-11-07",
            "الشهر": "2026-11",
            "الوقت": "10:15 ص",
            "الغرفة_الموقع": "غرفة 302",
            "البند": "صوبر السيفون (عوامة تالفة)",
            "مستوى_الهدر": "شديد (ماء مستمر)",
            "الحالة": "معلق",
            "وقت_الإصلاح": "-",
            "الملاحظة": "تهريب مياه مستمر في الكرسي",
        },
        {
            "التاريخ": "2026-11-08",
            "الشهر": "2026-11",
            "الوقت": "09:00 ص",
            "الغرفة_الموقع": "دورات مياه الدور 4",
            "البند": "سيفون معلق يسرب",
            "مستوى_الهدر": "شديد (ماء مستمر)",
            "الحالة": "تم الإصلاح",
            "وقت_الإصلاح": "09:25 ص",
            "الملاحظة": "تم فك السيفون وضبط المكبس فوراً",
        },
    ]

st.title("🚰 جولات المياه ومكافحة الهدر")
st.caption(f"📅 اليوم: {datetime.now().strftime('%Y-%m-%d | %I:%M %p')}")

tab1, tab2, tab3 = st.tabs([
    "⚡ جولة الرصد الفوري",
    "📋 التقرير اليومي",
    "📊 التقرير الشهري والتراكمي",
])

# ==============================================================================
# 1. جولة الرصد الميداني السريع (صوبر، سيفون، تسريب، شطاف)
# ==============================================================================
with tab1:
    st.subheader("⚡ تسجيل بلاغ صيانة / هدر مياه")

    with st.form("form_water_inspect", clear_on_submit=True):
        c1, c2 = st.columns([1, 1.2])
        loc_in = c1.text_input("الغرفة أو الموقع:", placeholder="مثال: 405 أو حمامات دور 2")
        item_in = c2.selectbox(
            "بند العطل / الفحص:",
            [
                "صوبر السيفون (عوامة تالفة) ⚙️",
                "سيفون معلق يسرب 🚽",
                "محبس زاوية / لي شطاف يهرب 🚿",
                "بلف / صنبور مياه مفتوح وهدر 🚰",
                "كسر ماسورة / تسريب أرضي ⚠️",
                "فحص سليم (لا يوجد تسريب) ✅",
            ],
        )

        c3, c4 = st.columns(2)
        waste_level = c3.selectbox("مستوى الهدر:", ["شديد (ماء مستمر)", "تنقيط / خفيف", "معدوم (سليم)"])
        init_status = c4.radio("حالة المعالجة:", ["معلق", "تم الإصلاح في الموقع"], horizontal=True)

        notes_in = st.text_input("ملاحظة الجولة:", placeholder="مثال: تم إغلاق المحبس مؤقتاً لحين تبديل الصوبر...")
        btn_save = st.form_submit_button("⚡ حفظ البلاغ وتوليد رسالة الواتساب", use_container_width=True)

        if btn_save:
            clean_loc = loc_in.strip()
            if not clean_loc:
                st.error("اكتب رقم الغرفة أو الموقع أولاً.")
            else:
                d_now = datetime.now().strftime("%Y-%m-%d")
                m_now = datetime.now().strftime("%Y-%m")
                t_now = datetime.now().strftime("%I:%M %p")
                fix_time = t_now if init_status == "تم الإصلاح في الموقع" else "-"
                clean_item = item_in.split()[0] + " " + item_in.split()[1]

                st.session_state.water_db.append({
                    "التاريخ": d_now,
                    "الشهر": m_now,
                    "الوقت": t_now,
                    "الغرفة_الموقع": clean_loc,
                    "البند": clean_item,
                    "مستوى_الهدر": waste_level,
                    "الحالة": "تم الإصلاح" if init_status == "تم الإصلاح في الموقع" else "معلق",
                    "وقت_الإصلاح": fix_time,
                    "الملاحظة": notes_in.strip() or "جولة كشف ميداني",
                })

                msg_inspect = f"""بلاغ سباكة وهدر مياه عاجل - سكن جامعة 3:
- الموقع: {clean_loc}
- العطل: {clean_item}
- مستوى الهدر: {waste_level}
- الحالة: {init_status}
- التوقيت: {t_now} ({d_now})
- الملاحظة: {notes_in.strip() or 'يرجى المباشرة فوراً'}"""

                st.session_state["active_water_wa"] = msg_inspect
                st.success(f"تم توثيق {clean_item} لموقع ({clean_loc}) بنجاح!")

    if "active_water_wa" in st.session_state:
        st.link_button("📲 فتح الواتساب والإرسال الآن لسباك الصيانة / الإدارة", make_wa_url(st.session_state["active_water_wa"]), use_container_width=True)

    st.markdown("---")
    st.markdown("#### ⏳ تسريبات مياه معلقة تتطلب معالجة فورية:")
    
    pending_list = [x for x in st.session_state.water_db if x["الحالة"] == "معلق" and "سليم" not in x["البند"]]
    if not pending_list:
        st.info("لا توجد تسريبات مياه معلقة حالياً. السكن خالٍ من الهدر النشط.")
    else:
        for idx, row in enumerate(pending_list):
            with st.container(border=True):
                st.markdown(f"🚨 **{row['الغرفة_الموقع']}** — <span style='color:#f87171;'>{row['البند']}</span> ({row['مستوى_الهدر']})", unsafe_allow_html=True)
                st.caption(f"⏰ مرصود الساعة {row['الوقت']} بتاريخ {row['التاريخ']} | الملاحظة: {row['الملاحظة']}")
                
                c_act1, c_act2 = st.columns(2)
                remind_msg = f"تذكير صيانة عاجل: نرجو مباشرة تسريب ({row['البند']}) بموقع {row['الغرفة_الموقع']} لتفادي هدر المياه. مسجل منذ {row['الوقت']}."
                c_act1.link_button("📲 إرسال تذكير للمقاول", make_wa_url(remind_msg), use_container_width=True)
                
                if c_act2.button(f"✅ تم الإصلاح وتغيير القطعة", key=f"fixed_{idx}", use_container_width=True):
                    row["الحالة"] = "تم الإصلاح"
                    row["وقت_الإصلاح"] = datetime.now().strftime("%I:%M %p")
                    st.rerun()

# ==============================================================================
# 2. التقرير اليومي الشامل (مخصص لتسليم الوردية وإدارة الصيانة)
# ==============================================================================
with tab2:
    st.subheader("📋 تقرير موقف المياه اليومي المعتمد")
    
    df_all = pd.DataFrame(st.session_state.water_db)
    today_date = datetime.now().strftime("%Y-%m-%d")
    df_today = df_all[df_all["التاريخ"] == today_date] if not df_all.empty else pd.DataFrame()

    total_today = len(df_today)
    pending_today = len(df_today[df_today["الحالة"] == "معلق"])
    fixed_today = len(df_today[df_today["الحالة"] == "تم الإصلاح"])
    severe_waste = len(df_today[df_today["مستوى_الهدر"].str.contains("شديد", na=False)])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("فحوصات اليوم", total_today)
    m2.metric("هدر شديد", severe_waste, delta_color="inverse")
    m3.metric("تم إصلاحه", fixed_today)
    m4.metric("معلق حالياً", pending_today, delta_color="inverse")

    # صياغة التقرير اليومي الجاهز للإرسال
    open_details = "\n".join([f"  • {r['الغرفة_الموقع']}: {r['البند']} ({r['مستوى_الهدر']})" for _, r in df_today[df_today['الحالة'] == 'معلق'].iterrows()]) if pending_today > 0 else "  • لا توجد أعطال معلقة."
    done_details = "\n".join([f"  • تم إصلاح {r['البند']} في {r['الغرفة_الموقع']} (الساعة {r['وقت_الإصلاح']})" for _, r in df_today[df_today['الحالة'] == 'تم الإصلاح'].iterrows()]) if fixed_today > 0 else "  • لا يوجد."

    daily_report_txt = f"""مساك الله بالخير،،
تقرير جولات السباكة ومكافحة هدر المياه اليومي - سكن جامعة 3
التاريخ: {today_date}

📊 الإحصائيات الميدانية:
- إجمالي المواقع المفحوصة: {total_today}
- بلاغات هدر المياه النشطة: {severe_waste}
- تم إصلاحه ومعالجته: {fixed_today}
- البلاغات المعلقة قيد التنفيذ: {pending_today}

🔴 البلاغات المعلقة المطلوب إنهاؤها:
{open_details}

🟢 ما تم إنجازه وضبطه اليوم:
{done_details}

الوضع العام: متابعة مستمرة لمنع أي هدر مائي بالسكن."""

    st.text_area("معاينة التقرير اليومي الموجه للمدير / المشرف:", value=daily_report_txt, height=220)
    st.link_button("📲 إرسال التقرير اليومي بالواتساب", make_wa_url(daily_report_txt), use_container_width=True)

    st.markdown("---")
    st.markdown("##### 📥 جدول إكسل بلاغات اليوم:")
    st.dataframe(df_today, use_container_width=True, hide_index=True)
    
    if not df_today.empty:
        csv_daily = df_today.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 تحميل إكسل بلاغات اليوم (CSV)",
            data=csv_daily,
            file_name=f"water_daily_{today_date}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ==============================================================================
# 3. التقرير الشهري التراكمي (تحليل الهدر + مؤشرات الأداء + تقرير قيادي)
# ==============================================================================
with tab3:
    st.subheader("📊 التقرير الشهري والتحليلي لهدر السباكة")
    st.caption("يعطيك تحليلاً دقيقاً لكل شهر: أكثر الأعطال تكراراً، الغرف المكررة، ونسبة الإنجاز:")

    if not df_all.empty:
        available_months = sorted(df_all["الشهر"].unique().tolist(), reverse=True)
        selected_month = st.selectbox("اختر شهر التقرير:", available_months)

        df_month = df_all[df_all["الشهر"] == selected_month]

        m_total = len(df_month)
        m_fixed = len(df_month[df_month["الحالة"] == "تم الإصلاح"])
        m_pending = len(df_month[df_month["الحالة"] == "معلق"])
        fix_rate = round((m_fixed / m_total * 100), 1) if m_total > 0 else 0

        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("إجمالي البلاغات بالشهر", m_total)
        c_m2.metric("نسبة الإغلاق والإصلاح", f"{fix_rate}%")
        c_m3.metric("متبقي معلق", m_pending, delta_color="inverse")

        # تحليل أكثر قطع السباكة استهلاكاً وتلفاً
        st.markdown("##### 🔍 الأعطال الأكثر تكراراً خلال الشهر:")
        top_issues = df_month["البند"].value_counts()
        st.dataframe(top_issues.rename("عدد المرات"), use_container_width=True)

        # الغرف الأكثر تكراراً للتسريب (لحفظ حقوق السكن وعدم التكرار)
        repeats_room = df_month["الغرفة_الموقع"].value_counts()
        frequent_rooms = repeats_room[repeats_room >= 2]
        
        repeat_str = "لا توجد مواقع متكررة بشكل ملحوظ."
        if not frequent_rooms.empty:
            repeat_str = "، ".join([f"{k} ({v} مرات)" for k, v in frequent_rooms.items()])
            st.warning(f"⚠️ **مواقع تكرر فيها هدر المياه هذا الشهر:** {repeat_str}")

        # صياغة التقرير الشهري القيادي
        monthly_report_txt = f"""مساك الله بالخير أبو عمر،،
التقرير الشهري الشامل لصيانة السباكة وهدر المياه - {selected_month}
سكن جامعة 3:

📈 مؤشرات الأداء الشهري:
- إجمالي البلاغات المسجلة: {m_total}
- البلاغات المنجزة والمصلحة: {m_fixed} ({fix_rate}%)
- البلاغات المعلقة بنهاية الشهر: {m_pending}

🔧 أكثر الأعطال المسجلة تكراراً:
{chr(10).join([f"  • {issue}: {count} مرات" for issue, count in top_issues.head(3).items()])}

⚠️ المواقع التي تكرر فيها التسريب:
- {repeat_str}

💡 التوصية التشغيلية: إلزام مقاول الصيانة بتوفير كميات كافية من صوبر السيفونات وجلود العوامات الأصلية للحد من الهدر المتكرر في الكراسي."""

        st.text_area("نص التقرير الشهري التنفيذي:", value=monthly_report_txt, height=220)
        st.link_button("📲 إرسال التقرير الشهري بالواتساب للإدارة", make_wa_url(monthly_report_txt), use_container_width=True)

        st.markdown("---")
        # تنزيل السجل الشهري الكامل
        csv_monthly = df_month.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label=f"📥 تنزيل كشف شهر {selected_month} كاملاً (Excel/CSV)",
            data=csv_monthly,
            file_name=f"water_monthly_report_{selected_month}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("لا توجد بيانات مسجلة حتى الآن.")
