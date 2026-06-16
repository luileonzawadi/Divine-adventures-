import re
import html

file_path = r"C:\Users\leonm\.gemini\antigravity\brain\a8c93ce7-ccfa-491f-b041-00a844471bbb\.system_generated\steps\8\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Strip markdown line number prefixes if they exist (they are added in view_file but the file in brain is raw HTML)
# Let's inspect the first 200 chars
print("Start of file:", content[:200])

# Regex to find title
title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
if title_match:
    print("=== TITLE ===")
    print(html.unescape(title_match.group(1).strip()))

# Regex to find headings
print("\n=== HEADINGS ===")
headings = re.findall(r"<(h[1-6])(?:\s[^>]*)?>(.*?)</\1>", content, re.IGNORECASE | re.DOTALL)
for tag, text in headings:
    # Remove HTML tags inside heading
    clean_text = re.sub(r"<[^>]*>", "", text)
    clean_text = html.unescape(clean_text.strip())
    if clean_text:
        print(f"{tag.upper()}: {clean_text}")

# Regex to find nav links
print("\n=== LINKS ===")
links = re.findall(r"<a(?:\s[^>]*)?\shref=[\"']([^\"']+)[\"'](?:\s[^>]*)?>(.*?)</a>", content, re.IGNORECASE | re.DOTALL)
printed_links = set()
for href, link_text in links:
    clean_text = re.sub(r"<[^>]*>", "", link_text)
    clean_text = html.unescape(clean_text.strip())
    if clean_text and href not in printed_links and not href.startswith('#'):
        print(f"Link: {clean_text} -> {href}")
        printed_links.add(href)
        if len(printed_links) > 30:
            break
