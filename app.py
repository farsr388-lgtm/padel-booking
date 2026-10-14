import html
import hmac
import re
import urllib.parse
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client

# ==============================================================================
# 1. إعداد الصفحة ودوال التنظيف والحماية الصارمة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | تقاسم عروض بلوم - نيوتن",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def clean_html(raw_html: str) -> str:
    """تنظيف صارم للمسافات البادئة والمسافات غير المرئية لضمان عمل الـ CSS والـ HTML بنسبة 100%."""
    if not raw_html:
        return ""
    normalized = raw_html.replace("\u00a0", " ")
    return "\n".join(
        line.strip() for line in normalized.strip().splitlines() if line.strip()
    )


def sanitize_phone_number(raw_input: str) -> str:
    """تنظيف وتوحيد أرقام الجوال ومعالجة الأرقام العربية والرموز ومفتاح الدولة 966."""
    if not raw_input:
        return ""

    arabic_indic_table = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
        "01234567890123456789",
    )
    cleaned = re.sub(
        r"[\s\-\+\(\)]", "", raw_input.strip().translate(arabic_indic_table)
    )

    if cleaned.startswith("00966"):
        cleaned = cleaned[5:]
    elif cleaned.startswith("966"):
        cleaned = cleaned[3:]

    if cleaned.startswith("5"):
        cleaned = f"0{cleaned}"
    elif not cleaned.startswith("0") and len(cleaned) == 9:
        cleaned = f"0{cleaned}"

    return cleaned


# تتبع Clarity + حارس JavaScript الحي لاستئصال اللون الأحمر من BaseWeb وتثبيت بطاقات الاختيار
components.html(
    clean_html("""
    <script type="text/javascript">
        try {
            (function(c,l,a,r,i,t,y){
                c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
            })(window.parent, window.parent.document, "clarity", "script", "ytjnujh8td");

            const doc = window.parent.document;
            const enforceEmeraldUI = () => {
                const radios = doc.querySelectorAll('label[data-baseweb="radio"]');
                radios.forEach(label => {
                    const input = label.querySelector('input[type="radio"]');
                    const mark = label.querySelector('div:first-child');
                    const isChecked = input && input.checked;

                    label.style.setProperty('background-color', isChecked ? '#064e3b' : '#111827', 'important');
                    label.style.setProperty('border', isChecked ? '2px solid #10b981' : '1.5px solid rgba(255,255,255,0.14)', 'important');
                    label.style.setProperty('border-radius', '10px', 'important');
                    label.style.setProperty('padding', '10px 12px', 'important');
                    label.style.setProperty('width', '100%', 'important');
                    label.style.setProperty('box-sizing', 'border-box', 'important');
                    label.style.setProperty('margin', '0', 'important');
                    label.style.setProperty('box-shadow', isChecked ? '0 0 14px rgba(16,185,129,0.25)' : 'none', 'important');

                    if (mark) {
                        mark.style.setProperty('background-color', isChecked ? '#10b981' : 'rgba(255,255,255,0.08)', 'important');
                        mark.style.setProperty('border-color', isChecked ? '#10b981' : 'rgba(255,255,255,0.3)', 'important');
                    }
                });
            };

            enforceEmeraldUI();
            const observer = new MutationObserver(() => enforceEmeraldUI());
            observer.observe(doc.body, { childList: true, subtree: true, attributes: true });
        } catch(e) {}
    </script>
"""),
    height=0,
    width=0,
)

# ==============================================================================
# 2. محرك الأنماط البصرية الجذري (Unified Progress Bar & Zero Red Accent)
# ==============================================================================
st.markdown(
    clean_html("""
<style>
:root {
    color-scheme: dark;
    --primary: #10b981;
    --primary-glow: rgba(16, 185, 129, 0.28);
    --active-bg: #064e3b;
    --card-bg: #111827;
    --border-color: rgba(255, 255, 255, 0.14);
}

/* 1. إخفاء كافة أشرطة وشعارات Streamlit الافتراضية */
header[data-testid="stHeader"],
#MainMenu,
footer,
div[data-testid="stStatusWidget"],
.stDeployButton,
[data-testid="stToolbar"],
div[class*="viewerBadge"],
[class*="viewerBadge"],
[class*="manageApp"],
div[data-testid="stDecoration"],
[data-testid="InputInstructions"],
[data-testid="stWidgetInstructions"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* 2. ضبط عرض الصفحة لشاشات الجوال */
.block-container {
    padding-top: 0.3rem !important;
    padding-bottom: 2rem !important;
    padding-left: 10px !important;
    padding-right: 10px !important;
    max-width: 100% !important;
    margin: 0 auto !important;
}
@media (min-width: 480px) {
    .block-container {
        max-width: 430px !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
    }
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, "Cairo", sans-serif;
    direction: rtl;
    text-align: right;
    background-color: #0b0f19 !important;
    color: #f8fafc !important;
    -webkit-tap-highlight-color: transparent;
}

/* 3. البطاقة العلوية وشريط التقدم المتصل (لا يوحي بالنقر نهائياً) */
.top-card,
.progress-wrapper,
.sensory-strip,
.ingredient-thumb {
    pointer-events: none !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    cursor: default !important;
}

.top-card {
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    text-align: center;
    width: 100%;
    box-sizing: border-box;
}
.brand-badge {
    color: var(--primary);
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75em;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 5px;
}
.headline {
    font-size: 1.22em;
    font-weight: 900;
    color: #ffffff;
    margin: 0;
}
.sub-headline {
    font-size: 0.82em;
    font-weight: 600;
    color: #94a3b8;
    margin: 4px 0 10px 0;
}

/* شريط التقدم الأفقي المتصل بدلاً من المربعات الـ 4 المشتتة */
.progress-status-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78em;
    font-weight: 800;
    margin-bottom: 6px;
    color: #e2e8f0;
}
.progress-track {
    width: 100%;
    height: 10px;
    background: #030712;
    border-radius: 999px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #059669 0%, #10b981 100%);
    border-radius: 999px;
    box-shadow: 0 0 10px var(--primary-glow);
    transition: width 0.4s ease;
}

.centered-section-title {
    text-align: center !important;
    font-size: 0.95em !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    margin-top: 8px !important;
    margin-bottom: 8px !important;
}

/* 4. تحويل خيارات الراديو إلى بطاقات أزرار زمردية واستئصال النقطة الحمراء */
div[data-testid="stRadio"] {
    width: 100% !important;
}
div[data-testid="stRadio"] > div {
    width: 100% !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 8px !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
div[data-testid="stForm"] div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    width: 100% !important;
}

label[data-baseweb="radio"] {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 10px !important;
    padding: 11px 12px !important;
    min-height: 48px !important;
    width: 100% !important;
    margin: 0 !important;
    cursor: pointer !important;
    box-sizing: border-box !important;
    transition: all 0.2s ease !important;
}

label[data-baseweb="radio"] > div:first-child {
    background-color: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    margin-left: 8px !important;
    margin-right: 0 !important;
    flex-shrink: 0 !important;
}

label[data-baseweb="radio"]:has(input:checked) {
    background-color: var(--active-bg) !important;
    border: 2px solid var(--primary) !important;
    box-shadow: 0 0 14px var(--primary-glow) !important;
}

label[data-baseweb="radio"]:has(input:checked) > div:first-child {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
}

label[data-baseweb="radio"] p,
label[data-baseweb="radio"] span {
    color: #e2e8f0 !important;
    font-size: 0.88em !important;
    font-weight: 800 !important;
    margin: 0 !important;
}

/* 5. شريط مواصفات العطر المختار (مدمج وغير قابل للنقر) */
.sensory-strip {
    background: rgba(17, 24, 39, 0.75);
    border-right: 3.5px solid var(--primary);
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    border-left: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0 12px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    width: 100%;
    box-sizing: border-box;
}
.sensory-info {
    display: flex;
    flex-direction: column;
    gap: 3px;
}
.sensory-title {
    font-size: 0.92em;
    font-weight: 900;
    color: #ffffff;
}
.sensory-notes {
    font-size: 0.76em;
    color: #94a3b8;
}
.sensory-price-badge {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 8px;
    padding: 6px 10px;
    text-align: center;
    flex-shrink: 0;
}
.sensory-price-badge b {
    color: var(--primary);
    font-size: 1.05em;
    display: block;
}
.sensory-price-badge span {
    color: #94a3b8;
    font-size: 0.7em;
    text-decoration: line-through;
}

/* 6. حقول الإدخال وزر التثبيت */
div[data-testid="stTextInput"] div[data-baseweb="input"] {
    border: 1.5px solid var(--border-color) !important;
    background-color: var(--card-bg) !important;
    border-radius: 8px !important;
}
div[data-testid="stTextInput"]:focus-within div[data-baseweb="input"] {
    border: 1.5px solid var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15) !important;
}
input {
    caret-color: var(--primary) !important;
    color: #ffffff !important;
    font-size: 0.9em !important;
    padding: 10px 12px !important;
}

div[data-testid="stFormSubmitButton"] > button {
    background: var(--primary) !important;
    color: #022c22 !important;
    font-size: 0.98em !important;
    font-weight: 900 !important;
    height: 50px !important;
    border-radius: 10px !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35) !important;
    width: 100% !important;
    margin-top: 6px !important;
}

/* 7. زر الواتساب النابض في شاشة الخطوة الأخيرة */
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.55), 0 4px 18px rgba(16, 185, 129, 0.35); transform: scale(1); }
    50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0), 0 6px 24px rgba(16, 185, 129, 0.5); transform: scale(1.015); }
}
.wa-link-btn {
    display: block;
    background: var(--primary);
    color: #022c22 !important;
    text-align: center;
    padding: 16px 14px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 1.04em;
    text-decoration: none;
    margin-top: 12px;
    margin-bottom: 8px;
    animation: pulseGlow 2s infinite ease-in-out;
}

/* شارة الخطوة الأخيرة التحذيرية الدافئة في شاشة الواتساب */
.pending-step-badge {
    color: #fef3c7;
    background: rgba(245, 158, 11, 0.16);
    border: 1px solid rgba(245, 158, 11, 0.45);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78em;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 6px;
}

/* رابط الإلغاء الهادئ الصغير في أقصى أسفل شاشة التأكيد */
div:has(> #cancel-link-hook) ~ div[data-testid="stButton"] button {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 4px 10px !important;
    height: auto !important;
    min-height: auto !important;
    margin: 16px auto 0 auto !important;
    display: block !important;
    width: auto !important;
}
div:has(> #cancel-link-hook) ~ div[data-testid="stButton"] button p {
    color: #64748b !important;
    font-size: 0.76em !important;
    text-decoration: underline !important;
    font-weight: 500 !important;
}

/* تنبيه التحقق الكهرماني الدافئ */
@keyframes alertShake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-6px); }
    40%, 80% { transform: translateX(6px); }
}
.warning-pill-shake {
    background: rgba(245, 158, 11, 0.12) !important;
    border: 1.5px solid rgba(245, 158, 11, 0.5) !important;
    color: #fef3c7 !important;
    padding: 12px 14px !important;
    border-radius: 10px !important;
    font-size: 0.86em !important;
    font-weight: 800 !important;
    margin-bottom: 12px !important;
    text-align: center !important;
    animation: alertShake 0.45s ease-in-out !important;
}

.cancellation-card, .waitlist-card, .notice-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 12px;
    font-size: 0.84em;
    color: #cbd5e1;
    text-align: center;
    line-height: 1.55;
    margin: 8px 0;
}

div[data-testid="stTextInput"]:has(input[aria-label="hp"]),
input[aria-label="hp"] { display: none !important; }
</style>
"""),
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. محرك البيانات والربط (Supabase & Catalog Engine)
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client | None:
    try:
        url = str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
        if url.endswith("/rest/v1"):
            url = url[:-8]
        key = str(st.secrets.get("SUPABASE_KEY", "")).strip()
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None


supabase = get_supabase_client()

BASKET_ID = "BLOM-NEWTON-JEDDAH-V13"
BASKET_CAPACITY = 4
UNIFIED_PRICE = 132
ORIGINAL_RETAIL = 265
SAVINGS_AMOUNT = ORIGINAL_RETAIL - UNIFIED_PRICE
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD = str(st.secrets.get("ADMIN_PASSWORD", "")).strip()

PERFUMES: dict[str, dict[str, str]] = {
    "عطر روميو": {
        "en_name": "Romeo",
        "tag": "رجالي فاخر • الأكثر طلباً",
        "notes": "باتشولي نقي، فانيلا، ومسك فاخر",
    },
    "عطر يوجا": {
        "en_name": "Yoga",
        "tag": "هادئ ومنعش • فوّاح",
        "notes": "برغموت إيطالي، مسك نقي، ونرجس",
    },
    "عطر لونار": {
        "en_name": "Lunar",
        "tag": "أناقة للجنسين • ثبات عالي",
        "notes": "عنب أسود، باتشولي، وعنبر دافئ",
    },
    "عطر لاروزيه": {
        "en_name": "Larose",
        "tag": "أنثوي ساحر • ناعم وجذاب",
        "notes": "فانيلا فرنسية، زنبق أبيض، وياسمين",
    },
    "عطر إليسيوم": {
        "en_name": "Elysium",
        "tag": "فخامة ملكية • للمناسبات",
        "notes": "عنبر ملكي، فانيلا، ولافندر بارد",
    },
    "عطر هارت بيت": {
        "en_name": "Heart Beat",
        "tag": "حيوي ورومانسي • جذاب",
        "notes": "كشمش أسود، مسك أبيض، وورد مخملي",
    },
}


@st.cache_data(ttl=5)
def get_confirmed_bookings(basket_key: str) -> list[dict[str, Any]]:
    if not supabase:
        return []
    try:
        res = (
            supabase.table("bookings")
            .select("*")
            .eq("session_day", basket_key)
            .neq("status", "cancelled")
            .order("id")
            .execute()
        )
        return res.data or []
    except Exception:
        return []


# ==============================================================================
# 4. الرأسية التسويقية وشريط التقدم المتصل (لا يوحي بوجود أزرار نهائياً)
# ==============================================================================
@st.fragment(run_every="15s")
def render_live_slots() -> None:
    current_bookings = get_confirmed_bookings(BASKET_ID)
    taken_count = min(len(current_bookings), BASKET_CAPACITY)
    remaining = max(0, BASKET_CAPACITY - taken_count)
    progress_pct = int((taken_count / BASKET_CAPACITY) * 100)

    status_label = (
        f"🔥 باقي {remaining} مقاعد وتكتمل الباقة"
        if remaining > 0
        else "✅ اكتملت الباقة بالكامل"
    )

    st.markdown(
        clean_html(f"""
        <div class="top-card">
            <div class="brand-badge">عروض بلوم (2+2 مجاناً) • جدة</div>
            <div class="headline">تقاسم باقة عطور نيوتن Blom</div>
            <div class="sub-headline">العطر الأصلي بـ <b style="color:#10b981;">{UNIFIED_PRICE} ر.س</b> بدلاً من {ORIGINAL_RETAIL} ر.س (توفير 50%)</div>
            <div class="progress-wrapper">
                <div class="progress-status-row">
                    <span>حالة الباقة: {taken_count} من {BASKET_CAPACITY} محجوز</span>
                    <span style="color:#10b981;">{status_label}</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: {max(12, progress_pct)}%;"></div>
                </div>
            </div>
        </div>
    """),
        unsafe_allow_html=True,
    )


# ==============================================================================
# 5. شاشة الخطوة الأخيرة: إرسال رسالة الواتساب لتثبيت المقعد
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(str(deal.get("name", "")))
    safe_perfume = html.escape(str(deal.get("perfume", "")))
    safe_delivery = html.escape(str(deal.get("delivery", "")))

    fresh_list = get_confirmed_bookings(BASKET_ID)
    current_taken = len(fresh_list)
    remaining_seats = max(0, BASKET_CAPACITY - current_taken)

    if remaining_seats > 0:
        seats_status_msg = f"⏳ باقي {remaining_seats} وينقفل القروب ونطلب فوراً."
    else:
        seats_status_msg = "🔥 اكتملت الـ 4 مقاعد وجاري تنفيذ الطلب!"

    if "توصيل" in deal.get("delivery", ""):
        delivery_details_msg = (
            "• طريقة الاستلام: توصيل مجاني بجدة 🚗\n"
            "• موقعي: (برسل لك دبوس الموقع تحت هذي الرسالة الحين 📍)\n"
            f"• الدفع: {UNIFIED_PRICE} ر.س يد بيد بعد فحص العطر والفاتورة الأصلية 🤝"
        )
        card_delivery_note = "اضغط الزر الأخضر بالأسفل لإرسال طلبك وموقعك عبر الواتساب وتثبيت مقعدك رسمياً."
    else:
        delivery_details_msg = (
            "• طريقة الاستلام: السلام مول (بوابة 5 و 6) 📍\n"
            "• الموعد: السبت (المغرب إلى العشاء: 6:30م – 9:00م) ⏰\n"
            f"• الدفع: {UNIFIED_PRICE} ر.س يد بيد بعد فحص العطر والفاتورة الأصلية 🤝"
        )
        card_delivery_note = "اضغط الزر الأخضر بالأسفل لإرسال رسالة التثبيت عبر الواتساب وتأكيد موعد السلام مول."

    st.markdown(
        clean_html(f"""
        <div class="top-card" style="border-color:var(--primary);">
            <div class="pending-step-badge">⏳ خطوة أخيرة لتثبيت مقعدك</div>
            <div class="headline" style="font-size:1.15em;">يا {safe_name}، أرسل رسالة التأكيد بالواتساب الآن</div>
            <div class="sub-headline" style="color:#cbd5e1 !important; margin-top:6px;">
                العطر المختار: <b style="color:#ffffff;">{safe_perfume}</b> ({UNIFIED_PRICE} ر.س عند الاستلام)
            </div>
        </div>
        <div class="notice-card">
            📲 <b>الرسالة جاهزة ومكتوبة تلقائياً:</b><br>
            {card_delivery_note}
        </div>
    """),
        unsafe_allow_html=True,
    )

    components.html(
        clean_html("""
        <script>
            try {
                if (window.parent && window.parent.clarity) {
                    window.parent.clarity("event", "seat_booked");
                }
            } catch(e) {}
        </script>
    """),
        height=0,
        width=0,
    )

    wa_admin_msg = (
        f"مرحباً 🌿\n"
        f"حجزت حصتي في تطبيق مَقسوم ({UNIFIED_PRICE} ر.س):\n\n"
        f"• الاسم: {deal.get('name')}\n"
        f"• الجوال: {deal.get('phone')}\n"
        f"• العطر: {deal.get('perfume')}\n"
        f"{delivery_details_msg}\n\n"
        f"{seats_status_msg}\n\n"
        f"بانتظار تأكيدك واعتماد حصتي 🌿"
    )
    admin_link = (
        f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_admin_msg)}"
    )

    st.markdown(
        clean_html(
            f'<a href="{admin_link}" target="_blank" class="wa-link-btn">📲 اضغط هنا لإرسال رسالة التثبيت عبر واتساب الآن</a>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown('<div id="cancel-link-hook"></div>', unsafe_allow_html=True)
    if st.button("تراجعت عن الحجز؟ اضغط هنا لإلغاء المقعد والعودة", use_container_width=True):
        booking_id = deal.get("id")
        if supabase:
            if booking_id:
                supabase.table("bookings").update(
                    {"status": "cancelled"}
                ).eq("id", booking_id).execute()
            else:
                supabase.table("bookings").update(
                    {"status": "cancelled"}
                ).eq("phone", deal.get("phone")).eq(
                    "session_day", BASKET_ID
                ).execute()

        get_confirmed_bookings.clear()
        st.session_state.pop("confirmed_deal", None)
        st.session_state["just_cancelled"] = True
        st.rerun()

# ==============================================================================
# 6. شاشة الحجز الرئيسية (بطاقات أزرار واضحة بدون صور مشتتة)
# ==============================================================================
else:
    render_live_slots()

    if st.session_state.get("just_cancelled"):
        st.markdown(
            clean_html("""
            <div class="cancellation-card" style="border-color:#10b981;">
                🌿 <b>تم إلغاء حجزك بنجاح</b><br>
                مقعدك متاح الآن في الباقة، ويمكنك اختيار عطرك من جديد في أي وقت.
            </div>
        """),
            unsafe_allow_html=True,
        )

    st.markdown(
        clean_html(
            '<div class="centered-section-title">1. اضغط على العطر المفضل لك:</div>'
        ),
        unsafe_allow_html=True,
    )

    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed",
    )

    p = PERFUMES[chosen_perfume]

    # شريط معلوماتي أنيق وهادئ بدون صورة مربعة تشتت نقرات العميل
    st.markdown(
        clean_html(f"""
        <div class="sensory-strip">
            <div class="sensory-info">
                <div class="sensory-title">🌿 {chosen_perfume} ({p['en_name']}) — <span style="color:#10b981;font-size:0.85em;">{p['tag']}</span></div>
                <div class="sensory-notes">المكونات: {p['notes']}</div>
            </div>
            <div class="sensory-price-badge">
                <b>{UNIFIED_PRICE} ر.س</b>
                <span>{ORIGINAL_RETAIL} ر.س</span>
            </div>
        </div>
    """),
        unsafe_allow_html=True,
    )

    with st.form(
        "quick_order_form",
        clear_on_submit=False,
        enter_to_submit=False,
        border=False,
    ):
        st.markdown(
            clean_html(
                '<div class="centered-section-title" style="margin-top:0;">2. سجل اسمك ورقمك لتثبيت الحصة:</div>'
            ),
            unsafe_allow_html=True,
        )

        alert_placeholder = st.empty()

        f_name = st.text_input(
            "الاسم الكريم:",
            value=st.session_state.get("saved_name", ""),
            placeholder="الاسم الثنائي",
        )
        f_phone = st.text_input(
            "رقم الجوال:",
            value=st.session_state.get("saved_phone", ""),
            placeholder="05xxxxxxxx",
        )

        st.markdown(
            clean_html(
                '<div class="centered-section-title" style="font-size:0.88em;margin-top:8px;margin-bottom:4px;">3. اختر طريقة الاستلام في جدة:</div>'
            ),
            unsafe_allow_html=True,
        )

        delivery_mode = st.radio(
            "طريقة وموعد الاستلام:",
            [
                f"السلام مول (بوابة 5 و 6) • السبت (المغرب إلى العشاء) — {UNIFIED_PRICE} ر.س",
                f"توصيل مجاني داخل أحياء جدة — {UNIFIED_PRICE} ر.س",
            ],
            key="delivery_mode",
            label_visibility="collapsed",
        )

        st.markdown(
            clean_html("""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:6px;padding:7px;text-align:center;font-size:0.73em;color:#94a3b8;margin:8px 0;">
                🛡️ أصلي 100% • فحص العطر والفاتورة الأصلية قبل الدفع يد بيد
            </div>
        """),
            unsafe_allow_html=True,
        )

        hp = st.text_input("hp", label_visibility="collapsed")
        submit_btn = st.form_submit_button(
            f"تثبيت حصتك الآن ({UNIFIED_PRICE} ر.س عند الاستلام)",
            use_container_width=True,
        )

        if submit_btn and not hp:
            clean_name = f_name.strip()
            clean_phone = sanitize_phone_number(f_phone)

            if len(clean_name) < 2 or not re.match(r"^05\d{8}$", clean_phone):
                alert_placeholder.markdown(
                    clean_html("""
                    <div id="form-top-alert" class="warning-pill-shake">
                        🌿 خطوة أخيرة يا غالي: تأكد من كتابة اسمك الكريم ورقم جوالك (05xxxxxxxx) لنثبت مقعدك فوراً
                    </div>
                """),
                    unsafe_allow_html=True,
                )
                components.html(
                    clean_html("""
                    <script>
                        setTimeout(() => {
                            try {
                                const banner = window.parent.document.getElementById('form-top-alert');
                                if (banner) {
                                    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                }
                            } catch(e) {}
                        }, 50);
                    </script>
                """),
                    height=0,
                    width=0,
                )

            else:
                st.session_state["saved_name"] = clean_name
                st.session_state["saved_phone"] = clean_phone
                st.session_state.pop("just_cancelled", None)

                get_confirmed_bookings.clear()
                fresh_bookings = get_confirmed_bookings(BASKET_ID)

                existing_booking = next(
                    (b for b in fresh_bookings if b.get("phone") == clean_phone),
                    None,
                )

                if existing_booking:
                    client_note = f"BLOM_NEWTON | {chosen_perfume} | {delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"
                    if supabase:
                        try:
                            supabase.table("bookings").update({
                                "name": clean_name,
                                "level": chosen_perfume,
                                "hear_about": delivery_mode[:50],
                                "player_note": client_note,
                            }).eq("id", existing_booking.get("id")).execute()
                        except Exception:
                            pass

                    get_confirmed_bookings.clear()
                    st.session_state["confirmed_deal"] = {
                        "id": existing_booking.get("id"),
                        "name": clean_name,
                        "phone": clean_phone,
                        "perfume": chosen_perfume,
                        "delivery": delivery_mode,
                        "price": UNIFIED_PRICE,
                    }
                    st.rerun()

                elif len(fresh_bookings) >= BASKET_CAPACITY:
                    alert_placeholder.markdown(
                        clean_html("""
                        <div class="waitlist-card">
                            ✨ <b>شكراً جزيلاً لثقتك واهتمامك يا غالي 🌿</b><br>
                            مقاعد هذه الباقة اكتملت للتو بالكامل، وسنتواصل معك عبر الواتساب مع إطلاق السلة القادمة مباشرة.
                        </div>
                    """),
                        unsafe_allow_html=True,
                    )

                else:
                    if not supabase:
                        alert_placeholder.error(
                            "تعذر الاتصال بقاعدة البيانات. يرجى مراجعة إعدادات Secrets."
                        )
                    else:
                        try:
                            client_note = f"BLOM_NEWTON | {chosen_perfume} | {delivery_mode} | PRICE:{UNIFIED_PRICE} | PHONE:{clean_phone}"

                            insert_res = supabase.table("bookings").insert({
                                "name": clean_name,
                                "phone": clean_phone,
                                "session_day": BASKET_ID,
                                "court": 1,
                                "level": chosen_perfume,
                                "status": "confirmed",
                                "payment_status": "pending",
                                "hear_about": delivery_mode[:50],
                                "player_note": client_note,
                            }).execute()

                            new_id = (
                                insert_res.data[0].get("id")
                                if insert_res.data
                                else None
                            )

                            get_confirmed_bookings.clear()

                            st.session_state["confirmed_deal"] = {
                                "id": new_id,
                                "name": clean_name,
                                "phone": clean_phone,
                                "perfume": chosen_perfume,
                                "delivery": delivery_mode,
                                "price": UNIFIED_PRICE,
                            }
                            st.rerun()
                        except Exception as db_err:
                            alert_placeholder.error(
                                f"تعذر إتمام التسجيل في السيرفر: {db_err}"
                            )

# ==============================================================================
# 7. لوحة المشرف المحصنة بنظام التشفير الثنائي UTF-8
# ==============================================================================
if st.query_params.get("manage") == "faris":
    st.markdown("---")
    st.caption("لوحة الإدارة والتحليلات السريعة")
    admin_pin = st.text_input(
        "رمز الدخول السري:", type="password", key="adm_key"
    )

    input_pin_str = str(admin_pin or "").strip()
    target_pwd_str = str(ADMIN_PASSWORD or "").strip()

    is_authenticated = False
    if input_pin_str and target_pwd_str:
        try:
            is_authenticated = hmac.compare_digest(
                input_pin_str.encode("utf-8"), target_pwd_str.encode("utf-8")
            )
        except Exception:
            is_authenticated = False

    if is_authenticated:
        bookings_list = get_confirmed_bookings(BASKET_ID)
        total_count = len(bookings_list)
        paid_count = sum(
            1 for b in bookings_list if b.get("payment_status") == "paid"
        )
        total_val = total_count * UNIFIED_PRICE

        k1, k2, k3 = st.columns(3)
        k1.metric("المقاعد المحجوزة", f"{total_count} / {BASKET_CAPACITY}")
        k2.metric("المحصل (مدفوع)", f"{paid_count * UNIFIED_PRICE} ر.س")
        k3.metric("إجمالي السلة", f"{total_val} ر.س")

        st.markdown("##### قائمة المشتركين:")
        for b in bookings_list:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(
                    f"**{b.get('name')}** | `{b.get('phone')}`\nالعطر:"
                    f" **{b.get('level')}**\nالتسليم: `{b.get('hear_about')}`"
                )
            with c2:
                if b.get("payment_status") == "paid":
                    st.markdown(
                        "<span style='color:var(--primary);"
                        " font-weight:700;'>مدفوع ✓</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button("اعتماد دفع", key=f"pay_{b.get('id')}"):
                        if supabase:
                            (
                                supabase.table("bookings")
                                .update({"payment_status": "paid"})
                                .eq("id", b.get("id"))
                                .execute()
                            )
                        get_confirmed_bookings.clear()
                        st.rerun()

                if st.button("إلغاء المقعد", key=f"cancel_{b.get('id')}"):
                    if supabase:
                        (
                            supabase.table("bookings")
                            .update({"status": "cancelled"})
                            .eq("id", b.get("id"))
                            .execute()
                        )
                    get_confirmed_bookings.clear()
                    st.rerun()
            st.divider()
    elif input_pin_str:
        st.error("رمز الدخول غير صحيح.")
