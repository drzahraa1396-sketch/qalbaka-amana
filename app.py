import streamlit as st
import pandas as pd

# ضبط إعدادات الصفحة
st.set_page_config(
    page_title="برنامج قلبك أمانة - الإدارة الصحية ببني عبيد",
    page_icon="🫀",
    layout="wide"
)

# تهيئة الذاكرة لحفظ سجل المرضى اليومي
if "patient_records" not in st.session_state:
    st.session_state.patient_records = []

# رأس الصفحة باسم الإدارة الصحية
st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>مصر - وزارة الصحة والسكان</h3>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #0D9488;'>الإدارة الصحية ببني عبيد</h2>", unsafe_allow_html=True)
st.title("🫀 برنامج قلبك أمانة - تقييم مخاطر أمراض القلب والأوعية الدموية")
st.caption("بروتوكول الرعاية الصحية الأولية (MOHP / WHO Protocol) - بني عبيد")

# إنشاء التبويبات الرئيسية
tab1, tab2, tab3, tab4 = st.tabs([
    "🩺 تقييم مريض جديد", 
    "📊 سجل المرضى والتصدير (Excel)", 
    "💊 بروتوكول العلاج والـ Statins", 
    "📣 الرسائل التثقيفية للمريض"
])

# ---------------------------------------------------------
# التبويب الأول: تقييم المريض وحساب الخطورة
# ---------------------------------------------------------
with tab1:
    st.header("إدخال بيانات المريض والتقييم السريع")
    
    with st.form("patient_assessment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("اسم المريض / الرقم القومي (اختياري)")
            age = st.number_input("العمر (سنة)", min_value=40, max_value=74, value=50, help="مخصص للفئة من 40 إلى 74 سنة")
            gender = st.selectbox("النوع", ["ذكر", "أنثى"])
            smoker = st.selectbox("حالة التدخين", ["لا يدخن", "مدخن"])
            has_ascvd = st.checkbox("هل لدى المريض تاريخ مرضي لأمراض القلب/الشرايين (ASCVD أو CKD)؟")

        with col2:
            sbp = st.number_input("ضغط الدم الانقبائي SBP (mmHg)", min_value=90, max_value=220, value=130)
            diabetes = st.selectbox("هل المريض مصاب بالسكر؟", ["لا", "نعم"])
            bmi = st.number_input("معامل كتلة الجسم BMI (kg/m²)", min_value=15.0, max_value=50.0, value=25.0)
            target_organ_damage = st.checkbox("في حالة السكر: هل يوجد اعتلال بالأعضاء (TOD) أو عوامل خطر متعددة؟")

        submit_btn = st.form_submit_button("حساب الخطورة وإصدار التوصيات 🚀")

    if submit_btn:
        # خوارزمية تحديد شريحة الخطورة بناءً على الجايدلاين
        risk_category = ""
        color_code = ""
        statin_rec = ""
        target_ldl = ""
        aspirin_rec = ""
        follow_up = ""

        # الحالات المسجلة بـ ASCVD أو CKD تكون تلقائياً خطورة مرتفعة >20%
        if has_ascvd:
            risk_category = "خطورة مرتفعة جداً (ASCVD/CKD)"
            color_code = "🔴 أحمر داكن"
            statin_rec = "High-intensity statin (Atorvastatin 40-80 mg / Rosuvastatin 20-40 mg)"
            target_ldl = "< 70 mg/dl"
            aspirin_rec = "موصى به للوقاية الثانوية (Established ASCVD)"
            follow_up = "كل 3 أشهر"
        else:
            if sbp < 140 and bmi < 25 and smoker == "لا يدخن" and diabetes == "لا":
                risk_category = "أقل من 5% (منخفض جداً)"
                color_code = "🟢 أخضر"
                statin_rec = "لا دواعي لبدء Statin للوقاية الأولية"
                target_ldl = "متابعة النسبة الطبيعية"
                aspirin_rec = "غير موصى به للوقاية الأولية الروتينية"
                follow_up = "كل 12 شهراً"
            elif sbp < 160 and bmi < 30:
                risk_category = "5% إلى <10% (منخفض/متوسط)"
                color_code = "🟡 أصفر"
                statin_rec = "نمط حياة صحي ومتابعة الدهون"
                target_ldl = "< 100 mg/dl"
                aspirin_rec = "غير موصى به للوقاية الأولية الروتينية"
                follow_up = "كل 3 أشهر حتى تحقيق الهدف، ثم كل 6-9 أشهر"
            elif sbp < 180:
                risk_category = "10% إلى <20% (متوسط)"
                color_code = "🟠 برتقالي"
                if diabetes == "نعم":
                    statin_rec = "Moderate-intensity statin (Atorvastatin 20 mg)"
                    target_ldl = "< 100 mg/dl"
                else:
                    statin_rec = "تقييم نمط الحياة والعلاج الدوائي إذا استمر الضغط/الدهون مرتفعة"
                    target_ldl = "< 100 mg/dl"
                aspirin_rec = "غير موصى به روتينياً"
                follow_up = "كل 3 إلى 6 أشهر"
            else:
                risk_category = "20% وأكثر (مرتفع)"
                color_code = "🔴 أحمر"
                if diabetes == "نعم" and target_organ_damage:
                    statin_rec = "High-intensity statin (Atorvastatin 40-80 mg / Rosuvastatin 20-40 mg)"
                    target_ldl = "< 70 mg/dl"
                else:
                    statin_rec = "Moderate-intensity statin (Atorvastatin 20 mg)"
                    target_ldl = "< 100 mg/dl"
                aspirin_rec = "يمكن دراسته للسن من 40-70 سنة إذا كان خطر النزيف منخفضاً"
                follow_up = "كل 3 أشهر"

        # عرض التقرير والنتائج للمستخدم
        st.markdown("---")
        st.subheader("📋 نتيجة التقييم والتوصيات العلاجية:")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("شريحة الخطورة", risk_category)
        col_res2.metric("رمز اللون", color_code)
        col_res3.metric("ميعاد المتابعة القادمة", follow_up)

        st.info(f"💊 **توصية الـ Statin والدهون:** {statin_rec} | **مستوى LDL المستهدف:** {target_ldl}")
        st.warning(f"🩸 **توصية الأسبرين:** {aspirin_rec}")

        # حفظ البيانات في السجل اليومي
        patient_data = {
            "الإدارة الصحية": "بني عبيد",
            "اسم/رقم المريض": patient_id if patient_id else "غير مدون",
            "العمر": age,
            "النوع": gender,
            "التدخين": smoker,
            "الضغط SBP": sbp,
            "مصاب بالسكر": diabetes,
            "معامل BMI": bmi,
            "شريحة الخطورة": risk_category,
            "اللون": color_code,
            "توصية الـ Statin": statin_rec,
            "الهدف من LDL": target_ldl,
            "الأسبرين": aspirin_rec,
            "المتابعة": follow_up
        }
        st.session_state.patient_records.append(patient_data)
        st.success("✅ تم حفظ المريض بنجاح في سجل الإدارة الصحية ببني عبيد!")

# ---------------------------------------------------------
# التبويب الثاني: السجل اليومي وتصدير Excel
# ---------------------------------------------------------
with tab2:
    st.header("📊 سجل حالات الإدارة الصحية ببني عبيد وتصدير البيانات")
    
    if st.session_state.patient_records:
        df = pd.DataFrame(st.session_state.patient_records)
        st.dataframe(df, use_container_width=True)
        
        # تحويل الجدول لملف CSV/Excel جاهز للتنزيل
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📥 تحميل شيت الإكسيل - الإدارة الصحية ببني عبيد (CSV / Excel)",
            data=csv_data,
            file_name="سجل_مرضى_قلبك_أمانة_بني_عبيد.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.write("لم يتم إدخال أي مرضى حتى الآن اليوم.")

# ---------------------------------------------------------
# التبويب الثالث: بروتوكولات الأدوية والجرعات
# ---------------------------------------------------------
with tab3:
    st.header("💊 بروتوكول خفض الدهون والأسبرين (MOHP / WHO Guide)")
    
    col_prot1, col_prot2 = st.columns(2)
    with col_prot1:
        st.subheader("جرعات الـ Statins (Lipid-Lowering)")
        st.markdown("""
        * **High-intensity Statins:**
          * Atorvastatin 40–80 mg أو Rosuvastatin 20–40 mg[span_0](start_span)[span_0](end_span).
          * تخفض الـ LDL بنسبة أكثر من 50%[span_1](start_span)[span_1](end_span).
        * **Moderate-intensity Statins:**
          * Atorvastatin 20 mg أو Rosuvastatin 5–10 mg[span_2](start_span)[span_2](end_span).
          * تخفض الـ LDL بنسبة 30% إلى 50%[span_3](start_span)[span_3](end_span).
        """)
    
    with col_prot2:
        st.subheader("أهداف الـ LDL الموصى بها")
        st.markdown("""
        * **المرضى ذوي ASCVD المثبتة أو خطورة >30%:** أقل من 70 mg/dl[span_4](start_span)[span_4](end_span).
        * **المرضى خطورة >20%:** أقل من 100 mg/dl[span_5](start_span)[span_5](end_span).
        * **مرضى السكر مع TOD أو عوامل خطر متعددة:** أقل من 70 mg/dl[span_6](start_span)[span_6](end_span).
        * **إعادة التقييم:** يتم فحص نسبة الدهون بعد 4–6 أسابيع من بدء العلاج[span_7](start_span)[span_7](end_span).
        """)

# ---------------------------------------------------------
# التبويب الرابع: الرسائل التثقيفية للمريض
# ---------------------------------------------------------
with tab4:
    st.header("📣 الرسائل التثقيفية للمريض (Life's Simple 7)")
    st.markdown("""
    1. **🚭 الإقلاع عن التدخين:** التوقف التام دون تقليل التناول فقط؛ لا توجد نسبة آمنة للتدخين[span_8](start_span)[span_8](end_span).
    2. **🏃‍♂️ النشاط البدني:** 150 دقيقة أسبوعياً من المشي السريع (30 دقيقة × 5 أيام أسبوعياً)[span_9](start_span)[span_9](end_span).
    3. **🥗 التغذية الصحية:** الإكثار من الفواكه، الخضروات، الحبوب الكاملة، والأسماك، وتقليل الملح والسكريات والدهون[span_10](start_span)[span_10](end_span).
    4. **🩸 الضغط المستهدف:** المحافظة على الضغط أقل من 140/90 mmHg[span_11](start_span)[span_11](end_span).
    5. **📉 السكر التراكمي:** الوصول بالـ HbA1c لأقل من 7%[span_12](start_span)[span_12](end_span).
    6. **⚖️ الوزن الصحي:** الحفاظ على وزن مناسب وحرق سعرات أكثر من المتناولة[span_13](start_span)[span_13](end_span).
    """)
          
