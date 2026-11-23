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
if "undo_stack" not in st.session_state:
    st.session_state["undo_stack"] = []

active_flr = st.session_state["sel_floor"]
active_rm = st.session_state["sel_room"]

# ==============================================================================
# 2. التصميم البصري المبسط (أزرار مريحة للإبهام + وضوح تام)
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
    height: 53px !important;
    width: 100% !important;
    padding: 0 4px !important;
    font-size: 1.0em !important;
    font-weight: 900 !important;
    border-radius: 14px !important;
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
    height: 41px !important;
    font-size: 0.91em !important;
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
    height: 40px !important;
    font-size: 0.89em !important;
    border-radius: 11px !important;
    background: #111827 !important;
}}
div.st-key-rm_{active_rm} button {{
    border: 2.5px solid #10b981 !important;
    background: rgba(16, 185, 129, 0.25) !important;
    color: #ecfdf5 !important;
}}

/* زر الغرفة النظيفة */
div.st-key-b_star button {{
    height: 55px !important;
    font-size: 1.1em !important;
    background: rgba(16, 185, 129, 0.2) !important;
    border: 2px solid #10b981 !important;
    color: #6ee7b7 !important;
}}

/* أزرار المخالفات */
div.st-key-b_heater button, div.st-key-b_clean button, div.st-key-b_both button {{
    background: rgba(245, 158, 11, 0.16) !important;
    border-color: rgba(251, 191, 36, 0.55) !important;
    color: #fde68a !important;
}}

/* زر الدواء */
div.st-key-b_pest button {{
    background: rgba(168, 85, 247, 0.18) !important;
    border-color: rgba(192, 132, 252, 0.6) !important;
    color: #e9d5ff !important;
}}

/* أزرار الصيانة */
div.st-key-m_
