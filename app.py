import html
import hmac
import math
import re
import urllib.parse
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client

# ==============================================================================
# 1. إعداد الصفحة ودوال التنظيف الصارمة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | تقاسم عروض العطور الفاخرة",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def clean_html(raw_html: str) -> str:
    """تنظيف شامل للمسافات البادئة والمسافات غير المرئية (\u00a0) لضمان سلامة الـ CSS."""
    if not raw_html:
        return ""
    normalized = raw_html.replace("\u00a0", " ")
    return "\n".join(
        line.strip() for line in normalized.strip().splitlines() if line.strip()
    )


def sanitize_phone_number(raw_input: str) -> str:
    """توحيد أرقام الجوال إلى صيغة 05xxxxxxxx."""
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


# ==============================================================================
# 2. الخزنة المركزية والنسخ الاحتياطي الآلي (تطبيق شريحة أمان المعرفة 350)
# معالجة خطأ (275 ر.س بدلاً من 265 ر.س) وخطأ انقطاع السيرفر [Errno -2]
# ==============================================================================
@st.cache_resource
def get_global_store_config() -> dict[str, Any]:
    return {
        "offer_name": "عروض بلوم نيوتن (تقاسم الباقة)",
        "group_size": 2,             # 2 لنظام الثنائيات السريع (1+1) أو 4 للرباعيات (2+2)
        "bundle_cost": 265.0,        # تكلفة باقة الثنائيات (عطرين بـ 265 ر.س) أو الرباعيات (530 ر.س)
        "retail_price": 265,         # سعر العبوة الفردي الرسمي بالسوق
        "target_profit": 0.0,        # الربح المستهدف في الحبة
        "pkg_cost": 0.0,             # 0 ر.س بدون أغلفة إضافية
        "total_inventory": 20,       # إجمالي الكمية المتاحة
        "locker_fee": 15,            # رسوم خزائن ريد بوكس الذكية
        "home_delivery_fee": 25,     # رسوم التوصيل لباب البيت بجدة
    }


@st.cache_resource
def get_fallback_memory_db() -> list[dict[str, Any]]:
    """خزنة نسخ احتياطي محلية تعمل فوراً إذا تعطل اتصال Supabase ([Errno -2])."""
    return []


store_cfg = get_global_store_config()
fallback_db = get_fallback_memory_db()

OFFER_NAME: str = str(store_cfg["offer_name"])
GROUP_SIZE: int = int(store_cfg["group_size"])
BUNDLE_ORIGINAL_COST: float = float(store_cfg["bundle_cost"])
ORIGINAL_RETAIL: int = int(store_cfg["retail_price"])
TARGET_PROFIT_PER_UNIT: float = float(store_cfg["target_profit"])
PACKAGING_COST_PER_UNIT: float = float(store_cfg["pkg_cost"])
TOTAL_INVENTORY_LIMIT: int = int(store_cfg["total_inventory"])
LOCKER_FEE: int = int(store_cfg["locker_fee"])
HOME_DELIVERY_FEE: int = int(store_cfg["home_delivery_fee"])

# المعادلة المحاسبية المصححة (تمنع تجاوز السعر الفردي وتضمن قانون الربع والنصف)
base_unit_cost = BUNDLE_ORIGINAL_COST / GROUP_SIZE
minimum_break_even_price = base_unit_cost + PACKAGING_COST_PER_UNIT
UNIT_SELL_PRICE = int(math.ceil(minimum_break_even_price + TARGET_PROFIT_PER_UNIT))
SAVINGS_AMOUNT = max(0, ORIGINAL_RETAIL - UNIT_SELL_PRICE)

BASKET_ID = "BLOM-NEWTON-JEDDAH-V13"
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD = str(st.secrets.get("ADMIN_PASSWORD", "")).strip()

# ==============================================================================
# 3. محرك الأنماط البصرية الصارم (Pure CSS للقضاء على الدائرة الحمراء في Safari)
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

header[data-testid="stHeader"], #MainMenu, footer,
div[data-testid="stStatusWidget"], .stDeployButton,
[data-testid="stToolbar"], div[class*="viewerBadge"],
[class*="manageApp"], div[data-testid="stDecoration"],
[data-testid="InputInstructions"], [data-testid="stWidgetInstructions"] { 
    display: none !important; 
}

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
        max-width: 435px !important;
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

.top-card, .progress-container, .progress-meta, .sensory-card, .ingredient-thumb {
    pointer-events: none !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    cursor: default !important;
}

.top-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 14px;
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
.headline { font-size: 1.24em; font-weight: 900; color: #ffffff; margin: 0; }
.sub-headline { font-size: 0.84em; font-weight: 700; color: #94a3b8; margin: 4px 0 8px 0; }

.progress-container {
    width: 100%;
    background: #030712;
    border: 1px solid var(--border-color);
    border-radius: 20px;
    height: 10px;
    overflow: hidden;
    margin: 8px 0 6px 0;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #059669, #10b981);
    border-radius: 20px;
    box-shadow: 0 0 10px var(--primary-glow);
    transition: width 0.4s ease;
}
.progress-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.76em;
    font-weight: 800;
    color: #cbd5e1;
    margin-top: 4px;
}
.stock-badge {
    display: inline-block;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #fef3c7;
    font-size: 0.74em;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    margin-top: 6px;
}

.centered-section-title {
    text-align: center !important;
    font-size: 0.96em !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    margin-top: 10px !important;
    margin-bottom: 8px !important;
}

/* الحل الجذري بـ Pure CSS للقضاء على الدائرة الحمراء في جميع المتصفحات */
div[data-testid="stRadio"] { width: 100% !important; }
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 8px !important;
    width: 100% !important;
    margin-bottom: 10px !important;
}
div[data-testid="stForm"] div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    width: 100% !important;
}

div[data-testid="stRadio"] label[data-baseweb="radio"] {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    background-color: var(--card-bg) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    min-height: 46px !important;
    width: 100% !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
}

/* تلوين الدائرة الداخلية بالزمردي بدلاً من الأحمر بـ CSS مباشر */
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    background-color: rgba(255, 255, 255, 0.1) !important;
    border-color: rgba(255, 255, 255, 0.35) !important;
    margin-left: 8px !important;
    margin-right: 0 !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
    background-color: var(--active-bg) !important;
    border: 2px solid var(--primary) !important;
    box-shadow: 0 0 12px var(--primary-glow) !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child > div {
    background-color: #022c22 !important;
}

div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span {
    color: #f8fafc !important;
    font-size: 0.86em !important;
    font-weight: 800 !important;
    margin: 0 !important;
}

.sensory-card {
    background: var(--card-bg);
    border: 1.5px solid rgba(16, 185, 129, 0.4);
    border-radius: 12px;
    padding: 11px 13px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
}
.sensory-top-row { display: flex; align-items: center; gap: 12px; }
.ingredient-thumb {
    width: 66px !important;
    height: 66px !important;
    border-radius: 10px !important;
    object-fit: cover !important;
    border: 1.5px solid var(--primary) !important;
    flex-shrink: 0 !important;
}
.sensory-details { flex-grow: 1; display: flex; flex-direction: column; gap: 2px; }
.sensory-name { font-size: 0.96em; font-weight: 900; color: #ffffff; }
.sensory-tag { font-size: 0.74em; color: var(--primary); font-weight: 800; }
.sensory-notes { font-size: 0.76em; color: #94a3b8; }

.price-chip {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 8px;
    padding: 7px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.78em;
    font-weight: 700;
}

/* إصلاح وضوح نص زر التثبيت الأخضر */
div[data-testid="stFormSubmitButton"] > button {
    background: var(--primary) !important;
    color: #022c22 !important;
    height: 50px !important;
    border-radius: 10px !important;
    border: none !important;
    width: 100% !important;
    margin-top: 8px !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35) !important;
}
div[data-testid="stFormSubmitButton"] > button p,
div[data-testid="stFormSubmitButton"] > button span {
    color: #022c22 !important;
    font-size: 0.98em !important;
    font-weight: 900 !important;
}

@keyframes ctaPulse {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
    70% { box-shadow: 0 0 0 12px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.wa-link-btn {
    display: block;
    background: var(--primary);
    color: #022c22 !important;
    text-align: center;
    padding: 16px 14px;
    border-radius: 12px;
    font-weight: 900;
    font-size: 1.02em;
    text-decoration: none;
    margin-top: 10px;
    margin-bottom: 6px;
    animation: ctaPulse 2s infinite;
}

div:has(> #cancel-link-hook) ~ div[data-testid="stButton"] button {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 6px 12px !important;
    margin: 14px auto 0 auto !important;
    display: block !important;
}
div:has(> #cancel-link-hook) ~ div[data-testid="stButton"] button p {
    color: #64748b !important;
    font-size: 0.76em !important;
    text-decoration: underline !important;
}

.warning-pill-shake {
    background: rgba(245, 158, 11, 0.12) !important;
    border: 1.5px solid rgba(245, 158, 11, 0.45) !important;
    color: #fef3c7 !important;
    padding: 12px 14px !important;
    border-radius: 10px !important;
    font-size: 0.86em !important;
    font-weight: 800 !important;
    margin-bottom: 12px !important;
    text-align: center !important;
}
.cancellation-card, .notice-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 11px;
    font-size: 0.82em;
    color: #cbd5e1;
    text-align: center;
    line-height: 1.5;
    margin: 6px 0;
}
div[data-testid="stTextInput"]:has(input[aria-label="hp"]),
input[aria-label="hp"] { display: none !important; }
</style>
"""),
    unsafe_allow_html=True,
)

# ==============================================================================
# 4. محرك الاتصال المحصن ضد خطأ [Errno -2] وتصحيح صور الكتالوج
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client | None:
    try:
        raw_url = str(st.secrets.get("SUPABASE_URL", "")).strip()
        # تنظيف الرابط من أي علامات اقتباس أو مسافات خفية تسبب خطأ [Errno -2]
        clean_url = re.sub(r'[\"\'\s]', '', raw_url).rstrip("/")
        if clean_url.endswith("/rest/v1"):
            clean_url = clean_url[:-8]
        if clean_url and not clean_url.startswith("http"):
            clean_url = "https://" + clean_url

        raw_key = str(st.secrets.get("SUPABASE_KEY", "")).strip()
        clean_key = re.sub(r'[\"\'\s]', '', raw_key)
        if not clean_url or not clean_key:
            return None
        return create_client(clean_url, clean_key)
    except Exception:
        return None


supabase = get_supabase_client()

# تصحيح صورة عطر لونار لتكون صورة مكونات عطرية فاخرة بدلاً من الصورة الشخصية
PERFUMES: dict[str, dict[str, str]] = {
    "عطر روميو": {
        "en_name": "Romeo",
        "tag": "رجالي فاخر • الأكثر طلباً 🔥",
        "notes": "باتشولي نقي، فانيلا، ومسك فاخر",
        "ingredient_label": "خلاصة الباتشولي الطبيعي",
        "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=400&h=400&q=80",
    },
    "عطر يوجا": {
        "en_name": "Yoga",
        "tag": "هادئ ومنعش • فوّاح",
        "notes": "برغموت إيطالي، مسك نقي، ونرجس",
        "ingredient_label": "البرغموت الإيطالي النقي",
        "img": "https://images.unsplash.com/photo-1582281298055-e25b84a30b0b?auto=format&fit=crop&w=400&h=400&q=80",
    },
    "عطر لونار": {
        "en_name": "Lunar",
        "tag": "أناقة للجنسين • ثبات عالي",
        "notes": "عنب أسود، باتشولي، وعنبر دافئ",
        "ingredient_label": "راتنج العنبر والأخشاب العطرية",
        "img": "https://images.unsplash.com/photo-1595425970377-c9703cf48b6d?auto=format&fit=crop&w=400&h=400&q=80",
    },
    "عطر لاروزيه": {
        "en_name": "Larose",
        "tag": "أنثوي ساحر • ناعم وجذاب",
        "notes": "فانيلا فرنسية، زنبق أبيض، وياسمين",
        "ingredient_label": "بتلات الياسمين الأبيض والزنبق",
        "img": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?auto=format&fit=crop&w=400&h=400&q=80",
    },
    "عطر إليسيوم": {
        "en_name": "Elysium",
        "tag": "فخامة ملكية • للمناسبات",
        "notes": "عنبر ملكي، فانيلا، ولافندر بارد",
        "ingredient_label": "زهور الخزامى واللافندر النقي",
        "img": "https://images.unsplash.com/photo-1528722828814-77b9b83aafb2?auto=format&fit=crop&w=400&h=400&q=80",
    },
    "عطر هارت بيت": {
        "en_name": "Heart Beat",
        "tag": "حيوي ورومانسي • جذاب",
        "notes": "كشمش أسود، مسك أبيض، وورد مخملي",
        "ingredient_label": "الكشمش الأسود والورد المخملي",
        "img": "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=400&h=400&q=80",
    },
}


@st.cache_data(ttl=5)
def get_all_bookings(basket_key: str) -> list[dict[str, Any]]:
    """جلب الحجوزات من Supabase، وفي حال انقطاع الشبكة [Errno -2] يعمل النسخ الاحتياطي تلقائياً."""
    if supabase:
        try:
            res = (
                supabase.table("bookings")
                .select("*")
                .eq("session_day", basket_key)
                .order("id")
                .execute()
            )
            if res.data is not None:
                return res.data
        except Exception:
            pass
    return [b for b in fallback_db if b.get("session_day") == basket_key]


def save_booking_resilient(record: dict[str, Any]) -> int:
    """حفظ الحجز في السحابة، وفي حال تعذر الاتصال بالشبكة يحفظ في الخزنة الاحتياطية فوراً ولا يعطل العميل."""
    if supabase:
        try:
            ins_res = supabase.table("bookings").insert(record).execute()
            if ins_res.data:
                get_all_bookings.clear()
                return int(ins_res.data[0].get("id", len(fallback_db) + 1))
        except Exception:
            pass
    new_id = len(fallback_db) + 1
    record_copy = dict(record)
    record_copy["id"] = new_id
    fallback_db.append(record_copy)
    get_all_bookings.clear()
    return new_id


def cancel_booking_and_auto_promote(target_id: int | None, target_phone: str) -> None:
    """إلغاء المقعد وترقية أول منتظر في الطابور سواء في السحابة أو النسخة الاحتياطية."""
    if supabase:
        try:
            if target_id:
                supabase.table("bookings").update({"status": "cancelled"}).eq("id", target_id).execute()
            else:
                supabase.table("bookings").update({"status": "cancelled"}).eq("phone", target_phone).eq("session_day", BASKET_ID).execute()

            waitlist_res = (
                supabase.table("bookings")
                .select("*")
                .eq("session_day", BASKET_ID)
                .eq("status", "waitlist")
                .order("id")
                .limit(1)
                .execute()
            )
            if waitlist_res.data:
                next_customer = waitlist_res.data[0]
                supabase.table("bookings").update({
                    "status": "confirmed",
                    "player_note": str(next_customer.get("player_note", "")) + " | PROMOTED_AUTO"
                }).eq("id", next_customer.get("id")).execute()
            get_all_bookings.clear()
            return
        except Exception:
            pass

    for item in fallback_db:
        if item.get("id") == target_id or item.get("phone") == target_phone:
            item["status"] = "cancelled"
    for item in fallback_db:
        if item.get("status") == "waitlist":
            item["status"] = "confirmed"
            break
    get_all_bookings.clear()


# ==============================================================================
# 5. حسابات السلات التلقائية وعرض الشريط العلوي
# ==============================================================================
all_cached_records = get_all_bookings(BASKET_ID)
confirmed_bookings = [b for b in all_cached_records if b.get("status") == "confirmed"]
waitlist_bookings = [b for b in all_cached_records if b.get("status") == "waitlist"]

active_count = len(confirmed_bookings)
current_basket_number = (active_count // GROUP_SIZE) + 1
seats_taken_in_current = active_count % GROUP_SIZE
seats_remaining_in_current = GROUP_SIZE - seats_taken_in_current
remaining_stock = max(0, TOTAL_INVENTORY_LIMIT - active_count)
is_waitlist_mode = active_count >= TOTAL_INVENTORY_LIMIT


@st.fragment(run_every="15s")
def render_live_progress() -> None:
    fresh_records = get_all_bookings(BASKET_ID)
    fresh_confirmed = [b for b in fresh_records if b.get("status") == "confirmed"]
    f_active = len(fresh_confirmed)
    f_basket_num = (f_active // GROUP_SIZE) + 1
    f_taken = f_active % GROUP_SIZE
    f_rem = GROUP_SIZE - f_taken
    f_stock = max(0, TOTAL_INVENTORY_LIMIT - f_active)
    pct = max(12, int((f_taken / GROUP_SIZE) * 100))

    st.markdown(
        clean_html(f"""
        <div class="top-card">
            <div class="brand-badge">{OFFER_NAME} • نظام {GROUP_SIZE} مشتركين</div>
            <div class="headline">تقاسم عروض العطور الفاخرة</div>
            <div class="sub-headline">العطر الأصلي بـ <b style="color:var(--primary);">{UNIT_SELL_PRICE} ر.س</b> بدلاً من {ORIGINAL_RETAIL} ر.س (توفير {SAVINGS_AMOUNT} ر.س)</div>
            <div class="progress-container">
                <div class="progress-fill" style="width: {pct}%;"></div>
            </div>
            <div class="progress-meta">
                <span>سلة رقم {f_basket_num} • حجز {f_taken} من {GROUP_SIZE}</span>
                <span style="color:var(--primary);">باقي {f_rem} مقاعد لإغلاق السلة 🔥</span>
            </div>
            <div>
                <span class="stock-badge">📦 المتبقي من كمية العرض الكلية: {f_stock} عبوة فقط</span>
            </div>
        </div>
    """),
        unsafe_allow_html=True,
    )


# ==============================================================================
# 6. شاشة الخطوة الأخيرة (الواتساب النابض)
# ==============================================================================
if "confirmed_deal" in st.session_state:
    deal = st.session_state["confirmed_deal"]
    safe_name = html.escape(str(deal.get("name", "")))
    safe_perfume = html.escape(str(deal.get("perfume", "")))
    safe_delivery_label = html.escape(str(deal.get("delivery_label", "")))
    client_final_total = deal.get("total_price", UNIT_SELL_PRICE)

    fresh_confirmed_cnt = len([b for b in get_all_bookings(BASKET_ID) if b.get("status") == "confirmed"])
    f_rem_seats = GROUP_SIZE - (fresh_confirmed_cnt % GROUP_SIZE)

    if deal.get("status") == "waitlist":
        status_banner = "⏳ خطوة أخيرة لتثبيت اسمك في قائمة الانتظار"
        seats_status_msg = "سيتم ترقية مقعدك فورياً بمجرد اعتذار أحد المشتركين أو فتح باقة إضافية!"
    else:
        status_banner = "⏳ خطوة أخيرة لتثبيت مقعدك في السلة"
        seats_status_msg = (
            f"⏳ باقي {f_rem_seats} مقاعد في السلة الحالية ونطلب فوراً."
            if f_rem_seats > 0
            else "🔥 اكتملت السلة الحالية بالكامل وجاري تنفيذ الطلب!"
        )

    st.markdown(
        clean_html(f"""
        <div class="top-card" style="border-color:var(--primary);">
            <div class="brand-badge">{status_banner}</div>
            <div class="headline" style="font-size:1.15em;">يا {safe_name}، أرسل رسالة الواتساب الآن</div>
            <div class="sub-headline" style="color:#cbd5e1 !important;">{safe_perfume} — {safe_delivery_label}</div>
            <div style="font-size:1.12em;font-weight:800;color:#ffffff;margin-top:5px;">
                الإجمالي عند الاستلام: <span style="color:var(--primary);">{client_final_total} ر.س فقط</span> (بدون دفع مسبق)
            </div>
        </div>
        <div class="notice-card">
            📲 <b>الرسالة مكتوبة وجاهزة تلقائياً:</b><br>
            اضغط الزر الأخضر بالأسفل لإرسال رسالة التثبيت عبر الواتساب واعتماد حصتك رسمياً.
        </div>
    """),
        unsafe_allow_html=True,
    )

    wa_delivery_text = deal.get("wa_delivery_text", "")
    wa_admin_msg = (
        f"مرحباً 🌿\n"
        f"حجزت حصتي في تطبيق مَقسوم ({client_final_total} ر.س):\n\n"
        f"• الاسم: {deal.get('name')}\n"
        f"• الجوال: {deal.get('phone')}\n"
        f"• العطر: {deal.get('perfume')}\n"
        f"• السلة: رقم {deal.get('basket_number', current_basket_number)}\n"
        f"{wa_delivery_text}\n\n"
        f"{seats_status_msg}\n\n"
        f"بانتظار تأكيدك واعتماد طلبي 🌿"
    )
    admin_link = f"https://wa.me/{ADMIN_PHONE}?text={urllib.parse.quote(wa_admin_msg)}"

    st.markdown(
        clean_html(
            f'<a href="{admin_link}" target="_blank" class="wa-link-btn">📲 اضغط هنا لإرسال رسالة التثبيت عبر واتساب الآن</a>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown('<div id="cancel-link-hook"></div>', unsafe_allow_html=True)
    if st.button("تراجعت عن الحجز؟ اضغط هنا لإلغاء المقعد وإتاحته للانتظار", use_container_width=True):
        cancel_booking_and_auto_promote(deal.get("id"), str(deal.get("phone", "")))
        st.session_state.pop("confirmed_deal", None)
        st.session_state["just_cancelled"] = True
        st.rerun()

# ==============================================================================
# 7. شاشة الحجز الرئيسية
# ==============================================================================
else:
    render_live_progress()

    if st.session_state.get("just_cancelled"):
        st.markdown(
            clean_html("""
            <div class="cancellation-card">
                🌿 <b>تم إلغاء حجزك بنجاح</b><br>
                تمت إتاحة مقعدك لقائمة الانتظار تلقائياً. نتشرف بك في أي وقت.
            </div>
        """),
            unsafe_allow_html=True,
        )

    st.markdown(
        clean_html('<div class="centered-section-title">1. اختر عطرك المفضل:</div>'),
        unsafe_allow_html=True,
    )

    chosen_perfume = st.radio(
        "اختر العطر:",
        options=list(PERFUMES.keys()),
        label_visibility="collapsed",
    )

    p = PERFUMES[chosen_perfume]

    st.markdown(
        clean_html(f"""
        <div class="sensory-card">
            <div class="sensory-top-row">
                <img src="{p['img']}" class="ingredient-thumb" alt="{p['ingredient_label']}" width="66" height="66" loading="eager" />
                <div class="sensory-details">
                    <div class="sensory-name">{chosen_perfume} <span style="font-size:0.8em;color:#94a3b8;font-weight:500;">({p['en_name']})</span></div>
                    <div class="sensory-tag">🌿 {p['ingredient_label']}</div>
                    <div class="sensory-notes">المكونات: {p['notes']}</div>
                </div>
            </div>
            <div class="price-chip">
                <span style="color:#cbd5e1;">سعر العبوة الفردي: <s style="color:#64748b;">{ORIGINAL_RETAIL} ر.س</s> ➔ <b style="color:var(--primary);font-size:1.15em;">{UNIT_SELL_PRICE} ر.س</b></span>
                <span style="color:var(--primary);font-weight:800;">وفرت {SAVINGS_AMOUNT} ر.س</span>
            </div>
        </div>
    """),
        unsafe_allow_html=True,
    )

    with st.form("order_form", clear_on_submit=False, enter_to_submit=False, border=False):
        st.markdown(
            clean_html('<div class="centered-section-title" style="margin-top:0;">2. بيانات التأكيد والاستلام:</div>'),
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
            clean_html('<div class="centered-section-title" style="font-size:0.88em;margin-top:8px;margin-bottom:4px;">3. حدد طريقة الاستلام (بدون دفع مسبق):</div>'),
            unsafe_allow_html=True,
        )

        delivery_choice = st.radio(
            "طريقة الاستلام:",
            [
                f"📍 استلام مباشر (السلام مول بوابة 5 و 6 - السبت المغرب للعشاء) — مجاناً ({UNIT_SELL_PRICE} ر.س فقط)",
                f"📦 استلام عبر خزائن ريد بوكس الذكية بجدة (+{LOCKER_FEE} ر.س) — الإجمالي: {UNIT_SELL_PRICE + LOCKER_FEE} ر.س",
                f"🚗 توصيل خاص لباب البيت داخل أحياء جدة (+{HOME_DELIVERY_FEE} ر.س) — الإجمالي: {UNIT_SELL_PRICE + HOME_DELIVERY_FEE} ر.س",
            ],
            key="delivery_mode",
            label_visibility="collapsed",
        )

        st.markdown(
            clean_html("""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:6px;padding:7px;text-align:center;font-size:0.73em;color:#94a3b8;margin:8px 0;">
                🛡️ أصلي 100% بكرتون الوكالة • فحص العطر والفاتورة الأصلية قبل الدفع يد بيد
            </div>
        """),
            unsafe_allow_html=True,
        )

        hp = st.text_input("hp", label_visibility="collapsed")

        if is_waitlist_mode:
            btn_label = "⏳ سجل في قائمة الانتظار (الأولوية تلقائياً عند أي إلغاء)"
        else:
            btn_label = f"تثبيت حصتك في العرض (سلة رقم {current_basket_number})"

        submit_btn = st.form_submit_button(btn_label, use_container_width=True)

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
            else:
                st.session_state["saved_name"] = clean_name
                st.session_state["saved_phone"] = clean_phone
                st.session_state.pop("just_cancelled", None)

                if "ريد بوكس" in delivery_choice:
                    applied_fee = LOCKER_FEE
                    clean_delivery_label = "خزائن ريد بوكس الذكية"
                    wa_del_msg = (
                        f"• طريقة الاستلام: خزائن ريد بوكس الذكية بجدة (+{LOCKER_FEE} ر.س) 📦\n"
                        f"• الخزانة المفضلة: (برسل لك اسم أو موقع الخزانة الأقرب لي 📍)\n"
                        f"• الإجمالي المطلوب: {UNIT_SELL_PRICE + LOCKER_FEE} ر.س"
                    )
                elif "توصيل خاص" in delivery_choice or "باب البيت" in delivery_choice:
                    applied_fee = HOME_DELIVERY_FEE
                    clean_delivery_label = "توصيل منزلي خاص"
                    wa_del_msg = (
                        f"• طريقة الاستلام: توصيل منزلي لباب البيت (+{HOME_DELIVERY_FEE} ر.س) 🚗\n"
                        f"• موقعي: (برسل لك دبوس الموقع تحت هذي الرسالة الحين 📍)\n"
                        f"• الإجمالي المطلوب: {UNIT_SELL_PRICE + HOME_DELIVERY_FEE} ر.س يد بيد بعد الفحص 🤝"
                    )
                else:
                    applied_fee = 0
                    clean_delivery_label = "استلام السلام مول (مجاناً)"
                    wa_del_msg = (
                        f"• طريقة الاستلام: السلام مول (بوابة 5 و 6) 📍\n"
                        f"• الموعد: السبت (المغرب إلى العشاء: 6:30م – 9:00م) ⏰\n"
                        f"• الإجمالي المطلوب: {UNIT_SELL_PRICE} ر.س يد بيد بعد الفحص 🤝"
                    )

                final_total = UNIT_SELL_PRICE + applied_fee

                get_all_bookings.clear()
                live_records = get_all_bookings(BASKET_ID)
                live_confirmed = [b for b in live_records if b.get("status") == "confirmed"]
                live_basket_num = (len(live_confirmed) // GROUP_SIZE) + 1

                target_status = "waitlist" if len(live_confirmed) >= TOTAL_INVENTORY_LIMIT else "confirmed"
                client_note = (
                    f"BASKET:{live_basket_num} | {chosen_perfume} | {clean_delivery_label} | "
                    f"UNIT:{UNIT_SELL_PRICE} | FEE:{applied_fee} | TOTAL:{final_total}"
                )

                new_id = save_booking_resilient({
                    "name": clean_name,
                    "phone": clean_phone,
                    "session_day": BASKET_ID,
                    "court": live_basket_num,
                    "level": chosen_perfume,
                    "status": target_status,
                    "payment_status": "pending",
                    "hear_about": clean_delivery_label[:50],
                    "player_note": client_note,
                })

                st.session_state["confirmed_deal"] = {
                    "id": new_id,
                    "name": clean_name,
                    "phone": clean_phone,
                    "perfume": chosen_perfume,
                    "delivery_label": clean_delivery_label,
                    "total_price": final_total,
                    "basket_number": live_basket_num,
                    "status": target_status,
                    "wa_delivery_text": wa_del_msg,
                }
                st.rerun()

# ==============================================================================
# 8. لوحة القيادة المحاسبية والإدارية (?manage=faris)
# ==============================================================================
if st.query_params.get("manage") == "faris":
    st.markdown("---")
    st.markdown("### 🎛️ لوحة القيادة المحاسبية ونظام إدارة المعرفة")

    admin_pin = st.text_input("رمز الدخول السري للمشرف:", type="password", key="adm_auth_key")
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
        all_admin_records = get_all_bookings(BASKET_ID)
        confirmed_list = [b for b in all_admin_records if b.get("status") == "confirmed"]
        waitlist_list = [b for b in all_admin_records if b.get("status") == "waitlist"]

        tab_sim, tab_pnl, tab_users = st.tabs([
            "📊 محاكي التسعير الذكي",
            "📈 المحاسبة الدقيقة (P&L)",
            "👥 السلات وطابور الانتظار",
        ])

        with tab_sim:
            st.markdown("##### ⚙️ ضبط معايير الباقة (يرتبط تلقائياً بحجم المجموعة لمنع خطأ الـ 275 ر.س):")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                sim_offer_name = st.text_input("اسم العرض التجاري:", value=OFFER_NAME)
                sim_group_size = st.selectbox("حجم المجموعة (2 = النصف | 4 = الربع):", options=[2, 4], index=0 if GROUP_SIZE == 2 else 1)
                default_suggested_cost = 265.0 if sim_group_size == 2 else 530.0
                sim_bundle_cost = st.number_input("تكلفة شراء الباقة من الشركة (ر.س):", value=default_suggested_cost, step=10.0)
                sim_retail = st.number_input("سعر العبوة الفردي بالسوق (ر.س):", value=ORIGINAL_RETAIL, step=5)
            with c_s2:
                sim_target_profit = st.number_input("صافي ربحك المستهدف في الحبة (ر.س):", value=TARGET_PROFIT_PER_UNIT, step=5.0)
                sim_inventory = st.number_input("إجمالي الكمية المتاحة (عبوة):", value=TOTAL_INVENTORY_LIMIT, step=2)
                sim_locker = st.number_input("رسوم خزائن ريد بوكس (ر.س):", value=LOCKER_FEE, step=1)
                sim_home = st.number_input("رسوم التوصيل للمنزل (ر.س):", value=HOME_DELIVERY_FEE, step=1)

            calc_fraction_name = "النصف (1/2)" if sim_group_size == 2 else "الربع (1/4)"
            calc_unit_cost = sim_bundle_cost / sim_group_size
            calc_sell_price = int(math.ceil(calc_unit_cost + sim_target_profit))
            calc_unit_profit = calc_sell_price - calc_unit_cost
            calc_basket_profit = calc_unit_profit * sim_group_size

            if calc_sell_price >= sim_retail:
                st.error(f"⚠️ تحذير جودة المحتوى: سعر البيع ({calc_sell_price} ر.س) أعلى أو مساوٍ للسعر الفردي بالسوق ({sim_retail} ر.س)! خفّض تكلفة الباقة إلى 265 ر.س لنظام الثنائيات.")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"التكلفة ({calc_fraction_name})", f"{calc_unit_cost:.1f} ر.س")
            m2.metric("سعر البيع للعميل", f"{calc_sell_price} ر.س")
            m3.metric("صافي ربحك بالحبة", f"{calc_unit_profit:.1f} ر.س")
            m4.metric("صافي ربحك بالسلة", f"{calc_basket_profit:.1f} ر.س")

            if st.button("💾 اعتماد وتعميم الإعدادات لجميع الزوار الآن", use_container_width=True):
                store_cfg["offer_name"] = sim_offer_name
                store_cfg["group_size"] = sim_group_size
                store_cfg["bundle_cost"] = sim_bundle_cost
                store_cfg["retail_price"] = sim_retail
                store_cfg["target_profit"] = sim_target_profit
                store_cfg["total_inventory"] = sim_inventory
                store_cfg["locker_fee"] = sim_locker
                store_cfg["home_delivery_fee"] = sim_home
                st.success("✅ تم تحديث إعدادات المتجر بنجاح لجميع المستخدمين!")
                st.rerun()

        with tab_pnl:
            n_confirmed = len(confirmed_list)
            completed_baskets_count = n_confirmed // GROUP_SIZE
            completed_units_count = completed_baskets_count * GROUP_SIZE
            open_basket_seats = n_confirmed % GROUP_SIZE

            realized_perfume_rev = completed_units_count * UNIT_SELL_PRICE
            realized_cogs = completed_baskets_count * BUNDLE_ORIGINAL_COST
            realized_net_profit = realized_perfume_rev - realized_cogs
            pending_open_rev = open_basket_seats * UNIT_SELL_PRICE

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("مبيعات السلات المكتملة", f"{realized_perfume_rev} ر.س")
            r2.metric("تكلفة الباقات المكتملة", f"{realized_cogs:.0f} ر.س")
            r3.metric("صافي الربح المحقق", f"{realized_net_profit:.1f} ر.س")
            r4.metric("مبيعات معلقة (سلة مفتوحة)", f"{pending_open_rev} ر.س")

        with tab_users:
            st.markdown(f"##### 📦 المشتركون المؤكدون ({len(confirmed_list)}) | ⏳ الانتظار ({len(waitlist_list)}):")
            for member in confirmed_list:
                st.write(f"• **{member.get('name')}** | `{member.get('phone')}` | **{member.get('level')}** | `{member.get('hear_about')}`")
    elif input_pin_str:
        st.error("رمز الدخول غير صحيح.")
