from datetime import datetime
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (سريع وخفيف)
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
# 2. الثوابت العامة والرمز الدائم 5050
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

# أرقام الواتساب الافتراضية
if "phone_maint" not in st.session_state:
  st.session_state["phone_maint"] = "966500000000"
if "phone_mgr" not in st.session_state:
  st.session_state["phone_mgr"] = "966500000000"

# تهيئة قواعد البيانات
if "meals_db" not in st.session_state:
  st.session_state["meals_db"] = []

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

if "rounds_db" not in st.session_state:
  st.session_state["rounds_db"] = []

if "is_supervisor" not in st.session_state:
  st.session_state["is_supervisor"] = False

# ==============================================================================
# 3. ترويسة التطبيق
# ==============================================================================
st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 إدارة {LOCATION_TAG}</div>
    <div class="sub-headline">العمليات اليومية • بلاغات الصيانة • رصد المخالفات</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_repairs, tab_viol, tab_meals, tab_rounds, tab_daily_report, tab_vault = (
    st.tabs([
        "🛠️ الصيانة",
        "⚠️ المخالفات",
        "🍽️ الأكل",
        "🚶 الجولات",
        "📋 تقرير آخر اليوم",
        "🔐 الخزنة",
    ])
)

# ------------------------------------------------------------------------------
# 1. تبويب الصيانة: التعامل البسيط (تم تصليح المكيف مع تسجيل الوقت)
# ------------------------------------------------------------------------------
with tab_repairs:
  st.markdown("##### 🛠️ بلاغ عطل جديد:")

  with st.form("quick_rep", clear_on_submit=True):
    r_room = st.text_input("رقم الغرفة:", placeholder="مثال: 104")
    r_item = st.radio(
        "العطل:", ["مكيف ❄️", "شطاف 🚿", "أخرى 🛠️"], horizontal=True
    )

    other_text = ""
    if "أخرى" in r_item:
      other_text = st.text_input(
          "اكتب العطل:", placeholder="مثال: لمبة / فيش / سخان موية..."
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
        st.success(f"تم تسجيل بلاغ: غرفة {c_r} ({final_i}).")

  st.markdown("---")
  st.markdown("##### 📋 البلاغات الحالية:")

  open_reps = [
      x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"
  ]
  if open_reps:
    # صياغة رسالة واتساب عادية وطبيعية للصيانة
    maint_wa_lines = [f"السلام عليكم، بلاغات صيانة {LOCATION_TAG}:"]
    for idx, row in enumerate(open_reps):
      st.markdown(
          f"""
                <div class="stat-box">
                    <b>غرفة {row['room']}</b> — <span style="color:var(--primary); font-weight:800;">{row['item']}</span><br>
                    <small style="color:#94a3b8;">وقت البلاغ: {row['opened_at']}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )
      maint_wa_lines.append(f"- غرفة {row['room']}: {row['item']}")

      # زر التعامل العادي مع المشكلة
      if st.button(
          f"✅ تم تصليح {row['item']} غرفة {row['room']}", key=f"fix_b_{idx}"
      ):
        row["status"] = "تم الإصلاح"
        row["closed_at"] = datetime.now().strftime("%I:%M %p")
        st.success(
            f"تم تصليح {row['item']} غرفة {row['room']} (الساعة"
            f" {row['closed_at']}) ✓"
        )
        st.rerun()

    maint_wa_lines.append("\nيعطيكم العافية يرجى التشييك عليها والإصلاح.")
    enc_maint = urllib.parse.quote("\n".join(maint_wa_lines))
    wa_maint_link = f"https://wa.me/{st.session_state['phone_maint']}?text={enc_maint}"

    st.markdown(
        f'<a href="{wa_maint_link}" target="_blank" class="wa-btn">📲 إرسال'
        " البلاغات للصيانة عبر واتساب</a>",
        unsafe_allow_html=True,
    )
  else:
    st.info("ما فيه أي بلاغات مفتوحة حالياً، السكن سليم.")

  # كشف ما تم تصليحه اليوم
  done_reps = [
      x
      for x in st.session_state["maintenance_db"]
      if x["status"] == "تم الإصلاح"
  ]
  if done_reps:
    with st.expander("🔍 وش اللي تصلح اليوم؟"):
      for d in reversed(done_reps[-4:]):
        st.markdown(
            f"""
                    <div class="stat-box" style="border-right: 3px solid #10b981;">
                        <b>غرفة {d['room']}</b>: {d['item']} <span class='done-tag'>تم تصليحه ✓</span><br>
                        <small style="color:#94a3b8;">أُصلح الساعة: <b>{d['closed_at']}</b> (البلاغ كان {d['opened_at']})</small>
                    </div>
                    """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------------------
# 2. تبويب المخالفات: رقم الغرفة والسبب والمرة الكم مع التاريخ والوقت
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
        "السبب والملاحظة:",
        placeholder="مثال: مشغل هيتر طبخ / مجمع أكياس زبالة...",
    )

    btn_viol = st.form_submit_button("⚡ حفظ المخالفة")

    if btn_viol:
      c_vr = v_room.strip()
      chosen_type = (
          custom_v.strip()
          if ("أخرى" in v_type and custom_v.strip())
          else v_type.split()[0]
      )

      if not c_vr:
        st.error("اكتب رقم الغرفة أولاً.")
      else:
        # حساب تكرار المخالفة لنفس الغرفة
        past_times = sum(
            1
            for v in st.session_state["violations_db"]
            if v["room"] == c_vr and v["type"] == chosen_type
        )
        this_count = past_times + 1
        now_time = datetime.now().strftime("%I:%M %p")
        now_date = datetime.now().strftime("%Y-%m-%d")

        st.session_state["violations_db"].append({
            "room": c_vr,
            "type": chosen_type,
            "reason": (
                v_reason.strip() if v_reason.strip() else "رصد مخالفة بالسكن"
            ),
            "count": this_count,
            "time": now_time,
            "date": now_date,
        })
        st.success(
            f"تم قيد مخالفة غرفة {c_vr} ({chosen_type}) — المرة الـ"
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
                    <b>غرفة {v['room']}</b> — <span style="color:#f87171; font-weight:800;">{v['type']}</span>
                    <span class='{tag_c}'>المرة الـ {c_num}</span><br>
                    <small style="color:#cbd5e1;">السبب: {v['reason']}</small><br>
                    <small style="color:#94a3b8;">📅 التاريخ: {v['date']} | ⏰ الوقت: {v['time']}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )
  else:
    st.info("سجل المخالفات نظيف.")

# ------------------------------------------------------------------------------
# 3. تبويب الأكل: كم وجبة جات وكوبون وفائض
# ------------------------------------------------------------------------------
with tab_meals:
  st.markdown("##### 🍽️ حصر وجبة اليوم:")

  with st.form("meal_form", clear_on_submit=False):
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
# 4. تبويب الجولات الميدانية
# ------------------------------------------------------------------------------
with tab_rounds:
  st.markdown("##### 🚶 توثيق جولة اليوم:")

  curr_hour = datetime.now().hour
  def_round = 0 if curr_hour < 14 else 1

  with st.form("round_form", clear_on_submit=True):
    sel_r = st.radio(
        "الجولة:",
        ["جولة الصباح (09:30 ص)", "جولة الليل (08:30 م)"],
        index=def_round,
        horizontal=True,
    )
    r_notes = st.text_input(
        "ملاحظة الجولة:",
        placeholder="مثال: تم التشييك على النظافة والسكن هادئ...",
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
                    <b>{r['round']}</b> — <small style="color:var(--primary);">{r['time']}</small><br>
                    <small style="color:#cbd5e1;">الملاحظة: {r['note']}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )

# ------------------------------------------------------------------------------
# 5. تبويب تقرير آخر اليوم: ملخص عادي وسريع ومباشر للإرسال بضغطة زر
# ------------------------------------------------------------------------------
with tab_daily_report:
  st.markdown("##### 📋 تقرير آخر اليوم الميداني:")
  st.caption("ملخص مركز بالمهم والمخالفات مع التاريخ والوقت بأسلوب مباشر وعادي:")

  today_date = datetime.now().strftime("%Y-%m-%d")

  # تجميع بيانات اليوم
  last_meal_data = (
      st.session_state["meals_db"][-1]
      if st.session_state["meals_db"]
      else {"delivered": 77, "coupons": 42, "surplus": 0}
  )

  # الأعطال التي تم تصليحها اليوم
  fixed_today = [
      x
      for x in st.session_state["maintenance_db"]
      if x["status"] == "تم الإصلاح"
  ]
  fixed_text = (
      "\n".join(
          [f"  • تم تصليح {x['item']} غرفة {x['room']} (الساعة {x['closed_at']})" for x in fixed_today]
      )
      if fixed_today
      else "  • لا توجد أعطال تم إصلاحها اليوم."
  )

  # الأعطال المتبقية المفتوحة
  pending_today = [
      x for x in st.session_state["maintenance_db"] if x["status"] == "مفتوح"
  ]
  pending_text = (
      "\n".join(
          [f"  • غرفة {x['room']}: {x['item']} (مسجل {x['opened_at']})" for x in pending_today]
      )
      if pending_today
      else "  • لا توجد أعطال معلقة."
  )

  # المخالفات المرصودة بالوقت والتاريخ
  today_viols = st.session_state["violations_db"]
  viols_text = (
      "\n".join([
          f"  • غرفة {v['room']}: {v['type']} (المرة {v.get('count', 1)}) -"
          f" السبب: {v['reason']} [{v['date']} {v['time']}]"
          for v in today_viols[-5:]
      ])
      if today_viols
      else "  • لا توجد مخالفات مرصودة اليوم."
  )

  # آخر جولة
  last_rnd = (
      st.session_state["rounds_db"][-1]
      if st.session_state["rounds_db"]
      else {"round": "جولة المساء", "note": "السكن هادئ ونظيف"}
  )

  # صياغة التقرير العادي المباشر
  daily_report_message = f"""تقرير {LOCATION_TAG} اليومي - {today_date}

1️⃣ الإعاشة:
- الوجبات اللي جات: {last_meal_data.get('delivered', 0)}
- المصروف بكوبون: {last_meal_data.get('coupons', 0)}
- الفائض بالصواني: {last_meal_data.get('surplus', 0)}

2️⃣ الصيانة والأعطال:
- المنجز اليوم:
{fixed_text}
- البلاغات المعلقة:
{pending_text}

3️⃣ المخالفات المضبوطة:
{viols_text}

4️⃣ الجولات الميدانية:
- آخر جولة: {last_rnd.get('round', '')} ({last_rnd.get('note', '')})

الوضع العام بالسكن: منضبط وكل شيء تحت السيطرة."""

  st.text_area(
      "نص تقرير آخر اليوم (رسالة عادية):",
      value=daily_report_message,
      height=260,
  )

  enc_report = urllib.parse.quote(daily_report_message)
  wa_report_link = (
      f"https://wa.me/{st.session_state['phone_mgr']}?text={enc_report}"
  )

  st.markdown(
      f'<a href="{wa_report_link}" target="_blank" class="wa-btn">📲 إرسال'
      " تقرير آخر اليوم للمدير عبر واتساب</a>",
      unsafe_allow_html=True,
  )

  with st.expander("⚙️ تعديل رقم جوال المدير للواتساب"):
    new_mgr_no = st.text_input(
        "رقم المدير (مع مفتاح 966):", value=st.session_state["phone_mgr"]
    )
    if st.button("حفظ رقم المدير"):
      st.session_state["phone_mgr"] = new_mgr_no.strip()
      st.success("تم حفظ الرقم!")
      st.rerun()

# ------------------------------------------------------------------------------
# 6. الخزنة الرقمية (PIN: 5050) وتصدير Excel
# ------------------------------------------------------------------------------
with tab_vault:
  st.markdown("##### 🔐 الخزنة الرقمية:")

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
    st.markdown("###### 📥 تنزيل تقارير Excel الموثقة بالتاريخ والوقت:")

    if st.session_state["violations_db"]:
      df_v = pd.DataFrame(st.session_state["violations_db"])
      st.download_button(
          label="تحميل سجل المخالفات بالتاريخ والوقت (Excel)",
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
