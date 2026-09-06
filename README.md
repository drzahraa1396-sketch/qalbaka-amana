# قلبك أمانة — Streamlit App

## تشغيل محلي
```bash
pip install -r requirements.txt
streamlit run app.py
```

## النشر على Streamlit Community Cloud
1. ارفعي `app.py`, `risk_tables.py`, `requirements.txt` إلى GitHub.
2. اربطي المستودع بـ Streamlit Community Cloud.
3. اختاري `app.py` كـ Main file.
4. لتخزين دائم، اربطي Google Sheets من صفحة **إعداد Google Sheets** وأضيفي بيانات Service Account إلى Streamlit Secrets.

## منطق النظام
- يمنع تسجيل نفس الرقم القومي أكثر من مرة في نفس الشهر.
- يحسب BMI تلقائياً.
- يدعم WHO Egypt non-laboratory chart باستخدام BMI و laboratory chart باستخدام total cholesterol، مع فصل diabetic/non-diabetic في جدول المعمل.
- يعرض قيمة الخطر الرقمية نفسها من الخانة في الجدول (مثل 3% أو 5% أو 18%) مع لون الخطر.
- ينشئ موعد متابعة حسب شرائح الـ guideline.
- يسجل المرضى والزيارات والمتابعة والإحالات.
- يولد البيان الشهري بنفس أعمدة نموذج Excel المرفوع، مع صف إجمالي.

> تنبيه: التطبيق أداة دعم قرار مبنية على المستندات المرفوعة، ويجب مراجعته واعتماده من المسؤول الطبي قبل الاستخدام السريري الفعلي.
