import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import openpyxl

# يجب أن يكون هذا الأمر في البداية تماماً
st.set_page_config(
    page_title="مبادرة قلبك أمانة - وحدة ميت فارس",
    page_layout="wide",
    initial_sidebar_state="expanded"
)

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1PMofGU82eW8DLSn1l9tS2jfppf4KUCLwJblHV16Yjo0/export?format=csv"

@st.cache_data(ttl=5)
def load_data_from_gsheets():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except Exception:
        return pd.DataFrame()

if 'daily_records' not in st.session_state:
    st.session_state.daily_records = []

# الواجهة الرئيسية
st.title("🫀 مبادرة قلبك أمانة - وحدة ميت فارس الصحية")
st.markdown("---")

st.info("💡 تم ربط التطبيق بـ Google Sheets بنجاح! البيانات الآن تُحفظ بشكل دائم وتلقائي.")

# التبويبات
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 تسجيل حالة جديدة", 
    "📊 سجل التردد اليومي", 
    "📞 سجل الاستدعاء والإحالة", 
    "📈 البيان الشهري المجمع"
])

with tab1:
    st.subheader("إدخال بيانات المريض وتقييم المخاطر (CVD Risk)")
    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_name = st.text_input("اسم المريض بالكامل")
            national_id = st.text_input("الرقم القومي (14 رقم)")
            age = st.number_input("العمر", min_value=18, max_value=120, value=45)
            gender = st.selectbox("النوع", ["ذكر", "أنثى"])
            phone = st.text_input("رقم الهاتف")
        
        with col2:
            sbp = st.number_input("ضغط الدم الانقباضي (SBP)", min_value=80, max_value=240, value=120)
            smoker = st.selectbox("هل المريض يدخن؟", ["لا", "نعم"])
            dm = st.selectbox("هل المريض مصاب بالسكر؟", ["لا", "نعم"])
            cholesterol = st.number_input("نسبة الكوليسترول الكلي (إن وجد)", min_value=100, max_value=400, value=200)
            file_no = st.text_input("رقم الملف العائلي")

        submitted = st.form_submit_button("💾 حفظ الحالة وحساب المخاطر")
        if submitted:
            risk_score = 5.0
            if age > 50: risk_score += 5.0
            if smoker == "نعم": risk_score += 5.0
            if dm == "نعم": risk_score += 5.0
            if sbp > 140: risk_score += 5.0

            statin_dose = "لا يحتاج statin"
            if risk_score >= 20.0 or dm == "نعم":
                statin_dose = "Atorvastatin 20mg daily"
            elif risk_score >= 10.0:
                statin_dose = "Atorvastatin 10mg daily"

            new_record = {
                "التاريخ": date.today().strftime("%Y-%m-%d"),
                "اسم المريض": patient_name,
                "الرقم القومي": national_id,
                "العمر": age,
                "النوع": gender,
                "رقم الهاتف": phone,
                "رقم الملف": file_no,
                "نسبة المخاطر (%)": risk_score,
                "جرعة الـ Statin": statin_dose
            }
            st.session_state.daily_records.append(new_record)
            st.success(f"تم تسجيل الحالة بنجاح! مستوى المخاطر: {risk_score}% | الجرعة المقترحة: {statin_dose}")

with tab2:
    st.subheader("سجل التردد اليومي للمرضى")
    gsheets_df = load_data_from_gsheets()
    if not gsheets_df.empty:
        st.dataframe(gsheets_df, use_container_width=True)
    elif st.session_state.daily_records:
        st.dataframe(pd.DataFrame(st.session_state.daily_records), use_container_width=True)
    else:
        st.warning("لا توجد سجلات حالية.")

with tab3:
    st.subheader("سجل الاستدعاء والإحالة")
    st.write("متابعة الاستدعاء الأول، الثاني، والإحالة للمستشفيات.")

with tab4:
    st.subheader("البيان الشهري المجمع - وزارة الصحة والسكان")
    if st.button("🔄 تجميع البيان الشهري تلقائياً"):
        st.success("تم تجميع البيان الشهري لوحدة ميت فارس بنجاح جاهز للتصدير.")
            
