from datetime import datetime, timedelta, timezone
import json
import os
import threading
import time
import urllib.parse
import uuid
import streamlit as st

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

# ترجمة بنود الصيانة إلى الأوردو فقط لضمان وضوحها للعامل
MAINT_URDU = {
    "المكيف": "اے سی",
    "تهريب خفيف": "پانی لیکج",
    "كهرباء / فيش": "بجلی",
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

/* زر الغرفة النظيفة */
div.st-key-b_star button {{
    height: 45px !important;
    margin-top: 3px !important;
    margin-bottom: 4px !important;
    background: rgba(16, 185, 129, 0.16) !important;
    border-color: #10b981 !important;
    color: #6ee7b7 !important;
    font-size: 0.98em !important;
}}

/* أزرار المخالفات */
div.st-key-b_heater button, div.st-key-b_clean button, div.st-key-b_both button {{
    background: rgba(245, 158, 11, 0.13) !important;
    border-color: rgba(251, 191, 36, 0.45) !important;
}}

/* زر طلب الدواء */
div.st-key-b_pest button {{
    background: rgba(168, 85, 247, 0.15) !important;
    border-color: rgba(192, 132, 252, 0.5) !important;
}}

/* أزرار الصيانة */
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
.fairness-shield {{
    background: rgba(56, 189, 248, 0.14);
    border: 1.5px solid #38bdf8;
    border-radius: 11px;
    padding: 7px 10px;
    margin: 4px 0;
    text-align: center;
    font-weight: 800;
    font-size: 0.85em;
    color: #bae6fd;
}}
.floor-done-banner {{
    background: rgba(16, 185, 129, 0.18);
    border: 1.5px solid #34d399;
    border-radius: 11px;
    padding: 7px;
    margin: 4px 0;
    text-align: center;
    font-weight: 900;
    font-size: 0.92em;
    color: #a7f3d0;
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
.task-worker {{
    background: rgba(168, 85, 247, 0.12) !important;
    border: 1.5px solid rgba(192, 132, 252, 0.45) !important;
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
.wa-btn-worker {{
    display: block;
    background: linear-gradient(135deg, #8b5cf6 0%, #0ea5e9 100%) !important;
    color: #ffffff !important;
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
# 3. قاعدة البيانات ومحرك الرسائل المهذبة (عربي + أوردو فقط للعامل)
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


def compress_room_ranges(codes: list[str]) -> str:
    nums = sorted({int(c) for c in codes if str(c).isdigit()})
    others = list(dict.fromkeys([str(c) for c in codes if not str(c).isdigit()]))
    parts = []

    i = 0
    while i < len(nums):
        start = nums[i]
        end = start
        while i + 1 < len(nums) and nums[i + 1] == end + 1:
            end = nums[i + 1]
            i += 1
        span = end - start + 1
        if span >= 3:
            parts.append(f"من {start} إلى {end} ({span} غرف)")
        elif span == 2:
            parts.append(f"{start}، {end}")
        else:
            parts.append(str(start))
        i += 1

    parts.extend(others)
    return "، ".join(parts) if parts else "لا يوجد"


def build_grouped_by_floor(items: list[dict], show_escalated_tag: bool = False) -> str:
    if not items:
        return "• لا يوجد"

    by_floor = {f_code: [] for f_code in FLOORS}
    other_items = []

    for item in items:
        rc = str(item.get("room_code", ""))
        tag = " *(توصية بالمتابعة أو النقل)*" if (show_escalated_tag and item.get("escalated")) else ""
        if len(rc) >= 3 and rc[0] in FLOORS and rc.isdigit():
            by_floor[rc[0]].append((rc, tag))
        else:
            other_items.append(f"{item['loc']}{tag}")

    lines = []
    for f_code, f_info in FLOORS.items():
        entries = by_floor[f_code]
        if not entries:
            continue
        normal_codes = [c for c, t in entries if not t]
        esc_codes = [c for c, t in entries if t]

        segments = []
        if normal_codes:
            segments.append(compress_room_ranges(normal_codes))
        if esc_codes:
            segments.append(f"{compress_room_ranges(esc_codes)} *(توصية بالمتابعة أو النقل)*")
        lines.append(f"  - {f_info['name']}: {' | '.join(segments)}")

    for o in dict.fromkeys(other_items):
        lines.append(f"  - {o}")

    return "\n".join(lines) if lines else "• لا يوجد"


def build_worker_checklist(undelivered_pests: list[dict], open_repairs: list[dict]) -> str:
    """رسالة مهام موحدة للعامل باللغتين العربية والأوردو فقط وبصيغة مهذبة"""
    lines = [
        "السلام عليكم ورحمة الله وبركاته،",
        f"*🏢 {LOCATION_TAG} — قائمة مهام الصيانة والمبيدات*",
        f"*تكليف من المشرف: {SUPERVISOR_NAME} | {now_str()}*",
        f"*سپروائزر {SUPERVISOR_NAME} کی جانب سے کام کی تفصیل*",
        "────────────────────",
    ]

    if undelivered_pests:
        lines.append("*🪲 طلبات المبيدات الحشرية (کیڑے مار دوا):*")
        for p in undelivered_pests:
            rep_s = f" (مرة {p['count']})" if p.get("count", 1) > 1 else ""
            lines.append(f"⬜ {p['loc']}{rep_s}")
        lines.append("")

    if open_repairs:
        lines.append("*🛠️ أعمال الصيانة المطلوبة (مرمت کا کام):*")
        for r in open_repairs:
            urdu_lbl = MAINT_URDU.get(r["item"], "")
            item_disp = f"{r['item']} ({urdu_lbl})" if urdu_lbl else r["item"]
            lines.append(f"⬜ {r['loc']} : {item_disp}")
        lines.append("")

    lines.extend([
        "────────────────────",
        "*🤝 فضلاً وتكرماً (براہ کرم):*",
        "نرجو الرد على هذه الرسالة بكتابة رقم الغرفة وكلمة (تم) فور الانتهاء، ولكم جزيل الشكر.",
        "کام مکمل ہونے پر براہ کرم اسی میسج پر ریپلائی کریں اور کمرہ نمبر کے ساتھ (مکمل) لکھ دیں، بہت شکریہ۔",
    ])
    return "\n".join(lines)


def get_room_pending_worker_items(room_num: str) -> list[str]:
    loc = format_room(room_num)
    waiting = []
    for f in db["followups"]:
        if f["loc"] == loc and f["state"] == "📦 بانتظار تسليم المبيد":
            waiting.append("تسليم مبيد حشرات")
    for r in db["repairs"]:
        if r["loc"] == loc and r["status"] == "مفتوح":
            waiting.append(f"صيانة: {r['item']}")
    return waiting


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
            st.session_state["floor_done_msg"] = ""
        else:
            st.session_state["floor_done_msg"] = (
                f"🎉 اكتمل تفتيش {FLOORS[f_code]['name']} بالكامل ({max_r}/{max_r})"
            )


def select_floor(f_code: str):
    st.session_state["sel_floor"] = f_code
    st.session_state["sel_room"] = f"{f_code}01"
    st.session_state["floor_done_msg"] = ""


def select_room(room_num: str):
    st.session_state["sel_room"] = room_num
    st.session_state["floor_done_msg"] = ""


def set_custom_location():
    val = st.session_state.get("custom_loc_in", "").strip()
    if val:
        st.session_state["sel_room"] = val
        st.session_state["custom_loc_in"] = ""
        st.session_state["floor_done_msg"] = ""


# ==============================================================================
# 4. دوال التسجيل (منع تكرار الغرفة الأخيرة + تحديث الحالة المتعارضة)
# ==============================================================================
def record_daily(cat: str, label: str):
    raw_room = st.session_state.get("sel_room", "").strip()
    if not raw_room:
        return

    loc = format_room(raw_room)
    ts = now_str()
    now_ep = time.time()
    is_star = cat == "نظيفة"
    is_pest = cat == "مبيد"

    with db["lock"]:
        existing_idx = None
        for idx, f in enumerate(db["followups"]):
            if f["loc"] == loc and f["state"] in [
                "بانتظار التشيك",
                "📦 بانتظار تسليم المبيد",
                "غرفة نظيفة (تخطي) 🌟",
            ]:
                existing_idx = idx
                break

        if existing_idx is not None and db["followups"][existing_idx]["cat"] == cat:
            existing_rec = db["followups"][existing_idx]
            st.session_state["last_saved"] = {
                "kind": "pest" if is_pest else ("star" if is_star else "viol"),
                "loc": loc,
                "label": existing_rec["detail"],
                "repeat": existing_rec["count"],
                "dup": True,
            }
            advance_to_next_room(raw_room)
            return

        replaced_record = None
        if existing_idx is not None:
            replaced_record = db["followups"].pop(existing_idx)
            old_h_key = f"{loc}_{replaced_record['cat']}"
            if old_h_key in db["history"]:
                db["history"][old_h_key] = max(0, db["history"][old_h_key] - 1)

        h_key = f"{loc}_{cat}"
        db["history"][h_key] = db["history"].get(h_key, 0) + 1
        cnt = db["history"][h_key]

        auto_escalate = (not is_star) and (not is_pest) and (cnt >= 2)
        if is_pest:
            init_state = "📦 بانتظار تسليم المبيد"
            detail_txt = "طلب دواء (تشيك النظافة بعد 3 أيام من التسليم)"
        elif is_star:
            init_state = "غرفة نظيفة (تخطي) 🌟"
            detail_txt = label
        else:
            init_state = "بانتظار التشيك"
            detail_txt = label

        fid = uuid.uuid4().hex[:8]
        db["followups"].append({
            "id": fid,
            "room_code": short_room(raw_room),
            "loc": loc,
            "cat": cat,
            "detail": detail_txt,
            "time": ts,
            "ts": now_ep,
            "state": init_state,
            "count": cnt,
            "escalated": auto_escalate,
        })
        db["followups"] = db["followups"][-MAX_RECORDS:]
        save_db()

        st.session_state["undo"] = ("daily", None, fid, h_key, raw_room, replaced_record)
        st.session_state["last_saved"] = {
            "kind": "pest" if is_pest else ("star" if is_star else "viol"),
            "loc": loc,
            "label": detail_txt,
            "repeat": cnt,
            "dup": False,
        }

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
                st.session_state["last_saved"] = {
                    "kind": "maint",
                    "loc": loc,
                    "label": issue_label,
                    "repeat": r["repeat"],
                    "dup": True,
                }
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

        st.session_state["undo"] = ("maint", tid, None, h_key, raw_room, None)
        st.session_state["last_saved"] = {
            "kind": "maint",
            "loc": loc,
            "label": issue_label,
            "repeat": rep,
            "dup": False,
        }

    if from_custom:
        st.session_state["custom_maint"] = ""
    advance_to_next_room(raw_room)


def undo_last():
    item = st.session_state.pop("undo", None)
    if not item:
        return
    kind, tid, fid, h_key, prev_room, replaced_rec = item
    with db["lock"]:
        if tid:
            db["repairs"] = [r for r in db["repairs"] if r["id"] != tid]
        if fid:
            db["followups"] = [f for f in db["followups"] if f["id"] != fid]
        if h_key in db["history"]:
            db["history"][h_key] = max(0, db["history"][h_key] - 1)
        if replaced_rec:
            db["followups"].append(replaced_rec)
            old_k = f"{replaced_rec['loc']}_{replaced_rec['cat']}"
            db["history"][old_k] = db["history"].get(old_k, 0) + 1
        save_db()
    st.session_state["sel_room"] = prev_room
    st.session_state["floor_done_msg"] = ""
    st.session_state.pop("last_saved", None)


# ==============================================================================
# 5. الواجهة
# ==============================================================================
open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]
undelivered_pests = [f for f in db["followups"] if f["state"] == "📦 بانتظار تسليم المبيد"]
pending_checks = [f for f in db["followups"] if f["state"] == "بانتظار التشيك"]
due_checks = [f for f in pending_checks if days_since(f.get("ts", 0)) >= CHECK_CYCLE_DAYS]

worker_basket_count = len(undelivered_pests) + len(open_reps)

st.markdown(
    f"""
    <div class="top-bar">
        <span>🏢 {LOCATION_TAG}</span>
        <span>👷 للعامل: {worker_basket_count} &nbsp;|&nbsp; 🔔 تشيك: {len(due_checks)}/{len(pending_checks)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "✏️ الجولة",
    f"⏳ المهام ({worker_basket_count + len(pending_checks)})",
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

    if st.session_state.get("floor_done_msg"):
        st.markdown(
            f'<div class="floor-done-banner">{st.session_state["floor_done_msg"]}</div>',
            unsafe_allow_html=True,
        )

    # درع العدالة: تنبيه فوري إذا الغرفة تنتظر صيانة أو مبيد من العامل
    waiting_worker = get_room_pending_worker_items(active_rm)
    if waiting_worker:
        st.markdown(
            f'<div class="fairness-shield">🛡️ تنبيه عدالة: الغرفة تنتظر من العامل ({ " + ".join(waiting_worker) }) — يُفضّل التمهّل قبل تسجيل مخالفة</div>',
            unsafe_allow_html=True,
        )

    # 1. زر الغرفة النظيفة
    st.button(
        "🌟 غرفة نظيفة (تخطي)",
        key="b_star",
        on_click=record_daily,
        args=("نظيفة", "غرفة نظيفة ومميزة"),
        use_container_width=True,
    )

    # 2. أزرار المخالفات وطلب الدواء
    c1, c2 = st.columns(2)
    with c1:
        st.button("🔌 سحب سخان", key="b_heater", on_click=record_daily, args=("سحب سخان", "سحب سخان"), use_container_width=True)
        st.button("⚠️ سخان ونظافة", key="b_both", on_click=record_daily, args=("سخان ونظافة", "إنذار سخان ونظافة"), use_container_width=True)
    with c2:
        st.button("🗑️ إنذار نظافة", key="b_clean", on_click=record_daily, args=("إنذار نظافة", "إنذار نظافة"), use_container_width=True)
        st.button("🪲 طلب دواء (سلة العامل)", key="b_pest", on_click=record_daily, args=("مبيد", "طلب دواء (مبيد حشرات)"), use_container_width=True)

    # 3. الشريط الأخضر للغرفة المحددة حالياً
    st.markdown(
        f'<div class="active-banner">📍 {format_room(active_rm)}</div>',
        unsafe_allow_html=True,
    )

    # إشعار الحفظ الفوري + زر التراجع
    if "last_saved" in st.session_state:
        s = st.session_state["last_saved"]
        rep_note = f" (تكرار {s['repeat']})" if s["repeat"] > 1 else ""
        status_txt = "⏳ مسجل مسبقاً:" if s["dup"] else "✅ أُضيف:"
        basket_note = " ← في قائمة مهام العامل" if s["kind"] in ("pest", "maint") else ""

        st.markdown(
            f'<div class="ok-card">{status_txt} {s["loc"]} — {s["label"]}{rep_note}{basket_note}</div>',
            unsafe_allow_html=True,
        )

        if "undo" in st.session_state:
            st.button("↩️ تراجع عن آخر ضغطة", on_click=undo_last, use_container_width=True)

    # 4. قسم الصيانة
    st.markdown('<div class="sec-lbl">🛠️ صيانة (تُجمع في قائمة مهام العامل):</div>', unsafe_allow_html=True)
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
        st.button("➕ إضافة", key="m_add", on_click=record_maint, args=("", True), use_container_width=True)

    st.text_input(
        "موقع عام",
        placeholder="موقع عام خارج الغرف (مثل: السطح أو الممر)",
        key="custom_loc_in",
        label_visibility="collapsed",
        on_change=set_custom_location,
    )

    # زر إرسال قائمة المهام للعامل دفعة واحدة
    if worker_basket_count > 0:
        worker_msg = build_worker_checklist(undelivered_pests, open_reps)
        worker_url = wa_app_url(worker_msg)
        st.markdown(
            f'<a href="{worker_url}" class="wa-btn-worker">📋 إرسال قائمة المهام للعامل ({worker_basket_count} مهام) دفعة واحدة 📲</a>',
            unsafe_allow_html=True,
        )

# --- التبويب 2: المهام (تأكيد تسليم العامل + دورة 3 أيام العادلة) ---
with tab2:
    if not undelivered_pests and not open_reps and not pending_checks:
        st.info("✨ لا توجد مهام معلقة للعامل أو غرف بانتظار التشيك حالياً.")

    if undelivered_pests or open_reps:
        st.markdown(f"##### 👷 مهام العامل المعلقة ({worker_basket_count}):")
        worker_msg_tab2 = build_worker_checklist(undelivered_pests, open_reps)
        st.markdown(
            f'<a href="{wa_app_url(worker_msg_tab2)}" class="wa-btn-worker">📋 إرسال / تذكير قائمة المهام للعامل 📲</a>',
            unsafe_allow_html=True,
        )

        for p in reversed(undelivered_pests):
            col_a, col_b = st.columns([1.9, 1.3])
            col_a.markdown(
                f"<div class='task-card task-worker'><b>🪲 {p['loc']}</b><br><small style='color:#d8b4fe;'>بانتظار تسليم المبيد ({p['time']})</small></div>",
                unsafe_allow_html=True,
            )
            if col_b.button("📦 تم التسليم (ابدأ 3 أيام)", key=f"deliv_{p['id']}", use_container_width=True):
                with db["lock"]:
                    p["state"] = "بانتظار التشيك"
                    p["ts"] = time.time()
                    p["time"] = now_str()
                    save_db()
                st.rerun()

        for r in reversed(open_reps):
            col_a, col_b = st.columns([2.2, 1])
            col_a.markdown(
                f"<div class='task-card task-worker'><b>🛠️ {r['loc']}</b> — {r['item']}<br><small style='color:#7dd3fc;'>قُيّد: {r['time']}</small></div>",
                unsafe_allow_html=True,
            )
            if col_b.button("تم الإصلاح ✓", key=f"done_{r['id']}", use_container_width=True):
                with db["lock"]:
                    r["status"] = "تم الإصلاح"
                    r["closed"] = now_str()
                    save_db()
                st.rerun()

    if pending_checks:
        st.markdown("---")
        st.markdown(f"##### 🔍 متابعة النظافة والمخالفات (دورة 3 أيام — {len(pending_checks)}):")
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
            if b2.button("🚨 توصية بالمتابعة أو النقل", key=f"esc_{f['id']}", use_container_width=True):
                with db["lock"]:
                    f["state"] = "مرفوع للمتابعة الإدارية أو النقل 🚨"
                    f["escalated"] = True
                    save_db()
                st.rerun()

# --- التبويب 3: التقارير المهذبة (العامل + الإدارة) ---
with tab3:
    # 1. قائمة مهام العامل (عربي + أوردو فقط)
    if worker_basket_count > 0:
        w_msg = build_worker_checklist(undelivered_pests, open_reps)
        st.markdown(
            f'<a href="{wa_app_url(w_msg)}" class="wa-btn-worker">📋 إرسال قائمة المهام للعامل ({worker_basket_count} مهام) دفعة واحدة 📲</a>',
            unsafe_allow_html=True,
        )
        with st.expander("👁️ معاينة رسالة العامل (عربي + أوردو)"):
            st.text_area("رسالة العامل:", value=w_msg, height=200, label_visibility="collapsed")

    heater_recs = [f for f in db["followups"] if f["cat"] == "سحب سخان"]
    clean_recs = [f for f in db["followups"] if f["cat"] == "إنذار نظافة"]
    both_recs = [f for f in db["followups"] if f["cat"] == "سخان ونظافة"]
    pest_recs = [f for f in db["followups"] if f["cat"] == "مبيد"]
    star_recs = [f for f in db["followups"] if f["cat"] == "نظيفة"]
    escalated_recs = [f for f in db["followups"] if f.get("escalated")]

    # 2. ملخص سريع مهذب للإدارة
    def fast_list(items):
        return compress_room_ranges([i.get("room_code", i["loc"]) for i in items])

    short_wa_msg = f"""السلام عليكم ورحمة الله وبركاته،
مرفق لسعادتكم ملخص الجولة الميدانية في *{LOCATION_TAG}*:

• سحب سخان ({len(heater_recs)}): {fast_list(heater_recs)}
• إنذار نظافة ({len(clean_recs)}): {fast_list(clean_recs)}
• سخان ونظافة ({len(both_recs)}): {fast_list(both_recs)}
• طلب دواء ({len(pest_recs)}): {fast_list(pest_recs)}
• توصية بالمتابعة أو النقل ({len(escalated_recs)}): {fast_list(escalated_recs)}"""

    if open_reps:
        short_wa_msg += f"\n• صيانة مفتوحة ({len(open_reps)}): " + "، ".join(
            [f"{r.get('room_code', r['loc'])} ({r['item']})" for r in open_reps]
        )

    short_wa_msg += f"\n\nوتفضلوا بقبول فائق الاحترام والتقدير،\nالمشرف: {SUPERVISOR_NAME}"

    st.markdown(
        f'<a href="{wa_app_url(short_wa_msg)}" class="wa-btn-fast">⚡ إرسال الملخص السريع للإدارة 📲</a>',
        unsafe_allow_html=True,
    )

    # 3. التقرير الميداني التفصيلي للإدارة
    total_inspected = len(set(f["loc"] for f in db["followups"]))
    unique_clean_count = len(set(f["loc"] for f in star_recs))
    notes_count = len(heater_recs) + len(clean_recs) + len(both_recs) + len(pest_recs)
    compliance_pct = round((unique_clean_count / total_inspected) * 100) if total_inspected else 0

    clean_by_flr = {f_code: [] for f_code in FLOORS}
    for s_item in star_recs:
        rc = str(s_item.get("room_code", ""))
        if len(rc) >= 3 and rc[0] in FLOORS and rc.isdigit():
            clean_by_flr[rc[0]].append(rc)

    clean_summary_lines = []
    for f_code, f_info in FLOORS.items():
        c_codes = sorted(set(clean_by_flr[f_code]))
        if not c_codes:
            continue
        max_r = f_info["count"]
        if len(c_codes) >= max_r:
            clean_summary_lines.append(f"  - {f_info['name']}: {max_r}/{max_r} نظيفة بالكامل 🌟")
        else:
            clean_summary_lines.append(
                f"  - {f_info['name']}: {len(c_codes)}/{max_r} نظيفة ({compress_room_ranges(c_codes)})"
            )
    clean_block = "\n".join(clean_summary_lines) if clean_summary_lines else "• لا يوجد"

    esc_by_flr = {f_code: [] for f_code in FLOORS}
    for e_item in escalated_recs:
        rc = str(e_item.get("room_code", ""))
        if len(rc) >= 3 and rc[0] in FLOORS and rc.isdigit():
            esc_by_flr[rc[0]].append(f"{rc} ({e_item['cat']})")

    esc_lines = []
    for f_code, f_info in FLOORS.items():
        if esc_by_flr[f_code]:
            esc_lines.append(f"  - {f_info['name']}: {' | '.join(esc_by_flr[f_code])}")
    esc_block = "\n".join(esc_lines) if esc_lines else "• لا يوجد"

    maint_open_txt = "\n".join([f"• {r['loc']} — {r['item']} ({r['time']})" for r in open_reps]) or "• لا يوجد"
    maint_done_txt = "\n".join([f"• {r['loc']} — {r['item']} ✓" for r in fixed_reps]) or "• لا يوجد"

    pest_waiting = [p for p in pest_recs if p["state"] == "📦 بانتظار تسليم المبيد"]
    pest_active = [p for p in pest_recs if p["state"] != "📦 بانتظار تسليم المبيد"]

    full_report = f"""السلام عليكم ورحمة الله وبركاته،
مرفق لسعادتكم التقرير الميداني التفصيلي لـ *{LOCATION_TAG}*:

*📊 الملخص العام للجولة ({total_inspected} غرفة):*
• نسبة الالتزام والنظافة: *{compliance_pct}%* ({unique_clean_count} غرفة نظيفة 🌟)
• إجمالي الملاحظات المسجلة: *{notes_count} غرفة*
• مهام قيد التنفيذ لدى العامل: *{worker_basket_count}* (صيانة: {len(open_reps)} | مبيدات: {len(pest_waiting)})

*🛠️ أعمال الصيانة العاجلة ({len(open_reps)}):*
{maint_open_txt}

*🚨 توصية بالمتابعة الإدارية أو النقل ({len(escalated_recs)}):*
{esc_block}

*📋 متابعة السخانات والإنذارات والمبيدات:*
• *🔌 سحب سخان ({len(heater_recs)}):*
{build_grouped_by_floor(heater_recs, show_escalated_tag=True)}

• *🗑️ إنذار نظافة ({len(clean_recs)}):*
{build_grouped_by_floor(clean_recs, show_escalated_tag=True)}

• *⚠️ سخان ونظافة معاً ({len(both_recs)}):*
{build_grouped_by_floor(both_recs, show_escalated_tag=True)}

• *🪲 طلبات المبيدات الحشرية ({len(pest_recs)}):*
  - بانتظار تسليم العامل ({len(pest_waiting)}): {fast_list(pest_waiting)}
  - تم التسليم / متابعة 3 أيام ({len(pest_active)}): {fast_list(pest_active)}

*🌟 مؤشر النظافة والتميز حسب الأدوار:*
{clean_block}

*✅ أعمال صيانة تم إنجازها ({len(fixed_reps)}):*
{maint_done_txt}

وتفضلوا بقبول فائق الاحترام والتقدير،
*المشرف: {SUPERVISOR_NAME}*"""

    st.text_area("التقرير الميداني التفصيلي:", value=full_report, height=260, label_visibility="collapsed")
    st.markdown(
        f'<a href="{wa_app_url(full_report)}" class="wa-btn">📲 إرسال التقرير الميداني للإدارة 📲</a>',
        unsafe_allow_html=True,
    )

    if st.button("🌅 بدء يوم جديد (تصفير المنجز وحفظ المعلق)", use_container_width=True):
        with db["lock"]:
            db["repairs"] = [r for r in db["repairs"] if r["status"] == "مفتوح"]
            db["followups"] = [
                f
                for f in db["followups"]
                if f["state"] in ["بانتظار التشيك", "📦 بانتظار تسليم المبيد"]
            ]
            save_db()
        st.session_state.pop("last_saved", None)
        st.session_state["floor_done_msg"] = ""
        st.rerun()

    if st.checkbox("تأكيد مسح كل السجلات"):
        if st.button("🗑️ مسح شامل", use_container_width=True):
            with db["lock"]:
                db["repairs"].clear()
                db["followups"].clear()
                db["history"].clear()
                save_db()
            st.session_state.pop("last_saved", None)
            st.session_state["floor_done_msg"] = ""
            st.rerun()
