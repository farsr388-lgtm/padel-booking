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
/* أزرار كبيرة متتالية تحت إصبع الإبهام (56px) */
div.stButton > button {
    height: 56px !important;
    font-size: 1.03em !important;
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
/* إبقاء الأعمدة متجاورة على الآيباد والآيفون */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 6px !important;
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
    padding: 11px;
    margin-top: 6px;
    margin-bottom: 8px;
    color: #6ee7b7;
}
.crimson-box {
    background: rgba(190, 18, 60, 0.14);
    border: 1px solid rgba(244, 63, 94, 0.4);
    border-radius: 12px;
    padding: 11px;
    margin-top: 6px;
    margin-bottom: 8px;
    color: #fda4af;
}
.task-row {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    padding: 9px 11px;
    font-size: 0.92em;
    margin-bottom: 4px;
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
# 2. الذاكرة المشتركة خفيفة الاستهلاك (سقف 150 سجل + ذاكرة الغرف المستمرة)
# ==============================================================================
MAX_RECORDS = 150


@st.cache_resource
def get_shared_db():
  return {
      "repairs": [],  # بلاغات الصيانة والمبيدات
      "followups": [],  # سجل المتابعة والتشيك بالتاريخ (مبيدات + إنذارات + نظافة)
      "room_history": (
          {}
      ),  # ذاكرة تراكمية لعدد التكرارات لكل غرفة حتى بعد بدء يوم جديد
  }


db = get_shared_db()

LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
ADMIN_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()


def now_stamp() -> str:
  """التاريخ والساعة بتوقيت جدة (مثال: 11/17 - 11:05 م)."""
  return (
      datetime.now(KSA_TZ)
      .strftime("%m/%d - %I:%M %p")
      .replace("AM", "ص")
      .replace("PM", "م")
  )


def format_room_only(raw_txt: str) -> str:
  clean = raw_txt.strip()
  if clean.isdigit():
    return f"غرفة {clean}"
  return clean


def save_maintenance_ticket(raw_room: str, issue_label: str, severity: str):
  loc_clean = format_room_only(raw_room)
  ts = now_stamp()

  # منع التكرار إذا كان البلاغ مفتوحاً حالياً لنفس الغرفة ونفس العطل
  for r in db["repairs"]:
    if (
        r["loc"] == loc_clean
        and r["item"] == issue_label
        and r["status"] == "مفتوح"
    ):
      r["pings"] = r.get("pings", 1) + 1
      r["severity"] = severity
      r["last_ping_time"] = ts
      st.session_state["last_maint_action"] = {
          "loc": r["loc"],
          "item": r["item"],
          "severity": severity,
          "time": r["time"],
          "repeat_count": r.get("repeat_count", 1),
          "is_duplicate": True,
      }
      return

  # تحديث الذاكرة الدائمة لتكرار الأعطال في هذه الغرفة
  hist_key = f"{loc_clean}_{issue_label}"
  db["room_history"][hist_key] = db["room_history"].get(hist_key, 0) + 1
  current_repeat = db["room_history"][hist_key]

  if len(db["room_history"]) > 500:
    oldest_key = next(iter(db["room_history"]))
    del db["room_history"][oldest_key]

  db["repairs"].append({
      "loc": loc_clean,
      "item": issue_label,
      "severity": severity,
      "time": ts,
      "closed_time": "",
      "status": "مفتوح",
      "pings": 1,
      "repeat_count": current_repeat,
  })
  if len(db["repairs"]) > MAX_RECORDS:
    db["repairs"] = db["repairs"][-MAX_RECORDS:]

  # إذا كان الطلب (مبيد حشرات)، يُضاف تلقائياً لقائمة المراجعة والتشيك بالتاريخ
  if "مبيد حشرات" in issue_label:
    db["followups"].append({
        "loc": loc_clean,
        "category": "مبيد حشرات",
        "detail": f"طلب/تسليم مبيد حشرات (مرة {current_repeat})",
        "created_at": ts,
        "checked_at": "",
        "state": "بانتظار التشيك",
        "count": current_repeat,
    })
    if len(db["followups"]) > MAX_RECORDS:
      db["followups"] = db["followups"][-MAX_RECORDS:]

  st.session_state["last_maint_action"] = {
      "loc": loc_clean,
      "item": issue_label,
      "severity": severity,
      "time": ts,
      "repeat_count": current_repeat,
      "is_duplicate": False,
  }


def save_followup_record(raw_room: str, category: str, detail_label: str):
  loc_clean = format_room_only(raw_room)
  ts = now_stamp()

  hist_key = f"{loc_clean}_{category}"
  db["room_history"][hist_key] = db["room_history"].get(hist_key, 0) + 1
  cnt = db["room_history"][hist_key]

  initial_state = (
      "غرفة نظيفة ومميزة 🌟"
      if category == "غرفة نظيفة"
      else "بانتظار المراجعة"
  )
  checked_stamp = ts if category == "غرفة نظيفة" else ""

  db["followups"].append({
      "loc": loc_clean,
      "category": category,
      "detail": detail_label,
      "created_at": ts,
      "checked_at": checked_stamp,
      "state": initial_state,
      "count": cnt,
  })
  if len(db["followups"]) > MAX_RECORDS:
    db["followups"] = db["followups"][-MAX_RECORDS:]

  st.session_state["last_viol_action"] = {
      "loc": loc_clean,
      "detail": detail_label,
      "count": cnt,
      "time": ts,
  }


# دوال الاستجابة الفورية للأزرار (تُنفذ الحفظ وتمسح رقم الغرفة تلقائياً)
def on_click_maint(issue_label: str):
  raw_room = st.session_state.get("m_room_in", "").strip()
  if not raw_room:
    st.session_state["maint_err"] = "⚠️ اكتب رقم الغرفة أو الموقع أولاً."
    return
  st.session_state["maint_err"] = ""
  sev = st.session_state.get("m_sev_radio", "🔴 طارئ")
  save_maintenance_ticket(raw_room, issue_label, sev)
  st.session_state["m_room_in"] = ""


def on_click_followup(category: str, detail_label: str):
  raw_room = st.session_state.get("v_room_in", "").strip()
  if not raw_room:
    st.session_state["viol_err"] = "⚠️ اكتب رقم الغرفة أولاً."
    return
  st.session_state["viol_err"] = ""
  save_followup_record(raw_room, category, detail_label)
  st.session_state["v_room_in"] = ""


# ==============================================================================
# 3. الترويسة والتبويبان الأساسيان (الصيانة والمبيدات | الإنذارات والنظافة)
# ==============================================================================
st.markdown(
    f"""
    <div class="header-box">
        <b style="font-size:1.12em;">🏢 {LOCATION_TAG} | {SUPERVISOR_NAME}</b>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_maint, tab_viol = st.tabs([
    "🛠️ 1. الصيانة والمبيدات",
    "📋 2. الإنذارات والنظافة",
])

# ------------------------------------------------------------------------------
# المهمة 1: الصيانة والمبيدات (تصنيف طارئ/نص حالة + مسح الرقم تلقائياً + تم ✓)
# ------------------------------------------------------------------------------
with tab_maint:
  st.text_input(
      "1️⃣ رقم الغرفة أو الموقع:", placeholder="مثال: 213 أو السطح", key="m_room_in"
  )

  st.radio(
      "الحالة:",
      ["🔴 طارئ", "🟡 نص حالة"],
      horizontal=True,
      key="m_sev_radio",
  )

  st.caption("2️⃣ اضغط نوع الطلب (يُحفظ فوراً ويُمسح الرقم):")
  st.button(
      "🔌 كهربائي / فيش",
      key="btn_m_elec",
      on_click=on_click_maint,
      args=("كهربائي / فيش",),
  )
  st.button(
      "❄️ مكيف AC",
      key="btn_m_ac",
      on_click=on_click_maint,
      args=("مكيف AC",),
  )
  st.button(
      "🚰 سباكة / صنبور",
      key="btn_m_plumb",
      on_click=on_click_maint,
      args=("سباكة / صنبور",),
  )
  st.button(
      "🪲 مبيد حشرات",
      key="btn_m_pest",
      on_click=on_click_maint,
      args=("مبيد حشرات",),
  )

  if st.session_state.get("maint_err"):
    st.warning(st.session_state["maint_err"])

  if "last_maint_action" in st.session_state:
    act = st.session_state["last_maint_action"]
    rep_note = (
        f" (تكرار {act['repeat_count']})" if act.get("repeat_count", 1) > 1 else ""
    )
    wa_maint_msg = (
        f"*{LOCATION_TAG} — صيانة*\n• الموقع: {act['loc']}\n• الطلب:"
        f" {act['item']} [{act['severity']}]{rep_note}\n• الوقت: {act['time']}"
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
                    <b>✅ تم الحفظ:</b> {act['loc']} — {act['item']} [{act['severity']}]{rep_note}<br>
                    <small>📅 {act['time']}</small>
                </div>
                <a href="{wa_maint_url}" target="_blank" class="wa-btn">📲 إرسال عبر واتساب</a>
                """,
          unsafe_allow_html=True,
      )

  # قائمة الصيانة المفتوحة في الواجهة مباشرة — ضغطة (تم ✓) تغلقها وتختم تاريخ الإنجاز
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
      col_txt.markdown(
          f"<div class='task-row'><b>{r['loc']}</b> — {r['item']}"
          f" [{r.get('severity', '🔴 طارئ')}]<br><small"
          f" style='color:#94a3b8;'>📅 {r['time']}{rep_badge}</small></div>",
          unsafe_allow_html=True,
      )
      if col_btn.button(
          "تم ✓", key=f"main_done_{idx}_{r['loc']}_{r['item']}_{r['time']}"
      ):
        r["status"] = "تم الإصلاح"
        r["closed_time"] = now_stamp()
        st.rerun()

# ------------------------------------------------------------------------------
# المهمة 2: الإنذارات وتقييم النظافة + المراجعة والتشيك بالتاريخ
# ------------------------------------------------------------------------------
with tab_viol:
  st.text_input("1️⃣ رقم الغرفة:", placeholder="مثال: 108", key="v_room_in")

  st.caption("2️⃣ اضغط التصنيف (يُحفظ بالتاريخ ويُمسح الرقم تلقائياً):")
  st.button(
      "⚡ إنذار سخان",
      key="btn_v_heater",
      on_click=on_click_followup,
      args=("إنذار", "إنذار سخان"),
  )
  st.button(
      "🗑️ إنذار نظافة",
      key="btn_v_clean",
      on_click=on_click_followup,
      args=("إنذار", "إنذار نظافة"),
  )
  st.button(
      "⚠️ إنذار سخان ونظافة",
      key="btn_v_both",
      on_click=on_click_followup,
      args=("إنذار", "إنذار سخان ونظافة"),
  )
  st.button(
      "🟡 غرفة نص نص (متابعة)",
      key="btn_v_half",
      on_click=on_click_followup,
      args=("متابعة نظافة", "غرفة نص نص"),
  )
  st.button(
      "🌟 غرفة نظيفة ومميزة",
      key="btn_v_good",
      on_click=on_click_followup,
      args=("غرفة نظيفة", "غرفة نظيفة ومميزة"),
  )

  if st.session_state.get("viol_err"):
    st.warning(st.session_state["viol_err"])

  if "last_viol_action" in st.session_state:
    v_act = st.session_state["last_viol_action"]
    st.markdown(
        f"""
            <div class="success-box">
                <b>✅ تم القيد:</b> {v_act['loc']} — {v_act['detail']}<br>
                <small>📅 {v_act['time']} • السجل التراكمي: <b>{v_act['count']}</b></small>
            </div>
            """,
        unsafe_allow_html=True,
    )

  # قائمة المراجعة والتشيك (للغرف التي أخذت مبيد حشري أو إنذار أو نص نص)
  pending_checks = [
      f
      for f in db["followups"]
      if f["state"] in ["بانتظار التشيك", "بانتظار المراجعة", "مخالفة مستمرة"]
  ]
  if pending_checks:
    st.markdown("---")
    st.markdown(
        f"##### 🔍 المراجعة والتشيك الميداني ({len(pending_checks)}):"
    )
    for f_idx, f_item in enumerate(reversed(pending_checks)):
      st.markdown(
          f"<div class='task-row'><b>{f_item['loc']}</b> —"
          f" {f_item['detail']}<br><small style='color:#94a3b8;'>📅 قُيّد:"
          f" {f_item['created_at']}"
          + (
              f" | آخر تشيك: {f_item['checked_at']}"
              if f_item["checked_at"]
              else ""
          )
          + "</small></div>",
          unsafe_allow_html=True,
      )
      fc1, fc2 = st.columns(2)
      if f_item["category"] == "مبيد حشرات":
        with fc1:
          if st.button(
              "✅ تم التشيك (سليم)",
              key=f"chk_pest_ok_{f_idx}_{f_item['loc']}_{f_item['created_at']}",
          ):
            f_item["state"] = "تم التشيك - سليم ✓"
            f_item["checked_at"] = now_stamp()
            st.rerun()
        with fc2:
          if st.button(
              "🔄 إعادة رش مبيد",
              key=f"chk_pest_re_{f_idx}_{f_item['loc']}_{f_item['created_at']}",
          ):
            f_item["checked_at"] = now_stamp()
            save_maintenance_ticket(
                f_item["loc"], "مبيد حشرات (إعادة رش)", "🔴 طارئ"
            )
            st.rerun()
      else:
        with fc1:
          if st.button(
              "🌟 تحسنت ونظيفة ✓",
              key=f"chk_imp_{f_idx}_{f_item['loc']}_{f_item['created_at']}",
          ):
            f_item["state"] = "تحسنت بعد الإنذار 🌟"
            f_item["checked_at"] = now_stamp()
            st.rerun()
        with fc2:
          if st.button(
              "🚨 مستمرة (إنذار إضافي)",
              key=f"chk_cont_{f_idx}_{f_item['loc']}_{f_item['created_at']}",
          ):
            f_item["state"] = "مخالفة مستمرة"
            f_item["count"] += 1
            f_item["checked_at"] = now_stamp()
            st.rerun()

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

    # 1. الصيانة بالتواريخ والتصنيف
    open_lines = (
        "\n".join([
            f"• {r['loc']}: {r['item']} [{r.get('severity', '🔴 طارئ')}]"
            f" (قُيّد: {r['time']})"
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
            f"• {r['loc']}: {r['item']} ✓ (قُيّد: {r['time']} | أُنجز:"
            f" {r.get('closed_time', '')})"
            for r in fixed_reps
        ])
        if fixed_reps
        else "• لا يوجد"
    )

    recurring_items = [
        f"{r['loc']} ({r['item']} ×{r['repeat_count']})"
        for r in db["repairs"]
        if r.get("repeat_count", 1) > 1
    ]
    recurring_summary = (
        "، ".join(dict.fromkeys(recurring_items)) if recurring_items else "لا يوجد"
    )

    # 2. حصر مبيد الحشرات والمراجعة بالتاريخ
    pest_records = [f for f in db["followups"] if f["category"] == "مبيد حشرات"]
    pest_rooms_unique = len(set(f["loc"] for f in pest_records))
    pest_lines = (
        "\n".join([
            f"• {f['loc']}: الرش ({f['created_at']}) — الحالة: {f['state']}"
            + (f" (تشيك: {f['checked_at']})" if f["checked_at"] else "")
            for f in pest_records
        ])
        if pest_records
        else "• لا يوجد"
    )

    # 3. الإنذارات، التحسن، والغرف النظيفة المميزة بالتاريخ
    warn_records = [
        f
        for f in db["followups"]
        if f["category"] in ["إنذار", "متابعة نظافة"]
        and "تحسنت" not in f["state"]
    ]
    improved_records = [
        f for f in db["followups"] if "تحسنت" in f["state"]
    ]
    exemplary_records = [
        f for f in db["followups"] if f["category"] == "غرفة نظيفة"
    ]

    warn_lines = (
        "\n".join([
            f"• {f['loc']}: {f['detail']} (تكرار {f['count']}) — قُيّد:"
            f" {f['created_at']}"
            + (f" | مراجعة: {f['checked_at']}" if f["checked_at"] else "")
            for f in warn_records
        ])
        if warn_records
        else "• لا يوجد"
    )

    improved_lines = (
        "\n".join([
            f"• {f['loc']}: تحسنت بعد ({f['detail']}) — إنذار:"
            f" {f['created_at']} | تشيك: {f['checked_at']}"
            for f in improved_records
        ])
        if improved_records
        else "• لا يوجد"
    )

    exemplary_lines = (
        "\n".join([
            f"• {f['loc']}: نظيفة ومميزة 🌟 ({f['created_at']})"
            for f in exemplary_records
        ])
        if exemplary_records
        else "• لا يوجد"
    )

    clean_report = f"""*{LOCATION_TAG}*
*المشرف: {SUPERVISOR_NAME}*

*🛠️ الصيانة:*
قيد التنفيذ ({len(open_reps)}):
{open_lines}
تم الإصلاح ({len(fixed_reps)}):
{fixed_lines}
• المتكرر: {recurring_summary}

*🪲 مبيد الحشرات (المستلمين: {pest_rooms_unique} غرف):*
{pest_lines}

*⚠️ الإنذارات والمتابعة ({len(warn_records)}):*
{warn_lines}

*🌟 غرف تحسنت بعد الإنذار ({len(improved_records)}):*
{improved_lines}

*✨ غرف نظيفة ومميزة للتقدير ({len(exemplary_records)}):*
{exemplary_lines}"""

    st.text_area("نص التقرير الجاهز:", value=clean_report, height=270)

    wa_rep_url = (
        f"https://api.whatsapp.com/send?text={urllib.parse.quote(clean_report)}"
    )
    st.markdown(
        f'<a href="{wa_rep_url}" target="_blank" class="wa-btn">📲 مشاركة'
        " التقرير عبر واتساب</a>",
        unsafe_allow_html=True,
    )

    dl_c1, dl_c2 = st.columns(2)
    with dl_c1:
      st.download_button(
          "📥 إكسل الصيانة CSV",
          data=pd.DataFrame(db["repairs"]).to_csv(index=False).encode("utf-8-sig"),
          file_name="Maintenance.csv",
          mime="text/csv",
          use_container_width=True,
      )
    with dl_c2:
      st.download_button(
          "📥 إكسل المتابعة CSV",
          data=pd.DataFrame(db["followups"]).to_csv(index=False).encode("utf-8-sig"),
          file_name="Followups_History.csv",
          mime="text/csv",
          use_container_width=True,
      )

    st.markdown("---")

    if st.button(
        "🌅 بدء يوم جديد (مع حفظ سجل التكرار والمراجعة)", key="btn_new_day"
    ):
      db["repairs"] = [r for r in db["repairs"] if r["status"] == "مفتوح"]
      db["followups"] = [
          f
          for f in db["followups"]
          if f["state"]
          in ["بانتظار التشيك", "بانتظار المراجعة", "مخالفة مستمرة"]
      ]
      for k in ["last_maint_action", "last_viol_action"]:
        if k in st.session_state:
          del st.session_state[k]
      st.success(
          "✅ تم تصفير تقرير اليوم والاحتفاظ بالغرف التي تنتظر المراجعة والتكرار!"
      )
      st.rerun()

    if st.button("🗑️ مسح شامل لكل السجلات من الصفر", key="btn_wipe_all"):
      db["repairs"].clear()
      db["followups"].clear()
      db["room_history"].clear()
      for k in ["last_maint_action", "last_viol_action"]:
        if k in st.session_state:
          del st.session_state[k]
      st.success("✅ تم مسح جميع السجلات بالكامل.")
      st.rerun()
  elif pin_in:
    st.error("⛔ رمز الدخول غير صحيح.")
