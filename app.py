from datetime import datetime
import urllib.parse
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. إعداد الشاشة للجوال الميداني (RTL / Dark Mode)
# ==============================================================================
st.set_page_config(
    page_title="منظومة التوسع الاستراتيجي | سكن جامعة 3",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
:root {
    color-scheme: dark;
    --primary: #10b981;
    --card-bg: #111827;
    --border-color: rgba(255, 255, 255, 0.12);
}
header[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { 
    padding-top: 0.5rem !important; 
    padding-bottom: 2rem !important; 
    max-width: 430px !important; 
    margin: 0 auto !important;
}
html, body, [class*="css"] { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; 
    direction: rtl; 
    text-align: right; 
    background-color: #0b0f19 !important; 
    color: #f8fafc !important; 
}
.header-card { 
    background: var(--card-bg); 
    border: 1px solid var(--border-color); 
    border-radius: 12px; 
    padding: 12px; 
    margin-bottom: 10px; 
    text-align: center; 
}
.headline { font-size: 1.15em; font-weight: 900; color: #ffffff; margin: 0; }
.sub-headline { font-size: 0.82em; font-weight: 700; color: #94a3b8; margin-top: 2px; }
div[data-testid="stFormSubmitButton"] > button { 
    background: var(--primary) !important; 
    color: #022c22 !important; 
    font-weight: 900 !important; 
    height: 46px !important; 
    border-radius: 10px !important; 
    width: 100% !important; 
    border: none !important; 
    font-size: 1.05em !important; 
}
.stat-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 6px;
}
.badge-vert {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.6);
    color: #93c5fd;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75em;
    font-weight: 800;
}
.badge-horiz {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(16, 185, 129, 0.6);
    color: #6ee7b7;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75em;
    font-weight: 800;
}
.wa-btn {
    display: block;
    background: #10b981;
    color: #022c22 !important;
    text-align: center;
    padding: 13px;
    border-radius: 10px;
    font-weight: 900;
    font-size: 1.05em;
    text-decoration: none !important;
    margin-top: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. قواعد البيانات الحية (توسع رأسي + توسع أفقي)
# ==============================================================================
# التوسع الرأسي: شراء المواد وتخزينها داخلياً والاستغناء عن عمولة المقاول الوسيط
if "vertical_inventory" not in st.session_state:
    st.session_state["vertical_inventory"] = [
        {"item": "شطاف حمام أصلي", "qty": 18, "cost_direct": 22.0, "contractor_quote": 65.0},
        {"item": "صنبور / بزبوز مياه نحاس", "qty": 10, "cost_direct": 30.0, "contractor_quote": 85.0},
        {"item": "فلتر مكيف سبليت", "qty": 25, "cost_direct": 15.0, "contractor_quote": 45.0},
    ]

# التوسع الأفقي: إيرادات الخدمات الإضافية وتعدد العمائر
if "horizontal_services" not in st.session_state:
    st.session_state["horizontal_services"] = [
        {"building": "سكن جامعة 3", "room": "213", "service": "غسيل وكوي ملابس", "fee": 25.0, "date": "2026-11-09"},
        {"building": "سكن جامعة 3", "room": "104", "service": "تنظيف غرفة شامل", "fee": 50.0, "date": "2026-11-10"},
        {"building": "سكن جامعة 2", "room": "301", "service": "سناكات ومشروبات ذاتية", "fee": 15.0, "date": "2026-11-10"},
    ]

SUPERVISOR_NAME = "فارس العصيمي"
now_str = datetime.now().strftime("%Y-%m-%d | %I:%M %p")

# ==============================================================================
# 3. الترويسة والمؤشرات الاستراتيجية
# ==============================================================================
st.markdown(
    f"""
<div class="header-card">
    <div class="headline">🏢 إدارة التوسع والنمو الميداني</div>
    <div class="sub-headline">تطبيق مفاهيم ريادة الأعمال على السكن • المشرف: {SUPERVISOR_NAME}</div>
</div>
""",
    unsafe_allow_html=True,
)

# حساب الوفر المالي من التوسع الرأسي (فرق سعر الشراء المباشر عن تسعيرة المقاول)
df_v = pd.DataFrame(st.session_state["vertical_inventory"])
df_v["saved_per_unit"] = df_v["contractor_quote"] - df_v["cost_direct"]
total_saved = (df_v["saved_per_unit"] * df_v["qty"]).sum()

# حساب إجمالي الإيرادات من التوسع الأفقي (الخدمات الجديدة وتعدد العمائر)
df_h = pd.DataFrame(st.session_state["horizontal_services"])
total_new_rev = df_h["fee"].sum()

c_k1, c_k2 = st.columns(2)
with c_k1:
    st.metric("وفر التوسع الرأسي 📉", f"{int(total_saved)} ريال", delta="استغناء عن الوسطاء")
with c_k2:
    st.metric("دخل التوسع الأفقي 📈", f"{int(total_new_rev)} ريال", delta="خدمات إضافية جديدة")

tab_strategy, tab_vert, tab_horiz, tab_report = st.tabs([
    "💡 المحاكي الاستراتيجي",
    "⚙️ التوسع الرأسي (المخزون)",
    "🛒 التوسع الأفقي (الخدمات)",
    "📊 تقرير الواتساب الشامل",
])

# ------------------------------------------------------------------------------
# 1. تبويب المحاكي الاستراتيجي: شرح منطقي ومقارنة علمية حية
# ------------------------------------------------------------------------------
with tab_strategy:
    st.markdown("##### 🔍 كيف تنعكس الاستراتيجيتان على أرض الواقع؟")
    
    st.markdown(
        """
        <div class="stat-card" style="border-right: 4px solid #3b82f6;">
            <b>1. التوسع الرأسي (Vertical Integration):</b><br>
            <span class="badge-vert">السيطرة على سلسلة التوريد</span><br>
            • <b>الفكرة:</b> بدل أن تنتظر مقاول الصيانة ليأتي بقطعة ويحسبها بضعف السعر، نشتري قطع الغيار بالجملة من المصدر وندير الإصلاح ذاتياً.<br>
            • <b>الأثر:</b> استقلالية تامة، خفض التكاليف، وسرعة إنجاز تحافظ على راحة النزيل.
        </div>
        
        <div class="stat-card" style="border-right: 4px solid #10b981; margin-top:8px;">
            <b>2. التوسع الأفقي (Horizontal Integration):</b><br>
            <span class="badge-horiz">تنويع الخدمات وتعدد المواقع</span><br>
            • <b>الفكرة:</b> النزيل يسكن عندك؛ بدل الاكتفاء بالسكن فقط، تقدم له خدمات يحتاجها يومياً (غسيل، قهوة، تنظيف خاص) بنفس الموارد الحالية.<br>
            • <b>الأثر:</b> زيادة العائد المالي لكل نزيل وتكرار النموذج على العمائر المجاورة (عمارة 1 و 2 و 3).
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------------------
# 2. تبويب التوسع الرأسي: السيطرة على قطع الغيار وإلغاء عمولة المقاول
# ------------------------------------------------------------------------------
with tab_vert:
    st.markdown("##### ⚙️ إدارة سلسلة الإمداد الذاتية (شراء مباشر):")
    st.caption("شراء المواد الخام وتخزينها لحساب السكن بدل الاعتماد على المقاولين:")

    with st.form("form_vert_item", clear_on_submit=True):
        v_item_name = st.text_input("اسم القطعة أو المادة الخام:", placeholder="مثال: قلب صنبور ماء أصلي / شطاف...")
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            v_qty = st.number_input("الكمية المشتراة:", min_value=1, value=10)
        with col_v2:
            v_direct_cost = st.number_input("سعر الجملة المباشر:", min_value=1.0, value=25.0)
        with col_v3:
            v_contractor_cost = st.number_input("تسعيرة المقاول لو جابها:", min_value=1.0, value=70.0)

        if st.form_submit_button("⚡ حفظ القطعة وحساب وفر الاستغناء عن المقاول"):
            if v_item_name.strip():
                st.session_state["vertical_inventory"].append({
                    "item": v_item_name.strip(),
                    "qty": int(v_qty),
                    "cost_direct": float(v_direct_cost),
                    "contractor_quote": float(v_contractor_cost),
                })
                st.success(f"تم إدراج {v_item_name} بالمخزون المباشر وتوفير {int((v_contractor_cost - v_direct_cost) * v_qty)} ريال!")
                st.rerun()

    st.markdown("###### 📦 مخزون الصيانة الذاتي (الرأسي):")
    for row in st.session_state["vertical_inventory"]:
        saved = (row["contractor_quote"] - row["cost_direct"]) * row["qty"]
        st.markdown(
            f"""
            <div class="stat-card">
                <b>{row['item']}</b> — الكمية: <b>{row['qty']}</b><br>
                <small style="color:#94a3b8;">شراء مباشر: {row['cost_direct']} ر.س | تسعيرة المقاول: {row['contractor_quote']} ر.س</small><br>
                <span class="badge-vert">الوفر المحقق: {int(saved)} ريال</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------------------
# 3. تبويب التوسع الأفقي: إضافة خدمات جديدة وتوسيع الرقعة للعمائر
# ------------------------------------------------------------------------------
with tab_horiz:
    st.markdown("##### 🛒 تقديم خدمات جديدة للنزلاء (توسع أفقي):")
    st.caption("توليد مداخيل إضافية من نفس النزيل أو التوسع لإدارة عمائر أخرى:")

    with st.form("form_horiz_service", clear_on_submit=True):
        target_bld = st.selectbox("العمارة المستهدفة:", ["سكن جامعة 3", "سكن جامعة 2", "سكن جامعة 1"])
        h_room = st.text_input("رقم الغرفة / النزيل المستفيد:", placeholder="مثال: 213")
        h_serv_type = st.selectbox(
            "الخدمة الجديدة المضافة:",
            ["غسيل وكوي ملابس 🧺", "تنظيف غرفة خاص 🧹", "مشروبات ومكائن ذاتية ☕", "توصيل وجبة سريعة 🍱"],
        )
        h_fee = st.number_input("رسوم الخدمة (ريال):", min_value=5.0, value=25.0)

        if st.form_submit_button("⚡ تسجيل تقديم الخدمة الإضافية"):
            if h_room.strip():
                st.session_state["horizontal_services"].append({
                    "building": target_bld,
                    "room": h_room.strip(),
                    "service": h_serv_type.split()[0] + " " + h_serv_type.split()[1],
                    "fee": float(h_fee),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })
                st.success(f"تم تسجيل خدمة ({h_serv_type.split()[0]}) لغرفة {h_room} بقيمة {h_fee} ريال!")
                st.rerun()

    st.markdown("###### 📋 العمليات الأفقية الحديثة:")
    for h in reversed(st.session_state["horizontal_services"][-4:]):
        st.markdown(
            f"""
            <div class="stat-card">
                <b>{h['building']} - غرفة {h['room']}</b>: {h['service']}<br>
                <span class="badge-horiz">إيراد إضافي: +{h['fee']} ريال</span> • <small style="color:#94a3b8;">{h['date']}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------------------
# 4. تقرير الواتساب الاستراتيجي للإدارة العليا
# ------------------------------------------------------------------------------
with tab_report:
    st.markdown("##### 📊 التقرير الاستراتيجي الشامل للإدارة:")
    st.caption("تقرير علمي يوضح لمدير السكن وفر التكاليف وزيادة كفاءة الأصول:")

    strategy_report_text = f"""*تقرير الأداء الاستراتيجي والنمو التشغيلي - {LOCATION_TAG}*
*التاريخ:* {now_str}
*المشرف المسؤول:* {SUPERVISOR_NAME}
-------------------------------------------
*1️⃣ أثر التوسع الرأسي (سلسلة التوريد والصيانة المباشرة):*
• تم شراء وتأمين ({len(st.session_state['vertical_inventory'])}) أصناف تشغيلية أساسية بالجملة.
• تسعيرة المقاول التقليدية: {int(sum([r['contractor_quote'] * r['qty'] for r in st.session_state['vertical_inventory']]))} ريال.
• تكلفة الشراء المباشر الذاتي: {int(sum([r['cost_direct'] * r['qty'] for r in st.session_state['vertical_inventory']]))} ريال.
💡 *صافي الوفر المالي المحقق للسكن:* ({int(total_saved)} ريال) مع تحكم كامل بالجودة والسرعة.

*2️⃣ أثر التوسع الأفقي (الخدمات الجديدة والعمائر):*
• الخدمات المسجلة للنزلاء: {len(st.session_state['horizontal_services'])} عمليات (غسيل، تنظيف، مكائن).
• نطاق التوسع: يغطي (سكن جامعة 3، سكن جامعة 2، سكن جامعة 1).
💡 *صافي الدخل الإضافي المستحدث:* (+{int(total_new_rev)} ريال) دون أي تكاليف تأسيس جديدة.

*الخلاصة الاستراتيجية:*
تم تطبيق نموذج تشغيلي مستقل يقلل الاعتماد على مقاولي الباطن ويزيد من كفاءة استغلال موارد السكن القائمة.
-------------------------------------------"""

    st.text_area("معاينة التقرير الاستراتيجي:", value=strategy_report_text, height=270)

    # زر مشاركة الواتساب الحر بدون كتابة أرقام
    enc_strategy_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(strategy_report_text)}"
    st.markdown(
        f'<a href="{enc_strategy_url}" target="_blank" class="wa-btn">📲 إرسال التقرير الاستراتيجي عبر واتساب (اختر الإدارة من جوالك)</a>',
        unsafe_allow_html=True,
    )

    st.divider()
    # تصدير الإكسل المعتمد
    if st.session_state["vertical_inventory"]:
        st.download_button(
            label="📥 تنزيل كشف وفر التوسع الرأسي (Excel CSV)",
            data=pd.DataFrame(st.session_state["vertical_inventory"]).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"Vertical_Savings_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
