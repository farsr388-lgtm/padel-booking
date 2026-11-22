from datetime import datetime, timedelta, timezone
import json
import os
import threading
import urllib.parse
import uuid
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. الثوابت وخريطة الأدوار (سكن جامعة 3 — فارس العصيمي)
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
DATA_FILE = "sakan_u3_mobile.json"
MAX_RECORDS = 150

FLOOR_MAP = {
    "1": "الدور M2",
    "2": "الدور M",
    "3": "الدور الأول",
    "4": "الدور الثاني",
    "5": "الدور الثالث",
    "6": "الدور الرابع",
}

FLOOR_ROWS = [
    [("1", "M2"), ("2", "M"), ("3", "دور 1")],
    [("4", "دور 2"), ("5", "دور 3"), ("6", "دور 4")],
]

ARABIC_TO_EN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

st.set_page_config(
    page_title="سكن جامعة 3",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
header[data-testid="stHeader"], #MainMenu, footer, iframe[height="0"] { display: none !important; }

/* مقاس الجوال المريح بيد واحدة */
.block-container {
    max-width: 400px !important;
    padding: 0.35rem 0.65rem 2.5rem 0.65rem !important;
    margin: 0 auto !important;
}
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
    background-color: #0b0f19 !important;
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Cairo", sans-serif;
}

/* منع تكبير شاشة الجوال عند فتح الكيبورد */
input[type="text"] {
    font-size: 16px !important;
    height: 44px !important;
    border-radius: 12px !important;
    background-color: #111827 !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
}

/* أزرار مريحة للإبهام */
div.stButton > button {
    min-height: 52px !important;
    font-size: 0.98em !important;
    font-weight: 800 !important;
    border-radius: 14px !important;
    width: 100% !important;
    padding: 0 6px !important;
    margin-bottom: 4px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(16, 185, 129, 0.42) !important;
    transition: all 0.1s ease !important;
}
div.stButton > button:active, div.stButton > button:hover {
    background: #10b981 !important;
    color: #022c22 !important;
}

/* إبقاء الأعمدة بجانب بعضها دائماً في الجوال */
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

/* تنسيق التبويبات للجوال */
button[data-baseweb="tab"] {
    flex: 1 !important;
    justify-content: center !important;
    font-weight: 800 !important;
    font-size: 0.92em !important;
    padding: 8px 4px !important;
}

/* شريط علوي مدمج في سطر واحد */
.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 8px 10px;
    margin-bottom: 8px;
}
.top-title {
    font-weight: 900;
    font-size: 0.95em;
    color: #f8fafc;
}
.top-kpis {
    display: flex;
    gap: 6px;
    font-size: 0.8em;
    font-weight: 800;
}
.kpi-chip {
    background: #0b0f19;
    padding: 3px 7px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

/* بطاقة الغرفة النشطة */
.room-hero {
    background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
    border: 2px solid #10b981;
    border-radius: 14px;
    padding: 10px 12px;
    margin-bottom: 8px;
    text-align: center;
}
.room-hero-num {
    font-size: 1.28em;
    font-weight: 900;
    color: #ecfdf5;
}
.room-hero-note {
    font-size: 0.82em;
    color: #a7f3d0;
    margin-top: 2px;
}
.sec-title {
    font-size: 0.84em;
    font-weight: 800;
    color: #94a3b8;
    margin: 8px 0 4px 0;
}
.success-box {
    background: rgba(16, 185, 129, 0.14);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 10px;
    margin: 6px 0;
    color: #6ee7b7;
    font-size: 0.94em;
}
.crimson-box {
    background: rgba(190, 18, 60, 0.16);
    border: 1px solid rgba(244, 63, 94, 0.45);
    border-radius: 12px;
    padding: 10px;
    margin: 6px 0;
    color: #fda4af;
    font-size: 0.94em;
}
.task-row {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 11px;
    padding: 10px 11px;
    font-size: 0.92em;
    margin-bottom: 5px;
}
.task-hotspot {
    background: rgba(245, 158, 11, 0.14) !important;
    border: 1.5px solid #f59e0b !important;
}
.wa-btn {
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 13px;
    font-weight: 900;
    font-size: 1.03em;
    text-decoration: none !important;
    margin: 6px 0 8px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# تفعيل لوحة الأرقام الفورية على الجوال لحقل الغرفة اليدوي
components.html(
    """
    <script>
    const setNumPad = () => {
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        inputs.forEach(inp => {
            if (inp.placeholder && inp.placeholder.includes('السطح')) {
                inp.setAttribute('inputmode', 'numeric');
            }
        });
    };
    setNumPad();
    new MutationObserver(setNumPad).observe(window.parent.document.body, { childList: true, subtree: true });
    </script>
    """,
    height=0,
)


# ==============================================================================
# 2. التخزين المحلي والتعرف المكاني
# ==============================================================================
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "repairs": data.get("repairs", []),
                    "followups": data.get("followups", []),
                    "room_history": data.get("room_history", {}),
                }
        except Exception:
            pass
    return {"repairs": [], "followups": [], "room_history": {}}


@st.cache_resource
def get_db():
    saved = load_data()
    return {
        "lock": threading.Lock(),
        "repairs": saved["repairs"],
        "followups": saved["followups"],
        "room_history": saved["room_history"],
    }


db = get_db()


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "repairs": db["repairs"],
                    "followups": db["followups"],
                    "room_history": db["room_history"],
                },
                f,
                ensure_ascii=False,
            )
    except Exception:
        pass


def now_stamp() -> str:
    return (
        datetime.now(KSA_TZ)
        .strftime("%m/%d - %I:%M %p")
        .replace("AM", "ص")
        .replace("PM", "م")
    )


def clean_digits(raw_txt: str) -> str:
    txt = str(raw_txt).strip().translate(ARABIC_TO_EN_DIGITS)
    return "".join(filter(str.isdigit, txt))


def parse_room(raw_txt: str) -> str:
    clean = str(raw_txt).strip().translate(ARABIC_TO_EN_DIGITS)
    digits = "".join(filter(str.isdigit, clean))
    if len(digits) >= 3:
        floor = FLOOR_MAP.get(digits[0], f"الدور {digits[0]}")
        return f"غرفة {digits} ({floor})"
    if digits:
        return f"غرفة {digits}"
    return clean


def get_room_past_summary(loc_clean: str) -> str:
    matches = []
    for k, v in db["room_history"].items():
        if k.startswith(f"{loc_clean}_") and v > 0:
            label = k.split("_", 1)[1]
            matches.append(f"{label} ×{v}")
    return " | ".join(matches)


def get_three_room_strip(active_raw: str) -> list[str]:
    digits = clean_digits(active_raw)
    if len(digits) >= 3:
        num = int(digits)
        floor_start = int(digits[0]) * 100 + 1
        start = max(floor_start, num - 1)
        return [str(start), str(start + 1), str(start + 2)]
    return ["301", "302", "303"]


def get_adjacent_rooms(active_raw: str) -> tuple[str, str]:
    digits = clean_digits(active_raw)
    if digits:
        num = int(digits)
        prev_r = str(num - 1) if num > 101 else ""
        next_r = str(num + 1)
        return prev_r, next_r
    return "", "301"


# ==============================================================================
# 3. منطق التسجيل السريع والتراجع (Undo Engine)
# ==============================================================================
if "active_room" not in st.session_state:
    st.session_state["active_room"] = "301"


def set_active_room(room_val: str):
    val = str(room_val).strip().translate(ARABIC_TO_EN_DIGITS)
    if val:
        st.session_state["active_room"] = val


def apply_custom_room():
    typed = st.session_state.get("custom_room_input", "").strip()
    if typed:
        set_active_room(typed)
        st.session_state["custom_room_input"] = ""


def add_repair(raw_room: str, issue: str, default_sev: str, record_undo: bool = True) -> str:
    loc = parse_room(raw_room)
    ts = now_stamp()

    if st.session_state.get("override_half_sev", False):
        severity = "🟡 نص حالة"
        st.session_state["override_half_sev"] = False
    else:
        severity = default_sev

    with db["lock"]:
        for r in db["repairs"]:
            if r["loc"] == loc and r["item"] == issue and r["status"] == "مفتوح":
                prev_sev = r.get("severity", "🔴 طارئ")
                r["pings"] = r.get("pings", 1) + 1
                r["severity"] = severity
                save_data()
                st.session_state["last_action"] = {
                    "kind": "maint",
                    "loc": loc,
                    "item": issue,
                    "severity": severity,
                    "time": r["time"],
                    "repeat": r.get("repeat_count", 1),
                    "dup": True,
                }
                if record_undo:
                    st.session_state["undo_action"] = {
                        "type": "ping_maint",
                        "label": f"تذكير {loc}",
                        "ticket_id": r["id"],
                        "prev_sev": prev_sev,
                    }
                return r["id"]

        key = f"{loc}_{issue}"
        db["room_history"][key] = db["room_history"].get(key, 0) + 1
        rep_cnt = db["room_history"][key]

        ticket_id = uuid.uuid4().hex[:8]
        db["repairs"].append({
            "id": ticket_id,
            "loc": loc,
            "item": issue,
            "severity": severity,
            "time": ts,
            "closed_time": "",
            "status": "مفتوح",
            "repeat_count": rep_cnt,
        })
        db["repairs"] = db["repairs"][-MAX_RECORDS:]

        linked_f_id = None
        if "مبيد حشرات" in issue:
            linked_f_id = uuid.uuid4().hex[:8]
            db["followups"].append({
                "id": linked_f_id,
                "loc": loc,
                "category": "مبيد حشرات",
                "detail": f"طلب/تسليم مبيد حشرات (مرة {rep_cnt})",
                "created_at": ts,
                "checked_at": "",
                "state": "بانتظار التشيك",
                "count": rep_cnt,
            })
            db["followups"] = db["followups"][-MAX_RECORDS:]

        save_data()
        st.session_state["last_action"] = {
            "kind": "maint",
            "loc": loc,
            "item": issue,
            "severity": severity,
            "time": ts,
            "repeat": rep_cnt,
            "dup": False,
        }
        if record_undo:
            st.session_state["undo_action"] = {
                "type": "add_maint",
                "label": f"{loc} ({issue})",
                "ticket_id": ticket_id,
                "followup_id": linked_f_id,
                "hist_key": key,
            }
        return ticket_id


def add_followup(raw_room: str, category: str, detail: str):
    loc = parse_room(raw_room)
    ts = now_stamp()

    with db["lock"]:
        key = f"{loc}_{category}"
        db["room_history"][key] = db["room_history"].get(key, 0) + 1
        cnt = db["room_history"][key]

        is_clean = category == "غرفة نظيفة"
        f_id = uuid.uuid4().hex[:8]
        db["followups"].append({
            "id": f_id,
            "loc": loc,
            "category": category,
            "detail": detail,
            "created_at": ts,
            "checked_at": ts if is_clean else "",
            "state": "غرفة نظيفة ومميزة 🌟" if is_clean else "بانتظار المراجعة",
            "count": cnt,
        })
        db["followups"] = db["followups"][-MAX_RECORDS:]
        save_data()

        st.session_state["last_action"] = {
            "kind": "viol",
            "loc": loc,
            "item": detail,
            "time": ts,
            "repeat": cnt,
            "dup": False,
        }
        st.session_state["undo_action"] = {
            "type": "add_followup",
            "label": f"{loc} ({detail})",
            "followup_id": f_id,
            "hist_key": key,
        }


def execute_undo():
    undo = st.session_state.pop("undo_action", None)
    if not undo:
        return

    with db["lock"]:
        u_type = undo["type"]
        if u_type == "add_maint":
            db["repairs"] = [r for r in db["repairs"] if r["id"] != undo["ticket_id"]]
            if undo.get("followup_id"):
                db["followups"] = [
                    f for f in db["followups"] if f["id"] != undo["followup_id"]
                ]
            hk = undo.get("hist_key")
            if hk and hk in db["room_history"]:
                db["room_history"][hk] = max(0, db["room_history"][hk] - 1)
                if db["room_history"][hk] == 0:
                    del db["room_history"][hk]
            st.session_state.pop("last_action", None)

        elif u_type == "ping_maint":
            for r in db["repairs"]:
                if r["id"] == undo["ticket_id"]:
                    r["pings"] = max(1, r.get("pings", 1) - 1)
                    r["severity"] = undo["prev_sev"]
                    break
            st.session_state.pop("last_action", None)

        elif u_type == "close_maint":
            for r in db["repairs"]:
                if r["id"] == undo["ticket_id"]:
                    r["status"] = "مفتوح"
                    r["closed_time"] = ""
                    break

        elif u_type == "add_followup":
            db["followups"] = [
                f for f in db["followups"] if f["id"] != undo["followup_id"]
            ]
            hk = undo.get("hist_key")
            if hk and hk in db["room_history"]:
                db["room_history"][hk] = max(0, db["room_history"][hk] - 1)
                if db["room_history"][hk] == 0:
                    del db["room_history"][hk]
            st.session_state.pop("last_action", None)

        elif u_type == "update_followup":
            for f in db["followups"]:
                if f["id"] == undo["followup_id"]:
                    f["state"] = undo["prev_state"]
                    f["checked_at"] = undo["prev_checked_at"]
                    f["count"] = undo["prev_count"]
                    break
            if undo.get("spawned_ticket_id"):
                db["repairs"] = [
                    r for r in db["repairs"] if r["id"] != undo["spawned_ticket_id"]
                ]

        save_data()


# ==============================================================================
# 4. الواجهة الرئيسية (ترتيب الجوال بيد واحدة)
# ==============================================================================
open_list = [r for r in db["repairs"] if r["status"] == "مفتوح"]
fixed_list = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]
pending_list = [
    f
    for f in db["followups"]
    if f["state"] in ["بانتظار التشيك", "بانتظار المراجعة", "مخالفة مستمرة"]
]

# شريط علوي مدمج في سطر واحد لتوفير مساحة شاشة الجوال
st.markdown(
    f"""
    <div class="top-bar">
        <div class="top-title">🏢 {LOCATION_TAG}</div>
        <div class="top-kpis">
            <span class="kpi-chip" style="color:#fda4af;">🔴 {len(open_list)}</span>
            <span class="kpi-chip" style="color:#fcd34d;">🔍 {len(pending_list)}</span>
            <span class="kpi-chip" style="color:#6ee7b7;">✅ {len(fixed_list)}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "undo_action" in st.session_state:
    st.button(
        f"↩️ تراجع: {st.session_state['undo_action']['label']}",
        key="btn_undo",
        on_click=execute_undo,
    )

tab_field, tab_tasks, tab_report = st.tabs([
    "⚡ الجولة",
    f"⏳ المهام ({len(open_list) + len(pending_list)})",
    "📄 التقرير",
])

# ------------------------------------------------------------------------------
# التبويب 1: الجولة الميدانية (ترتيب الجوال بالإبهام)
# ------------------------------------------------------------------------------
with tab_field:
    active_raw = st.session_state["active_room"]
    active_loc = parse_room(active_raw)
    past_info = get_room_past_summary(active_loc)
    past_html = (
        f'<div class="room-hero-note">⚠️ سجل سابق: {past_info}</div>'
        if past_info
        else '<div class="room-hero-note">المس الإجراء مباشرة</div>'
    )

    st.markdown(
        f"""
        <div class="room-hero">
            <div class="room-hero-num">📍 {active_loc}</div>
            {past_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # أزرار التنقل العريضة (50% / 50%) للغرفة السابقة والتالية
    prev_r, next_r = get_adjacent_rooms(active_raw)
    nav_c1, nav_c2 = st.columns(2)
    with nav_c1:
        if prev_r:
            st.button(
                f"⏮️ السابقة ({prev_r})",
                key="btn_prev_room",
                on_click=set_active_room,
                args=(prev_r,),
            )
    with nav_c2:
        if next_r:
            st.button(
                f"⏭️ التالية ({next_r})",
                key="btn_next_room",
                on_click=set_active_room,
                args=(next_r,),
            )

    # 3 أزرار عريضة للغرف المتجاورة
    room_strip = get_three_room_strip(active_raw)
    r_cols = st.columns(3)
    for idx, r_num in enumerate(room_strip):
        btn_label = f"• {r_num} •" if r_num == clean_digits(active_raw) else r_num
        r_cols[idx].button(
            btn_label,
            key=f"rm_pill_{r_num}",
            on_click=set_active_room,
            args=(r_num,),
        )

    # إشعار آخر حركة + زر واتساب يظهر في المنتصف قريباً من الإبهام
    if "last_action" in st.session_state:
        act = st.session_state["last_action"]
        rep_txt = f" (تكرار {act['repeat']})" if act["repeat"] > 1 else ""

        if act["kind"] == "maint":
            wa_msg = (
                f"*{LOCATION_TAG} — صيانة*\n• الموقع: {act['loc']}\n• الطلب:"
                f" {act['item']} [{act['severity']}]{rep_txt}\n• الوقت: {act['time']}"
            )
            wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_msg)}"

            if act["dup"]:
                st.markdown(
                    f'<div class="crimson-box"><b>⏳ مسجل مسبقاً:</b> {act["loc"]} —'
                    f' {act["item"]}</div><a href="{wa_url}" target="_blank"'
                    ' class="wa-btn">📲 إرسال تذكير واتساب</a>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="success-box"><b>✅ تم الحفظ:</b> {act["loc"]} —'
                    f' {act["item"]} [{act["severity"]}]{rep_txt}</div><a'
                    f' href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال'
                    " واتساب</a>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div class="success-box"><b>✅ تم القيد:</b> {act["loc"]} —'
                f' {act["item"]} (سجل: {act["repeat"]})</div>',
                unsafe_allow_html=True,
            )

    # القسم الأول: الصيانة (شبكة 2×2 عريضة)
    st.markdown('<div class="sec-title">🛠️ الصيانة والمبيدات:</div>', unsafe_allow_html=True)
    m_c1, m_c2 = st.columns(2)
    with m_c1:
        st.button(
            "🔌 كهرباء / فيش",
            key="act_elec",
            on_click=add_repair,
            args=(active_raw, "كهربائي / فيش", "🔴 طارئ"),
        )
        st.button(
            "🚰 سباكة / صنبور",
            key="act_plumb",
            on_click=add_repair,
            args=(active_raw, "سباكة / صنبور", "🔴 طارئ"),
        )
    with m_c2:
        st.button(
            "❄️ مكيف AC",
            key="act_ac",
            on_click=add_repair,
            args=(active_raw, "مكيف AC", "🔴 طارئ"),
        )
        st.button(
            "🪲 مبيد حشرات",
            key="act_pest",
            on_click=add_repair,
            args=(active_raw, "مبيد حشرات", "🟡 نص حالة"),
        )

    st.checkbox("🟡 اجعل البلاغ القادم (نص حالة)", key="override_half_sev")

    # القسم الثاني: الإنذارات والنظافة (شبكة 2×2 عريضة + زر التميز)
    st.markdown('<div class="sec-title">📋 الإنذارات والنظافة:</div>', unsafe_allow_html=True)
    v_c1, v_c2 = st.columns(2)
    with v_c1:
        st.button(
            "⚡ إنذار سخان",
            key="act_heater",
            on_click=add_followup,
            args=(active_raw, "إنذار", "إنذار سخان"),
        )
        st.button(
            "⚠️ سخان ونظافة",
            key="act_both",
            on_click=add_followup,
            args=(active_raw, "إنذار", "إنذار سخان ونظافة"),
        )
    with v_c2:
        st.button(
            "🗑️ إنذار نظافة",
            key="act_clean_warn",
            on_click=add_followup,
            args=(active_raw, "إنذار", "إنذار نظافة"),
        )
        st.button(
            "🟡 غرفة نص نص",
            key="act_half_clean",
            on_click=add_followup,
            args=(active_raw, "متابعة نظافة", "غرفة نص نص"),
        )

    st.button(
        "🌟 غرفة نظيفة ومميزة",
        key="act_clean_star",
        on_click=add_followup,
        args=(active_raw, "غرفة نظيفة", "غرفة نظيفة ومميزة"),
    )

    # اختيار الدور (صفّان 3×2 عريضة) + خانة كتابة رقم بعيد أو موقع
    st.markdown('<div class="sec-title">🏢 الانتقال السريع لدور أو موقع:</div>', unsafe_allow_html=True)
    for row_idx, f_row in enumerate(FLOOR_ROWS):
        f_cols = st.columns(3)
        for col_idx, (f_code, f_lbl) in enumerate(f_row):
            f_cols[col_idx].button(
                f_lbl,
                key=f"flr_{row_idx}_{f_code}",
                on_click=set_active_room,
                args=(f"{f_code}01",),
            )

    st.text_input(
        "غرفة بعيدة أو موقع:",
        placeholder="اكتب رقم غرفة أو موقع مثل: السطح",
        key="custom_room_input",
        label_visibility="collapsed",
        on_change=apply_custom_room,
    )

# ------------------------------------------------------------------------------
# التبويب 2: المهام المفتوحة والتشيك الميداني
# ------------------------------------------------------------------------------
with tab_tasks:
    if not open_list and not pending_list:
        st.info("✨ لا توجد مهام مفتوحة أو غرف بانتظار التشيك حالياً.")

    if open_list:
        st.markdown(f"##### 🛠️ صيانة قيد التنفيذ ({len(open_list)}):")
        for r in reversed(open_list):
            c1, c2 = st.columns([2.4, 1.1])
            rep_cnt = r.get("repeat_count", 1)
            is_hot = rep_cnt >= 3
            row_cls = "task-row task-hotspot" if is_hot else "task-row"
            rep_b = f" • {'🔥' if is_hot else '🔁'} تكرار {rep_cnt}" if rep_cnt > 1 else ""
            c1.markdown(
                f"<div class='{row_cls}'><b>{r['loc']}</b> — {r['item']}"
                f" [{r['severity']}]<br><small style='color:#94a3b8;'>📅"
                f" {r['time']}{rep_b}</small></div>",
                unsafe_allow_html=True,
            )
            if c2.button("تم ✓", key=f"done_{r['id']}"):
                with db["lock"]:
                    r["status"] = "تم الإصلاح"
                    r["closed_time"] = now_stamp()
                    save_data()
                st.session_state["undo_action"] = {
                    "type": "close_maint",
                    "label": f"إنجاز {r['loc']}",
                    "ticket_id": r["id"],
                }
                st.rerun()

    if pending_list:
        st.markdown("---")
        st.markdown(f"##### 🔍 بانتظار التشيك والمراجعة ({len(pending_list)}):")
        for f in reversed(pending_list):
            is_hot_f = f.get("count", 1) >= 3
            f_cls = "task-row task-hotspot" if is_hot_f else "task-row"
            hot_tag = " 🔥" if is_hot_f else ""
            st.markdown(
                f"<div class='{f_cls}'><b>{f['loc']}</b> — {f['detail']}{hot_tag}<br><small"
                f" style='color:#94a3b8;'>📅 قُيّد: {f['created_at']}"
                + (f" | آخر تشيك: {f['checked_at']}" if f["checked_at"] else "")
                + "</small></div>",
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns(2)
            if f["category"] == "مبيد حشرات":
                if b1.button("✅ تم التشيك", key=f"ok_{f['id']}"):
                    prev_s, prev_c, prev_cnt = f["state"], f["checked_at"], f["count"]
                    with db["lock"]:
                        f["state"] = "تم التشيك - سليم ✓"
                        f["checked_at"] = now_stamp()
                        save_data()
                    st.session_state["undo_action"] = {
                        "type": "update_followup",
                        "label": f"تشيك {f['loc']}",
                        "followup_id": f["id"],
                        "prev_state": prev_s,
                        "prev_checked_at": prev_c,
                        "prev_count": prev_cnt,
                    }
                    st.rerun()
                if b2.button("🔄 إعادة رش", key=f"re_{f['id']}"):
                    prev_s, prev_c, prev_cnt = f["state"], f["checked_at"], f["count"]
                    with db["lock"]:
                        f["checked_at"] = now_stamp()
                        save_data()
                    spawned_id = add_repair(
                        f["loc"], "مبيد حشرات (إعادة رش)", "🔴 طارئ", record_undo=False
                    )
                    st.session_state["undo_action"] = {
                        "type": "update_followup",
                        "label": f"إعادة رش {f['loc']}",
                        "followup_id": f["id"],
                        "prev_state": prev_s,
                        "prev_checked_at": prev_c,
                        "prev_count": prev_cnt,
                        "spawned_ticket_id": spawned_id,
                    }
                    st.rerun()
            else:
                if b1.button("🌟 تحسنت ✓", key=f"imp_{f['id']}"):
                    prev_s, prev_c, prev_cnt = f["state"], f["checked_at"], f["count"]
                    with db["lock"]:
                        f["state"] = "تحسنت بعد الإنذار 🌟"
                        f["checked_at"] = now_stamp()
                        save_data()
                    st.session_state["undo_action"] = {
                        "type": "update_followup",
                        "label": f"تحسّن {f['loc']}",
                        "followup_id": f["id"],
                        "prev_state": prev_s,
                        "prev_checked_at": prev_c,
                        "prev_count": prev_cnt,
                    }
                    st.rerun()
                if b2.button("🚨 مستمرة", key=f"cont_{f['id']}"):
                    prev_s, prev_c, prev_cnt = f["state"], f["checked_at"], f["count"]
                    with db["lock"]:
                        f["state"] = "مخالفة مستمرة"
                        f["count"] += 1
                        f["checked_at"] = now_stamp()
                        save_data()
                    st.session_state["undo_action"] = {
                        "type": "update_followup",
                        "label": f"مخالفة مستمرة {f['loc']}",
                        "followup_id": f["id"],
                        "prev_state": prev_s,
                        "prev_checked_at": prev_c,
                        "prev_count": prev_cnt,
                    }
                    st.rerun()

# ------------------------------------------------------------------------------
# التبويب 3: التقرير اليومي الجاهز للواتساب
# ------------------------------------------------------------------------------
with tab_report:
    open_lines = (
        "\n".join([
            f"• {r['loc']}: {r['item']} [{r['severity']}] ({r['time']})"
            + (f" (تكرار {r['repeat_count']})" if r.get("repeat_count", 1) > 1 else "")
            for r in open_list
        ])
        or "• لا يوجد"
    )

    fixed_lines = (
        "\n".join([
            f"• {r['loc']}: {r['item']} ✓ ({r.get('closed_time', '')})"
            for r in fixed_list
        ])
        or "• لا يوجد"
    )

    recurring_items = [
        f"{r['loc']} ({r['item']} ×{r['repeat_count']})"
        for r in db["repairs"]
        if r.get("repeat_count", 1) > 1
    ]
    recurring_summary = (
        "، ".join(dict.fromkeys(recurring_items)) if recurring_items else "لا يوجد"
    )

    pest_recs = [f for f in db["followups"] if f["category"] == "مبيد حشرات"]
    pest_lines = (
        "\n".join([
            f"• {f['loc']}: ({f['created_at']}) — {f['state']}"
            for f in pest_recs
        ])
        or "• لا يوجد"
    )

    warn_recs = [
        f
        for f in db["followups"]
        if f["category"] in ["إنذار", "متابعة نظافة"] and "تحسنت" not in f["state"]
    ]
    warn_lines = (
        "\n".join([
            f"• {f['loc']}: {f['detail']} (تكرار {f['count']})"
            for f in warn_recs
        ])
        or "• لا يوجد"
    )

    imp_recs = [f for f in db["followups"] if "تحسنت" in f["state"]]
    imp_lines = (
        "\n".join([f"• {f['loc']}: تحسنت بعد ({f['detail']})" for f in imp_recs])
        or "• لا يوجد"
    )

    good_recs = [f for f in db["followups"] if f["category"] == "غرفة نظيفة"]
    good_lines = (
        "\n".join([f"• {f['loc']}: نظيفة ومميزة 🌟" for f in good_recs])
        or "• لا يوجد"
    )

    report = f"""*{LOCATION_TAG}*
*المشرف: {SUPERVISOR_NAME}*

*🛠️ الصيانة:*
قيد التنفيذ ({len(open_list)}):
{open_lines}
تم الإصلاح ({len(fixed_list)}):
{fixed_lines}
- المتكرر: {recurring_summary}

*🪲 مبيد الحشرات ({len(set(f['loc'] for f in pest_recs))} غرف):*
{pest_lines}

*⚠️ الإنذارات والمتابعة ({len(warn_recs)}):*
{warn_lines}

*🌟 تحسنت بعد الإنذار ({len(imp_recs)}):*
{imp_lines}

*✨ غرف نظيفة ومميزة ({len(good_recs)}):*
{good_lines}"""

    st.text_area("التقرير الجاهز:", value=report, height=250)

    wa_rep = f"https://api.whatsapp.com/send?text={urllib.parse.quote(report)}"
    st.markdown(
        f'<a href="{wa_rep}" target="_blank" class="wa-btn">📲 إرسال التقرير عبر واتساب</a>',
        unsafe_allow_html=True,
    )

    if st.button("🌅 بدء يوم جديد (حفظ المعلق والتكرار)"):
        with db["lock"]:
            db["repairs"] = [r for r in db["repairs"] if r["status"] == "مفتوح"]
            db["followups"] = [
                f
                for f in db["followups"]
                if f["state"] in ["بانتظار التشيك", "بانتظار المراجعة", "مخالفة مستمرة"]
            ]
            save_data()
        st.session_state.pop("last_action", None)
        st.session_state.pop("undo_action", None)
        st.rerun()

    if st.checkbox("تأكيد مسح كل السجلات"):
        if st.button("🗑️ مسح شامل من الصفر"):
            with db["lock"]:
                db["repairs"].clear()
                db["followups"].clear()
                db["room_history"].clear()
                save_data()
            st.session_state.pop("last_action", None)
            st.session_state.pop("undo_action", None)
            st.rerun()
