import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
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
    padding-top: 0.4rem !important; 
    padding-bottom: 1.5rem !important; 
    padding-left: 0.5rem !important; 
    padding-right: 0.5rem !important; 
    max-width: 100% !important; 
}

html, body, p, div, span, label, input, select, button, .stMarkdown {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Geeza Pro", Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
    box-sizing: border-box;
}

.hero-header { font-size: 1.55em; font-weight: 800; color: #f8fafc; margin: 0; line-height: 1.2; }
.hero-sub { font-size: 0.85em; color: #94a3b8; margin: 2px 0 6px 0; }
.contrast-pill { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 4px 8px; font-size: 0.74em; color: #cbd5e1; font-weight: 600; margin-bottom: 4px; }
.promo-badge { background: rgba(30, 58, 138, 0.35); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 6px; padding: 4px 8px; text-align: center; color: #bfdbfe; font-weight: 700; font-size: 0.74em; margin-bottom: 4px; }

.thankyou-box {
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid #10b981;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 8px 0;
    text-align: center;
}
.thankyou-title { color: #34d399; font-size: 0.95em; font-weight: 700; margin-bottom: 2px; }
.thankyou-sub { color: #e2e8f0; font-size: 0.8em; }

.alrajhi-card {
    background: #111418;
    border: 1.5px solid #2d3748;
    border-radius: 14px;
    padding: 12px;
    margin: 8px 0;
    color: #ffffff;
}
.card-top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 5px; margin-bottom: 8px; }
.bank-title { font-size: 0.9em; font-weight: 700; color: #f8fafc; }
.price-pill { background: #10b981; color: #022c22; padding: 2px 7px; border-radius: 12px; font-weight: 700; font-size: 0.8em; }
.qr-container { background: #ffffff; padding: 6px; border-radius: 8px; display: inline-block; margin: 2px auto 6px auto; }
.qr-container img { display: block; width: 115px; height: 115px; }
.card-owner { font-size: 1em; font-weight: 700; color: #f8fafc; margin-bottom: 6px; text-align: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.12); padding-bottom: 5px; }
.copy-badge {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 8px;
    font-family: monospace;
    font-size: 0.84em;
    color: #38bdf8;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    margin-bottom: 5px;
}

.wa-btn {
    display: block;
    width: 100%;
    background: #25D366;
    color: white !important;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    font-weight: 700;
    text-decoration: none;
    margin-top: 6px;
    font-size: 0.88em;
}

.support-btn {
    display: block;
    width: 100%;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #cbd5e1 !important;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    margin-top: 10px;
    font-size: 0.8em;
}

.padel-court { background: #064e3b; border: 1.5px solid rgba(16, 185, 129, 0.6); border-radius: 10px; padding: 8px; margin: 8px 0; }
.court-title { text-align: center; color: #a7f3d0; font-weight: 700; font-size: 0.85em; margin-bottom: 6px; border-bottom: 1px dashed rgba(16, 185, 129, 0.4); padding-bottom: 3px; }
.court-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.slot-box { background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 5px 3px; text-align: center; min-height: 44px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.slot-occupied { color: #f4f4f5; font-weight: 600; font-size: 0.78em; line-height: 1.2; }
.slot-meta { display: flex; align-items: center; justify-content: center; gap: 3px; font-size: 0.65em; margin-top: 2px; flex-wrap: wrap; }
.slot-empty { color: #64748b; font-size: 0.72em; }
.badge-loyalty { background-color: #1e3a8a; color: #93c5fd; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 600; }
.badge-level { background-color: rgba(255, 255, 255, 0.1); color: #e2e8f0; padding: 1px 3px; border-radius: 3px; font-size: 0.68em; font-weight: 500; }

div[data-testid="stTextInput"]:has(input[aria-label="hp_security_field"]) { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد قاعدة البيانات السحابية (Google Sheets)
# ==========================================
COURT_CAPACITY = 6
SHEET_COLUMNS = ["id", "name", "phone", "session_day", "court", "level", "status", "payment_status", "hear_about", "player_note", "created_at"]
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1j7NcXOzoKk6ldBN4FZ9_Y4ejhEdwl5O8_y3uYvledz8/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(spreadsheet=GSHEET_URL, worksheet="bookings", ttl=0)
        if df.empty or "phone" not in df.columns:
            return pd.DataFrame(columns=SHEET_COLUMNS)
        df["phone"] = df["phone"].astype(str).str.replace(r"^'", "", regex=True)
        return df
    except Exception:
        return pd.DataFrame(columns=SHEET_COLUMNS)

def save_data(df):
    conn.update(spreadsheet=GSHEET_URL, worksheet="bookings", data=df)

# ==========================================
# 3. المنطق ودوال المعالجة
# ==========================================
def clean_and_validate_sa_phone(raw_phone):
    if not raw_phone:
        return None
    ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    p = str(raw_phone).translate(ar_digits).strip()
    p = re.sub(r'[\s\-\(\)\+]', '', p)
    if p.startswith("966"):
        p = "0" + p[3:]
    elif p.startswith("5"):
        p = "0" + p
    if re.match(r"^05[0-9]{8}$", p):
        return p
    return None

def get_next_session():
    ksa_tz = timezone(timedelta(hours=3))
    now = datetime.now(ksa_tz)
    weekday = now.weekday()

    schedule = {
        6: (0, "الأحد"),
        0: (1, "الثلاثاء"),
        1: (0, "الثلاثاء"),
        2: (1, "الخميس"),
        3: (0, "الخميس"),
        4: (2, "الأحد"),
        5: (1, "الأحد")
    }
    
    days_to_add, d_ar = schedule.get(weekday, (0, "الأحد"))
    target_date = now + timedelta(days=days_to_add)
    label_ar = f"{d_ar} ({target_date.strftime('%d/%m')})"
    db_key = f"{d_ar} {target_date.strftime('%Y-%m-%d')}"
    return label_ar, db_key

def get_session_lists(df, db_session_key):
    if df.empty:
        return [], []
    session_df = df[df["session_day"] == db_session_key]
    confirmed = session_df[session_df["status"] == "confirmed"].head(COURT_CAPACITY).to_dict("records")
    waitlist = session_df[session_df["status"] == "waitlist"].to_dict("records")
    return confirmed, waitlist

def calculate_loyalty(df, phone):
    if df.empty:
        return 0
    return len(df[(df["phone"] == str(phone)) & (df["status"] == "confirmed")]["session_day"].unique())

def get_level_badge(lvl):
    if lvl in ["Advanced", "متقدم"]:
        return "🔥 متقدم"
    elif lvl in ["Beginner", "مبتدئ"]:
        return "⚪ مبتدئ"
    return "🟢 متوسط"

# ==========================================
# 4. بناء الواجهة
# ==========================================
df_all = get_data()
display_session, db_session_key = get_next_session()
c1, waitlist = get_session_lists(df_all, db_session_key)
total_booked = len(c1)

st.markdown("<div class='hero-header'>بادل 99.</div>", unsafe_allow_html=True)
st.markdown(f"<div class='hero-sub'>تمرين {display_session}. متعة اللعب، بتنظيم أبسط.</div>", unsafe_allow_html=True)
st.markdown("<div class='contrast-pill'>⚡ حجز فوري • 6 لاعبين للملعب • السابع علينا.</div>", unsafe_allow_html=True)
st.markdown("<div class='promo-badge'>✨ العب 6 تمارين واحصل على السابع مجاناً</div>", unsafe_allow_html=True)
st.caption(f"⏰ 9:30 م إلى 11:00 م | كورت 1 • <b>المؤكدين: {total_booked}/6</b>", unsafe_allow_html=True)

tab_book, tab_rules, tab_cancel = st.tabs(["⚡ حجز مقعد", "📜 القواعد", "❌ اعتذار"])

# --- تبويب الحجز ---
with tab_book:
    with st.form("booking_form", clear_on_submit=True):
        f_name = st.text_input("الاسم الثلاثي")
        f_phone = st.text_input("رقم الجوال (05xxxxxxxx)", placeholder="05xxxxxxxx")
        f_level_raw = st.selectbox("مستوى اللعب", [
            "🟢 متوسط - تبادل وثبات",
            "🔥 متقدم - سرعة وتكتيك",
            "⚪ مبتدئ - انطلاقة وتعلّم"
        ])
        f_level = "متوسط" if "متوسط" in f_level_raw else ("متقدم" if "متقدم" in f_level_raw else "مبتدئ")
        
        with st.expander("💡 استبيان سريع (اختياري)", expanded=False):
            f_source = st.selectbox("كيف سمعت عن بادل 99؟", ["قروب واتساب", "توصية من صديق", "منصة إكس أو تيك توك", "أخرى"])
            f_note = st.text_input("ملاحظة أو اقتراح لتمرين اليوم:", placeholder="مثلاً: تفضيل كور معينة أو وقت...")

        honeypot_val = st.text_input("hp_security_field", key="hp_val", label_visibility="collapsed")
        btn_submit = st.form_submit_button("تأكيد الانضمام 🚀", use_container_width=True)

        if btn_submit:
            if honeypot_val:
                st.error("تم رفض الطلب للاشتباه في نشاط آلي.")
                st.stop()
                
            clean_name = f_name.strip()
            clean_phone = clean_and_validate_sa_phone(f_phone)

            if len(clean_name) < 2 or not clean_phone:
                st.error("فضلاً أدخل الاسم ورقم جوال صحيح يبدأ بـ 05.")
            else:
                current_df = get_data()
                active_mask = (current_df["phone"] == clean_phone) & (current_df["session_day"] == db_session_key) & (current_df["status"].isin(["confirmed", "waitlist"]))
                
                if not current_df.empty and active_mask.any():
                    st.warning("أنت مسجل بالفعل في تمرين اليوم.")
                else:
                    cur_confirmed = len(current_df[(current_df["session_day"] == db_session_key) & (current_df["status"] == "confirmed")]) if not current_df.empty else 0
                    status_val = "confirmed" if cur_confirmed < COURT_CAPACITY else "waitlist"
                    
                    new_id = int(current_df["id"].max() + 1) if (not current_df.empty and "id" in current_df.columns and len(current_df) > 0 and pd.notna(current_df["id"].max())) else 1
                    
                    new_entry = {
                        "id": new_id,
                        "name": clean_name,
                        "phone": f"'{clean_phone}",
                        "session_day": db_session_key,
                        "court": 1,
                        "level": f_level,
                        "status": status_val,
                        "payment_status": "pending",
                        "hear_about": f_source,
                        "player_note": f_note,
                        "created_at": datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M")
                    }
                    
                    updated_df = pd.concat([current_df, pd.DataFrame([new_entry])], ignore_index=True)
                    save_data(updated_df)
                    
                    wait_pos = len(updated_df[(updated_df["session_day"] == db_session_key) & (updated_df["status"] == "waitlist")]) if status_val == "waitlist" else None

                    st.session_state["last_booking"] = {
                        "name": clean_name,
                        "phone": clean_phone,
                        "status": status_val,
                        "wait_pos": wait_pos,
                        "session": display_session,
                        "is_new": True
                    }
                    st.rerun()

    if "last_booking" in st.session_state:
        lb = st.session_state["last_booking"]
        if lb["status"] == "confirmed":
            if lb.get("is_new", False):
                st.balloons()
                lb["is_new"] = False

            st.markdown(f"""
            <div class="thankyou-box">
                <div class="thankyou-title">✅ تم تأكيد حجزك بنجاح! شكراً لك يا كابتن {lb['name']}</div>
                <div class="thankyou-sub">تم حجز مقعدك في <b>{lb['session']}</b>. نلتقي في الملعب!</div>
            </div>
            """, unsafe_allow_html=True)
            
            iban_raw = "SA9380000222608016013114"
            iban_display = "SA93 8000 0222 6080 1601 3114"
            acc_raw = "222000010006086013114"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={iban_raw}&color=000000&bgcolor=ffffff"

            card_html = f"""
            <div class="alrajhi-card">
                <div class="card-top">
                    <div class="bank-title">🏛️ مصرف الراجحي</div>
                    <div class="price-pill">65 ر.س</div>
                </div>
                <div style="text-align:center;">
                    <div class="qr-container">
                        <img src="{qr_url}" alt="QR" />
                    </div>
                </div>
                <div class="card-owner">فارس ربيع بن عواض العصيمي</div>
                <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الحساب:</div>
                <div class="copy-badge">
                    <span>{acc_raw}</span>
                </div>
                <div style="font-size:0.72em; color:#94a3b8; margin-bottom:2px;">رقم الآيبان:</div>
                <div class="copy-badge">
                    <span>{iban_display}</span>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            wa_msg = f"🎾 تأكيد حجز | بادل 99\n\nالكابتن: {lb['name']}\nالتمرين: {lb['session']} (كورت 1)\nالمبلغ: 65 ر.س\n\nمرفق إشعار التحويل البنكي لحساب كابتن فارس العصيمي."
            wa_url = f"https://wa.me/966566261868?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 إرسال إشعار التحويل وتثبيت المقعد</a>', unsafe_allow_html=True)
        else:
            st.info(f"اكتملت المقاعد الأساسية. أنت في قائمة الاحتياط رقم ({lb.get('wait_pos', 1)}). سيتم إشعارك وتصعيدك تلقائياً فور توفر مقعد.")

# --- تبويب القواعد ---
with tab_rules:
    st.markdown("""
    <div style="background:#18181b; border:1px solid #27272a; border-radius:10px; padding:10px; margin:8px 0; font-size:0.82em; color:#e2e8f0; line-height:1.4;">
        <div style="margin-bottom:8px;">⏱️ <b>قبل 4 ساعات:</b> استرجاع كامل أو ترحيل فوري لتمرينك القادم.</div>
        <div style="margin-bottom:8px;">⚠️ <b>أقل من 4 ساعات:</b> يُسترجع المبلغ فور تأكيد لاعب بديل من قائمة الانتظار.</div>
        <div>⚡ <b>تأكيد فوري:</b> أرسل إشعار التحويل خلال 15 دقيقة لضمان تثبيت مقعدك.</div>
    </div>
    """, unsafe_allow_html=True)

# --- تبويب الاعتذار والإلغاء ---
with tab_cancel:
    with st.form("cancel_form", clear_on_submit=True):
        can_phone_raw = st.text_input("رقم الجوال المسجل")
        can_reason = st.selectbox("سبب الاعتذار", [
            "تعارض في المواعيد أو انشغال طارئ",
            "إجهاد بدني أو إصابة",
            "ظرف عائلي طارئ",
            "صعوبة في المواصلات"
        ])
        btn_cancel_sub = st.form_submit_button("إلغاء المقعد وإتاحته للبديل", use_container_width=True)

        if btn_cancel_sub:
            clean_cp = clean_and_validate_sa_phone(can_phone_raw)
            if not clean_cp:
                st.error("فضلاً أدخل رقم جوال صحيح.")
            else:
                current_df = get_data()
                mask = (current_df["phone"] == clean_cp) & (current_df["session_day"] == db_session_key) & (current_df["status"].isin(["confirmed", "waitlist"]))
                
                if not current_df.empty and mask.any():
                    idx = current_df[mask].index[0]
                    was_confirmed = current_df.loc[idx, "status"] == "confirmed"
                    player_name = current_df.loc[idx, "name"]
                    
                    current_df.loc[idx, "status"] = "cancelled"
                    
                    promoted_name = None
                    if was_confirmed:
                        wait_mask = (current_df["session_day"] == db_session_key) & (current_df["status"] == "waitlist")
                        if wait_mask.any():
                            wait_idx = current_df[wait_mask].index[0]
                            current_df.loc[wait_idx, "status"] = "confirmed"
                            promoted_name = current_df.loc[wait_idx, "name"]
                    
                    save_data(current_df)
                    st.success(f"تم إلغاء الحجز بنجاح يا كابتن {player_name}.")
                    if promoted_name:
                        st.info(f"⚡ تم تصعيد الكابتن **{promoted_name}** من قائمة الانتظار للملعب مباشرة!")
                    if "last_booking" in st.session_state:
                        del st.session_state["last_booking"]
                    st.rerun()
                else:
                    st.error("لا يوجد حجز نشط مرتبط بهذا الرقم لتمرين اليوم.")

# ==========================================
# 5. تشكيلة الملعب
# ==========================================
st.markdown("---")
slots_html = ""
for i in range(COURT_CAPACITY):
    if i < len(c1):
        p = c1[i]
        loyalty_val = calculate_loyalty(df_all, p["phone"])
        points = (loyalty_val % 7)
        pts_badge = f"⭐ {points}/6" if points < 6 else "🎁 مجاني!"
        pay_icon = "✅" if p.get("payment_status") == "paid" else "⏳"
        lvl_badge = get_level_badge(p.get("level", "متوسط"))
        slots_html += f'''<div class="slot-box">
            <div class="slot-occupied">🎾 {p["name"]}</div>
            <div class="slot-meta">
                <span class="badge-level">{lvl_badge}</span>
                <span class="badge-loyalty">{pts_badge}</span>
                <span>{pay_icon}</span>
            </div>
        </div>'''
    else:
        slots_html += '<div class="slot-box"><div class="slot-empty">مقعد شاغر ✨</div></div>'

st.markdown(f'<div class="padel-court"><div class="court-title">🏟️ كورت 1 ({len(c1)}/{COURT_CAPACITY})</div><div class="court-grid">{slots_html}</div></div>', unsafe_allow_html=True)

if waitlist:
    st.caption("📋 **قائمة الانتظار النشطة:** " + " • ".join([f"#{idx+1} {w['name']}" for idx, w in enumerate(waitlist)]))

# ==========================================
# 6. الدعم والمساعدة
# ==========================================
support_msg = "مرحباً كابتن فارس، عندي استفسار بخصوص حجز بادل 99."
support_url = f"https://wa.me/966566261868?text={urllib.parse.quote(support_msg)}"
st.markdown(f'<a href="{support_url}" target="_blank" class="support-btn">💬 تواجه مشكلة؟ تواصل مباشرة عبر واتساب</a>', unsafe_allow_html=True)

# ==========================================
# 7. لوحة الإدارة السحابية
# ==========================================
with st.expander("⚙️ لوحة الإدارة والتحليلات", expanded=False):
    pin_input = st.text_input("رمز الإدارة المشفر:", type="password")
    
    if pin_input:
        ar_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        p = str(pin_input).translate(ar_digits).strip()
        
        if hmac.compare_digest(p, "Padel99#Master@2026"):
            st.success("تم تأكيد الهوية 👑")
            df_current = get_data()
            
            if not df_current.empty:
                total_confirmed = len(df_current[df_current["status"] == "confirmed"])
                total_paid = len(df_current[df_current["payment_status"] == "paid"])
                
                c_kpi1, c_kpi2 = st.columns(2)
                c_kpi1.metric("إجمالي الحجوزات السحابية", total_confirmed)
                c_kpi2.metric("المؤكد دفعهم", f"{total_paid * 65} ر.س")
                
                csv_data = df_current.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 تصدير السجل النظيف (Excel/CSV)",
                    csv_data,
                    f"padel_cloud_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )
                
                st.markdown("---")
                st.markdown("##### 🗑️ إدارة البيانات:")
                col_reset1, col_reset2 = st.columns(2)
                with col_reset1:
                    if st.button("تصفير تمرين اليوم فقط 🔄", use_container_width=True):
                        df_filtered = df_current[df_current["session_day"] != db_session_key]
                        save_data(df_filtered)
                        st.success("تم تصفير تمرين اليوم بنجاح!")
                        st.rerun()
                with col_reset2:
                    if st.button("تصفير قاعدة البيانات بالكامل ⚠️", use_container_width=True):
                        save_data(pd.DataFrame(columns=SHEET_COLUMNS))
                        st.success("تم تصفير كافة البيانات سحابياً!")
                        st.rerun()
        else:
            st.error("رمز الدخول غير صحيح.")
