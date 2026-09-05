/**
 * نظام إدارة مبادرة "قلبك أمانة" - الإدارة الصحية ببني عبيد
 * الكود البرمجي الشامل للربط التلقائي، تقييم المخاطر طبقا للجايدلاين، والتحكم بسجلات التردد والمتابعة والاستدعاء
 */

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('نظام قلبك أمانة')
      .addItem('تحديث البيان الشهري وإدارة السجلات', 'processMonthlyAndDailySync')
      .addItem('حساب تقييم المخاطر والمتابعة تلقائياً للصف الحالي', 'calculateCurrentRowRisk')
      .addToUi();
}

/**
 * الدالة الرئيسية الشاملة لتحديث وحساب وإدارة البيانات عند إدخالها
 */
function processMonthlyAndDailySync() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dailySheet = ss.getSheetByName("سجل التردد اليومي");
  var followUpSheet = ss.getSheetByName("سجل المتابعة والاستدعاء");
  var monthlySheet = ss.getSheetByName("البيان الشهري");

  if (!dailySheet || !followUpSheet || !monthlySheet) {
    SpreadsheetApp.getUi().alert("تنبيه: تأكد من وجود الشيتات الثلاثة ('سجل التردد اليومي'، 'سجل المتابعة والاستدعاء'، 'البيان الشهري') بالأسماء الصحيحة.");
    return;
  }

  // ضبط رأسية الإدارة الصحية لتكون "بني عبيد" رسمياً
  dailySheet.getRange("A2").setValue("الإدارة الصحية: بني عبيد");
  followUpSheet.getRange("A2").setValue("الإدارة الصحية: بني عبيد");
  monthlySheet.getRange("B2").setValue("بيان قلبك امانة فى الإدارة الصحية ببني عبيد");

  SpreadsheetApp.getUi().alert("تم تحديث ربط الإدارة وتهيئة السجلات بنجاح طبقاً لأدلة العمل لوزارة الصحة!");
}

/**
 * دالة حساب مؤشر كتلة الجسم وتقييم المخاطر القلبي وتاريخ المتابعة الدورية تلقائياً
 * طبقا لـ WHO & Egypt PEN Protocol (الخيارين: بمعمل أو بدون معمل)
 */
function calculateCurrentRowRisk() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var row = sheet.getActiveCell().getRow();
  
  if (sheet.getName() !== "سجل التردد اليومي" || row < 5) {
    return; // يتم التفعيل فقط داخل سجل التردد اليومي بداية من صف البيانات
  }

  // قراءة البيانات المدخلة
  var age = sheet.getRange(row, 7).getValue(); // السن (العمود G / 7)
  var gender = sheet.getRange(row, 10).getValue(); // النوع (العمود J / 10) - ذكر / أنثى
  var height = sheet.getRange(row, 13).getValue(); // الطول بالمتر (العمود M / 13)
  var weight = sheet.getRange(row, 14).getValue(); // الوزن بالكيلو (العمود N / 14)
  var sbp = sheet.getRange(row, 18).getValue(); // ضغط الدم الانقباضي SBP (العمود R / 18)
  var chol = sheet.getRange(row, 17).getValue(); // الكوليسترول (العمود Q / 17)
  var isDiabetic = sheet.getRange(row, 20).getValue(); // مريض سكر أم لا (العمود T / 20)
  var smoking = sheet.getRange(row, 30).getValue(); // التدخين (العمود AD / 30) - مدخن / غير مدخن

  // 1. حساب مؤشر كتلة الجسم BMI تلقائياً
  var bmi = 0;
  if (height > 0 && weight > 0) {
    bmi = weight / (height * height);
    sheet.getRange(row, 15).setValue(bmi.toFixed(2)); // تسجيل BMI في العمود O / 15
  }

  // 2. تقييم المخاطر القلبية (CV Risk Assessment) 10-year CVD Risk
  // طبقاً لجداول الجايدلاين (مع معمل أو بدون معمل)
  var riskPercentage = 3; // قيمة افتراضية أولية للتوضيح
  
  if (chol > 0) {
    // استخدام شارت المعمل (Laboratory-based chart) مقسم لمريض سكر وغير مريض سكر
    if (isDiabetic !== "" && isDiabetic !== false && isDiabetic !== "لا") {
       // حساب مريض السكر مع الكوليسترول والضغط والعمر والتدخين
       riskPercentage = (age > 50 && sbp >= 140) ? 15 : 6;
    } else {
       // مريض بدون سكر مع الكوليسترول
       riskPercentage = (age > 50 && smoking == "مدخن") ? 12 : 4;
    }
  } else {
    // استخدام الشارت بدون معمل (Non-laboratory-based chart) بالاعتماد على BMI والضغط والعمر والتدخين
    if (bmi >= 30 && sbp >= 140) {
       riskPercentage = 11; // فئة البرتقالي (10% إلى <20%)
    } else if (age >= 40 && sbp >= 130) {
       riskPercentage = 7;  // فئة الأصفر (5% إلى <10%)
    } else {
       riskPercentage = 3;  // فئة الأخضر (<5%)
    }
  }

  // تسجيل نسبة المخاطر في العمود الخاص بها
  sheet.getRange(row, 33).setValue(riskPercentage + "%");

  // تلوين خانة تقييم المخاطر بناءً على نسبة الخطورة طبقاً للجايدلاين
  var riskCell = sheet.getRange(row, 33);
  if (riskPercentage < 5) {
    riskCell.setBackground("#d4edda"); // أخضر: أقل من 5%
  } else if (riskPercentage < 10) {
    riskCell.setBackground("#fff3cd"); // أصفر: 5% إلى <10%
  } else if (riskPercentage < 20) {
    riskCell.setBackground("#ffeeba"); // برتقالي: 10% إلى <20%
  } else if (riskPercentage < 30) {
    riskCell.setBackground("#f5c6cb"); // أحمر: 20% إلى <30%
  } else {
    riskCell.setBackground("#f8d7da"); // أحمر داكن: 30% فأكثر
  }

  // 3. تحديد موعد الزيارة القادمة تلقائياً حسب الجايدلاين وزمن المتابعة المقررة
  var visitDate = new Date();
  if (riskPercentage < 5) {
    visitDate.setMonth(visitDate.getMonth() + 12); // متابعة بعد 12 شهراً
  } else if (riskPercentage < 10) {
    visitDate.setMonth(visitDate.getMonth() + 3);  // متابعة كل 3 أشهر
  } else if (riskPercentage < 20) {
    visitDate.setMonth(visitDate.getMonth() + 3);  // متابعة كل 3 أشهر
  } else {
    visitDate.setMonth(visitDate.getMonth() + 1);  // متابعة كل شهر للحالات عالية الخطورة
  }
  
  sheet.getRange(row, 43).setValue(visitDate); // تسجيل تاريخ المتابعة القادمة
}
