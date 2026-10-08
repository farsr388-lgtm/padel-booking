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
# 2. أنماط الواجهة فائقة الخفة وتوزيع الأحجام البصرية (Two-Tone System)
# ==============================================================================
st.markdown("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.6rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 420px !important; 
    margin: 0 auto; 
}

/* نظام الخطوط والخلفيات المظلمة */
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19;
    color: #f1f5f9;
}

/* تحويل خيارات الراديو إلى كروت نشطة باللمس المباشر */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    background-color: #111827 !important;
    border: 1.5px solid #1f2937 !important;
    border-radius: 12px !important;
    padding: 11px 13px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.15s ease-in-out !important;
    display: flex !important;
    align-items: center !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
    border-color: #334155 !important;
    background-color: #141e33 !important;
}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.08) !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* القضاء الجذري على اللون الأحمر في إطارات التحديد */
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

/* حقول الإدخال */
input, textarea { 
    caret-color: #10b981 !important; 
}
input:focus, textarea:focus, 
div[data-baseweb="input"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* الهيدر العلوي المتناسق */
.store-header {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    text-align: center;
}
.store-badge {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78em;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 6px;
}
.store-title { 
    font-size: 1.3em; 
    font-weight: 900; 
    color: #ffffff; 
    margin: 2px 0 6px 0; 
}
.store-desc { 
    font-size: 0.82em; 
    color: #94a3b8; 
    line-height: 1.5; 
    margin-bottom: 10px; 
}

/* شريط السعر البارز */
.price-strip {
    background: #0b0f19;
    border: 1
