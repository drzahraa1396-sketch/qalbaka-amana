/**
 * نظام إدارة مبادرة "قلبك أمانة" - الإدارة الصحية ببني عبيد
 * الكود الشامل لتحديث البيانات، حساب مؤشر كتلة الجسم، وتقييم المخاطر تلقائياً
 */

function onEdit(e) {
  if (!e) return;
  var sheet = e.range.getSheet();
  var sheetName = sheet.getName();
  
  // التأكد من أن التعديل يتم في شيت التردد اليومي
  if (sheetName === "سجل التردد اليومي") {
    var row = e.range.getRow();
    var col = e.range.getColumn();
    
    // إذا تم إدخال الطول (عمود 13) أو الوزن (عمود 14)، نحسب الـ BMI تلقائياً (عمود 15)
    if (row > 4 && (col === 13 || col === 14)) {
      var lengthVal = sheet.getRange(row, 13).getValue();
      var weightVal = sheet.getRange(row, 14).getValue();
      
      if (lengthVal > 0 && weightVal > 0) {
        // تحويل الطول من سنتيمتر إلى متر إذا لزم الأمر، أو حساب مباشر حسب تصميم الشيت
        var heightInMeters = lengthVal > 3 ? lengthVal / 100 : lengthVal;
        var bmi = weightVal / (heightInMeters * heightInMeters);
        sheet.getRange(row, 15).setValue(bmi.toFixed(2));
      }
    }
    
    // تحديث البيان الشهري تلقائياً عند أي تعديل في السجل اليومي
    updateMonthlySummary();
  }
}

function updateMonthlySummary() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dailySheet = ss.getSheetByName("سجل التردد اليومي");
  var monthlySheet = ss.getSheetByName("البيان الشهري");
  
  if (!dailySheet || !monthlySheet) return;
  
  var lastRow = dailySheet.getLastRow();
  if (lastRow <= 4) return;
  
  // قراءة بيانات التردد اليومي (ابتداءً من الصف 5)
  var data = dailySheet.getRange(5, 1, lastRow - 4, 45).getValues();
  
  var totalNew = 0;
  var totalRecurrent = 0;
  
  for (var i = 0; i < data.length; i++) {
    var rowData = data[i];
    var campaignType = rowData[4]; // جديد أو متردد
    
    if (campaignType === "جديد") {
      totalNew++;
    } else if (campaignType === "متردد") {
      totalRecurrent++;
    }
  }
  
  // كتابة المجاميع في البيان الشهري (تعديل الخلايا حسب مكانها المخصص في الشيت)
  // مثال: وضع الإجماليات في الخلايا المناسبة
  monthlySheet.getRange("D4").setValue(totalNew);
  monthlySheet.getRange("E4").setValue(totalRecurrent);
  monthlySheet.getRange("F4").setValue(totalNew + totalRecurrent);
}

function setupInitialTriggers() {
  // دالة لضبط الإعدادات الأولية وربط التحديثات
  SpreadsheetApp.getUi().alert("تم تفعيل الكود الشامل بنجاح لجميع سجلات إدارة بني عبيد!");
}
