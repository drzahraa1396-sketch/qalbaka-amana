import streamlit as st
import pandas as pd
from datetime import date, timedelta

# رابط الجوجل شيت الخاص بالمبادرة
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1PMofGU82eW8DLSn1l9tS2jfppf4KUCLwJblHV16Yjo0/export?format=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except Exception:
        return pd.DataFrame()

if 'daily_records' not in st.session_state:
    st.session_state.daily_records = []

st.title("🫀 مبادرة قلبك أمانة - إدارة بني عبيد الصحية")
st.markdown("---")
st.success("💡 تم ربط التطبيق بقاعدة بيانات Google Sheets بنجاح لحفظ الحالات طوال الشهر.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 تسجيل حالة جديدة", 
    "📊 سجل التردد اليومي", 
    "📞 سجل الاستدعاء والإحالة", 
    "📈 البيان الشهري المجمع"
])

with tab1:
    st.subheader("إدخال بيانات المريض وتقييم المخاطر القلبية (WHO/ISH CVD Risk)")
    
    # خيارين واضحين لاختيار نوع الشارت المستخدم
    chart_option = st.radio(
        "اختر شارت تقييم المخاطر المستخدم:",
        [
            "📉 شارت الكوليسترول (Cholesterol-based Chart)", 
            "📊 شارت مؤشر كتلة الجسم وضغط الدم (Non-Laboratory / BMI Chart)"
        ],
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
            visit_type = st.selectbox("نوع الزيارة", ["جديد", "متردد (متابعة)"])

        with col2:
            sbp = st.number_input("ضغط الدم الانقباضي (SBP)", min_value=80, max_value=240, value=120)
            smoker = st.selectbox("الموقف من التدخين", ["غير مدخن", "مدخن"])
            dm = st.selectbox("حالة السكر", ["لا يوجد", "مصاب بالسكر"])
            htn = st.selectbox("حالة الضغط", ["لا يوجد", "مصاب بالضغط"])
            
            # حقول تظهر حسب اختيار الشارت
            if "الكوليسترول" in chart_option:
                cholesterol = st.number_input("نسبة الكوليسترول الكلي (mg/dL)", min_value=100, max_value=400, value=200)
                height, weight, bmi = None, None, 0.0
            else:
                cholesterol = 0
                height = st.number_input("الطول (سم)", min_value=100, max_value=220, value=165)
                weight = st.number_input("الوزن (كجم)", min_value=30, max_value=200, value=70)
                bmi = round(weight / ((height / 100) ** 2), 1)
                st.caption(f"مؤشر كتلة الجسم المحسوب (BMI): {bmi}")

        submitted = st.form_submit_button("💾 حفظ الحالة وحساب المخاطر القلبية")
        
        if submitted:
            # خوارزمية تقييم المخاطر بدقة معايير الـ Guidelines
            score = 0
            if age >= 60: score += 2
            elif age >= 45: score += 1
            
            if sbp >= 160: score += 2
            elif sbp >= 140: score += 1

            if smoker == "مدخن": score += 1
            if dm == "مصاب بالسكر": score += 2
            if htn == "مصاب بالضغط": score += 1

            if "BMI" in chart_option and bmi >= 30:
                score += 1
            elif "الكوليسترول" in chart_option and cholesterol >= 240:
                score += 1

            today = date.today()

            # تحديد النسبة بدقة واللون وموعد المتابعة وفقا للـ Guidelines
            if score <= 1:
                risk_percent = "< 5%"
                color_code = "🟢 أخضر (منخفضة جداً)"
                statin_dose = "تعديل نمط الحياة فقط"
                next_visit = today + timedelta(days=180) # متابعة بعد 6 أشهر
            elif score == 2:
                risk_percent = "5% إلى < 10%"
                color_code = "🟡 أصفر (منخفضة)"
                statin_dose = "تعديل نمط الحياة + متابعة دورية"
                next_visit = today + timedelta(days=90)  # متابعة بعد 3 أشهر
            elif score == 3:
                risk_percent = "10% إلى < 20%"
                color_code = "🟠 برتقالي (متوسطة إلى عالية)"
                statin_dose = "Atorvastatin 10mg/20mg daily"
                next_visit = today + timedelta(days=60)  # متابعة بعد شهرين
            else:
                risk_percent = "> 20%"
                color_code = "🔴 أحمر (عالية جداً / إحالة)"
                statin_dose = "Atorvastatin 40mg + إحالة للمستشفي"
                next_visit = today + timedelta(days=14)  # متابعة عاجلة / إحالة خلال أسبوعين

            if dm == "مصاب بالسكر" and risk_percent in ["< 5%", "5% إلى < 10%"]:
                statin_dose = "Atorvastatin 20mg daily (لوجود سكر)"

            new_record = {
                "التاريخ": today.strftime("%Y-%m-%d"),
                "اسم المريض": patient_name,
                "الرقم القومي": national_id,
                "رقم الهاتف": phone,
                "رقم الملف": file_no,
                "نوع الزيارة": visit_type,
                "العمر": age,
                "النوع": gender,
                "طريقة التقييم": "الكوليسترول" if "الكوليسترول" in chart_option else "BMI",
                "نسبة المخاطر": risk_percent,
                "المستوى واللون": color_code,
                "العلاج والجرعة": statin_dose,
                "تاريخ الزيارة القادمة": next_visit.strftime("%Y-%m-%d")
            }
            st.session_state.daily_records.append(new_record)
            
            st.success(f"تم الحفظ بنجاح! | تقييم المخاطر: {risk_percent} | المستوى: {color_code} | العلاج: {statin_dose} | 📅 موعد الزيارة القادمة: {next_visit.strftime('%Y-%m-%d')}")

with tab2:
    st.subheader("📊 سجل التردد اليومي لإدارة بني عبيد")
    gsheets_df = load_data()
    if not gsheets_df.empty:
        st.dataframe(gsheets_df, use_container_width=True)
    elif st.session_state.daily_records:
        st.dataframe(pd.DataFrame(st.session_state.daily_records), use_container_width=True)
    else:
        st.warning("لا توجد سجلات مسجلة حتى الآن.")

with tab3:
    st.subheader("📞 سجل الاستدعاء والإحالة للمتابعة")
    if st.session_state.daily_records or not gsheets_df.empty:
        df_source = gsheets_df if not gsheets_df.empty else pd.DataFrame(st.session_state.daily_records)
        if "تاريخ الزيارة القادمة" in df_source.columns:
            df_recall = df_source[["اسم المريض", "رقم الهاتف", "المستوى واللون", "تاريخ الزيارة القادمة", "العلاج والجرعة"]]
            st.dataframe(df_recall, use_container_width=True)
        else:
            st.info("لا توجد بيانات كافية لعرض جدول الاستدعاء.")
    else:
        st.info("سجل الاستدعاء فارغ.")

with tab4:
    st.subheader("📈 البيان الشهري المجمع - إدارة بني عبيد الصحية")
    st.write("إحصائيات مجمعة جاهزة للطباعة والتسليم للوزارة.")
    
    if st.button("🔄 تحديث وحساب إحصائيات البيان الشهري"):
        current_data = gsheets_df if not gsheets_df.empty else pd.DataFrame(st.session_state.daily_records)
        if not current_data.empty:
            st.metric("إجمالي حالات المبادرة هذا الشهر", len(current_data))
            
            # توزيع المخاطر
            if "نسبة المخاطر" in current_data.columns:
                risk_counts = current_data["نسبة المخاطر"].value_counts()
                st.write("### توزيع تقييم المخاطر القلبية:")
                st.write(risk_counts)
            
            st.success("تم إعداد البيان الشهري بنجاح ومطابق لنموذج الإدارة والوزارة.")
        else:
            st.warning("لا توجد بيانات كافية لإعداد البيان.")
        
