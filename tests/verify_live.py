"""
Live End-to-End Application Verification Script for GutGuard.
Runs real HTTP requests against the live running server (http://127.0.0.1:5000),
maintaining cookies, parsing HTML and JSON, and verifying all critical user journeys.
"""
import re
import urllib.request
import urllib.parse
import http.cookiejar
import json
import sys

BASE_URL = "http://127.0.0.1:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(path):
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={"User-Agent": "GutGuard-Audit-Agent"})
    try:
        resp = opener.open(req)
        return resp.status, resp.read().decode("utf-8", errors="replace"), resp.headers, resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace"), e.headers, e.geturl()

def post(path, data_dict):
    url = BASE_URL + path
    encoded = urllib.parse.urlencode(data_dict, doseq=True).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, headers={
        "User-Agent": "GutGuard-Audit-Agent",
        "Content-Type": "application/x-www-form-urlencoded"
    })
    try:
        resp = opener.open(req)
        return resp.status, resp.read(), resp.headers, resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers, e.geturl()

def extract_csrf(html):
    m = re.search(r'<input[^>]*name=[\'"]csrf_token[\'"][^>]*value=[\'"]([^\'"]+)[\'"]', html, re.I)
    if m:
        return m.group(1)
    m2 = re.search(r'<input[^>]*value=[\'"]([^\'"]+)[\'"][^>]*name=[\'"]csrf_token[\'"]', html, re.I)
    if m2:
        return m2.group(1)
    return ""

results = []
def record(name, passed, details=""):
    results.append({"name": name, "passed": passed, "details": details})
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name} - {details}")

print("=== STARTING LIVE VERIFICATION OF GUTGUARD ===")

# 1. Landing Page
status, html, headers, final_url = get("/")
record("Landing Page (Public)", status == 200 and "GutGuard" in html and "Sign In" in html, f"Status: {status}")

# 2. Extract CSRF from login page
status, html, _, _ = get("/auth/login")
csrf_token = extract_csrf(html)
record("CSRF Token on Login Form", status == 200 and bool(csrf_token), f"CSRF extracted: {csrf_token[:20]}...")

# 3. Student Login
status, data, headers, final_url = post("/auth/login", {
    "email": "demo@gutguard.local",
    "password": "demopassword123",
    "csrf_token": csrf_token,
})
html_str = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
login_success = status == 200 and "dashboard" in final_url.lower() and "Meals Today" in html_str
record("Student Login (demo@gutguard.local)", login_success, f"Final URL: {final_url}")

# 4. Student Dashboard
status, html, _, final_url = get("/dashboard")
dash_ok = status == 200 and "Dashboard" in html and "Consistency" in html and "Meals Today" in html
record("Student Dashboard Page", dash_ok, f"Status: {status}, contains Consistency & Meals Today")

# 5. Food Catalogue Browse
status, html, _, final_url = get("/catalogue/browse")
cat_ok = status == 200 and "Campus Food Catalogue" in html and "All Items" in html
record("Food Catalogue Browse Page", cat_ok, f"Status: {status}, categories rendered")

# 6. Food Catalogue Autocomplete API
status, json_str, _, _ = get("/catalogue/search?q=dosa")
try:
    foods = json.loads(json_str)
    search_ok = status == 200 and isinstance(foods, list) and len(foods) > 0 and any("Dosa" in f.get("name", "") for f in foods)
    record("Catalogue Search Autocomplete API", search_ok, f"Returned {len(foods)} items for 'dosa'")
except Exception as e:
    record("Catalogue Search Autocomplete API", False, f"JSON Error: {e}, Response: {json_str[:100]}")

# 7. Meal Journal
status, html, _, _ = get("/meals/journal")
journal_ok = status == 200 and "Meal Journal" in html and "Water Intake" in html
record("Meal Journal View", journal_ok, f"Status: {status}, contains Water Intake")

# 8. Meal Log Page & CSRF
status, html, _, _ = get("/meals/log")
log_csrf = extract_csrf(html)
log_page_ok = status == 200 and "Log a Meal" in html and bool(log_csrf)
record("Meal Log Form Load", log_page_ok, f"Status: {status}, CSRF token present: {bool(log_csrf)}")

# 9. Submit a New Meal
status, data, _, final_url = post("/meals/log", {
    "meal_type": "lunch",
    "meal_date": "2026-10-19T13:30",
    "notes": "Verified lunch from campus mess",
    "food_id[]": ["1"],
    "quantity[]": ["2"],
    "unit[]": ["piece"],
    "item_notes[]": ["chutney on side"],
    "csrf_token": log_csrf,
})
resp_str = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
meal_logged = status == 200 and ("Meal logged successfully" in resp_str or "journal" in final_url.lower())
record("Post Real Meal Log", meal_logged, f"Status: {status}, Redirect: {final_url}")

# 10. Water Intake Logging
status, html, _, _ = get("/meals/journal")
w_csrf = extract_csrf(html)
status, data, _, final_url = post("/meals/water/log", {
    "quantity": "350",
    "unit": "ml",
    "date": "2026-10-19T14:00",
    "notes": "Afternoon glass",
    "csrf_token": w_csrf,
})
w_resp = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
water_logged = status == 200 and ("Water intake logged" in w_resp or "journal" in final_url.lower())
record("Post Water Log Entry", water_logged, f"Status: {status}, Redirect: {final_url}")

# 11. Insights Page
status, html, _, _ = get("/insights/")
insights_ok = status == 200 and "Weekly Insights" in html and "mealsPerDayChart" in html and "About These Figures" in html
record("Insights Page & Charts", insights_ok, f"Status: {status}, Chart.js element found")

# 12. Insights Weekly Data API
status, json_str, _, _ = get("/insights/api/weekly-data")
try:
    wdata = json.loads(json_str)
    api_ok = status == 200 and "labels" in wdata and len(wdata["labels"]) == 7
    record("Insights Weekly Data API", api_ok, f"Labels count: {len(wdata.get('labels', []))}")
except Exception as e:
    record("Insights Weekly Data API", False, f"JSON Error: {e}, Response: {json_str[:100]}")

# 13. Reports Page & PDF Generation
status, html, _, _ = get("/reports/")
rep_csrf = extract_csrf(html)
rep_page_ok = status == 200 and "Meal Habit Reports" in html and "not medical assessments" in html
record("Reports Page & Disclaimers", rep_page_ok, f"Status: {status}, disclaimer present")

status, pdf_data, headers, _ = post("/reports/generate", {
    "period": "week",
    "csrf_token": rep_csrf,
})
is_pdf = status == 200 and pdf_data.startswith(b"%PDF")
record("PDF Report Generation (ReportLab)", is_pdf, f"Status: {status}, Magic bytes %PDF: {is_pdf}, Length: {len(pdf_data)} bytes")

# 14. Student Profile Page
status, html, _, _ = get("/auth/profile")
prof_ok = status == 200 and "Your Profile" in html and "demo@gutguard.local" in html
record("Student Profile & Privacy Notice", prof_ok, f"Status: {status}, student email displayed")

# 15. Student Forbidden on Admin Routes (RBAC)
status, html, _, _ = get("/admin/")
record("RBAC: Student Access to /admin Blocked", status == 403, f"Status: {status} (Expected 403)")

# 16. Logout
status, html, _, final_url = get("/auth/logout")
record("Student Logout", status == 200 and ("logged out" in html or final_url.endswith("/")), f"Status: {status}, URL: {final_url}")

# 17. Admin Login
# Use new cookie jar for admin
cj.clear()
status, html, _, _ = get("/auth/login")
admin_csrf = extract_csrf(html)
status, data, _, final_url = post("/auth/login", {
    "email": "admin@gutguard.local",
    "password": "AdminPass123!",
    "csrf_token": admin_csrf,
})
admin_resp = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data

status, html, _, _ = get("/admin/")
admin_ok = status == 200 and "Admin Dashboard" in html and "Active Foods" in html
record("Admin Dashboard Access", admin_ok, f"Status: {status}, Active Foods metric present")

# 18. Admin Catalogue Management
status, html, _, _ = get("/admin/catalogue")
admin_cat_ok = status == 200 and "Food Catalogue" in html
record("Admin Catalogue Management Page", admin_cat_ok, f"Status: {status}")

# 19. Admin Custom Food Queue
status, html, _, _ = get("/admin/custom-foods")
admin_custom_ok = status == 200 and "Custom Foods" in html
record("Admin Custom Foods Review Queue", admin_custom_ok, f"Status: {status}")

# 20. 404 Error Page
status, html, _, _ = get("/does-not-exist-page-404")
record("Custom 404 Error Page", status == 404 and "Page Not Found" in html, f"Status: {status}")

print("=== VERIFICATION SUMMARY ===")
total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = total - passed
print(f"Total Live Checks: {total} | Passed: {passed} | Failed: {failed}")
if failed > 0:
    sys.exit(1)
