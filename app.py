from datetime import datetime
import urllib.parse
import pandas as pd
import streamlit as st

# ضبط خفيف جداً بدون أكواد CSS معقدة تثقل الجوال
st.set_page_config(page_title="سكن 3 | العمليات", page_icon="🏢", layout="centered")

def get_wa_url(text: str) -> str:
    """رابط واتساب مباشر يفتح لك قائمة المحادثات الأخيرة بدون حفظ أرقام"""
    return f"https://api.whatsapp.com/send?text={urllib.parse.quote(text)}"

# قاعدة البيانات الحية في الصفحة
if "log_db" not in st.session_state:
    st.session_state.log_db = [
        {"الوقت": "08:15 م", "التاريخ": "2026-11-07", "الغرفة/الموقع": "405", "النوع": "صيانة", "البند": "شفاط", "التكرار": 1, "الحالة": "معلق", "الملاحظة": "يحتاج تبديل فوري"},
        {"الوقت": "09:30 م", "التاريخ": "2026-11-07", "الغرفة/الموقع": "108", "النوع": "مخالفة", "البند": "هيتر / طبخ", "التكرار": 1, "الحالة": "تنبيه", "الملاحظة": "تنبيه أول وسحب الجهاز"},
    ]

st.title("🏢 سكن جامعة 3 — إدارة الموقف")
st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d | %I:%M %p')}")

# ==============================================================================
# 1. شاشة الرصد السريع (أقل من 5 ثوانٍ لإنهاء أي بلاغ)
# ==============================================================================
st.markdown("### ⚡ رصد فوري")

c_target, c_type = st.columns([1, 1.2])
target = c_target.text_input("الغرفة أو الدور:", placeholder="مثال: 405 أو الدور 3")
op_type = c_type.selectbox("النوع:", ["صيانة 🛠️", "مخالفة ⚠️", "جولة دور 🚶"])

# الخيارات تتغير تلقائياً حسب نوع العملية بلمسة واحدة
if "صيانة" in op_type:
    item = st.selectbox("بند الصيانة:", ["شفاط", "مكيف", "سباكة / شطاف", "كهرباء / إنارة", "قفل باب", "أخرى"])
elif "مخالفة" in op_type:
    item = st.selectbox("بند المخالفة:", ["هيتر / طبخ بالغرفة", "إهمال نظافة ونفايات", "تأخر عمال النظافة", "سخان ماء مخالف", "إزعاج"])
else:
    item = st.selectbox("الجولة:", ["تفتيش الدور ومتابعة الهدوء", "فحص ممرات وطوارئ", "تأكيد نظافة المرافق"])

note = st.text_input("ملاحظة سريعة (اختياري):", placeholder="مثال: عطلان تماماً / إنذار شفهي / سليم...")

if st.button("⚡ تسجيل وتجهيز رسالة الواتساب", use_container_width=True):
    t_clean = target.strip()
    if not t_clean:
        st.error("اكتب رقم الغرفة أو الدور أولاً.")
    else:
        # حساب التكرار تلقائياً لحفظ الحقوق وعدم ظلم أحد
        prev_count = sum(1 for x in st.session_state.log_db if x["الغرفة/الموقع"] == t_clean and x["البند"] == item)
        current_count = prev_count + 1
        
        t_now = datetime.now().strftime("%I:%M %p")
        d_now = datetime.now().strftime("%Y-%m-%d")
        status_val = "معلق" if "صيانة" in op_type else ("إنذار" if "مخالفة" in op_type else "منجز")

        # حفظ مباشر في الإكسل
        st.session_state.log_db.append({
            "الوقت": t_now,
            "التاريخ": d_now,
            "الغرفة/الموقع": t_clean,
            "النوع": op_type.split()[0],
            "البند": item,
            "التكرار": current_count,
            "الحالة": status_val,
            "الملاحظة": note.strip() or "تم الرصد الميداني",
        })

        # صياغة رسالة رسمية وجاهزة للقرار
        repeat_txt = f"⚠️ (تكرار للمرة الـ {current_count})" if current_count > 1 else "(أول مرة)"
        wa_text = f"""بلاغ ميداني - سكن جامعة 3:
- الموقع/الغرفة: {t_clean}
- البند: {item} {repeat_txt}
- التوقيت: {t_now} ({d_now})
- الملاحظة: {note.strip() or 'المباشرة واتخاذ الإجراء'}"""

        st.session_state["ready_wa"] = wa_text
        st.success(f"تم الحفظ! {t_clean} — تكرار: ({current_count})")

# زر الواتساب الفوري: يفتح مباشرة لاختيار أي محادثة أو قروب
if "ready_wa" in st.session_state:
    st.link_button("📲 فتح الواتساب والإرسال الآن", get_wa_url(st.session_state["ready_wa"]), use_container_width=True)

st.markdown("---")

# ==============================================================================
# 2. كشف الإكسل التفاعلي المباشر (فوقه تنبيه الغرف المكررة)
# ==============================================================================
df = pd.DataFrame(st.session_state.log_db)

st.markdown("### 📋 سجل العمليات الميدانية (Excel الحقيقي)")

# كشف سريع للغرف المكررة لاتخاذ القرار
repeats = df[df["التكرار"] >= 2]
if not repeats.empty:
    with st.container(border=True):
        st.markdown("🚨 **غرف مكررة تستوجب المساءلة اللائحية (بدون ظلم):**")
        for _, r in repeats.drop_duplicates(subset=["الغرفة/الموقع", "البند"]).iterrows():
            st.write(f"• **غرفة {r['الغرفة/الموقع']}**: تكرار {r['البند']} ({r['التكرار']} مرات)")

# عرض الجدول بشكل نظيف ومتناسق مع شاشة الجوال
st.dataframe(df, use_container_width=True, hide_index=True)

# تنزيل ملف الإكسل الحقيقي بضغطة زر
csv_data = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "📥 تحميل كشف الإكسل كاملاً (CSV/Excel)",
    data=csv_data,
    file_name=f"housing_log_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True,
)

st.markdown("---")

# ==============================================================================
# 3. تقرير آخر اليوم المجمع للإدارة بضغطة زر واحدة
# ==============================================================================
st.markdown("### 📊 تقرير تسليم الوردية المجمع")

pending_m = len(df[(df["النوع"] == "صيانة") & (df["الحالة"] == "معلق")])
total_v = len(df[df["النوع"] == "مخالفة"])
rounds_done = "، ".join(df[df["النوع"] == "جولة"]["الغرفة/الموقع"].unique()) or "لا يوجد"

rep_summary = f"""مساك الله بالخير،،
تقرير موقف سكن جامعة 3 الميداني اليوم ({datetime.now().strftime('%Y-%m-%d')}):

1️⃣ الصيانة:
- البلاغات المعلقة حالياً: {pending_m}

2️⃣ المخالفات والإنذارات:
- إجمالي ما تم رصده: {total_v}
- أبرز الغرف المتكررة: {', '.join(repeats['الغرفة/الموقع'].unique()) if not repeats.empty else 'الوضع طبيعي ولا يوجد تكرار مقلق'}

3️⃣ الجولات والأدوار المزارة:
- الأدوار التي تم تغطيتها: {rounds_done}

الوضع العام بالسكن منضبط وتحت السيطرة."""

st.text_area("معاينة التقرير النهائي:", value=rep_summary, height=180)
st.link_button("📲 إرسال التقرير الشامل لمديرك / زميلك بالواتساب", get_wa_url(rep_summary), use_container_width=True)
