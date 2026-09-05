import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="الإدارة الصحية ببني عبيد - قلبك أمانة", layout="wide")

st.title("الإدارة الصحية ببني عبيد")
st.subheader("نظام تسجيل المتابعة والاستدعاء - مبادرة قلبك أمانة")

# إدخال بيانات المريض الأساسية
with st.form("patient_form"):
    st.write("تسجيل بيانات المريض الجديد / المتردد")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        patient_name = st.text_input("اسم المريض رباعي")
        file_no = st.text_input("رقم الملف العائلي")
        phone = st.text_input("رقم الموبايل")
        
    with col2:
        age = st.number_input("السن", min_value=18, max_value=100, value=40)
        gender = st.selectbox("النوع", ["ذكر", "أنثى"])
        visit_type = st.selectbox("حالة المريض", ["جديد", "متردد (متابعة)"])
        
    with col3:
        weight = st.number_input("الوزن (كجم)", min_value=30.0, max_value=200.0, value=75.0)
        height = st.number_input("الطول (متر)", min_value=1.0, max_value=2.0, value=1.70)
        chart_type = st.selectbox("نوع شارت تقييم المخاطر", ["بمعمل (Lab-based)", "بدون معمل (Non-lab-based)"])

    submitted = st.form_submit_button("حفظ وتحديث السجلات")
    
    if submitted:
        if patient_name and file_no:
            # حساب مؤشر كتلة الجسم BMI
            bmi = weight / (height ** 2)
            
            # تحديد نسبة المخاطر وميعاد المتابعة افتراضياً حسب الـ Guidelines
            risk_percentage = "< 5%"
            next_follow_up = "بعد 12 شهراً"
            
            if bmi >= 30:
                risk_percentage = "5% إلى < 10%"
                next_follow_up = "كل 3 أشهر"
            
            st.success(f"تم تسجيل المريض بنجاح! مؤشر كتلة الجسم: {bmi:.2f}")
            st.info(f"معدل المخاطر المقدر: {risk_percentage} | ميعاد المتابعة القادمة: {next_follow_up}")
            
            # محاكاة الترحيل لجدول المتابعة والاستدعاء
            st.write("---")
            st.write("**بيانات سجل المتابعة والاستدعاء (تم الترحيل تلقائياً):**")
            df_recall = pd.DataFrame({
                "اسم المريض": [patient_name],
                "رقم الملف": [file_no],
                "رقم الموبايل": [phone],
                "ميعاد المتابعة": [next_follow_up],
                "الموقف من المتابعة": ["لم يتم بعد"],
                "الاستدعاء الأول": [""],
                "الاستدعاء الثاني": [""],
                "الاستدعاء الثالث": [""]
            })
            st.dataframe(df_recall)
        else:
            st.error("برجاء إدخال اسم المريض ورقم الملف على الأقل.")
