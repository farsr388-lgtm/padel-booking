import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==============================================================================
# 1. إعداد الصفحة وتنسيق الموبايل المطور
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | قطة عطور درعة",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 430px !important; 
    margin: 0 auto; 
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
}
.hero-box {
    background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
    border: 1px solid #4338ca;
    border-radius: 14px;
    padding: 12px;
    text-align: center;
    margin-bottom: 8px;
}
.hero-title { font-size: 1.45em; font-weight: 900; color: #f8fafc; margin: 0; }
.offer-pill {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid #818cf8;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.82em;
    color: #c7d2fe;
    margin: 6px 0;
    display: inline-block;
    font-weight: 800;
}
.slots-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin: 8px 0;
}
.slot-card {
    border-radius: 8px;
    padding: 8px 4px;
    text-align: center;
    font-size: 0.78em;
    font-weight: 800;
    line-height: 1.35;
}
.slot-empty {
    background: rgba(30, 41, 59, 0.5);
    border: 1.5px dashed #6366f1;
    color: #c7d2fe;
}
.slot-taken {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #a7f3d0;
}

/* بطاقة ما بعد الحجز المكبرة */
.status-card-success {
    background: rgba(16, 185, 129, 0.12);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    margin-top: 8px;
}

/* إبراز كود الحجز ورقم الجوال المنفصل */
.big-code-box {
    background: #0f172a;
    border: 2px solid #38bdf8;
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0;
    text-align: center;
}
.big-code-title {
    font-size: 0.82em;
    color: #94a3b8;
    margin-bottom: 2px;
}
.big-code-val {
    font-family: monospace;
    font-size: 1.6em;
    font-weight: 900;
    color: #38bdf8;
    letter-spacing: 2px;
}

.big-phone-box {
    background: rgba(30, 41, 59, 0.6);
    border: 1px dashed #64748b;
    border-radius: 10px;
    padding: 8px;
    margin: 6px 0;
    font-size: 0.9em;
    color: #e2e8f0;
}

.alert-instruction {
    background: rgba(245, 158, 11, 0.15);
    border: 1.5px solid #f59e0b;
    border-radius: 12px;
    padding: 12px;
    margin: 10px 0;
    font-size: 0.88em;
    line-height: 1.6;
    color: #fef3c7;
    text-align: right;
}

.wa-btn {
    display: block;
    background: #25D366;
    color: #ffffff !important;
    text-align: center;
    padding: 14px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 1em;
    text-decoration: none;
    box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
    margin-top: 10px;
}
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    font-size: 1.05em !important;
    font-weight: 800 !important;
    height: 50px !important;
    border-radius: 10px !important;
    border: none !important;
    margin-top: 4px !important;
}
div[data-testid="stTextInput"]:has(input[aria-label="hp"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ربط قاعدة البيانات السحابية (Supabase)
# ==============================================================================
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    if url.endswith("/rest/v1"):
        url = url[:-8]
    return create_client(url, st.secrets["SUPABASE_KEY"].strip())

try:
    supabase = get_supabase_client()
except Exception:
    st.error("تعذر الاتصال بقاعدة البيانات. تأكد من إعداد Secrets.")
    st.stop()

# ==============================================================================
# 3. إعدادات السلة والحسبة المالية (88 ر.س شامل RedBox)
# ==============================================================================
BASKET_ID = "MAQSOOM-DERAAH-01"
BASKET_CAPACITY = 6
ADMIN_PHONE = "966566261868"
ADMIN_PASSWORD_HASH = st.secrets.get("ADMIN_PASSWORD", "Mq99#Jeddah!2026")

PERFUMES = {
    "عطر ليدر (Leader)": "جلود وأخشاب فاخرة •
