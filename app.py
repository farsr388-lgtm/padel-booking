from datetime import datetime, timedelta, timezone
import json
import os
import threading
import urllib.parse
import uuid
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. الإعدادات الأساسية وخريطة الأدوار
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العصيمي"
DATA_FILE = "sakan_clean.json"
MAX_RECORDS = 150

FLOOR_MAP = {
    "1": "الدور M2",
    "2": "الدور M",
    "3": "الدور الأول",
    "4": "الدور الثاني",
    "5": "الدور الثالث",
    "6": "الدور الرابع",
}

M2_ROOMS = [str(100 + i) for i in range(1, 17)]  # 101 إلى 116 (16 غرفة)
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

st.set_page_config(
    page_title="سكن جامعة 3",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 2. التصميم النظيف المتجاوب للجوال (يدعم شبكات 2 و 3 و 4 أعمدة بدون قص)
# ==============================================================================
st.markdown(
    """
<style>
header[data-testid="stHeader"], #MainMenu, footer, iframe[height="0"] { display: none !important; }
div[data-testid="InputInstructions"] { display: none !important; }

html, body, .stApp {
    direction: rtl;
    text-align: right;
    background-color: #0b0f19 !important;
    color: #f8fafc !important;
    font-family: -apple-system, BlinkMacSystemFont, "Cairo", sans-serif;
    overflow-x: hidden !important;
}

.block-container {
    max-width: 440px !important;
    width: 100% !important;
    padding: 0.4rem 0.6rem 2rem 0.6rem !important;
    margin: 0 auto !important;
}

/* خانة رقم الغرفة الكبيرة */
div.st-key-room_box input {
    font-size: 20px !important;
    font-weight: 900 !important;
    text-align: center !important;
    height: 50px !important;
    border-radius: 14px !important;
    background-color: #111827 !important;
    color: #10b981 !important;
    border: 2px solid #10b981 !important;
}

/* خانة الصيانة الحرة الصغيرة */
div.st-key-custom_maint input {
    font-size: 16px !important;
    height: 44px !important;
    border-radius: 12px !important;
    background-color: #111827 !important;
    color: #f8fafc !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
}

/* توزيع مرن للأعمدة (يعمل مع 2 أو 3 أو 4 أعمدة في شاشة الآيفون) */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 5px !important;
    width: 100% !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    flex: 1 1 0% !important;
    min-width: 0 !important;
    width: auto !important;
}

/* الأزرار الأساسية */
div.stButton { width: 100% !important; }
div.stButton > button {
    height: 52px !important;
    width: 100% !important;
    padding: 0 3px !important;
    font-size: 0.96em !important;
    font-weight: 800 !important;
    border-radius: 13px !important;
    margin-bottom: 3px !important;
    background: #161f30 !important;
    color: #f8fafc !important;
    border: 1.5px solid rgba(255, 255, 255, 0.14) !important;
    white-space: nowrap !important;
}
div.stButton > button:active {
    background: #10b981 !important;
    color: #022c22 !important;
}

/* أزرار شبكة M2 (101 - 116) مدمجة وسريعة اللمس */
div[class*="st-key-m2_"] button {
    height: 40px !important;
    font-size: 0.88em !important;
    border-radius: 10px !important;
    background: #111827 !important;
}

/* ألوان هادئة لتمييز المهام اليومية */
div.st-key-b_heater button, div.st-key-b_clean button, div.st-key-b_both button {
    background: rgba(245, 158, 11, 0.13) !important;
    border-color: rgba(251, 191, 36, 0.45) !important;
}
div.st-key-b_pest button {
    background: rgba(168, 85, 247, 0.14) !important;
    border-color: rgba(192, 132, 252, 0.48) !important;
}
div.st-key-b_star button {
    height: 44px !important;
    background: rgba(16, 185, 129, 0.14) !important;
    border-color: #10b981 !important;
    color: #6ee7b7 !important;
}

/* أزرار الصيانة الخفيفة */
div.st-key-m_ac button, div.st-key-m_leak button,
div.st-key-m_elec button, div.st-key-m_add button {
    height: 44px !important;
    font-size: 0.86em !important;
    background: rgba(14, 165, 233, 0.11) !important;
    border-color: rgba(56, 189, 248, 0.38) !important;
}

button[data-baseweb="tab"] {
    flex: 1 !important;
    justify-content: center !important;
    font-weight: 800 !important;
    font-size: 0.9em !important;
}

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-weight: 800;
    font-size: 0.9em;
}
.sec-lbl {
    font-size: 0.82em;
    color: #94a3b8;
    font-weight: 800;
    margin: 7px 0 3px 0;
}
.ok-card {
    background: rgba(16, 185, 129, 0.14);
    border: 1.5px solid #10b981;
    border-radius: 12px;
    padding: 9px;
    margin-top: 6px;
    color: #6ee7b7;
    text-align: center;
    font-weight: 800;
    font-size: 0.92em;
}
.task-card {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 11px;
    padding: 9px 10px;
    margin-bottom: 5px;
    font-size: 0.9em;
}
.wa-btn {
    display: block;
    background: #10b981 !important;
    color: #022c22 !important;
    text-align: center;
    padding: 12px;
    border-radius: 12px;
    font-weight: 900;
    text-decoration: none !important;
    margin-top: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# فتح لوحة الأرقام الكبيرة في الآيفون عند لمس خانة رقم الغرفة
components.html(
    """
    <script>
    const forceKeypad = () => {
        window.parent.document.querySelectorAll('input[type="text"]').forEach(el => {
            if (el.placeholder && el.placeholder.includes('رقم الغرفة')) {
                el.setAttribute('inputmode', 'numeric');
                el.setAttribute('pattern', '[0-9]*');
            }
        });
    };
    forceKeypad();
    new MutationObserver(forceKeypad).observe(window.parent.document.body, { childList: true, subtree: true });
    </script>
    """,
    height=0,
)


# ==============================================================================
# 3. قاعدة البيانات البسيطة
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


def now_str() -> str:
    return (
        datetime.now(KSA_TZ)
        .strftime("%m/%d - %I:%M %p")
        .replace("AM", "ص")
        .replace("PM", "م")
    )


def format_room(raw: str) -> str:
    clean = raw.strip().translate(ARABIC_DIGITS)
    digits = "".join(filter(str.isdigit, clean))
    if len(digits) >= 3:
        floor = FLOOR_MAP.get(digits[0], f"الدور {digits[0]}")
        return f"غرفة {digits} ({floor})"
    return f"غرفة {digits}" if digits else clean


def get_m2_badge(room_num: str) -> str:
    """إظهار نقطة ملونة بجانب رقم الغرفة في شبكة M2 إذا كان عليها سجل اليوم"""
    loc = format_room(room_num)
    for f in reversed(db["followups"]):
        if f["loc"] == loc:
            if f["cat"] == "نظيفة":
                return f"🟢 {room_num}"
            if f["cat"] == "مبيد":
                return f"🟣 {room_num}"
            return f"🟠 {room_num}"
    for r in reversed(db["repairs"]):
        if r["loc"] == loc and r["status"] == "مفتوح":
            return f"🔵 {room_num}"
    return room_num


def pick_m2_room(room_num: str):
    st.session_state["room_box"] = room_num
    st.session_state["err_msg"] = ""


# ==============================================================================
# 4. دوال التسجيل السريع (اليومي + الصيانة الخفيفة)
# ==============================================================================
def record_daily(cat: str, label: str):
    raw_room = st.session_state.get("room_box", "").strip()
    if not raw_room:
        st.session_state["err_msg"] = "⚠️ اختر الغرفة أو اكتب رقمها أولاً"
        return

    st.session_state["err_msg"] = ""
    loc = format_room(raw_room)
    ts = now_str()

    with db["lock"]:
        h_key = f"{loc}_{cat}"
        db["history"][h_key] = db["history"].get(h_key, 0) + 1
        cnt = db["history"][h_key]

        is_star = cat == "نظيفة"
        fid = uuid.uuid4().hex[:8]
        db["followups"].append({
            "id": fid,
            "loc": loc,
            "cat": cat,
            "detail": label,
            "time": ts,
            "state": "غرفة نظيفة 🌟" if is_star else "بانتظار التشيك",
            "count": cnt,
        })
        db["followups"] = db["followups"][-MAX_RECORDS:]
        save_db()

        st.session_state["undo"] = ("daily", None, fid, h_key)
        st.session_state["last_saved"] = {
            "kind": "daily",
            "loc": loc,
            "label": label,
            "time": ts,
            "repeat": cnt,
            "dup": False,
        }
    st.session_state["room_box"] = ""


def record_maint(issue_label: str, from_custom: bool = False):
    raw_room = st.session_state.get("room_box", "").strip()
    if not raw_room:
        st.session_state["err_msg"] = "⚠️ اختر الغرفة أو اكتب رقمها أولاً"
        return

    if from_custom:
        issue_label = st.session_state.get("custom_maint", "").strip()
        if not issue_label:
            st.session_state["err_msg"] = "⚠️ اكتب ملاحظة الصيانة أولاً"
            return

    st.session_state["err_msg"] = ""
    loc = format_room(raw_room)
    ts = now_str()

    with db["lock"]:
        for r in db["repairs"]:
            if r["loc"] == loc and r["item"] == issue_label and r["status"] == "مفتوح":
                st.session_state["last_saved"] = {
                    "kind": "maint",
                    "loc": loc,
                    "label": issue_label,
                    "time": r["time"],
                    "repeat": r["repeat"],
                    "dup": True,
                }
                st.session_state["room_box"] = ""
                if from_custom:
                    st.session_state["custom_maint"] = ""
                return

        h_key = f"{loc}_{issue_label}"
        db["history"][h_key] = db["history"].get(h_key, 0) + 1
        rep = db["history"][h_key]

        tid = uuid.uuid4().hex[:8]
        db["repairs"].append({
            "id": tid,
            "loc": loc,
            "item": issue_label,
            "time": ts,
            "closed": "",
            "status": "مفتوح",
            "repeat": rep,
        })
        db["repairs"] = db["repairs"][-MAX_RECORDS:]
        save_db()

        st.session_state["undo"] = ("maint", tid, None, h_key)
        st.session_state["last_saved"] = {
            "kind": "maint",
            "loc": loc,
            "label": issue_label,
            "time": ts,
            "repeat": rep,
            "dup": False,
        }

    st.session_state["room_box"] = ""
    if from_custom:
        st.session_state["custom_maint"] = ""


def undo_last():
    item = st.session_state.pop("undo", None)
    if not item:
        return
    kind, tid, fid, h_key = item
    with db["lock"]:
        if tid:
            db["repairs"] = [r for r in db["repairs"] if r["id"] != tid]
        if fid:
            db["followups"] = [f for f in db["followups"] if f["id"] != fid]
        if h_key in db["history"]:
            db["history"][h_key] = max(0, db["history"][h_key] - 1)
        save_db()
    st.session_state.pop("last_saved", None)


# ==============================================================================
# 5. الواجهة (خريطة M2 + أزرارك الأربعة + الصيانة الخفيفة)
# ==============================================================================
open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]
pending_checks = [f for f in db["followups"] if f["state"] == "بانتظار التشيك"]

st.markdown(
    f"""
    <div class="top-bar">
        <span>🏢 {LOCATION_TAG}</span>
        <span>🔍 {len(pending_checks)} &nbsp;|&nbsp; 🛠️ {len(open_reps)} &nbsp;|&nbsp; ✅ {len(fixed_reps)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "✏️ الجولة",
    f"⏳ المهام ({len(pending_checks) + len(open_reps)})",
    "📄 التقرير",
])

# --- التبويب 1: الجولة الميدانية ---
with tab1:
    st.text_input(
        "رقم الغرفة",
        placeholder="رقم الغرفة (مثل 101 أو 305)",
        key="room_box",
        label_visibility="collapsed",
    )

    if st.session_state.get("err_msg"):
        st.warning(st.session_state["err_msg"])

    # خريطة دور M2 السريعة (16 غرفة: 101 إلى 116) قابلة للفتح والطي بلمسة
    with st.expander("🗺️ خريطة دور M2 السريعة (101 — 116)", expanded=True):
        for row_i in range(0, 16, 4):
            cols = st.columns(4)
            for col_i in range(4):
                rm = M2_ROOMS[row_i + col_i]
                cols[col_i].button(
                    get_m2_badge(rm),
                    key=f"m2_{rm}",
                    on_click=pick_m2_room,
                    args=(rm,),
                    use_container_width=True,
                )

    # 1. أزرارك اليومية الأربعة الأساسية
    st.markdown('<div class="sec-lbl">⚡ الإجراء اليومي:</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.button("🔌 سحب سخان", key="b_heater", on_click=record_daily, args=("سحب سخان", "سحب سخان"), use_container_width=True)
        st.button("⚠️ سخان ونظافة", key="b_both", on_click=record_daily, args=("سخان ونظافة", "إنذار سخان ونظافة"), use_container_width=True)
    with c2:
        st.button("🗑️ إنذار نظافة", key="b_clean", on_click=record_daily, args=("إنذار نظافة", "إنذار نظافة"), use_container_width=True)
        st.button("🪲 طلب دواء", key="b_pest", on_click=record_daily, args=("مبيد", "طلب دواء (مبيد حشرات)"), use_container_width=True)

    st.button("🌟 غرفة نظيفة ومميزة", key="b_star", on_click=record_daily, args=("نظيفة", "غرفة نظيفة ومميزة"), use_container_width=True)

    # 2. الصيانة النادرة / البلاغات الخفيفة من الجوال
    st.markdown('<div class="sec-lbl">🛠️ صيانة خفيفة (عند الحاجة):</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.button("❄️ تنقيط مكيف", key="m_ac", on_click=record_maint, args=("تنقيط مكيف",), use_container_width=True)
    with m2:
        st.button("💧 تهريب خفيف", key="m_leak", on_click=record_maint, args=("تهريب خفيف",), use_container_width=True)
    with m3:
        st.button("⚡ كهرباء", key="m_elec", on_click=record_maint, args=("كهرباء / فيش",), use_container_width=True)

    cm1, cm2 = st.columns([2.6, 1])
    with cm1:
        st.text_input(
            "ملاحظة صيانة أخرى",
            placeholder="أو اكتب ملاحظة صيانة أخرى هنا...",
            key="custom_maint",
            label_visibility="collapsed",
        )
    with cm2:
        st.button("➕ حفظ", key="m_add", on_click=record_maint, args=("", True), use_container_width=True)

    # إشعار الحفظ + واتساب + تراجع
    if "last_saved" in st.session_state:
        s = st.session_state["last_saved"]
        rep_note = f" (تكرار {s['repeat']})" if s["repeat"] > 1 else ""
        status_txt = "⏳ مسجل مسبقاً:" if s["dup"] else "✅ تم الحفظ:"

        st.markdown(
            f'<div class="ok-card">{status_txt} {s["loc"]} — {s["label"]}{rep_note}</div>',
            unsafe_allow_html=True,
        )

        if s["kind"] == "maint":
            wa_txt = f"*{LOCATION_TAG} — صيانة*\n• الموقع: {s['loc']}\n• الملاحظة: {s['label']}{rep_note}\n• الوقت: {s['time']}"
            wa_link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_txt)}"
            st.markdown(
                f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 إرسال واتساب</a>',
                unsafe_allow_html=True,
            )

        if "undo" in st.session_state:
            st.button("↩️ تراجع عن آخر ضغطة", on_click=undo_last, use_container_width=True)

# --- التبويب 2: المهام والتشيك ---
with tab2:
    if not pending_checks and not open_reps:
        st.info("✨ لا توجد غرف بانتظار التشيك أو صيانة مفتوحة حالياً.")

    if pending_checks:
        st.markdown("##### 🔍 غرف للمراجعة والتشيك:")
        for f in reversed(pending_checks):
            col_a, col_b = st.columns([2.2, 1])
            rep_b = f" • مرة {f['count']}" if f.get("count", 1) > 1 else ""
            col_a.markdown(
                f"<div class='task-card'><b>{f['loc']}</b> — {f['detail']}<br><small style='color:#94a3b8;'>📅 {f['time']}{rep_b}</small></div>",
                unsafe_allow_html=True,
            )
            if col_b.button("تشيك ✓", key=f"chk_{f['id']}", use_container_width=True):
                with db["lock"]:
                    f["state"] = "تم التشيك ✓"
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

# --- التبويب 3: التقرير اليومي ---
with tab3:
    heater_recs = [f for f in db["followups"] if f["cat"] == "سحب سخان"]
    clean_recs = [f for f in db["followups"] if f["cat"] == "إنذار نظافة"]
    both_recs = [f for f in db["followups"] if f["cat"] == "سخان ونظافة"]
    pest_recs = [f for f in db["followups"] if f["cat"] == "مبيد"]
    star_recs = [f for f in db["followups"] if f["cat"] == "نظيفة"]

    heater_txt = "\n".join([f"• {f['loc']} (تكرار {f['count']}) — {f['state']}" for f in heater_recs]) or "• لا يوجد"
    clean_txt = "\n".join([f"• {f['loc']} (تكرار {f['count']}) — {f['state']}" for f in clean_recs]) or "• لا يوجد"
    both_txt = "\n".join([f"• {f['loc']} (تكرار {f['count']}) — {f['state']}" for f in both_recs]) or "• لا يوجد"
    pest_txt = "\n".join([f"• {f['loc']} (مرة {f['count']}) — {f['state']}" for f in pest_recs]) or "• لا يوجد"
    star_txt = "\n".join([f"• {f['loc']} 🌟" for f in star_recs]) or "• لا يوجد"

    maint_open_txt = "\n".join([f"• {r['loc']}: {r['item']} ({r['time']})" for r in open_reps]) or "• لا يوجد"
    maint_done_txt = "\n".join([f"• {r['loc']}: {r['item']} ✓" for r in fixed_reps]) or "• لا يوجد"

    report = f"""*{LOCATION_TAG}*
*المشرف: {SUPERVISOR_NAME}*

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

    st.text_area("التقرير:", value=report, height=250, label_visibility="collapsed")
    wa_rep = f"https://api.whatsapp.com/send?text={urllib.parse.quote(report)}"
    st.markdown(
        f'<a href="{wa_rep}" target="_blank" class="wa-btn">📲 إرسال التقرير واتساب</a>',
        unsafe_allow_html=True,
    )

    if st.button("🌅 بدء يوم جديد (تصفير المنجز)", use_container_width=True):
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
