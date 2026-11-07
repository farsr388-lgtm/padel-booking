from datetime import datetime
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (Mobile-First / Dark Mode)
# ==============================================================================
st.set_page_config(
    page_title="إدارة سكن جامعة 3",
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
.refresh-btn > button {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    font-weight: 700 !important;
    height: 38px !important;
    border-radius: 8px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت العامة وقواعد البيانات
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

# أرقام التواصل الافتراضية
if "contacts" not in st.session_state:
  st.session_state["contacts"] = {
      "المدير": "966500000000",
      "مقاول الصيانة": "966500000000",
      "متعهد الإعاشة": "966500000000",
  }

# ترقية البيانات المحفوظة والتأكد من عدم حدوث KeyError
if "maintenance_db" not in st.session_state:
  st.session_state["maintenance_db"] = [
      {
          "room": "104",
          "item": "مكيف",
          "opened_at": "09:30 ص",
          "closed_at": None,
          "status": "مفتوح",
      },
      {
          "room": "208",
          "item": "شطاف",
          "opened_at": "08:15 م",
          "closed_at": None,
          "status": "مفتوح",
      },
  ]
else:
  for row in st.session_state["maintenance_db"]:
    if "opened_at" not in row:
      row["opened_at"] = row.get("date", "اليوم")
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
# 3. ترويسة التطبيق مع زر تحديث الشاشة
# ==============================================================================
st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 إدارة {LOCATION_TAG}</div>
    <div class="sub-headline">العمليات الميدانية • متابعة العقود والمخالفات</div>
</div>
""",
    unsafe_allow_html=True,
)

# زر التحديث الفوري للشاشة ومسح الحقول العالقة
col_ref1, col_ref2 = st.columns([2, 1])
with col_ref1:
  st.caption("⚡ اضغط للتحديث وإعادة مزامنة الحسابات:")
with col_ref2:
  st.markdown('<div class="refresh-btn">', unsafe_allow_html=True)
  if st.button("🔄 تحديث الشاشة", use_container_width=True):
    st.rerun()
  st.markdown("</div>", unsafe_allow_html=True)

# تقسيم التبويبات بحسب جهة العمل والمسؤولية
tab_mgr, tab_repairs, tab_viol, tab_meals, tab_rounds, tab_wa_center, tab_vault = st.tabs([
    "👔 تقرير المدير",
    "🛠️ الصيانة",
    "⚠️ المخالفات",
    "🍽️ الإعاشة",
    "🚶 الجولات",
    "📲 مركز الواتساب",
    "🔐 الخزنة",
])

# ------------------------------------------------------------------------------
# 1. تبويب تقرير المدير اليومي (مخصص للمدير بملخص دقيق ومباشر)
# ------------------------------------------------------------------------------
with tab_mgr:
  st.markdown("##### 👔 تقرير الموقف اليومي لمدير السكن:")
  st.caption("ملخص تنفيذي يجمع الأكل، الصيانة المنجزة، والمخالفات المرصودة:")

  today_date = datetime.now().strftime("%Y-%m-%d")

  last_meal = (
      st.session_state["meals_db"][-1]
      if st.session_state["meals_db"]
      else {"delivered": 77, "coupons": 42, "surplus": 0}
  )

  # المنجز بالصيانة اليوم
  fixed_list = [
      f"  • تم تصليح {x.get('item', '')} غرفة {x.get('room', '')} (الساعة"
      f" {x.get('closed_at', 'اليوم')})"
      for x in st.session_state["maintenance_db"]
      if x.get("status") == "تم الإصلاح"
  ]
  fixed_str = (
      "\n".join(fixed_list)
      if fixed_list
      else "  • لا توجد أعطال تم إصلاحها اليوم."
  )

  # الأعطال المعلقة
  pending_list = [
      f"  • غرفة {x.get('room', '')}: {x.get('item', '')} (مسجل"
      f" {x.get('opened_at', 'اليوم')})"
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  pending_str = (
      "\n".join(pending_list) if pending_list else "  • لا توجد أعطال معلقة."
  )

  # المخالفات
  viols_list = [
      f"  • غرفة {v.get('room', '')}: {v.get('type', '')} (المرة"
      f" {v.get('count', 1)}) - السبب: {v.get('reason', '')} [{v.get('date', '')}"
      f" {v.get('time', '')}]"
      for v in st.session_state["violations_db"][-5:]
  ]
  viols_str = (
      "\n".join(viols_list)
      if viols_list
      else "  • لا توجد مخالفات مرصودة اليوم."
  )

  last_rnd = (
      st.session_state["rounds_db"][-1]
      if st.session_state["rounds_db"]
      else {"round": "جولة المساء", "note": "السكن منضبط وهادئ"}
  )

  mgr_msg = f"""تقرير الموقف اليومي - {LOCATION_TAG}
التاريخ: {today_date}

1️⃣ الإعاشة:
- الوجبات اللي جات: {last_meal.get('delivered', 0)}
- المصروف بكوبون: {last_meal.get('coupons', 0)}
- الفائض بالصواني: {last_meal.get('surplus', 0)}

2️⃣ الصيانة والأعطال:
- المنجز اليوم:
{fixed_str}
- البلاغات المعلقة:
{pending_str}

3️⃣ المخالفات المضبوطة:
{viols_str}

4️⃣ الجولات الرقابية:
- آخر جولة: {last_rnd.get('round', '')} ({last_rnd.get('note', '')})

الوضع العام بالسكن: منضبط وتحت السيطرة."""

  st.text_area("نص التقرير المجهز للمدير:", value=mgr_msg, height=260)

  mgr_phone = st.session_state["contacts"].get("المدير", "966500000000")
  enc_mgr_msg = urllib.parse.quote(mgr_msg)
  wa_mgr_url = f"https://wa.me/{mgr_phone}?text={enc_mgr_msg}"

  st.markdown(
      f'<a href="{wa_mgr_url}" target="_blank" class="wa-btn">📲 إرسال التقرير'
      " فوراً للمدير عبر واتساب</a>",
      unsafe_allow_html=True,
  )

# ------------------------------------------------------------------------------
# 2. تبويب الصيانة (تسجيل عطل وإغلاق المصلح في ثوانٍ)
# ------------------------------------------------------------------------------
with tab_repairs:
  st.markdown("##### 🛠️ بلاغ عطل جديد:")

  with st.form("rep_form", clear_on_submit=True):
    r_room = st.text_input("رقم الغرفة:", placeholder="مثال: 104")
    r_item = st.radio(
        "العطل:", ["مكيف ❄️", "شطاف 🚿", "أخرى 🛠️"], horizontal=True
    )

    other_text = ""
    if "أخرى" in r_item:
      other_text = st.text_input(
          "اكتب العطل:", placeholder="مثال: لمبة / فيش / سخان..."
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
            "closed_at": None,
            "status": "مفتوح",
        })
        st.success(f"تم قيد بلاغ: غرفة {c_r} ({final_i}).")

  st.markdown("---")
  st.markdown("##### 📋 البلاغات المفتوحة حالياً:")

  open_reps = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status", "مفتوح") == "مفتوح"
  ]
  if open_reps:
    maint_lines = [f"السلام عليكم، بلاغات صيانة {LOCATION_TAG}:"]
    for idx, row in enumerate(open_reps):
      r_num = row.get("room", "")
      i_name = row.get("item", "")
      t_open = row.get("opened_at", "اليوم")

      st.markdown(
          f"""
                <div class="stat-box">
                    <b>غرفة {r_num}</b> — <span style="color:var(--primary); font-weight:800;">{i_name}</span><br>
                    <small style="color:#94a3b8;">وقت البلاغ: {t_open}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )
      maint_lines.append(f"- غرفة {r_num}: {i_name}")

      if st.button(f"✅ تم تصليح {i_name} غرفة {r_num}", key=f"fix_k_{idx}"):
        row["status"] = "تم الإصلاح"
        row["closed_at"] = datetime.now().strftime("%I:%M %p")
        st.success(
            f"تم تصليح {i_name} غرفة {r_num} (الساعة {row['closed_at']}) ✓"
        )
        st.rerun()

    maint_lines.append("\nيرجى المتابعة والإصلاح لا هنتوا.")
    maint_phone = st.session_state["contacts"].get(
        "مقاول الصيانة", "966500000000"
    )
    enc_maint = urllib.parse.quote("\n".join(maint_lines))
    wa_maint_url = f"https://wa.me/{maint_phone}?text={enc_maint}"

    st.markdown(
        f'<a href="{wa_maint_url}" target="_blank" class="wa-btn">📲 إرسال'
        " قائمة البلاغات لمقاول الصيانة عبر واتساب</a>",
        unsafe_allow_html=True,
    )
  else:
    st.info("لا توجد بلاغات معلقة حالياً.")

  # كشف المنجز
  done_reps = [
      x
      for x in st.session_state["maintenance_db"]
      if x.get("status") == "تم الإصلاح"
  ]
  if done_reps:
    with st.expander("🔍 وش اللي أُصلح اليوم؟"):
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
# 3. تبويب المخالفات (سخان / نظافة + السبب + عداد التكرار)
# ------------------------------------------------------------------------------
with tab_viol:
  st.markdown("##### ⚠️ تسجيل مخالفة غرفة:")

  with st.form("viol_input", clear_on_submit=True):
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
        "السبب والرصد الميداني:",
        placeholder="مثال: تشغيل هيتر طبخ / أكياس نفايات...",
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
            f"تم قيد مخالفة غرفة {c_vr} ({chosen_t}) — المرة الـ"
            f" ({this_count})!"
        )

  st.markdown("---")
  st.markdown("##### 📋 المخالفات المرصودة مع التاريخ والوقت:")
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
# 4. تبويب الإعاشة (جات / كوبون / فائض)
# ------------------------------------------------------------------------------
with tab_meals:
  st.markdown("##### 🍽️ حصر وجبة اليوم:")

  with st.form("meal_input", clear_on_submit=False):
    c1, c2, c3 = st.columns(3)
    with c1:
      deliv = st.number_input(
          "كم وجبة جات:", min_value=0, max_value=600, value=77
      )
    with c2:
      coups = st.number_input("كوبون:", min_value=0, max_value=600, value=42)
    with c3:
      surp = st.number_input("فائض:", min_value=0, max_value=600, value=0)

    btn_meal = st.form_submit_button("⚡ حفظ الوجبة")

    dist = max(0, deliv - surp)
    no_cp = max(0, dist - coups)

    if btn_meal:
      st.session_state["meals_db"].append({
          "date": datetime.now().strftime("%Y-%m-%d"),
          "time": datetime.now().strftime("%I:%M %p"),
          "delivered": int(deliv),
          "coupons": int(coups),
          "surplus": int(surp),
          "distributed": int(dist),
          "no_coupon": int(no_cp),
      })
      st.success("تم حفظ بيانات الوجبة بنجاح!")

  st.markdown("---")
  m1, m2 = st.columns(2)
  m1.metric("الموزع فعلياً", f"{dist} وجبة")
  m2.metric(
      "بدون كوبون",
      f"{no_cp} وجبة",
      delta=f"{no_cp}" if no_cp > 0 else "0",
      delta_color="inverse",
  )

# ------------------------------------------------------------------------------
# 5. تبويب الجولات الميدانية
# ------------------------------------------------------------------------------
with tab_rounds:
  st.markdown("##### 🚶 توثيق جولة اليوم:")

  curr_hour = datetime.now().hour
  def_round = 0 if curr_hour < 14 else 1

  with st.form("round_input", clear_on_submit=True):
    sel_r = st.radio(
        "الجولة:",
        ["جولة الصباح (09:30 ص)", "جولة الليل (08:30 م)"],
        index=def_round,
        horizontal=True,
    )
    r_notes = st.text_input(
        "ملاحظة الجولة:", placeholder="مثال: السكن منضبط ونظيف..."
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
# 6. تبويب مركز إرسال الواتساب (تختار لمن ترسل وتنتقل للمحادثة بنقرة)
# ------------------------------------------------------------------------------
with tab_wa_center:
  st.markdown("##### 📲 مركز إرسال رسائل الواتساب الموجهة:")
  st.caption("اختر الشخص ونوع الرسالة واضغط زر الإرسال المباشر:")

  # اختيار الجهة المستلمة
  recipient_choice = st.selectbox(
      "إرسال إلى من؟",
      ["المدير", "مقاول الصيانة", "متعهد الإعاشة", "رقم آخر (أكتبه بيدي)"],
  )

  # تحديد رقم الجوال
  if recipient_choice == "رقم آخر (أكتبه بيدي)":
    target_phone = st.text_input("أدخل رقم الجوال مع المفتاح (مثال: 9665...):")
  else:
    target_phone = st.session_state["contacts"].get(
        recipient_choice, "966500000000"
    )
    st.info(f"الرقم المعتمد لـ ({recipient_choice}): **{target_phone}**")

  # اختيار نوع الرسالة الجاهزة
  msg_template = st.radio(
      "محتوى الرسالة:",
      [
          "تقرير آخر اليوم الشامل",
          "قائمة بلاغات الصيانة المفتوحة",
          "محضر مطابقة الإعاشة (الوجبات)",
          "رسالة مخصصة أكتبها بيدي",
      ],
  )

  # صياغة محتوى الرسالة بحسب الاختيار
  final_text = ""
  if msg_template == "تقرير آخر اليوم الشامل":
    final_text = mgr_msg
  elif msg_template == "قائمة بلاغات الصيانة المفتوحة":
    final_text = (
        f"السلام عليكم، قائمة أعطال {LOCATION_TAG} المفتوحة:\n{pending_str}\n\nيرجى"
        " التوجيه بالإصلاح لا هنتوا."
    )
  elif msg_template == "محضر مطابقة الإعاشة (الوجبات)":
    final_text = (
        f"السلام عليكم، محضر مطابقة وجبة {LOCATION_TAG}:\n- الوجبات اللي جات:"
        f" {last_meal.get('delivered', 0)}\n- المصروف بكوبون:"
        f" {last_meal.get('coupons', 0)}\n- الفائض بالصواني:"
        f" {last_meal.get('surplus', 0)}\n\nيعطيكم العافية."
    )
  else:
    final_text = st.text_area(
        "اكتب رسالتك هنا:",
        placeholder="السلام عليكم، بخصوص سكن جامعة 3...",
        height=120,
    )

  if msg_template != "رسالة مخصصة أكتبها بيدي":
    st.text_area("معاينة الرسالة قبل الإرسال:", value=final_text, height=180)

  if target_phone and target_phone.strip():
    enc_txt = urllib.parse.quote(final_text)
    direct_wa_link = f"https://wa.me/{target_phone.strip()}?text={enc_txt}"
    st.markdown(
        f'<a href="{direct_wa_link}" target="_blank" class="wa-btn">📲 إرسال'
        f" الرسالة فوراً إلى {recipient_choice} عبر واتساب</a>",
        unsafe_allow_html=True,
    )
  else:
    st.warning("الرجاء التأكد من كتابة رقم هاتف صحيح للإرسال.")

  st.divider()
  with st.expander("⚙️ تعديل وتحديث دليل أرقام الواتساب المعتمدة"):
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
      u_mgr = st.text_input(
          "رقم المدير:", value=st.session_state["contacts"]["المدير"]
      )
    with col_u2:
      u_mnt = st.text_input(
          "رقم الصيانة:", value=st.session_state["contacts"]["مقاول الصيانة"]
      )
    with col_u3:
      u_cat = st.text_input(
          "رقم الإعاشة:", value=st.session_state["contacts"]["متعهد الإعاشة"]
      )

    if st.button("حفظ الأرقام الجديدة في الدليل"):
      st.session_state["contacts"]["المدير"] = u_mgr.strip()
      st.session_state["contacts"]["مقاول الصيانة"] = u_mnt.strip()
      st.session_state["contacts"]["متعهد الإعاشة"] = u_cat.strip()
      st.success("تم تحديث دليل الأرقام بنجاح!")
      st.rerun()

# ------------------------------------------------------------------------------
# 7. الخزنة الرقمية (PIN: 5050) وتصدير Excel
# ------------------------------------------------------------------------------
with tab_vault:
  st.markdown("##### 🔐 الخزنة الرقمية والنسخ الاحتياطي:")

  if not st.session_state["is_supervisor"]:
    pin_in = st.text_input("رمز الدخول (5050):", type="password")
    if st.button("🔓 فتح الخزنة", use_container_width=True):
      if hmac.compare_digest(pin_in.strip().encode(), PERMANENT_PIN.encode()):
        st.session_state["is_supervisor"] = True
        st.rerun()
      else:
        st.error("الرمز غير صحيح.")
  else:
    st.success("🟢 الخزنة مفتوحة ومؤمنة.")
    if st.button("🔒 قفل الخزنة"):
      st.session_state["is_supervisor"] = False
      st.rerun()

    st.divider()
    st.markdown("###### 📥 تنزيل تقارير Excel الموثقة:")

    if st.session_state["violations_db"]:
      df_v = pd.DataFrame(st.session_state["violations_db"])
      st.download_button(
          label="تحميل سجل المخالفات (Excel)",
          data=df_v.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Violations_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["maintenance_db"]:
      df_m = pd.DataFrame(st.session_state["maintenance_db"])
      st.download_button(
          label="تحميل سجل الصيانة والإصلاح (Excel)",
          data=df_m.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Repairs_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    if st.session_state["meals_db"]:
      df_meals = pd.DataFrame(st.session_state["meals_db"])
      st.download_button(
          label="تحميل كشف الوجبات (Excel)",
          data=df_meals.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Meals_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )
