from datetime import datetime
import hmac
import math
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (RTL / Dark Mode / Mobile-First)
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
    margin-bottom: 6px;
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
# 2. الثوابت العامة وإدارة الجلسة الآمنة
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

if "maintenance_db" not in st.session_state:
  st.session_state["maintenance_db"] = [
      {
          "location": "غرفة 104",
          "item": "مكيف",
          "desc": "تنقيط ماء وتجمع أوساخ تحت الوحدة",
          "opened_at": "09:30 ص",
          "date": "2026-11-07",
          "closed_at": None,
          "status": "مفتوح",
          "photo": None,
      },
      {
          "location": "السطح",
          "item": "صنبور / بزبوز موية",
          "desc": "تهريب شديد ويبق موية بقوة",
          "opened_at": "10:15 ص",
          "date": "2026-11-08",
          "closed_at": None,
          "status": "مفتوح",
          "photo": None,
      },
  ]
else:
  for row in st.session_state["maintenance_db"]:
    if "location" not in row:
      row["location"] = row.get("room", "موقع عام")
    if "desc" not in row:
      row["desc"] = ""
    if "opened_at" not in row:
      row["opened_at"] = row.get("time", "اليوم")
    if "date" not in row:
      row["date"] = datetime.now().strftime("%Y-%m-%d")
    if "status" not in row:
      row["status"] = "مفتوح"
    if "closed_at" not in row:
      row["closed_at"] = None
    if "photo" not in row:
      row["photo"] = None

if "violations_db" not in st.session_state:
  st.session_state["violations_db"] = [
      {
          "location": "غرفة 108",
          "type": "سخان",
          "reason": "استخدام هيتر طبخ على الأرض",
          "count": 1,
          "time": "09:15 م",
          "date": "2026-11-05",
          "photo": None,
      },
      {
          "location": "غرفة 108",
          "type": "سخان",
          "reason": "تكرار تشغيل هيتر مخالف (خطر حريق)",
          "count": 2,
          "time": "10:30 م",
          "date": "2026-11-07",
          "photo": None,
      },
  ]
else:
  for v in st.session_state["violations_db"]:
    if "location" not in v:
      v["location"] = v.get("room", "غرفة غير محددة")

if "meals_db" not in st.session_state:
  st.session_state["meals_db"] = []

if "rounds_db" not in st.session_state:
  st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
  st.session_state["is_supervisor"] = False

# محرك التوقيت الدقيق
now = datetime.now()
now_minutes = now.hour * 60 + now.minute
is_friday = now.weekday() == 4

if now_minutes < 570:
  auto_meal_idx = 0
  active_period_name = "الفطور (05:30 ص - 07:00 ص)"
  is_within_official_window = 330 <= now_minutes <= 420
elif now_minutes < 990:
  auto_meal_idx = 1
  active_period_name = "الغداء (11:30 ص - 02:30 م)"
  is_within_official_window = 690 <= now_minutes <= 870
else:
  auto_meal_idx = 2
  active_period_name = "العشاء (05:30 م - 09:00 م)"
  is_within_official_window = 1050 <= now_minutes <= 1260

# ==============================================================================
# 3. الترويسة الرئيسية
# ==============================================================================
st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 إدارة {LOCATION_TAG}</div>
    <div class="sub-headline">المشرف: {SUPERVISOR_NAME} • تسلسل الوردية الميداني</div>
</div>
""",
    unsafe_allow_html=True,
)

c_h1, c_h2 = st.columns([2, 1])
with c_h1:
  st.caption(f"📅 التوقيت: {now.strftime('%Y-%m-%d | %I:%M %p')}")
with c_h2:
  if st.button("🔄 تحديث الشاشة", use_container_width=True):
    st.rerun()

# التبويبات بالترتيب الزمني الدقيق للوردية
tab_rounds, tab_repairs, tab_viol, tab_meals, tab_report, tab_vault = st.tabs([
    "🚶 1. جولة الصباح",
    "🛠️ 2. الصيانة والسباكة",
    "⚠️ 3. رصد المخالفات",
    "🍽️ 4. الإعاشة والقرار",
    "📊 5. تقرير الوردية (واتساب)",
    "🔐 الخزنة والأرشيف",
])

# ------------------------------------------------------------------------------
# 1. تبويب أول ما أقوم: جولة الصباح اليومية أو حملة نظافة الجمعة
# ------------------------------------------------------------------------------
with tab_rounds:
  st.markdown("##### 🚶 1. التفتيش الميداني الصباحي (أول ما تقوم):")

  r_idx = 2 if is_friday and now.hour < 12 else (0 if now.hour < 14 else 1)

  with st.form("morning_round_form", clear_on_submit=True):
    sel_round = st.radio(
        "نوع الجولة:",
        [
            "جولة الصباح اليومية (09:30 ص)",
            "جولة الليل اليومية (08:30 م)",
            (
                "حملة نظافة الجمعة الصباح 🧹 (غسيل ممرات وتفتيش شامل للأسطح"
                " والسباكة)"
            ),
        ],
        index=r_idx,
    )
    r_note = st.text_input(
        "الملاحظة الميدانية الصباحية:",
        placeholder=(
            "مثال: تم التفتيش الصباحي، الممرات نظيفة، ورصد تسريب ماء بالسطح..."
        ),
    )
    btn_rnd = st.form_submit_button("⚡ اعتماد الجولة الصباحية")

    if btn_rnd:
      round_title = (
          sel_round.split()[0]
          + " "
          + sel_round.split()[1]
          + (" " + sel_round.split()[2] if "الجمعة" in sel_round else "")
      )
      st.session_state["rounds_db"].append({
          "date": datetime.now().strftime("%Y-%m-%d"),
          "time": datetime.now().strftime("%I:%M %p"),
          "round": round_title,
          "note": (
              r_note.strip()
              if r_note.strip()
              else (
                  "تمت الجولة الصباحية بنجاح والسكن سليم"
                  if "الصباح" in sel_round
                  else "السكن مستقر"
              )
          ),
      })
      st.success(f"تم اعتماد {round_title} بنجاح!")

  if st.session_state["rounds_db"]:
    st.markdown("---")
    for r in st.session_state["rounds_db"][-3:]:
      st.markdown(
          f"""
                <div class="stat-box">
                    <b>{r.get('round', '')}</b> — <small style="color:var(--primary);">{r.get('time', '')}</small><br>
                    <small style="color:#cbd5e1;">الملاحظة: {r.get('note', '')}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )

# ------------------------------------------------------------------------------
# 2. تبويب الصيانة: رصد السباكة، المكيفات، وصنابير السطح
# ------------------------------------------------------------------------------
with tab_repairs:
  st.markdown("##### 🛠️ 2. بلاغات الصيانة والسباكة المرصودة:")

  with st.form("quick_rep_form", clear_on_submit=True):
    r_loc = st.text_input(
        "الموقع أو رقم الغرفة (مثل: السطح، 104، الحمامات، ممر 1):",
        placeholder="مثال: السطح أو 104",
    )
    r_item = st.radio(
        "العطل:",
        [
            "صنبور / بزبوز موية 🚰 (تهريب / يبق موية)",
            "مكيف ❄️ (تنقيط / تبريد)",
            "شطاف 🚿 (تهريب / كسر)",
            "سخان موية 🔥",
            "أخرى 🛠️",
        ],
        horizontal=False,
    )
    other_text = ""
    if "أخرى" in r_item:
      other_text = st.text_input(
          "حدد العطل الآخر:", placeholder="لمبة / فيش / تسريب..."
      )

    r_desc = st.text_input(
        "شرح العطل بالتفصيل:",
        placeholder=(
            "مثال: الصنبور مكسور ويبق موية بقوة / المكيف يهرب ماء تحت"
            " الوحدة..."
        ),
    )
    rep_photo = st.file_uploader(
        "📷 صورة العطل (كاميرا أو استوديو):", type=["jpg", "jpeg", "png"]
    )

    btn_rep = st.form_submit_button("⚡ حفظ بلاغ الصيانة")

    if btn_rep:
      clean_loc = r_loc.strip()
      final_loc = f"غرفة {clean_loc}" if clean_loc.isdigit() else clean_loc
      final_item = (
          other_text.strip()
          if ("أخرى" in r_item and other_text.strip())
          else r_item.split()[0] + " " + r_item.split()[1]
      )

      if clean_loc:
        photo_bytes = rep_photo.getvalue() if rep_photo else None
        st.session_state["maintenance_db"].append({
            "location": final_loc,
            "item": final_item,
            "desc": (
                r_desc.strip() if r_desc.strip() else "تم رصد العطل ميدانياً"
            ),
            "opened_at": datetime.now().strftime("%I:%M %p"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "closed_at": None,
            "status": "مفتوح",
            "photo": photo_bytes,
        })
        st.success(f"تم قيد بلاغ {final_loc} ({final_item})!")
      else:
        st.error("اكتب الموقع أو رقم الغرفة.")

  st.markdown("---")
  st.markdown("##### 📋 البلاغات المعلقة (اضغط للإصلاح الفوري):")
  open_reps = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  if open_reps:
    for idx, row in enumerate(open_reps):
      c_a, c_b = st.columns([2, 1])
      with c_a:
        st.markdown(
            f"<b>{row.get('location')}</b>: {row.get('item')}<br><small"
            f" style='color:#cbd5e1;'>{row.get('desc')}</small> <small"
            f" style='color:#94a3b8;'>({row.get('opened_at')})</small>",
            unsafe_allow_html=True,
        )
        if row.get("photo"):
          with st.expander("🖼️ صورة العطل"):
            st.image(row["photo"], use_container_width=True)
      with c_b:
        if st.button("تم إصلاحه ✓", key=f"rep_btn_{idx}"):
          row["status"] = "تم الإصلاح"
          row["closed_at"] = datetime.now().strftime("%I:%M %p")
          st.success(
              f"أُصلح عطل {row.get('location')} الساعة {row['closed_at']}!"
          )
          st.rerun()
  else:
    st.info("لا توجد بلاغات صيانة معلقة.")

# ------------------------------------------------------------------------------
# 3. تبويب المخالفات: السخانات والهيترات والنظافة
# ------------------------------------------------------------------------------
with tab_viol:
  st.markdown("##### ⚠️ 3. رصد مخالفات الغرف والسلامة:")

  with st.form("quick_viol_form", clear_on_submit=True):
    v_loc = st.text_input(
        "الموقع أو رقم الغرفة المخالفة:", placeholder="مثال: 108 أو السطح"
    )
    v_type = st.radio(
        "نوع المخالفة:",
        [
            "سخان / هيتر طبخ ⚡ (خطر حريق مباشر)",
            "إهمال نظافة ونفايات 🗑️",
            "هدر ماء أو صنبور مفتوح 🚰",
            "سخان ونظافة معاً ⚠️",
            "أخرى 📝",
        ],
        horizontal=False,
    )
    custom_v = ""
    if "أخرى" in v_type:
      custom_v = st.text_input(
          "اكتب نوع المخالفة:", placeholder="تدخين / إزعاج..."
      )
    v_reason = st.text_input(
        "التفاصيل والرصد الميداني:",
        placeholder="مثال: تشغيل هيتر طبخ على الأرض / رمي نفايات...",
    )
    viol_photo = st.file_uploader(
        "📷 صورة إثبات المخالفة:", type=["jpg", "jpeg", "png"]
    )

    btn_v = st.form_submit_button("⚡ حفظ المخالفة وحساب التكرار")

    if btn_v:
      clean_v = v_loc.strip()
      final_v = f"غرفة {clean_v}" if clean_v.isdigit() else clean_v
      chosen_t = (
          custom_v.strip()
          if ("أخرى" in v_type and custom_v.strip())
          else v_type.split()[0] + " " + v_type.split()[1]
      )

      if clean_v:
        repeats = (
            sum(
                1
                for v in st.session_state["violations_db"]
                if v.get("location") == final_v and v.get("type") == chosen_t
            )
            + 1
        )
        v_bytes = viol_photo.getvalue() if viol_photo else None
        st.session_state["violations_db"].append({
            "location": final_v,
            "type": chosen_t,
            "reason": (
                v_reason.strip()
                if v_reason.strip()
                else "رصد مخالفة باشتراطات السكن"
            ),
            "count": repeats,
            "time": datetime.now().strftime("%I:%M %p"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "photo": v_bytes,
        })
        st.success(
            f"تم توثيق مخالفة {final_v} ({chosen_t}) — للمرة الـ ({repeats})!"
        )
      else:
        st.error("اكتب الموقع أو رقم الغرفة.")

  st.markdown("---")
  st.markdown("##### 📋 كشف سوابق ومخالفات الغرف:")
  if st.session_state["violations_db"]:
    for v in reversed(st.session_state["violations_db"][-4:]):
      c_num = v.get("count", 1)
      tag_c = "alert-tag" if c_num >= 2 else "done-tag"
      st.markdown(
          f"""
                <div class="stat-box" style="border-right: 3px solid #ef4444;">
                    <b>{v.get('location', '')}</b> — <span style="color:#f87171; font-weight:800;">{v.get('type', '')}</span>
                    <span class='{tag_c}'>المرة الـ {c_num}</span><br>
                    <small style="color:#cbd5e1;">السبب: {v.get('reason', '')}</small><br>
                    <small style="color:#94a3b8;">📅 التاريخ: {v.get('date', '')} | ⏰ الوقت: {v.get('time', '')}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )
      if v.get("photo"):
        with st.expander(f"🖼️ صورة مخالفة ({v.get('location')})"):
          st.image(v["photo"], use_container_width=True)
  else:
    st.info("سجل المخالفات نظيف.")

# ------------------------------------------------------------------------------
# 4. تبويب الإعاشة: توثيق الوجبة والقرار العلمي للطلبية
# ------------------------------------------------------------------------------
with tab_meals:
  st.markdown("##### 🍽️ 4. حصر الوجبة والقرار التشغيلي العلمي:")

  if is_within_official_window:
    st.markdown(
        f"<div class='stat-box' style='border-right: 3px solid #10b981;'>"
        f"<span class='done-tag'>🟢 فترة صرف رسمية مفتوحة الآن</span><br>"
        f"<b>{active_period_name}</b></div>",
        unsafe_allow_html=True,
    )
  else:
    st.markdown(
        f"<div class='stat-box' style='border-right: 3px solid #94a3b8;'>"
        f"<span style='color:#94a3b8; font-size:0.8em;'>🕒 خارج نافذة التوزيع المباشرة</span><br>"
        f"<small>المواعيد: فطور (05:30-07:00 ص) | غداء (11:30-02:30 م) | عشاء (05:30-09:00 م)</small></div>",
        unsafe_allow_html=True,
    )

  with st.form("quick_meal_form", clear_on_submit=False):
    meal_name = st.selectbox(
        "نوع الوجبة:",
        [
            "فطور 🌅 (05:30-07:00 ص)",
            "غداء ☀️ (11:30-02:30 م)",
            "عشاء 🌙 (05:30-09:00 م)",
        ],
        index=auto_meal_idx,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
      deliv = st.number_input(
          "المستلم (جات):", min_value=0, max_value=600, value=77
      )
    with c2:
      coups = st.number_input("كوبون:", min_value=0, max_value=600, value=42)
    with c3:
      surp = st.number_input(
          "فائض صواني:", min_value=0, max_value=600, value=0
      )

    btn_m = st.form_submit_button("⚡ حفظ الوجبة واحتساب القرار")

    actual_eaten = max(0, deliv - surp)
    no_cp = max(0, actual_eaten - coups)
    buff = math.ceil(actual_eaten * 0.03) if actual_eaten > 0 else 0
    rec_order = actual_eaten + buff

    if btn_m:
      st.session_state["meals_db"].append({
          "meal_type": meal_name.split()[0],
          "date": datetime.now().strftime("%Y-%m-%d"),
          "time": datetime.now().strftime("%I:%M:%S %p"),
          "delivered": int(deliv),
          "coupons": int(coups),
          "surplus": int(surp),
          "distributed": int(actual_eaten),
          "no_coupon": int(no_cp),
          "recommended": int(rec_order),
      })
      st.success(
          f"تم توثيق وجبة {meal_name.split()[0]}! المستهلك الفعلي:"
          f" {actual_eaten} شخص | التوصية القادمة: {rec_order} وجبة."
      )

  st.markdown("---")
  m1, m2 = st.columns(2)
  m1.metric("الموزع فعلياً", f"{actual_eaten} شخص")
  m2.metric(
      "بدون كوبون",
      f"{no_cp} وجبة",
      delta=f"{no_cp}" if no_cp > 0 else "0",
      delta_color="inverse",
  )

  st.info(
      f"💡 **القرار التشغيلي العلمي:**\nالمستهلك الفعلي: **{actual_eaten} شخص**."
      f" الطلبية المعتمدة للوجبة القادمة: **{rec_order} وجبة** لمنع هدر"
      f" **{max(0, deliv - rec_order)} وجبة**."
  )

# ------------------------------------------------------------------------------
# 5. تبويب تقرير الوردية الشامل: إرسال فوري للواتساب بدون الحاجة لكتابة رقم
# ------------------------------------------------------------------------------
with tab_report:
  st.markdown("##### 📊 5. تقرير الوردية الشامل والمنطقي:")
  st.caption(
      "صياغة علمية مفصلة تغطي كل ما قمت به؛ تضغط الزر ويفتح الواتساب لتحدد"
      " المستلم بيدك مباشرة:"
  )

  # بيانات الإعاشة
  last_m = (
      st.session_state["meals_db"][-1]
      if st.session_state["meals_db"]
      else {
          "meal_type": "عشاء",
          "time": "08:30 م",
          "delivered": 77,
          "coupons": 42,
          "surplus": 0,
          "distributed": 77,
          "recommended": 77,
          "no_coupon": 35,
      }
  )

  # بيانات الصيانة
  open_m = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  fixed_m = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status") == "تم الإصلاح"
  ]

  open_lines = [
      f"  • {x.get('location')}: {x.get('item')} [{x.get('desc')}] (رُصد:"
      f" {x.get('opened_at')})"
      for x in open_m
  ]
  open_m_txt = (
      "\n".join(open_lines)
      if open_lines
      else "  • لا توجد أعطال معلقة (كافة المرافق سليمة)."
  )

  fixed_lines = [
      f"  • {x.get('location')}: تم إنهاء وإصلاح {x.get('item')} (أُنجز:"
      f" {x.get('closed_at')})"
      for x in fixed_m
  ]
  fixed_m_txt = (
      "\n".join(fixed_lines)
      if fixed_lines
      else "  • لم تسجل أعمال صيانة منجزة خلال الوردية."
  )

  # بيانات المخالفات
  viols = st.session_state["violations_db"]
  viol_lines = [
      f"  • {v.get('location')}: مخالفة ({v.get('type')}) - المرة الـ"
      f" ({v.get('count')}) - التفاصيل: {v.get('reason')} [{v.get('time')}]"
      for v in viols[-4:]
  ]
  viols_txt = (
      "\n".join(viol_lines)
      if viol_lines
      else "  • السجل منضبط وخالٍ من المخالفات."
  )

  # بيانات الجولة الصباحية
  last_r = (
      st.session_state["rounds_db"][-1]
      if st.session_state["rounds_db"]
      else {
          "round": "جولة الصباح التفتيشية",
          "note": "السكن مستقر وهادئ وكافة الممرات نظيفة",
      }
  )

  today_full = datetime.now().strftime("%Y-%m-%d | %I:%M %p")

  comprehensive_shift_report = f"""*تقرير الوردية الميداني الشامل - {LOCATION_TAG}*
*التاريخ والوقت:* {today_full}
*المشرف المسؤول:* {SUPERVISOR_NAME}
-------------------------------------------
*1️⃣ الجولة التفتيشية الصباحية وحملة النظافة:*
• نوع الجولة: {last_r.get('round', '')}.
• الرصد الميداني: {last_r.get('note', '')}.

*2️⃣ كفاءة الأصول وصيانة السباكة والتبريد:*
• إجمالي البلاغات: {len(open_m)} معلقة | {len(fixed_m)} منجزة ومصلحة بالوردية.
• المنجز والمعالج:
{fixed_m_txt}
• الأعطال المعلقة قيد المتابعة:
{open_m_txt}

*3️⃣ الرقابة والامتثال لاشتراطات السلامة (Zero-Tolerance):*
{viols_txt}

*4️⃣ التحليل التشغيلي للإعاشة [{last_m.get('meal_type', 'الوجبة')}]:*
• توثيق التوقيت: الساعة {last_m.get('time', '')} (ضمن نافذة التوزيع الرسمية).
• الكميات: المستلم: {last_m.get('delivered', 0)} | المصروف بكوبون: {last_m.get('coupons', 0)} | الفائض: {last_m.get('surplus', 0)}.
• المستهلك الفعلي: {last_m.get('distributed', 0)} شخص.
💡 *القرار العلمي للطلبية القادمة:* اعتماد ({last_m.get('recommended', 0)} وجبة) شاملة 3% طوارئ لمنع هدر ({max(0, last_m.get('delivered', 0) - last_m.get('recommended', 0))} وجبة).

*الخلاصة الميدانية:*
الوضع العام بالسكن منضبط وتحت السيطرة التشغيلية الكاملة، وكافة البلاغات موثقة بالسجلات.
-------------------------------------------"""

  st.text_area(
      "معاينة تقرير الوردية المنطقي:",
      value=comprehensive_shift_report,
      height=270,
  )

  # مشاركة مباشرة بدون الحاجة لرقم جوال إطلاقاً
  enc_report = urllib.parse.quote(comprehensive_shift_report)
  wa_direct_share_url = f"https://api.whatsapp.com/send?text={enc_report}"

  st.markdown(
      f'<a href="{wa_direct_share_url}" target="_blank" class="wa-btn">📲 مشاركة'
      " التقرير عبر واتساب (أنت تختار الشخص أو القروب من جوالك)</a>",
      unsafe_allow_html=True,
  )

# ------------------------------------------------------------------------------
# 6. تبويب الخزنة والأرشيف (الرمز الدائم 5050 وتنزيل ملفات Excel)
# ------------------------------------------------------------------------------
with tab_vault:
  st.markdown("##### 🔐 الخزنة الرقمية والأرشيف المعتمد:")

  if not st.session_state["is_supervisor"]:
    pin_code = st.text_input("أدخل رمز المشرف للدخول (5050):", type="password")
    if st.button("🔓 فتح الخزنة", use_container_width=True):
      if hmac.compare_digest(pin_code.strip().encode(), PERMANENT_PIN.encode()):
        st.session_state["is_supervisor"] = True
        st.rerun()
      else:
        st.error("رمز المشرف غير صحيح.")
  else:
    st.success(
        f"🟢 الخزنة مؤمنة ومفتوحة بصلاحية المشرف ({SUPERVISOR_NAME})."
    )
    if st.button("🔒 قفل الخزنة"):
      st.session_state["is_supervisor"] = False
      st.rerun()

    st.divider()
    st.markdown("###### 📥 تنزيل سجلات وتقارير Excel الرسمية:")

    if st.session_state["meals_db"]:
      df_meals = pd.DataFrame(st.session_state["meals_db"])
      st.download_button(
          label="تحميل كشف الإعاشة والقرارات (Excel)",
          data=df_meals.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Meals_Log_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["maintenance_db"]:
      clean_maint = []
      for m in st.session_state["maintenance_db"]:
        c_c = m.copy()
        c_c["photo"] = "يوجد صورة مرفقة" if c_c.get("photo") else "لا يوجد"
        clean_maint.append(c_c)
      df_m = pd.DataFrame(clean_maint)
      st.download_button(
          label="تحميل سجل الصيانة ووقت الإصلاح (Excel)",
          data=df_m.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Repairs_Log_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["violations_db"]:
      clean_viols = []
      for v in st.session_state["violations_db"]:
        v_c = v.copy()
        v_c["photo"] = "يوجد صورة مرفقة" if v_c.get("photo") else "لا يوجد"
        clean_viols.append(v_c)
      df_v = pd.DataFrame(clean_viols)
      st.download_button(
          label="تحميل سجل المخالفات والتكرار (Excel)",
          data=df_v.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Violations_Log_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )
