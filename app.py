from datetime import datetime
import hmac
import math
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (RTL / Dark Mode / 430px One-Thumb UX)
# ==============================================================================
st.set_page_config(
    page_title="منظومة سكن جامعة 3 | التشغيل والتوسع الشامل",
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
    padding-bottom: 2.5rem !important; 
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
.header-card { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 12px; 
    padding: 12px; 
    margin-bottom: 10px; 
    text-align: center; 
}
.headline { font-size: 1.15em; font-weight: 900; color: #ffffff; margin: 0; }
.sub-headline { font-size: 0.8em; font-weight: 700; color: #94a3b8; margin-top: 3px; }
div[data-testid="stFormSubmitButton"] > button { 
    background: var(--primary) !important; 
    color: #022c22 !important; 
    font-weight: 900 !important; 
    height: 46px !important; 
    border-radius: 10px !important; 
    width: 100% !important; 
    border: none !important; 
    font-size: 1.02em !important; 
}
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9px;
    padding: 10px 12px;
    margin-bottom: 7px;
}
.badge-green {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #6ee7b7;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76em;
    font-weight: 800;
}
.badge-red {
    background: rgba(239, 68, 68, 0.25);
    border: 1px solid rgba(239, 68, 68, 0.6);
    color: #fca5a5;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76em;
    font-weight: 800;
}
.badge-blue {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.6);
    color: #93c5fd;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76em;
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
    font-size: 1.02em;
    text-decoration: none !important;
    margin-top: 8px;
    margin-bottom: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت العامة وقواعد البيانات المحمية (Zero-NameError)
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

now = datetime.now()
now_str = now.strftime("%Y-%m-%d | %I:%M %p")
now_minutes = now.hour * 60 + now.minute
is_friday = now.weekday() == 4

# أ) سجل الجولة الصباحية وحملة الجمعة
if "morning_round_note" not in st.session_state:
  st.session_state["morning_round_note"] = (
      "تم التفتيش الصباحي، الممرات نظيفة، والوضع العام منضبط"
  )

# ب) سجل الصيانة والسباكة ومطابقة الوعد التسويقي
if "maintenance_db" not in st.session_state:
  st.session_state["maintenance_db"] = [
      {
          "location": "السطح",
          "item": "صنبور / بزبوز موية",
          "desc": "تهريب شديد ويبق موية بقوة على العازل",
          "promise_match": "خلل تشغيلي حرج 🚨",
          "time": "10:15 ص",
          "status": "مفتوح",
          "closed_at": None,
          "photo": None,
      },
      {
          "location": "غرفة 213",
          "item": "مكيف",
          "desc": "صوت عالي وتبريد ضعيف وتنقيط ماء",
          "promise_match": "غير مطابق للوعد التسويقي ❌",
          "time": "09:30 ص",
          "status": "مفتوح",
          "closed_at": None,
          "photo": None,
      },
  ]

# ج) سجل المخالفات والسلامة (السخانات والنظافة)
if "violations_db" not in st.session_state:
  st.session_state["violations_db"] = [
      {
          "location": "غرفة 108",
          "type": "سخان / هيتر طبخ",
          "desc": "تشغيل هيتر طبخ على الأرض (خطر حريق)",
          "count": 2,
          "time": "09:15 م",
          "photo": None,
      }
  ]

# د) سجل الإعاشة والوجبات
if "meals_db" not in st.session_state:
  st.session_state["meals_db"] = []

# هـ) سجل التوسع الرأسي (شراء قطع الغيار بالجملة وتجاوز عمولة المقاول)
if "vertical_inventory" not in st.session_state:
  st.session_state["vertical_inventory"] = [
      {
          "item": "شطاف حمام أصلي",
          "qty": 18,
          "cost_direct": 22.0,
          "contractor_quote": 65.0,
      },
      {
          "item": "صنبور / بزبوز مياه نحاس",
          "qty": 10,
          "cost_direct": 30.0,
          "contractor_quote": 85.0,
      },
      {
          "item": "فلتر مكيف سبليت",
          "qty": 25,
          "cost_direct": 15.0,
          "contractor_quote": 45.0,
      },
  ]

# و) سجل التوسع الأفقي (إضافة خدمات جديدة وتوسيع الإدارة للعمائر 1 و2 و3)
if "horizontal_services" not in st.session_state:
  st.session_state["horizontal_services"] = [
      {
          "building": "سكن جامعة 3",
          "room": "213",
          "service": "غسيل وكوي ملابس",
          "fee": 25.0,
          "date": "2026-11-09",
      },
      {
          "building": "سكن جامعة 3",
          "room": "104",
          "service": "تنظيف غرفة خاص",
          "fee": 50.0,
          "date": "2026-11-10",
      },
      {
          "building": "سكن جامعة 2",
          "room": "301",
          "service": "مكائن قهوة وسناكات",
          "fee": 15.0,
          "date": "2026-11-10",
      },
  ]

# ==============================================================================
# 3. محرك فحص ساعات الأكل الرسمية تلقائياً
# ==============================================================================
# الفطور: 05:30 ص (330) -> 07:00 ص (420)
# الغداء: 11:30 ص (690) -> 02:30 م (870)
# العشاء: 05:30 م (1050) -> 09:00 م (1260)

if 330 <= now_minutes <= 420:
  meal_window_status = "🟢 وقت الفطور مفتوح الآن (05:30 ص - 07:00 ص)"
  default_meal_idx = 0
  meal_is_open = True
elif 690 <= now_minutes <= 870:
  meal_window_status = "🟢 وقت الغداء مفتوح الآن (11:30 ص - 02:30 م)"
  default_meal_idx = 1
  meal_is_open = True
elif 1050 <= now_minutes <= 1260:
  meal_window_status = "🟢 وقت العشاء مفتوح الآن (05:30 م - 09:00 م)"
  default_meal_idx = 2
  meal_is_open = True
else:
  meal_is_open = False
  if now_minutes < 330:
    meal_window_status = "🕒 مغلق حالياً - الوجبة القادمة: الفطور (05:30 ص)"
    default_meal_idx = 0
  elif now_minutes < 690:
    meal_window_status = "🕒 مغلق حالياً - الوجبة القادمة: الغداء (11:30 ص)"
    default_meal_idx = 1
  elif now_minutes < 1050:
    meal_window_status = "🕒 مغلق حالياً - الوجبة القادمة: العشاء (05:30 م)"
    default_meal_idx = 2
  else:
    meal_window_status = "🕒 انتهت وجبات اليوم - موعدنا فطور الغد (05:30 ص)"
    default_meal_idx = 0

# حساب المؤشرات الاستراتيجية
df_v = pd.DataFrame(st.session_state["vertical_inventory"])
total_saved_vert = int(
    ((df_v["contractor_quote"] - df_v["cost_direct"]) * df_v["qty"]).sum()
)
df_h = pd.DataFrame(st.session_state["horizontal_services"])
total_rev_horiz = int(df_h["fee"].sum())

# ==============================================================================
# 4. الترويسة الرئيسية والتبويبات المنظمة
# ==============================================================================
st.markdown(
    f"""
<div class="header-card">
    <div class="headline">🏢 منظومة {LOCATION_TAG} الشاملة</div>
    <div class="sub-headline">المشرف: {SUPERVISOR_NAME} • التشغيل الميداني والتوسع الاستراتيجي</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_daily, tab_meals, tab_expansion, tab_reports, tab_lessons = st.tabs([
    "⚡ 1. الوردية والصيانة",
    "🍽️ 2. الأكل وساعته",
    "🚀 3. التوسع (رأسي/أفقي)",
    "📲 4. التقارير والخزنة",
    "🎓 5. الدروس والمبادئ",
])

# ------------------------------------------------------------------------------
# التبويب 1: الوردية الميدانية (جولة الصباح + الصيانة والسطح + المخالفات)
# ------------------------------------------------------------------------------
with tab_daily:
  st.markdown("##### 🚶 أولاً: جولة الصباح وحملة نظافة الجمعة")
  with st.expander("توثيق الجولة التفتيشية الصباحية", expanded=False):
    round_type = st.radio(
        "نوع الجولة:",
        [
            "جولة الصباح اليومية (09:30 ص)",
            "حملة نظافة الجمعة الصباح 🧹 (غسيل ممرات وتفتيش السطح والسباكة)",
            "جولة المساء (08:30 م)",
        ],
        index=1 if is_friday and now.hour < 12 else 0,
    )
    r_note_in = st.text_input(
        "ملاحظة الجولة التي شاهدتها بعينك:",
        value=st.session_state["morning_round_note"],
    )
    if st.button("⚡ اعتماد الجولة التفتيشية"):
      st.session_state["morning_round_note"] = f"[{round_type}] {r_note_in}"
      st.success("تم حفظ وتحديث الجولة بنجاح!")

  st.markdown("##### 🛠️ ثانياً: تسجيل عطل (السطح / صنبور يبق موية / مكيف)")
  with st.expander(
      "إضافة بلاغ صيانة أو عدم مطابقة للوعد التسويقي", expanded=True
  ):
    with st.form("form_maint_unified", clear_on_submit=True):
      m_loc = st.text_input(
          "📍 الموقع (اكتب رقم غرفة مثل 104 أو اسم مثل: السطح، الممر):",
          placeholder="مثال: السطح أو 104",
      )
      m_item = st.selectbox(
          "🔧 نوع العطل:",
          [
              "صنبور / بزبوز موية 🚰 (تهريب / يبق موية)",
              "مكيف ❄️ (تنقيط ماء / تبريد ضعيف)",
              "شطاف 🚿 (تهريب / كسر)",
              "سخان موية 🔥",
              "نظافة ومخلفات 🗑️",
              "أخرى 🛠️",
          ],
      )
      m_desc = st.text_input(
          "👁️ صِف ما رأيته بعينك بدقة:",
          placeholder=(
              "مثال: الصنبور بالسطح مكسور ويبق موية بقوة / المكيف يقطر..."
          ),
      )
      m_promise = st.selectbox(
          "⚖️ مطابقة الغرفة/المرفق للوعد التسويقي (إدارة التخصصات):",
          [
              "ملاحظة تشغيلية عادية ⚠️",
              "غير مطابق للوعد التسويقي (يوقف التسكين) ❌",
              "خلل تشغيلي حرج / هدر مياه 🚨",
          ],
      )
      m_photo = st.file_uploader(
          "📷 صورة إثبات العطل (اختياري):", type=["jpg", "jpeg", "png"]
      )

      if st.form_submit_button("⚡ حفظ بلاغ الصيانة"):
        c_loc = m_loc.strip()
        final_loc = f"غرفة {c_loc}" if c_loc.isdigit() else c_loc
        if c_loc:
          p_bytes = m_photo.getvalue() if m_photo else None
          st.session_state["maintenance_db"].append({
              "location": final_loc,
              "item": m_item.split()[0] + " " + m_item.split()[1],
              "desc": (
                  m_desc.strip()
                  if m_desc.strip()
                  else "تم رصد العطل بالوردية"
              ),
              "promise_match": m_promise,
              "time": datetime.now().strftime("%I:%M %p"),
              "status": "مفتوح",
              "closed_at": None,
              "photo": p_bytes,
          })
          st.success(f"تم توثيق بلاغ ({final_loc}) بنجاح!")
          st.rerun()
        else:
          st.error("الرجاء كتابة الموقع أولاً.")

  st.markdown("##### ⚠️ ثالثاً: رصد المخالفات (السخانات والنظافة)")
  with st.expander("تسجيل مخالفة غرفة وحساب التكرار آلياً", expanded=False):
    with st.form("form_viol_unified", clear_on_submit=True):
      v_loc = st.text_input(
          "موقع المخالفة (مثل 108 أو السطح):", placeholder="مثال: 108"
      )
      v_type = st.radio(
          "نوع المخالفة:",
          [
              "سخان / هيتر طبخ ⚡",
              "إهمال نظافة ونفايات 🗑️",
              "هدر مياه 🚰",
          ],
          horizontal=True,
      )
      v_desc = st.text_input(
          "تفاصيل المخالفة:", placeholder="تشغيل هيتر طبخ على الفرش..."
      )
      v_photo = st.file_uploader(
          "📷 صورة المخالفة:", type=["jpg", "jpeg", "png"]
      )

      if st.form_submit_button("⚡ توثيق المخالفة"):
        cv = v_loc.strip()
        fv = f"غرفة {cv}" if cv.isdigit() else cv
        ct = v_type.split()[0]
        if cv:
          rep_cnt = (
              sum(
                  1
                  for x in st.session_state["violations_db"]
                  if x.get("location") == fv and ct in x.get("type", "")
              )
              + 1
          )
          vb = v_photo.getvalue() if v_photo else None
          st.session_state["violations_db"].append({
              "location": fv,
              "type": ct,
              "desc": (
                  v_desc.strip() if v_desc.strip() else "مخالفة تعليمات السكن"
              ),
              "count": rep_cnt,
              "time": datetime.now().strftime("%I:%M %p"),
              "photo": vb,
          })
          st.success(f"تم رصد مخالفة {fv} — المرة الـ ({rep_cnt})!")
          st.rerun()
        else:
          st.error("اكتب رقم الغرفة أو الموقع.")

  st.markdown("---")
  st.markdown("##### 📋 البلاغات المفتوحة حالياً (اضغط للإصلاح الفوري):")
  open_list = [
      x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"
  ]
  if open_list:
    for i, r in enumerate(open_list):
      col_a, col_b = st.columns([2.6, 1.4])
      with col_a:
        st.markdown(
            f"<b>📍 {r['location']}</b>: {r['item']}<br><small"
            f" style='color:#cbd5e1;'>👁️ {r['desc']}</small><br><span"
            f" class='badge-red'>{r.get('promise_match', '')}</span>",
            unsafe_allow_html=True,
        )
        if r.get("photo"):
          with st.expander("🖼️ عرض الصورة"):
            st.image(r["photo"], use_container_width=True)
      with col_b:
        if st.button("تم إصلاحه ✓", key=f"fix_unified_{i}"):
          r["status"] = "تم الإصلاح"
          r["closed_at"] = datetime.now().strftime("%I:%M %p")
          st.rerun()
  else:
    st.info("كافة المرافق سليمة ولا توجد أعطال معلقة.")

# ------------------------------------------------------------------------------
# التبويب 2: الأكل وساعته والقرار العلمي
# ------------------------------------------------------------------------------
with tab_meals:
  st.markdown("##### 🕒 نافذة مواعيد الأكل الرسمية:")
  b_cls = "badge-green" if meal_is_open else "badge-blue"
  st.markdown(
      f"""
        <div class="stat-box">
            <span class="{b_cls}">{meal_window_status}</span><br>
            <small style="color:#cbd5e1; display:inline-block; margin-top:6px;">
                • <b>الفطور:</b> 05:30 ص - 07:00 ص | • <b>الغداء:</b> 11:30 ص - 02:30 م | • <b>العشاء:</b> 05:30 م - 09:00 م
            </small>
        </div>
        """,
      unsafe_allow_html=True,
  )

  with st.form("form_meals_unified", clear_on_submit=False):
    m_choice = st.selectbox(
        "الوجبة:", ["فطور", "غداء", "عشاء"], index=default_meal_idx
    )
    c1, c2, c3 = st.columns(3)
    with c1:
      d_in = st.number_input("المستلم (جات):", min_value=0, value=77)
    with c2:
      c_in = st.number_input("بكوبون:", min_value=0, value=42)
    with c3:
      s_in = st.number_input("الفائض بالصواني:", min_value=0, value=0)

    actual_used = max(0, d_in - s_in)
    without_coup = max(0, actual_used - c_in)
    safety_margin = math.ceil(actual_used * 0.03) if actual_used > 0 else 0
    next_order_rec = actual_used + safety_margin

    if st.form_submit_button("⚡ حفظ الوجبة واحتساب القرار العلمي"):
      st.session_state["meals_db"].append({
          "meal": m_choice,
          "time": datetime.now().strftime("%I:%M %p"),
          "date": datetime.now().strftime("%Y-%m-%d"),
          "delivered": int(d_in),
          "coupons": int(c_in),
          "surplus": int(s_in),
          "distributed": int(actual_used),
          "no_coupon": int(without_coup),
          "recommended": int(next_order_rec),
      })
      st.success(
          f"تم حفظ وجبة {m_choice}! المستهلك الفعلي: {actual_used} شخص."
      )

  k1, k2 = st.columns(2)
  k1.metric("المستهلك الفعلي", f"{actual_used} شخص")
  k2.metric("صرف بدون كوبون", f"{without_coup} وجبة")
  st.info(
      f"💡 **القرار العلمي للوجبة القادمة:** اطلب **{next_order_rec} وجبة**"
      f" (الفعلي + 3% طوارئ) لتوفير **{max(0, d_in - next_order_rec)} وجبة** من"
      " الهدر."
  )

# ------------------------------------------------------------------------------
# التبويب 3: التوسع الرأسي (المخزون) والتوسع الأفقي (الخدمات والعمائر)
# ------------------------------------------------------------------------------
with tab_expansion:
  st.markdown("##### 🚀 تطبيق استراتيجيات النمو على السكن:")
  ck1, ck2 = st.columns(2)
  ck1.metric(
      "وفر التوسع الرأسي 📉",
      f"{total_saved_vert} ريال",
      delta="شراء مباشر بلا وسيط",
  )
  ck2.metric(
      "دخل التوسع الأفقي 📈",
      f"{total_rev_horiz} ريال",
      delta="خدمات إضافية وعمائر",
  )

  with st.expander(
      "⚙️ 1. التوسع الرأسي (تأمين قطع الغيار بالجملة بدل المقاول)",
      expanded=True,
  ):
    with st.form("vert_form_unified", clear_on_submit=True):
      vi_name = st.text_input(
          "الصنف (مثل: شطاف، صنبور نحاس، فلتر مكيف):",
          placeholder="مثال: قلب صنبور أصلي",
      )
      vc1, vc2, vc3 = st.columns(3)
      with vc1:
        vi_qty = st.number_input("الكمية:", min_value=1, value=10)
      with vc2:
        vi_dir = st.number_input("سعر الجملة:", min_value=1.0, value=25.0)
      with vc3:
        vi_con = st.number_input("سعر المقاول:", min_value=1.0, value=70.0)

      if st.form_submit_button("⚡ إضافة للمخزون الرأسي"):
        if vi_name.strip():
          st.session_state["vertical_inventory"].append({
              "item": vi_name.strip(),
              "qty": int(vi_qty),
              "cost_direct": float(vi_dir),
              "contractor_quote": float(vi_con),
          })
          st.rerun()

  with st.expander(
      "🛒 2. التوسع الأفقي (خدمات إضافية للنزلاء وإدارة عمائر 1 و2 و3)",
      expanded=False,
  ):
    with st.form("horiz_form_unified", clear_on_submit=True):
      hb_name = st.selectbox(
          "العمارة:", ["سكن جامعة 3", "سكن جامعة 2", "سكن جامعة 1"]
      )
      hr_num = st.text_input("رقم الغرفة:", placeholder="مثال: 213")
      hs_type = st.selectbox(
          "الخدمة المضافة:",
          [
              "غسيل وكوي ملابس 🧺",
              "تنظيف غرفة خاص 🧹",
              "مكائن قهوة وسناكات ☕",
          ],
      )
      hf_val = st.number_input("رسوم الخدمة (ريال):", min_value=5.0, value=25.0)

      if st.form_submit_button("⚡ تسجيل إيراد التوسع الأفقي"):
        if hr_num.strip():
          st.session_state["horizontal_services"].append({
              "building": hb_name,
              "room": hr_num.strip(),
              "service": hs_type,
              "fee": float(hf_val),
              "date": datetime.now().strftime("%Y-%m-%d"),
          })
          st.rerun()

# ------------------------------------------------------------------------------
# التبويب 4: مركز تقارير الواتساب الشامل + الخزنة والإكسل (5050)
# ------------------------------------------------------------------------------
with tab_reports:
  st.markdown("##### 📲 التقرير الشامل للوردية والاستراتيجية (واتساب مباشر):")

  last_m = (
      st.session_state["meals_db"][-1]
      if st.session_state["meals_db"]
      else {
          "meal": "عشاء",
          "time": "08:30 م",
          "delivered": 77,
          "coupons": 42,
          "surplus": 0,
          "distributed": 77,
          "recommended": 77,
      }
  )

  open_m = [
      x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"
  ]
  fixed_m = [
      x
      for x in st.session_state["maintenance_db"]
      if x["status"] == "تم الإصلاح"
  ]

  open_txt = (
      "\n".join([
          f"  • {x['location']}: {x['item']} ({x['desc']}) -"
          f" [{x.get('promise_match', '')}]"
          for x in open_m
      ])
      if open_m
      else "  • لا توجد أعطال معلقة."
  )
  fixed_txt = (
      "\n".join([
          f"  • {x['location']}: تم إصلاح {x['item']}"
          f" ({x.get('closed_at', 'اليوم')})"
          for x in fixed_m
      ])
      if fixed_m
      else "  • لا توجد صيانات مغلقة اليوم."
  )
  viol_txt = (
      "\n".join([
          f"  • {v['location']}: {v['type']} (المرة {v['count']}) - {v['desc']}"
          for v in st.session_state["violations_db"][-4:]
      ])
      if st.session_state["violations_db"]
      else "  • السجل نظيف."
  )

  master_wa_report = f"""*التقرير الميداني والاستراتيجي الشامل - {LOCATION_TAG}*
*التاريخ:* {now_str} | *المشرف:* {SUPERVISOR_NAME}
-------------------------------------------
*1️⃣ الجولة التفتيشية الصباحية:*
• {st.session_state['morning_round_note']}

*2️⃣ الإعاشة والقرار العلمي [{last_m['meal']}]:*
• المستلم: {last_m['delivered']} | بكوبون: {last_m['coupons']} | الفائض: {last_m['surplus']}
• المستهلك الفعلي: {last_m['distributed']} شخص
💡 *الطلب المعتمد للوجبة القادمة:* ({last_m['recommended']} وجبة) شاملة 3% طوارئ لمنع الهدر.

*3️⃣ الصيانة والسباكة ومطابقة الوعد التسويقي:*
- المعلق ({len(open_m)}):
{open_txt}
- المنجز ({len(fixed_m)}):
{fixed_txt}

*4️⃣ الرقابة والسلامة (المخالفات):*
{viol_txt}

*5️⃣ العائد الاستراتيجي (التوسع الرأسي والأفقي):*
• وفر التوسع الرأسي (تأمين قطع الغيار مباشر): {total_saved_vert} ريال.
• دخل التوسع الأفقي (خدمات النزلاء والعمائر): +{total_rev_horiz} ريال.
-------------------------------------------"""

  st.text_area("معاينة التقرير الشامل:", value=master_wa_report, height=260)

  wa_url = (
      f"https://api.whatsapp.com/send?text={urllib.parse.quote(master_wa_report)}"
  )
  st.markdown(
      f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال التقرير عبر'
      " واتساب (اختر الشخص أو القروب من جوالك)</a>",
      unsafe_allow_html=True,
  )

  st.divider()
  with st.expander("🔐 الخزنة وتصدير كشوفات Excel المعتمدة (الرمز: 5050)"):
    pin_in = st.text_input("أدخل رمز المشرف:", type="password")
    if hmac.compare_digest(pin_in.strip().encode(), PERMANENT_PIN.encode()):
      st.success("🟢 الخزنة مفتوحة!")
      clean_m = [
          {k: v for k, v in r.items() if k != "photo"}
          for r in st.session_state["maintenance_db"]
      ]
      st.download_button(
          "📥 تحميل سجل الصيانة ومطابقة الواقع (Excel)",
          data=pd.DataFrame(clean_m).to_csv(index=False).encode("utf-8-sig"),
          file_name="Maintenance_Log.csv",
          use_container_width=True,
      )
      st.download_button(
          "📥 تحميل سجل وفر التوسع الرأسي (Excel)",
          data=df_v.to_csv(index=False).encode("utf-8-sig"),
          file_name="Vertical_Expansion.csv",
          use_container_width=True,
      )
      st.download_button(
          "📥 تحميل سجل دخل التوسع الأفقي (Excel)",
          data=df_h.to_csv(index=False).encode("utf-8-sig"),
          file_name="Horizontal_Expansion.csv",
          use_container_width=True,
      )
    elif pin_in:
      st.error("الرمز غير صحيح.")

# ------------------------------------------------------------------------------
# التبويب 5: مرجع الدروس الجامعية والمبادئ الإدارية (الخلاصة العلمية)
# ------------------------------------------------------------------------------
with tab_lessons:
  st.markdown("##### 🎓 مرجع الدروس الجامعية المطبقة في هذا النظام:")
  st.markdown(
      """
        <div class="stat-box">
            <b>1. إدارة التخصصات المختلفة:</b><br>
            • خلق لغة أرقام مشتركة يفهمها التسويق والصيانة والإدارة.<br>
            • المشرف يعمل كـ <b>"مترجم وسيط"</b> يمنع تسكين أي غرفة غير مطابقة للوعد التسويقي.<br>
            • استخدام لوحة بصرية موحدة وأهداف مشتركة تمنع الازدواجية.
        </div>
        <div class="stat-box">
            <b>2. استراتيجية التوسع الرأسي (مثال ستاربكس):</b><br>
            • السيطرة على سلسلة العمل بتأمين قطع الغيار (شطافات/صنابير/فلاتر) مباشرة بدلاً من عمولة المقاول الوسيط.<br>
            • يحقق استقلالية أكبر، يخفض التكاليف، ويرفع الجودة وسرعة الإصلاح.
        </div>
        <div class="stat-box">
            <b>3. استراتيجية التوسع الأفقي (مثال مطعم الدمام):</b><br>
            • البناء على النشاط الأساسي بإضافة خدمات جديدة لنفس السكان (غسيل، تنظيف خاص، مكائن قهوة) وتوسيع الإدارة لتشمل عمارة 1 و 2 و 3.<br>
            • يرفع العائد المالي ويستغل الموارد الحالية بأفضل شكل.
        </div>
        """,
      unsafe_allow_html=True,
  )
