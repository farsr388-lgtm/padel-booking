from datetime import datetime, timedelta, timezone
import hmac
import json
import os
import threading
import time
import urllib.parse
import uuid
import streamlit as st

# ==============================================================================
# 1. الإعدادات وثوابت الصفقات (مَقسوم — صفقات العطور التشاركية)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
BRAND_NAME = "مَقسوم | Maqsoom"
ADMIN_PHONE = "966566261868"
ADMIN_PIN = str(st.secrets.get("ADMIN_PIN", "9900")).strip()
DATA_FILE = "maqsoom_pro.json"
HOLD_MINUTES = 15

DEALS = {
    "DERAAH-GOLD-01": {
        "short": "درعه 50%",
        "title": "باقة درعه الذهبية (خصم 50%)",
        "orig_price": 210,
        "deal_price": 105,
        "capacity": 4,
    },
    "DERAAH-VIP-02": {
        "short": "درعه VIP",
        "title": "مجموعة درعه النخبة (خصم 50%)",
        "orig_price": 300,
        "deal_price": 150,
        "capacity": 4,
    },
}

PICKUP_OPTIONS = {
    "redsea": {
        "short": "🏬 الرد سي مول",
        "full": "استلام يد بيد — الرد سي مول (جدة)",
    },
    "redbox": {
        "short": "📦 خزائن RedBox",
        "full": "توصيل ذكي — خزائن RedBox",
    },
}

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

st.set_page_config(
    page_title="مَقسوم | صفقات العطور",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "sel_deal" not in st.session_state:
  st.session_state["sel_deal"] = "DERAAH-GOLD-01"
if "sel_seat" not in st.session_state:
  st.session_state["sel_seat"] = 1
if "sel_pickup" not in st.session_state:
  st.session_state["sel_pickup"] = "redsea"
if "undo_stack" not in st.session_state:
  st.session_state["undo_stack"] = []

active_deal_id = st.session_state["sel_deal"]
active_seat_num = st.session_state["sel_seat"]
active_pickup_key = st.session_state["sel_pickup"]

# ==============================================================================
# 2. التصميم البصري المبسط (نفس فلسفة الإبهام الواحد والألوان الواضحة)
# ==============================================================================
st.markdown(
    f"""
<style>
header[data-testid="stHeader"], #MainMenu, footer {{ display: none !important; }}
div[data-testid="InputInstructions"] {{ display: none !important; }}

html, body, .stApp {{
    direction: rtl;
    text-align: right;
    background-color: #0b0f19 !important;
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Cairo", sans-serif;
    overflow-x: hidden !important;
}}

.block-container {{
    max-width: 440px !important;
    width: 100% !important;
    padding: 0.35rem 0.6rem 2rem 0.6rem !important;
    margin: 0 auto !important;
}}

div[data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    width: 100% !important;
}}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
    flex: 1 1 0% !important;
    min-width: 0 !important;
    width: auto !important;
}}

div.stButton {{ width: 100% !important; }}
div.stButton > button {{
    height: 53px !important;
    width: 100% !important;
    padding: 0 6px !important;
    font-size: 0.98em !important;
    font-weight: 900 !important;
    border-radius: 14px !important;
    margin-bottom: 4px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 2px solid rgba(255, 255, 255, 0.14) !important;
    white-space: nowrap !important;
    transition: transform 0.08s ease !important;
}}
div.stButton > button:active {{
    transform: scale(0.95) !important;
}}

/* أزرار اختيار الباقة */
div[class*="st-key-deal_"] button {{
    height: 42px !important;
    font-size: 0.92em !important;
    background: #111827 !important;
}}
div.st-key-deal_{active_deal_id} button {{
    background: #10b981 !important;
    color: #022c22 !important;
    border-color: #10b981 !important;
}}

/* أزرار المقاعد الأربعة (1 إلى 4) */
div[class*="st-key-seat_"] button {{
    height: 48px !important;
    font-size: 0.94em !important;
    background: #111827 !important;
}}
div.st-key-seat_{active_seat_num} button {{
    border: 2.5px solid #10b981 !important;
    background: rgba(16, 185, 129, 0.25) !important;
    color: #ecfdf5 !important;
}}

/* أزرار طريقة الاستلام */
div[class*="st-key-pick_"] button {{
    height: 44px !important;
    font-size: 0.9em !important;
    background: #111827 !important;
}}
div.st-key-pick_{active_pickup_key} button {{
    background: rgba(56, 189, 248, 0.22) !important;
    border-color: #38bdf8 !important;
    color: #bae6fd !important;
}}

/* زر الحجز الرئيسي */
div.st-key-btn_join_seat button {{
    height: 58px !important;
    font-size: 1.08em !important;
    background: rgba(16, 185, 129, 0.22) !important;
    border: 2px solid #10b981 !important;
    color: #6ee7b7 !important;
}}

/* أزرار التراجع وتصفير المقعد */
div.st-key-btn_undo button {{
    height: 46px !important;
    background: rgba(244, 63, 94, 0.18) !important;
    border: 1.5px solid #f43f5e !important;
    color: #fda4af !important;
    font-size: 0.93em !important;
}}
div.st-key-btn_clear_seat button {{
    height: 46px !important;
    background: rgba(148, 163, 184, 0.16) !important;
    border: 1.5px solid #94a3b8 !important;
    color: #e2e8f0 !important;
    font-size: 0.91em !important;
}}

/* أزرار الصح والخطأ في التبويب الثاني */
div[class*="st-key-pay_ok_"] button {{
    height: 50px !important;
    background: rgba(16, 185, 129, 0.22) !important;
    border: 2px solid #10b981 !important;
    color: #6ee7b7 !important;
}}
div[class*="st-key-pay_no_"] button {{
    height: 50px !important;
    background: rgba(244, 63, 94, 0.18) !important;
    border: 2px solid rgba(244, 63, 94, 0.6) !important;
    color: #fda4af !important;
}}

input[type="text"] {{
    font-size: 16px !important;
    height: 44px !important;
    border-radius: 11px !important;
    background-color: #111827 !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}}

button[data-baseweb="tab"] {{
    flex: 1 !important;
    justify-content: center !important;
    font-weight: 900 !important;
    font-size: 0.94em !important;
}}

.top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-weight: 900;
    font-size: 0.92em;
}}

.prog-wrap {{
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 10px;
    margin: 4px 0 6px 0;
}}
.prog-head {{
    display: flex;
    justify-content: space-between;
    font-size: 0.82em;
    font-weight: 800;
    color: #94a3b8;
    margin-bottom: 4px;
}}
.prog-track {{
    background: #1e293b;
    height: 8px;
    border-radius: 999px;
    overflow: hidden;
}}
.prog-fill {{
    background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}}

.seat-hero {{
    background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
    border: 2px solid #10b981;
    border-radius: 15px;
    padding: 9px 10px;
    margin: 4px 0 6px 0;
    text-align: center;
}}
.seat-hero-big {{
    font-size: 1.25em;
    font-weight: 900;
    color: #ecfdf5;
}}
.seat-hero-sub {{
    font-size: 0.84em;
    color: #a7f3d0;
    margin-top: 2px;
    font-weight: 700;
}}

.shield-box {{
    background: rgba(56, 189, 248, 0.16);
    border: 1.5px solid #38bdf8;
    border-radius: 11px;
    padding: 8px;
    margin: 4px 0;
    text-align: center;
    font-weight: 900;
    font-size: 0.88em;
    color: #bae6fd;
}}
.done-banner {{
    background: rgba(16, 185, 129, 0.22);
    border: 2px solid #34d399;
    border-radius: 12px;
    padding: 9px;
    margin: 5px 0;
    text-align: center;
    font-weight: 900;
    font-size: 0.96em;
    color: #a7f3d0;
}}
.ok-card {{
    background: rgba(16, 185, 129, 0.16);
    border: 2px solid #10b981;
    border-radius: 13px;
    padding: 9px;
    margin-top: 5px;
    color: #6ee7b7;
    text-align: center;
    font-weight: 900;
    font-size: 0.94em;
}}
.task-card {{
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 10px 12px;
    margin-top: 6px;
    margin-bottom: 4px;
    font-size: 0.95em;
}}
.task-expired {{
    background: rgba(244, 63, 94, 0.15) !important;
    border: 2px solid rgba(244, 63, 94, 0.55) !important;
}}
.wa-btn {{
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 15px;
    border-radius: 14px;
    font-weight: 900;
    font-size: 1.05em;
    text-decoration: none !important;
    margin: 7px 0;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. قاعدة البيانات (JSON Persistence + Thread Lock)
# ==============================================================================
def load_db() -> dict:
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return {"bookings": [], "completed_groups": 0}


@st.cache_resource
def get_db():
  data = load_db()
  return {
      "lock": threading.Lock(),
      "bookings": data.get("bookings", []),
      "completed_groups": data.get("completed_groups", 0),
  }


db = get_db()


def save_db():
  try:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
      json.dump(
          {
              "bookings": db["bookings"],
              "completed_groups": db["completed_groups"],
          },
          f,
          ensure_ascii=False,
      )
  except Exception:
    pass


def now_str() -> str:
  return (
      datetime.now(KSA_TZ)
      .strftime("%m/%d - %I:%M %p")
      .replace("AM", "ص")
      .replace("PM", "م")
  )


def mins_remaining(created_ts: float) -> int:
  elapsed = (time.time() - created_ts) / 60.0
  return max(0, int(round(HOLD_MINUTES - elapsed)))


def wa_link(msg: str, phone: str = "") -> str:
  encoded = urllib.parse.quote(msg)
  if phone:
    return f"https://wa.me/{phone}?text={encoded}"
  return f"whatsapp://send?text={encoded}"


def get_deal_bookings(deal_id: str) -> list[dict]:
  return [b for b in db["bookings"] if b["deal_id"] == deal_id]


def get_seat_record(deal_id: str, seat_num: int) -> dict | None:
  for b in db["bookings"]:
    if b["deal_id"] == deal_id and b["seat"] == seat_num:
      return b
  return None


def get_seat_button_label(deal_id: str, seat_num: int) -> str:
  rec = get_seat_record(deal_id, seat_num)
  if not rec:
    return f"⚪ مقعد {seat_num}"
  if rec["status"] == "مدفوع ✅":
    return f"🟢 {rec['name']}"
  rem = mins_remaining(rec["ts"])
  if rem == 0:
    return f"🔴 {rec['name']}"
  return f"🟡 {rec['name']}"


def advance_to_next_empty_seat(deal_id: str, current_seat: int):
  cap = DEALS[deal_id]["capacity"]
  taken = {b["seat"] for b in get_deal_bookings(deal_id)}
  for offset in range(1, cap + 1):
    cand = ((current_seat - 1 + offset) % cap) + 1
    if cand not in taken:
      st.session_state["sel_seat"] = cand
      return


def select_deal(deal_id: str):
  st.session_state["sel_deal"] = deal_id
  st.session_state["sel_seat"] = 1
  st.session_state.pop("last_action_msg", None)


def select_seat(seat_num: int):
  st.session_state["sel_seat"] = seat_num
  st.session_state.pop("last_action_msg", None)


def select_pickup(pick_key: str):
  st.session_state["sel_pickup"] = pick_key


def push_undo(action_obj: dict):
  stack = st.session_state.setdefault("undo_stack", [])
  stack.append(action_obj)
  if len(stack) > 20:
    stack.pop(0)


# ==============================================================================
# 4. دوال الحجز، التصفير، والتراجع المتعدد (Zero-Friction)
# ==============================================================================
def join_selected_seat():
  deal_id = st.session_state["sel_deal"]
  seat_num = st.session_state["sel_seat"]
  pick_key = st.session_state["sel_pickup"]
  raw_name = st.session_state.get("buyer_name_in", "").strip()
  raw_phone = (
      st.session_state.get("buyer_phone_in", "")
      .strip()
      .translate(ARABIC_DIGITS)
  )

  buyer_name = raw_name if raw_name else f"مشارك {seat_num}"
  deal_info = DEALS[deal_id]

  with db["lock"]:
    existing = get_seat_record(deal_id, seat_num)
    if existing:
      st.session_state["last_action_msg"] = {
          "text": f"🛡️ المقعد {seat_num} محجوز مسبقاً باسم ({existing['name']})",
          "warn": True,
      }
      return

    bid = uuid.uuid4().hex[:8]
    db["bookings"].append({
        "id": bid,
        "deal_id": deal_id,
        "seat": seat_num,
        "name": buyer_name,
        "phone": raw_phone,
        "pickup_key": pick_key,
        "pickup_label": PICKUP_OPTIONS[pick_key]["full"],
        "price": deal_info["deal_price"],
        "status": "بانتظار الدفع ⏳",
        "time": now_str(),
        "ts": time.time(),
    })
    save_db()

    push_undo({
        "type": "join",
        "bid": bid,
        "deal_id": deal_id,
        "prev_seat": seat_num,
    })
    st.session_state["last_action_msg"] = {
        "text": (
            f"✅ تم حجز مقعد {seat_num} باسم ({buyer_name}) — السعر"
            f" {deal_info['deal_price']} ريال"
        ),
        "warn": False,
    }

  st.session_state["buyer_name_in"] = ""
  st.session_state["buyer_phone_in"] = ""
  advance_to_next_empty_seat(deal_id, seat_num)


def clear_selected_seat():
  deal_id = st.session_state["sel_deal"]
  seat_num = st.session_state["sel_seat"]
  with db["lock"]:
    rec = get_seat_record(deal_id, seat_num)
    if not rec:
      return
    db["bookings"] = [b for b in db["bookings"] if b["id"] != rec["id"]]
    save_db()
    push_undo({
        "type": "clear_seat",
        "record": rec,
        "deal_id": deal_id,
        "prev_seat": seat_num,
    })
    st.session_state["last_action_msg"] = {
        "text": f"🧹 تم إخلاء مقعد {seat_num} وإتاحته للجميع",
        "warn": False,
    }


def undo_last_action():
  stack = st.session_state.get("undo_stack", [])
  if not stack:
    return
  act = stack.pop()
  with db["lock"]:
    if act["type"] == "join":
      db["bookings"] = [b for b in db["bookings"] if b["id"] != act["bid"]]
    elif act["type"] == "clear_seat":
      db["bookings"].append(act["record"])
    save_db()

  st.session_state["sel_deal"] = act["deal_id"]
  st.session_state["sel_seat"] = act["prev_seat"]
  st.session_state.pop("last_action_msg", None)


# ==============================================================================
# 5. مولدات رسائل الواتساب الجاهزة (للمجموعة + للمشرف)
# ==============================================================================
def build_customer_join_wa(deal_id: str, bookings: list[dict]) -> str:
  d = DEALS[deal_id]
  rem_seats = max(0, d["capacity"] - len(bookings))
  lines = [
      f"🛍️ *حجز جديد في {BRAND_NAME}*",
      f"• الباقة: *{d['title']}*",
      (
          f"• السعر بعد الخصم: *{d['deal_price']} ريال* (بدلاً من"
          f" {d['orig_price']} ريال)"
      ),
      (
          f"• المقاعد المحجوزة: *{len(bookings)} من {d['capacity']}* (المتبقي:"
          f" {rem_seats})"
      ),
      "────────────────────",
  ]
  for b in sorted(bookings, key=lambda x: x["seat"]):
    lines.append(
        f"• مقعد {b['seat']}: *{b['name']}* — {b['pickup_label']}"
        f" ({b['status']})"
    )
  lines.append("\n⏳ فضلاً إرسال إيصال التحويل خلال 15 دقيقة لتأكيد المقعد.")
  return "\n".join(lines)


def build_group_summary_report() -> str:
  lines = [
      f"📊 *تقرير صفقات {BRAND_NAME}*",
      f"• التوقيت: {now_str()} | المجموعات المكتملة: *{db['completed_groups']}*",
      "────────────────────",
  ]
  for d_id, d_info in DEALS.items():
    d_books = sorted(get_deal_bookings(d_id), key=lambda x: x["seat"])
    paid_cnt = sum(1 for x in d_books if x["status"] == "مدفوع ✅")
    total_sar = paid_cnt * d_info["deal_price"]
    lines.append(
        f"\n*▪️ {d_info['title']} ({len(d_books)}/{d_info['capacity']}):*"
    )
    if not d_books:
      lines.append("  - لا توجد حجوزات حالياً.")
    else:
      for b in d_books:
        ph = f" | جوال: {b['phone']}" if b.get("phone") else ""
        lines.append(
            f"  - مقعد {b['seat']}: *{b['name']}*{ph} | {b['pickup_label']} |"
            f" {b['status']}"
        )
      lines.append(f"  💰 المحصّل المؤكد: *{total_sar} ريال*")
  return "\n".join(lines)


# ==============================================================================
# 6. الواجهة الموحدة (1️⃣ المقاعد، 2️⃣ تأكيد الدفع، 3️⃣ إرسال 📲)
# ==============================================================================
deal_info = DEALS[active_deal_id]
deal_bookings = get_deal_bookings(active_deal_id)
paid_count = sum(1 for b in deal_bookings if b["status"] == "مدفوع ✅")
pending_count = len(deal_bookings) - paid_count
undo_len = len(st.session_state.get("undo_stack", []))

st.markdown(
    f"""
    <div class="top-bar">
        <span>🛍️ {BRAND_NAME}</span>
        <span>✅ مؤكد: {paid_count} &nbsp;|&nbsp; ⏳ معلق: {pending_count}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "1️⃣ المقاعد",
    f"2️⃣ الدفع ({pending_count})",
    "3️⃣ إرسال 📲",
])

# --- الخطوة 1: اختيار الباقة، المقعد، والاستلام بلمسة واحدة ---
with tab1:
  d_cols = st.columns(len(DEALS))
  for idx, (d_id, d_obj) in enumerate(DEALS.items()):
    d_cols[idx].button(
        d_obj["short"],
        key=f"deal_{d_id}",
        on_click=select_deal,
        args=(d_id,),
        use_container_width=True,
    )

  cap = deal_info["capacity"]
  s_cols = st.columns(cap)
  for s_num in range(1, cap + 1):
    s_cols[s_num - 1].button(
        get_seat_button_label(active_deal_id, s_num),
        key=f"seat_{s_num}",
        on_click=select_seat,
        args=(s_num,),
        use_container_width=True,
    )

  pct = min(100, round((len(deal_bookings) / cap) * 100))
  st.markdown(
      f"""
        <div class="prog-wrap">
            <div class="prog-head">
                <span>🎯 {deal_info['title']}</span>
                <span>{len(deal_bookings)} من {cap} مقاعد</span>
            </div>
            <div class="prog-track">
                <div class="prog-fill" style="width:{pct}%;"></div>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  if len(deal_bookings) >= cap:
    st.markdown(
        '<div class="done-banner">🎉 اكتملت المجموعة (4/4)! جاهزة للشراء من'
        " درعه</div>",
        unsafe_allow_html=True,
    )

  current_seat_rec = get_seat_record(active_deal_id, active_seat_num)
  if current_seat_rec:
    rem_m = mins_remaining(current_seat_rec["ts"])
    timer_txt = (
        "مؤكد بالكامل ✅"
        if current_seat_rec["status"] == "مدفوع ✅"
        else (
            f"متبقي {rem_m} دقيقة للدفع ⏳"
            if rem_m > 0
            else "انتهت مهلة الـ 15 دقيقة 🔴"
        )
    )
    st.markdown(
        f'<div class="shield-box">🛡️ مقعد {active_seat_num} محجوز:'
        f' {current_seat_rec["name"]} ({timer_txt})</div>',
        unsafe_allow_html=True,
    )

  p_cols = st.columns(2)
  for idx, (p_key, p_val) in enumerate(PICKUP_OPTIONS.items()):
    p_cols[idx].button(
        p_val["short"],
        key=f"pick_{p_key}",
        on_click=select_pickup,
        args=(p_key,),
        use_container_width=True,
    )

  in_c1, in_c2 = st.columns(2)
  with in_c1:
    st.text_input(
        "اسم المشارك",
        placeholder="الاسم (اختياري)...",
        key="buyer_name_in",
        label_visibility="collapsed",
    )
  with in_c2:
    st.text_input(
        "رقم الجوال",
        placeholder="الجوال 05...",
        key="buyer_phone_in",
        label_visibility="collapsed",
    )

  st.button(
      f"⚡ احجز مقعد {active_seat_num} ({deal_info['deal_price']} ريال)",
      key="btn_join_seat",
      on_click=join_selected_seat,
      use_container_width=True,
  )

  st.markdown(
      f"""
        <div class="seat-hero">
            <div class="seat-hero-big">💺 مقعد {active_seat_num} — {deal_info['deal_price']} ريال</div>
            <div class="seat-hero-sub">{PICKUP_OPTIONS[active_pickup_key]['full']}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  if undo_len > 0 or current_seat_rec is not None:
    u_cols = st.columns(2 if (undo_len > 0 and current_seat_rec is not None) else 1)
    u_ptr = 0
    if undo_len > 0:
      with u_cols[u_ptr]:
        st.button(
            f"↩️ رجوع ({undo_len})",
            key="btn_undo",
            on_click=undo_last_action,
            use_container_width=True,
        )
      u_ptr += 1
    if current_seat_rec is not None:
      with u_cols[u_ptr]:
        st.button(
            "🧹 تصفير المقعد",
            key="btn_clear_seat",
            on_click=clear_selected_seat,
            use_container_width=True,
        )

  if "last_action_msg" in st.session_state:
    msg_obj = st.session_state["last_action_msg"]
    card_style = "shield-box" if msg_obj["warn"] else "ok-card"
    st.markdown(
        f'<div class="{card_style}">{msg_obj["text"]}</div>',
        unsafe_allow_html=True,
    )

  if deal_bookings:
    wa_cust = build_customer_join_wa(active_deal_id, deal_bookings)
    st.markdown(
        f'<a href="{wa_link(wa_cust, ADMIN_PHONE)}" class="wa-btn">📲 إرسال'
        " الحجز وتأكيده عبر واتساب</a>",
        unsafe_allow_html=True,
    )

# --- الخطوة 2: تأكيد الدفع أو إلغاء المقعد المنتهي (✅ / ❌) ---
with tab2:
  all_pending = [b for b in db["bookings"] if b["status"] != "مدفوع ✅"]
  if not all_pending:
    st.markdown(
        '<div class="done-banner">🏆 جميع المقاعد المحجوزة مدفوعة ومؤكدة!</div>',
        unsafe_allow_html=True,
    )
  else:
    st.markdown("##### 💳 مراجعة التحويلات (مهلة 15 دقيقة):")
    for b in all_pending:
      rem_min = mins_remaining(b["ts"])
      is_exp = rem_min == 0
      c_cls = "task-card task-expired" if is_exp else "task-card"
      t_badge = (
          "🔴 انتهت الـ 15 دقيقة!" if is_exp else f"⏳ متبقي {rem_min} دقيقة"
      )
      d_title = DEALS.get(b["deal_id"], {}).get("short", b["deal_id"])

      st.markdown(
          f"<div class='{c_cls}'><b>💺 مقعد {b['seat']} ({d_title}) —"
          f" {b['name']}</b><br><small>{b['pickup_label']} • <span"
          f" style='color:#fbbf24;'>{t_badge}</span></small></div>",
          unsafe_allow_html=True,
      )
      p_c1, p_c2 = st.columns(2)
      with p_c1:
        if st.button(
            "✅ تم الدفع", key=f"pay_ok_{b['id']}", use_container_width=True
        ):
          with db["lock"]:
            b["status"] = "مدفوع ✅"
            save_db()
          st.rerun()
      with p_c2:
        if st.button(
            "❌ إلغاء المقعد",
            key=f"pay_no_{b['id']}",
            use_container_width=True,
        ):
          with db["lock"]:
            db["bookings"] = [x for x in db["bookings"] if x["id"] != b["id"]]
            save_db()
          st.rerun()

# --- الخطوة 3: إرسال التقرير وإغلاق المجموعة المكتملة ---
with tab3:
  full_rep = build_group_summary_report()
  st.markdown(
      f'<a href="{wa_link(full_rep)}" class="wa-btn">📲 إرسال ملخص الصفقات'
      " عبر واتساب</a>",
      unsafe_allow_html=True,
  )
  with st.expander("👁️ معاينة الملخص", expanded=True):
    st.text_area(
        "الملخص:", value=full_rep, height=220, label_visibility="collapsed"
    )

  st.markdown("---")
  pin_in = st.text_input(
      "رمز الإدارة لتصفير المجموعة (9900):", type="password", key="admin_pin_in"
  )
  if hmac.compare_digest(
      pin_in.strip().encode("utf-8"), ADMIN_PIN.encode("utf-8")
  ):
    if st.button(
        "🎉 إغلاق المجموعة المكتملة وبدء مجموعة جديدة", use_container_width=True
    ):
      with db["lock"]:
        db["completed_groups"] += 1
        db["bookings"] = [
            b for b in db["bookings"] if b["deal_id"] != active_deal_id
        ]
        save_db()
      st.session_state["sel_seat"] = 1
      st.session_state["undo_stack"].clear()
      st.session_state.pop("last_action_msg", None)
      st.rerun()
