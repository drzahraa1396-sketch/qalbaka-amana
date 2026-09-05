import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# إعداد الصفحة
st.set_page_config(page_title="برنامج قلبك أمانة - وحدة ميت فارس", layout="wide")

st.title("🫀 برنامج قلبك أمانة - وحدة ميت فارس")
st.caption("الإدارة الصحية ببني عبيد - نظام التقييم التلقائي، الاستدعاء، الإحالة، والتقرير الشهري المجمع")

# دالة لحساب القيمة الرقمية الصحيحة لمخاطر القلب (بدون أرقام عشرية)
def calculate_exact_cvd_risk(age, gender, sbp, bmi, chol, is_diabetic, is_smoker, family_history):
    base_score = (age - 30) * 0.15
    
    if gender == "ذكر":
        base_score += 1.2
        
    if is_smoker == "مدخن":
        base_score += 2.5
        
    if is_diabetic in ["سكر", "سكر وضغط"]:
        base_score += 3.0
        
    if sbp > 120:
        base_score += (sbp - 120) * 0.08
        
    if chol > 150:
        base_score += (chol - 150) * 0.03
    elif bmi > 25:
        base_score += (bmi - 25) * 0.15
        
    if family_history:
        base_score += 1.5

    risk_percentage = int(round(base_score))
    return max(1, min(risk_percentage, 50))

# دالة لتحديد التوصية بالستاتين (Statin) والجرعة
def check_statin_recommendation(risk_score, chol, ldl, dm_htn, age):
    reasons = []
    if risk_score >= 20:
        reasons.append("مخاطر عالية جداً (>=20%)")
    if "سكر" in dm_htn:
        reasons.append("مريض سكر")
    if ldl >= 190 or chol >= 240:
        reasons.append("ارتفاع شديد في الكوليسترول/LDL")
    elif risk_score >= 10:
        reasons.append("مخاطر متوسطة إلى عالية (>=10%)")
        
    if reasons:
        if risk_score >= 20 or ldl >= 190:
            dosage = "Atorvastatin 40 mg أو Rosuvastatin 20 mg (شدة عالية High Intensity)"
        else:
            dosage = "Atorvastatin 10-20 mg أو Rosuvastatin 5-10 mg (شدة متوسطة Moderate Intensity)"
        return True, dosage, " + ".join(reasons)
    
    return False, "لا يستدعي العلاج بالستاتين حالياً", "المخاطر منخفضة"

# تهيئة قواعد البيانات في الذاكرة
if "daily_register" not in st.session_state:
    st.session_state.daily_register = pd.DataFrame(columns=[
        "م", "التاريخ", "الاسم", "رقم الملف العائلي", "حملة قلبك أمانة", "السن", "النوع", "رقم الموبايل",
        "الطول", "الوزن", "BMI", "الكوليسترول", "LDL", "قياس الضغط", "سكر", "ضغط", "سكر وضغط",
        "رسم القلب", "الموقف من التدخين", "التاريخ المرضي للأقارب", "نسبة المخاطر (%)", "شريحة المخاطر",
        "التثقيف الصحي", "العلاج", "توصية الستاتين", "الإحالة", "تاريخ المتابعة القادمة", "توقيع الطبيب"
    ])

if "recall_register" not in st.session_state:
    st.session_state.recall_register = pd.DataFrame(columns=[
        "م", "الاسم", "رقم الملف العائلي", "رقم الموبايل", "تاريخ المتابعة", "الموقف من المتابعة",
        "تاريخ الاستدعاء (1)", "الموقف (1)", "تاريخ الاستدعاء (2)", "الموقف (2)",
        "تاريخ الاستدعاء (3)", "الموقف (3)", "القائم بالاستدعاء"
    ])

if "referral_register" not in st.session_state:
    st.session_state.referral_register = pd.DataFrame(columns=[
        "م", "التاريخ", "الاسم", "رقم الملف العائلي", "رقم الموبايل", "سبب الإحالة", "الجهة المحول إليها",
        "التخصص المحول إليه", "حالة المريض", "متابعة (1)", "متابعة (2)", "متابعة (3)", "التغذية الراجعة", "القائم بالمتابعة"
    ])

# القائمة الجانبية
menu = st.sidebar.radio("اختر السجل أو الإجراء:", [
    "📝 تقييم جديد (سجل التردد اليومي)",
    "📞 سجل المتابعة والاستدعاء",
    "🔄 سجل الإحالة والتغذية الراجعة",
    "📊 البيان الشهري المجمع (وحدة ميت فارس)",
    "💾 تصدير السجلات (Excel)"
])

# ---------------------------------------------------------
# 1. تقييم جديد
# ---------------------------------------------------------
if menu == "📝 تقييم جديد (سجل التردد اليومي)":
    st.header("إدخال بيانات المريض وحساب المخاطر والجرعات تلقائياً")
    
    with st.form("patient_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            visit_date = st.date_input("تاريخ الزيارة", datetime.now())
            name = st.text_input("اسم المريض رباعي*")
            file_no = st.text_input("رقم الملف العائلي")
            phone = st.text_input("رقم الموبايل*")
            campaign_type = st.selectbox("حملة قلبك أمانة", ["جديد", "متردد"])
            
        with col2:
            age = st.number_input("السن", min_value=1, max_value=120, value=45)
            gender = st.selectbox("النوع", ["ذكر", "أنثى"])
            height = st.number_input("الطول (سم)", value=165.0)
            weight = st.number_input("الوزن (كجم)", value=70.0)
            bp_sys = st.number_input("الضغط الانقباضي (Systolic BP)", value=120)
            bp_dia = st.number_input("الضغط الانبساطي (Diastolic BP)", value=80)
            
        with col3:
            chol = st.number_input("الكوليسترول (Chol)", value=180)
            ldl = st.number_input("LDL", value=100)
            dm_htn = st.selectbox("الحالة المرضية", ["طبيعي", "سكر", "ضغط", "سكر وضغط"])
            ecg = st.selectbox("رسم القلب", ["لم يتم/طبيعي", "غير طبيعي"])
            smoking = st.selectbox("الموقف من التدخين", ["غير مدخن", "مدخن"])
            family_history = st.checkbox("تاريخ مرضي لأقارب درجة أولى")

        st.subheader("الإجراءات والتوصيات الطبية")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            health_edu = st.checkbox("تم عمل التثقيف الصحي", value=True)
            medication = st.multiselect("العلاج المنصرف", ["ضغط", "سكر", "ستاتين", "أسبيرين"])
            
        with col_r2:
            is_referral = st.checkbox("تحويل المريض (إحالة)")
            ref_reason = st.text_input("سبب الإحالة (إن وجد)")
            ref_place = st.text_input("الجهة والمواجهة المحول إليها")
            ref_type = st.selectbox("حالة الإحالة", ["عادية", "طارئة"])
            doctor_name = st.text_input("اسم الطبيب الفاحص")

        submitted = st.form_submit_button("حساب تقييم المخاطر وتحديد الجرعات وتأكيد الحفظ 💾")

    if submitted:
        if not name or not phone:
            st.error("يرجى إدخال اسم المريض ورقم الموبايل على الأقل.")
        else:
            bmi = round(weight / ((height / 100) ** 2), 1)

            # حساب النسبة كعدد صحيح
            exact_risk = calculate_exact_cvd_risk(age, gender, bp_sys, bmi, chol, dm_htn, smoking, family_history)

            # تحديد الشريحة وتاريخ المتابعة (من 5 إلى 10 كل 3 أشهر)
            if exact_risk < 5:
                risk_category = "< 5% (منخفض جداً 🟢)"
                next_followup = visit_date + timedelta(days=365)
            elif 5 <= exact_risk < 10:
                risk_category = "5% إلى <10% (منخفض/متوسط 🟡)"
                next_followup = visit_date + timedelta(days=90)
            elif 10 <= exact_risk < 20:
                risk_category = "10% إلى <20% (متوسط 🟠)"
                next_followup = visit_date + timedelta(days=90)
            else:
                risk_category = ">= 20% (مرتفع 🔴)"
                next_followup = visit_date + timedelta(days=30)

            # تقييم احتياج الستاتين
            needs_statin, statin_dose, statin_reason = check_statin_recommendation(exact_risk, chol, ldl, dm_htn, age)

            bp_str = f"{bp_sys}/{bp_dia}"

            # إضافة لسجل التردد اليومي
            st.session_state.daily_register.loc[len(st.session_state.daily_register)] = [
                len(st.session_state.daily_register) + 1, visit_date.strftime("%Y-%m-%d"), name, file_no, campaign_type, age, gender, phone,
                height, weight, bmi, chol, ldl, bp_str,
                "✓" if "سكر" in dm_htn else "", "✓" if "ضغط" in dm_htn else "", "✓" if dm_htn == "سكر وضغط" else "",
                ecg, smoking, "✓" if family_history else "", f"{exact_risk}%", risk_category, "✓" if health_edu else "X",
                ", ".join(medication), statin_dose if needs_statin else "لا يتطلب", "✓" if is_referral else "X", next_followup.strftime("%Y-%m-%d"), doctor_name
            ]

            # الترحيل لسجل الاستدعاء
            st.session_state.recall_register.loc[len(st.session_state.recall_register)] = [
                len(st.session_state.recall_register) + 1, name, file_no, phone, next_followup.strftime("%Y-%m-%d"),
                "لم يتم", "", "", "", "", "", "", ""
            ]

            # الترحيل لسجل الإحالة
            if is_referral:
                st.session_state.referral_register.loc[len(st.session_state.referral_register)] = [
                    len(st.session_state.referral_register) + 1, visit_date.strftime("%Y-%m-%d"), name, file_no,
                    phone, ref_reason, ref_place, "", ref_type, "", "", "", "", ""
                ]

            st.success(f"🎯 تقييم المخاطر للمريض: **%{exact_risk}** | الشريحة: ({risk_category})")
            st.info(f"📅 تاريخ المتابعة القادمة: **{next_followup.strftime('%Y-%m-%d')}**")
            
            if needs_statin:
                st.warning(f"💊 **توصية الستاتين (Statin):** المريض يحتاج ستاتين بسبب ({statin_reason})\n\n**الجرعة المقترحة:** {statin_dose}")

# ---------------------------------------------------------
# 2. سجل المتابعة والاستدعاء
# ---------------------------------------------------------
elif menu == "📞 سجل المتابعة والاستدعاء":
    st.header("سجل المتابعة الدورية والاستدعاء")
    if not st.session_state.recall_register.empty:
        edited_recall = st.data_editor(st.session_state.recall_register, num_rows="dynamic", use_container_width=True, key="recall_editor")
        st.session_state.recall_register = edited_recall
    else:
        st.warning("لا يوجد مرضى في سجل الاستدعاء حالياً.")

# ---------------------------------------------------------
# 3. سجل الإحالة
# ---------------------------------------------------------
elif menu == "🔄 سجل الإحالة والتغذية الراجعة":
    st.header("سجل الإحالة والتغذية الراجعة")
    if not st.session_state.referral_register.empty:
        edited_ref = st.data_editor(st.session_state.referral_register, num_rows="dynamic", use_container_width=True, key="referral_editor")
        st.session_state.referral_register = edited_ref
    else:
        st.warning("لا توجد حالات إحالة مسجلة حالياً.")

# ---------------------------------------------------------
# 4. البيان الشهري المجمع (تجميعة وحدة ميت فارس)
# ---------------------------------------------------------
elif menu == "📊 البيان الشهري المجمع (وحدة ميت فارس)":
    st.header("📊 البيان الشهري المجمع لبرنامج قلبك أمانة - وحدة ميت فارس")
    st.info("يتم إحصاء هذه الأرقام تلقائياً من واقع الحالات المسجلة طوال الشهر ومطابقتها لنموذج الوزارة الرسمي.")

    df = st.session_state.daily_register

    if df.empty:
        st.warning("لم يتم تسجيل أي حالات خلال هذا الشهر حتى الآن.")
    else:
        total_new = len(df[df['حملة قلبك أمانة'] == 'جديد'])
        total_rec = len(df[df['حملة قلبك أمانة'] == 'متردد'])
        total_all = len(df)

        age_18_40 = len(df[(df['السن'] >= 18) & (df['السن'] <= 40)])
        age_40_65 = len(df[(df['السن'] > 40) & (df['السن'] <= 65)])
        age_above_65 = len(df[df['السن'] > 65])

        males = len(df[df['النوع'] == 'ذكر'])
        females = len(df[df['النوع'] == 'أنثى'])

        bmi_under_30 = len(df[df['BMI'] < 30])
        bmi_over_30 = len(df[df['BMI'] >= 30])

        dm_new = len(df[(df['سكر'] == '✓') & (df['حملة قلبك أمانة'] == 'جديد')])
        dm_rec = len(df[(df['سكر'] == '✓') & (df['حملة قلبك أمانة'] == 'متردد')])
        
        htn_new = len(df[(df['ضغط'] == '✓') & (df['حملة قلبك أمانة'] == 'جديد')])
        htn_rec = len(df[(df['ضغط'] == '✓') & (df['حملة قلبك أمانة'] == 'متردد')])

        both_new = len(df[(df['سكر وضغط'] == '✓') & (df['حملة قلبك أمانة'] == 'جديد')])
        both_rec = len(df[(df['سكر وضغط'] == '✓') & (df['حملة قلبك أمانة'] == 'متردد')])

        smokers = len(df[df['الموقف من التدخين'] == 'مدخن'])
        non_smokers = len(df[df['الموقف من التدخين'] == 'غير مدخن'])

        fam_yes = len(df[df['التاريخ المرضي للأقارب'] == '✓'])
        fam_no = len(df[df['التاريخ المرضي للأقارب'] == ''])

        # الشرائح
        risk_under_5 = len(df[df['شريحة المخاطر'].str.contains('< 5%', na=False)])
        risk_5_10 = len(df[df['شريحة المخاطر'].str.contains('5% إلى <10%', na=False)])
        risk_10_20 = len(df[df['شريحة المخاطر'].str.contains('10% إلى <20%', na=False)])
        risk_over_20 = len(df[df['شريحة المخاطر'].str.contains('>= 20%', na=False)])

        # الإجراءات والعلاج
        edu_count = len(df[df['التثقيف الصحي'] == '✓'])
        htn_med = len(df[df['العلاج'].str.contains('ضغط', na=False)])
        dm_med = len(df[df['العلاج'].str.contains('سكر', na=False)])
        statin_med = len(df[df['العلاج'].str.contains('ستاتين', na=False)])
        asp_med = len(df[df['العلاج'].str.contains('أسبيرين', na=False)])
        ref_count = len(df[df['الإحالة'] == '✓'])

        # عرض التجميعة في جدول رسمي
        monthly_summary_data = {
            "البند": [
                "الإدارة الصحية", "الوحدة / المركز", "إجمالي قلبك أمانة (جديد)", "إجمالي قلبك أمانة (متردد)", "إجمالي قلبك أمانة (الكلي)",
                "السن (18-40)", "السن (40-65)", "السن (>65)", "النوع (ذكر)", "النوع (أنثى)",
                "BMI (<30)", "BMI (>30)", "سكر (جديد)", "سكر (متردد)", "ضغط (جديد)", "ضغط (متردد)", "سكر+ضغط (جديد)", "سكر+ضغط (متردد)",
                "الموقف من التدخين (مدخن)", "الموقف من التدخين (غير مدخن)", "تاريخ مرضي لأقارب (يوجد)", "تاريخ مرضي لأقارب (لا يوجد)",
                "تقييم المخاطر (< 5%)", "تقييم المخاطر (5 - 10%)", "تقييم المخاطر (10 - 20%)", "تقييم المخاطر (> 20%)",
                "التثقيف الصحي", "علاج ضغط", "علاج سكر", "علاج ستاتين", "علاج أسبيرين", "الإحالة"
            ],
            "القيمة / العدد": [
                "بني عبيد", "ميت فارس", total_new, total_rec, total_all,
                age_18_40, age_40_65, age_above_65, males, females,
                bmi_under_30, bmi_over_30, dm_new, dm_rec, htn_new, htn_rec, both_new, both_rec,
                smokers, non_smokers, fam_yes, fam_no,
                risk_under_5, risk_5_10, risk_10_20, risk_over_20,
                edu_count, htn_med, dm_med, statin_med, asp_med, ref_count
            ]
        }
        
        summary_df = pd.DataFrame(monthly_summary_data)
        st.dataframe(summary_df, use_container_width=True, height=500)

        # زر تحميل الشيت المجمع
        st.download_button(
            label="📥 تحميل البيان الشهري المجمع لوحدة ميت فارس (Excel)",
            data=summary_df.to_csv(index=False).encode('utf-8-sig'),
            file_name="البيان_الشهري_قلبك_أمانة_ميت_فارس.csv",
            mime="text/csv"
        )

# ---------------------------------------------------------
# 5. تصدير السجلات
# ---------------------------------------------------------
elif menu == "💾 تصدير السجلات (Excel)":
    st.header("تصدير السجلات الكاملة بصيغة Excel")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        st.download_button("تصدير سجل التردد اليومي", st.session_state.daily_register.to_csv(index=False).encode('utf-8-sig'), "سجل_التردد_اليومي.csv", "text/csv")
    with col_e2:
        st.download_button("تصدير سجل الاستدعاء", st.session_state.recall_register.to_csv(index=False).encode('utf-8-sig'), "سجل_الاستدعاء.csv", "text/csv")
    with col_e3:
        st.download_button("تصدير سجل الإحالة", st.session_state.referral_register.to_csv(index=False).encode('utf-8-sig'), "سجل_الإحالة.csv", "text/csv")
            
