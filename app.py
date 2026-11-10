from datetime import datetime
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (RTL / Dark Mode / Mobile-First)
# ==============================================================================
st.set_page_config(
    page_title="سكن جامعة 3 | رصد الواقع الميداني",
    page_icon="👁️",
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
.header-box { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 12px; 
    padding: 12px; 
    margin-bottom: 10px; 
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
.obs-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 8px;
}
.tag-critical {
    background: rgba(239, 68, 68, 0.25);
    border: 1px solid rgba(239, 68, 68, 0.6);
    color: #fca5a5;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.75em;
    font-weight: 800;
}
.tag-warning {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid rgba(245, 158, 11, 0.6);
    color: #fcd34d;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.75em;
    font-weight: 800;
}
.tag-pass {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #6ee7b7;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.75em;
    font-weight: 800;
}
.wa-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 10px;
    font-weight: 900;
    font-size: 1.05em;
    text-decoration: none !important;
    margin-top: 10px;
    margin-bottom: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت وقاعدة بيانات الرصد الميداني
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
OBSERVER_NAME = "فارس العصيمي"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

if "observations_db" not in st.session_state:
  st.session_state["observations_db"] = [
      {
          "id": "OBS-01",
          "location": "السطح",
          "category": "سباكة وهدر مياه",
          "what_i_saw": (
              "صنبور الخط الرئيسي مكسور ويبق موية بقوة وتجمع مياه على العازل"
          ),
          "compliance_status": "غير مطابق - خلل تشغيلي حرج",
          "assigned_to": "مقاول الصيانة",
          "photo": None,
          "time": "10:15 ص",
          "date": "2026-11-10",
      },
      {
          "location": "غرفة 213",
          "category": "تكييف وتبريد",
          "what_i_saw": (
              "كمبروسر المكيف له صوت اهتزاز عالي جداً والتبريد ضعيف لا يطابق"
              " معايير التسكين"
          ),
          "compliance_status": "غير مطابق للوعد التسويقي",
          "assigned_to": "إدارة السكن والتسويق",
          "photo": None,
          "time": "11:30 ص",
          "date": "2026-11-10",
      },
  ]

now = datetime.now()

# ==============================================================================
# 3. ترويسة التطبيق
# ==============================================================================
st.markdown(
    f"""
<div class="header-box">
    <div class="headline">👁️ توثيق الواقع المشاهد | {LOCATION_TAG}</div>
    <div class="sub-headline">المشرف الراصد: {OBSERVER_NAME} • مطابقة الوعد للواقع الميداني</div>
</div>
""",
    unsafe_allow_html=True,
)

c_t1, c_t2 = st.columns([2, 1])
with c_t1:
  st.caption(f"📅 توقيت الرصد: {now.strftime('%Y-%m-%d | %I:%M %p')}")
with c_t2:
  if st.button("🔄 تحديث الشاشة", use_container_width=True):
    st.rerun()

tab_record, tab_feed, tab_report, tab_archive = st.tabs([
    "✍️ رصد ما أراه",
    "📋 سجل المشاهدات الحية",
    "📲 تقرير الواتساب",
    "🔐 الخزنة والتصدير",
])

# ------------------------------------------------------------------------------
# 1. شاشة "رصد ما أراه بنفسي" (تسجيل مفصل ودقيق للواقع)
# ------------------------------------------------------------------------------
with tab_record:
  st.markdown("##### 📝 تسجيل الواقع كما رأيته بعينك:")

  with st.form("observation_entry_form", clear_on_submit=True):
    raw_loc = st.text_input(
        "📍 أين أنت الآن؟ (الموقع بدقة):",
        placeholder="مثال: السطح، غرفة 104، ممر الدور 2، صالة الطعام...",
    )

    category = st.selectbox(
        "🔍 ما هو قطاع المشاهدة؟",
        [
            "سباكة وهدر مياه 🚰",
            "تكييف وتهوية ❄️",
            "نظافة وتراكم نفايات 🗑️",
            "سلامة وسخانات مخالفة ⚡",
            "مطابقة التسكين للوعد التسويقي 🏢",
            "إعاشة وتوزيع وجبات 🍽️",
            "أخرى 📝",
        ],
    )

    what_i_saw = st.text_area(
        "👁️ صِف ما رأيته بعينك بدقة وتفصيل:",
        placeholder=(
            "اكتب المشهد بدقة: مثل: لقيت تسريب ماء متجمع في الزاوية، المكيف"
            " يقطر على الفرش، النظافة غير مقبولة في مدخل الدور..."
        ),
        height=110,
    )

    col_st1, col_st2 = st.columns(2)
    with col_st1:
      compliance = st.selectbox(
          "⚖️ تقييم ما رأيته مقارنة بالمعايير:",
          [
              "مطابق وسليم 100% ✓",
              "ملاحظة بسيطة تحت المتابعة ⚠️",
              "غير مطابق للوعد التسويقي ❌",
              "خلل تشغيلي حرج / خطر حريق 🚨",
          ],
          index=1,
      )

    with col_st2:
      assigned = st.selectbox(
          "🎯 من المسؤول المعني بما رأيت؟",
          [
              "مقاول الصيانة",
              "مقاول النظافة",
              "متعهد الإعاشة",
              "فريق التسويق (لتعديل الوعد)",
              "مدير السكن (عمر)",
          ],
      )

    obs_photo = st.file_uploader(
        "📷 التقط صورة تثبت ما رأيته بعينك (كاميرا أو استوديو):",
        type=["jpg", "jpeg", "png"],
        help="الصورة ترفع فوراً وتثبت الحالة كما شاهدتها ميدانياً",
    )

    btn_submit = st.form_submit_button("⚡ توثيق وتثبيت المشاهدة في السجل")

    if btn_submit:
      clean_loc = raw_loc.strip()
      final_loc = (
          f"غرفة {clean_loc}"
          if (clean_loc.isdigit() and len(clean_loc) < 5)
          else clean_loc
      )
      clean_desc = what_i_saw.strip()

      if not clean_loc or not clean_desc:
        st.error("الرجاء تحديد الموقع وكتابة وصف ما شاهدته.")
      else:
        photo_bytes = obs_photo.getvalue() if obs_photo else None
        new_obs = {
            "id": f"OBS-{len(st.session_state['observations_db'])+1:02d}",
            "location": final_loc,
            "category": category.split()[0] + " " + category.split()[1],
            "what_i_saw": clean_desc,
            "compliance_status": compliance,
            "assigned_to": assigned,
            "photo": photo_bytes,
            "time": datetime.now().strftime("%I:%M %p"),
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        st.session_state["observations_db"].append(new_obs)
        st.success(f"تم توثيق مشاهدة ({final_loc}) بدقة وإسنادها بنجاح!")
        st.rerun()

# ------------------------------------------------------------------------------
# 2. سجل المشاهدات الحية (عرض تفصيلي لما تم رصده)
# ------------------------------------------------------------------------------
with tab_feed:
  st.markdown("##### 📋 سجل الواقع المرصود في السكن:")

  if not st.session_state["observations_db"]:
    st.info("لم يتم رصد أي مشاهدات ميدانية حتى الآن.")
  else:
    for idx, obs in enumerate(
        reversed(st.session_state["observations_db"][-6:])
    ):
      status_txt = obs.get("compliance_status", "")
      tag_cls = "tag-pass"
      if "حرج" in status_txt or "خطر" in status_txt:
        tag_cls = "tag-critical"
      elif "غير مطابق" in status_txt or "ملاحظة" in status_txt:
        tag_cls = "tag-warning"

      st.markdown(
          f"""
            <div class="obs-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b>📍 {obs.get('location')}</b>
                    <span class="{tag_cls}">{status_txt}</span>
                </div>
                <div style="color:var(--primary); font-size:0.85em; font-weight:700; margin-top:3px;">
                    القطاع: {obs.get('category')} | المعني: {obs.get('assigned_to')}
                </div>
                <div style="color:#e2e8f0; font-size:0.92em; margin:6px 0; background:rgba(0,0,0,0.25); padding:8px; border-radius:6px;">
                    👁️ <b>المشاهدة الفعلية:</b> {obs.get('what_i_saw')}
                </div>
                <small style="color:#94a3b8;">📅 التاريخ: {obs.get('date')} | ⏰ الوقت: {obs.get('time')}</small>
            </div>
            """,
          unsafe_allow_html=True,
      )

      if obs.get("photo"):
        with st.expander(f"🖼️ صورة الإثبات المشاهدة ({obs.get('location')})"):
          st.image(obs["photo"], use_container_width=True)

# ------------------------------------------------------------------------------
# 3. توليد تقرير الواتساب الميداني (لغة رصينة ومباشرة للإدارة والتسويق)
# ------------------------------------------------------------------------------
with tab_report:
  st.markdown("##### 📊 تقرير مطابقة الواقع الميداني:")
  st.caption(
      "تقرير تحليلي يترجم ما رأيته بعينك إلى نقاط عمل واضحة لكل قسم لمنع"
      " التضارب:"
  )

  today_str = datetime.now().strftime("%Y-%m-%d | %I:%M %p")

  obs_list = st.session_state["observations_db"]
  obs_lines = []
  for o in obs_list[-5:]:
    obs_lines.append(
        f"• الموقع: {o.get('location')} [{o.get('category')}]\n"
        f"  - المشاهدة الواقعية: {o.get('what_i_saw')}\n"
        f"  - التقييم: {o.get('compliance_status')} (المعني:"
        f" {o.get('assigned_to')})"
    )

  obs_text_block = (
      "\n\n".join(obs_lines)
      if obs_lines
      else "• كافة المرافق المرصودة مطابقة وسليمة."
  )

  whatsapp_report = f"""*تقرير رصد الواقع الميداني - {LOCATION_TAG}*
*التاريخ والوقت:* {today_str}
*الراصد الميداني:* {OBSERVER_NAME}
-------------------------------------------
*بيان المشاهدات الحية ومطابقة المعايير:*

{obs_text_block}

-------------------------------------------
💡 *التوصية الإدارية والتسويقية المشتركة:*
1. إلزام مقاولي الصيانة والنظافة بمعالجة المواقع غير المطابقة فوراً.
2. عدم تسكين أو ترويج أي غرفة مسجل عليها خلل حتى إشعار الإغلاق الرسمي.
3. العمليات موثقة بالصور والتوقيت الزمني لحماية الجميع."""

  st.text_area("معاينة التقرير:", value=whatsapp_report, height=260)

  encoded_report = urllib.parse.quote(whatsapp_report)
  wa_link = f"https://api.whatsapp.com/send?text={encoded_report}"

  st.markdown(
      f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 إرسال التقرير'
      " بالواتساب (اختر الإدارة / التسويق / المقاول من جوالك)</a>",
      unsafe_allow_html=True,
  )

# ------------------------------------------------------------------------------
# 4. الخزنة والتصدير المعتمد (PIN: 5050)
# ------------------------------------------------------------------------------
with tab_archive:
  st.markdown("##### 🔐 الخزنة الرقمية والأرشيف المعتمد:")

  pin_in = st.text_input("أدخل رمز المشرف للدخول (5050):", type="password")
  if pin_in == PERMANENT_PIN:
    st.success(f"🟢 الخزنة مؤمنة ومفتوحة بصلاحية المشرف ({OBSERVER_NAME}).")

    if st.session_state["observations_db"]:
      clean_data = []
      for row in st.session_state["observations_db"]:
        r_copy = row.copy()
        r_copy["photo"] = (
            "يوجد صورة موثقة" if r_copy.get("photo") else "بدون صورة"
        )
        clean_data.append(r_copy)

      df_obs = pd.DataFrame(clean_data)
      csv_bytes = df_obs.to_csv(index=False).encode("utf-8-sig")

      st.download_button(
          label="📥 تحميل سجل المشاهدات الميدانية الكامل (Excel CSV)",
          data=csv_bytes,
          file_name=f"Ground_Truth_Observations_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )
  elif pin_in:
    st.error("رمز المشرف غير صحيح.")
