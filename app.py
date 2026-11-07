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
    padding: 12px;
    border-radius: 10px;
    font-weight: 900;
    text-decoration: none !important;
    margin-top: 8px;
    margin-bottom: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت العامة وإدارة الجلسة الآمنة (الرمز الدائم 5050)
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

if "contacts" not in st.session_state:
  st.session_state["contacts"] = {
      "المدير عمر": "966500000000",
      "مقاول الصيانة": "966500000000",
      "متعهد الإعاشة": "966500000000",
  }

# ترقية قواعد البيانات لتفادي أي تعارض في المفاتيح
if "maintenance_db" not in st.session_state:
  st.session_state["maintenance_db"] = [
      {
          "room": "104",
          "item": "مكيف",
          "opened_at": "09:30 ص",
          "date": "2026-11-06",
          "closed_at": None,
          "status": "مفتوح",
      },
      {
          "room": "208",
          "item": "شطاف",
          "opened_at": "08:15 م",
          "date": "2026-11-07",
          "closed_at": None,
          "status": "مفتوح",
      },
  ]
else:
  for row in st.session_state["maintenance_db"]:
    if "opened_at" not in row:
      row["opened_at"] = row.get("time", "اليوم")
    if "date" not in row:
      row["date"] = datetime.now().strftime("%Y-%m-%d")
    if "status" not in row:
      row["status"] = "مفتوح"
    if "closed_at" not in row:
      row["closed_at"] = None

if "violations_db" not in st.session_state:
  st.session_state["violations_db"] = [
      {
          "room": "108",
          "type": "سخان",
          "reason": "استخدام هيتر طبخ في الغرفة",
          "count": 1,
          "time": "09:15 م",
          "date": "2026-11-05",
      },
      {
          "room": "108",
          "type": "سخان",
          "reason": "تكرار تشغيل هيتر مخالف",
          "count": 2,
          "time": "10:30 م",
          "date": "2026-11-07",
      },
  ]

if "meals_db" not in st.session_state:
  st.session_state["meals_db"] = []

if "rounds_db" not in st.session_state:
  st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
  st.session_state["is_supervisor"] = False

# ==============================================================================
# 3. محرك التوقيت الدقيق للوجبات وفق مواعيد السكن الرسمية
# ==============================================================================
now = datetime.now()
now_minutes = now.hour * 60 + now.minute

# الفترات بالدقائق من بداية اليوم:
# الفطور: 05:30 (330 دقيقة) حتى 07:00 (420 دقيقة)
# الغداء: 11:30 (690 دقيقة) حتى 14:30 (870 دقيقة)
# العشاء: 17:30 (1050 دقيقة) حتى 21:00 (1260 دقيقة)

if now_minutes < 570:  # حتى 09:30 صباحاً -> الافتراضي فطور
  auto_meal_idx = 0
  active_period_name = "الفطور (05:30 ص - 07:00 ص)"
  is_within_official_window = 330 <= now_minutes <= 420
elif now_minutes < 990:  # حتى 04:30 عصراً -> الافتراضي غداء
  auto_meal_idx = 1
  active_period_name = "الغداء (11:30 ص - 02:30 م)"
  is_within_official_window = 690 <= now_minutes <= 870
else:  # المساء والليل -> الافتراضي عشاء
  auto_meal_idx = 2
  active_period_name = "العشاء (05:30 م - 09:00 م)"
  is_within_official_window = 1050 <= now_minutes <= 1260

# ==============================================================================
# 4. ترويسة التطبيق مع زر التحديث اللحظي
# ==============================================================================
st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 إدارة {LOCATION_TAG}</div>
    <div class="sub-headline">العمليات الميدانية • التوثيق الزمني • القرارات التشغيلية</div>
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

tab_meals, tab_repairs, tab_viol, tab_rounds, tab_dispatch, tab_vault = st.tabs(
    [
        "🍽️ الأكل والقرار",
        "🛠️ الصيانة",
        "⚠️ المخالفات",
        "🚶 الجولات",
        "📲 مركز الواتساب",
        "🔐 الأدمن والخزنة",
    ]
)

# ------------------------------------------------------------------------------
# 1. تبويب الأكل: فطور (5:30-7) / غداء (11:30-2:30) / عشاء (5:30-9)
# ------------------------------------------------------------------------------
with tab_meals:
  st.markdown("##### 🍽️ توثيق الوجبة والقرار التشغيلي:")

  # شريط التوقيت الرسمي
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

  with st.form("meal_operational_form", clear_on_submit=False):
    meal_type_chosen = st.selectbox(
        "نوع الوجبة:",
        [
            "فطور 🌅 (05:30 ص - 07:00 ص)",
            "غداء ☀️ (11:30 ص - 02:30 م)",
            "عشاء 🌙 (05:30 م - 09:00 م)",
        ],
        index=auto_meal_idx,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
      deliv = st.number_input(
          "كم وجبة جات:", min_value=0, max_value=600, value=77
      )
    with c2:
      coups = st.number_input("كوبون:", min_value=0, max_value=600, value=42)
    with c3:
      surp = st.number_input("فائض بالصواني:", min_value=0, max_value=600, value=0)

    meal_note = st.text_input(
        "ملاحظة الوجبة (اختياري):", placeholder="سليم / تأخر في التوريد..."
    )

    btn_meal = st.form_submit_button("⚡ حفظ الوجبة وتثبيت الوقت")

    actual_distributed = max(0, deliv - surp)
    no_coupon_count = max(0, actual_distributed - coups)

    # قرار الطلبية القادمة علمياً: المستهلك الفعلي + 3% طوارئ
    buffer_calc = (
        math.ceil(actual_distributed * 0.03) if actual_distributed > 0 else 0
    )
    recommended_order = actual_distributed + buffer_calc

    exact_time_now = datetime.now().strftime("%I:%M:%S %p")
    exact_date_now = datetime.now().strftime("%Y-%m-%d")

    clean_meal_name = meal_type_chosen.split()[0]

    if btn_meal:
      st.session_state["meals_db"].append({
          "meal_type": clean_meal_name,
          "date": exact_date_now,
          "time": exact_time_now,
          "delivered": int(deliv),
          "coupons": int(coups),
          "surplus": int(surp),
          "distributed": int(actual_distributed),
          "no_coupon": int(no_coupon_count),
          "recommended": int(recommended_order),
          "notes": meal_note.strip() if meal_note.strip() else "سليم",
      })
      st.success(
          f"تم توثيق وجبة {clean_meal_name} رسمياً (الساعة {exact_time_now})!"
      )

  st.markdown("---")
  m1, m2 = st.columns(2)
  m1.metric("الموزع فعلياً", f"{actual_distributed} شخص")
  m2.metric(
      "الصرف بدون كوبون",
      f"{no_coupon_count} وجبة",
      delta=f"{no_coupon_count}" if no_coupon_count > 0 else "0",
      delta_color="inverse",
  )

  st.info(
      f"💡 **القرار التشغيلي العلمي:**\n"
      f"المستهلك الفعلي لوجبة ({clean_meal_name}) هو **{actual_distributed} شخص**.\n"
      f"الطلبية المقترحة للوجبة القادمة هي **{recommended_order} وجبة** (تغطي كافة الأفراد مع 3% طوارئ) لتفادي هدر **{max(0, deliv - recommended_order)} وجبة**."
  )

# ------------------------------------------------------------------------------
# 2. تبويب الصيانة: قيد سريع وإغلاق بلمسة مع تسجيل الوقت
# ------------------------------------------------------------------------------
with tab_repairs:
  st.markdown("##### 🛠️ بلاغ صيانة جديد:")

  with st.form("quick_rep_form", clear_on_submit=True):
    r_room = st.text_input("رقم الغرفة:", placeholder="مثال: 104")
    r_item = st.radio(
        "العطل:", ["مكيف ❄️", "شطاف 🚿", "أخرى 🛠️"], horizontal=True
    )

    other_text = ""
    if "أخرى" in r_item:
      other_text = st.text_input(
          "اكتب العطل الآخر:", placeholder="مثال: لمبة / فيش / سخان موية..."
      )

    btn_rep = st.form_submit_button("⚡ تسجيل البلاغ")

    if btn_rep:
      c_r = r_room.strip()
      final_i = (
          other_text.strip()
          if ("أخرى" in r_item and other_text.strip())
          else r_item.split()[0]
      )
      if not c_r:
        st.error("اكتب رقم الغرفة أولاً.")
      else:
        st.session_state["maintenance_db"].append({
            "room": c_r,
            "item": final_i,
            "opened_at": datetime.now().strftime("%I:%M %p"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "closed_at": None,
            "status": "مفتوح",
        })
        st.success(f"تم تسجيل بلاغ: غرفة {c_r} ({final_i}).")

  st.markdown("---")
  st.markdown("##### 📋 البلاغات المعلقة:")

  open_reps = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  if open_reps:
    for idx, row in enumerate(open_reps):
      r_val = row.get("room", "")
      i_val = row.get("item", "")
      t_val = row.get("opened_at", row.get("time", "اليوم"))
      d_val = row.get("date", "اليوم")

      st.markdown(
          f"""
                <div class="stat-box">
                    <b>غرفة {r_val}</b> — <span style="color:var(--primary); font-weight:800;">{i_val}</span><br>
                    <small style="color:#94a3b8;">📅 التاريخ: {d_val} | ⏰ الوقت: {t_val}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )

      if st.button(f"✅ تم تصليح {i_val} غرفة {r_val}", key=f"fix_btn_{idx}"):
        row["status"] = "تم الإصلاح"
        row["closed_at"] = datetime.now().strftime("%I:%M %p")
        st.success(
            f"تم تصليح {i_val} غرفة {r_val} (الساعة {row['closed_at']}) ✓"
        )
        st.rerun()
  else:
    st.info("لا توجد بلاغات صيانة معلقة حالياً.")

  done_reps = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status") == "تم الإصلاح"
  ]
  if done_reps:
    with st.expander("🔍 ما تم تصليحه اليوم:"):
      for d in reversed(done_reps[-4:]):
        st.markdown(
            f"""
                    <div class="stat-box" style="border-right: 3px solid #10b981;">
                        <b>غرفة {d.get('room', '')}</b>: {d.get('item', '')} <span class='done-tag'>تم تصليحه ✓</span><br>
                        <small style="color:#94a3b8;">أُصلح الساعة: <b>{d.get('closed_at', 'اليوم')}</b> (البلاغ كان {d.get('opened_at', '')})</small>
                    </div>
                    """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------------------
# 3. تبويب المخالفات: رصد السخانات والنظافة بالتاريخ والوقت
# ------------------------------------------------------------------------------
with tab_viol:
  st.markdown("##### ⚠️ تسجيل مخالفة غرفة:")

  with st.form("viol_form", clear_on_submit=True):
    v_room = st.text_input("رقم الغرفة:", placeholder="مثال: 108")
    v_type = st.radio(
        "المخالفة:",
        ["سخان ⚡", "نظافة 🗑️", "سخان ونظافة ⚠️", "أخرى 📝"],
        horizontal=True,
    )

    custom_v = ""
    if "أخرى" in v_type:
      custom_v = st.text_input(
          "اكتب نوع المخالفة:", placeholder="مثال: تدخين / إزعاج..."
      )

    v_reason = st.text_input(
        "السبب والملاحظة الميدانية:",
        placeholder="مثال: تشغيل هيتر طبخ / نفايات...",
    )

    btn_viol = st.form_submit_button("⚡ حفظ المخالفة")

    if btn_viol:
      c_vr = v_room.strip()
      chosen_t = (
          custom_v.strip()
          if ("أخرى" in v_type and custom_v.strip())
          else v_type.split()[0]
      )

      if not c_vr:
        st.error("اكتب رقم الغرفة أولاً.")
      else:
        past_times = sum(
            1
            for v in st.session_state["violations_db"]
            if v.get("room") == c_vr and v.get("type") == chosen_t
        )
        this_count = past_times + 1

        st.session_state["violations_db"].append({
            "room": c_vr,
            "type": chosen_t,
            "reason": (
                v_reason.strip() if v_reason.strip() else "رصد مخالفة بالسكن"
            ),
            "count": this_count,
            "time": datetime.now().strftime("%I:%M %p"),
            "date": datetime.now().strftime("%Y-%m-%d"),
        })
        st.success(
            f"تم تسجيل مخالفة غرفة {c_vr} ({chosen_t}) — المرة الـ"
            f" ({this_count})!"
        )

  st.markdown("---")
  st.markdown("##### 📋 كشف المخالفات المرصودة:")
  if st.session_state["violations_db"]:
    for v in reversed(st.session_state["violations_db"][-4:]):
      c_num = v.get("count", 1)
      tag_c = "alert-tag" if c_num >= 2 else "done-tag"
      st.markdown(
          f"""
                <div class="stat-box" style="border-right: 3px solid #ef4444;">
                    <b>غرفة {v.get('room', '')}</b> — <span style="color:#f87171; font-weight:800;">{v.get('type', '')}</span>
                    <span class='{tag_c}'>المرة الـ {c_num}</span><br>
                    <small style="color:#cbd5e1;">السبب: {v.get('reason', '')}</small><br>
                    <small style="color:#94a3b8;">📅 التاريخ: {v.get('date', '')} | ⏰ الوقت: {v.get('time', '')}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )
  else:
    st.info("سجل المخالفات نظيف.")

# ------------------------------------------------------------------------------
# 4. تبويب الجولات الميدانية
# ------------------------------------------------------------------------------
with tab_rounds:
  st.markdown("##### 🚶 توثيق جولة اليوم:")

  def_round = 0 if now.hour < 14 else 1

  with st.form("round_form", clear_on_submit=True):
    sel_r = st.radio(
        "الجولة:",
        ["جولة الصباح (09:30 ص)", "جولة الليل (08:30 م)"],
        index=def_round,
        horizontal=True,
    )
    r_notes = st.text_input(
        "ملاحظة الجولة:", placeholder="مثال: هدوء تام ونظافة الممرات ممتازة..."
    )
    btn_r = st.form_submit_button("⚡ حفظ الجولة")

    if btn_r:
      st.session_state["rounds_db"].append({
          "date": datetime.now().strftime("%Y-%m-%d"),
          "time": datetime.now().strftime("%I:%M %p"),
          "round": sel_r.split()[0] + " " + sel_r.split()[1],
          "note": (
              r_notes.strip() if r_notes.strip() else "السكن منضبط وسليم"
          ),
      })
      st.success(f"تم توثيق {sel_r} بنجاح!")

  if st.session_state["rounds_db"]:
    st.markdown("---")
    for r in st.session_state["rounds_db"][-2:]:
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
# 5. تبويب مركز الواتساب: اختيار المستلم وتحديد المحتوى بضغطة زر
# ------------------------------------------------------------------------------
with tab_dispatch:
  st.markdown("##### 📲 مركز إرسال الواتساب والتقارير:")
  st.caption("تحكم كامل: حدد لمن تريد الإرسال، واضغط زر الإرسال المباشر:")

  recipient = st.selectbox(
      "إرسال الرسالة إلى من؟",
      ["المدير عمر", "مقاول الصيانة", "متعهد الإعاشة", "رقم مخصص (أكتبه بيدي)"],
  )

  if recipient == "رقم مخصص (أكتبه بيدي)":
    target_wa_phone = st.text_input(
        "أدخل رقم الجوال مع المفتاح (مثال: 966500000000):"
    )
  else:
    target_wa_phone = st.session_state["contacts"].get(
        recipient, "966500000000"
    )
    st.info(f"رقم الواتساب المعتمد لـ ({recipient}): **{target_wa_phone}**")

  report_scope = st.radio(
      "محتوى الرسالة المراد إرساله:",
      [
          "1. تقرير الموقف اليومي الشامل للمدير (مع القرار والتوصية)",
          "2. كشف الصيانة فقط (كم شخص/غرفة معلقة ومصلحة)",
          "3. كشف الإعاشة فقط (مواعيد الوجبة والكميات والقرار)",
          "4. كشف المخالفات فقط (الغرف والسخانات والتكرار)",
          "5. رسالة مخصصة أكتبها بيدي",
      ],
  )

  today_str = datetime.now().strftime("%Y-%m-%d | %I:%M %p")
  last_meal_record = (
      st.session_state["meals_db"][-1]
      if st.session_state["meals_db"]
      else {
          "meal_type": "عشاء",
          "date": datetime.now().strftime("%Y-%m-%d"),
          "time": "08:30 م",
          "delivered": 77,
          "coupons": 42,
          "surplus": 0,
          "distributed": 77,
          "recommended": 77,
      }
  )

  open_m_list = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  fixed_m_list = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status") == "تم الإصلاح"
  ]

  open_m_str = (
      "\n".join([
          f"  • غرفة {x.get('room')}: {x.get('item')} (مسجل {x.get('opened_at')})"
          for x in open_m_list
      ])
      if open_m_list
      else "  • لا توجد أعطال معلقة."
  )
  fixed_m_str = (
      "\n".join([
          f"  • تم تصليح {x.get('item')} غرفة {x.get('room')} ({x.get('closed_at')})"
          for x in fixed_m_list
      ])
      if fixed_m_list
      else "  • لا توجد أعطال مصلحة اليوم."
  )

  viols_all = st.session_state["violations_db"]
  viols_str = (
      "\n".join([
          f"  • غرفة {v.get('room')}: {v.get('type')} (المرة"
          f" {v.get('count')}) - {v.get('reason')} [{v.get('date')}]"
          for v in viols_all[-4:]
      ])
      if viols_all
      else "  • السجل نظيف ولا توجد مخالفات."
  )

  message_to_send = ""
  if "تقرير الموقف اليومي الشامل" in report_scope:
    message_to_send = f"""مساك الله بالخير أبو عمر،،
تقرير {LOCATION_TAG} اليومي المعتمد ({today_str}):

1️⃣ الإعاشة [{last_meal_record.get('meal_type', 'عشاء')}]:
- توثيق الوقت: {last_meal_record.get('time', '')}
- الوجبات اللي جات: {last_meal_record.get('delivered', 0)}
- المستلم بكوبون: {last_meal_record.get('coupons', 0)}
- الفائض بالصواني: {last_meal_record.get('surplus', 0)}
- المستهلك الفعلي: {last_meal_record.get('distributed', 0)} شخص.
💡 القرار التشغيلي للطلبية القادمة: {last_meal_record.get('recommended', 0)} وجبة.

2️⃣ الصيانة ({len(open_m_list)} بلاغات معلقة / {len(fixed_m_list)} مصلحة):
- المعلق:
{open_m_str}
- المنجز:
{fixed_m_str}

3️⃣ المخالفات المضبوطة بالسكن:
{viols_str}

الوضع العام بالسكن: منضبط وتحت السيطرة الكاملة."""

  elif "كشف الصيانة فقط" in report_scope:
    message_to_send = f"""السلام عليكم، بلاغات صيانة {LOCATION_TAG}:
التاريخ: {today_str}

الأعطال المعلقة المطلوب صيانتها ({len(open_m_list)} غرف):
{open_m_str}

المنجز الذي تم إصلاحه اليوم:
{fixed_m_str}

يرجى سرعة معالجة الغرف المعلقة وإشعارنا بالإنجاز."""

  elif "كشف الإعاشة فقط" in report_scope:
    message_to_send = f"""السلام عليكم، محضر مطابقة الإعاشة - {LOCATION_TAG}:
التاريخ: {today_str}
الوجبة: {last_meal_record.get('meal_type', 'عشاء')} (وقت التسجيل: {last_meal_record.get('time', '')})

- الوجبات الموردة (جات): {last_meal_record.get('delivered', 0)}
- المستلم بموجب كوبون: {last_meal_record.get('coupons', 0)}
- الفائض بالصواني: {last_meal_record.get('surplus', 0)}
- المستهلك الفعلي: {last_meal_record.get('distributed', 0)} شخص.

💡 التوصية التشغيلية للوجبة القادمة: {last_meal_record.get('recommended', 0)} وجبة."""

  elif "كشف المخالفات فقط" in report_scope:
    message_to_send = f"""إشعار أمن وسلامة ومخالفات - {LOCATION_TAG}:
التاريخ: {today_str}

بيان المخالفات المضبوطة:
{viols_str}

يرجى اتخاذ الإجراء اللائحي وتطبيق الجزاءات بحق المخالفين لا سيما تكرار السخانات."""

  else:
    message_to_send = st.text_area(
        "اكتب رسالتك المخصصة هنا:",
        placeholder="السلام عليكم بخصوص سكن جامعة 3...",
        height=140,
    )

  if "رسالة مخصصة" not in report_scope:
    st.text_area("معاينة الرسالة قبل الإرسال:", value=message_to_send, height=220)

  if target_wa_phone and target_wa_phone.strip():
    enc_payload = urllib.parse.quote(message_to_send)
    direct_link = f"https://wa.me/{target_wa_phone.strip()}?text={enc_payload}"
    st.markdown(
        f'<a href="{direct_link}" target="_blank" class="wa-btn">📲 إرسال'
        f" الرسالة فوراً إلى {recipient} عبر واتساب</a>",
        unsafe_allow_html=True,
    )
  else:
    st.warning("الرجاء التأكد من كتابة رقم هاتف صالح للإرسال.")

# ------------------------------------------------------------------------------
# 6. تبويب الأدمن والخزنة (PIN: 5050 وإدارة أرقام التواصل والأرشيف)
# ------------------------------------------------------------------------------
with tab_vault:
  st.markdown("##### 🔐 لوحة الأدمن والخزنة الرقمية:")

  if not st.session_state["is_supervisor"]:
    pin_code = st.text_input("أدخل رمز المشرف للدخول:", type="password")
    if st.button("🔓 فتح لوحة الأدمن", use_container_width=True):
      if hmac.compare_digest(pin_code.strip().encode(), PERMANENT_PIN.encode()):
        st.session_state["is_supervisor"] = True
        st.rerun()
      else:
        st.error("رمز المشرف غير صحيح.")
  else:
    st.success("🟢 لوحة الأدمن مفتوحة ومؤمنة.")
    if st.button("🔒 قفل لوحة الأدمن"):
      st.session_state["is_supervisor"] = False
      st.rerun()

    st.divider()

    st.markdown("###### ⚙️ إدارة أرقام الواتساب المعتمدة للتواصل:")
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
      edit_mgr = st.text_input(
          "رقم المدير عمر:",
          value=st.session_state["contacts"].get(
              "المدير عمر", "966500000000"
          ),
      )
    with col_u2:
      edit_mnt = st.text_input(
          "رقم الصيانة:",
          value=st.session_state["contacts"].get(
              "مقاول الصيانة", "966500000000"
          ),
      )
    with col_u3:
      edit_cat = st.text_input(
          "رقم الإعاشة:",
          value=st.session_state["contacts"].get(
              "متعهد الإعاشة", "966500000000"
          ),
      )

    if st.button("حفظ وتثبيت الأرقام في النظام"):
      st.session_state["contacts"]["المدير عمر"] = edit_mgr.strip()
      st.session_state["contacts"]["مقاول الصيانة"] = edit_mnt.strip()
      st.session_state["contacts"]["متعهد الإعاشة"] = edit_cat.strip()
      st.success("تم تحديث وحفظ أرقام الواتساب بنجاح!")
      st.rerun()

    st.divider()
    st.markdown("###### 📥 تنزيل سجلات وتقارير Excel الرسمية:")

    if st.session_state["meals_db"]:
      df_meals = pd.DataFrame(st.session_state["meals_db"])
      st.download_button(
          label="تحميل سجل الإعاشة والقرارات (Excel)",
          data=df_meals.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Meals_Decisions_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["maintenance_db"]:
      df_m = pd.DataFrame(st.session_state["maintenance_db"])
      st.download_button(
          label="تحميل سجل الصيانة ووقت الإصلاح (Excel)",
          data=df_m.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Repairs_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["violations_db"]:
      df_v = pd.DataFrame(st.session_state["violations_db"])
      st.download_button(
          label="تحميل سجل المخالفات والتكرار (Excel)",
          data=df_v.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Violations_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )
