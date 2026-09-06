import datetime
import pandas as pd
import streamlit as st

# إعداد الصفحة وتصميم الواجهة
st.set_page_config(
    page_title="قلبك أمانة - مبادرة الكشف المبكر", page_icon="❤️", layout="centered"
)

# ترويسة التطبيق والاعتماد الرسمي
st.markdown(
    "<h1 style='text-align: center; color: #d9534f;'>❤️ مبادرة قلبك أمانة</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-weight: bold; color: #555;'>Prepared"
    " by: Dr. Zahraa Yasser Saleh - Banni Ubayd Health Administration</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# نموذج إدخال بيانات المريض الأساسية
st.subheader("بيانات المريض الأساسية والقياسات الحيوية")

col1, col2 = st.columns(2)
with col1:
  patient_name = st.text_input("اسم المريض", "")
  national_id = st.text_input("الرقم القومي (14 رقم)", max_chars=14)

# حساب العمر وتاريخ الميلاد تلقائياً من الرقم القومي المصري
calculated_age = 46  # القيمة الافتراضية التجريبية
if national_id and len(national_id) == 14:
  try:
    century_code = int(national_id[0])
    year_digits = int(national_id[1:3])
    month = int(national_id[3:5])
    day = int(national_id[5:7])

    if century_code == 2:
      birth_year = 1900 + year_digits
    elif century_code == 3:
      birth_year = 2000 + year_digits
    else:
      birth_year = 1900 + year_digits

    birth_date = datetime.date(birth_year, month, day)
    today = datetime.date.today()
    calculated_age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
  except:
    pass

with col2:
  st.metric(label="العمر المحسوب (سنة)", value=calculated_age)
  visit_type = st.selectbox("نوع الزيارة", ["جديد", "متابعة"])

st.markdown("---")
st.subheader("القياسات والتحاليل الأساسية")

c1, c2, c3 = st.columns(3)
with c1:
  height = st.number_input("الطول (سم)", value=165.0, step=0.5)
with c2:
  weight = st.number_input("الوزن (كجم)", value=70.0, step=0.5)
with c3:
  bmi = weight / ((height / 100) ** 2)
  st.metric(label="مؤشر كتلة الجسم (BMI)", value=round(bmi, 1))

s1, s2 = st.columns(2)
with s1:
  sbp = st.number_input("ضغط الدم الانقباضي (SBP)", value=120, step=1)
with s2:
  dbp = st.number_input("ضغط الدم الانبساطي (DBP)", value=80, step=1)

chol = st.number_input("الكوليسترول الكلي (mg/dl)", value=180, step=5)
ldl_val = st.number_input("مستوى LDL (mg/dl)", value=100, step=5)

# عوامل الخطورة والأمراض المزمنة
st.markdown("---")
st.subheader("التاريخ المرضي وعوامل الخطورة")

col_r1, col_r2 = st.columns(2)
with col_r1:
  smoking = st.checkbox("مدخن")
  diabetes = st.checkbox("مريض سكر")
  hypertension = st.checkbox("مريض ضغط")
with col_r2:
  ascvd = st.checkbox("تاريخ مرضي سابق بالقلب (ASCVD)")
  ckd = st.checkbox("مرض كلوي مزمن (CKD)")
  statin_needed = st.checkbox("يوجد توصية علاجية بالستاتين")

statin_intensity = ""
if statin_needed:
  statin_intensity = st.selectbox(
      "جرعة/شدة الستاتين", ["متوسطة", "عالية", "أخرى"]
  )

# حساب تقريبي للخطورة النسبة المئوية
risk_score = 5
if sbp >= 140 or chol >= 240 or diabetes:
  risk_score = 15
if sbp >= 160 or ascvd or ckd:
  risk_score = 25
if smoking and diabetes:
  risk_score = 22

# دالة توليد رسائل التثقيف الصحي بناءً على الكود المرفق[span_0](start_span)[span_0](end_span)
def generate_health_education(data: dict) -> str:
  messages = [
      "رسالة من حملة «قلبك أمانة»",
      (
          "هدفنا مساعدتك على تقليل عوامل الخطورة وحماية القلب والأوعية"
          " الدموية."
      ),
  ]

  if data.get("smoking"):
    messages.append(
        " التدخين: الإقلاع عن التدخين من أهم الخطوات لحماية القلب والأوعية"
        " الدموية. ضع خطة للإقلاع واطلب مساعدة الفريق الطبي إذا احتجت."
    )
  else:
    messages.append(
        " التدخين: استمر في تجنب التدخين وتجنب التعرض المستمر لدخان الآخرين قدر"
        " الإمكان."
    )

  b = data.get("bmi")
  if b is not None:
    if b >= 30:
      messages.append(
          " الوزن: الوزن الزائد قد يزيد من عوامل خطورة القلب. ناقش مع الطبيب"
          " خطة تدريجية مناسبة لتحسين الوزن والنشاط البدني والغذاء."
      )
    elif b >= 25:
      messages.append(
          " الوزن: حاول الحفاظ على وزن صحي، وزيادة النشاط البدني تدريجيًا، واختيار"
          " غذاء متوازن."
      )
    else:
      messages.append(" الوزن: حافظ على وزنك الحالي ونمط حياة صحي.")

  s = data.get("sbp")
  if s is not None:
    if s >= 180:
      messages.append(
          " ضغط الدم: قراءة الضغط مرتفعة جدًا وتحتاج إلى تقييم طبي سريع، خاصة"
          " إذا صاحبها ألم بالصدر أو ضيق نفس أو ضعف مفاجئ أو اضطراب في الكلام أو"
          " الرؤية."
      )
    elif s >= 140 or (data.get("dbp") is not None and data.get("dbp") >= 90):
      messages.append(
          " ضغط الدم: احرص على قياس الضغط ومتابعته مع الطبيب، وقلل الملح، والتزم"
          " بالأدوية الموصوفة إذا كانت موجودة."
      )
    else:
      messages.append(
          " ضغط الدم: استمر في متابعة ضغط الدم ونمط الحياة الصحي والالتزام"
          " بالعلاج الموصوف."
      )

  if data.get("diabetes"):
    messages.append(
        " السكر: التزم بمتابعة السكر والعلاج الموصوف، وناقش نتائج القياسات"
        " والفحوصات مع الطبيب بانتظام."
    )

  if data.get("risk") is not None:
    r_val = data.get("risk")
    if r_val < 10:
      r_text = "أقل من 10%"
    elif r_val < 20:
      r_text = "من 10% إلى أقل من 20%"
    elif r_val < 30:
      r_text = "من 20% إلى أقل من 30%"
    else:
      r_text = "30% أو أكثر"
    messages.append(f" تقييم الخطورة: تقييم الخطورة القلبية المسجل {r_text}.")
    messages.append(" التزم بخطة المتابعة التي حددها الطبيب.")

  messages.append(
      "هذه الرسالة للتثقيف الصحي وليست تشخيصًا نهائيًا. القرار الطبي النهائي"
      " والعلاج يحدده الطبيب المعالج."
  )
  messages.append("نتمنى لك دوام الصحة والعافية.")

  return "\n\n".join(messages)


# زر تقييم الحالة وعرض رسالة التثقيف الصحي
st.markdown("---")
if st.button("تقييم الحالة وتوليد رسالة التثقيف الصحي", type="primary"):
  st.success(
      f"تم تقييم حالة المريض بنجاح! نسبة الخطورة المقدرة: {risk_score}%"
  )

  # تجهيز الداتا للدالة
  patient_data = {
      "age": calculated_age,
      "bmi": bmi,
      "sbp": sbp,
      "dbp": dbp,
      "chol_mgdl": chol,
      "ldl_mgdl": ldl_val,
      "risk_pct": risk_score,
      "smoking": smoking,
      "diabetes": diabetes,
      "hypertension": hypertension,
      "established_ascvd": ascvd,
      "ckd": ckd,
      "statin_needed": statin_needed,
      "statin_intensity": statin_intensity,
  }

  edu_text = generate_health_education(patient_data)

  st.markdown("### 📋 رسالة التثقيف الصحي المخصصة للمريض:")
  st.info(edu_text)
