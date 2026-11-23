from datetime import datetime, timedelta, timezone
import json
import os
import threading
import time
import urllib.parse
import uuid
import streamlit as st

# ==============================================================================
# 1. الإعدادات وخريطة السكن (عربي + أوردو)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
LOCATION_TAG = "سكن جامعة 3"
LOCATION_URDU = "یونیورسٹی ہاسٹل 3"
SUPERVISOR_NAME = "فارس العصيمي"
DATA_FILE = "sakan_u3_pro.json"
MAX_RECORDS = 150
CHECK_CYCLE_DAYS = 3

FLOORS = {
    "1": {"short": "M2", "name": "الدور M2", "urdu": "ایم ٹو فلور M2", "count": 16},
    "2": {"short": "M", "name": "الدور M", "urdu": "ایم فلور M", "count": 19},
    "3": {"short": "د1", "name": "الدور الأول", "urdu": "پہلی منزل 1", "count": 19},
    "4": {"short": "د2", "name": "الدور الثاني", "urdu": "دوسری منزل 2", "count": 19},
    "5": {"short": "د3", "name": "الدور الثالث", "urdu": "تیسری منزل 3", "count": 19},
    "6": {"short": "د4", "name": "الدور الرابع", "urdu": "چوتھی منزل 4", "count": 19},
}

MAINT_URDU = {
    "المكيف": "اے سی خراب",
    "تهريب خفيف": "پانی لیکج",
    "كهرباء / فيش": "بجلی کا مسئلہ",
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
# 2. التصميم الميداني للجوال (أزرار كبيرة مريحة للإبهام)
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
    padding: 0 3px !important;
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

/* شريط الأدوار */
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

/* زر الصح الكبير في تبويب التشيك */
div[class*="st-key-chk_"] button {{
    height: 54px !important;
    background: rgba(16, 185, 129, 0.2) !important;
    border: 2px solid #10b981 !important;
    color: #6ee7b7 !important;
    font-size: 1.05em !important;
    font-weight: 900 !important;
}}
div[class*="st-key-esc_"] button {{
    height: 54px !important;
    background: rgba(244, 63, 94, 0.14) !important;
    border-color: rgba(244, 63, 94, 0.45) !important;
    color: #fda4af !important;
    font-size: 0.9em !important;
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
    margin-bottom: 4px;
    font-size: 0.92em;
}}
.task-due {{
    background: rgba(245, 158, 11, 0.15) !important;
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
# 3. قاعدة البيانات ومحرك الرسائل المختصرة (بدون قص Read More)
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
            parts.append(f"من {start} إلى {end}")
        elif span == 2:
            parts.append(f"{start}، {end}")
        else:
            parts.append(str(start))
        i += 1

    parts.extend(others)
    return "، ".join(parts) if parts else ""


def build_grouped_by_floor(items: list[dict], show_escalated_tag: bool = False) -> str:
    if not items:
        return ""

    by_floor = {f_code: [] for f_code in FLOORS}
    other_items = []

    for item in items:
        rc = str(item.get("room_code", ""))
        tag = " *(نقل)*" if (show_escalated_tag and item.get("escalated")) else ""
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
            segments.append(f"{compress_room_ranges(esc_codes)} *(توصية بالنقل)*")
        lines.append(f"  - {f_info['name']}: {' | '.join(segments)}")

    for o in dict.fromkeys(other_items):
        lines.append(f"  - {o}")

    return "\n".join(lines)


def build_worker_checklist(undelivered_pests: list[dict], open_repairs: list[dict]) -> str:
    """رسالة مجمّعة ومختصرة جداً بالعربي والأوردو (تظهر كاملة في واتساب بدون Read More)"""
    sup_label = SUPERVISOR_NAME.strip() or "فارس العصيمي"
    lines = [
        f"السلام عليكم | *{LOCATION_TAG} ({LOCATION_URDU})*",
        f"المشرف: *{sup_label}* | سپروائزر: *{sup_label}*",
        "⚠️ *اكتب رقم الغرفة + (تم) عند الانتهاء:*",
        "⚠️ *کام مکمل ہونے پر کمرہ نمبر + (مکمل) لکھ کر ریپلائی کریں:*",
    ]

    if undelivered_pests:
        lines.append("\n*🪲 مبيد حشرات (کیڑے مار دوا دینی ہے):*")
        by_flr = {f_code: [] for f_code in FLOORS}
        others = []
        for p in undelivered_pests:
            rc = str(p.get("room_code", ""))
            if len(rc) >= 3 and rc[0] in FLOORS and rc.isdigit():
                by_flr[rc[0]].append(rc)
            else:
                others.append(p["loc"])

        for f_code, f_info in FLOORS.items():
            if by_flr[f_code]:
                rooms_txt = "، ".join(sorted(set(by_flr[f_code])))
                lines.append(f"• *{rooms_txt}* ({f_info['name']} / {f_info['urdu']})")
        for o in dict.fromkeys(others):
            lines.append(f"• {o}")

    if open_repairs:
        lines.append("\n*🛠️ صيانة (مرمت کا کام):*")
        for r in open_repairs:
            rc = str(r.get("room_code", ""))
            urdu_issue = MAINT_URDU.get(r["item"], r["item"])
            if len(rc) >= 3 and rc[0] in FLOORS and rc.isdigit():
                flr = FLOORS[rc[0]]
                lines.append(f"• کمرہ *{rc}* ({flr['urdu']}) : *{r['item']}* ({urdu_issue})")
            else:
                lines.append(f"• {r['loc']} : *{r['item']}* ({urdu_issue})")

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
            if f["state"] == "تم التشيك — سليم ✅":
                return f"☑️ {room_num}"
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
# 4. دوال التسجيل والتشيك
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
            detail_txt = "طلب مبيد حشرات"
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
            "checked_at": "",
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
cleared_checks = [f for f in db["followups"] if f["state"] == "تم التشيك — سليم ✅"]
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
    f"✅ التشيك ({worker_basket_count + len(pending_checks)})",
    "📄 التقرير",
])

# --- التبويب 1: الجولة الميدانية ---
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

    waiting_worker = get_room_pending_worker_items(active_rm)
    if waiting_worker:
        st.markdown(
            f'<div class="fairness-shield">🛡️ تنبيه عدالة: الغرفة تنتظر من العامل ({ " + ".join(waiting_worker) }) — يُفضّل التمهّل</div>',
            unsafe_allow_html=True,
        )

    st.button(
        "🌟 غرفة نظيفة (تخطي)",
        key="b_star",
        on_click=record_daily,
        args=("نظيفة", "غرفة نظيفة ومميزة"),
        use_container_width=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.button("🔌 سحب سخان", key="b_heater", on_click=record_daily, args=("سحب سخان", "سحب سخان"), use_container_width=True)
        st.button("⚠️ سخان ونظافة", key="b_both", on_click=record_daily, args=("سخان ونظافة", "إنذار سخان ونظافة"), use_container_width=True)
    with c2:
        st.button("🗑️ إنذار نظافة", key="b_clean", on_click=record_daily, args=("إنذار نظافة", "إنذار نظافة"), use_container_width=True)
        st.button("🪲 طلب دواء (للعامل)", key="b_pest", on_click=record_daily, args=("مبيد", "طلب مبيد حشرات"), use_container_width=True)

    st.markdown(
        f'<div class="active-banner">📍 {format_room(active_rm)}</div>',
        unsafe_allow_html=True,
    )

    if "last_saved" in st.session_state:
        s = st.session_state["last_saved"]
        rep_note = f" (تكرار {s['repeat']})" if s["repeat"] > 1 else ""
        status_txt = "⏳ مسجل مسبقاً:" if s["dup"] else "✅ أُضيف:"
        basket_note = " ← في مهام العامل" if s["kind"] in ("pest", "maint") else ""

        st.markdown(
            f'<div class="ok-card">{status_txt} {s["loc"]} — {s["label"]}{rep_note}{basket_note}</div>',
            unsafe_allow_html=True,
        )

        if "undo" in st.session_state:
            st.button("↩️ تراجع عن آخر ضغطة", on_click=undo_last, use_container_width=True)

    st.markdown('<div class="sec-lbl">🛠️ صيانة (تُجمع للعامل):</div>', unsafe_allow_html=True)
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

    if worker_basket_count > 0:
        worker_msg = build_worker_checklist(undelivered_pests, open_reps)
        st.markdown(
            f'<a href="{wa_app_url(worker_msg)}" class="wa-btn-worker">📋 إرسال مهام العامل ({worker_basket_count}) عربي + أوردو 📲</a>',
            unsafe_allow_html=True,
        )

# --- التبويب 2: التشيك بالصح الكبير (✅) ---
with tab2:
    if not undelivered_pests and not open_reps and not pending_checks:
        st.info("✨ لا توجد مهام معلقة للعامل أو غرف بانتظار التشيك حالياً.")

    if undelivered_pests or open_reps:
        st.markdown(f"##### 👷 مهام العامل المعلقة ({worker_basket_count}):")
        worker_msg_tab2 = build_worker_checklist(undelivered_pests, open_reps)
        st.markdown(
            f'<a href="{wa_app_url(worker_msg_tab2)}" class="wa-btn-worker">📋 إرسال قائمة العامل (عربي + أوردو) 📲</a>',
            unsafe_allow_html=True,
        )

        if len(undelivered_pests) >= 2:
            if st.button(
                f"📦 تأكيد تسليم جميع المبيدات ({len(undelivered_pests)}) دفعة واحدة",
                key="deliv_all_pests",
                use_container_width=True,
            ):
                with db["lock"]:
                    now_ep = time.time()
                    now_t = now_str()
                    for p in undelivered_pests:
                        p["state"] = "بانتظار التشيك"
                        p["ts"] = now_ep
                        p["time"] = now_t
                    save_db()
                st.rerun()

        for p in reversed(undelivered_pests):
            col_a, col_b = st.columns([1.9, 1.3])
            col_a.markdown(
                f"<div class='task-card task-worker'><b>🪲 {p['loc']}</b><br><small style='color:#d8b4fe;'>بانتظار تسليم المبيد</small></div>",
                unsafe_allow_html=True,
            )
            if col_b.button("📦 تم التسليم", key=f"deliv_{p['id']}", use_container_width=True):
                with db["lock"]:
                    p["state"] = "بانتظار التشيك"
                    p["ts"] = time.time()
                    p["time"] = now_str()
                    save_db()
                st.rerun()

        for r in reversed(open_reps):
            col_a, col_b = st.columns([2.2, 1])
            col_a.markdown(
                f"<div class='task-card task-worker'><b>🛠️ {r['loc']}</b> — {r['item']}</div>",
                unsafe_allow_html=True,
            )
            if col_b.button("تم ✓", key=f"done_{r['id']}", use_container_width=True):
                with db["lock"]:
                    r["status"] = "تم الإصلاح"
                    r["closed"] = now_str()
                    save_db()
                st.rerun()

    if pending_checks:
        st.markdown("---")
        st.markdown(f"##### ✅ التشيك الميداني (المس الصح الكبير للغرفة السليمة):")
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
                f"🔔 مستحق للتشيك (مرّ {d_passed} أيام)"
                if is_due
                else f"⏳ مضى {d_passed} يوم (المراجعة بعد {CHECK_CYCLE_DAYS - d_passed} أيام)"
            )

            col_info, col_ok, col_esc = st.columns([2.1, 1.2, 0.9])
            col_info.markdown(
                f"<div class='{card_cls}'><b>{f['loc']}</b><br>"
                f"<small style='color:#cbd5e1;'>{f['detail']}</small><br>"
                f"<small style='color:#fbbf24;'>{age_badge}</small></div>",
                unsafe_allow_html=True,
            )
            if col_ok.button("✅ سليم", key=f"chk_{f['id']}", use_container_width=True):
                with db["lock"]:
                    f["state"] = "تم التشيك — سليم ✅"
                    f["checked_at"] = now_str()
                    f["escalated"] = False
                    save_db()
                st.rerun()
            if col_esc.button("🚨 نقل", key=f"esc_{f['id']}", use_container_width=True):
                with db["lock"]:
                    f["state"] = "مرفوع للمتابعة الإدارية أو النقل 🚨"
                    f["escalated"] = True
                    save_db()
                st.rerun()

# --- التبويب 3: التقارير الواضحة والمختصرة ---
with tab3:
    sup_label = SUPERVISOR_NAME.strip() or "فارس العصيمي"

    if worker_basket_count > 0:
        w_msg = build_worker_checklist(undelivered_pests, open_reps)
        st.markdown(
            f'<a href="{wa_app_url(w_msg)}" class="wa-btn-worker">📋 إرسال مهام العامل ({worker_basket_count}) عربي + أوردو 📲</a>',
            unsafe_allow_html=True,
        )
        with st.expander("👁️ معاينة رسالة العامل"):
            st.text_area("رسالة العامل:", value=w_msg, height=170, label_visibility="collapsed")

    active_followups = [
        f
        for f in db["followups"]
        if f["state"] not in ["تم التشيك — سليم ✅", "غرفة نظيفة (تخطي) 🌟"]
    ]
    heater_recs = [f for f in active_followups if f["cat"] == "سحب سخان"]
    clean_recs = [f for f in active_followups if f["cat"] == "إنذار نظافة"]
    both_recs = [f for f in active_followups if f["cat"] == "سخان ونظافة"]
    pest_recs = [f for f in active_followups if f["cat"] == "مبيد"]
    star_recs = [f for f in db["followups"] if f["cat"] == "نظيفة"]
    escalated_recs = [f for f in active_followups if f.get("escalated")]

    def fast_list(items):
        return compress_room_ranges([i.get("room_code", i["loc"]) for i in items])

    total_inspected = len(set(f["loc"] for f in db["followups"]))
    unique_clean_count = len(set(f["loc"] for f in star_recs))
    compliance_pct = round((unique_clean_count / total_inspected) * 100) if total_inspected else 0

    # 1. التقرير المختصر الواضح للإدارة (يظهر كاملاً في واتساب بدون Read More)
    short_lines = [
        "السلام عليكم ورحمة الله وبركاته،",
        f"*تقرير جولة {LOCATION_TAG} — المشرف: {sup_label}*",
        f"📊 *الجولة:* {total_inspected} غرفة | نظيفة: {unique_clean_count} ({compliance_pct}%)",
    ]
    if open_reps:
        short_lines.append(
            f"🛠️ *صيانة ({len(open_reps)}):* "
            + "، ".join([f"{r.get('room_code', r['loc'])} ({r['item']})" for r in open_reps])
        )
    if pest_recs:
        short_lines.append(f"🪲 *مبيدات ({len(pest_recs)}):* {fast_list(pest_recs)}")
    if heater_recs:
        short_lines.append(f"🔌 *سحب سخان ({len(heater_recs)}):* {fast_list(heater_recs)}")
    if clean_recs:
        short_lines.append(f"🗑️ *إنذار نظافة ({len(clean_recs)}):* {fast_list(clean_recs)}")
    if both_recs:
        short_lines.append(f"⚠️ *سخان ونظافة ({len(both_recs)}):* {fast_list(both_recs)}")
    if escalated_recs:
        short_lines.append(f"🚨 *توصية بالنقل ({len(escalated_recs)}):* {fast_list(escalated_recs)}")
    if cleared_checks:
        short_lines.append(f"✅ *تم التشيك والوضع سليم ({len(cleared_checks)}):* {fast_list(cleared_checks)}")
    short_lines.append("وتفضلوا بقبول فائق الاحترام والتقدير.")

    short_wa_msg = "\n".join(short_lines)
    st.markdown(
        f'<a href="{wa_app_url(short_wa_msg)}" class="wa-btn-fast">⚡ إرسال التقرير المختصر للإدارة 📲</a>',
        unsafe_allow_html=True,
    )

    # 2. التقرير التفصيلي المجمّع حسب الأدوار
    rep_lines = [
        "السلام عليكم ورحمة الله وبركاته،",
        f"*التقرير الميداني التفصيلي — {LOCATION_TAG}*",
        f"*المشرف: {sup_label}* | {now_str()}",
        f"📊 *الملخص:* {total_inspected} غرفة | نظيفة: {unique_clean_count} ({compliance_pct}%) | ملاحظات مفتوحة: {len(active_followups)}",
    ]

    if open_reps:
        rep_lines.append(f"\n*🛠️ الصيانة المفتوحة ({len(open_reps)}):*")
        for r in open_reps:
            rep_lines.append(f"• {r['loc']} — {r['item']} ({r['time']})")

    if escalated_recs:
        rep_lines.append(f"\n*🚨 توصية بالمتابعة الإدارية أو النقل ({len(escalated_recs)}):*")
        for e in escalated_recs:
            rep_lines.append(f"• {e['loc']} — {e['detail']} (تكرار {e['count']})")

    if heater_recs or clean_recs or both_recs or pest_recs:
        rep_lines.append("\n*📋 الملاحظات والمبيدات قيد المتابعة:*")
        if heater_recs:
            rep_lines.append(f"• *🔌 سحب سخان ({len(heater_recs)}):*\n{build_grouped_by_floor(heater_recs, True)}")
        if clean_recs:
            rep_lines.append(f"• *🗑️ إنذار نظافة ({len(clean_recs)}):*\n{build_grouped_by_floor(clean_recs, True)}")
        if both_recs:
            rep_lines.append(f"• *⚠️ سخان ونظافة ({len(both_recs)}):*\n{build_grouped_by_floor(both_recs, True)}")
        if pest_recs:
            pest_waiting = [p for p in pest_recs if p["state"] == "📦 بانتظار تسليم المبيد"]
            pest_active = [p for p in pest_recs if p["state"] != "📦 بانتظار تسليم المبيد"]
            rep_lines.append(f"• *🪲 طلبات المبيدات ({len(pest_recs)}):*")
            if pest_waiting:
                rep_lines.append(f"  - بانتظار تسليم العامل ({len(pest_waiting)}): {fast_list(pest_waiting)}")
            if pest_active:
                rep_lines.append(f"  - تم التسليم / متابعة 3 أيام ({len(pest_active)}): {fast_list(pest_active)}")

    if cleared_checks:
        rep_lines.append(f"\n*✅ غرف تم التشيك عليها والوضع سليم ({len(cleared_checks)}):*")
        rep_lines.append(build_grouped_by_floor(cleared_checks, False))

    if star_recs:
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
        if clean_summary_lines:
            rep_lines.append("\n*🌟 الغرف النظيفة حسب الأدوار:*")
            rep_lines.extend(clean_summary_lines)

    if fixed_reps:
        rep_lines.append(f"\n*✔️ صيانة تم إنجازها ({len(fixed_reps)}):*")
        for fx in fixed_reps:
            rep_lines.append(f"• {fx['loc']} — {fx['item']} ✓")

    rep_lines.append(f"\nوتفضلوا بقبول فائق الاحترام والتقدير،\n*المشرف: {sup_label}*")

    full_report = "\n".join(rep_lines)
    st.text_area("التقرير التفصيلي:", value=full_report, height=230, label_visibility="collapsed")
    st.markdown(
        f'<a href="{wa_app_url(full_report)}" class="wa-btn">📲 إرسال التقرير التفصيلي للإدارة 📲</a>',
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
