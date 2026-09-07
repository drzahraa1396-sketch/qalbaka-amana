import io
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from copy import copy

import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

from risk_tables import AGES, SBPS, CHOL, BMI, NONLAB_ROWS, LAB_ROWS
from health_education import generate_health_education

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "qalbak_amanah.db"

st.set_page_config(page_title="قلبك أمانة | مساعد الطبيب V5", page_icon="❤️", layout="wide")

HEADERS = {
    "Patients": [
        "national_id", "name", "dob", "sex", "family_file", "mobile",
        "governorate", "health_admin", "unit", "created_at"
    ],
    "Visits": [
        "visit_id", "visit_date", "national_id", "name", "family_file", "campaign_status",
        "age", "sex", "mobile", "governorate", "health_admin", "unit", "height_cm", "weight_kg", "bmi",
        "chol_mgdl", "ldl_mgdl", "sbp", "dbp", "diabetes", "hypertension", "diabetes_status",
        "hypertension_status", "ecg", "smoking", "family_history", "established_ascvd", "ckd",
        "tod", "multiple_rf", "pregnancy", "lactation", "risk_method", "risk_pct", "risk_color",
        "statin_needed", "statin_intensity", "statin_regimen", "bp_treatment", "dm_treatment",
        "statin_given", "aspirin_given", "health_education", "referral", "referral_reason",
        "referral_specialty", "referral_urgency", "next_followup", "doctor", "nurse", "created_at"
    ],
    "Followup": [
        "id", "national_id", "name", "scheduled_date", "visit_date", "status",
        "call_1_date", "call_1_status", "call_2_date", "call_2_status", "call_3_date", "call_3_status",
        "caller", "created_at"
    ],
    "Referrals": [
        "id", "referral_date", "national_id", "name", "family_file", "mobile", "reason", "specialty", "urgency",
        "followup_1_date", "followup_1_status", "followup_2_date", "followup_2_status", "followup_3_date",
        "followup_3_status", "feedback_treatment", "feedback_tests", "feedback_admission", "feedback_other",
        "followup_staff", "created_at"
    ],
}

RISK_HELP = {
    "أخضر": "خطورة أقل من 5%",
    "أصفر": "خطورة من 5% إلى أقل من 10%",
    "برتقالي": "خطورة من 10% إلى أقل من 20%",
    "أحمر": "خطورة من 20% إلى أقل من 30%",
    "أحمر داكن": "خطورة 30% أو أكثر",
}


def safe_num(v):
    try:
        if v in (None, "", "nan", "None"): return None
        return float(v)
    except Exception:
        return None


def risk_color(p):
    if p is None: return "غير متاح"
    if p < 5: return "أخضر"
    if p < 10: return "أصفر"
    if p < 20: return "برتقالي"
    if p < 30: return "أحمر"
    return "أحمر داكن"


def age_group(age):
    if age < 40: return "18-40"
    if age <= 65: return "40-65"
    return ">65"


def bmi_group(bmi):
    return "<30" if bmi < 30 else ">30"


def sbp_group(sbp):
    if sbp < 120: return "<120"
    if sbp < 140: return "120-139"
    if sbp < 160: return "140-159"
    if sbp < 180: return "160-179"
    return "≥180"


def age_chart_group(age):
    for g in AGES:
        a, b = map(int, g.split("-"))
        if a <= age <= b:
            return g
    return None


def bmi_chart_group(bmi):
    if bmi < 20: return "<20"
    if bmi < 25: return "20-24"
    if bmi < 30: return "25-29"
    if bmi <= 35: return "30-35"
    return "≥35"


def chol_chart_group(chol_mmol):
    if chol_mmol < 4: return "<4"
    if chol_mmol < 5: return "4-4.9"
    if chol_mmol < 6: return "5-5.9"
    if chol_mmol < 7: return "6-6.9"
    return "≥7"


def calculate_risk(method, age, sex, smoker, sbp, bmi=None, chol_mgdl=None, diabetic=False):
    if age < 40 or age > 74:
        return None, None
    ag = age_chart_group(age)
    sg = sbp_group(float(sbp))
    sex_i = 0 if sex == "ذكر" else 1
    smoker_i = 1 if smoker else 0
    if method == "BMI / بدون معمل":
        row = next(r for r in NONLAB_ROWS if r[0] == ag and r[1] == sg)[2]
        idx = (0 if sex_i == 0 else 10) + smoker_i * 5
        p = int(row[idx + BMI.index(bmi_chart_group(float(bmi)))])
        return p, risk_color(p)
    if chol_mgdl is None:
        return None, None
    row = next(r for r in LAB_ROWS if r[0] == ag and r[1] == sg)
    vals = row[2] if not diabetic else row[3]
    idx = (0 if sex_i == 0 else 10) + smoker_i * 5
    p = int(vals[idx + CHOL.index(chol_chart_group(float(chol_mgdl) / 38.7))])
    return p, risk_color(p)


def add_months(d, months):
    return (pd.Timestamp(d) + pd.DateOffset(months=months)).date()


def followup_options(visit_date, risk_pct):
    if risk_pct is None: return []
    if risk_pct < 5: return [("بعد 12 شهر", add_months(visit_date, 12))]
    if risk_pct < 10:
        return [("بعد 3 أشهر", add_months(visit_date, 3)), ("بعد 6 أشهر", add_months(visit_date, 6)), ("بعد 9 أشهر", add_months(visit_date, 9))]
    if risk_pct < 20:
        return [("بعد 3 أشهر", add_months(visit_date, 3)), ("بعد 6 أشهر", add_months(visit_date, 6))]
    return [("بعد 3 أشهر", add_months(visit_date, 3))]


def statin_recommendation(risk_pct, diabetic, tod, multiple_rf, ldl, chol, established_ascvd, pregnancy, lactation):
    if pregnancy or lactation:
        return "ممنوع حسب الدليل", "لا يوجد", "لا تستخدم الستاتين"
    if established_ascvd or (ldl is not None and ldl >= 190) or (chol is not None and chol > 320) or (risk_pct is not None and risk_pct > 30):
        return "نعم", "High-intensity", "Atorvastatin 40–80 mg أو Rosuvastatin 20–40 mg"
    if risk_pct is not None and risk_pct > 20:
        return "نعم", "Moderate-intensity", "Atorvastatin 20 mg أو Rosuvastatin 5–10 mg"
    if diabetic and (tod or multiple_rf):
        return "نعم", "High-intensity", "Atorvastatin 40–80 mg أو Rosuvastatin 20–40 mg"
    if diabetic:
        return "نعم", "Moderate-intensity", "Atorvastatin 20 mg أو Rosuvastatin 5–10 mg"
    return "لا", "لا يوجد", ""


def clinical_summary(age, bmi, diabetes, hypertension, smoking, family_history, risk_pct, ldl, established_ascvd, ckd):
    findings = []
    if established_ascvd: findings.append("ASCVD مثبتة")
    if ckd: findings.append("CKD مسجلة")
    if diabetes == "نعم": findings.append("سكري مسجل")
    if hypertension == "نعم": findings.append("ضغط مسجل")
    if bmi >= 30: findings.append("BMI ≥30")
    if smoking == "مدخن": findings.append("مدخن")
    if family_history == "يوجد": findings.append("تاريخ عائلي موجود")
    if ldl is not None and ldl >= 190: findings.append("LDL ≥190 mg/dL")
    if risk_pct is not None: findings.append(f"CVD Risk = {risk_pct}%")
    return findings


def clinical_alerts(age, bmi, sbp, dbp, diabetes, hypertension, smoking, ldl, chol, risk_pct, established_ascvd, ckd, pregnancy, lactation, ecg):
    alerts, actions = [], []
    if age < 40 or age > 74:
        alerts.append("تقييم WHO المرفوع لا يغطي هذا العمر؛ لا تعرض نسبة خطر مصطنعة.")
    if sbp >= 180 or dbp >= 120:
        alerts.append("⚠️ قراءة ضغط شديدة الارتفاع: أعد القياس وقيّم الحالة سريريًا فورًا، وخصوصًا إذا توجد أعراض.")
    elif sbp >= 140 or dbp >= 90:
        actions.append("متابعة ضغط الدم وتقليل الملح ومراجعة العلاج حسب قرار الطبيب.")
    if diabetes == "نعم":
        actions.append("متابعة السكر بانتظام والالتزام بالخطة العلاجية.")
    if bmi >= 30:
        actions.append("خطة إنقاص وزن تدريجية وغذاء صحي ونشاط بدني حسب القدرة.")
    if smoking == "مدخن":
        actions.append("دعم الإقلاع عن التدخين.")
    if ldl is not None and ldl >= 190:
        alerts.append("LDL ≥190 mg/dL: راجع سبب الارتفاع وفكرة تقييم فرط كوليسترول عائلي حسب الدليل.")
    if chol is not None and chol > 320:
        alerts.append("Total cholesterol >320 mg/dL: يحتاج مراجعة علاجية متخصصة حسب الدليل.")
    if risk_pct is not None and risk_pct >= 20:
        alerts.append("خطورة قلبية مرتفعة (≥20%): تحتاج متابعة أقرب حسب الدليل.")
    if established_ascvd:
        alerts.append("ASCVD مثبتة: تعامل مع الحالة كخطورة مرتفعة جدًا وفق الدليل، وراجع العلاج والمتابعة.")
    if ckd:
        alerts.append("CKD مسجلة: راجع الحالة كعامل خطورة مرتفع وفق الدليل.")
    if pregnancy or lactation:
        alerts.append("الحمل/الرضاعة: الستاتين ممنوع حسب الدليل المرفوع.")
    if ecg == "غير طبيعي":
        alerts.append("رسم القلب غير طبيعي: يلزم تقييم الطبيب وتحديد الحاجة للإحالة حسب الحالة.")
    return alerts, actions


def education_text(**kwargs):
    return generate_health_education(**kwargs)


class Store:
    def __init__(self):
        self.gs = None
        if self.google_configured():
            try:
                self.gs = self._connect_gs()
            except Exception as e:
                st.warning(f"تعذر الاتصال بـ Google Sheets؛ سيُستخدم التخزين المحلي في هذه الجلسة. {e}")
        self.init_local()

    def google_configured(self):
        return gspread is not None and Credentials is not None and "gcp_service_account" in st.secrets and "google_sheet" in st.secrets

    def _connect_gs(self):
        cfg = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(cfg, scopes=scopes)
        ss = gspread.authorize(creds).open(st.secrets["google_sheet"]["spreadsheet_name"])
        for title, headers in HEADERS.items():
            try:
                ws = ss.worksheet(title)
            except Exception:
                ws = ss.add_worksheet(title=title, rows=3000, cols=max(30, len(headers)))
                ws.append_row(headers)
                continue
            vals = ws.get_all_values()
            if not vals:
                ws.append_row(headers)
            elif vals[0] != headers:
                # V5 keeps the same schema as V4. If an old sheet differs, fail safe rather than shifting patient data.
                raise RuntimeError(f"رؤوس تبويب {title} مختلفة عن مخطط V5. راجع الصف الأول قبل التشغيل.")
        return ss

    def init_local(self):
        con = sqlite3.connect(DB_PATH)
        for table, headers in HEADERS.items():
            cols = ",".join([f'"{h}" TEXT' for h in headers])
            con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols})')
        con.commit(); con.close()

    def df(self, table):
        headers = HEADERS[table]
        if self.gs:
            vals = self.gs.worksheet(table).get_all_values()
            if not vals: return pd.DataFrame(columns=headers)
            rows = [list(r) + [""] * max(0, len(headers)-len(r)) for r in vals[1:]]
            return pd.DataFrame([r[:len(headers)] for r in rows], columns=headers)
        con = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f'SELECT * FROM "{table}"', con)
        con.close(); return df

    def append(self, table, row):
        headers = HEADERS[table]
        vals = [row.get(h, "") for h in headers]
        if self.gs:
            self.gs.worksheet(table).append_row(["" if v is None else str(v) for v in vals], value_input_option="USER_ENTERED")
        con = sqlite3.connect(DB_PATH)
        con.execute(f'INSERT INTO "{table}" ({",".join(headers)}) VALUES ({",".join(["?"]*len(headers))})', vals)
        con.commit(); con.close()

    def update_by_id(self, table, record_id, updates):
        headers = HEADERS[table]; id_col = "visit_id" if table == "Visits" else "id"
        if self.gs:
            ws = self.gs.worksheet(table); vals = ws.get_all_values()
            for r, row in enumerate(vals[1:], start=2):
                if row and str(row[headers.index(id_col)] if len(row) > headers.index(id_col) else "") == str(record_id):
                    for k, v in updates.items():
                        if k in headers: ws.update_cell(r, headers.index(k)+1, "" if v is None else str(v))
                    break
        con = sqlite3.connect(DB_PATH)
        sets, vals = [], []
        for k,v in updates.items():
            if k in headers: sets.append(f'"{k}"=?'); vals.append(v)
        if sets:
            vals.append(record_id); con.execute(f'UPDATE "{table}" SET {", ".join(sets)} WHERE "{id_col}"=?', vals); con.commit()
        con.close()

    def exists_visit_month(self, national_id, year, month):
        df = self.df("Visits")
        if df.empty: return False
        d = pd.to_datetime(df.visit_date, errors="coerce")
        return ((df.national_id.astype(str) == str(national_id)) & (d.dt.year == year) & (d.dt.month == month)).any()

    def patient(self, national_id):
        df = self.df("Patients")
        if df.empty: return None
        m = df[df.national_id.astype(str) == str(national_id)]
        return None if m.empty else m.iloc[-1].to_dict()

    def upsert_patient(self, row):
        old = self.patient(row["national_id"])
        if old is None or any(str(old.get(k,"")) != str(row.get(k,"")) for k in HEADERS["Patients"] if k != "created_at"):
            self.append("Patients", row)


def make_excel(store):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for table in HEADERS: store.df(table).to_excel(writer, index=False, sheet_name=table[:31])
    out.seek(0); return out


def monthly_report(store, year, month, governorate="", admin=""):
    visits = store.df("Visits")
    if visits.empty: return pd.DataFrame()
    d = pd.to_datetime(visits.visit_date, errors="coerce")
    v = visits[(d.dt.year == year) & (d.dt.month == month)].copy()
    if governorate: v = v[v.governorate.astype(str) == governorate]
    if admin: v = v[v.health_admin.astype(str) == admin]
    if v.empty: return pd.DataFrame()
    rows=[]
    for unit,g in v.groupby("unit", dropna=False):
        n=lambda m:int(m.sum())
        age=pd.to_numeric(g.age,errors="coerce"); bmi=pd.to_numeric(g.bmi,errors="coerce"); risk=pd.to_numeric(g.risk_pct,errors="coerce")
        rows.append({
            "م":len(rows)+1,"الادارة":admin or (g.health_admin.dropna().iloc[0] if not g.health_admin.dropna().empty else ""),"الوحدة /المركز":unit or "",
            "جديد":n(g.campaign_status.eq("جديد")),"متردد":n(g.campaign_status.eq("متردد")),"اجمالي":len(g),
            "18-40":n(age<40),"40-65":n((age>=40)&(age<=65)),">65":n(age>65),"ذكر":n(g.sex.eq("ذكر")),"أنثى":n(g.sex.eq("أنثى")),
            "BMI <30":n(bmi<30),"BMI >30":n(bmi>=30),"سكر جديد":n((g.diabetes.eq("نعم"))&g.diabetes_status.eq("جديد")),"سكر متردد":n((g.diabetes.eq("نعم"))&g.diabetes_status.eq("متردد")),
            "ضغط جديد":n((g.hypertension.eq("نعم"))&g.hypertension_status.eq("جديد")),"ضغط متردد":n((g.hypertension.eq("نعم"))&g.hypertension_status.eq("متردد")),
            "سكر+ضغط جديد":n((g.diabetes.eq("نعم"))&(g.hypertension.eq("نعم"))&g.diabetes_status.eq("جديد")&g.hypertension_status.eq("جديد")),
            "سكر+ضغط متردد":n((g.diabetes.eq("نعم"))&(g.hypertension.eq("نعم"))&g.diabetes_status.eq("متردد")&g.hypertension_status.eq("متردد")),
            "رسم قلب جديد":n(g.ecg.eq("جديد")),"رسم قلب متابعة":n(g.ecg.eq("متابعة")),"طبيعي":n(g.ecg.eq("طبيعي")),"غير طبيعي":n(g.ecg.eq("غير طبيعي")),
            "مدخن":n(g.smoking.eq("مدخن")),"غير مدخن":n(g.smoking.eq("غير مدخن")),"تاريخ مرضي يوجد":n(g.family_history.eq("يوجد")),"تاريخ مرضي لا يوجد":n(g.family_history.eq("لا يوجد")),
            "<5":n(risk<5),"5-10":n((risk>=5)&(risk<10)),"10-20":n((risk>=10)&(risk<20)),">20":n(risk>=20),
            "تثقيف صحي":n(g.health_education.eq("نعم")),"علاج ضغط":n(g.bp_treatment.eq("نعم")),"علاج سكر":n(g.dm_treatment.eq("نعم")),"ستاتين":n(g.statin_given.eq("نعم")),"اسبرين":n(g.aspirin_given.eq("نعم")),"احالة":n(g.referral.eq("نعم"))})
    return pd.DataFrame(rows)


def report_xlsx(df, governorate, year, month):
    from openpyxl import load_workbook
    template=APP_DIR/"monthly_template.xlsx"
    if not template.exists(): return io.BytesIO()
    wb=load_workbook(template); ws=wb["اسم المحافظه"]
    ws["G3"]=f"بيان قلبك امانة فى محافظة {governorate or ''} — شهر {month:02d}/{year}"
    data_start,total_row=8,23; needed=len(df)
    if needed>15:
        ws.insert_rows(total_row, needed-15); total_row += needed-15
        for r in range(23,total_row):
            for c in range(1,38):
                src,dst=ws.cell(8,c),ws.cell(r,c)
                if src.has_style: dst._style=copy(src._style)
                dst.number_format=src.number_format; dst.alignment=copy(src.alignment)
            ws.row_dimensions[r].height=ws.row_dimensions[8].height
    cmap={1:"م",2:"الادارة",3:"الوحدة /المركز",4:"جديد",5:"متردد",6:"اجمالي",7:"18-40",8:"40-65",9:">65",10:"ذكر",11:"أنثى",12:"BMI <30",13:"BMI >30",14:"سكر جديد",15:"سكر متردد",16:"ضغط جديد",17:"ضغط متردد",18:"سكر+ضغط جديد",19:"سكر+ضغط متردد",20:"رسم قلب جديد",21:"رسم قلب متابعة",22:"طبيعي",23:"غير طبيعي",24:"مدخن",25:"غير مدخن",26:"تاريخ مرضي يوجد",27:"تاريخ مرضي لا يوجد",28:"<5",29:"5-10",30:"10-20",31:">20",32:"تثقيف صحي",33:"علاج ضغط",34:"علاج سكر",35:"ستاتين",36:"اسبرين",37:"احالة"}
    for i in range(needed):
        r=data_start+i
        for c,k in cmap.items():
            v=df.iloc[i].get(k,""); ws.cell(r,c).value="" if pd.isna(v) else v
    for r in range(data_start+needed,total_row):
        for c in range(1,38): ws.cell(r,c).value=None
    ws.cell(total_row,1).value="الاجمالى"
    for c in range(4,38): ws.cell(total_row,c).value=sum(float(ws.cell(r,c).value or 0) for r in range(data_start,data_start+needed))
    out=io.BytesIO(); wb.save(out); out.seek(0); return out


def optional_pin_login():
    try:
        cfg=st.secrets.get("security", {})
        enabled=str(cfg.get("enabled", "false")).lower() in ("true","1","yes")
        pin=str(cfg.get("pin", ""))
    except Exception:
        enabled=False; pin=""
    if not enabled or not pin: return True
    if st.session_state.get("authenticated"): return True
    st.title("🔐 تسجيل الدخول")
    entered=st.text_input("رمز الدخول", type="password")
    if st.button("دخول", type="primary"):
        if entered == pin:
            st.session_state.authenticated=True; st.rerun()
        else: st.error("رمز الدخول غير صحيح.")
    st.info("الحماية اختيارية وتُفعّل من Streamlit Secrets.")
    return False


if not optional_pin_login():
    st.stop()

store=Store()
st.sidebar.markdown("# ❤️ قلبك أمانة")
st.sidebar.markdown("### 🏛️ الإدارة الصحية بني عبيد")
st.sidebar.markdown("**Prepared by: Dr. Alzahraa Yasser Saleh**")
st.sidebar.caption("تصميم وتطوير البرنامج: Dr. Alzahraa Yasser Saleh")
st.sidebar.caption("V5 — مساعد الطبيب وإدارة دورة الحملة")
if store.gs: st.sidebar.success("الحفظ: Google Sheets")
else: st.sidebar.warning("الحفظ الحالي محلي. فعّلي Google Sheets للحفظ الدائم على Cloud.")

page=st.sidebar.radio("القائمة", ["🏠 لوحة الطبيب","➕ زيارة جديدة","👤 ملف المريض","📅 المتابعة والاستدعاء","🚨 الإحالات","📊 التقارير","💾 تصدير البيانات","⚙️ الإعدادات"])

if page == "🏠 لوحة الطبيب":
    st.title("🏠 لوحة الطبيب — ماذا يحتاج اليوم؟")
    today=date.today(); visits=store.df("Visits"); follow=store.df("Followup"); refs=store.df("Referrals")
    if visits.empty: today_v=month_v=visits.copy()
    else:
        vd=pd.to_datetime(visits.visit_date,errors="coerce"); today_v=visits[vd.dt.date==today]; month_v=visits[(vd.dt.year==today.year)&(vd.dt.month==today.month)]
    if follow.empty: due=follow.copy()
    else:
        fd=pd.to_datetime(follow.scheduled_date,errors="coerce"); due=follow[fd.dt.date<=today].copy(); due=due[~due.status.isin(["تمت المتابعة","حضر","مغلق"])]
    if refs.empty: open_refs=refs.copy()
    else: open_refs=refs[~refs.followup_3_status.eq("حضر") & ~refs.followup_3_status.eq("مغلق")]
    risk=pd.to_numeric(month_v.risk_pct,errors="coerce") if not month_v.empty else pd.Series(dtype=float)
    high=int(risk.ge(20).sum()) if not month_v.empty else 0
    statins=int(month_v.statin_given.eq("نعم").sum()) if not month_v.empty else 0
    referrals=int(month_v.referral.eq("نعم").sum()) if not month_v.empty else 0
    cols=st.columns(7)
    for col,label,val in zip(cols,["زيارات اليوم","زيارات الشهر","متابعات مستحقة","خطورة ≥20%","ستاتين مصروف","إحالات الشهر","إحالات مفتوحة"],[len(today_v),len(month_v),len(due),high,statins,referrals,len(open_refs)]): col.metric(label,val)
    st.divider()
    l,r=st.columns(2)
    with l:
        st.subheader("🔔 قائمة العمل")
        if not due.empty: st.warning(f"لديك {len(due)} متابعة مستحقة أو متأخرة.")
        if high: st.warning(f"راجع {high} حالة بخطورة ≥20% هذا الشهر.")
        if not open_refs.empty: st.info(f"هناك {len(open_refs)} إحالة تحتاج متابعة.")
        if due.empty and high==0 and open_refs.empty: st.success("لا توجد مهام حرجة ظاهرة الآن.")
    with r:
        st.subheader("📈 مؤشرات الشهر")
        if month_v.empty: st.info("لا توجد زيارات هذا الشهر.")
        else:
            m1,m2,m3,m4=st.columns(4)
            m1.metric("جديد",int(month_v.campaign_status.eq("جديد").sum())); m2.metric("متردد",int(month_v.campaign_status.eq("متردد").sum())); m3.metric("ضغط",int(month_v.hypertension.eq("نعم").sum())); m4.metric("سكر",int(month_v.diabetes.eq("نعم").sum()))
            rr=pd.DataFrame({"الفئة":["<5%","5–<10%","10–<20%","≥20%"],"العدد":[int(risk.lt(5).sum()),int(risk.ge(5).sum()-risk.ge(10).sum()),int(risk.ge(10).sum()-risk.ge(20).sum()),int(risk.ge(20).sum())]})
            st.dataframe(rr,use_container_width=True,hide_index=True)
    if not due.empty:
        st.subheader("📅 أقرب المتابعات المستحقة")
        dd=due.copy(); dd["scheduled_date"]=pd.to_datetime(dd.scheduled_date,errors="coerce"); st.dataframe(dd.sort_values("scheduled_date")[['name','national_id','scheduled_date','status']].head(20),use_container_width=True,hide_index=True)

elif page == "➕ زيارة جديدة":
    st.title("➕ زيارة جديدة — إدخال مرة واحدة")
    st.caption("البرنامج يحسب BMI والخطورة، يعرض التنبيهات، يقترح المتابعة، ويولّد رسالة المريض قبل الحفظ.")
    st.subheader("1) بيانات المريض")
    c1,c2,c3=st.columns([1.2,1.5,1.5])
    with c1:
        visit_date=st.date_input("تاريخ الزيارة",date.today(),key="v5_visit_date")
        national_id=st.text_input("الرقم القومي *",max_chars=14,key="v5_nid")
        if st.button("🔎 بحث عن المريض",use_container_width=True):
            p=store.patient(national_id)
            if p:
                for k in ["name","family_file","mobile","governorate","health_admin","unit"]: st.session_state[f"v5_{k}"]=p.get(k,"") or ""
                st.session_state["v5_sex"]=p.get("sex","ذكر") or "ذكر"; st.success("تم تحميل بيانات المريض السابقة.")
            else: st.info("المريض غير موجود؛ سيتم تسجيله كمريض جديد.")
    with c2:
        name=st.text_input("اسم المريض رباعي *",key="v5_name"); dob=st.date_input("تاريخ الميلاد",date(1980,1,1),min_value=date(1900,1,1),max_value=date.today(),key="v5_dob"); sex=st.selectbox("النوع",["ذكر","أنثى"],key="v5_sex"); family_file=st.text_input("رقم الملف العائلي",key="v5_family_file")
    with c3:
        mobile=st.text_input("رقم الموبايل",key="v5_mobile"); governorate=st.text_input("المحافظة",key="v5_governorate"); health_admin=st.text_input("الإدارة الصحية",key="v5_health_admin"); unit=st.text_input("الوحدة / المركز",key="v5_unit"); campaign_status=st.selectbox("حملة قلبك أمانة",["جديد","متردد"],key="v5_campaign")
    age=max(0,(visit_date-dob).days//365); st.metric("العمر المحسوب",age)
    duplicate=bool(national_id and store.exists_visit_month(national_id,visit_date.year,visit_date.month))
    if duplicate: st.error("⚠️ يوجد تسجيل سابق لنفس الرقم القومي في نفس الشهر؛ لن يسمح التطبيق بالحفظ مرة أخرى.")

    st.subheader("2) القياسات")
    a,b,c,d,e=st.columns(5)
    with a: height=st.number_input("الطول (سم)",80.0,250.0,165.0,key="v5_height")
    with b: weight=st.number_input("الوزن (كجم)",20.0,300.0,70.0,key="v5_weight")
    bmi=round(weight/((height/100)**2),1)
    with c: st.metric("BMI",bmi)
    with d: sbp=st.number_input("SBP",60,260,130,key="v5_sbp")
    with e: dbp=st.number_input("DBP",30,160,80,key="v5_dbp")
    st.caption("جدول WHO المرفوع يستخدم SBP في حساب الخطورة؛ DBP يُحفظ ويُستخدم للتنبيه السريري فقط.")

    st.subheader("3) الأمراض وعوامل الخطورة")
    a,b,c,d,e=st.columns(5)
    with a: diabetes=st.selectbox("السكري",["لا","نعم"],key="v5_diabetes")
    with b: hypertension=st.selectbox("الضغط",["لا","نعم"],key="v5_htn")
    with c: smoking=st.selectbox("التدخين",["مدخن","غير مدخن"],key="v5_smoking")
    with d: family_history=st.selectbox("تاريخ مرضي عائلي",["يوجد","لا يوجد"],key="v5_family_history")
    with e: ecg=st.selectbox("رسم القلب",["غير مطلوب","جديد","متابعة","طبيعي","غير طبيعي"],key="v5_ecg")
    a,b,c,d=st.columns(4)
    with a: diabetes_status=st.selectbox("حالة السكر",["جديد","متردد","غير منطبق"],key="v5_dm_status")
    with b: hypertension_status=st.selectbox("حالة الضغط",["جديد","متردد","غير منطبق"],key="v5_bp_status")
    with c: established_ascvd=st.checkbox("ASCVD مثبتة؟",key="v5_ascvd")
    with d: ckd=st.checkbox("CKD؟",key="v5_ckd")
    a,b,c,d=st.columns(4)
    with a: tod=st.checkbox("Target Organ Damage / TOD؟",key="v5_tod")
    with b: multiple_rf=st.checkbox("Multiple additional risk factors؟",key="v5_mrf")
    with c: pregnancy=st.checkbox("حمل",key="v5_preg")
    with d: lactation=st.checkbox("رضاعة",key="v5_lact")

    st.subheader("4) التحاليل وتقييم الخطورة")
    method=st.radio("طريقة التقييم",["معمل / Cholesterol","BMI / بدون معمل"],horizontal=True,key="v5_method")
    chol=ldl=None
    if method=="معمل / Cholesterol":
        a,b=st.columns(2)
        with a: chol=st.number_input("Total Cholesterol (mg/dL)",50.0,600.0,190.0,key="v5_chol")
        with b: ldl=st.number_input("LDL (mg/dL)",20.0,400.0,100.0,key="v5_ldl")
    else: st.info("الطريقة غير المعملية تستخدم العمر + الجنس + التدخين + SBP + BMI.")
    risk_pct,risk_col=calculate_risk(method,age,sex,smoking=="مدخن",sbp,bmi,chol,diabetes=="نعم")
    if risk_pct is None: st.warning("نسبة الخطورة غير متاحة لهذا العمر (WHO 40–74 فقط) أو تحتاج Total Cholesterol.")
    else: st.success(f"❤️ CVD Risk خلال 10 سنوات: **{risk_pct}%** — {RISK_HELP[risk_col]}")

    alerts,actions=clinical_alerts(age,bmi,sbp,dbp,diabetes,hypertension,smoking,ldl,chol,risk_pct,established_ascvd,ckd,pregnancy,lactation,ecg)
    if alerts:
        st.subheader("🚨 تنبيهات الطبيب")
        for x in alerts: st.warning(x)
    if actions:
        st.subheader("✅ نقاط عمل مقترحة")
        for x in actions: st.write("• "+x)

    st.subheader("5) مساعد القرار للطبيب")
    stat_needed,intensity,regimen=statin_recommendation(risk_pct,diabetes=="نعم",tod,multiple_rf,ldl,chol,established_ascvd,pregnancy,lactation)
    findings=clinical_summary(age,bmi,diabetes,hypertension,smoking,family_history,risk_pct,ldl,established_ascvd,ckd)
    if findings: st.write("**المشكلات/العوامل المسجلة:** "+" • ".join(findings))
    a,b=st.columns(2)
    with a:
        st.markdown("### 💊 الستاتين")
        if stat_needed=="نعم": st.success(f"**التوصية حسب المعايير المدخلة:** {intensity}\n\n{regimen}")
        elif stat_needed=="ممنوع حسب الدليل": st.error("لا يستخدم الستاتين في الحمل/الرضاعة حسب الدليل المرفوع.")
        else: st.info("لا توجد توصية تلقائية بالستاتين من المعايير المدخلة.")
    with b:
        st.markdown("### 📅 المتابعة")
        opts=followup_options(visit_date,risk_pct)
        if opts:
            choice=st.selectbox("الفترة المقترحة",[x[0] for x in opts],key="v5_fu_choice"); next_fu=st.date_input("التاريخ النهائي (يمكن للطبيب تعديله)",dict(opts)[choice],key="v5_next_fu")
        else: next_fu=None; st.info("لا يوجد موعد WHO تلقائي لهذا العمر/النتيجة.")

    st.subheader("6) قرار الطبيب والإجراءات")
    a,b,c,d,e=st.columns(5)
    with a: health_education=st.selectbox("تثقيف صحي تم تقديمه",["نعم","لا"],key="v5_edu")
    with b: bp_treatment=st.selectbox("علاج ضغط",["نعم","لا"],key="v5_bp_treat")
    with c: dm_treatment=st.selectbox("علاج سكر",["نعم","لا"],key="v5_dm_treat")
    with d: statin_given=st.selectbox("ستاتين مصروف",["نعم","لا"],key="v5_statin_given")
    with e: aspirin_given=st.selectbox("أسبرين مصروف",["نعم","لا"],key="v5_aspirin")
    referral=st.selectbox("إحالة",["لا","نعم"],key="v5_referral")
    referral_reason=referral_specialty=referral_urgency=""
    if referral=="نعم":
        a,b,c=st.columns(3)
        with a: referral_reason=st.text_input("سبب الإحالة",key="v5_ref_reason")
        with b: referral_specialty=st.text_input("التخصص",key="v5_ref_specialty")
        with c: referral_urgency=st.selectbox("الاستعجال",["عادية","طارئة"],key="v5_ref_urgency")
    a,b=st.columns(2)
    with a: doctor=st.text_input("اسم الطبيب ثلاثي",key="v5_doctor")
    with b: nurse=st.text_input("اسم الممرضة ثلاثي",key="v5_nurse")

    st.subheader("7) 📱 الرسالة العملية للمريض")
    edu=education_text(age=age,bmi=bmi,sbp=sbp,dbp=dbp,smoking=smoking,diabetes=diabetes,hypertension=hypertension,chol_mgdl=chol,ldl_mgdl=ldl,statin_needed=stat_needed,statin_intensity=intensity,statin_regimen=regimen,bp_treatment=bp_treatment,dm_treatment=dm_treatment,statin_given=statin_given,established_ascvd=established_ascvd,ckd=ckd,next_followup=next_fu.strftime("%d-%m-%Y") if next_fu else None)
    st.text_area("جاهزة للنسخ والإرسال",edu,height=420,key="v5_edu_preview")
    st.download_button("⬇️ حفظ رسالة المريض",edu,"رسالة_تثقيف_صحي_قلبك_أمانة.txt","text/plain; charset=utf-8",use_container_width=True)

    st.subheader("8) مراجعة قبل الاعتماد")
    review=pd.DataFrame({"البند":["المريض","العمر","BMI","BP","Risk","Statin","المتابعة","الإحالة"],"القيمة":[name or "-",age,bmi,f"{sbp}/{dbp}",f"{risk_pct}%" if risk_pct is not None else "غير متاح",f"{stat_needed} — {intensity}",next_fu.strftime("%d/%m/%Y") if next_fu else "-",referral]})
    st.dataframe(review,use_container_width=True,hide_index=True)
    if st.button("💾 اعتماد وحفظ الزيارة",type="primary",use_container_width=True,disabled=duplicate):
        if not national_id or not name: st.error("الرقم القومي والاسم رباعي مطلوبان.")
        elif store.exists_visit_month(national_id,visit_date.year,visit_date.month): st.error("هذا المريض مسجل بالفعل في هذا الشهر.")
        else:
            now=datetime.now().isoformat(timespec="seconds")
            store.upsert_patient({"national_id":national_id,"name":name,"dob":dob.isoformat(),"sex":sex,"family_file":family_file,"mobile":mobile,"governorate":governorate,"health_admin":health_admin,"unit":unit,"created_at":now})
            row={"visit_id":f"{national_id}-{visit_date.isoformat()}","visit_date":visit_date.isoformat(),"national_id":national_id,"name":name,"family_file":family_file,"campaign_status":campaign_status,"age":age,"sex":sex,"mobile":mobile,"governorate":governorate,"health_admin":health_admin,"unit":unit,"height_cm":height,"weight_kg":weight,"bmi":bmi,"chol_mgdl":chol,"ldl_mgdl":ldl,"sbp":sbp,"dbp":dbp,"diabetes":diabetes,"hypertension":hypertension,"diabetes_status":diabetes_status,"hypertension_status":hypertension_status,"ecg":ecg,"smoking":smoking,"family_history":family_history,"established_ascvd":"نعم" if established_ascvd else "لا","ckd":"نعم" if ckd else "لا","tod":"نعم" if tod else "لا","multiple_rf":"نعم" if multiple_rf else "لا","pregnancy":"نعم" if pregnancy else "لا","lactation":"نعم" if lactation else "لا","risk_method":method,"risk_pct":risk_pct,"risk_color":risk_col,"statin_needed":stat_needed,"statin_intensity":intensity,"statin_regimen":regimen,"bp_treatment":bp_treatment,"dm_treatment":dm_treatment,"statin_given":statin_given,"aspirin_given":aspirin_given,"health_education":health_education,"referral":referral,"referral_reason":referral_reason,"referral_specialty":referral_specialty,"referral_urgency":referral_urgency,"next_followup":next_fu.isoformat() if next_fu else "","doctor":doctor,"nurse":nurse,"created_at":now}
            store.append("Visits",row)
            if next_fu: store.append("Followup",{"id":f"{national_id}-{next_fu.isoformat()}","national_id":national_id,"name":name,"scheduled_date":next_fu.isoformat(),"visit_date":visit_date.isoformat(),"status":"مجدول","created_at":now})
            if referral=="نعم": store.append("Referrals",{"id":f"{national_id}-{visit_date.isoformat()}","referral_date":visit_date.isoformat(),"national_id":national_id,"name":name,"family_file":family_file,"mobile":mobile,"reason":referral_reason,"specialty":referral_specialty,"urgency":referral_urgency,"followup_1_date":(pd.Timestamp(visit_date)+pd.Timedelta(days=3)).date().isoformat(),"created_at":now})
            st.success("تم الحفظ بنجاح. المريض أُضيف للسجل والمتابعة/الإحالة والتقارير تلقائيًا.")

elif page == "👤 ملف المريض":
    st.title("👤 ملف المريض — سجل واحد عبر كل الزيارات")
    nid=st.text_input("الرقم القومي")
    if nid:
        p=store.patient(nid); v=store.df("Visits")
        if not v.empty: v=v[v.national_id.astype(str)==str(nid)].copy()
        if not p: st.warning("المريض غير موجود.")
        else:
            st.success(f"تم العثور على: {p.get('name','')}")
            a,b,c,d=st.columns(4); a.metric("الاسم",p.get("name","-")); b.metric("النوع",p.get("sex","-")); c.metric("الموبايل",p.get("mobile","-")); d.metric("الملف العائلي",p.get("family_file","-"))
            if not v.empty:
                v["visit_date"]=pd.to_datetime(v.visit_date,errors="coerce"); latest=v.sort_values("visit_date").iloc[-1]
                st.subheader("آخر زيارة")
                a,b,c,d,e=st.columns(5); a.metric("التاريخ",latest.visit_date.strftime("%d/%m/%Y")); b.metric("BP",f"{latest.sbp}/{latest.dbp}"); c.metric("BMI",latest.bmi); d.metric("Risk",f"{latest.risk_pct}%" if str(latest.risk_pct) not in ("","nan") else "-"); e.metric("Statin",latest.statin_intensity or "-")
                st.subheader("📜 تاريخ الزيارات")
                cols=["visit_date","campaign_status","age","bmi","sbp","dbp","ldl_mgdl","risk_pct","risk_color","statin_given","referral","next_followup"]
                st.dataframe(v.sort_values("visit_date",ascending=False)[cols],use_container_width=True,hide_index=True)

elif page == "📅 المتابعة والاستدعاء":
    st.title("📅 المتابعة والاستدعاء")
    df=store.df("Followup")
    if df.empty: st.info("لا توجد سجلات متابعة.")
    else:
        df["scheduled_date"]=pd.to_datetime(df.scheduled_date,errors="coerce"); today=date.today(); open_df=df[~df.status.isin(["تمت المتابعة","حضر","مغلق"])]
        due=open_df[open_df.scheduled_date.dt.date<=today].copy(); upcoming=open_df[open_df.scheduled_date.dt.date>today].copy()
        a,b,c=st.columns(3); a.metric("مستحق/متأخر",len(due)); b.metric("القادم",len(upcoming)); c.metric("إجمالي",len(df))
        st.subheader("🔴 المستحق والمتأخر")
        for _,r in due.sort_values("scheduled_date").head(100).iterrows():
            rid=r.get("id","")
            with st.expander(f"{r.get('name','')} — {r.get('national_id','')} — {r.scheduled_date.strftime('%d/%m/%Y')}"):
                opts=["مجدول","تم الاتصال","لم يرد","حضر","تمت المتابعة","مغلق"]; cur=r.get("status","") if r.get("status","") in opts else "مجدول"
                c1,c2,c3=st.columns(3); status=c1.selectbox("الموقف",opts,index=opts.index(cur),key=f"fu_s_{rid}"); call_date=c2.date_input("تاريخ الاتصال",today,key=f"fu_d_{rid}"); caller=c3.text_input("اسم المتابع",r.get("caller","") or "",key=f"fu_c_{rid}")
                if st.button("💾 حفظ",key=f"fu_b_{rid}"):
                    store.update_by_id("Followup",rid,{"status":status,"call_1_date":call_date.isoformat(),"call_1_status":status,"caller":caller}); st.success("تم تحديث المتابعة."); st.rerun()
        st.subheader("🟢 المواعيد القادمة"); st.dataframe(upcoming.sort_values("scheduled_date").head(100),use_container_width=True,hide_index=True)
        st.caption("الاستدعاء ليس زيارة جديدة؛ تُسجل زيارة جديدة فقط عند حضور المريض.")

elif page == "🚨 الإحالات":
    st.title("🚨 الإحالات — من الإحالة حتى التغذية الراجعة")
    df=store.df("Referrals")
    if df.empty: st.info("لا توجد إحالات.")
    else:
        df["referral_date"]=pd.to_datetime(df.referral_date,errors="coerce")
        st.metric("إجمالي الإحالات",len(df))
        for _,r in df.sort_values("referral_date",ascending=False).head(100).iterrows():
            rid=r.get("id","")
            with st.expander(f"{r.get('name','')} — {r.get('specialty','')} — {r.get('urgency','')}"):
                st.write(f"سبب الإحالة: {r.get('reason','-')} | تاريخ الإحالة: {r.get('referral_date','-')}")
                opts=["","تم الاتصال","لم يرد","حضر","لم يحضر","مغلق"]
                a,b,c=st.columns(3)
                s1=a.selectbox("المتابعة 1",opts,index=opts.index(r.get("followup_1_status","") if r.get("followup_1_status","") in opts else ""),key=f"rs1_{rid}")
                s2=b.selectbox("المتابعة 2",opts,index=opts.index(r.get("followup_2_status","") if r.get("followup_2_status","") in opts else ""),key=f"rs2_{rid}")
                s3=c.selectbox("المتابعة 3",opts,index=opts.index(r.get("followup_3_status","") if r.get("followup_3_status","") in opts else ""),key=f"rs3_{rid}")
                f1=st.text_input("تغذية راجعة عن العلاج",r.get("feedback_treatment","") or "",key=f"rt_{rid}")
                f2=st.text_input("الفحوصات/النتائج",r.get("feedback_tests","") or "",key=f"rtest_{rid}")
                f3=st.text_input("دخول مستشفى",r.get("feedback_admission","") or "",key=f"rad_{rid}")
                f4=st.text_area("ملاحظات أخرى",r.get("feedback_other","") or "",key=f"ro_{rid}")
                staff=st.text_input("اسم المتابع",r.get("followup_staff","") or "",key=f"rst_{rid}")
                if st.button("💾 حفظ متابعة الإحالة",key=f"rb_{rid}"):
                    store.update_by_id("Referrals",rid,{"followup_1_status":s1,"followup_2_status":s2,"followup_3_status":s3,"feedback_treatment":f1,"feedback_tests":f2,"feedback_admission":f3,"feedback_other":f4,"followup_staff":staff}); st.success("تم تحديث الإحالة."); st.rerun()

elif page == "📊 التقارير":
    st.title("📊 التقارير والبيان الشهري")
    today=date.today(); a,b,c=st.columns(3)
    with a: year=st.number_input("السنة",2020,2100,today.year)
    with b: month=st.number_input("الشهر",1,12,today.month)
    with c: gov=st.text_input("المحافظة (اختياري)")
    admin=st.text_input("الإدارة الصحية (اختياري)")
    rep=monthly_report(store,int(year),int(month),gov,admin)
    if rep.empty: st.info("لا توجد بيانات لهذا الشهر/الفلاتر.")
    else:
        risk_cols=["<5","5-10","10-20",">20"]
        a,b,c,d,e=st.columns(5); a.metric("الإجمالي",int(rep.اجمالي.sum())); b.metric("جديد",int(rep.جديد.sum())); c.metric("متردد",int(rep.متردد.sum())); d.metric("الوحدات",len(rep)); e.metric("إحالات",int(rep.احالة.sum()))
        st.dataframe(rep,use_container_width=True,hide_index=True)
        rr=pd.DataFrame({"الفئة":["<5%","5–<10%","10–<20%","≥20%"],"العدد":[int(rep[x].sum()) for x in risk_cols]}); st.subheader("❤️ توزيع الخطورة"); st.dataframe(rr,use_container_width=True,hide_index=True)
        st.download_button("⬇️ إنشاء البيان الشهري بنفس قالب Excel",report_xlsx(rep,gov,int(year),int(month)),f"البيان_الشهري_قلبك_أمانة_{int(year)}_{int(month):02d}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

elif page == "💾 تصدير البيانات":
    st.title("💾 تصدير ونسخة احتياطية")
    st.download_button("⬇️ تحميل قاعدة البيانات كاملة Excel",make_excel(store),"قلبك_أمانة_كل_البيانات.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
    for t in HEADERS: st.write(f"**{t}**: {len(store.df(t))} سجل")
    st.info("للاستخدام المؤسسي، اجعلي Google Sheets هو التخزين الدائم ثم احتفظي بتصدير دوري كنسخة احتياطية.")

elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات والحماية")
    st.markdown("""
### التخزين الدائم
فعّلي Google Sheets من Streamlit Secrets باستخدام Service Account، وشاركي ملف Google Sheet مع البريد الخاص بالحساب الخدمي كمحرر.

### حماية اختيارية برمز دخول
أضيفي إلى Secrets:
```toml
[security]
enabled = true
pin = "غيّري-هذا-الرمز"
```

### مبدأ البرنامج
- البرنامج أداة **دعم قرار للطبيب** وليس تشخيصًا ذاتيًا للمريض.
- نسبة الخطر مأخوذة من جداول WHO 2019 المتكيفة لمصر المرفوعة للمشروع، وتُحسب فقط لعمر 40–74 سنة.
- رسالة المريض تثقيف صحي عملي وليست وصفة علاجية.
- الطبيب يراجع ويعتمد القرار النهائي قبل الحفظ.
""")
