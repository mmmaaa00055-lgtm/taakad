from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn
import os
import requests
import whois
from bs4 import BeautifulSoup

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# -----------------------------
# نظام الإحصائيات
# -----------------------------
stats = {
    "safe": 0,
    "warning": 0,
    "danger": 0,
    "marouf": 0,
    "cr": 0,
    "reports": 0
}

# -----------------------------
# فحص سريع للسجل التجاري
# -----------------------------
def fast_cr_check(store_name):
    try:
        r = requests.get(
            "https://mc.gov.sa/ar/eservices/Pages/CommercialRecordInquiry.aspx",
            timeout=3
        )
        return "valid" if store_name.lower() in r.text.lower() else "not_found"
    except:
        return "error"

# -----------------------------
# فحص سريع لمعروف
# -----------------------------
def fast_marouf_check(store_name):
    try:
        r = requests.get(
            f"https://maroof.sa/Search?q={store_name}",
            timeout=3
        )
        return "registered" if "المتجر" in r.text else "not_registered"
    except:
        return "error"

# -----------------------------
# فحص سريع للبلاغات الحكومية
# -----------------------------
def fast_reports_check(store_name):
    try:
        r = requests.get(
            f"https://www.consumers.gov.sa/search?query={store_name}",
            timeout=3
        )
        text = r.text.lower()
        return "has_reports" if "بلاغ" in text or "تحذير" in text else "clean"
    except:
        return "error"

# -----------------------------
# فحص نطاق السجل التجاري
# -----------------------------
def fast_registry_check(domain):
    try:
        if domain.endswith(".sa"):
            return "saudi"
        return "global"
    except:
        return "error"

# -----------------------------
# فحص WHOIS سريع
# -----------------------------
def fast_whois(domain):
    try:
        w = whois.whois(domain)
        if w and w.creation_date:
            creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
            age_years = (2024 - creation_date.year)
            return age_years
        return 0
    except:
        return 0

# -----------------------------
# نظام التقييم السريع
# -----------------------------
def fast_check(url):
    score = 0
    domain = url.split("//")[-1].split("/")[0]
    store_name = domain.split(".")[0]

    # HTTPS
    score += 10 if url.startswith("https") else -20

    # كلمات مشبوهة
    bad_words = ["free", "win", "bank", "verify", "gift", "click", "login"]
    score -= sum(10 for w in bad_words if w in url.lower())

    # WHOIS سريع
    age = fast_whois(domain)
    score += 20 if age >= 3 else -10 if age >= 1 else -30

    # إعادة التوجيه
    try:
        r = requests.get(url, timeout=2)
        score -= 20 if len(r.history) > 1 else -5 if len(r.history) == 1 else 0
    except:
        score -= 10

    # فحص السجل التجاري
    cr = fast_cr_check(store_name)
    score += 20 if cr == "valid" else -20 if cr == "not_found" else -5

    # فحص معروف
    marouf = fast_marouf_check(store_name)
    score += 15 if marouf == "registered" else -10 if marouf == "not_registered" else -5

    # فحص البلاغات
    reports = fast_reports_check(store_name)
    score -= 40 if reports == "has_reports" else 10 if reports == "clean" else -5

    # نطاق سعودي
    registry = fast_registry_check(domain)
    score += 20 if registry == "saudi" else -10

    final_score = max(0, min(100, int((score + 100) / 2)))

    return final_score, cr, marouf, reports, registry


# -----------------------------
# صفحات الموقع
# -----------------------------
@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/result.html")
def result_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "result.html"))

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


# -----------------------------
# مسار الإحصائيات
# -----------------------------
@app.get("/stats")
def get_stats():
    return stats


# -----------------------------
# مسار الفحص
# -----------------------------
@app.get("/check")
def check(url: str):
    score, cr, marouf, reports, registry = fast_check(url)

    # تحديث الإحصائيات
    if score > 70:
        stats["safe"] += 1
    elif score > 40:
        stats["warning"] += 1
    else:
        stats["danger"] += 1

    if marouf == "registered":
        stats["marouf"] += 1

    if cr == "valid":
        stats["cr"] += 1

    if reports == "has_reports":
        stats["reports"] += 1

    domain = url.split("//")[-1].split("/")[0]
    store_name = domain.split(".")[0]

    return {
        "url": url,
        "score": score,
        "status": "آمن" if score > 70 else "مشبوه" if score > 40 else "خطر",
        "domain": domain,
        "store_name": store_name,
        "commercial_record": cr,
        "marouf": marouf,
        "reports": reports,
        "registry": registry
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
