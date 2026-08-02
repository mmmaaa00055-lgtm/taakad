// قراءة البيانات من الرابط
const params = new URLSearchParams(window.location.search);

const status = params.get("status");
const score = Number(params.get("score"));
const details = params.get("details");

const reviews = params.get("reviews");
const reports = params.get("reports");

// عرض البيانات
document.getElementById("status").innerText = status;
document.getElementById("details").innerText = details;
document.getElementById("circle").innerText = score + "%";

const circle = document.getElementById("circle");
const icon = document.getElementById("icon");

// تغيير اللون والأيقونة حسب النتيجة
if (score >= 80) {
    circle.classList.add("safe");
    icon.innerText = "✔️";
} else if (score >= 50) {
    circle.classList.add("warning");
    icon.innerText = "⚠️";
} else {
    circle.classList.add("danger");
    icon.innerText = "❌";
}

// زر تقييمات المستخدمين
document.getElementById("reviewsBtn").href =
    "reviews.html?reviews=" + encodeURIComponent(reviews);

// زر سجل البلاغات
document.getElementById("reportsBtn").href =
    "reports.html?reports=" + encodeURIComponent(reports);
