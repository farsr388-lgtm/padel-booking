from datetime import datetime, timedelta, timezone
import json
import math
import os
import threading
import time
import urllib.parse
import uuid
import streamlit as st

# ==============================================================================
# 1. الإعدادات المحاسبية والتشغيلية لمشروع «مَقسوم»
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
APP_TITLE = "مَقسوم — التجميع الذكي"
DATA_FILE = "maqsoom_pro.json"
ADMIN_PIN = "9900"
HOLD_MINUTES = 15

# إعدادات التسعير والمحاسبة (عرض 2+2 = 4 مقاعد)
BUNDLE_TOTAL_PRICE = 132.0   # إجمالي تكلفة الباقة (4 عطور)
SEATS_PER_BASKET = 4         # عدد المقاعد في السلة الواحدة
SINGLE_RETAIL_PRICE = 66.0   # السعر الفردي خارج العرض (لإبراز التوفير)
SEAT_PRICE = math.ceil(BUNDLE_TOTAL_PRICE / SEATS_PER_BASKET)  # 33 ريال للمقعد
SAVED_PER_SEAT = max(0, int(SINGLE_RETAIL_PRICE - SEAT_PRICE))
SAVED_PCT = round((SAVED_PER_SEAT / SINGLE_RETAIL_PRICE) * 100) if SINGLE_RETAIL_PRICE else 0

PICKUP_POINTS = {
    "redsea": "🛍️ الرد سي مول (استلام مباشر)",
    "redbox": "📦 خزائن RedBox (توصيل ذكي)",
}

st.set_page_config(
    page_title="مَقسوم | وفّر 50%",
    page_icon="💎",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "sel_seat" not in st.session_state:
    st.session_state["sel_seat"] = 1
if "sel_pickup" not in st.session_state:
    st.session_state["sel_pickup"] = "redsea"
if "undo_stack" not in st.session_state:
    st.session_state["undo_stack"] = []

active_seat = st.session_state["sel_seat"]
active_pickup = st.session_state["sel_pickup"]

# ==============================================================================
# 2. التصميم البصري المبسط (نفس فلسفة لمسة الإبهام الواحدة + وضوح مالي)
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
    padding: 0.4rem 0.65rem 2.2rem 0.65rem !important;
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
    height: 54px !important;
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

/* أزرار المقاعد الأربعة */
div[class*="st-key-seat_"] button {{
    height: 62px !important;
    font-size: 0.94em !important;
    border-radius: 14px !important;
    background: #111827 !important;
}}
div.st-key-seat_{active_seat} button {{
    border: 2.5px solid #10b981 !important;
    background: rgba(16, 185, 129, 0.22) !important;
    color: #ecfdf5 !important;
}}

/* أزرار نقطة الاستلام */
div[class*="st-key-pk_"] button {{
    height: 46px !important;
    font-size: 0.88em !important;
    border-radius: 12px !important;
    background: #111827 !important;
}}
div.st-key-pk_{active_pickup} button {{
    background: #0ea5e9 !important;
    color: #082f49 !important;
    border-color: #38bdf8 !important;
}}

/* زر الحجز الرئيسي */
div.st-key-btn_book_main button {{
    height: 58px !important;
    font-size: 1.08em !important;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    border: none !important;
    color: #022c22 !important;
}}

/* أزرار التراجع والتصفير */
div.st-key-btn_undo button {{
    height: 46px !important;
    background: rgba(244, 63, 94, 0.18) !important;
    border: 1.5px solid #f43f5e !important;
    color: #fda4af !important;
    font-size: 0.92em !important;
}}
div.st-key-btn_clear_seat button {{
    height: 46px !important;
    background: rgba(148, 163, 184, 0.16) !important;
    border: 1.5px solid #94a3b8 !important;
    color: #e2e8f0 !important;
    font-size: 0.92em !important;
}}

/* أزرار تأكيد الدفع والإلغاء في التبويب 2 */
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

input[type="text"], input[type="password"] {{
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

.saving-banner {{
    background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
    border: 2px solid #10b981;
    border-radius: 15px;
    padding: 10px 12px;
    margin: 4px 0 8px 0;
    text-align: center;
}}
.saving-big {{
    font-size: 1.25em;
    font-weight: 900;
    color: #ecfdf5;
}}
.saving-sub {{
    font-size: 0.85em;
    color: #6ee7b7;
    margin-top: 2px;
    font-weight: 800;
}}

.prog-wrap {{
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 11px;
    padding: 7px 10px;
    margin: 5px 0 8px 0;
}}
.prog-head {{
    display: flex;
    justify-content: space-between;
    font-size: 0.84em;
    font-weight: 800;
    color: #cbd5e1;
    margin-bottom: 5px;
}}
.prog-track {{
    background: #1e293b;
    height: 9px;
    border-radius: 999px;
    overflow: hidden;
}}
.prog-fill {{
    background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}}

.basket-done-banner {{
    background: rgba(16, 185, 129, 0.22);
    border: 2px solid #34d399;
    border-radius: 12px;
    padding: 10px;
    margin: 6px 0;
    text-align: center;
    font-weight: 900;
    font-size: 0.98em;
    color: #a7f3d0;
}}

.seat-card {{
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 10px 12px;
    margin: 6px 0 4px 0;
    font-size: 0.94em;
}}
.seat-expired {{
    background: rgba(244, 63, 94, 0.18) !important;
    border: 2px solid #f43f5e !important;
}}
.seat-paid {{
    background: rgba(16, 185, 129, 0.15) !important;
    border: 2px solid #10b981 !important;
}}

.wa-btn {{
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 14px;
    border-radius: 14px;
    font-weight: 900;
    font-size: 1.04em;
    text-decoration: none !important;
    margin: 7px 0;
}}
.ledger-box {{
    background: #111827;
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 12px;
    padding: 10px 12px;
    margin: 6px 0;
    font-size: 0.92em;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. قاعدة البيانات الدائمة ومحرك القيد المحاسبي المزدوج
# ==============================================================================
def default_seats() -> dict:
    return {
        str(i): {
            "seat_no": i,
            "status": "free",       # free | pending | paid
            "name": "",
            "phone": "",
            "pickup": "redsea",
            "booked_ts": 0.0,
            "booked_str": "",
            "paid_str": "",
            "amount": SEAT_PRICE,
        }
        for i in range(1, SEATS_PER_BASKET + 1)
    }


def load_db() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "seats" in data and len(data["seats"]) == SEATS_PER_BASKET:
                    return data
        except Exception:
            pass
    return {
        "basket_no": 1,
        "completed_baskets": 0,
        "seats": default_seats(),
        "ledger": [],
    }


@st.cache_resource
def get_db():
    data = load_db()
    return {
        "lock": threading.Lock(),
        "basket_no": data.get("basket_no", 1),
        "completed_baskets": data.get("completed_baskets", 0),
        "seats": data.get("seats", default_seats()),
        "ledger": data.get("ledger", []),
    }


db = get_db()


def save_db():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "basket_no": db["basket_no"],
                    "completed_baskets": db["completed_baskets"],
                    "seats": db["seats"],
                    "ledger": db["ledger"],
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


def wa_app_url(msg: str) -> str:
    return f"whatsapp://send?text={urllib.parse.quote(msg)}"


def remaining_seconds(booked_ts: float) -> int:
    if not booked_ts:
        return 0
    elapsed = time.time() - booked_ts
    return int((HOLD_MINUTES * 60) - elapsed)


def format_countdown(booked_ts: float) -> tuple[str, bool]:
    rem = remaining_seconds(booked_ts)
    if rem <= 0:
        return "🔴 انتهت الـ 15 دقيقة (متأخر)", True
    mins = rem // 60
    secs = rem % 60
    return f"⏳ متبقي {mins:02d}:{secs:02d} دقيقة", False


def push_undo(action_obj: dict):
    stack = st.session_state.setdefault("undo_stack", [])
    stack.append(action_obj)
    if len(stack) > 30:
        stack.pop(0)


def get_seat_button_label(seat_no: int) -> str:
    s = db["seats"][str(seat_no)]
    st_code = s["status"]
    if st_code == "paid":
        who = s["name"] or f"مقعد {seat_no}"
        return f"✅ {who}"
    if st_code == "pending":
        _, expired = format_countdown(s["booked_ts"])
        icon = "🔴" if expired else "🟡"
        who = s["name"] or f"مقعد {seat_no}"
        return f"{icon} {who}"
    return f"⚪ مقعد {seat_no}"


# ==============================================================================
# 4. دوال الحجز، الدفع، التراجع، وإغلاق السلة
# ==============================================================================
def select_seat(seat_no: int):
    st.session_state["sel_seat"] = seat_no


def select_pickup(pk_key: str):
    st.session_state["sel_pickup"] = pk_key


def book_active_seat():
    seat_no = st.session_state["sel_seat"]
    pk_key = st.session_state["sel_pickup"]
    cust_name = st.session_state.get("in_name", "").strip()
    cust_phone = st.session_state.get("in_phone", "").strip()

    with db["lock"]:
        s = db["seats"][str(seat_no)]
        if s["status"] != "free":
            st.session_state["flash_msg"] = ("warn", f"المقعد {seat_no} محجوز مسبقاً!")
            return

        prev_snapshot = dict(s)
        s["status"] = "pending"
        s["name"] = cust_name if cust_name else f"مشترك {seat_no}"
        s["phone"] = cust_phone
        s["pickup"] = pk_key
        s["booked_ts"] = time.time()
        s["booked_str"] = now_str()
        s["amount"] = SEAT_PRICE
        save_db()

        push_undo({
            "type": "book",
            "seat_no": seat_no,
            "prev": prev_snapshot,
        })
        st.session_state["flash_msg"] = (
            "ok",
            f"تم حجز المقعد {seat_no} ({s['name']}) — لديك 15 دقيقة للتحويل!",
        )

    st.session_state["in_name"] = ""
    st.session_state["in_phone"] = ""

    # الانتقال التلقائي لأول مقعد شاغر لتسهيل تجربة المستخدم
    for nxt in range(1, SEATS_PER_BASKET + 1):
        if db["seats"][str(nxt)]["status"] == "free":
            st.session_state["sel_seat"] = nxt
            break


def clear_specific_seat(seat_no: int):
    with db["lock"]:
        s = db["seats"][str(seat_no)]
        if s["status"] == "free":
            return
        prev_snapshot = dict(s)
        db["seats"][str(seat_no)] = {
            "seat_no": seat_no,
            "status": "free",
            "name": "",
            "phone": "",
            "pickup": "redsea",
            "booked_ts": 0.0,
            "booked_str": "",
            "paid_str": "",
            "amount": SEAT_PRICE,
        }
        save_db()
        push_undo({
            "type": "clear",
            "seat_no": seat_no,
            "prev": prev_snapshot,
        })
        st.session_state["flash_msg"] = ("ok", f"🧹 تم تصفير المقعد {seat_no} وإتاحته من جديد")


def undo_last_action():
    stack = st.session_state.get("undo_stack", [])
    if not stack:
        return
    act = stack.pop()
    seat_no = act["seat_no"]
    with db["lock"]:
        db["seats"][str(seat_no)] = act["prev"]
        save_db()
    st.session_state["sel_seat"] = seat_no
    st.session_state["flash_msg"] = ("ok", f"↩️ تم التراجع عن آخر حركة في المقعد {seat_no}")


def close_completed_basket():
    with db["lock"]:
        paid_total = sum(
            s["amount"] for s in db["seats"].values() if s["status"] == "paid"
        )
        net_profit = paid_total - BUNDLE_TOTAL_PRICE
        db["ledger"].append({
            "id": uuid.uuid4().hex[:6],
            "basket_no": db["basket_no"],
            "closed_at": now_str(),
            "revenue": paid_total,
            "cost": BUNDLE_TOTAL_PRICE,
            "net": net_profit,
            "members": [s["name"] for s in db["seats"].values()],
        })
        db["completed_baskets"] += 1
        db["basket_no"] += 1
        db["seats"] = default_seats()
        save_db()

    st.session_state["undo_stack"].clear()
    st.session_state["sel_seat"] = 1
    st.session_state["flash_msg"] = ("ok", "🎉 تم إغلاق السلة وترحيل القيد المحاسبي وبدء سلة جديدة!")


# ==============================================================================
# 5. الحسابات اللحظية والواجهة الرئيسية
# ==============================================================================
seats_list = [db["seats"][str(i)] for i in range(1, SEATS_PER_BASKET + 1)]
paid_seats = [s for s in seats_list if s["status"] == "paid"]
pending_seats = [s for s in seats_list if s["status"] == "pending"]
free_seats = [s for s in seats_list if s["status"] == "free"]

occupied_count = len(paid_seats) + len(pending_seats)
progress_pct = round((occupied_count / SEATS_PER_BASKET) * 100)

realized_cash = sum(s["amount"] for s in paid_seats)
pending_cash = sum(s["amount"] for s in pending_seats)
undo_len = len(st.session_state.get("undo_stack", []))

st.markdown(
    f"""
    <div class="top-bar">
        <span>💎 {APP_TITLE} (سلة #{db['basket_no']})</span>
        <span>🏆 مكتملة: {db['completed_baskets']} &nbsp;|&nbsp; 💺 متاح: {len(free_seats)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "1️⃣ احجز مقعدك",
    f"2️⃣ الدفع ({len(pending_seats)})",
    "3️⃣ المحاسبة والإدارة",
])

# --- الخطوة 1: واجهة العميل بلمسة واحدة وتحفيز الادخار ---
with tab1:
    st.markdown(
        f"""
        <div class="saving-banner">
            <div class="saving-big">سعر المقعد: {SEAT_PRICE} ريال فقط (بدلاً من {int(SINGLE_RETAIL_PRICE)} ريال)</div>
            <div class="saving-sub">💰 وفّر في محفظتك {SAVED_PER_SEAT} ريال مباشرة ({SAVED_PCT}% خصم التجميع)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # شبكة المقاعد الأربعة
    s_cols = st.columns(4)
    for idx, s_no in enumerate(range(1, SEATS_PER_BASKET + 1)):
        s_cols[idx].button(
            get_seat_button_label(s_no),
            key=f"seat_{s_no}",
            on_click=select_seat,
            args=(s_no,),
            use_container_width=True,
        )

    # شريط اكتمال السلة (تحفيز نفسي لإغلاق المجموعة)
    rem_txt = (
        "🔥 اكتملت السلة! بانتظار تأكيد الدفع"
        if len(free_seats) == 0
        else f"⚡ باقي {len(free_seats)} مقعد وتُغلق السلة!"
    )
    st.markdown(
        f"""
        <div class="prog-wrap">
            <div class="prog-head">
                <span>{rem_txt}</span>
                <span>{occupied_count} من {SEATS_PER_BASKET}</span>
            </div>
            <div class="prog-track">
                <div class="prog-fill" style="width:{progress_pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if occupied_count == SEATS_PER_BASKET:
        st.markdown(
            f'<div class="basket-done-banner">🎉 السلة #{db["basket_no"]} ممتلئة (4/4) — إجمالي توفير المجموعة: {SAVED_PER_SEAT * 4} ريال!</div>',
            unsafe_allow_html=True,
        )

    # اختيار نقطة الاستلام بلمسة واحدة
    pk_cols = st.columns(2)
    pk_cols[0].button("🛍️ الرد سي مول", key="pk_redsea", on_click=select_pickup, args=("redsea",), use_container_width=True)
    pk_cols[1].button("📦 خزائن RedBox", key="pk_redbox", on_click=select_pickup, args=("redbox",), use_container_width=True)

    # حقول اختيارية خفيفة لتقليل الاحتكاك
    in_c1, in_c2 = st.columns(2)
    with in_c1:
        st.text_input("الاسم (اختياري)", placeholder="اسمك أو لقبك...", key="in_name", label_visibility="collapsed")
    with in_c2:
        st.text_input("الجوال (اختياري)", placeholder="05xxxxxxxx", key="in_phone", label_visibility="collapsed")

    cur_seat_obj = db["seats"][str(active_seat)]
    if cur_seat_obj["status"] == "free":
        st.button(
            f"✅ احجز المقعد {active_seat} الآن ({SEAT_PRICE} ريال)",
            key="btn_book_main",
            on_click=book_active_seat,
            use_container_width=True,
        )
    else:
        st_label = "مدفوع ومؤكد ✅" if cur_seat_obj["status"] == "paid" else "محجوز بانتظار التحويل ⏳"
        st.markdown(
            f'<div class="seat-card"><b>مقعد {active_seat}:</b> {cur_seat_obj["name"]} — {st_label} ({PICKUP_POINTS[cur_seat_obj["pickup"]]})</div>',
            unsafe_allow_html=True,
        )

    # أزرار السلامة: التراجع المتعدد + تصفير المقعد المحدد
    if undo_len > 0 or cur_seat_obj["status"] != "free":
        c_cols = st.columns(2 if (undo_len > 0 and cur_seat_obj["status"] != "free") else 1)
        ptr = 0
        if undo_len > 0:
            with c_cols[ptr]:
                st.button(f"↩️ رجوع ({undo_len})", key="btn_undo", on_click=undo_last_action, use_container_width=True)
            ptr += 1
        if cur_seat_obj["status"] != "free":
            with c_cols[ptr]:
                st.button(f"🧹 تصفير مقعد {active_seat}", key="btn_clear_seat", on_click=clear_specific_seat, args=(active_seat,), use_container_width=True)

    if "flash_msg" in st.session_state:
        f_type, f_txt = st.session_state.pop("flash_msg")
        card_style = "seat-paid" if f_type == "ok" else "seat-expired"
        st.markdown(f'<div class="seat-card {card_style}">{f_txt}</div>', unsafe_allow_html=True)

    # زر إرسال رابط السلة أو إيصال التحويل عبر واتساب
    share_msg = (
        f"💎 عرض مَقسوم (سلة #{db['basket_no']})\n"
        f"سعر المقعد: {SEAT_PRICE} ريال بدل {int(SINGLE_RETAIL_PRICE)} ريال (توفير {SAVED_PCT}%)\n"
        f"المقاعد المتاحة حالياً: {len(free_seats)} من {SEATS_PER_BASKET}\n"
        f"احجز مقعدك الآن قبل إغلاق السلة!"
    )
    st.markdown(
        f'<a href="{wa_app_url(share_msg)}" class="wa-btn">📲 مشاركة السلة / إرسال الإيصال واتساب</a>',
        unsafe_allow_html=True,
    )

# --- الخطوة 2: إدارة المتأخرين والعداد التنازلي (15 دقيقة) ---
with tab2:
    if not pending_seats and not paid_seats:
        st.markdown('<div class="seat-card">لا توجد حجوزات نشطة في السلة الحالية بعد.</div>', unsafe_allow_html=True)

    if pending_seats:
        st.markdown("##### ⏳ حجوزات بانتظار تأكيد التحويل (مهلة 15 دقيقة)")
        for s in pending_seats:
            cd_txt, is_exp = format_countdown(s["booked_ts"])
            cls_name = "seat-card seat-expired" if is_exp else "seat-card"
            st.markdown(
                f"<div class='{cls_name}'>"
                f"<b>💺 مقعد {s['seat_no']} — {s['name']}</b> ({s['amount']} ريال)<br>"
                f"<small>{PICKUP_POINTS[s['pickup']]} | {cd_txt}</small>"
                f"</div>",
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✅ تم الدفع", key=f"pay_ok_{s['seat_no']}", use_container_width=True):
                    with db["lock"]:
                        s["status"] = "paid"
                        s["paid_str"] = now_str()
                        save_db()
                    st.rerun()
            with b2:
                if st.button("❌ إلغاء المقعد", key=f"pay_no_{s['seat_no']}", use_container_width=True):
                    clear_specific_seat(s["seat_no"])
                    st.rerun()

    if paid_seats:
        st.markdown("---")
        st.markdown("##### ✅ مقاعد مؤكدة الدفع")
        for s in paid_seats:
            st.markdown(
                f"<div class='seat-card seat-paid'>"
                f"<b>✅ مقعد {s['seat_no']} — {s['name']}</b> ({s['amount']} ريال)<br>"
                f"<small>{PICKUP_POINTS[s['pickup']]} | تأكد الدفع: {s['paid_str']}</small>"
                f"</div>",
                unsafe_allow_html=True,
            )

# --- الخطوة 3: القيد المحاسبي ولوحة الإدارة (PIN: 9900) ---
with tab3:
    st.markdown(
        f"""
        <div class="ledger-box">
            <b>📊 الموقف المحاسبي للسلة الحالية (#{db['basket_no']}):</b><br>
            • الكاش المحقق الفعلي: <b>{realized_cash} ريال</b> ({len(paid_seats)}/{SEATS_PER_BASKET})<br>
            • إيراد معلّق (قيد الانتظار): <b>{pending_cash} ريال</b> ({len(pending_seats)} مقاعد)<br>
            • تكلفة شراء الباقة كاملة: <b>{int(BUNDLE_TOTAL_PRICE)} ريال</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pin_in = st.text_input("رمز الإدارة (9900)", type="password", placeholder="أدخل رمز الإدارة لإغلاق السلة...")
    if pin_in == ADMIN_PIN:
        if len(paid_seats) == SEATS_PER_BASKET:
            st.button(
                f"🔒 إغلاق السلة #{db['basket_no']} (4/4) وبدء جولة جديدة",
                key="btn_close_basket",
                on_click=close_completed_basket,
                use_container_width=True,
            )
        else:
            st.warning(f"لا يمكن إغلاق السلة محاسبياً قبل تحصيل كامل المقاعد ({len(paid_seats)}/{SEATS_PER_BASKET} مدفوع).")

        if db["ledger"]:
            st.markdown("##### 📒 سجل السلات المغلقة (دفتر الأستاذ)")
            for entry in reversed(db["ledger"][-10:]):
                st.markdown(
                    f"<div class='seat-card'>"
                    f"<b>سلة #{entry['basket_no']}</b> — {entry['closed_at']}<br>"
                    f"<small>التحصيل: {entry['revenue']} ريال | التكلفة: {int(entry['cost'])} ريال | الصافي: {entry['net']} ريال</small>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
