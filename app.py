function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  var sheetName = sheet.getName();
  
  // اسم شيت التردد اليومي
  if (sheetName === "التردد اليومي") {
    var row = e.range.getRow();
    if (row > 5) { // لتجاوز صفوف العناوين والترويسة
      syncToRecallSheet(sheet, row);
    }
  }
}

function syncToRecallSheet(dailySheet, row) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var values = dailySheet.getRange(row, 1, 1, dailySheet.getLastColumn()).getValues()[0];
  
  var patientName = values[2];     // اسم المريض (العمود الثالث)
  var fileNo = values[3];          // رقم الملف العائلي (العمود الرابع)
  var phone = values[7];           // رقم الموبايل
  var nextFollowUpDate = values[22]; // تاريخ المتابعة القادمة طبقا لتقييم المخاطر
  
  if (!patientName) return;
  
  // ربط وتحديث سجل المتابعة والاستدعاء تلقائياً
  var recallSheet = ss.getSheetByName("المتابعة والاستدعاء");
  if (recallSheet) {
    var lastRow = recallSheet.getLastRow();
    var found = false;
    
    // التحقق مما إذا كان المريض مسجلاً مسبقاً في جدول الاستدعاء لهذا الشهر
    for (var i = 6; i <= lastRow; i++) {
      if (recallSheet.getRange(i, 3).getValue() == fileNo) {
        found = true;
        // تحديث موعد المتابعة إذا تم تسجيل زيارة جديدة
        recallSheet.getRange(i, 5).setValue(nextFollowUpDate);
        break;
      }
    }
    
    // إذا لم يكن موجوداً، يتم إضافته لجدول المتابعة والاستدعاء
    if (!found) {
      var newRow = recallSheet.getLastRow() + 1;
      recallSheet.getRange(newRow, 1).setValue(newRow - 5); // المسلسل
      recallSheet.getRange(newRow, 2).setValue(patientName);
      recallSheet.getRange(newRow, 3).setValue(fileNo);
      recallSheet.getRange(newRow, 4).setValue(phone);
      recallSheet.getRange(newRow, 5).setValue(nextFollowUpDate);
      recallSheet.getRange(newRow, 6).setValue("لم يتم"); // الموقف من المتابعة مبدئياً
    }
  }
}
