# health_education.py
# رسائل تثقيف صحي مخصصة للمريض - حملة قلبك أمانة

def _yes(value):
    return str(value).strip().lower() in {
        "yes", "true", "1", "نعم", "موجود", "مدخن"
    }

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

    smoking = _yes(data.get("smoking")) or str(data.get("smoking", "")).strip() == "مدخن"
    diabetes = _yes(data.get("diabetes")) or str(data.get("diabetes_status", "")).strip() in {"جديد", "متردد"}
    hypertension = _yes(data.get("hypertension")) or _yes(data.get("hypertension_status"))
    ascvd = _yes(data.get("established_ascvd"))
    ckd = _yes(data.get("ckd"))

    messages = [
        "❤️ رسالة من حملة «قلبك أمانة»",
        "",
        "هدفنا مساعدتك على تقليل عوامل الخطورة وحماية القلب والأوعية الدموية."
    ]

    if smoking:
        messages += ["", "🚭 التدخين:",
                     "الإقلاع عن التدخين من أهم الخطوات لحماية القلب والأوعية الدموية. ضع خطة للإقلاع واطلب مساعدة الفريق الطبي إذا احتجت."]
    else:
        messages += ["", "🚭 التدخين:",
                     "استمر في تجنب التدخين وتجنب التعرض المستمر لدخان الآخرين قدر الإمكان."]

    if bmi is not None:
        if bmi >= 30:
            text = "الوزن الزائد قد يزيد من عوامل خطورة القلب. ناقش مع الطبيب خطة تدريجية مناسبة لتحسين الوزن والنشاط البدني والغذاء."
        elif bmi >= 25:
            text = "حاول الحفاظ على وزن صحي، وزيادة النشاط البدني تدريجيًا، واختيار غذاء متوازن."
        else:
            text = "حافظ على وزنك الحالي ونمط حياة صحي."
        messages += ["", "⚖️ الوزن:", text]

    if sbp is not None:
        if sbp >= 180:
            text = ("قراءة الضغط مرتفعة جدًا وتحتاج إلى تقييم طبي سريع، خاصة إذا صاحبها ألم بالصدر "
                    "أو ضيق نفس أو ضعف مفاجئ أو اضطراب في الكلام أو الرؤية.")
        elif sbp >= 140 or (dbp is not None and dbp >= 90):
            text = "احرص على قياس الضغط ومتابعته مع الطبيب، وقلل الملح، والتزم بالأدوية الموصوفة إذا كانت موجودة."
        else:
            text = "استمر في متابعة ضغط الدم ونمط الحياة الصحي والالتزام بالعلاج الموصوف."
        messages += ["", "🩺 ضغط الدم:", text]

    if diabetes:
        messages += ["", "🩸 السكر:",
                     "التزم بمتابعة السكر والعلاج الموصوف، وناقش نتائج القياسات والفحوصات مع الطبيب بانتظام."]

    if chol is not None or ldl is not None:
        if ldl is not None and ldl >= 190:
            text = "قيمة LDL مرتفعة جدًا وتحتاج إلى تقييم ومتابعة طبية، وقد يحتاج الطبيب إلى البحث عن أسباب وراثية وبدء علاج مناسب."
        elif chol is not None and chol > 320:
            text = "الكوليسترول الكلي مرتفع جدًا ويحتاج إلى تقييم ومتابعة طبية."
        else:
            text = "اهتم بالغذاء الصحي والمتابعة الدورية للدهون، والتزم بأي علاج يصفه الطبيب."
        messages += ["", "🧪 الدهون والكوليسترول:", text]

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
        messages += ["", "❤️ تقييم الخطورة:",
                     f"تقييم الخطورة القلبية المسجل {risk_text}. التزم بخطة المتابعة التي حددها الطبيب."]

    if ascvd:
        messages += ["", "❤️ تاريخ مرضي بالقلب أو الأوعية:",
                     "لأن لديك تاريخًا مرضيًا معروفًا بالقلب أو الأوعية الدموية، التزم بمتابعة الطبيب والأدوية والفحوصات المقررة."]

    if ckd:
        messages += ["", "🧪 الكلى:",
                     "مع وجود مرض كلوي مزمن، من المهم الالتزام بالمتابعة الطبية ومراجعة ضغط الدم والأدوية والفحوصات."]

    if _yes(data.get("statin_needed")):
        intensity = str(data.get("statin_intensity", "")).strip()
        label = f" ({intensity})" if intensity else ""
        messages += ["", "💊 الكوليسترول والعلاج:",
                     f"يوجد في سجل الزيارة توصية علاجية بالستاتين{label}. لا تبدأ أو توقف الدواء من نفسك؛ اتبع وصف الطبيب وراجع الطبيب عند حدوث أعراض غير معتادة."]

    followup = data.get("next_followup")
    if followup:
        messages += ["", "📅 المتابعة:",
                     f"موعد المتابعة المسجل: {followup}. احرص على الحضور في الموعد أو التواصل مع الوحدة إذا تعذر الحضور."]
    else:
        messages += ["", "📅 المتابعة:",
                     "احرص على المتابعة الدورية حسب تقييم الطبيب وعوامل الخطورة."]

    messages += [
        "",
        "⚠️ هذه الرسالة للتثقيف الصحي وليست تشخيصًا نهائيًا. القرار الطبي النهائي والعلاج يحدده الطبيب المعالج.",
        "",
        "نتمنى لك دوام الصحة والعافية ❤️"
    ]
    return "\n".join(messages)

def education_for_streamlit(data: dict):
    return generate_health_education(data)
