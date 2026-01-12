
import html
import re

def extract():
    with open("e2e_failure_2.log", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Look for the dpaste form content
    match = re.search(r'name="content" value="(Traceback.*?)"', content, re.DOTALL)
    if match:
        tb = match.group(1)
        print(html.unescape(tb))
    else:
        print("Could not find traceback in log.")

if __name__ == "__main__":
    extract()
