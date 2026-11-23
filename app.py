from datetime import datetime, timedelta, timezone
import json
import os
import threading
import time
import urllib.parse
import uuid
import streamlit as st

# ==============================================================================
# 1. الإعدادات وخريطة السكن (عربي + أوردو مبسط وواضح)
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
    "المكيف": "اے سی ٹھیک کرنا ہے",
    "تهريب خفيف": "پانی لیکج ٹھیک کرنا ہے",
    "كهرباء / فيش": "بجلی / ساکٹ ٹھیک کرنا ہے",
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
# 2. التصميم البصري المبسط (مناسب لعمر 7 سنوات)
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
    height: 54px !important;
    width: 100% !important;
    padding: 0 4px !important;
    font-size: 1.02em !important;
    font-weight: 900 !important;
    border-radius: 15px !important;
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

/* شريط الأدوار */
div[class*="st-key-flr_"] button {{
    height: 42px !important;
    font-size: 0.92em !important;
    border-radius: 11px !important;
    background: #111827 !important;
}}
div.st-key-flr_{active_flr} button {{
    background: #10b981 !important;
    color: #022c22 !important;
    border-color: #10b981 !important;
}}

/* شبكة الغرف */
div[class*="st-key-rm_"] button {{
    height: 41px !important;
    font-size: 0.9em !important;
    border-radius: 11px !important;
    background: #111827 !important;
}}
div.st-key-rm_{active_rm} button {{
    border: 2.5px solid #10b981 !important;
    background: rgba(16, 185, 129, 0.25) !important;
    color: #ecfdf5 !important;
}}

/* زر الغرفة النظيفة (أخضر كبير) */
div.st-key-b_star button {{
    height: 56px !important;
    font-size: 1.12em !important;
    background: rgba(16, 185, 129, 0.2) !important;
    border: 2px solid #10b981 !important;
    color: #6ee7b7 !important;
}}

/* أزرار المخالفات (برتقالي) */
div.st-key-b_heater button, div.st-key-b_clean button, div.st-key-b_both button {{
    background: rgba(245, 158, 11, 0.16) !important;
    border-color: rgba(251, 191, 36, 0.55) !important;
    color: #fde68a !important;
}}

/* زر الدواء (بنفسجي) */
div.st-key-b_pest button {{
    background: rgba(168, 85, 247, 0.18) !important;
    border-color: rgba(192, 132, 252, 0.6) !important;
    color: #e9d5ff !important;
}}

/* أزرار الصيانة (أزرق) */
div.st-key-m_ac button, div.st-key-m_leak button,
div.st-key-m_elec button, div.st-key-m_add button {{
    height: 48px !important;
    font-size: 0.94em !important;
    background: rgba(14, 165, 233, 0.15) !important;
    border-color: rgba(56, 189, 248, 0.5) !important;
    color: #bae6fd !important;
}}

/* زر التراجع السريع */
div.st-key-btn_undo button {{
    height: 46px !important;
    background: rgba(244, 63, 94, 0.16) !important;
    border: 1.5px solid #f43f5e !important;
    color: #fda4af !important;
}}

/* أزرار الصح والخطأ الكبيرة (✅ / ❌) */
div[class*="st-key-deliv_ok_"] button,
div[class*="st-key-chk_ok_"] button {{
    height: 54px !important;
    background: rgba(16, 185, 129, 0.22) !important;
    border: 2px solid #10b981 !important;
    color: #6ee7b7 !important;
    font-size: 1.05em !important;
}}
div[class*="st-key-deliv_no_"] button,
div[class*="st-key-chk_no_"] button {{
    height: 54px !important;
    background: rgba(244, 63, 94, 0.18) !important;
    border: 2px solid rgba(244, 63, 94, 0.6) !important;
    color: #fda4af !important;
    font-size: 1.05em !important;
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

.room-hero {{
    background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
    border: 2px solid #10b981;
    border-radius: 15px;
    padding: 10px;
    margin: 4px 0 6px 0;
    text-align: center;
}}
.room-hero-big {{
    font-size: 1.35em;
    font-weight: 900;
    color: #ecfdf5;
}}
.room-hero-sub {{
    font-size: 0.82em;
    color: #a7f3d0;
}}

.fairness-shield {{
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
.floor-done-banner {{
    background: rgba(16, 185, 129, 0.22);
    border: 2px solid #34d399;
    border-radius: 12px;
    padding: 9px;
    margin: 5px 0;
    text-align: center;
    font-weight: 900;
    font-size: 0.98em;
    color: #a7f3d0;
}}
.ok-card {{
    background: rgba(16, 185, 129, 0.16);
    border: 2px solid #10b981;
    border-radius: 13px;
    padding: 10px;
    margin-top: 6px;
    color: #6ee7b7;
    text-align: center;
    font-weight: 900;
    font-size: 0.98em;
}}
.task-card {{
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 10px 12px;
    margin-top: 6px;
    margin-bottom: 4px;
    font-size: 0.96em;
}}
.task-due {{
    background: rgba(245, 158, 11, 0.16) !important;
    border: 2px solid #f59e0b !important;
}}
.task-repeat {{
    background: rgba(244, 63, 94, 0.15) !important;
    border: 2px solid rgba(244, 63, 94, 0.55) !important;
}}
.task-worker {{
    background: rgba(168, 85, 247, 0.14) !important;
    border: 2px solid rgba(192, 132, 252, 0.5) !important;
}}
.wa-btn {{
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 15px;
    border-radius: 14px;
    font-weight: 900;
    font-size: 1.06em;
    text-decoration: none !important;
    margin: 7px 0;
}}
.wa-btn-worker {{
    display: block;
    background: linear-gradient(135deg, #8b5cf6 0%, #0ea5e9 100%) !important;
    color: #ffffff !important;
    text-align: center;
    padding: 15px;
    border-radius: 14px;
    font-weight: 900;
    font-size: 1.06em;
    text-decoration: none !important;
    margin: 7px 0;
}}
.wa-btn-fast {{
    display: block;
    background: #0ea5e9 !important;
    color: #082f49 !important;
    text-align: center;
    padding: 15px;
    border-radius: 14px;
    font-weight: 900;
    font-size: 1.06em;
    text-decoration: none !important;
    margin: 7px 0;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. قاعدة البيانات ومحرك الرسائل البسيطة (عربي + أوردو)
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


def inject_demo_scenario():
    clear_demo_scenario(save=False)
    now_ep = time.time()
    four_days_ago = now_ep - (4 * 86400)
    ts_now = now_str()

    with db["lock"]:
        for i in range(1, 17):
            rc = str(100 + i)
            loc = format_room(rc)
            db["followups"].append({
                "id": f"demo_{uuid.uuid4().hex[:6]}",
                "room_code": rc,
                "loc": loc,
                "cat": "نظيفة",
                "detail": "غرفة نظيفة",
                "time": ts_now,
                "checked_at": "",
                "ts": now_ep,
                "state": "غرفة نظيفة (تخطي) 🌟",
                "count": 1,
                "not_done": False,
                "is_demo": True,
            })

        for rc in ["601", "602"]:
            loc = format_room(rc)
            db["followups"].append({
                "id": f"demo_{uuid.uuid4().hex[:6]}",
                "room_code": rc,
                "loc": loc,
                "cat": "مبيد",
                "detail": "دواء حشرات",
                "time": ts_now,
                "checked_at": "",
                "ts": now_ep,
                "state": "📦 بانتظار تسليم المبيد",
                "count": 1,
                "not_done": False,
                "is_demo": True,
            })

        db["followups"].append({
            "id": f"demo_{uuid.uuid4().hex[:6]}",
            "room_code": "305",
            "loc": format_room("305"),
            "cat": "سحب سخان",
            "detail": "سحب سخان",
            "time": "منذ 4 أيام",
            "checked_at": "",
            "ts": four_days_ago,
            "state": "بانتظار التشيك",
            "count": 1,
            "not_done": False,
            "is_demo": True,
        })

        db["followups"].append({
            "id": f"demo_{uuid.uuid4().hex[:6]}",
            "room_code": "311",
            "loc": format_room("311"),
            "cat": "إنذار نظافة",
            "detail": "إنذار نظافة",
            "time": ts_now,
            "checked_at": ts_now,
            "ts": now_ep,
            "state": "بانتظار التشيك",
            "count": 2,
            "not_done": True,
            "is_demo": True,
        })

        db["followups"].append({
            "id": f"demo_{uuid.uuid4().hex[:6]}",
            "room_code": "204",
            "loc": format_room("204"),
            "cat": "سخان ونظافة",
            "detail": "إنذار سخان ونظافة",
            "time": "سابق",
            "checked_at": ts_now,
            "ts": now_ep,
            "state": "تم ✅",
            "count": 1,
            "not_done": False,
            "is_demo": True,
        })

        db["repairs"].append({
            "id": f"demo_{uuid.uuid4().hex[:6]}",
            "room_code": "607",
            "loc": format_room("607"),
            "item": "المكيف",
            "time": ts_now,
            "closed": "",
            "status": "مفتوح",
            "repeat": 1,
            "is_demo": True,
        })
        save_db()


def clear_demo_scenario(save: bool = True):
    with db["lock"]:
        db["followups"] = [f for f in db["followups"] if not f.get("is_demo")]
        db["repairs"] = [r for r in db["repairs"] if not r.get("is_demo")]
        if save:
            save_db()


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


def build_grouped_by_floor(items: list[dict], show_repeat_tag: bool = False) -> str:
    if not items:
        return ""

    by_floor = {f_code: [] for f_code in FLOORS}
    other_items = []

    for item in items:
        rc = str(item.get("room_code", ""))
        cnt = item.get("count", 1)
        tag = f" *(تكررت {cnt} مرات)*" if (show_repeat_tag and cnt > 1) else ""
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
        rep_entries = [f"{c}{t}" for c, t in entries if t]

        segments = []
        if normal_codes:
            segments.append(compress_room_ranges(normal_codes))
        if rep_entries:
            segments.append(" | ".join(rep_entries))
        lines.append(f"  - {f_info['name']}: {' | '.join(segments)}")

    for o in dict.fromkeys(other_items):
        lines.append(f"  - {o}")

    return "\n".join(lines)


def build_worker_checklist(undelivered_pests: list[dict], open_repairs: list[dict]) -> str:
    """رسالة مهام للعامل مبنية على الترميز المزدوج: يفهمها أي شخص (عربي أو أوردو) بعمر 10 سنوات"""
    sup_label = SUPERVISOR_NAME.strip() or "فارس العصيمي"
    lines = [
        f"السلام عليكم ورحمة الله وبركاته 🌹",
        f"🏢 *{LOCATION_TAG}* | *{LOCATION_URDU}*",
        f"المشرف: *{sup_label}* | سپروائزر: *{sup_label}*",
        "👇 *المطلوب منك (یہ کام کرنا ہے):*",
    ]

    if undelivered_pests:
        lines.append("\n*🪲 أعطِ دواء حشرات (کیڑے مار دوا دینی ہے):*")
        for p in undelivered_pests:
            rc = str(p.get("room_code", ""))
            if len(rc) >= 3 and rc[0] in FLOORS and rc.isdigit():
                flr = FLOORS[rc[0]]
                lines.append(
                    f"• غرفة *{rc}* ({flr['name']} / {flr['urdu']})\n"
                    f"  هل وصل الدواء؟ (دوا دے دی؟):  ✅ نعم   |   ❌ لا"
                )
            else:
                lines.append(
                    f"• {p['loc']}\n"
                    f"  هل وصل الدواء؟ (دوا دے دی؟):  ✅ نعم   |   ❌ لا"
                )

    if open_repairs:
        lines.append("\n*🛠️ صلح هذا العطل (یہ چیز ٹھیک کرنی ہے):*")
        for r in open_repairs:
            rc = str(r.get("room_code", ""))
            urdu_action = MAINT_URDU.get(r["item"], r["item"])
            if len(rc) >= 3 and rc[0] in FLOORS and rc.isdigit():
                flr = FLOORS[rc[0]]
                lines.append(
                    f"• غرفة *{rc}* ({flr['name']} / {flr['urdu']})\n"
                    f"  المطلوب: *{r['item']}* ({urdu_action})\n"
                    f"  هل تصلّح؟ (ٹھیک ہو گیا؟):  ✅ نعم   |   ❌ لا"
                )
            else:
                lines.append(
                    f"• {r['loc']} : *{r['item']}* ({urdu_action})\n"
                    f"  هل تصلّح؟ (ٹھیک ہو گیا؟):  ✅ نعم   |   ❌ لا"
                )

    lines.append(
        "\n📲 *رد على هذه الرسالة واكتب رقم الغرفة + ✅*\n"
        "📲 *اس میسج پر ریپلائی کر کے کمرہ نمبر + ✅ لکھ دیں، شکریہ*"
    )
    return "\n".join(lines)


def get_room_pending_worker_items(room_num: str) -> list[str]:
    loc = format_room(room_num)
    waiting = []
    for f in db["followups"]:
        if f["loc"] == loc and f["state"] in ["📦 بانتظار تسليم المبيد", "⚠️ لم يُسلّم المبيد بعد"]:
            waiting.append("دواء حشرات")
    for r in db["repairs"]:
        if r["loc"] == loc and r["status"] == "مفتوح":
            waiting.append(r["item"])
    return waiting


def get_room_label(room_num: str) -> str:
    loc = format_room(room_num)
    for f in reversed(db["followups"]):
        if f["loc"] == loc:
            if f["state"] == "تم ✅":
                return f"☑️ {room_num}"
            if f.get("not_done") or f.get("count", 1) >= 2:
                return f"❗ {room_num}"
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
                f"🎉 بطل! خلّصت {FLOORS[f_code]['name']} بالكامل ({max_r}/{max_r})"
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
# 4. دوال التسجيل السريع
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
                "⚠️ لم يُسلّم المبيد بعد",
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

        if is_pest:
            init_state = "📦 بانتظار تسليم المبيد"
            detail_txt = "دواء حشرات"
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
            "not_done": cnt >= 2 and not is_star and not is_pest,
            "is_demo": False,
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
            "is_demo": False,
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
# 5. الواجهة (3 خطوات مرقمة واضحة لعمر 7 سنوات)
# ==============================================================================
open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]
undelivered_pests = [
    f for f in db["followups"] if f["state"] in ["📦 بانتظار تسليم المبيد", "⚠️ لم يُسلّم المبيد بعد"]
]
pending_checks = [f for f in db["followups"] if f["state"] == "بانتظار التشيك"]
done_checks = [f for f in db["followups"] if f["state"] == "تم ✅"]
due_checks = [f for f in pending_checks if days_since(f.get("ts", 0)) >= CHECK_CYCLE_DAYS]
has_demo_data = any(f.get("is_demo") for f in db["followups"]) or any(r.get("is_demo") for r in db["repairs"])

worker_basket_count = len(undelivered_pests) + len(open_reps)

demo_tag_html = ' <span style="color:#fbbf24;font-size:0.8em;">(تجربة)</span>' if has_demo_data else ""
st.markdown(
    f"""
    <div class="top-bar">
        <span>🏢 {LOCATION_TAG}{demo_tag_html}</span>
        <span>👷 للعامل: {worker_basket_count} &nbsp;|&nbsp; 🔍 للتشيك: {len(pending_checks)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "1️⃣ الغرف",
    f"2️⃣ صح وخطأ ({worker_basket_count + len(pending_checks)})",
    "3️⃣ إرسال 📲",
])

# --- الخطوة 1: تلوين الغرف ---
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

    inspected_in_floor = {
        f.get("room_code")
        for f in db["followups"]
        if f.get("room_code") in floor_rooms
    }
    done_in_flr = len(inspected_in_floor)
    flr_pct = min(100, round((done_in_flr / room_count) * 100))

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

    st.markdown(
        f"""
        <div class="prog-wrap">
            <div class="prog-head">
                <span>⭐ {flr_info['name']}</span>
                <span>{done_in_flr} من {room_count}</span>
            </div>
            <div class="prog-track">
                <div class="prog-fill" style="width:{flr_pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("floor_done_msg"):
        st.markdown(
            f'<div class="floor-done-banner">{st.session_state["floor_done_msg"]}</div>',
            unsafe_allow_html=True,
        )

    waiting_worker = get_room_pending_worker_items(active_rm)
    if waiting_worker:
        st.markdown(
            f'<div class="fairness-shield">🛡️ انتظر! العامل باقي ما خلّص: ({ " + ".join(waiting_worker) })</div>',
            unsafe_allow_html=True,
        )

    st.button(
        "🌟 نظيفة (التالي)",
        key="b_star",
        on_click=record_daily,
        args=("نظيفة", "غرفة نظيفة"),
        use_container_width=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.button("🔌 سخان", key="b_heater", on_click=record_daily, args=("سحب سخان", "سحب سخان"), use_container_width=True)
        st.button("⚠️ سخان + نظافة", key="b_both", on_click=record_daily, args=("سخان ونظافة", "إنذار سخان ونظافة"), use_container_width=True)
    with c2:
        st.button("🗑️ نظافة", key="b_clean", on_click=record_daily, args=("إنذار نظافة", "إنذار نظافة"), use_container_width=True)
        st.button("🪲 دواء", key="b_pest", on_click=record_daily, args=("مبيد", "دواء حشرات"), use_container_width=True)

    st.markdown(
        f"""
        <div class="room-hero">
            <div class="room-hero-big">🚪 {format_room(active_rm)}</div>
            <div class="room-hero-sub">المس الحالة فوق أو العطل تحت</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "last_saved" in st.session_state:
        s = st.session_state["last_saved"]
        status_txt = "⏳ مسجل من قبل:" if s["dup"] else "✅ تم الحفظ:"
        st.markdown(
            f'<div class="ok-card">{status_txt} {s["loc"]} — {s["label"]}</div>',
            unsafe_allow_html=True,
        )
        if "undo" in st.session_state:
            st.button("↩️ رجوع (غلطت)", key="btn_undo", on_click=undo_last, use_container_width=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.button("❄️ مكيف", key="m_ac", on_click=record_maint, args=("المكيف",), use_container_width=True)
    with m2:
        st.button("💧 موية", key="m_leak", on_click=record_maint, args=("تهريب خفيف",), use_container_width=True)
    with m3:
        st.button("⚡ كهرباء", key="m_elec", on_click=record_maint, args=("كهرباء / فيش",), use_container_width=True)

    if worker_basket_count > 0:
        worker_msg = build_worker_checklist(undelivered_pests, open_reps)
        st.markdown(
            f'<a href="{wa_app_url(worker_msg)}" class="wa-btn-worker">👷 أرسل للعامل ({worker_basket_count}) 📲</a>',
            unsafe_allow_html=True,
        )

    with st.expander("⌨️ كتابة مكان أو عطل آخر"):
        cm1, cm2 = st.columns([2.6, 1])
        with cm1:
            st.text_input(
                "عطل آخر",
                placeholder="اكتب العطل هنا...",
                key="custom_maint",
                label_visibility="collapsed",
            )
        with cm2:
            st.button("➕ حفظ", key="m_add", on_click=record_maint, args=("", True), use_container_width=True)

        st.text_input(
            "مكان عام",
            placeholder="مكان خارج الغرف (مثل: السطح)",
            key="custom_loc_in",
            label_visibility="collapsed",
            on_change=set_custom_location,
        )

# --- الخطوة 2: صح وخطأ (✅ / ❌) ---
with tab2:
    if not undelivered_pests and not open_reps and not pending_checks:
        st.markdown(
            '<div class="floor-done-banner">🏆 ممتاز! كل المهام خالصة</div>',
            unsafe_allow_html=True,
        )

    if undelivered_pests or open_reps:
        st.markdown("##### 📦 هل وصل الدواء / تصلّح العطل؟")
        if len(undelivered_pests) >= 2:
            if st.button(
                f"✅ الكل وصل ({len(undelivered_pests)})",
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
            st.markdown(
                f"<div class='task-card task-worker'><b>🪲 {p['loc']}</b> — دواء حشرات</div>",
                unsafe_allow_html=True,
            )
            d_c1, d_c2 = st.columns(2)
            with d_c1:
                if st.button("✅ تم الاستلام", key=f"deliv_ok_{p['id']}", use_container_width=True):
                    with db["lock"]:
                        p["state"] = "بانتظار التشيك"
                        p["ts"] = time.time()
                        p["time"] = now_str()
                        save_db()
                    st.rerun()
            with d_c2:
                if st.button("❌ ما تم", key=f"deliv_no_{p['id']}", use_container_width=True):
                    with db["lock"]:
                        p["state"] = "⚠️ لم يُسلّم المبيد بعد"
                        save_db()
                    st.rerun()

        for r in reversed(open_reps):
            st.markdown(
                f"<div class='task-card task-worker'><b>🛠️ {r['loc']}</b> — {r['item']}</div>",
                unsafe_allow_html=True,
            )
            r_c1, r_c2 = st.columns(2)
            with r_c1:
                if st.button("✅ تصلّح", key=f"chk_ok_rep_{r['id']}", use_container_width=True):
                    with db["lock"]:
                        r["status"] = "تم الإصلاح"
                        r["closed"] = now_str()
                        save_db()
                    st.rerun()
            with r_c2:
                if st.button("❌ ما تم", key=f"chk_no_rep_{r['id']}", use_container_width=True):
                    with db["lock"]:
                        r["repeat"] = r.get("repeat", 1) + 1
                        save_db()
                    st.rerun()

    if pending_checks:
        st.markdown("---")
        st.markdown("##### 🔍 هل صارت الغرفة نظيفة؟ (كل 3 أيام)")
        sorted_checks = sorted(
            pending_checks,
            key=lambda x: days_since(x.get("ts", 0)),
            reverse=True,
        )
        for f in sorted_checks:
            d_passed = days_since(f.get("ts", 0))
            is_due = d_passed >= CHECK_CYCLE_DAYS
            is_rep = f.get("not_done") or f.get("count", 1) >= 2
            card_cls = "task-card task-repeat" if is_rep else ("task-card task-due" if is_due else "task-card")
            age_badge = f"🔔 مرّ {d_passed} أيام" if is_due else f"⏳ مرّ {d_passed} يوم"
            rep_badge = f" • مرة {f['count']}" if f.get("count", 1) > 1 else ""

            st.markdown(
                f"<div class='{card_cls}'><b>{f['loc']}</b> — {f['detail']}{rep_badge}<br>"
                f"<small style='color:#fbbf24;'>{age_badge}</small></div>",
                unsafe_allow_html=True,
            )
            c_ok, c_no = st.columns(2)
            with c_ok:
                if st.button("✅ تم (صارت نظيفة)", key=f"chk_ok_{f['id']}", use_container_width=True):
                    with db["lock"]:
                        f["state"] = "تم ✅"
                        f["checked_at"] = now_str()
                        f["not_done"] = False
                        save_db()
                    st.rerun()
            with c_no:
                if st.button("❌ ما تم", key=f"chk_no_{f['id']}", use_container_width=True):
                    with db["lock"]:
                        h_key = f"{f['loc']}_{f['cat']}"
                        db["history"][h_key] = db["history"].get(h_key, 1) + 1
                        f["count"] = db["history"][h_key]
                        f["not_done"] = True
                        f["ts"] = time.time()
                        f["checked_at"] = now_str()
                        save_db()
                    st.rerun()

# --- الخطوة 3: الإرسال بلمسة واحدة (رسائل بسيطة جداً ومفصلة) ---
with tab3:
    sup_label = SUPERVISOR_NAME.strip() or "فارس العصيمي"

    if worker_basket_count > 0:
        w_msg = build_worker_checklist(undelivered_pests, open_reps)
        st.markdown(
            f'<a href="{wa_app_url(w_msg)}" class="wa-btn-worker">👷 1. أرسل للعامل ({worker_basket_count}) 📲</a>',
            unsafe_allow_html=True,
        )

    active_followups = [
        f
        for f in db["followups"]
        if f["state"] not in ["تم ✅", "غرفة نظيفة (تخطي) 🌟"]
    ]
    heater_recs = [f for f in active_followups if f["cat"] == "سحب سخان"]
    clean_recs = [f for f in active_followups if f["cat"] == "إنذار نظافة"]
    both_recs = [f for f in active_followups if f["cat"] == "سخان ونظافة"]
    pest_recs = [f for f in active_followups if f["cat"] == "مبيد"]
    star_recs = [f for f in db["followups"] if f["cat"] == "نظيفة"]
    not_done_recs = [f for f in active_followups if f.get("not_done") or f.get("count", 1) >= 2]

    def fast_list(items):
        return compress_room_ranges([i.get("room_code", i["loc"]) for i in items])

    total_inspected = len(set(f["loc"] for f in db["followups"]))
    unique_clean_count = len(set(f["loc"] for f in star_recs))
    compliance_pct = round((unique_clean_count / total_inspected) * 100) if total_inspected else 0

    # 1. الملخص السريع للمدير (بسيط ومباشر)
    short_lines = [
        "السلام عليكم ورحمة الله وبركاته 🌹",
        f"*ملخص جولة {LOCATION_TAG}* (المشرف: {sup_label})",
        f"🌟 *الغرف النظيفة:* {unique_clean_count} من {total_inspected} غرفة ({compliance_pct}%)",
    ]
    if open_reps:
        short_lines.append(
            f"🛠️ *أعطال صيانة ({len(open_reps)}):* "
            + "، ".join([f"{r.get('room_code', r['loc'])} ({r['item']})" for r in open_reps])
        )
    if not_done_recs:
        short_lines.append(f"❌ *غرف ما نظّفت — تكررت ({len(not_done_recs)}):* {fast_list(not_done_recs)}")
    if pest_recs:
        short_lines.append(f"🪲 *تحتاج دواء حشرات ({len(pest_recs)}):* {fast_list(pest_recs)}")
    if heater_recs:
        short_lines.append(f"🔌 *سحب سخان ({len(heater_recs)}):* {fast_list(heater_recs)}")
    if clean_recs:
        short_lines.append(f"🗑️ *إنذار نظافة ({len(clean_recs)}):* {fast_list(clean_recs)}")
    if both_recs:
        short_lines.append(f"⚠️ *سخان ونظافة ({len(both_recs)}):* {fast_list(both_recs)}")
    if done_checks:
        short_lines.append(f"✅ *شيكنا عليها وصارت نظيفة ({len(done_checks)}):* {fast_list(done_checks)}")
    short_lines.append("ولكم جزيل الشكر والتقدير.")

    short_wa_msg = "\n".join(short_lines)
    st.markdown(
        f'<a href="{wa_app_url(short_wa_msg)}" class="wa-btn-fast">⚡ 2. أرسل ملخص سريع للمدير 📲</a>',
        unsafe_allow_html=True,
    )

    # 2. التقرير المفصل (يفهمه عمر 7 سنوات ويحوي كل التفاصيل بدقة)
    rep_lines = [
        "السلام عليكم ورحمة الله وبركاته 🌹",
        f"*تقرير المتابعة اليومي — {LOCATION_TAG}*",
        f"المشرف: *{sup_label}* | {now_str()}",
        f"📊 *النتيجة:* فحصنا *{total_inspected}* غرفة | النظيفة: *{unique_clean_count}* ({compliance_pct}%) | الملاحظات: *{len(active_followups)}*",
    ]

    if open_reps:
        rep_lines.append(f"\n*🛠️ أعطال تحتاج تصليح ({len(open_reps)}):*")
        for r in open_reps:
            rep_note = f" (تكررت {r['repeat']} مرات)" if r.get("repeat", 1) > 1 else ""
            rep_lines.append(f"• {r['loc']} : *{r['item']}*{rep_note} ({r['time']})")

    if not_done_recs:
        rep_lines.append(f"\n*❌ غرف ما نظّفت بعد التنبيه ({len(not_done_recs)}):*")
        for nd in not_done_recs:
            rep_lines.append(f"• {nd['loc']} : {nd['detail']} (تكررت {nd['count']} مرات)")

    if heater_recs or clean_recs or both_recs or pest_recs:
        rep_lines.append("\n*📋 تفاصيل الغرف تحت المتابعة (كل 3 أيام):*")
        if heater_recs:
            rep_lines.append(f"• *🔌 سحب سخان ({len(heater_recs)}):*\n{build_grouped_by_floor(heater_recs, True)}")
        if clean_recs:
            rep_lines.append(f"• *🗑️ إنذار نظافة ({len(clean_recs)}):*\n{build_grouped_by_floor(clean_recs, True)}")
        if both_recs:
            rep_lines.append(f"• *⚠️ سخان ونظافة ({len(both_recs)}):*\n{build_grouped_by_floor(both_recs, True)}")
        if pest_recs:
            pest_waiting = [p for p in pest_recs if p["state"] in ["📦 بانتظار تسليم المبيد", "⚠️ لم يُسلّم المبيد بعد"]]
            pest_active = [p for p in pest_recs if p["state"] == "بانتظار التشيك"]
            rep_lines.append(f"• *🪲 طلبات دواء الحشرات ({len(pest_recs)}):*")
            if pest_waiting:
                rep_lines.append(f"  - باقي عند العامل ما وصل ({len(pest_waiting)}): {fast_list(pest_waiting)}")
            if pest_active:
                rep_lines.append(f"  - وصل الغرفة ونشيك بعد 3 أيام ({len(pest_active)}): {fast_list(pest_active)}")

    if done_checks:
        rep_lines.append(f"\n*✅ غرف شيكنا عليها وصارت نظيفة ({len(done_checks)}):*")
        rep_lines.append(build_grouped_by_floor(done_checks, False))

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
                clean_summary_lines.append(f"  - {f_info['name']}: كل الغرف نظيفة ({max_r}/{max_r}) 🌟")
            else:
                clean_summary_lines.append(
                    f"  - {f_info['name']}: {len(c_codes)} من {max_r} نظيفة ({compress_room_ranges(c_codes)})"
                )
        if clean_summary_lines:
            rep_lines.append("\n*🌟 الغرف النظيفة في كل دور:*")
            rep_lines.extend(clean_summary_lines)

    if fixed_reps:
        rep_lines.append(f"\n*✔️ أعطال تصلّحت اليوم ({len(fixed_reps)}):*")
        for fx in fixed_reps:
            rep_lines.append(f"• {fx['loc']} : {fx['item']} ✓")

    rep_lines.append(f"\nولكم جزيل الشكر والتقدير،\n*المشرف: {sup_label}*")

    full_report = "\n".join(rep_lines)
    st.markdown(
        f'<a href="{wa_app_url(full_report)}" class="wa-btn">📄 3. أرسل التقرير الكامل للمدير 📲</a>',
        unsafe_allow_html=True,
    )

    with st.expander("👁️ قراءة التقرير أو تجربة سريعة"):
        st.text_area("التقرير:", value=full_report, height=200, label_visibility="collapsed")
        sim_c1, sim_c2 = st.columns(2)
        with sim_c1:
            if st.button("🚀 تشغيل تجربة", key="btn_run_demo", use_container_width=True):
                inject_demo_scenario()
                st.rerun()
        with sim_c2:
            if st.button("🧹 مسح التجربة", key="btn_clear_demo", use_container_width=True):
                clear_demo_scenario()
                st.rerun()

    if st.button("🌅 يوم جديد (حفظ المعلق)", use_container_width=True):
        with db["lock"]:
            db["repairs"] = [r for r in db["repairs"] if r["status"] == "مفتوح"]
            db["followups"] = [
                f
                for f in db["followups"]
                if f["state"] in ["بانتظار التشيك", "📦 بانتظار تسليم المبيد", "⚠️ لم يُسلّم المبيد بعد"]
            ]
            save_db()
        st.session_state.pop("last_saved", None)
        st.session_state["floor_done_msg"] = ""
        st.rerun()

    if st.checkbox("تأكيد مسح كل السجلات"):
        if st.button("🗑️ مسح الكل", use_container_width=True):
            with db["lock"]:
                db["repairs"].clear()
                db["followups"].clear()
                db["history"].clear()
                save_db()
            st.session_state.pop("last_saved", None)
            st.session_state["floor_done_msg"] = ""
            st.rerun()
