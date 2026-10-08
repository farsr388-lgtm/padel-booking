import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة وهوية المنصة
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | تقاسم عروض بلوم - مجموعة نيوتن",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تتبع Microsoft Clarity
components.html("""
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window.parent, window.parent.document, "clarity", "script", "ytjnujh8td");
</script>
""", height=0, width=0)

# ==============================================================================
# 2. أنماط الواجهة الثنائية (شبكة A/B، فك الالتصاق، وحواف مريحة)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.6rem !important; 
    padding-bottom: 2.2rem !important; 
    max-width: 420px !important; 
    margin: 0 auto; 
}

/* خلفيات داكنة ونصوص هادئة */
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f1f5f9;
}

/* -------------------------------------------------------------------------- */
/* شبكة الاختيار الثنائية (A/B Columns Grid) لتصغير الكروت وفك الالتصاق      */
/* -------------------------------------------------------------------------- */
div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
    margin-bottom: 10px !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1.5px solid #1f2937 !important;
    border-radius: 10px !important;
    padding: 10px 8px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.15s ease-in-out !important;
    display: flex !important;
    align-items: center !important;
    min-height: 48px !important;
    box-sizing: border-box !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] > label:hover {
    border-color: #334155 !important;
    background-color: #141e33 !important;
}

div[data-testid="stRadio"]:has(input[name*="perfume_choice"]) > div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* إخفاء اللون الأحمر واستبداله بالزمردي في مؤشر التحديد */
div[data-testid="stRadio"] div[role="radiogroup"] label div:first-child {
    border-color: #475569 !important;
    background-color: transparent !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child,
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] {
    border-color: #10b981 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] div,
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child div {
    background-color: #10b981 !important;
}

/* بطاقة خيارات التوصيل */
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
}
div[data-testid="stRadio"]:has(input[name*="delivery_mode"]) > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 10px !important;
    padding: 10px 12px !important;
    margin: 0 !important;
}

/* حقول الإدخال والمسافات */
div[data-testid="stTextInput"] {
    margin-bottom: 8px !important;
