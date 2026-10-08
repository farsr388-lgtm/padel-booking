import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import re
import html
import hmac
import urllib.parse

# ==============================================================================
# 1. إعداد الصفحة وهوية العرض
# ==============================================================================
st.set_page_config(
    page_title="مَقسوم | بلوم نيوتن",
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

def clean_html(raw: str) -> str:
    return "".join(line.strip() for line in raw.splitlines() if line.strip())

# ==============================================================================
# 2. تصميم الواجهة (Apple Minimalist + Zero Red)
# ==============================================================================
css_styles = clean_html("""
<style>
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }

.block-container { 
    padding-top: 0.2rem !important; 
    padding-bottom: 1.2rem !important; 
    max-width: 410px !important; 
    margin: 0 auto; 
}

html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #000000;
    color: #f5f5f7;
}

/* بطاقة الهيدر العلوية بأسلوب آبل */
.apple-card {
    background: #121214;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 8px;
    text-align: center;
}
.apple-badge {
    color: #34d399;
    font-size: 0.72em;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 2px;
    text-transform: uppercase;
}
.apple-headline {
    font-size: 1.2em;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
}
.apple-sub {
    font-size: 0.8em;
    color: #86868b;
    margin: 2px 0 8px 0;
}
.progress-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.74em;
    font-weight: 600;
    margin-bottom: 4px;
}
.apple-progress-bar {
    background: #1c1c1e;
    height: 5px;
    border-radius: 3px;
    overflow: hidden;
}
.apple-progress-fill {
    background: #10b981;
    height: 100%;
    border-radius: 3px;
}

/* شبكة اختيار العطور */
div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
    width: 100% !important;
    margin-bottom: 6px !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label {
    width: 100% !important;
    margin: 0 !important;
    background-color: #121214 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 8px !important;
    min-height: 38px !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
    font-size: 0.82em !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:hover {
    border-color: rgba(255, 255, 255, 0.25) !important;
}

div[data-testid="stRadio"]:not(form div[data-testid="stRadio"]) div[role="radiogroup"] > label:has(input:checked) {
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.08) !important;
}

/* استئصال دوائر الراديو الحمراء نهائياً */
div[data-testid="stRadio"] div[role="radiogroup"] label div:first-child {
    border-color: #52525b !important;
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

/* كرت العطر المختار فائق الدقة والاختصار */
.selected-product-card {
    background: #121214;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px 10px;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.product-image {
    width: 64px;
    height: 64px;
    border-radius: 8px;
    object-fit: cover;
    background: #1c1c1e;
    flex-shrink: 0;
}
.product-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.product-title {
    font-size: 0.9em;
    font-weight: 800;
    color: #ffffff;
    display: flex;
    justify-content: space-between;
}
.product-highlight {
    color: #34d399;
    font-size: 0.75em;
    font-weight: 700;
}
.product-brief {
    font-size: 0.75em;
