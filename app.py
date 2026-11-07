from datetime import datetime
import hmac
import urllib.parse
import pandas as pd
import streamlit as st

# استدعاء مكتبة Supabase
try:
  from supabase import Client, create_client

  HAS_SUPABASE_LIB = True
except ImportError:
  HAS_SUPABASE_LIB = False

# ==============================================================================
# 1. إعداد الصفحة والواجهة للجوال الميداني
# ==============================================================================
st.set_page_config(
    page_title="إدارة سكن جامعة 3 | العمليات وعقود التشغيل",
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
    max-width: 440px !important; 
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
.badge-admin {
    display: inline-block;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: var(--primary);
    padding: 2px 8px;
    border-radius: 16px;
    font-size: 0.72em;
    font-weight: 800;
}
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
.stat-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 6px;
}
.wa-btn-primary {
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
.wa-btn-danger {
    display: block;
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.6);
    color: #fca5a5 !important;
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    font-weight: 900;
    text-decoration: none !important;
    margin-top: 6px;
    margin-bottom: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. الثوابت العامة وإعداد الربط السحابي (Supabase Client)
# ==============================================================================
LOCATION_TAG = "سكن جامعة 3"
MOTTO = "إصرار"
PERMANENT_PIN = str(st.secrets.get("SUPERVISOR_PIN", "5050")).strip()

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

supabase_client = None
if HAS_SUPABASE_LIB and SUPABASE_URL and SUPABASE_KEY:
  try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
  except Exception:
    supabase_client = None

# أرقام التواصل الافتراضية لعقود التشغيل والإدارة
if "phone_maintenance" not in st.session_state:
  st.session_state["phone_maintenance"] = "966500000000"  # مقاول النظافة والصيانة
if "phone_catering" not in st.session_state:
  st.session_state["phone_catering"] = "966500000000"  # متعهد الإعاشة
if "phone_management" not in st.session_state:
  st.session_state["phone_management"] = "966500000000"  # إدارة السكن / HR

if "is_supervisor" not in st.session_state:
  st.session_state["is_supervisor"] = False

# ==============================================================================
# 3. دوال التخزين المزدوج (Supabase السحابية + Fallback محلي)
# ==============================================================================
if "local_violations" not in st.session_state:
  st.session_state["local_violations"] = [
      {
          "room": "108",
          "viol_type": "سخان ⚡",
          "reason": "استخدام هيتر كهربائي للطبخ داخل الغرفة",
          "recurrence_count": 1,
          "logged_at": "2026-11-05 09:15 م",
      },
      {
          "room": "108",
          "viol_type": "سخان ⚡",
          "reason": "تكرار تشغيل هيتر مخالف (خطر حريق مباشر)",
          "recurrence_count": 2,
          "logged_at": "2026-11-07 10:30 م",
      },
  ]

if "local_maintenance" not in st.session_state:
  st.session_state["local_maintenance"] = [
      {
          "room": "104",
          "item": "مكيف",
          "category": "صيانة",
          "opened_at": "2026-11-06 09:30 ص",
          "closed_at": None,
          "status": "مفتوح",
      },
      {
          "room": "104",
          "item": "شطاف",
          "category": "صيانة",
          "opened_at": "2026-11-07 08:30 م",
          "closed_at": None,
          "status": "مفتوح",
      },
  ]

if "local_meals" not in st.session_state:
  st.session_state["local_meals"] = []

if "local_rounds" not in st.session_state:
  st.session_state["local_rounds"] = []


def db_insert_violation(room, v_type, reason, count, date_str):
  data = {
      "room": room,
      "viol_type": v_type,
      "reason": reason,
      "recurrence_count": count,
      "logged_at": date_str,
      "supervisor": "إداري السكن",
  }
  if supabase_client:
    try:
      supabase_client.table("housing_violations").insert(data).execute()
    except Exception:
      pass
  st.session_state["local_violations"].append(data)


def db_insert_maintenance(room, item, category, opened_at):
  data = {
      "room": room,
      "item": item,
      "category": category,
      "opened_at": opened_at,
      "closed_at": None,
      "status": "مفتوح",
      "supervisor": "إداري السكن",
  }
  if supabase_client:
    try:
      supabase_client.table("housing_maintenance").insert(data).execute()
    except Exception:
      pass
  st.session_state["local_maintenance"].append(data)


def db_insert_meal(delivered, coupons, surplus, distributed, no_coupon):
  data = {
      "meal_date": datetime.now().strftime("%Y-%m-%d"),
      "meal_time": datetime.now().strftime("%I:%M %p"),
      "delivered": int(delivered),
      "coupons": int(coupons),
      "surplus": int(surplus),
      "distributed": int(distributed),
      "no_coupon": int(no_coupon),
      "supervisor": "إداري السكن",
  }
  if supabase_client:
    try:
      supabase_client.table("housing_meals").insert(data).execute()
    except Exception:
      pass
  st.session_state["local_meals"].append(data)


def db_insert_round(round_name, observations):
  data = {
      "round_date": datetime.now().strftime("%Y-%m-%d"),
      "round_time": datetime.now().strftime("%I:%M %p"),
      "round_name": round_name,
      "observations": observations,
      "supervisor": "إداري السكن",
  }
  if supabase_client:
    try:
      supabase_client.table("housing_rounds").insert(data).execute()
    except Exception:
      pass
  st.session_state["local_rounds"].append(data)


# ==============================================================================
# 4. الترويسة الميدانية الرسمية
# ==============================================================================
status_cloud = (
    "🟢 سحابي (Supabase متصل)"
    if supabase_client
    else "🟡 محلي (الجلسة نشطة)"
)
st.markdown(
    f"""
<div class="top-card">
    <div class="headline">🏢 إدارة وتشغيل {LOCATION_TAG}</div>
    <div class="sub-headline">الرقابة على عقود التشغيل • السلامة والنظافة</div>
    <span class="badge-admin">شعار: {MOTTO}</span> • <small style="color:#94a3b8;">{status_cloud}</small>
</div>
""",
    unsafe_allow_html=True,
)

tab_viol, tab_repairs, tab_letters, tab_meals, tab_rounds, tab_vault = st.tabs([
    "⚠️ السخانات والنظافة",
    "🛠️ الصيانة والنظافة",
    "✉️ خطابات العقود",
    "🍽️ حصر الإعاشة",
    "🚶 الجولات",
    "🔐 الخزنة والتقرير",
])

# ------------------------------------------------------------------------------
# 1. تبويب المخالفات: حصر السخانات، النظافة، الطبخ غير النظامي، وتكرار الغرفة
# ------------------------------------------------------------------------------
with tab_viol:
  st.markdown("##### ⚠️ رصد مخالفات السخانات والنظافة داخل الغرف:")

  with st.form("viol_input_form", clear_on_submit=True):
    v_room = st.text_input("رقم الغرفة:", placeholder="مثال: 104")

    v_category = st.radio(
        "نوع المخالفة الرقابية:",
        [
            "سخان / طبخ مخالف ⚡",
            "نظافة الغرفة وإهمال صحي 🗑️",
            "كلاهما (سخان + نظافة) ⚠️",
            "أخرى 📝",
        ],
        horizontal=True,
    )

    custom_v = ""
    if "أخرى" in v_category:
      custom_v = st.text_input(
          "حدد المخالفة الأخرى:", placeholder="مثال: تدخين / أثاث..."
      )

    v_reason = st.text_input(
        "سبب ورصد المخالفة بدقة (خطر حريق / تراكم نفايات):",
        placeholder="مثال: استخدام سخان كهربائي للطبخ على الموكيت مباشرة...",
    )

    btn_save_viol = st.form_submit_button("⚡ حفظ المخالفة وحساب التكرار فوراً")

    if btn_save_viol:
      clean_room = v_room.strip()
      final_viol_name = (
          custom_v.strip()
          if ("أخرى" in v_category and custom_v.strip())
          else v_category
      )

      if not clean_room:
        st.error("الرجاء كتابة رقم الغرفة أولاً.")
      else:
        # حساب التكرار لنفس الغرفة ونوع المخالفة
        past_count = sum(
            1
            for x in st.session_state["local_violations"]
            if x["room"] == clean_room and x["viol_type"] == final_viol_name
        )
        cur_count = past_count + 1
        time_logged = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        db_insert_violation(
            clean_room,
            final_viol_name,
            (
                v_reason.strip()
                if v_reason.strip()
                else "رصد مخالفة اشتراطات السكن"
            ),
            cur_count,
            time_logged,
        )
        st.success(
            f"تم توثيق المخالفة على غرفة {clean_room} ({final_viol_name}) —"
            f" للمرة الـ ({cur_count})!"
        )

  st.markdown("---")
  st.markdown("##### 📋 كشف سوابق المخالفات المرصودة بالغرف:")
  if st.session_state["local_violations"]:
    for v_item in reversed(st.session_state["local_violations"][-4:]):
      c_num = v_item.get("recurrence_count", 1)
      badge_cls = "alert-tag" if c_num >= 2 else "badge-admin"
      st.markdown(
          f"""
                <div class="stat-box" style="border-right: 3px solid #ef4444;">
                    <b>غرفة {v_item['room']}</b> — <span style="color:#f87171; font-weight:800;">{v_item['viol_type']}</span>
                    <span class='{badge_cls}'>المرة الـ {c_num}</span><br>
                    <small style="color:#cbd5e1;">السبب والرصد: {v_item['reason']}</small><br>
                    <small style="color:#94a3b8;">التاريخ: {v_item['logged_at']}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )
  else:
    st.info("لا توجد مخالفات مسجلة بالسكن.")

# ------------------------------------------------------------------------------
# 2. تبويب الصيانة والنظافة: إلزام مقاول النظافة والصيانة مع توثيق الإصلاح
# ------------------------------------------------------------------------------
with tab_repairs:
  st.markdown("##### 🛠️ بلاغ أعطال وتقصير لشركة النظافة والصيانة:")

  with st.form("maint_input_form", clear_on_submit=True):
    r_room = st.text_input("رقم الغرفة / المرفق:", placeholder="مثال: 204")
    r_item = st.radio(
        "البلاغ المحدد:",
        ["مكيف ❄️", "شطاف 🚿", "تقصير نظافة ممرات/حمامات 🗑️", "أخرى 🛠️"],
        horizontal=True,
    )

    custom_item_name = ""
    if "أخرى" in r_item:
      custom_item_name = st.text_input(
          "اكتب العطل الآخر:", placeholder="مثال: فيش محروق / سخان الحمام..."
      )

    btn_save_maint = st.form_submit_button("⚡ إدراج البلاغ في جدول المقاول")

    if btn_save_maint:
      clean_r = r_room.strip()
      final_item = (
          custom_item_name.strip()
          if ("أخرى" in r_item and custom_item_name.strip())
          else r_item
      )
      category_val = (
          "نظافة" if "تقصير نظافة" in final_item else "صيانة وتشغيل"
      )

      if not clean_r:
        st.error("الرجاء تحديد رقم الغرفة أو الموقع.")
      else:
        db_insert_maintenance(
            clean_r,
            final_item,
            category_val,
            datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        )
        st.success(f"تم إدراج بلاغ {clean_r} ({final_item}) في قائمة المتابعة.")

  st.markdown("---")
  st.markdown("##### 📋 البلاغات المعلقة على مقاول الصيانة والنظافة:")

  open_maint = [
      x for x in st.session_state["local_maintenance"] if x["status"] == "مفتوح"
  ]
  if open_maint:
    df_m = pd.DataFrame(open_maint)
    room_repeats = df_m["room"].value_counts()
    wa_maint_summary = [
        f"*تقرير إشعار مقاول النظافة والصيانة - {LOCATION_TAG}:*"
    ]

    for idx, row in enumerate(open_maint):
      r_id = row["room"]
      reps = room_repeats.get(r_id, 1)
      rep_tag = (
          f"<span class='alert-tag'>⚠️ متكرر {reps} مرات</span>"
          if reps >= 2
          else ""
      )

      st.markdown(
          f"""
                <div class="stat-box">
                    <b>غرفة {row['room']}</b> — <span style="color:var(--primary); font-weight:800;">{row['item']}</span> {rep_tag}<br>
                    <small style="color:#94a3b8;">وقت وتاريخ البلاغ: {row['opened_at']}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )
      wa_maint_summary.append(
          f"• غرفة {row['room']}: {row['item']} (مسجل بتاريخ:"
          f" {row['opened_at']})"
      )

      if st.button(
          f"✅ تم الإنجاز والإصلاح لغرفة {row['room']} ({row['item']})",
          key=f"m_fix_{idx}",
      ):
        row["status"] = "تم الإصلاح"
        row["closed_at"] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        st.success(f"تم توثيق تاريخ ووقت الإنجاز: {row['closed_at']}")
        st.rerun()

    enc_maint_text = urllib.parse.quote("\n".join(wa_maint_summary))
    wa_url = f"https://wa.me/{st.session_state['phone_maintenance']}?text={enc_maint_text}"
    st.markdown(
        f'<a href="{wa_url}" target="_blank" class="wa-btn-primary">📲 إرسال'
        " البلاغات لمقاول الصيانة والنظافة عبر واتساب</a>",
        unsafe_allow_html=True,
    )
  else:
    st.info("لا توجد بلاغات معلقة على المقاول حالياً.")

# ------------------------------------------------------------------------------
# تبويب 3: مُوَلّد الخطابات الرسمية وفق عقود التشغيل (إرسال بضغطة زر)
# ------------------------------------------------------------------------------
with tab_letters:
  st.markdown("##### ✉️ مذكرات وخطابات عقود التشغيل المؤتمتة:")

  dest_choice = st.selectbox(
      "حدد الجهة الموجه لها الخطاب:",
      [
          "1. مذكرة أمن وسلامة عاجلة للإدارة / HR (مخالفات السخانات والطبخ)",
          "2. خطاب رسمي لمقاول النظافة والصيانة (أعطال المكيفات وتأخر الإصلاح)",
          "3. إشعار مطابقة استحقاق لشركة الإعاشة (حصر الوارد والفائض)",
      ],
  )

  now_time_full = datetime.now().strftime("%Y-%m-%d | %I:%M %p")

  if "مخالفات السخانات" in dest_choice:
    heater_viols = [
        v
        for v in st.session_state["local_violations"]
        if "سخان" in v["viol_type"]
    ]
    heater_text = (
        "\n".join([
            f"- غرفة {v['room']}: ({v['viol_type']}) - السبب: {v['reason']} -"
            f" للمرة الـ ({v['recurrence_count']}) - رُصدت: {v['logged_at']}"
            for v in heater_viols[-5:]
        ])
        if heater_viols
        else "- لا توجد مخالفات سخانات مسجلة حديثاً."
    )

    letter_body = f"""السادة / إدارة الموارد البشرية وشؤون الموظفين المحترمين
عناية مدير السكن - لمن يهمه الأمر،،

السلام عليكم ورحمة الله وبركاته،،

الموضوع: إشعار خطر حريق جسيم ومذكرة مخالفات سخانات وهيترات - {LOCATION_TAG}

نفيدكم بأنه ومن خلال المتابعة الميدانية الدورية المنفذة بتاريخ ({now_time_full})، تم ضبط غرف تقوم باستخدام سخانات مياه وهيترات كهربائية لأغراض الطبخ وتسخين الطعام داخل الغرف السكنية بشكل عشوائي، مما يشكل خطراً مباشراً على سلامة القاطنين وخطر اندلاع حرائق كهربائية لا قدر الله، وبيانها كالتالي:

{heater_text}

وحيث إن هذه الممارسات تعد خرقاً صريحاً لاشتراطات الدفاع المدني ولائحة السكن المعتمدة، نرفع لسعادتكم هذه المذكرة لإخلاء مسؤوليتنا الرقابية والمطالبة باتخاذ الإجراءات التأديبية والخصم المباشر ومصادرة الأجهزة المخالفة فوراً.

وتقبلوا خالص التحية والتقدير،،
إداري السكن - {LOCATION_TAG}"""
    target_wa = (
        f"https://wa.me/{st.session_state['phone_management']}?text={urllib.parse.quote(letter_body)}"
    )
    btn_label = "📲 إرسال مذكرة السخانات فوراً لإدارة الموارد البشرية عبر واتساب"

  elif "مقاول النظافة والصيانة" in dest_choice:
    open_ac = [
        x
        for x in st.session_state["local_maintenance"]
        if x["status"] == "مفتوح"
    ]
    ac_text = (
        "\n".join([
            f"- موقع/غرفة {x['room']}: بلاغ ({x['item']}) - تاريخ البلاغ:"
            f" {x['opened_at']}"
            for x in open_ac
        ])
        if open_ac
        else "- كافة البلاغات معالجة ومنجزة."
    )

    letter_body = f"""السادة / شركة النظافة والصيانة المعتمدة المحترمين
عناية مدير المشروع - لمن يهمه الأمر،،

السلام عليكم ورحمة الله وبركاته،،

الموضوع: إنذار تقصير تشغيلي ومطالبة بإصلاح عاجل - عقد صيانة ونظافة {LOCATION_TAG}

إشارة إلى عقد التشغيل والصيانة والنظافة المبرم معكم، وإلى الجولة الرقابية المنفذة بتاريخ ({now_time_full})، نفيدكم بوجود تدنٍ في الاستجابة للأعطال وملاحظات النظافة القائمة المبينة أدناه:

{ac_text}

نلزمكم بموجب بنود العقد بسرعة توجيه الفنيين وفرق النظافة لإغلاق هذه البلاغات وتوثيق تاريخ ووقت الإنجاز الفعلي خلال 24 ساعة لتفادي تطبيق غرامات التقصير التعاقدية.

وتقبلوا وافر الاحترام،،
إداري السكن والرقابة التشغيلية - {LOCATION_TAG}"""
    target_wa = (
        f"https://wa.me/{st.session_state['phone_maintenance']}?text={urllib.parse.quote(letter_body)}"
    )
    btn_label = (
        "📲 إرسال خطاب التقصير فوراً لمقاول النظافة والصيانة عبر واتساب"
    )

  else:
    last_m = (
        st.session_state["local_meals"][-1]
        if st.session_state["local_meals"]
        else {"delivered": 0, "coupons": 0, "surplus": 0}
    )
    letter_body = f"""السادة / متعهد شركة الإعاشة المحترمين
عناية مسؤول التوريد - لمن يهمه الأمر،،

السلام عليكم ورحمة الله وبركاته،،

الموضوع: محضر مطابقة استلام وتوزيع وجبات - {LOCATION_TAG}
التاريخ: {now_time_full}

نفيدكم بمطابقة استلام الوجبات الموردة من قبلكم ومقارنتها بالكوبونات المستلمة:
- إجمالي الوجبات الموردة (جات): {last_m.get('delivered', 0)} وجبة.
- إجمالي الوجبات المصروفة بموجب كوبون رسمي: {last_m.get('coupons', 0)} وجبة.
- الفائض المتبقي بالصواني: {last_m.get('surplus', 0)} وجبة.

نحيطكم علماً بأن المطابقة والاعتماد المالي للفواتير يتم استناداً لهذه الكوبونات والفائض الموثق رسمياً.

وتقبلوا تحياتنا،،
إداري السكن - {LOCATION_TAG}"""
    target_wa = (
        f"https://wa.me/{st.session_state['phone_catering']}?text={urllib.parse.quote(letter_body)}"
    )
    btn_label = "📲 إرسال محضر المطابقة فوراً لمتعهد الإعاشة عبر واتساب"

  st.text_area(
      "نص الخطاب الرسمي المولد (جاهز للمعاينة):",
      value=letter_body,
      height=220,
  )
  st.markdown(
      f'<a href="{target_wa}" target="_blank" class="wa-btn-primary">{btn_label}</a>',
      unsafe_allow_html=True,
  )

  # خانة تعديل أرقام العقود الثلاثة
  with st.expander("⚙️ أرقام الواتساب لعقود التشغيل والإدارة"):
    st.caption("حدث الأرقام مرة واحدة فقط لترتبط بالأزرار مباشرة:")
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
      np_m = st.text_input(
          "مقاول النظافة والصيانة:",
          value=st.session_state["phone_maintenance"],
      )
    with c_p2:
      np_c = st.text_input(
          "متعهد الإعاشة:", value=st.session_state["phone_catering"]
      )
    with c_p3:
      np_a = st.text_input(
          "إدارة السكن / HR:", value=st.session_state["phone_management"]
      )

    if st.button("حفظ وتثبيت الأرقام في الجلسة"):
      st.session_state["phone_maintenance"] = np_m.strip()
      st.session_state["phone_catering"] = np_c.strip()
      st.session_state["phone_management"] = np_a.strip()
      st.success("تم تحديث أرقام التواصل بنجاح!")
      st.rerun()

# ------------------------------------------------------------------------------
# 4. تبويب حصر الإعاشة (جات / كوبون / فائض)
# ------------------------------------------------------------------------------
with tab_meals:
  st.markdown("##### 🍽️ مطابقة وجبة الإعاشة اليومية:")

  with st.form("catering_form", clear_on_submit=False):
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
      d_qty = st.number_input(
          "جات (الوارد):", min_value=0, max_value=600, value=77
      )
    with col_c2:
      c_qty = st.number_input(
          "كوبون:", min_value=0, max_value=600, value=42
      )
    with col_c3:
      s_qty = st.number_input(
          "فائض بالصواني:", min_value=0, max_value=600, value=0
      )

    btn_meal = st.form_submit_button("⚡ حفظ المطابقة السحابية")

    dist_qty = max(0, d_qty - s_qty)
    leak_qty = max(0, dist_qty - c_qty)

    if btn_meal:
      db_insert_meal(d_qty, c_qty, s_qty, dist_qty, leak_qty)
      st.success("تم حفظ محضر الوجبة سحابياً بنجاح!")

  st.markdown("---")
  mc1, mc2 = st.columns(2)
  mc1.metric("الموزع فعلياً", f"{dist_qty} وجبة")
  mc2.metric(
      "الصرف بدون كوبون",
      f"{leak_qty} وجبة",
      delta=f"{leak_qty}" if leak_qty > 0 else "0",
      delta_color="inverse",
  )

# ------------------------------------------------------------------------------
# 5. تبويب الجولات الميدانية (صباح 09:30 ص / ليل 08:30 م)
# ------------------------------------------------------------------------------
with tab_rounds:
  st.markdown("##### 🚶 توثيق الجولات الرقابية على السكن:")

  curr_h = datetime.now().hour
  idx_round = 0 if curr_h < 14 else 1

  with st.form("round_log", clear_on_submit=True):
    sel_round = st.radio(
        "الجولة الرقابية:",
        ["جولة الصباح (09:30 ص)", "جولة الليل (08:30 م)"],
        index=idx_round,
        horizontal=True,
    )
    r_obs = st.text_input(
        "ملاحظات التفتيش على النظافة والسخانات:",
        placeholder="مثال: تم ضبط سخان بغرفة 108 / نظافة الممرات مقبولة...",
    )
    btn_round = st.form_submit_button("⚡ اعتماد الجولة وتخزينها")

    if btn_round:
      final_obs = (
          r_obs.strip()
          if r_obs.strip()
          else "تمت الجولة والسكن هادئ وتحت السيطرة"
      )
      db_insert_round(sel_round, final_obs)
      st.success(f"تم توثيق {sel_round} بنجاح!")

  if st.session_state["local_rounds"]:
    st.markdown("---")
    for r in st.session_state["local_rounds"][-2:]:
      st.markdown(
          f"""
                <div class="stat-box">
                    <b>{r['round_name']}</b> — <small style="color:var(--primary);">{r.get('round_time', '')}</small><br>
                    <small style="color:#cbd5e1;">الملاحظة: {r.get('observations', '')}</small>
                </div>
                """,
          unsafe_allow_html=True,
      )

# ------------------------------------------------------------------------------
# 6. تبويب الخزنة المشفرة وتصدير تقارير Excel المعتمدة (PIN: 5050)
# ------------------------------------------------------------------------------
with tab_vault:
  st.markdown("##### 🔐 الخزنة الرقمية لإداري السكن:")

  if not st.session_state["is_supervisor"]:
    pin_in = st.text_input("أدخل رمز المشرف:", type="password")
    if st.button("🔓 فتح الخزنة", use_container_width=True):
      if hmac.compare_digest(pin_in.strip().encode(), PERMANENT_PIN.encode()):
        st.session_state["is_supervisor"] = True
        st.rerun()
      else:
        st.error("رمز المشرف غير صحيح.")
  else:
    st.success("🟢 الخزنة مؤمنة ومفتوحة بصلاحية إداري السكن.")
    if st.button("🔒 قفل الخزنة"):
      st.session_state["is_supervisor"] = False
      st.rerun()

    st.divider()
    st.markdown("###### 📝 اعتماد التوقيع للتقارير المرفوعة للإدارة:")
    col_u1, col_u2 = st.columns(2)
    with col_u1:
      name_supervisor = st.text_input(
          "اسم إداري السكن:", placeholder="اكتب اسمك..."
      )
    with col_u2:
      name_manager = st.text_input(
          "اسم مدير السكن / المرجع الإداري:", placeholder="اكتب اسم المدير..."
      )

    last_obs_text = (
        st.session_state["local_rounds"][-1]["observations"]
        if st.session_state["local_rounds"]
        else "الوضع الرقابي بالسكن منضبط"
    )
    adm_note = st.text_area("توصية إداري السكن الميدانية:", value=last_obs_text)

    s_tag = (
        name_supervisor.strip() if name_supervisor.strip() else "إداري السكن"
    )
    m_tag = name_manager.strip() if name_manager.strip() else "مدير السكن"

    st.divider()
    st.markdown("###### 📥 سحب تقارير Excel المعتمدة والمحفوظة:")

    # 1. كشف مخالفات السخانات والنظافة
    if st.session_state["local_violations"]:
      df_viol_exp = pd.DataFrame(st.session_state["local_violations"])
      df_viol_exp["إداري_السكن"] = s_tag
      df_viol_exp["المدير"] = m_tag
      df_viol_exp["ملاحظة_الإدارة"] = adm_note
      st.download_button(
          label="تحميل تقرير مخالفات السخانات والنظافة (Excel)",
          data=df_viol_exp.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Heaters_Cleanliness_Violations_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    # 2. كشف الصيانة والنظافة لمقاول التشغيل
    if st.session_state["local_maintenance"]:
      df_maint_exp = pd.DataFrame(st.session_state["local_maintenance"])
      df_maint_exp["إداري_السكن"] = s_tag
      df_maint_exp["المدير"] = m_tag
      df_maint_exp["ملاحظة_الإدارة"] = adm_note
      st.download_button(
          label="تحميل سجل بلاغات وإنجاز مقاول الصيانة (Excel)",
          data=df_maint_exp.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Contractor_Maintenance_Log_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    # 3. كشف مطابقة الإعاشة
    if st.session_state["local_meals"]:
      df_meals_exp = pd.DataFrame(st.session_state["local_meals"])
      df_meals_exp["إداري_السكن"] = s_tag
      df_meals_exp["المدير"] = m_tag
      df_meals_exp["ملاحظة_الإدارة"] = adm_note
      st.download_button(
          label="تحميل محضر مطابقة الإعاشة (Excel)",
          data=df_meals_exp.to_csv(index=False).encode("utf-8-sig"),
          file_name=f"Catering_Reconciliation_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )
