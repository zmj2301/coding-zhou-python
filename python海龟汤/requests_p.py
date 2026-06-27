import requests

def parse_html(html):
    find_name = "宋江"
    url = f"https://www.quark.cn/s/J7AUy3Va3I226LiHWY?from=kkframenew_resultsearch&uc_param_str=ntnwvepffrbiprsvchutosstxs&by=submit&q={find_name}&queryId=IsF67t2VmKDKFX6g0MegCM8oequrX7X9qfx9rUMXcKsriLpreATq1EBzBsDn5xJEIVp21w0xQlXKe9OHYiqyVO16UutJs"
    res = requests.get(url)
    print(url)
    state = res.status_code
    if state != 200:
        return state,None
    return state,res.text

def write_html(html,filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


state,html = parse_html("")
if state == 200:
    write_html(html,"test.html")
