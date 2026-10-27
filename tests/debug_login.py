import urllib.request
import urllib.parse
import re
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. GET login page
r = opener.open('http://127.0.0.1:5000/auth/login')
html = r.read().decode('utf-8')

m = re.search(r'<input[^>]+name=[\'"]csrf_token[\'"][^>]+value=[\'"]([^\'"]+)[\'"]', html)
token = m.group(1)
print("CSRF token:", token)

# 2. POST login
data = urllib.parse.urlencode({
    'email': 'demo@gutguard.local',
    'password': 'demopassword123',
    'csrf_token': token
}).encode('utf-8')

req = urllib.request.Request('http://127.0.0.1:5000/auth/login', data=data, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Content-Type': 'application/x-www-form-urlencoded',
})
r2 = opener.open(req)
print("Status:", r2.status)
print("URL:", r2.geturl())
resp2 = r2.read().decode('utf-8')
for cookie in cj:
    print("Cookie:", cookie.name, cookie.value[:20])

for line in resp2.splitlines():
    if any(k in line.lower() for k in ['danger', 'invalid', 'error', 'dashboard', 'logged in', 'alert']):
        print("Line:", line.strip())
