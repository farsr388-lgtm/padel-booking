from datetime import datetime, timedelta, timezone
import json
import os
import threading
import urllib.parse
import uuid
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. الإعدادات الأساسية
# ==============================================================================
KSA_TZ = timezone(timedelta(hours=3))
LOCATION_TAG = "سكن جامعة 3"
SUPERVISOR_NAME = "فارس العتيبي"
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

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

st.set_page_config(
    page_title="سكن جامعة 3",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 2. التصميم النظيف للجوال (ضبط الأعمدة 50/50 + إخفاء تداخل النص)
# ==============================================================================
st.markdown(
    """
<style>
header[data-testid="stHeader"], #MainMenu, footer, iframe[height="0"] { display: none !important; }

/* إخفاء عبارة Press Enter to apply المتداخلة مع العربي */
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
    padding: 0.4rem 0.65rem 2rem 0.65rem !important;
    margin: 0 auto !important;
}

/* خانة رقم الغرفة الكبيرة الواضحة */
input[type="text"] {
    font-size: 19px !important;
    font-weight: 900 !important;
    text-align: center !important;
    height: 50px !important;
    border-radius: 14px !important;
    background-color: #111827 !important;
    color: #10b981 !important;
    border: 2px solid #10b981 !important;
}

/* ضبط الأعمدة في الجوال لتكون 50% لكل عمود بدون خروج عن الشاشة */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    width: 100% !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    width: calc(50% - 4px) !important;
    flex: 1 1 calc(50% - 4px) !important;
    min-width: 0 !important;
    max-width: calc(50% - 4px) !important;
}

/* أزرار كبيرة متساوية العرض */
div.stButton { width: 100% !important; }
div.stButton > button {
    height: 50px !important;
    width: 100% !important;
    padding: 0 4px !important;
    font-size: 0.95em !important;
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

/* تمييز لوني هادئ: أزرق للصيانة، عنبري للإنذار، أخضر للنظيفة */
div.st-key-b_elec button, div.st-key-b_ac button,
div.st-key-b_plumb button, div.st-key-b_pest button {
    background: rgba(14, 165, 233, 0.12) !important;
    border-color: rgba(56, 189, 248, 0.4) !important;
}
div.st-key-b_heat button, div.st-key-b_clean button, div.st-key-b_both button {
    background: rgba(245, 158, 11, 0.11) !important;
    border-color: rgba(251, 191, 36, 0.4) !important;
}
div.st-key-b_star button {
    background: rgba(16, 185, 129, 0.15) !important;
    border-color: #10b981 !important;
    color: #6ee7b7 !important;
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
    margin: 6px 0 3px 0;
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

# إجبار الآيفون على فتح لوحة الأرقام الكبيرة (1-9) عند لمس الخانة
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


# ==============================================================================
# 4. دوال الحفظ بضغطة واحدة
# ==============================================================================
def record_item(kind: str, label: str):
    raw_room = st.session_state.get("room_box", "").strip()
    if not raw_room:
        st.session_state["err_msg"] = "⚠️ اكتب رقم الغرفة أولاً"
        return

    st.session_state["err_msg"] = ""
    loc = format_room(raw_room)
    ts = now_str()

    with db["lock"]:
        if kind == "maint":
            for r in db["repairs"]:
                if r["loc"] == loc and r["item"] == label and r["status"] == "مفتوح":
                    st.session_state["last_saved"] = {
                        "kind": "maint",
                        "loc": loc,
                        "label": label,
                        "time": r["time"],
                        "repeat": r["repeat"],
                        "dup": True,
                    }
                    st.session_state["room_box"] = ""
                    return

            h_key = f"{loc}_{label}"
            db["history"][h_key] = db["history"].get(h_key, 0) + 1
            rep = db["history"][h_key]

            tid = uuid.uuid4().hex[:8]
            db["repairs"].append({
                "id": tid,
                "loc": loc,
                "item": label,
                "time": ts,
                "closed": "",
                "status": "مفتوح",
                "repeat": rep,
            })
            db["repairs"] = db["repairs"][-MAX_RECORDS:]

            fid = None
            if "مبيد" in label:
                fid = uuid.uuid4().hex[:8]
                db["followups"].append({
                    "id": fid,
                    "loc": loc,
                    "cat": "مبيد",
                    "detail": f"مبيد حشرات (مرة {rep})",
                    "time": ts,
                    "state": "بانتظار التشيك",
                    "count": rep,
                })
                db["followups"] = db["followups"][-MAX_RECORDS:]

            st.session_state["undo"] = ("maint", tid, fid, h_key)
            st.session_state["last_saved"] = {
                "kind": "maint",
                "loc": loc,
                "label": label,
                "time": ts,
                "repeat": rep,
                "dup": False,
            }

        else:
            h_key = f"{loc}_{kind}"
            db["history"][h_key] = db["history"].get(h_key, 0) + 1
            cnt = db["history"][h_key]

            is_star = kind == "star"
            fid = uuid.uuid4().hex[:8]
            db["followups"].append({
                "id": fid,
                "loc": loc,
                "cat": "نظيفة" if is_star else "إنذار",
                "detail": label,
                "time": ts,
                "state": "غرفة نظيفة 🌟" if is_star else "بانتظار التشيك",
                "count": cnt,
            })
            db["followups"] = db["followups"][-MAX_RECORDS:]

            st.session_state["undo"] = ("viol", fid, None, h_key)
            st.session_state["last_saved"] = {
                "kind": "viol",
                "loc": loc,
                "label": label,
                "time": ts,
                "repeat": cnt,
                "dup": False,
            }

        save_db()
    st.session_state["room_box"] = ""


def undo_last():
    item = st.session_state.pop("undo", None)
    if not item:
        return
    kind, tid, fid, h_key = item
    with db["lock"]:
        if kind == "maint":
            db["repairs"] = [r for r in db["repairs"] if r["id"] != tid]
        if fid:
            db["followups"] = [f for f in db["followups"] if f["id"] != fid]
        if h_key in db["history"]:
            db["history"][h_key] = max(0, db["history"][h_key] - 1)
        save_db()
    st.session_state.pop("last_saved", None)


# ==============================================================================
# 5. الواجهة (ورقة تسجيل + مهام + تقرير)
# ==============================================================================
open_reps = [r for r in db["repairs"] if r["status"] == "مفتوح"]
fixed_reps = [r for r in db["repairs"] if r["status"] == "تم الإصلاح"]
pending_checks = [f for f in db["followups"] if f["state"] == "بانتظار التشيك"]

st.markdown(
    f"""
    <div class="top-bar">
        <span>🏢 {LOCATION_TAG}</span>
        <span>🔴 {len(open_reps)} &nbsp;|&nbsp; 🔍 {len(pending_checks)} &nbsp;|&nbsp; ✅ {len(fixed_reps)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "✏️ تسجيل سريع",
    f"⏳ المهام ({len(open_reps) + len(pending_checks)})",
    "📄 التقرير",
])

# --- التبويب 1: ورقة التسجيل السريعة ---
with tab1:
    st.text_input(
        "رقم الغرفة",
        placeholder="رقم الغرفة (مثل 301)",
        key="room_box",
        label_visibility="collapsed",
    )

    if st.session_state.get("err_msg"):
        st.warning(st.session_state["err_msg"])

    st.markdown('<div class="sec-lbl">🛠️ الصيانة:</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.button("🔌 كهرباء", key="b_elec", on_click=record_item, args=("maint", "كهربائي / فيش"), use_container_width=True)
        st.button("🚰 سباكة", key="b_plumb", on_click=record_item, args=("maint", "سباكة / صنبور"), use_container_width=True)
    with c2:
        st.button("❄️ مكيف", key="b_ac", on_click=record_item, args=("maint", "مكيف AC"), use_container_width=True)
        st.button("🪲 مبيد حشرات", key="b_pest", on_click=record_item, args=("maint", "مبيد حشرات"), use_container_width=True)

    st.markdown('<div class="sec-lbl">📋 المتابعة والنظافة:</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.button("⚡ إنذار سخان", key="b_heat", on_click=record_item, args=("warn", "إنذار سخان"), use_container_width=True)
        st.button("⚠️ سخان ونظافة", key="b_both", on_click=record_item, args=("warn", "إنذار سخان ونظافة"), use_container_width=True)
    with c4:
        st.button("🗑️ إنذار نظافة", key="b_clean", on_click=record_item, args=("warn", "إنذار نظافة"), use_container_width=True)
        st.button("🌟 غرفة نظيفة", key="b_star", on_click=record_item, args=("star", "غرفة نظيفة ومميزة"), use_container_width=True)

    if "last_saved" in st.session_state:
        s = st.session_state["last_saved"]
        rep_note = f" (تكرار {s['repeat']})" if s["repeat"] > 1 else ""
        status_txt = "⏳ مسجل مسبقاً:" if s["dup"] else "✅ تم الحفظ:"

        st.markdown(
            f'<div class="ok-card">{status_txt} {s["loc"]} — {s["label"]}{rep_note}</div>',
            unsafe_allow_html=True,
        )

        if s["kind"] == "maint":
            wa_txt = f"*{LOCATION_TAG} — صيانة*\n• الموقع: {s['loc']}\n• الطلب: {s['label']}{rep_note}\n• الوقت: {s['time']}"
            wa_link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_txt)}"
            st.markdown(
                f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 إرسال واتساب</a>',
                unsafe_allow_html=True,
            )

        if "undo" in st.session_state:
            st.button("↩️ تراجع عن آخر ضغطة", on_click=undo_last, use_container_width=True)

# --- التبويب 2: المهام والتشيك ---
with tab2:
    if not open_reps and not pending_checks:
        st.info("✨ لا توجد مهام معلقة حالياً.")

    for r in reversed(open_reps):
        col_a, col_b = st.columns([2.2, 1])
        rep_b = f" • تكرار {r['repeat']}" if r.get("repeat", 1) > 1 else ""
        col_a.markdown(
            f"<div class='task-card'><b>{r['loc']}</b> — {r['item']}<br><small style='color:#94a3b8;'>📅 {r['time']}{rep_b}</small></div>",
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
        for f in reversed(pending_checks):
            col_a, col_b = st.columns([2.2, 1])
            col_a.markdown(
                f"<div class='task-card'><b>{f['loc']}</b> — {f['detail']}<br><small style='color:#94a3b8;'>📅 {f['time']}</small></div>",
                unsafe_allow_html=True,
            )
            if col_b.button("تشيك ✓", key=f"chk_{f['id']}", use_container_width=True):
                with db["lock"]:
                    f["state"] = "تم التشيك ✓"
                    save_db()
                st.rerun()

# --- التبويب 3: التقرير اليومي ---
with tab3:
    open_txt = "\n".join([f"• {r['loc']}: {r['item']} ({r['time']})" for r in open_reps]) or "• لا يوجد"
    fixed_txt = "\n".join([f"• {r['loc']}: {r['item']} ✓ ({r['closed']})" for r in fixed_reps]) or "• لا يوجد"
    pest_txt = "\n".join([f"• {f['loc']}: {f['detail']} — {f['state']}" for f in db["followups"] if f["cat"] == "مبيد"]) or "• لا يوجد"
    warn_txt = "\n".join([f"• {f['loc']}: {f['detail']} (تكرار {f['count']}) — {f['state']}" for f in db["followups"] if f["cat"] == "إنذار"]) or "• لا يوجد"
    star_txt = "\n".join([f"• {f['loc']}: نظيفة ومميزة 🌟" for f in db["followups"] if f["cat"] == "نظيفة"]) or "• لا يوجد"

    report = f"""*{LOCATION_TAG}*
*المشرف: {SUPERVISOR_NAME}*

*🛠️ الصيانة:*
قيد التنفيذ ({len(open_reps)}):
{open_txt}
تم الإصلاح ({len(fixed_reps)}):
{fixed_txt}

*🪲 مبيد الحشرات:*
{pest_txt}

*⚠️ الإنذارات:*
{warn_txt}

*🌟 غرف نظيفة ومميزة:*
{star_txt}"""

    st.text_area("التقرير:", value=report, height=240, label_visibility="collapsed")
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
