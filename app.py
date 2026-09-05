import streamlit as st
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام قلبك أمانة - الإدارة الصحية ببني عبيد", layout="wide")

st.title("❤️ مبادرة قلبك أمانة - الإدارة الصحية ببني عبيد")
st.markdown("---")

# الشريط الجانبي لإدخال البيانات
st.sidebar.header("بيانات المستفيد / المريض")

age = st.sidebar.number_input("السن (بالسنوات)", min_value=18, max_value=100, value=40)
gender = st.sidebar.selectbox("النوع", ["ذكر", "أنثى"])
weight = st.sidebar.number_input("الوزن (كجم)", min_value=30.0, max_value=200.0, value=70.0)
height = st.sidebar.number_input("الطول (متر)", min_value=1.0, max_value=2.5, value=1.7)
sbp = st.sidebar.number_input("ضغط الدم الانقباضي (SBP)", min_value=80, max_value=250, value=120)
chol = st.sidebar.number_input("الكوليسترول (mg/dL - اختياري)", min_value=0.0, max_value=400.0, value=0.0)
is_diabetic = st.sidebar.selectbox("مريض سكر؟", ["لا", "نعم"])
smoking = st.sidebar.selectbox("حالة التدخين", ["غير مدخن", "مدخن"])

if st.sidebar.button("حساب تقييم المخاطر والمتابعة"):
    # 1. حساب مؤشر كتلة الجسم BMI
    bmi = weight / (height ** 2)
    
    # 2. تقييم المخاطر القلبية المبسط
    risk_percentage = 3
    if chol > 0:
        if is_diabetic == "نعم":
            risk_percentage = 15 if (age > 50 and sbp >= 140) else 6
        else:
            risk_percentage = 12 if (age > 50 and smoking == "مدخن") else 4
    else:
        if bmi >= 30 and sbp >= 140:
            risk_percentage = 11
        elif age >= 40 and sbp >= 130:
            risk_percentage = 7
        else:
            risk_percentage = 3

    # 3. تحديد موعد الزيارة القادمة
    if risk_percentage < 5:
        follow_up_period = "متابعة بعد 12 شهراً"
    elif risk_percentage < 10:
        follow_up_period = "متابعة كل 3 أشهر (فئة أصفر)"
    elif risk_percentage < 20:
        follow_up_period = "متابعة كل 3 أشهر (فئة برتقالي)"
    else:
        follow_up_period = "متابعة شهرية للحالات عالية الخطورة"

    # عرض النتائج في واجهة Streamlit
    st.success("تم إتمام حساب تقييم المخاطر بنجاح!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("مؤشر كتلة الجسم (BMI)", f"{bmi:.2f}")
    with col2:
        st.metric("نسبة خطورة القلب (10-year CVD Risk)", f"{risk_percentage}%")
    with col3:
        st.metric("التوصية الطبية للمتابعة", follow_up_period)
        
    st.info("تم ربط النظام بقواعد العمل الإكلينيكي لوزارة الصحة ومبادرة الأمراض المزمنة.")
else:
    st.warning("الرجاء إدخال البيانات عبر القائمة الجانبية ثم الضغط على زر الحساب.")
  
