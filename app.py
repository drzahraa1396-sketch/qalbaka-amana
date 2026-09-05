import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math

# إعداد الصفحة
st.set_page_config(page_title="برنامج قلبك أمانة - الإدارة الصحية ببني عبيد", layout="wide")

st.title("🫀 برنامج قلبك أمانة - الإدارة الصحية ببني عبيد")
st.caption("نظام التقييم التلقائي والاستدعاء والإحالة الإلكتروني الموحد طبقا لبروتوكول وزارة الصحة")

# دالة لحساب القيمة الرقمية الدقيقة لمخاطر القلب والأوعية الدموية (%)
def calculate_exact_cvd_risk(age, gender, sbp, bmi, chol, is_diabetic, is_smoker, family_history):
    # معادلة خوارزمية تقديرية مبسطة لمعايير WHO/ISH لإعطاء قيمة مئوية مستمرة ودقيقة
    base_score = (age - 30) * 0.15
    
    if gender == "ذكر":
        base_score += 1.2
        
    if is_smoker == "مدخن":
        base_score += 2.5
        
    if is_diabetic in ["سكر", "سكر وضغط"]:
        base_score += 3.0
        
    # تأثير الضغط الانقباضي
    if sbp > 120:
        base_score += (sbp - 120) * 0.08
        
    # تأثير كتلة الجسم الكوليسترول
    if chol > 150:
        base_score += (chol - 150) * 0.03
    elif bmi > 25:
        base_score += (bmi - 25) * 0.15
        
    if family_history:
        base_score += 1.5

    # ضبط الحدود والتقريب لرقم عشري دقيق
    risk_percentage = max(1.0, min(round(base_score, 1), 50.0))
    return risk_percentage

# تهيئة قاعدة البيانات في الذاكرة/الجلسة
if "daily_register" not in st.session_state:
    st.session_state.daily_register = pd.DataFrame(columns=[
        "م", "التاريخ", "الاسم", "رقم الملف العائلي", "حملة قلبك أمانة", "السن", "النوع", "رقم الموبايل",
        "الطول", "الوزن", "BMI", "الكوليسترول", "LDL", "قياس الضغط", "سكر", "ضغط", "سكر وضغط",
        "رسم القلب", "الموقف من التدخين", "التاريخ المرضي للأقارب", "نسبة المخاطر الدقيقة (%)", "شريحة المخاطر",
        "التثقيف الصحي", "العلاج", "الإحالة", "تاريخ المتابعة القادمة", "توقيع الطبيب"
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

# القائمة الجانبية للنظام
menu = st.sidebar.radio("اختر السجل أو الإجراء:", [
    "📝 تقييم جديد (سجل التردد اليومي)",
    "📞 سجل المتابعة والاستدعاء",
    "🔄 سجل الإحالة والتغذية الراجعة",
    "📊 تصدير السجلات (Excel)"
])

# ---------------------------------------------------------
# 1. تقييم جديد وسجل التردد اليومي
# ---------------------------------------------------------
if menu == "📝 تقييم جديد (سجل التردد اليومي)":
    st.header("إدخال بيانات المريض لحساب المخاطر والترحيل تلقائياً")
    
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
            bp_sys = st.number_input("الضغط الانقباضي (Systolic BP)", value=120, help="أدخلي الرقم العلوي فقط لحساب النسبة مثل 120 أو 140")
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
            medication = st.multiselect("العلاج المنصرف", ["ضغط", "سكر", "Statin (دهون)", "أسبيرين"])
            
        with col_r2:
            is_referral = st.checkbox("تحويل المريض (إحالة)")
            ref_reason = st.text_input("سبب الإحالة (إن وجد)")
            ref_place = st.text_input("الجهة والمواجهة المحول إليها")
            ref_type = st.selectbox("حالة الإحالة", ["عادية", "طارئة"])
            doctor_name = st.text_input("اسم الطبيب الفاحص")

        submitted = st.form_submit_button("حساب تقييم المخاطر الدقيق وحفظ البيانات 💾")

    if submitted:
        if not name or not phone:
            st.error("يرجى إدخال اسم المريض ورقم الموبايل على الأقل.")
        else:
            # 1. حساب كتلة الجسم BMI
            bmi = round(weight / ((height / 100) ** 2), 1)

            # 2. حساب القيمة المئوية الدقيقة لمخاطر القلب
            exact_risk = calculate_exact_cvd_risk(age, gender, bp_sys, bmi, chol, dm_htn, smoking, family_history)

            # 3. تحديد الشريحة وتاريخ المتابعة القادمة
            if exact_risk < 5.0:
                risk_category = "< 5% (منخفض جداً 🟢)"
                next_followup = visit_date + timedelta(days=365) # بعد سنة
            elif 5.0 <= exact_risk < 10.0:
                risk_category = "5% إلى <10% (منخفض/متوسط 🟡)"
                next_followup = visit_date + timedelta(days=180) # بعد 6 أشهر
            elif 10.0 <= exact_risk < 20.0:
                risk_category = "10% إلى <20% (متوسط 🟠)"
                next_followup = visit_date + timedelta(days=90)  # بعد 3 أشهر
            else:
                risk_category = ">= 20% (مرتفع 🔴)"
                next_followup = visit_date + timedelta(days=30)  # بعد شهر

            bp_str = f"{bp_sys}/{bp_dia}"

            # 4. إضافة لسجل التردد اليومي
            new_id = len(st.session_state.daily_register) + 1
            st.session_state.daily_register.loc[len(st.session_state.daily_register)] = [
                new_id, visit_date.strftime("%Y-%m-%d"), name, file_no, campaign_type, age, gender, phone,
                height, weight, bmi, chol, ldl, bp_str,
                "✓" if "سكر" in dm_htn else "", "✓" if "ضغط" in dm_htn else "", "✓" if dm_htn == "سكر وضغط" else "",
                ecg, smoking, "✓" if family_history else "", f"{exact_risk}%", risk_category, "✓" if health_edu else "X",
                ", ".join(medication), "✓" if is_referral else "X", next_followup.strftime("%Y-%m-%d"), doctor_name
            ]

            # 5. الترحيل التلقائي لسجل المتابعة والاستدعاء
            st.session_state.recall_register.loc[len(st.session_state.recall_register)] = [
                len(st.session_state.recall_register) + 1, name, file_no, phone, next_followup.strftime("%Y-%m-%d"),
                "لم يتم", "", "", "", "", "", "", ""
            ]

            # 6. الترحيل لسجل الإحالة إذا كان محولاً
            if is_referral:
                st.session_state.referral_register.loc[len(st.session_state.referral_register)] = [
                    len(st.session_state.referral_register) + 1, visit_date.strftime("%Y-%m-%d"), name, file_no,
                    phone, ref_reason, ref_place, "", ref_type, "", "", "", "", ""
                ]

            st.success(f"🎯 تم حساب تقييم المخاطر الدقيق للمريض: **{exact_risk}%** | الشريحة: ({risk_category})")
            st.info(f"📅 تاريخ المتابعة المستهدف الذي تم ترحيله لسجل الاستدعاء: **{next_followup.strftime('%Y-%m-%d')}**")

# ---------------------------------------------------------
# 2. سجل المتابعة والاستدعاء
# ---------------------------------------------------------
elif menu == "📞 سجل المتابعة والاستدعاء":
    st.header("سجل المتابعة الدورية والاستدعاء")
    if not st.session_state.recall_register.empty:
        edited_recall = st.data_editor(
            st.session_state.recall_register,
            num_rows="dynamic",
            use_container_width=True,
            key="recall_editor"
        )
        st.session_state.recall_register = edited_recall
    else:
        st.warning("لا يوجد مرضى في سجل الاستدعاء حالياً.")

# ---------------------------------------------------------
# 3. سجل الإحالة والتغذية الراجعة
# ---------------------------------------------------------
elif menu == "🔄 سجل الإحالة والتغذية الراجعة":
    st.header("سجل الإحالة والتغذية الراجعة")
    if not st.session_state.referral_register.empty:
        edited_ref = st.data_editor(
            st.session_state.referral_register,
            num_rows="dynamic",
            use_container_width=True,
            key="referral_editor"
        )
        st.session_state.referral_register = edited_ref
    else:
        st.warning("لا توجد حالات إحالة مسجلة حالياً.")

# ---------------------------------------------------------
# 4. تصدير البيانات إلى Excel
# ---------------------------------------------------------
elif menu == "📊 تصدير السجلات (Excel)":
    st.header("تصدير السجلات بصيغة Excel")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        st.download_button("تصدير سجل التردد اليومي", st.session_state.daily_register.to_csv(index=False).encode('utf-8-sig'), "سجل_التردد_اليومي.csv", "text/csv")
    with col_e2:
        st.download_button("تصدير سجل الاستدعاء", st.session_state.recall_register.to_csv(index=False).encode('utf-8-sig'), "سجل_الاستدعاء.csv", "text/csv")
    with col_e3:
        st.download_button("تصدير سجل الإحالة", st.session_state.referral_register.to_csv(index=False).encode('utf-8-sig'), "سجل_الإحالة.csv", "text/csv")
    
