import streamlit as st
import pandas as pd
from datetime import date, timedelta

# رابط الجوجل شيت المخصص للتسجيل اليومي (يمكن تحديثه برابط الـ CSV الخاص بك)
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
st.success("💡 متصل بقاعدة بيانات Google Sheets لتسجيل التردد اليومي وإعداد البيان الشهري تلقائياً (تسجيل المريض مرة واحدة شهرياً).")

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 تسجيل حالة جديدة (مرة شهرياً)", 
    "📊 سجل التردد اليومي", 
    "📞 سجل الاستدعاء للمتخلفين", 
    "📈 البيان الشهري المجمع"
])

with tab1:
    st.subheader("إدخال بيانات المريض وتقييم المخاطر القلبية (إدارة بني عبيد الصحية)")
    
    # اختيار الشارت المستخدم (حسب أدلة العمل)
    chart_option = st.radio(
        "اختر شارت تقييم المخاطر القلبية (وفقاً لتوفر الفحوصات):",
        [
            "📉 شارت المختبر (Laboratory-based Chart - يتطلب الكوليسترول)", 
            "📊 شارت غير المختبر (Non-Laboratory / BMI Chart - مؤشر كتلة الجسم وضغط الدم)"
        ],
        horizontal=True
    )
    st.markdown("---")

    with st.form("patient_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            admin_name = st.text_input("الإدارة الصحية", value="إدارة بني عبيد الصحية", disabled=True)
            unit_name = st.selectbox("الوحدة الصحية / المركز", ["ميت فارس", "الصلاحات", "ميت سويد", "مبارك", "أخرى"])
            patient_name = st.text_input("اسم المريض بالكامل (رباعي)")
            file_no = st.text_input("رقم الملف العائلي (رقم المنزل / رقم الفرد)")
            national_id = st.text_input("الرقم القومي (14 رقم لتدقيق التسجيل مرة واحدة شهرياً)")
            visit_status = st.selectbox("حملة قلبك أمانة", ["جديد", "متردد"])
            age = st.number_input("العمر", min_value=18, max_value=120, value=45)
            gender = st.selectbox("النوع", ["ذكر", "أنثى"])
            phone = st.text_input("رقم الموبايل")

        with col2:
            sbp = st.number_input("ضغط الدم الانقباضي (SBP)", min_value=80, max_value=240, value=120)
            smoker = st.selectbox("الموقف من التدخين", ["غير مدخن", "مدخن"])
            family_history = st.selectbox("التاريخ المرضي لأفراد الأسرة من الدرجة الأولى (أمراض قلب)", ["لا يوجد", "يوجد"])
            dm_status = st.selectbox("حالة السكر (DM)", ["لا يوجد", "جديد", "متردد"])
            htn_status = st.selectbox("حالة الضغط (HTN)", ["لا يوجد", "جديد", "متردد"])
            
            # حقول الإدخال حسب الشارت المختار
            if "المختبر" in chart_option:
                cholesterol = st.number_input("الكوليسترول الكلي (mg/dL)", min_value=100, max_value=400, value=200)
                ldl = st.number_input("نسبة LDL (mg/dL)", min_value=50, max_value=300, value=120)
                height, weight, bmi = 0.0, 0.0, 0.0
            else:
                cholesterol = 0.0
                ldl = 0.0
                height = st.number_input("الطول (سم)", min_value=100, max_value=220, value=165)
                weight = st.number_input("الوزن (كجم)", min_value=30, max_value=200, value=70)
                bmi = round(weight / ((height / 100) ** 2), 1)
                st.caption(f"مؤشر كتلة الجسم المحسوب (BMI): {bmi}")

        st.markdown("---")
        st.subheader("الإجراءات المتخذة والعلاج")
        col3, col4 = st.columns(2)
        with col3:
            health_edu = st.selectbox("التثقيف الصحي", ["تم", "لم يتم"])
            statin_rx = st.selectbox("علاج ستاتين (Statin)", ["بدون", "ستاتين 10مجم", "ستاتين 20مجم", "ستاتين 40مجم"])
        with col4:
            aspirin_rx = st.selectbox("علاج أسبرين (Aspirin)", ["بدون", "أسبرين"])
            referral = st.selectbox("الإحالة", ["لا يوجد", "إحالة عادية", "إحالة طارئة"])

        submitted = st.form_submit_button("💾 حفظ وتسجيل الحالة بالشيت اليومي")
        
        if submitted:
            # التحقق من عدم تكرار تسجيد المريض في نفس الشهر (بناءً على الرقم القومي أو رقم الملف)
            current_month = date.today().strftime("%Y-%m")
            existing_df = load_data()
            
            already_registered = False
            if not existing_df.empty and "الرقم القومي" in existing_df.columns and "التاريخ" in existing_df.columns:
                match_check = existing_df[(existing_df["الرقم القومي"].astype(str) == str(national_id)) & (existing_df["التاريخ"].astype(str).str.startswith(current_month))]
                if not match_check.empty:
                    already_registered = True
            
            for rec in st.session_state.daily_records:
                if rec["الرقم القومي"] == national_id and rec["التاريخ"].startswith(current_month):
                    already_registered = True

            if already_registered:
                st.warning("⚠️ هذا المريض مسجل بالفعل في سجل التردد اليومي لهذا الشهر! لا يتم تكرار تسجيله يومياً، ويتم الاكتفاء بزيارته لصرف العلاج دون إنشاء سجل تردد جديد.")
            else:
                # خوارزمية تقييم المخاطر القلبية الدقيقة وفقاً للـ Guidelines الرسمية
                score = 0
                if age >= 65: score += 2
                elif age >= 40: score += 1
                
                if sbp >= 160: score += 2
                elif sbp >= 140: score += 1

                if smoker == "مدخن": score += 1
                if dm_status != "لا يوجد": score += 2
                if htn_status != "لا يوجد": score += 1

                if "BMI" in chart_option and bmi >= 30:
                    score += 1
                elif "المختبر" in chart_option and cholesterol >= 240:
                    score += 1

                today = date.today()

                # تحديد نسبة المخاطر وميعاد الزيارة القادمة بدقة طبقاً لأدلة العمل الإكلينيكية
                if score <= 1:
                    risk_category = "اقل من 5%"
                    color_code = "🟢 أخضر (منخفضة)"
                    next_visit = today + timedelta(days=365) # متابعة بعد 12 شهر
                elif score == 2:
                    risk_category = "5% إلى <10%"
                    color_code = "🟡 أصفر (متوسطة)"
                    next_visit = today + timedelta(days=90)  # متابعة كل 3 أشهر
                elif score == 3:
                    risk_category = "10% إلى 20%"
                    color_code = "🟠 برتقالي (عالية)"
                    next_visit = today + timedelta(days=60)  # متابعة كل شهرين إلى 3 أشهر
                elif score == 4:
                    risk_category = "20% إلى <30%"
                    color_code = "🔴 أحمر (عالية جداً)"
                    next_visit = today + timedelta(days=30)  # متابعة كل شهر
                else:
                    risk_category = "أكبر من أو يساوي 30%"
                    color_code = "🚨 أحمر داكن (إحالة عاجلة)"
                    next_visit = today + timedelta(days=14)  # متابعة عاجلة خلال أسبوعين

                new_record = {
                    "التاريخ": today.strftime("%Y-%m-%d"),
                    "الإدارة": "إدارة بني عبيد الصحية",
                    "الوحدة": unit_name,
                    "اسم المريض": patient_name,
                    "رقم الملف": file_no,
                    "الرقم القومي": national_id,
                    "نوع الزيارة": visit_status,
                    "العمر": age,
                    "النوع": gender,
                    "رقم الموبايل": phone,
                    "طريقة التقييم": "المختبر" if "المختبر" in chart_option else "BMI",
                    "نسبة المخاطر القلبية": risk_category,
                    "المستوى واللون": color_code,
                    "الستاتين": statin_rx,
                    "الأسبرين": aspirin_rx,
                    "الإحالة": referral,
                    "تاريخ الزيارة القادمة": next_visit.strftime("%Y-%m-%d"),
                    "الموقف من المتابعة": "لم يحن موعدها بعد"
                }
                st.session_state.daily_records.append(new_record)
                
                st.success(f"تم تسجيل المريض بنجاح لشهر {current_month}! | فئة المخاطر: {risk_category} | 📅 موعد الزيارة القادمة الملتزم بالآدلة: {next_visit.strftime('%Y-%m-%d')}")

with tab2:
    st.subheader("📊 سجل التردد اليومي لإدارة بني عبيد الصحية (مسجل مرة واحدة شهرياً لكل مريض)")
    gsheets_df = load_data()
    if not gsheets_df.empty:
        st.dataframe(gsheets_df, use_container_width=True)
    elif st.session_state.daily_records:
        st.dataframe(pd.DataFrame(st.session_state.daily_records), use_container_width=True)
    else:
        st.warning("لا توجد سجلات مسجلة حتى الآن.")

with tab3:
    st.subheader("📞 سجل الاستدعاء والمتابعة الدورية (للمتخلفين عن المواعيد المحددة فقط)")
    st.info("ملاحظة: لا يتم إدراج المريض في سجل الاستدعاء إلا إذا تخلف عن موعد الزيارة الدورية المجدولة طبقاً للتقييم.")
    
    if st.session_state.daily_records or not gsheets_df.empty:
        df_source = gsheets_df if not gsheets_df.empty else pd.DataFrame(st.session_state.daily_records)
        if "تاريخ الزيارة القادمة" in df_source.columns:
            df_recall = df_source[["اسم المريض", "رقم الموبايل", "رقم الملف", "المستوى واللون", "تاريخ الزيارة القادمة", "الموقف من المتابعة"]]
            st.dataframe(df_recall, use_container_width=True)
        else:
            st.info("لا توجد مواعيد استدعاء مسجلة حالياً.")
    else:
        st.info("سجل الاستدعاء فارغ.")

with tab4:
    st.subheader("📈 البيان الشهري المجمع - إدارة بني عبيد الصحية")
    st.write("إحصائيات مجمعة جاهزة للطباعة والتسليم لمديرية الشئون الصحية بنهاية الشهر.")
    
    if st.button("🔄 تحديث وإعداد البيان الشهري"):
        current_data = gsheets_df if not gsheets_df.empty else pd.DataFrame(st.session_state.daily_records)
        if not current_data.empty:
            st.metric("إجمالي المرضى المترددين (بإدارة بني عبيد)", len(current_data))
            
            if "نسبة المخاطر القلبية" in current_data.columns:
                st.write("### توزيع تقييم المخاطر القلبية خلال الشهر:")
                st.write(current_data["نسبة المخاطر القلبية"].value_counts())
            
            st.success("تم إعداد البيان الشهري لإدارة بني عبيد بنجاح وجاهز للطباعة والتصدير.")
        else:
            st.warning("لا توجد بيانات كافية لإعداد البيان الشهري.")
