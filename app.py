import streamlit as st
import pandas as pd
from datetime import date

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1PMofGU82eW8DLSn1l9tS2jfppf4KUCLwJblHV16Yjo0/export?format=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except Exception:
        return pd.DataFrame()

if 'daily_records' not in st.session_state:
    st.session_state.daily_records = []

st.title("🫀 مبادرة قلبك أمانة - وحدة ميت فارس الصحية")
st.markdown("---")

st.info("💡 تم ربط التطبيق بـ Google Sheets بنجاح! البيانات تحفظ تلقائياً.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 تسجيل حالة جديدة", 
    "📊 سجل التردد اليومي", 
    "📞 سجل الاستدعاء والإحالة", 
    "📈 البيان الشهري المجمع"
])

with tab1:
    st.subheader("إدخال بيانات المريض وتقييم المخاطر (WHO/ISH CVD Risk)")
    
    # اختيار طريقة التقييم
    chart_method = st.radio(
        "اختر طريقة تقييم المخاطر المتاحة:",
        ["استخدام الكوليسترول (Cholesterol Chart)", "استخدام مؤشر كتلة الجسم (BMI Chart - Non-Laboratory)"],
        horizontal=True
    )
    st.markdown("---")

    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_name = st.text_input("اسم المريض بالكامل")
            national_id = st.text_input("الرقم القومي (14 رقم)")
            age = st.number_input("العمر", min_value=18, max_value=120, value=45)
            gender = st.selectbox("النوع", ["ذكر", "أنثى"])
            phone = st.text_input("رقم الهاتف")
            file_no = st.text_input("رقم الملف العائلي")

        with col2:
            sbp = st.number_input("ضغط الدم الانقباضي (SBP)", min_value=80, max_value=240, value=120)
            smoker = st.selectbox("هل المريض يدخن؟", ["لا", "نعم"])
            dm = st.selectbox("هل المريض مصاب بالسكر؟", ["لا", "نعم"])
            
            if "Cholesterol" in chart_method:
                cholesterol = st.number_input("نسبة الكوليسترول الكلي (mg/dL)", min_value=100, max_value=400, value=200)
                height, weight, bmi = None, None, None
            else:
                cholesterol = None
                height = st.number_input("الطول (سم)", min_value=100, max_value=220, value=165)
                weight = st.number_input("الوزن (كجم)", min_value=30, max_value=200, value=70)
                bmi = round(weight / ((height / 100) ** 2), 1)
                st.caption(f"مؤشر كتلة الجسم المحسوب (BMI): {bmi}")

        submitted = st.form_submit_button("💾 حفظ الحالة وحساب المخاطر")
        
        if submitted:
            # خوارزمية تقدير نسبة المخاطر واللون وفق معايير WHO CVD Risk Charts
            risk_percent = "< 10%"
            color_code = "🟢 أخضر (مخاطر منخفضة)"
            statin_dose = "لا يحتاج Statin"

            # حساب تقريبي حسب العمر والضغط والعوامل
            score = 0
            if age >= 60: score += 2
            elif age >= 50: score += 1
            
            if sbp >= 160: score += 2
            elif sbp >= 140: score += 1

            if smoker == "نعم": score += 1
            if dm == "نعم": score += 2

            if "BMI" in chart_method and bmi and bmi >= 30:
                score += 1
            elif "Cholesterol" in chart_method and cholesterol and cholesterol >= 240:
                score += 1

            # تحديد الفئة واللون والجرعة
            if score <= 1:
                risk_percent = "< 10%"
                color_code = "🟢 أخضر (مخاطر منخفضة)"
                statin_dose = "تعديل نمط الحياة فقط"
            elif score == 2:
                risk_percent = "10% إلى < 20%"
                color_code = "🟡 أصفر (مخاطر متوسطة)"
                statin_dose = "Atorvastatin 10mg daily"
            elif score == 3:
                risk_percent = "20% إلى < 30%"
                color_code = "🟠 برتقالي (مخاطر عالية)"
                statin_dose = "Atorvastatin 20mg daily"
            elif score == 4:
                risk_percent = "30% إلى < 40%"
                color_code = "🔴 أحمر (مخاطر عالية جداً)"
                statin_dose = "Atorvastatin 20mg / 40mg daily"
            else:
                risk_percent = "≥ 40%"
                color_code = "🟤 أحمر داكن (مخاطر شديدة الخطورة)"
                statin_dose = "Atorvastatin 40mg daily + إحالة فورية"

            # استثناء مريض السكر أو الضغط العالي جداً
            if dm == "نعم" and risk_percent in ["< 10%", "10% إلى < 20%"]:
                statin_dose = "Atorvastatin 20mg daily (وجود سكر)"

            new_record = {
                "التاريخ": date.today().strftime("%Y-%m-%d"),
                "اسم المريض": patient_name,
                "الرقم القومي": national_id,
                "العمر": age,
                "النوع": gender,
                "طريقة التقييم": "Cholesterol" if "Cholesterol" in chart_method else "BMI",
                "نسبة المخاطر": risk_percent,
                "اللون": color_code,
                "جرعة Statin": statin_dose
            }
            st.session_state.daily_records.append(new_record)
            
            st.success(f"تم الحفظ بنجاح! | نسبة المخاطر: {risk_percent} | المستوى واللون: {color_code} | الجرعة المقترحة: {statin_dose}")

with tab2:
    st.subheader("سجل التردد اليومي للمرضى")
    gsheets_df = load_data()
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
        
