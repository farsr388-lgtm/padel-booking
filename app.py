from datetime import datetime
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني السريع (واجهة مريحة ومبسطة)
# ==============================================================================
st.set_page_config(
    page_title="سكن جامعة 3 | المشرف الميداني",
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
    padding-top: 0.5rem !important; 
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
.header-box { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 12px; 
    padding: 12px; 
    margin-bottom: 10px; 
    text-align: center; 
}
.title-txt { font-size: 1.15em; font-weight: 900; color: #ffffff; }
.sub-txt { font-size: 0.8em; color: #94a3b8; margin-top: 2px; }
div[data-testid="stFormSubmitButton"] > button { 
    background: var(--primary) !important; 
    color: #022c22 !important; 
    font-weight: 900 !important; 
    height: 46px !important; 
    border-radius: 10px !important; 
    width: 100% !important; 
    border: none !important; 
}
.stat-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 6px;
}
.tag-red {
    background: rgba(239, 68, 68, 0.25);
    border: 1px solid rgba(239, 68, 68, 0.6);
    color: #fca5a5;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.75em;
    font-weight: 800;
}
.tag-green {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #6ee7b7;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 0.75em;
    font-weight: 800;
}
.wa-direct-btn {
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
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت وقواعد البيانات الآمنة (الرمز الدائم 5050)
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

if "manager_phone" not in st.session_state:
  st.session_state["manager_phone"] = "966500000000"

if "maintenance_db" not in st.session_state:
  st.session_state["maintenance_db"] = [
      {
          "room": "104",
          "item": "مكيف",
          "time": "09:30 ص",
          "closed": None,
          "status": "مفتوح",
      },
  ]

if "violations_db" not in st.session_state:
  st.session_state["violations_db"] = [
      {
          "room": "108",
          "type": "سخان",
          "reason": "هيتر طبخ بالغرفة",
          "count": 1,
          "date": "2026-11-07 09:15 م",
      },
  ]

if "meals_db" not in st.session_state:
  st.session_state["meals_db"] = []

if "rounds_db" not in st.session_state:
  st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
  st.session_state["is_supervisor"] = False

# ==============================================================================
# 3. الترويسة الرئيسية + التبويبات الثلاثة فقط
# ==============================================================================
st.markdown(
    f"""
<div class="header-box">
    <div class="title-txt">⚡ تشغيل {LOCATION_TAG}</div>
    <div class="sub-txt">النظام الميداني السريع • راحة بال وتحكم كامل</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_quick, tab_report, tab_vault = st.tabs([
    "⚡ تسجيل سريع",
    "📋 تقرير المدير (عمر)",
    "🔐 الخزنة والأرشيف",
])

# ------------------------------------------------------------------------------
# 1. تبويب التسجيل السريع (كل العمليات الميدانية مدمجة في صفحة واحدة)
# ------------------------------------------------------------------------------
with tab_quick:
  # أ) حصر الأكل
  with st.expander("🍽️ حصر وجبة اليوم (اضغط للتسجيل)", expanded=False):
    with st.form("quick_meal", clear_on_submit=False):
      c1, c2, c3 = st.columns(3)
      with c1:
        deliv = st.number_input("جات:", min_value=0, max_value=600, value=77)
      with c2:
        coups = st.number_input("كوبون:", min_value=0, max_value=600, value=42)
      with c3:
        surp = st.number_input("فائض:", min_value=0, max_value=600, value=0)

      btn_m = st.form_submit_button("حفظ الأكل")
      if btn_m:
        dist = max(0, deliv - surp)
        no_cp = max(0, dist - coups)
        st.session_state["meals_db"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "delivered": int(deliv),
            "coupons": int(coups),
            "surplus": int(surp),
            "distributed": int(dist),
            "no_coupon": int(no_cp),
        })
        st.success(f"تم الحفظ! (الموزع: {dist} | بدون كوبون: {no_cp})")

  # ب) تسجيل بلاغ صيانة
  with st.expander("🛠️ بلاغ صيانة جديد (مكيف / شطاف / سخان)", expanded=True):
    with st.form("quick_maint", clear_on_submit=True):
      m_room = st.text_input("رقم الغرفة:", placeholder="مثال: 104")
      m_item = st.radio(
          "القطعة:",
          ["مكيف ❄️", "شطاف 🚿", "سخان 🔥", "أخرى 🛠️"],
          horizontal=True,
      )

      custom_item = ""
      if "أخرى" in m_item:
        custom_item = st.text_input(
            "اكتب العطل:", placeholder="مثال: لمبة / فيش..."
        )

      btn_rep = st.form_submit_button("قيد بلاغ الصيانة")
      if btn_rep:
        clean_r = m_room.strip()
        final_item = (
            custom_item.strip()
            if ("أخرى" in m_item and custom_item.strip())
            else m_item.split()[0]
        )
        if clean_r:
          st.session_state["maintenance_db"].append({
              "room": clean_r,
              "item": final_item,
              "time": datetime.now().strftime("%I:%M %p"),
              "closed": None,
              "status": "مفتوح",
          })
          st.success(f"تم قيد عطل {final_item} غرفة {clean_r}")
        else:
          st.error("اكتب رقم الغرفة أولاً.")

  # ج) تسجيل مخالفة غرفة
  with st.expander("⚠️ مخالفة غرفة (سخان / نظافة)", expanded=False):
    with st.form("quick_viol", clear_on_submit=True):
      v_room = st.text_input("رقم الغرفة المخالفة:", placeholder="مثال: 108")
      v_type = st.radio(
          "المخالفة:", ["سخان ⚡", "نظافة 🗑️", "أخرى ⚠️"], horizontal=True
      )
      v_reason = st.text_input(
          "السبب المباشر:", placeholder="مثال: مشغل هيتر طبخ / تراكم زبالة..."
      )

      btn_v = st.form_submit_button("حفظ المخالفة")
      if btn_v:
        c_vr = v_room.strip()
        sel_t = v_type.split()[0]
        if c_vr:
          # حساب تكرار المخالفة لنفس الغرفة آلياً
          repeats = (
              sum(
                  1
                  for x in st.session_state["violations_db"]
                  if x.get("room") == c_vr and x.get("type") == sel_t
              )
              + 1
          )
          st.session_state["violations_db"].append({
              "room": c_vr,
              "type": sel_t,
              "reason": (
                  v_reason.strip() if v_reason.strip() else "مخالفة اشتراطات"
              ),
              "count": repeats,
              "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
          })
          st.success(f"تم تسجيل غرفة {c_vr} ({sel_t}) — للمرة الـ ({repeats})!")
        else:
          st.error("اكتب رقم الغرفة.")

  # د) جولة سريعة
  with st.expander("🚶 توثيق الجولة (صباح / ليل)", expanded=False):
    c_r1, c_r2 = st.columns(2)
    with c_r1:
      if st.button("اعتماد جولة الصباح (09:30 ص)", use_container_width=True):
        st.session_state["rounds_db"].append({
            "round": "جولة الصباح",
            "time": datetime.now().strftime("%I:%M %p"),
        })
        st.success("تم توثيق جولة الصباح ✓")
    with c_r2:
      if st.button("اعتماد جولة الليل (08:30 م)", use_container_width=True):
        st.session_state["rounds_db"].append({
            "round": "جولة الليل",
            "time": datetime.now().strftime("%I:%M %p"),
        })
        st.success("تم توثيق جولة الليل ✓")

  st.markdown("---")
  # قائمة سريعة بما هو مفتوح للإصلاح بنقرة واحدة
  st.markdown("##### 🛠️ الأعطال المعلقة (اضغط للإصلاح):")
  open_list = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  if open_list:
    for idx, row in enumerate(open_list):
      c_a, c_b = st.columns([2, 1])
      with c_a:
        st.markdown(
            f"**غرفة {row.get('room')}**: {row.get('item')} <small"
            f" style='color:#94a3b8;'>({row.get('time')})</small>",
            unsafe_allow_html=True,
        )
      with c_b:
        if st.button("تم تصليحه ✓", key=f"fix_btn_{idx}"):
          row["status"] = "تم الإصلاح"
          row["closed"] = datetime.now().strftime("%I:%M %p")
          st.success(f"تم تصليح عطل غرفة {row.get('room')}!")
          st.rerun()
  else:
    st.info("ما فيه أي أعطال معلقة حالياً، السكن سليم.")

# ------------------------------------------------------------------------------
# 2. تبويب تقرير المدير (عمر) - رسالة واتساب جاهزة بزر مباشر
# ------------------------------------------------------------------------------
with tab_report:
  st.markdown("##### 📋 تقرير اليوم لمدير السكن (عمر):")
  st.caption("ملخص مركز وجاهز يرسل بضغطة زر واحدة على الواتساب:")

  today_str = datetime.now().strftime("%Y-%m-%d")

  # قراءة الوجبة
  m_data = (
      st.session_state["meals_db"][-1]
      if st.session_state["meals_db"]
      else {"delivered": 77, "coupons": 42, "surplus": 0}
  )

  # قراءة الصيانة
  fixed_today = [
      f"  • تم تصليح {x.get('item')} غرفة {x.get('room')} (الساعة {x.get('closed', 'اليوم')})"
      for x in st.session_state["maintenance_db"]
      if x.get("status") == "تم الإصلاح"
  ]
  fixed_txt = (
      "\n".join(fixed_today)
      if fixed_today
      else "  • لا توجد أعطال تم إصلاحها اليوم."
  )

  pending_today = [
      f"  • غرفة {x.get('room')}: {x.get('item')} (مسجل {x.get('time', '')})"
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  pending_txt = (
      "\n".join(pending_today)
      if pending_today
      else "  • لا توجد أعطال معلقة."
  )

  # قراءة المخالفات
  viols_today = [
      f"  • غرفة {v.get('room')}: {v.get('type')} (المرة {v.get('count', 1)})"
      f" - السبب: {v.get('reason')} [{v.get('date', '')}]"
      for v in st.session_state["violations_db"][-4:]
  ]
  viols_txt = (
      "\n".join(viols_today)
      if viols_today
      else "  • السجل نظيف ولا توجد مخالفات."
  )

  # آخر جولة
  last_r = (
      st.session_state["rounds_db"][-1].get("round", "تم التفتيش")
      if st.session_state["rounds_db"]
      else "تمت الجولات الدورية"
  )

  # الرسالة العادية والمباشرة للمدير
  report_msg = f"""مساك الله بالخير أبو عمر،،
تقرير {LOCATION_TAG} اليومي ({today_str}):

1️⃣ الإعاشة:
- الوجبات اللي جات: {m_data.get('delivered', 0)}
- المستلم بكوبون: {m_data.get('coupons', 0)}
- الفائض بالصواني: {m_data.get('surplus', 0)}

2️⃣ الصيانة:
- المنجز:
{fixed_txt}
- المعلق:
{pending_txt}

3️⃣ المخالفات:
{viols_txt}

4️⃣ الجولات الميدانية: {last_r}
الوضع العام بالسكن هادئ وكل شيء تحت السيطرة."""

  st.text_area("معاينة التقرير:", value=report_msg, height=250)

  # زر الواتساب للمدير مباشرة
  enc_msg = urllib.parse.quote(report_msg)
  mgr_phone = st.session_state["manager_phone"]
  wa_link = f"https://wa.me/{mgr_phone}?text={enc_msg}"

  st.markdown(
      f'<a href="{wa_link}" target="_blank" class="wa-direct-btn">📲 إرسال'
      " التقرير لأبو عمر عبر واتساب</a>",
      unsafe_allow_html=True,
  )

  with st.expander("⚙️ تعديل رقم جوال المدير"):
    new_phone = st.text_input(
        "رقم المدير (مع مفتاح 966):", value=st.session_state["manager_phone"]
    )
    if st.button("حفظ رقم المدير"):
      st.session_state["manager_phone"] = new_phone.strip()
      st.success("تم تحديث الرقم!")
      st.rerun()

# ------------------------------------------------------------------------------
# 3. تبويب الخزنة والأرشيف (الرمز 5050 وتنزيل Excel)
# ------------------------------------------------------------------------------
with tab_vault:
  st.markdown("##### 🔐 الخزنة والأرشيف:")

  if not st.session_state["is_supervisor"]:
    pin_in = st.text_input("رمز الدخول (5050):", type="password")
    if st.button("🔓 فتح الخزنة", use_container_width=True):
      if hmac.compare_digest(pin_in.strip().encode(), PERMANENT_PIN.encode()):
        st.session_state["is_supervisor"] = True
        st.rerun()
      else:
        st.error("الرمز غير صحيح.")
  else:
    st.success("🟢 الخزنة مفتوحة.")
    if st.button("🔒 قفل الخزنة"):
      st.session_state["is_supervisor"] = False
      st.rerun()

    st.divider()
    st.markdown("###### 📥 تنزيل ملفات Excel المعتمدة:")

    if st.session_state["violations_db"]:
      df_v = pd.DataFrame(st.session_state["violations_db"])
      st.download_button(
          label="تحميل تقرير المخالفات والتكرار (Excel)",
          data=df_v.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Violations_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["maintenance_db"]:
      df_m = pd.DataFrame(st.session_state["maintenance_db"])
      st.download_button(
          label="تحميل سجل الصيانة ووقت الإصلاح (Excel)",
          data=df_m.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Maintenance_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["meals_db"]:
      df_meals = pd.DataFrame(st.session_state["meals_db"])
      st.download_button(
          label="تحميل سجل الإعاشة اليومي (Excel)",
          data=df_meals.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Meals_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )
