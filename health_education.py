# رسائل تثقيف صحي مخصصة للمريض - حملة قلبك أمانة
# Prepared by Dr. Zahraa Yasser Saleh - الإدارة الصحية ببني عبيد

def _yes(value):
    return str(value).strip().lower() in {"yes", "true", "نعم", "موجود", "مدخن"}

def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def generate_health_education(data: dict) -> str:
    age = _num(data.get("age"))
    bmi = _num(data.get("bmi"))
    sbp = _num(data.get("sbp"))
    dbp = _num(data.get("dbp"))
    chol = _num(data.get("chol_mgdl"))
    ldl = _num(data.get("ldl_mgdl"))
    risk = _num(data.get("risk_pct"))
    
    smoking = _yes(data.get("smoking"))
    diabetes = _yes(data.get("diabetes"))
    hypertension = _yes(data.get("hypertension"))
    ascvd = _yes(data.get("established_ascvd"))
    ckd = _yes(data.get("ckd"))

    messages = [
        "❤️ رسالة من حملة «قلبك أمانة»",
        "تم إعداد هذا البرنامج بواسطة: د. زهراء ياسر صالح - الإدارة الصحية ببني عبيد",
        "هدفنا مساعدتك على تقليل عوامل الخطورة وحماية القلب والأوعية الدموية."
    ]

    if smoking:
        messages.append(" التدخين: الإقلاع عن التدخين من أهم الخطوات لحماية القلب والأوعية الدموية. ضع خطة للإقلاع واطلب مساعدة الفريق الطبي إذا احتجت.")
    else:
        messages.append(" التدخين: استمر في تجنب التدخين وتجنب التعرض المستمر لدخان الآخرين قدر الإمكان.")

    if bmi is not None:
        if bmi >= 30:
            messages.append(" الوزن: الوزن الزائد قد يزيد من عوامل خطورة القلب. ناقش مع الطبيب خطة تدريجية مناسبة لتحسين الوزن والنشاط البدني والغذاء.")
        elif bmi >= 25:
            messages.append(" الوزن: حاول الحفاظ على وزن صحي، وزيادة النشاط البدني تدريجيًا، واختيار غذاء متوازن.")
        else:
            messages.append(" الوزن: حافظ على وزنك الحالي ونمط حياة صحي.")

    if sbp is not None:
        if sbp >= 180:
            messages.append(" ضغط الدم: قراءة الضغط مرتفعة جدًا وتحتاج إلى تقييم طبي سريع، خاصة إذا صاحبها ألم بالصدر أو ضيق نفس أو ضعف مفاجئ أو اضطراب في الكلام أو الرؤية.")
        elif sbp >= 140 or (dbp is not None and dbp >= 90):
            messages.append(" ضغط الدم: احرص على قياس الضغط ومتابعته مع الطبيب، وقلل الملح، والتزم بالأدوية الموصوفة إذا كانت موجودة.")
        else:
            messages.append(" ضغط الدم: استمر في متابعة ضغط الدم ونمط الحياة الصحي والالتزام بالعلاج الموصوف.")

    if diabetes:
        messages.append(" السكر: التزم بمتابعة السكر والعلاج الموصوف، وناقش نتائج القياسات والفحوصات مع الطبيب بانتظام.")

    if risk is not None:
        if risk < 5:
            risk_text = "أقل من 5%"
        elif risk < 10:
            risk_text = "من 5% إلى أقل من 10%"
        elif risk < 20:
            risk_text = "من 10% إلى أقل من 20%"
        elif risk < 30:
            risk_text = "من 20% إلى أقل من 30%"
        else:
            risk_text = "30% أو أكثر"
        messages.append(f" تقييم الخطورة: تقييم الخطورة القلبية المسجل {risk_text}. التزم بخطة المتابعة التي حددها الطبيب.")

    messages.append("هذه الرسالة للتثقيف الصحي وليست تشخيصًا نهائيًا. القرار الطبي النهائي والعلاج يحدده الطبيب المعالج.")
    messages.append("نتمنى لك دوام الصحة والعافية.")

    return "\n\n".join(messages)

def education_for_streamlit(data: dict):
    return generate_health_education(data)
    
