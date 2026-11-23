from datetime import datetime, timedelta, timezone
import json
import os
import threading
import time
import urllib.parse
import uuid
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. الإعدادات وخريطة السكن (M2 = 16 غرفة | باقي الأدوار = 19 غرفة)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
DATA_FILE = "sakan_u3_pro.json"
MAX_RECORDS = 150
CHECK_CYCLE_DAYS = 3

FLOORS = {
    "1": {"short": "M2", "name": "الدور M2", "count": 16},
    "2": {"short": "M", "name": "الدور M", "count": 19},
    "3": {"short": "د1", "name": "الدور الأول", "count": 19},
    "4": {"short": "د2", "name": "الدور الثاني", "count": 19},
    "5": {"short": "د3", "name": "الدور الثالث", "count": 19},
    "6": {"short": "د4", "name": "الدور الرابع", "count": 19},
}

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

st.set_page_config(
    page_title="سكن جامعة 3",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "sel_floor" not in st.session_state:
    st.session_state["sel_floor"] = "1"
if "sel_room" not in st.session_state:
    st.session_state["sel_room"] = "101"

active_flr = st.session_state["sel_floor"]
active_rm = st.session_state["sel_room"]

# ==============================================================================
# 2. التصميم النظيف للجوال (من اليمين لليسار + أزرار كاملة العرض)
# ==============================================================================
st.markdown(
    f"""
<style>
header[data-testid="stHeader"], #MainMenu, footer, iframe[height="0"] {{ display: none !important; }}
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
    gap: 5px !important;
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
    height: 49px !important;
    width: 100% !important;
    padding: 0 2px !important;
    font-size: 0.94em !important;
    font-weight: 800 !important;
    border-radius: 13px !important;
    margin-bottom: 3px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(255, 255, 255, 0.13) !important;
    white-space: nowrap !important;
}}
div.stButton > button:active {{
    transform: scale(0.97) !important;
}}

/* شريط الأدوار الستة */
div[class*="st-key-flr_"] button {{
    height: 39px !important;
    font-size: 0.87em !important;
    border-radius: 10px !important;
    background: #111827 !important;
}}
div.st-key-flr_{active_flr} button {{
    background: #10b981 !important;
    color: #022c22 !important;
    border-color: #10b981 !important;
    font-weight: 900 !important;
}}

/* شبكة الغرف */
div[class*="st-key-rm_"] button {{
    height: 38px !important;
    font-size: 0.85em !important;
    border-radius: 10px !important;
    background: #111827 !important;
}}
div.st-key-rm_{active_rm} button {{
    border: 2px solid #10b981 !important;
    background: rgba(16, 185, 129, 0.22) !important;
    color: #ecfdf5 !important;
    font-weight: 900 !important;
}}

/* زر الغرفة النظيفة في الأعلى مباشرة تحت الشبكة */
div.st-key-b_star button {{
    height: 45px !important;
    margin-top: 3px !important;
    margin-bottom: 4px !important;
    background: rgba(16, 185, 129, 0.16) !important;
    border-color: #10b981 !important;
    color: #6ee7b7 !important;
    font-size: 0.98em !important;
}}

/* أزرار المخالفات (حفظ صامت + مراجعة 3 أيام) */
div.st-key-b_heater button, div.st-key-b_clean button, div.st-key-b_both button {{
    background: rgba(245, 158, 11, 0.13) !important;
    border-color: rgba(251, 191, 36, 0.45) !important;
}}

/* زر طلب الدواء (واتساب مباشر + تشيك نظافة بعد 3 أيام) */
div.st-key-b_pest button {{
    background: rgba(168, 85, 247, 0.15) !important;
    border-color: rgba(192, 132, 252, 0.5) !important;
}}

/* أزرار الصيانة (واتساب مباشر) */
div.st-key-m_ac button, div.st-key-m_leak button,
div.st-key-m_elec button, div.st-key-m_add button {{
    height: 43px !important;
    font-size: 0.85em !important;
    background: rgba(14, 165, 233, 0.12) !important;
    border-color: rgba(56, 189, 248, 0.4) !important;
}}

input[type="text"] {{
    font-size: 16px !important;
    height: 43px !important;
    border-radius: 11px !important;
    background-color: #111827 !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}}

button[data-baseweb="tab"] {{
    flex: 1 !important;
    justify-content: center !important;
    font-weight: 800 !important;
    font-size: 0.9em !important;
}}

.top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 7px 11px;
    margin-bottom: 6px;
    font-weight: 800;
    font-size: 0.88em;
}}
.active-banner {{
    background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 8px 10px;
    margin: 4px 0 6px 0;
    text-align: center;
    font-weight: 900;
    font-size: 1.03em;
    color: #ecfdf5;
}}
.sec-lbl {{
    font-size: 0.8em;
    color: #94a3b8;
    font-weight: 800;
    margin: 6px 0 3px 0;
}}
.ok-card {{
    background: rgba(16, 185, 129, 0.14);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 8px;
    margin-top: 6px;
    color: #6ee7b7;
    text-align: center;
    font-weight: 800;
    font-size: 0.9em;
}}
.task-card {{
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 11px;
    padding: 9px 10px;
    margin-bottom: 5px;
    font-size: 0.9em;
}}
.task-due {{
    background: rgba(245, 158, 11, 0.14) !important;
    border: 1.5px solid #f59e0b !important;
}}
.wa-btn {{
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 1.02em;
    text-decoration: none !important;
    margin: 6px 0;
}}
.wa-btn-fast {{
    display: block;
    background: #0ea5e9 !important;
    color: #082f49 !important;
    text-align: center;
    padding: 13px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 1.02em;
    text-decoration: none !important;
    margin: 6px 0;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. قاعدة البيانات والروابط المباشرة لتطبيق واتساب
# ==============================================================================
def load_db() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"repairs": [], "followups": [], "history": {}}


@st.cache_resource
def get_db():
    data = load_db()
    return {
        "lock": threading.Lock(),
        "repairs": data.get("repairs", []),
        "followups": data.get("followups", []),
        "history": data.get("history", {}),
    }


db = get_db()


def save_db():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "repairs": db["repairs"],
                    "followups": db["followups"],
                    "history": db["history"],
                },
                f,
                ensure_ascii=False,
            )
    except Exception:
        pass


def wa_app_url(msg: str) -> str:
    return f"whatsapp://send?text={urllib.parse.quote(msg)}"


def now_str() -> str:
    return (
        datetime.now(KSA_TZ)
        .strftime("%m/%d - %I:%M %p")
        .replace("AM", "ص")
        .replace("PM", "م")
    )


def days_since(ts_epoch: float) -> int:
    if not ts_epoch:
        return 0
    return int((time.time() - ts_epoch) // 86400)


def format_room(raw: str) -> str:
    clean = str(raw).strip().translate(ARABIC_DIGITS)
    digits = "".join(filter(str.isdigit, clean))
    if len(digits) >= 3 and digits[0] in FLOORS:
        return f"غرفة {digits} ({FLOORS[digits[0]]['name']})"
    return f"غرفة {digits}" if digits else clean


def short_room(raw: str) -> str:
    clean = str(raw).strip().translate(ARABIC_DIGITS)
    digits = "".join(filter(str.isdigit, clean))
    return digits if digits else clean


def get_room_label(room_num: str) -> str:
    loc = format_room(room_num)
    for f in reversed(db["followups"]):
        if f["loc"] == loc:
            if f.get("escalated"):
                return f"🚨 {room_num}"
            if f["cat"] == "نظيفة":
                return f"🟢 {room_num}"
            if f["cat"] == "مبيد":
                return f"🟣 {room_num}"
            return f"🟠 {room_num}"
    for r in reversed(db["repairs"]):
        if r["loc"] == loc and r["status"] == "مفتوح":
            return f"🔵 {room_num}"
    return room_num


def advance_to_next_room(current_room: str):
    digits = "".join(filter(str.isdigit, str(current_room)))
    if len(digits) >= 3 and digits[0] in FLOORS:
        f_code = digits[0]
        r_idx = int(digits[1:])
        max_r = FLOORS[f_code]["count"]
        if r_idx < max_r:
            st.session_state["sel_room"] = str(int(f_code) * 100 + r_idx + 1)


def select_floor(f_code: str):
    st.session_state["sel_floor"] = f_code
    st.session_state["sel_room"] = f"{f_code}01"


def select_room(room_num: str):
    st.session_state["sel_room"] = room_num


def set_custom_location():
    val = st.session_state.get("custom_loc_in", "").strip()
    if val:
        st.session_state["sel_room"] = val
        st.session_state["custom_loc_in"] = ""


# ==============================================================================
# 4. دوال التسجيل (واتساب فوري للمبيد والصيانة فقط + دورة 3 أيام للمبيد والمخالفات)
# ==============================================================================
def record_daily(cat: str, label: str):
    raw_room = st.session_state.get("sel_room", "").strip()
    if not raw_room:
        return

    loc = format_room(raw_room)
    ts = now_str()
    now_ep = time.time()

    with db["lock"]:
        h_key = f"{loc}_{cat}"
        db["history"][h_key] = db["history"].get(h_key, 0) + 1
        cnt = db["history"][h_key]

        is_star = cat == "نظيفة"
        is_pest = cat == "مبيد"
        auto_escalate = (not is_star) and (not is_pest) and (cnt >= 2)

        detail_txt = (
            "طلب دواء (تشيك نظافة ومبيد بعد 3 أيام)"
            if is_pest
            else label
        )

        fid = uuid.uuid4().hex[:8]
        db["followups"].append({
            "id": fid,
            "room_code": short_room(raw_room),
            "loc": loc,
            "cat": cat,
            "detail": detail_txt,
            "time": ts,
            "ts": now_ep,
            "state": "غرفة نظيفة (تخطي) 🌟" if is_star else "بانتظار التشيك",
            "count": cnt,
            "escalated": auto_escalate,
        })
        db["followups"] = db["followups"][-MAX_RECORDS:]
        save_db()

        rep_txt = f" (مرة {cnt})" if cnt > 1 else ""
        wa_msg = f"*{LOCATION_TAG} — طلب دواء / مبيد*\n• {loc}{rep_txt}\n• ملاحظة: تشيك النظافة والمبيد بعد 3 أيام"

        st.session_state["undo"] = ("daily", None, fid, h_key, raw_room)
        st.session_state["last_saved"] = {
            "kind": "pest" if is_pest else ("star" if is_star else "viol"),
            "loc": loc,
            "label": detail_txt,
            "time": ts,
            "repeat": cnt,
            "dup": False,
            "wa_msg": wa_msg if is_pest else "",
        }

        # الانتقال المباشر للواتساب في طلب المبيد فقط (وليس في المخالفات أو الغرفة النظيفة)
        if is_pest:
            st.session_state["jump_wa_url"] = wa_app_url(wa_msg)

    advance_to_next_room(raw_room)


def record_maint(issue_label: str, from_custom: bool = False):
    raw_room = st.session_state.get("sel_room", "").strip()
    if not raw_room:
        return

    if from_custom:
        issue_label = st.session_state.get("custom_maint", "").strip()
        if not issue_label:
            return

    loc = format_room(raw_room)
    ts = now_str()

    with db["lock"]:
        for r in db["repairs"]:
            if r["loc"] == loc and r["item"] == issue_label and r["status"] == "مفتوح":
                wa_msg = f"*{LOCATION_TAG} — تذكير صيانة*\n• {loc}: {issue_label}"
                st.session_state["last_saved"] = {
                    "kind": "maint",
                    "loc": loc,
                    "label": issue_label,
                    "time": r["time"],
                    "repeat": r["repeat"],
                    "dup": True,
                    "wa_msg": wa_msg,
                }
                st.session_state["jump_wa_url"] = wa_app_url(wa_msg)
                if from_custom:
                    st.session_state["custom_maint"] = ""
                return

        h_key = f"{loc}_{issue_label}"
        db["history"][h_key] = db["history"].get(h_key, 0) + 1
        rep = db["history"][h_key]

        tid = uuid.uuid4().hex[:8]
        db["repairs"].append({
            "id": tid,
            "room_code": short_room(raw_room),
            "loc": loc,
            "item": issue_label,
            "time": ts,
            "closed": "",
            "status": "مفتوح",
            "repeat": rep,
        })
        db["repairs"] = db["repairs"][-MAX_RECORDS:]
        save_db()

        rep_txt = f" (تكرار {rep})" if rep > 1 else ""
        wa_msg = f"*{LOCATION_TAG} — صيانة*\n• {loc}: {issue_label}{rep_txt}\n• الوقت: {ts}"

        st.session_state["undo"] = ("maint", tid, None, h_key, raw_room)
        st.session_state["last_saved"] = {
            "kind": "maint",
            "loc": loc,
            "label": issue_label,
            "time": ts,
            "repeat": rep,
            "dup": False,
            "wa_msg": wa_msg,
        }

        # الانتقال المباشر للواتساب في طلبات الصيانة
        st.session_state["jump_wa_url"] = wa_app_url(wa_msg)

    if from_custom:
        st.session_state["custom_maint"] = ""
    advance_to_next_room(raw_room)


def undo_last():
    item = st.session_state.pop("undo", None)
    if not item:
        return
    kind, tid, fid, h_key, prev_room = item
    with db["lock"]:
        if tid:
            db["repairs"] = [r for r in db["repairs"] if r["id"] != tid]
        if fid:
            db["followups"] = [f for f in db["followups"] if f["id"] != fid]
        if h_key in db["history"]:
            db["history"][h_key] = max(0, db["history"][h_key] - 1)
        save_db()
    st.session_state["sel_room"] = prev_room
    st.session_state.pop("last_saved", None)
    st.session_state.pop("jump_wa_url", None)


# تنفيذ الانتقال التلقائي إلى تطبيق واتساب (للمبيدات والصيانة فقط)
jump_url = st.session_state.pop("jump_wa_url", None)
if jump_url:
    components.html(
        f"""
        <script>
        try {{
            window.top.location.href = {json.dumps(jump_url)};
        }} catch (e) {{
            window.location.href = {json.dumps(jump_url)};
        }}
        </script>
        """,
        height=0,
    )

# ==============================================================================
# 5. الواجهة
# ==============================================================================
open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]
pending_checks = [f for f in db["followups"] if f["state"] == "بانتظار التشيك"]
due_checks = [f for f in pending_checks if days_since(f.get("ts", 0)) >= CHECK_CYCLE_DAYS]

st.markdown(
    f"""
    <div class="top-bar">
        <span>🏢 {LOCATION_TAG}</span>
        <span>🔔 مستحق: {len(due_checks)} &nbsp;|&nbsp; 🔍 {len(pending_checks)} &nbsp;|&nbsp; 🛠️ {len(open_reps)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "✏️ الجولة",
    f"⏳ المهام ({len(pending_checks) + len(open_reps)})",
    "📄 التقرير",
])

# --- التبويب 1: الجولة الميدانية بالخريطة ---
with tab1:
    f_cols = st.columns(6)
    for idx, (f_code, f_info) in enumerate(FLOORS.items()):
        f_cols[idx].button(
            f_info["short"],
            key=f"flr_{f_code}",
            on_click=select_floor,
            args=(f_code,),
            use_container_width=True,
        )

    flr_info = FLOORS[active_flr]
    room_count = flr_info["count"]
    floor_rooms = [str(int(active_flr) * 100 + i) for i in range(1, room_count + 1)]

    for r_start in range(0, room_count, 4):
        g_cols = st.columns(4)
        for c_i in range(4):
            idx_rm = r_start + c_i
            if idx_rm < room_count:
                rm_num = floor_rooms[idx_rm]
                g_cols[c_i].button(
                    get_room_label(rm_num),
                    key=f"rm_{rm_num}",
                    on_click=select_room,
                    args=(rm_num,),
                    use_container_width=True,
                )

    # 1. زر الغرفة النظيفة في الأعلى مباشرة تحت الشبكة
    st.button(
        "🌟 غرفة نظيفة (تخطي)",
        key="b_star",
        on_click=record_daily,
        args=("نظيفة", "غرفة نظيفة ومميزة"),
        use_container_width=True,
    )

    # 2. أزرار المخالفات (صامتة + تشيك 3 أيام) وطلب الدواء (واتساب مباشر + تشيك نظافة 3 أيام)
    c1, c2 = st.columns(2)
    with c1:
        st.button("🔌 سحب سخان", key="b_heater", on_click=record_daily, args=("سحب سخان", "سحب سخان"), use_container_width=True)
        st.button("⚠️ سخان ونظافة", key="b_both", on_click=record_daily, args=("سخان ونظافة", "إنذار سخان ونظافة"), use_container_width=True)
    with c2:
        st.button("🗑️ إنذار نظافة", key="b_clean", on_click=record_daily, args=("إنذار نظافة", "إنذار نظافة"), use_container_width=True)
        st.button("🪲 طلب دواء 📲", key="b_pest", on_click=record_daily, args=("مبيد", "طلب دواء (مبيد حشرات)"), use_container_width=True)

    # 3. الشريط الأخضر للغرفة المحددة حالياً
    st.markdown(
        f'<div class="active-banner">📍 {format_room(active_rm)}</div>',
        unsafe_allow_html=True,
    )

    # إشعار الحفظ الفوري + زر واتساب (للمبيد والصيانة فقط) + تراجع
    if "last_saved" in st.session_state:
        s = st.session_state["last_saved"]
        rep_note = f" (تكرار {s['repeat']})" if s["repeat"] > 1 else ""
        status_txt = "⏳ مسجل مسبقاً:" if s["dup"] else "✅ تم:"

        st.markdown(
            f'<div class="ok-card">{status_txt} {s["loc"]} — {s["label"]}{rep_note}</div>',
            unsafe_allow_html=True,
        )

        if s["kind"] in ("pest", "maint") and s.get("wa_msg"):
            direct_link = wa_app_url(s["wa_msg"])
            st.markdown(
                f'<a href="{direct_link}" class="wa-btn">📲 فتح واتساب الآن</a>',
                unsafe_allow_html=True,
            )

        if "undo" in st.session_state:
            st.button("↩️ تراجع عن آخر ضغطة", on_click=undo_last, use_container_width=True)

    # 4. قسم الصيانة (ينقلك للواتساب مباشرة عند اللمس)
    st.markdown('<div class="sec-lbl">🛠️ صيانة (تحويل واتساب فوري 📲):</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.button("❄️ المكيف", key="m_ac", on_click=record_maint, args=("المكيف",), use_container_width=True)
    with m2:
        st.button("💧 تهريب خفيف", key="m_leak", on_click=record_maint, args=("تهريب خفيف",), use_container_width=True)
    with m3:
        st.button("⚡ كهرباء", key="m_elec", on_click=record_maint, args=("كهرباء / فيش",), use_container_width=True)

    cm1, cm2 = st.columns([2.6, 1])
    with cm1:
        st.text_input(
            "ملاحظة صيانة أخرى",
            placeholder="ملاحظة صيانة أخرى...",
            key="custom_maint",
            label_visibility="collapsed",
        )
    with cm2:
        st.button("➕ إرسال", key="m_add", on_click=record_maint, args=("", True), use_container_width=True)

    st.text_input(
        "موقع عام",
        placeholder="موقع عام خارج الغرف (مثل: السطح أو الممر)",
        key="custom_loc_in",
        label_visibility="collapsed",
        on_change=set_custom_location,
    )

# --- التبويب 2: المهام والتشيك (دورة 3 أيام للمبيدات والمخالفات) ---
with tab2:
    if not pending_checks and not open_reps:
        st.info("✨ لا توجد غرف بانتظار التشيك أو صيانة مفتوحة حالياً.")

    if pending_checks:
        st.markdown("##### 🔍 متابعة النظافة والمخالفات (كل 3 أيام):")
        sorted_checks = sorted(
            pending_checks,
            key=lambda x: days_since(x.get("ts", 0)),
            reverse=True,
        )
        for f in sorted_checks:
            d_passed = days_since(f.get("ts", 0))
            is_due = d_passed >= CHECK_CYCLE_DAYS
            card_cls = "task-card task-due" if is_due else "task-card"
            age_badge = (
                f"🔔 مستحق للتشيك الآن (مرّ {d_passed} أيام)"
                if is_due
                else f"⏳ مضى {d_passed} يوم (المراجعة بعد {CHECK_CYCLE_DAYS - d_passed} أيام)"
            )
            rep_b = f" • تكرار {f['count']}" if f.get("count", 1) > 1 else ""

            st.markdown(
                f"<div class='{card_cls}'><b>{f['loc']}</b> — {f['detail']}{rep_b}<br>"
                f"<small style='color:#fbbf24;'>{age_badge}</small></div>",
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns(2)
            if b1.button("✅ تم التشيك (نظيفة)", key=f"chk_{f['id']}", use_container_width=True):
                with db["lock"]:
                    f["state"] = "تم التشيك ✓"
                    save_db()
                st.rerun()
            if b2.button("🚨 تقييم مخالفة / نقل", key=f"esc_{f['id']}", use_container_width=True):
                with db["lock"]:
                    f["state"] = "مرفوع للنقل / تقييم مخالفة 🚨"
                    f["escalated"] = True
                    save_db()
                st.rerun()

    if open_reps:
        st.markdown("---")
        st.markdown("##### 🛠️ ملاحظات الصيانة المفتوحة:")
        for r in reversed(open_reps):
            col_a, col_b = st.columns([2.2, 1])
            col_a.markdown(
                f"<div class='task-card'><b>{r['loc']}</b> — {r['item']}<br><small style='color:#94a3b8;'>📅 {r['time']}</small></div>",
                unsafe_allow_html=True,
            )
            if col_b.button("تم ✓", key=f"done_{r['id']}", use_container_width=True):
                with db["lock"]:
                    r["status"] = "تم الإصلاح"
                    r["closed"] = now_str()
                    save_db()
                st.rerun()

# --- التبويب 3: سلة الواتساب (تحويل مختصر جداً + تقرير مفصل كامل) ---
with tab3:
    heater_recs = [f for f in db["followups"] if f["cat"] == "سحب سخان"]
    clean_recs = [f for f in db["followups"] if f["cat"] == "إنذار نظافة"]
    both_recs = [f for f in db["followups"] if f["cat"] == "سخان ونظافة"]
    pest_recs = [f for f in db["followups"] if f["cat"] == "مبيد"]
    star_recs = [f for f in db["followups"] if f["cat"] == "نظيفة"]
    escalated_recs = [f for f in db["followups"] if f.get("escalated")]

    def rooms_csv(items):
        return "، ".join(dict.fromkeys([i.get("room_code", i["loc"]) for i in items])) or "لا يوجد"

    short_wa_msg = f"""*{LOCATION_TAG} — ملخص سريع*
• سحب سخان ({len(heater_recs)}): {rooms_csv(heater_recs)}
• إنذار نظافة ({len(clean_recs)}): {rooms_csv(clean_recs)}
• سخان ونظافة ({len(both_recs)}): {rooms_csv(both_recs)}
• طلب دواء ({len(pest_recs)}): {rooms_csv(pest_recs)}
• تقييم نقل/مخالفة ({len(escalated_recs)}): {rooms_csv(escalated_recs)}"""

    if open_reps:
        short_wa_msg += f"\n• صيانة ({len(open_reps)}): " + "، ".join(
            [f"{r.get('room_code', r['loc'])} ({r['item']})" for r in open_reps]
        )

    short_wa_url = wa_app_url(short_wa_msg)
    st.markdown(
        f'<a href="{short_wa_url}" class="wa-btn-fast">⚡ تحويل مختصر جداً للواتساب</a>',
        unsafe_allow_html=True,
    )

    heater_txt = "\n".join([f"• {f['loc']} (تكرار {f['count']}) — {f['state']}" for f in heater_recs]) or "• لا يوجد"
    clean_txt = "\n".join([f"• {f['loc']} (تكرار {f['count']}) — {f['state']}" for f in clean_recs]) or "• لا يوجد"
    both_txt = "\n".join([f"• {f['loc']} (تكرار {f['count']}) — {f['state']}" for f in both_recs]) or "• لا يوجد"
    pest_txt = "\n".join([f"• {f['loc']} (مرة {f['count']}) — {f['state']}" for f in pest_recs]) or "• لا يوجد"
    esc_txt = "\n".join([f"• {f['loc']}: {f['detail']} (تكرار {f['count']}) — يوصى بالتقييم/النقل" for f in escalated_recs]) or "• لا يوجد"
    star_txt = "\n".join([f"• {f['loc']} (تخطي في الجولة) 🌟" for f in star_recs]) or "• لا يوجد"

    maint_open_txt = "\n".join([f"• {r['loc']}: {r['item']} ({r['time']})" for r in open_reps]) or "• لا يوجد"
    maint_done_txt = "\n".join([f"• {r['loc']}: {r['item']} ✓" for r in fixed_reps]) or "• لا يوجد"

    full_report = f"""*{LOCATION_TAG} — التقرير المفصل*
*المشرف: {SUPERVISOR_NAME}*

*🚨 تقييم المخالفات / النقل لمكان آخر ({len(escalated_recs)}):*
{esc_txt}

*🔌 سحب السخانات ({len(heater_recs)}):*
{heater_txt}

*🗑️ إنذارات النظافة ({len(clean_recs)}):*
{clean_txt}

*⚠️ إنذارات سخان ونظافة ({len(both_recs)}):*
{both_txt}

*🪲 طلبات الدواء / المبيد ({len(pest_recs)}):*
{pest_txt}

*🌟 غرف نظيفة ومميزة ({len(star_recs)}):*
{star_txt}

*🛠️ ملاحظات الصيانة:*
قيد المتابعة ({len(open_reps)}):
{maint_open_txt}
تم الإنجاز ({len(fixed_reps)}):
{maint_done_txt}"""

    st.text_area("سلة التقرير المفصل:", value=full_report, height=240, label_visibility="collapsed")
    full_wa_url = wa_app_url(full_report)
    st.markdown(
        f'<a href="{full_wa_url}" class="wa-btn">📲 إرسال التقرير المفصل واتساب</a>',
        unsafe_allow_html=True,
    )

    if st.button("🌅 بدء يوم جديد (تصفير المنجز وحفظ دورة 3 أيام)", use_container_width=True):
        with db["lock"]:
            db["repairs"] = [r for r in db["repairs"] if r["status"] == "مفتوح"]
            db["followups"] = [f for f in db["followups"] if f["state"] == "بانتظار التشيك"]
            save_db()
        st.session_state.pop("last_saved", None)
        st.rerun()

    if st.checkbox("تأكيد مسح كل السجلات"):
        if st.button("🗑️ مسح شامل", use_container_width=True):
            with db["lock"]:
                db["repairs"].clear()
                db["followups"].clear()
                db["history"].clear()
                save_db()
            st.session_state.pop("last_saved", None)
            st.rerun()
