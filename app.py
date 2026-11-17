from datetime import datetime, timedelta, timezone
import hmac
import math
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. ضبط توقيت السعودية الموحد من السيرفر (جدة UTC+3) وإعداد الواجهة
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
now_ksa = datetime.now(KSA_TZ)
now_str = now_ksa.strftime("%Y-%m-%d | %I:%M %p")
now_minutes = now_ksa.hour * 60 + now_ksa.minute
is_friday = now_ksa.weekday() == 4

st.set_page_config(
    page_title="سكن جامعة 3 | منظومة NFC الذكية",
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
    max-width: 430px !important; 
    padding-top: 0.6rem !important; 
    padding-bottom: 2.2rem !important; 
    margin: 0 auto !important;
}
html, body, [class*="css"] {
    direction: rtl; 
    text-align: right;
    background-color: #090d16 !important; 
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif;
}
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    height: 64px !important; 
    font-size: 1.08em !important; 
    font-weight: 900 !important;
    border-radius: 14px !important; 
    width: 100% !important; 
    margin-bottom: 6px !important;
    background: #1e293b !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(16, 185, 129, 0.4) !important;
}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--primary) !important;
    color: #022c22 !important;
}
.header-card { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 14px; 
    padding: 12px; 
    margin-bottom: 10px; 
    text-align: center; 
}
.headline { font-size: 1.15em; font-weight: 900; color: #ffffff; margin: 0; }
.sub-headline { font-size: 0.8em; font-weight: 700; color: #94a3b8; margin-top: 3px; }
.receipt-box {
    background: rgba(16, 185, 129, 0.16); 
    border: 2px solid #10b981;
    border-radius: 16px; 
    padding: 24px 16px; 
    text-align: center; 
    margin-top: 20px;
}
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 8px;
}
.sla-green {
    background: rgba(16, 185, 129, 0.18);
    border: 1.5px solid #10b981;
    color: #6ee7b7;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.sla-yellow {
    background: rgba(245, 158, 11, 0.18);
    border: 1.5px solid #f59e0b;
    color: #fcd34d;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.sla-red {
    background: rgba(239, 68, 68, 0.22);
    border: 1.5px solid #ef4444;
    color: #fca5a5;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.wa-btn {
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 14px;
    border-radius: 12px;
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
# 2. الذاكرة المشتركة على السيرفر (@st.cache_resource) لربط جوالات العمال بجوال المشرف
# ==============================================================================
@st.cache_resource
def get_central_vault():
  return {
      "ticket_seq": 102,
      "morning_round_note": (
          "تم التفتيش الصباحي، الممرات نظيفة، والوضع العام منضبط"
      ),
      "maintenance_db": [
          {
              "id": 101,
              "location": "السطح والخزانات",
              "item": "تهريب مياه / سباكة",
              "priority": "🔴 حرج",
              "desc": "صنبور الخط الرئيسي مكسور ويبق موية",
              "time": "10:15 ص",
              "date": now_ksa.strftime("%Y-%m-%d"),
              "status": "مفتوح",
              "closed_at": None,
          },
          {
              "id": 102,
              "location": "غرفة 104",
              "item": "عطل مكيف (AC)",
              "priority": "🔴 حرج",
              "desc": "تنقيط ماء وتجمع أوساخ تحت الوحدة",
              "time": "09:30 ص",
              "date": now_ksa.strftime("%Y-%m-%d"),
              "status": "مفتوح",
              "closed_at": None,
          },
      ],
      "violations_db": [
          {
              "location": "غرفة 108",
              "type": "سخان / هيتر طبخ",
              "desc": "تشغيل هيتر طبخ على الأرض (خطر حريق)",
              "count": 2,
              "time": "09:15 م",
              "date": now_ksa.strftime("%Y-%m-%d"),
          }
      ],
      "meals_db": [],
  }


vault = get_central_vault()

# ==============================================================================
# 3. الثوابت الأمنية وقراءة معاملات الرابط من شريحة الـ NFC
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
SUPERVISOR_WA = "966566261868"
SECRET_NFC_KEY = "s3x9"
ADMIN_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

LOC_NAMES = {
    "reception": "الاستقبال / غرفة",
    "roof": "السطح والخزانات",
    "floor1": "الدور الأول",
    "floor2": "الدور الثاني",
    "floor3": "الدور الثالث",
    "floor4": "الدور الرابع",
    "catering": "نقطة الإعاشة",
}

MEAL_SPECS = {
    "فطور": {
        "target_mins": 330,
        "official_str": "05:30 ص",
        "def_h": 5,
        "def_m": 30,
        "def_ampm": 0,
    },
    "غداء": {
        "target_mins": 690,
        "official_str": "11:30 ص",
        "def_h": 11,
        "def_m": 30,
        "def_ampm": 0,
    },
    "عشاء": {
        "target_mins": 1050,
        "official_str": "05:30 م",
        "def_h": 5,
        "def_m": 30,
        "def_ampm": 1,
    },
}

params = st.query_params
mode = params.get("mode", "admin")
loc_code = params.get("loc", params.get("cp", ""))
token = params.get("k", "")


def save_instant_ticket(
    location_txt: str,
    issue_txt: str,
    priority: str,
    desc_txt: str = "بلاغ فوري عبر شريحة NFC",
):
  t_now = datetime.now(KSA_TZ)
  vault["ticket_seq"] += 1
  t_id = vault["ticket_seq"]
  time_formatted = t_now.strftime("%I:%M %p")
  date_formatted = t_now.strftime("%Y-%m-%d")

  if loc_code != "catering":
    vault["maintenance_db"].append({
        "id": t_id,
        "location": location_txt,
        "item": issue_txt,
        "priority": priority,
        "desc": desc_txt,
        "time": time_formatted,
        "date": date_formatted,
        "status": "مفتوح",
        "closed_at": None,
    })
  else:
    vault["last_catering_nfc_time"] = time_formatted

  st.session_state["worker_done_id"] = t_id
  st.session_state["worker_done_loc"] = location_txt
  st.session_state["worker_done_issue"] = issue_txt
  st.session_state["worker_done_time"] = time_formatted


# ==============================================================================
# المسار 1: بوابة العمال العمياء (NFC -> نقرة واحدة -> إغلاق وخصوصية تامة)
# الرابط: ?mode=worker&loc=roof&k=s3x9
# ==============================================================================
if mode == "worker":
  if not hmac.compare_digest(token.strip().encode(), SECRET_NFC_KEY.encode()):
    st.error(
        "⛔ وصول غير مصرح به. يرجى مسح ملصق الـ NFC المعتمد داخل المبنى."
    )
    st.stop()

  loc_label = LOC_NAMES.get(loc_code, "مرفق عام")
  st.markdown(
      f"""
        <div class="header-card">
            <div class="headline">⚡ {LOCATION_TAG} — {loc_label}</div>
            <div class="sub-headline">لمسة واحدة للإرسال الفوري • One-Tap Report • فوری رپورٹ</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  if "worker_done_id" in st.session_state:
    w_wa_text = (
        f"🚨 *بلاغ شريحة NFC فوري - {LOCATION_TAG}*\n"
        f"🔢 *رقم الإيصال:* #{st.session_state['worker_done_id']}\n"
        f"📍 *الموقع:* {st.session_state['worker_done_loc']}\n"
        f"🔧 *البلاغ:* {st.session_state['worker_done_issue']}\n"
        f"⏰ *توقيت جدة:* {st.session_state['worker_done_time']}"
    )
    enc_w_wa = urllib.parse.quote(w_wa_text)

    st.markdown(
        f"""
            <div class="receipt-box">
                <div style="font-size:2.8em;">✅</div>
                <h2 style="color:#6ee7b7; margin:6px 0;">تم استلام البلاغ بنجاح</h2>
                <p style="font-size:1.05em; margin-bottom:8px;">
                    رقم الإيصال: <b>#{st.session_state['worker_done_id']}</b><br>
                    الموقع: <b>{st.session_state['worker_done_loc']}</b><br>
                    البلاغ: <b>{st.session_state['worker_done_issue']}</b><br>
                    الوقت: <b>{st.session_state['worker_done_time']}</b>
                </p>
                <small style="color:#94a3b8;">
                    Received Successfully • شکایت موصول ہوگئی ہے<br>
                    🔒 تم إغلاق الشاشة لحماية الخصوصية ومنع التكرار
                </small>
            </div>
            <a href="https://wa.me/{SUPERVISOR_WA}?text={enc_w_wa}" target="_blank" class="wa-btn">
                📲 تأكيد فوري لواتساب المشرف | واٹس ایپ | WhatsApp
            </a>
            """,
        unsafe_allow_html=True,
    )
    st.stop()

  room_suffix = ""
  if loc_code == "reception":
    r_num = st.text_input(
        "1️⃣ رقم الغرفة / Room No / کمرہ نمبر:", placeholder="مثال: 213"
    )
    room_suffix = f" ({r_num.strip()})" if r_num.strip() else " (بدون رقم)"

  if loc_code == "catering":
    if st.button("🍱 وصول وجبة الإعاشة الآن | Meal Arrived | کھانا آ گیا"):
      auto_meal = (
          "فطور"
          if now_minutes < 570
          else ("غداء" if now_minutes < 990 else "عشاء")
      )
      m_spec = MEAL_SPECS[auto_meal]
      delay_m = now_minutes - m_spec["target_mins"]
      arr_str = (
          now_ksa.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
      )
      if delay_m <= 0:
        sla_tag = f"🟢 منضبط عبر NFC (وصل {arr_str})"
      elif delay_m <= 15:
        sla_tag = f"🟡 متأخر {delay_m} د عبر NFC (وصل {arr_str})"
      else:
        sla_tag = f"🔴 تأخير حرج {delay_m} د عبر NFC (وصل {arr_str})"

      vault["meals_db"].append({
          "meal": auto_meal,
          "date": now_ksa.strftime("%Y-%m-%d"),
          "official_time": m_spec["official_str"],
          "arrival_time": arr_str,
          "delay_mins": max(0, int(delay_m)),
          "sla_status": sla_tag,
          "sla_report_tag": sla_tag,
          "delivered": 77,
          "coupons": 42,
          "surplus": 0,
          "distributed": 77,
          "no_coupon": 35,
          "recommended": 80,
          "note": "تم إثبات الوصول بلمسة NFC",
      })
      save_instant_ticket("نقطة الإعاشة", f"وصول وجبة ({auto_meal})", "🟢 توثيق")
      st.rerun()
  else:
    if st.button("❄️ عطل مكيف | AC Issue | اے سی خراب"):
      save_instant_ticket(
          f"{loc_label}{room_suffix}", "عطل مكيف (AC)", "🔴 حرج"
      )
      st.rerun()

    if st.button("🚰 تهريب مياه / سباكة | Water Leak | پانی لیکج"):
      save_instant_ticket(
          f"{loc_label}{room_suffix}", "تهريب مياه / سباكة", "🔴 حرج"
      )
      st.rerun()

    if st.button("⚡ كهرباء / سخان | Power/Heater | بجلی/ہیٹر"):
      save_instant_ticket(
          f"{loc_label}{room_suffix}", "كهرباء / سخان", "🔴 حرج"
      )
      st.rerun()

    if st.button("🧹 تم التنظيف / طلب نظافة | Cleaning | صفائی"):
      if "الدور" in loc_label or "السطح" in loc_label:
        vault["morning_round_note"] = (
            f"[توثيق NFC - {loc_label} الساعة {now_ksa.strftime('%I:%M %p')}] تم"
            " التنظيف والتفتيش"
        )
      save_instant_ticket(
          f"{loc_label}{room_suffix}", "نظافة وممرات", "🟢 روتيني"
      )
      st.rerun()

  st.stop()

# ==============================================================================
# المسار 2: الوضع الافتراضي لمنصة مَقسوم (عند الدخول بـ ?mode=maqsoom)
# ==============================================================================
if mode == "maqsoom":
  st.markdown(
      """
        <div class="header-card">
            <div class="headline">🛍️ منصة مَقسوم | Maqsoom Deals</div>
            <div class="sub-headline">الواجهة العامة للمتجر تعمل بشكل مستقل وآمن</div>
        </div>
        """,
      unsafe_allow_html=True,
  )
  st.info(
      "هذه الواجهة العامة للزوار. للبلاغات الميدانية يرجى مسح ملصق الـ NFC"
      " المعتمد في السكن."
  )
  if st.button("🔐 الانتقال إلى غرفة عمليات المشرف"):
    st.query_params["mode"] = "admin"
    st.rerun()
  st.stop()

# ==============================================================================
# المسار 3: غرفة عمليات المشرف الخاصة (?mode=admin محمية بالرمز 5050)
# ==============================================================================
st.markdown(
    f"""
    <div class="header-card">
        <div class="headline">🔐 غرفة عمليات المشرف | {LOCATION_TAG}</div>
        <div class="sub-headline">المشرف: {SUPERVISOR_NAME} • توقيت جدة: {now_str}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "admin_auth" not in st.session_state:
  st.session_state["admin_auth"] = False

if not st.session_state["admin_auth"]:
  pin_input = st.text_input("أدخل رمز المشرف السري (5050):", type="password")
  if st.button("🔓 فتح غرفة العمليات"):
    if hmac.compare_digest(pin_input.strip().encode(), ADMIN_PIN.encode()):
      st.session_state["admin_auth"] = True
      st.rerun()
    else:
      st.error("⛔ رمز الدخول غير صحيح.")
  st.stop()

open_tickets = [x for x in vault["maintenance_db"] if x["status"] == "مفتوح"]
c_m1, c_m2 = st.columns([2.2, 1])
c_m1.metric("بلاغات NFC والصيانة المفتوحة", f"{len(open_tickets)} بلاغ")
with c_m2:
  if st.button("🔄 تحديث"):
    st.rerun()

tab_maint, tab_meals, tab_report = st.tabs([
    "🛠️ 1. البلاغات والمخالفات",
    "🍽️ 2. الأكل وساعة الوصول",
    "📲 3. الواتساب والخزنة",
])

# ------------------------------------------------------------------------------
# التبويب 1: إدارة بلاغات الـ NFC الواردة + إضافة يدوية + المخالفات
# ------------------------------------------------------------------------------
with tab_maint:
  st.markdown("##### 📡 البلاغات الحية الواردة من شرائح الـ NFC والميدان:")
  if open_tickets:
    for idx, item in enumerate(reversed(open_tickets)):
      col_info, col_action = st.columns([2.6, 1.4])
      with col_info:
        st.markdown(
            f"<div class='stat-box'><b>#{item['id']} | {item['location']}</b>"
            f" — {item['priority']}<br><span style='color:#10b981;"
            f" font-weight:800;'>{item['item']}</span><br><small"
            f" style='color:#94a3b8;'>{item['desc']} • ⏰"
            f" {item['time']}</small></div>",
            unsafe_allow_html=True,
        )
      with col_action:
        if st.button("تم إصلاحه ✓", key=f"close_t_{item['id']}_{idx}"):
          item["status"] = "تم الإصلاح"
          item["closed_at"] = now_ksa.strftime("%I:%M %p")
          st.rerun()
  else:
    st.success("✅ جميع البلاغات مغلقة والمرافق سليمة 100%.")

  with st.expander("➕ تسجيل بلاغ صيانة أو مخالفة يدوياً", expanded=False):
    with st.form("admin_manual_form", clear_on_submit=True):
      entry_kind = st.radio(
          "نوع القيد:",
          ["عطل صيانة 🛠️", "مخالفة سخان / نظافة ⚠️"],
          horizontal=True,
      )
      loc_in = st.text_input(
          "الموقع أو رقم الغرفة:", placeholder="مثال: السطح أو 108"
      )
      desc_in = st.text_input(
          "التفاصيل:", placeholder="صنبور يبق موية / تشغيل هيتر طبخ..."
      )
      if st.form_submit_button("⚡ حفظ في السجل"):
        if loc_in.strip():
          f_loc = (
              f"غرفة {loc_in.strip()}"
              if loc_in.strip().isdigit()
              else loc_in.strip()
          )
          if "صيانة" in entry_kind:
            save_instant_ticket(
                f_loc,
                "بلاغ مشرف ميداني",
                "🔴 حرج",
                desc_in.strip() or "رصد مباشر",
            )
          else:
            rep_c = (
                sum(1 for v in vault["violations_db"] if v["location"] == f_loc)
                + 1
            )
            vault["violations_db"].append({
                "location": f_loc,
                "type": "مخالفة سخان / نظافة",
                "desc": desc_in.strip() or "مخالفة تعليمات السكن",
                "count": rep_c,
                "time": now_ksa.strftime("%I:%M %p"),
                "date": now_ksa.strftime("%Y-%m-%d"),
            })
          st.success("تم التوثيق بنجاح!")
          st.rerun()

# ------------------------------------------------------------------------------
# التبويب 2: الأكل وموعد وصوله (ساعة الجوال ص/م + ألوان التأخير)
# ------------------------------------------------------------------------------
with tab_meals:
  default_m_idx = 0 if now_minutes < 570 else (1 if now_minutes < 990 else 2)
  m_choice = st.selectbox(
      "🍲 الوجبة:", ["فطور", "غداء", "عشاء"], index=default_m_idx
  )
  spec = MEAL_SPECS[m_choice]

  st.markdown(
      f"##### ⏰ موعد وصول ({m_choice}) — الموعد الرسمي: {spec['official_str']}"
  )
  if "last_catering_nfc_time" in vault:
    st.info(
        "📡 آخر مسح لشريحة طاولة الإعاشة تم الساعة:"
        f" **{vault['last_catering_nfc_time']}**"
    )

  hours_list = list(range(1, 13))
  mins_list = list(range(0, 60))

  t_col1, t_col2, t_col3 = st.columns([1.2, 1.2, 1.6])
  with t_col1:
    arr_hour = st.selectbox(
        "الساعة:",
        hours_list,
        index=hours_list.index(spec["def_h"]),
        key=f"h_{m_choice}",
    )
  with t_col2:
    arr_min = st.selectbox(
        "الدقيقة:",
        mins_list,
        index=mins_list.index(spec["def_m"]),
        format_func=lambda x: f"{x:02d}",
        key=f"m_{m_choice}",
    )
  with t_col3:
    arr_ampm = st.radio(
        "الفترة:",
        ["ص 🌅", "م 🌙"],
        index=spec["def_ampm"],
        key=f"ampm_{m_choice}",
    )

  is_pm = "م" in arr_ampm
  hour_24 = (
      (0 if arr_hour == 12 else arr_hour)
      if not is_pm
      else (12 if arr_hour == 12 else arr_hour + 12)
  )
  short_ampm = "م" if is_pm else "ص"

  arrival_total_mins = hour_24 * 60 + arr_min
  arrival_formatted = f"{arr_hour:02d}:{arr_min:02d} {short_ampm}"
  delay_minutes = arrival_total_mins - spec["target_mins"]

  if delay_minutes <= 0:
    sla_box_class = "sla-green"
    sla_title = "🟢 وصل في الموعد (التزام ممتاز)"
    sla_report_tag = f"🟢 منضبط (وصل {arrival_formatted})"
  elif 1 <= delay_minutes <= 15:
    sla_box_class = "sla-yellow"
    sla_title = f"🟡 تأخير جزئي ({delay_minutes} دقيقة) - تنبيه للمتعهد"
    sla_report_tag = (
        f"🟡 متأخر {delay_minutes} دقيقة (وصل {arrival_formatted} بدل"
        f" {spec['official_str']})"
    )
  else:
    sla_box_class = "sla-red"
    sla_title = f"🔴 تأخير حرج ({delay_minutes} دقيقة) - يرفع للإدارة"
    sla_report_tag = (
        f"🔴 تأخير حرج {delay_minutes} دقيقة (وصل {arrival_formatted} بدل"
        f" {spec['official_str']})"
    )

  st.markdown(
      f'<div class="{sla_box_class}"><b>{sla_title}</b></div>',
      unsafe_allow_html=True,
  )

  c1, c2, c3 = st.columns(3)
  with c1:
    d_in = st.number_input("المستلم (جات):", min_value=0, max_value=600, value=77)
  with c2:
    c_in = st.number_input("بكوبون:", min_value=0, max_value=600, value=42)
  with c3:
    s_in = st.number_input("الفائض بالصواني:", min_value=0, max_value=600, value=0)

  actual_used = max(0, d_in - s_in)
  next_order_rec = actual_used + (
      math.ceil(actual_used * 0.03) if actual_used > 0 else 0
  )

  if st.button("⚡ اعتماد حصر الوجبة وموعد وصولها"):
    vault["meals_db"].append({
        "meal": m_choice,
        "date": now_ksa.strftime("%Y-%m-%d"),
        "official_time": spec["official_str"],
        "arrival_time": arrival_formatted,
        "delay_mins": max(0, int(delay_minutes)),
        "sla_report_tag": sla_report_tag,
        "delivered": int(d_in),
        "coupons": int(c_in),
        "surplus": int(s_in),
        "distributed": int(actual_used),
        "recommended": int(next_order_rec),
    })
    st.success(f"تم توثيق وجبة {m_choice} بنجاح!")

# ------------------------------------------------------------------------------
# التبويب 3: تقرير الواتساب الشامل وتصدير الإكسل
# ------------------------------------------------------------------------------
with tab_report:
  last_m = (
      vault["meals_db"][-1]
      if vault["meals_db"]
      else {
          "meal": m_choice,
          "official_time": spec["official_str"],
          "arrival_time": arrival_formatted,
          "sla_report_tag": sla_report_tag,
          "delivered": int(d_in),
          "coupons": int(c_in),
          "surplus": int(s_in),
          "distributed": int(actual_used),
          "recommended": int(next_order_rec),
      }
  )

  open_m = [x for x in vault["maintenance_db"] if x["status"] == "مفتوح"]
  fixed_m = [x for x in vault["maintenance_db"] if x["status"] == "تم الإصلاح"]

  open_txt = (
      "\n".join([
          f"  • #{x.get('id', '')} [{x.get('priority', '')}] {x['location']}:"
          f" {x['item']} ({x['time']})"
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
          for v in vault["violations_db"][-4:]
      ])
      if vault["violations_db"]
      else "  • السجل نظيف."
  )

  wa_report = f"""*تقرير الوردية الميداني وبلاغات NFC - {LOCATION_TAG}*
*التاريخ:* {now_str} | *المشرف:* {SUPERVISOR_NAME}
-------------------------------------------
*1️⃣ التفتيش الميداني والنظافة (NFC):*
• {vault['morning_round_note']}

*2️⃣ الإعاشة وموعد التوريد [{last_m['meal']}]:*
• الموعد الرسمي: {last_m['official_time']} | الوصول الفعلي: {last_m['arrival_time']}
• حالة الموعد: {last_m['sla_report_tag']}
• الكميات: المستلم: {last_m['delivered']} | بكوبون: {last_m['coupons']} | الفائض: {last_m['surplus']}
• المستهلك الفعلي: {last_m['distributed']} شخص
💡 *التوصية للوجبة القادمة:* طلب ({last_m['recommended']} وجبة) شاملة 3% طوارئ لمنع الهدر.

*3️⃣ بلاغات الصيانة والسباكة (NFC):*
- المعلق ({len(open_m)}):
{open_txt}
- المنجز ({len(fixed_m)}):
{fixed_txt}

*4️⃣ المخالفات والسلامة:*
{viol_txt}

الوضع العام بالسكن: منضبط وتحت السيطرة.
-------------------------------------------"""

  st.text_area("معاينة التقرير:", value=wa_report, height=250)

  wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_report)}"
  st.markdown(
      f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال التقرير عبر'
      " واتساب (اختر الشخص أو القروب من جوالك)</a>",
      unsafe_allow_html=True,
  )

  st.divider()
  st.markdown("###### 📥 تنزيل كشوفات الإكسل الرسمية (CSV UTF-8):")
  st.download_button(
      "📥 تحميل سجل الصيانة وبلاغات NFC (Excel)",
      data=pd.DataFrame(vault["maintenance_db"])
      .to_csv(index=False)
      .encode("utf-8-sig"),
      file_name=f"NFC_Maintenance_{now_ksa.strftime('%Y%m%d')}.csv",
      use_container_width=True,
  )
  if vault["meals_db"]:
    st.download_button(
        "📥 تحميل سجل الإعاشة ومواعيد الوصول (Excel)",
        data=pd.DataFrame(vault["meals_db"])
        .to_csv(index=False)
        .encode("utf-8-sig"),
        file_name=f"Meals_SLA_{now_ksa.strftime('%Y%m%d')}.csv",
        use_container_width=True,
    )
