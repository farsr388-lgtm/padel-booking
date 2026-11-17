from datetime import datetime, timedelta, timezone
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعدادات السرعة القصوى وتوقيت جدة (UTC+3) والواجهة الميدانية (420px RTL)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))

st.set_page_config(
    page_title="سكن جامعة 3 | عمليات المشرف",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container {
    max-width: 420px !important;
    padding-top: 0.45rem !important;
    padding-bottom: 2rem !important;
    margin: 0 auto !important;
}
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
    background-color: #0b0f19 !important;
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Cairo", sans-serif;
}
/* أزرار كبيرة متتالية تحت إصبع الإبهام (58px) */
div.stButton > button {
    height: 58px !important;
    font-size: 1.05em !important;
    font-weight: 900 !important;
    border-radius: 14px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(16, 185, 129, 0.5) !important;
}
div.stButton > button:active, div.stButton > button:hover {
    background: #10b981 !important;
    color: #022c22 !important;
}
/* إبقاء الأعمدة متجاورة على الآيباد والآيفون (عجلة الساعة + زر تم) */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 0 !important;
}
.header-box {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 8px;
    text-align: center;
}
.success-box {
    background: rgba(16, 185, 129, 0.12);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 12px;
    margin-top: 6px;
    margin-bottom: 8px;
    color: #6ee7b7;
}
.crimson-box {
    background: rgba(190, 18, 60, 0.14);
    border: 1px solid rgba(244, 63, 94, 0.4);
    border-radius: 12px;
    padding: 12px;
    margin-top: 6px;
    margin-bottom: 8px;
    color: #fda4af;
}
.task-row {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.96em;
}
.wa-btn {
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 1.04em;
    text-decoration: none !important;
    margin-top: 6px;
    margin-bottom: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الذاكرة المشتركة خفيفة الاستهلاك (سقف 150 سجل لحماية موارد السيرفر)
# ==============================================================================
MAX_RECORDS = 150


@st.cache_resource
def get_shared_db():
  return {
      "repairs": [],
      "violations": [],
      "meals": [],
  }


db = get_shared_db()

LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
ADMIN_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

OFFICIAL_MEAL_MINS = {
    "فطور": 5 * 60 + 30,  # 05:30 ص
    "غداء": 11 * 60 + 30,  # 11:30 ص
    "عشاء": 17 * 60 + 30,  # 05:30 م
}

DEFAULT_MEAL_PICKER = {
    "فطور": (5, 30, "ص"),
    "غداء": (11, 30, "ص"),
    "عشاء": (5, 30, "م"),
}


def format_room_only(raw_txt: str) -> str:
  clean = raw_txt.strip()
  if clean.isdigit():
    return f"غرفة {clean}"
  return clean


def save_maintenance_ticket(raw_room: str, issue_label: str):
  loc_clean = format_room_only(raw_room)
  t_now = (
      datetime.now(KSA_TZ)
      .strftime("%I:%M %p")
      .replace("AM", "ص")
      .replace("PM", "م")
  )

  # منع التكرار إذا كان البلاغ مفتوحاً حالياً لنفس الغرفة ونفس العطل
  for r in db["repairs"]:
    if (
        r["loc"] == loc_clean
        and r["item"] == issue_label
        and r["status"] == "مفتوح"
    ):
      r["pings"] = r.get("pings", 1) + 1
      st.session_state["last_maint_action"] = {
          "loc": r["loc"],
          "item": r["item"],
          "time": r["time"],
          "repeat_count": r.get("repeat_count", 1),
          "is_duplicate": True,
      }
      return

  # حساب عدد مرات تكرار نفس العطل في نفس الغرفة (حتى لو أُصلح سابقاً)
  prior_count = sum(
      1
      for r in db["repairs"]
      if r["loc"] == loc_clean and r["item"] == issue_label
  )
  current_repeat = prior_count + 1

  db["repairs"].append({
      "loc": loc_clean,
      "item": issue_label,
      "time": t_now,
      "status": "مفتوح",
      "pings": 1,
      "repeat_count": current_repeat,
  })
  if len(db["repairs"]) > MAX_RECORDS:
    db["repairs"] = db["repairs"][-MAX_RECORDS:]

  st.session_state["last_maint_action"] = {
      "loc": loc_clean,
      "item": issue_label,
      "time": t_now,
      "repeat_count": current_repeat,
      "is_duplicate": False,
  }


def save_violation_record(raw_room: str, viol_label: str):
  loc_clean = format_room_only(raw_room)
  t_now = (
      datetime.now(KSA_TZ)
      .strftime("%I:%M %p")
      .replace("AM", "ص")
      .replace("PM", "م")
  )
  repeat_cnt = sum(1 for v in db["violations"] if v["loc"] == loc_clean) + 1

  db["violations"].append({
      "loc": loc_clean,
      "type": viol_label,
      "count": repeat_cnt,
      "time": t_now,
  })
  if len(db["violations"]) > MAX_RECORDS:
    db["violations"] = db["violations"][-MAX_RECORDS:]

  st.session_state["last_viol_action"] = {
      "loc": loc_clean,
      "type": viol_label,
      "count": repeat_cnt,
      "time": t_now,
  }


# ==============================================================================
# 3. الترويسة والتبويبات الثلاثة المفتوحة مباشرة (بدون كلمة مرور)
# ==============================================================================
st.markdown(
    f"""
    <div class="header-box">
        <b style="font-size:1.12em;">🏢 {LOCATION_TAG} | {SUPERVISOR_NAME}</b>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_maint, tab_viol, tab_meals = st.tabs([
    "🛠️ 1. الصيانة",
    "⚠️ 2. المخالفات",
    "🍱 3. الوجبات",
])

# ------------------------------------------------------------------------------
# المهمة 1: الصيانة + قائمة الإنجاز الفوري (تم ✓) في الواجهة مباشرة
# ------------------------------------------------------------------------------
with tab_maint:
  m_room = st.text_input(
      "1️⃣ رقم الغرفة أو الموقع:",
      placeholder="مثال: 213 أو السطح",
      key="m_room_in",
  )

  st.caption("2️⃣ اضغط نوع الطلب للحفظ الفوري:")
  b_elec = st.button("🔌 كهربائي / فيش", key="btn_m_elec")
  b_ac = st.button("❄️ مكيف AC", key="btn_m_ac")
  b_plumb = st.button("🚰 سباكة / صنبور", key="btn_m_plumb")
  b_pest = st.button("🪲 مبيد حشرات", key="btn_m_pest")

  chosen_m_issue = None
  if b_elec:
    chosen_m_issue = "كهربائي / فيش"
  elif b_ac:
    chosen_m_issue = "مكيف AC"
  elif b_plumb:
    chosen_m_issue = "سباكة / صنبور"
  elif b_pest:
    chosen_m_issue = "مبيد حشرات"

  if chosen_m_issue:
    if not m_room.strip():
      st.warning("⚠️ اكتب رقم الغرفة أو الموقع أولاً.")
    else:
      save_maintenance_ticket(m_room, chosen_m_issue)

  if "last_maint_action" in st.session_state:
    act = st.session_state["last_maint_action"]
    rep_note = (
        f" (تكرار {act['repeat_count']})" if act.get("repeat_count", 1) > 1 else ""
    )
    wa_maint_msg = (
        f"*{LOCATION_TAG} — صيانة*\n• الموقع: {act['loc']}\n• الطلب:"
        f" {act['item']}{rep_note}\n• الوقت: {act['time']}"
    )
    wa_maint_url = (
        f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_maint_msg)}"
    )

    if act.get("is_duplicate"):
      st.markdown(
          f"""
                <div class="crimson-box">
                    <b>⏳ قيد التنفيذ مسبقاً:</b> {act['loc']} — {act['item']} ({act['time']})
                </div>
                <a href="{wa_maint_url}" target="_blank" class="wa-btn">📲 إرسال تذكير عبر واتساب</a>
                """,
          unsafe_allow_html=True,
      )
    else:
      st.markdown(
          f"""
                <div class="success-box">
                    <b>✅ تم الحفظ:</b> {act['loc']} — {act['item']}{rep_note} ({act['time']})
                </div>
                <a href="{wa_maint_url}" target="_blank" class="wa-btn">📲 إرسال عبر واتساب</a>
                """,
          unsafe_allow_html=True,
      )

  # قائمة الطلبات المفتوحة في الواجهة مباشرة — ضغطة (تم ✓) تنقلها للمنجز فوراً
  open_reps_main = [r for r in db["repairs"] if r["status"] == "مفتوح"]
  if open_reps_main:
    st.markdown("---")
    st.markdown(
        f"##### ⏳ قيد التنفيذ ({len(open_reps_main)}) — اضغط تم عند الإنجاز:"
    )
    for idx, r in enumerate(reversed(open_reps_main)):
      col_txt, col_btn = st.columns([2.5, 1.1])
      rep_badge = (
          f" • تكرار {r['repeat_count']}" if r.get("repeat_count", 1) > 1 else ""
      )
      ping_badge = f" • استعجال {r['pings']}" if r.get("pings", 1) > 1 else ""
      col_txt.markdown(
          f"<div class='task-row'><b>{r['loc']}</b> — {r['item']}<br><small"
          f" style='color:#94a3b8;'>⏰"
          f" {r['time']}{rep_badge}{ping_badge}</small></div>",
          unsafe_allow_html=True,
      )
      if col_btn.button(
          "تم ✓", key=f"main_done_{idx}_{r['loc']}_{r['item']}_{r['time']}"
      ):
        r["status"] = "تم الإصلاح"
        st.rerun()

# ------------------------------------------------------------------------------
# المهمة 2: رصد المخالفات (خطوتان + بدون زر واتساب + حفظ التكرار)
# ------------------------------------------------------------------------------
with tab_viol:
  v_room = st.text_input(
      "1️⃣ رقم الغرفة المخالفة:", placeholder="مثال: 108", key="v_room_in"
  )

  st.caption("2️⃣ اضغط نوع المخالفة للحفظ الفوري:")
  bv_heater = st.button("⚡ مخالفة سخان", key="btn_v_heater")
  bv_clean = st.button("🗑️ مخالفة نظافة", key="btn_v_clean")
  bv_both = st.button("⚠️ مخالفة سخان ونظافة معاً", key="btn_v_both")

  chosen_v_type = None
  if bv_heater:
    chosen_v_type = "مخالفة سخان"
  elif bv_clean:
    chosen_v_type = "مخالفة نظافة"
  elif bv_both:
    chosen_v_type = "مخالفة سخان ونظافة معاً"

  if chosen_v_type:
    if not v_room.strip():
      st.warning("⚠️ اكتب رقم الغرفة المخالفة أولاً.")
    else:
      save_violation_record(v_room, chosen_v_type)

  if "last_viol_action" in st.session_state:
    v_act = st.session_state["last_viol_action"]
    st.markdown(
        f"""
            <div class="success-box">
                <b>✅ تم تسجيل المخالفة:</b> {v_act['loc']} — {v_act['type']}<br>
                <small>التكرار للغرفة: <b>{v_act['count']}</b> • الوقت: {v_act['time']}</small>
            </div>
            """,
        unsafe_allow_html=True,
    )

  if db["violations"]:
    st.markdown("---")
    st.markdown(f"##### 📋 مخالفات اليوم ({len(db['violations'])}):")
    for v_idx, v_item in enumerate(reversed(db["violations"])):
      vc1, vc2 = st.columns([2.6, 1.0])
      vc1.markdown(
          f"<div class='task-row'><b>{v_item['loc']}</b> — {v_item['type']}"
          f" <small style='color:#fda4af;'>(تكرار"
          f" {v_item['count']})</small></div>",
          unsafe_allow_html=True,
      )
      if vc2.button("حذف", key=f"del_v_{v_idx}_{v_item['loc']}_{v_item['time']}"):
        db["violations"].remove(v_item)
        st.rerun()

# ------------------------------------------------------------------------------
# المهمة 3: توثيق وصول الوجبات (عجلة ساعة Apple الدوارة + قاعدة التأخير > 30 دقيقة)
# ------------------------------------------------------------------------------
with tab_meals:
  meal_choice = st.radio(
      "1️⃣ اختر الوجبة:", ["فطور", "غداء", "عشاء"], index=1, horizontal=True
  )

  st.caption("2️⃣ اسحب عجلة الوقت لتحديد ساعة الوصول:")
  def_h, def_m, def_p = DEFAULT_MEAL_PICKER[meal_choice]
  hours_opts = list(range(1, 13))
  mins_opts = list(range(0, 60))
  period_opts = ["ص", "م"]

  w_col1, w_col2, w_col3 = st.columns([1, 1, 1])
  with w_col1:
    sel_h = st.selectbox(
        "الساعة",
        hours_opts,
        index=hours_opts.index(def_h),
        key=f"wheel_h_{meal_choice}",
    )
  with w_col2:
    sel_m = st.selectbox(
        "الدقيقة",
        mins_opts,
        index=mins_opts.index(def_m),
        format_func=lambda x: f"{x:02d}",
        key=f"wheel_m_{meal_choice}",
    )
  with w_col3:
    sel_p = st.selectbox(
        "الفترة",
        period_opts,
        index=period_opts.index(def_p),
        key=f"wheel_p_{meal_choice}",
    )

  if sel_p == "ص":
    h24 = 0 if sel_h == 12 else sel_h
  else:
    h24 = 12 if sel_h == 12 else sel_h + 12

  actual_mins = h24 * 60 + sel_m
  official_mins = OFFICIAL_MEAL_MINS[meal_choice]
  raw_delay = actual_mins - official_mins
  counted_delay = raw_delay if raw_delay > 30 else 0
  arr_formatted = f"{sel_h:02d}:{sel_m:02d} {sel_p}"

  if counted_delay > 0:
    status_text = f"تأخير {counted_delay} دقيقة - وصل الساعة {arr_formatted}"
    st.markdown(
        f"<div class='crimson-box'>🟣 <b>{status_text}</b></div>",
        unsafe_allow_html=True,
    )
  else:
    status_text = "في الموعد"
    st.markdown(
        f"<div class='success-box'>🟢 <b>{status_text}</b> (الوصول:"
        f" {arr_formatted})</div>",
        unsafe_allow_html=True,
    )

  deliv_qty = st.text_input("العدد المستلم:", value="77", key="meal_deliv_qty")
  has_surplus = st.radio(
      "هل يوجد فائض؟", ["لا", "نعم"], horizontal=True, key="meal_has_surp"
  )
  surplus_qty = (
      st.text_input("كم الفائض؟", value="0", key="meal_surp_qty")
      if has_surplus == "نعم"
      else "0"
  )

  if st.button("✅ اعتماد الوجبة", key="btn_save_meal"):
    db["meals"].append({
        "meal": meal_choice,
        "arrival": arr_formatted,
        "delay_mins": counted_delay,
        "status_text": status_text,
        "delivered": deliv_qty.strip() or "0",
        "has_surplus": has_surplus,
        "surplus": surplus_qty.strip() or "0",
    })
    if len(db["meals"]) > MAX_RECORDS:
      db["meals"] = db["meals"][-MAX_RECORDS:]
    st.session_state["last_meal_saved"] = f"{meal_choice} ({status_text})"

  if "last_meal_saved" in st.session_state:
    st.markdown(
        "<div class='success-box'>✅ <b>تم اعتماد الوجبة:</b>"
        f" {st.session_state['last_meal_saved']}</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ==============================================================================
# 4. قسم الإدارة المغلق برمز 5050 [🔐 التقرير الشامل وبدء يوم جديد]
# ==============================================================================
with st.expander("🔐 التقرير الشامل وبدء يوم جديد"):
  pin_in = st.text_input(
      "رمز الدخول (5050):", type="password", key="admin_pin_box"
  )
  if hmac.compare_digest(
      pin_in.strip().encode("utf-8"), ADMIN_PIN.encode("utf-8")
  ):
    open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
    fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]

    if db["meals"]:
      lm = db["meals"][-1]
    else:
      lm = {
          "meal": meal_choice,
          "status_text": status_text,
          "delivered": deliv_qty.strip() or "0",
          "has_surplus": has_surplus,
          "surplus": surplus_qty.strip() or "0",
      }

    open_lines = (
        "\n".join([
            f"• {r['loc']}: {r['item']}"
            + (
                f" (تكرار {r['repeat_count']})"
                if r.get("repeat_count", 1) > 1
                else ""
            )
            for r in open_reps
        ])
        if open_reps
        else "• لا يوجد"
    )
    fixed_lines = (
        "\n".join([
            f"• {r['loc']}: {r['item']} ✓"
            + (
                f" (تكرار {r['repeat_count']})"
                if r.get("repeat_count", 1) > 1
                else ""
            )
            for r in fixed_reps
        ])
        if fixed_reps
        else "• لا يوجد"
    )

    # حصر الغرف المتكررة في الصيانة أو المخالفات لتوثيقها بالأرقام
    recurring_items = [
        f"{r['loc']} ({r['item']} ×{r['repeat_count']})"
        for r in db["repairs"]
        if r.get("repeat_count", 1) > 1
    ]
    recurring_summary = (
        "، ".join(dict.fromkeys(recurring_items)) if recurring_items else "لا يوجد"
    )

    viol_total = len(db["violations"])
    viol_lines = (
        "\n".join([
            f"• {v['loc']}: {v['type']} (التكرار: {v['count']})"
            for v in db["violations"]
        ])
        if viol_total > 0
        else "• لا يوجد"
    )

    clean_report = f"""*{LOCATION_TAG}*
*المشرف: {SUPERVISOR_NAME}*

*🍱 الإعاشة ({lm['meal']}):* {lm['status_text']}
• العدد المستلم: {lm['delivered']}
• هل يوجد فائض: {lm['has_surplus']}
• كم الفائض: {lm['surplus']}

*🛠️ الصيانة:*
قيد التنفيذ ({len(open_reps)}):
{open_lines}
تم الإصلاح ({len(fixed_reps)}):
{fixed_lines}
• المتكرر: {recurring_summary}

*⚠️ المخالفات اليوم ({viol_total}):*
{viol_lines}"""

    st.text_area("نص التقرير الجاهز:", value=clean_report, height=240)

    wa_rep_url = (
        f"https://api.whatsapp.com/send?text={urllib.parse.quote(clean_report)}"
    )
    st.markdown(
        f'<a href="{wa_rep_url}" target="_blank" class="wa-btn">📲 مشاركة'
        " التقرير عبر واتساب</a>",
        unsafe_allow_html=True,
    )

    repairs_df = pd.DataFrame(db["repairs"])
    viols_df = pd.DataFrame(db["violations"])
    meals_df = pd.DataFrame(db["meals"])

    dl_c1, dl_c2, dl_c3 = st.columns(3)
    with dl_c1:
      st.download_button(
          "📥 الصيانة CSV",
          data=repairs_df.to_csv(index=False).encode("utf-8-sig"),
          file_name="Maintenance.csv",
          mime="text/csv",
          use_container_width=True,
      )
    with dl_c2:
      st.download_button(
          "📥 المخالفات CSV",
          data=viols_df.to_csv(index=False).encode("utf-8-sig"),
          file_name="Violations.csv",
          mime="text/csv",
          use_container_width=True,
      )
    with dl_c3:
      st.download_button(
          "📥 الوجبات CSV",
          data=meals_df.to_csv(index=False).encode("utf-8-sig"),
          file_name="Meals.csv",
          mime="text/csv",
          use_container_width=True,
      )

    st.markdown("---")

    if st.button("🗑️ تصفير السجل بالكامل وبدء يوم جديد", key="btn_reset_all"):
      db["repairs"].clear()
      db["violations"].clear()
      db["meals"].clear()
      for k in ["last_maint_action", "last_viol_action", "last_meal_saved"]:
        if k in st.session_state:
          del st.session_state[k]
      st.success("✅ تم تصفير السجل بالكامل وبدء يوم جديد!")
      st.rerun()
  elif pin_in:
    st.error("⛔ رمز الدخول غير صحيح.")
