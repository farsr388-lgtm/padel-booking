import streamlit as st
from supabase import create_client, Client
import re
import hmac
import urllib.parse
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. إعداد الصفحة والتصميم
# ==========================================
st.set_page_config(
    page_title="بادل 99 | Padel 99",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 100% !important; 
}

html, body, p, div, span, label, input, select, button, .stMarkdown {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Geeza Pro", Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
}

.hero-header { font-size: 1.6em; font-weight: 800; color: #f8fafc; margin: 0; }
