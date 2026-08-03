#!/bin/bash
nginx -s reload 2>/dev/null
echo "nginx reloaded"
curl -sk -o /dev/null -w "status:%{http_code}\n" https://codingzhou.dpdns.org/
curl -sk https://codingzhou.dpdns.org/ | python3 -c "
import sys,re
html=sys.stdin.read()
links=re.findall(r'href=\"([^\"]+)\"', html)
for l in links:
    if 'console' in l or 'api' in l.lower():
        print(l)
"