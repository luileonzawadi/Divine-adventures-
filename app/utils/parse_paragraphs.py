import re
import html

file_path = r"C:\Users\leonm\.gemini\antigravity\brain\a8c93ce7-ccfa-491f-b041-00a844471bbb\.system_generated\steps\8\content.md"
output_path = r"c:\Users\leonm\Desktop\Devine adventures\app\utils\parsed_text.txt"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's strip script and style tags first
content_clean = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
content_clean = re.sub(r"<style[^>]*>.*?</style>", "", content_clean, flags=re.DOTALL | re.IGNORECASE)

# Get all text inside elements or paragraphs
paragraphs = re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", content_clean, re.IGNORECASE | re.DOTALL)
headings = re.findall(r"<(h[1-6])(?:\s[^>]*)?>(.*?)</\1>", content_clean, re.IGNORECASE | re.DOTALL)

with open(output_path, "w", encoding="utf-8") as out:
    out.write("=== HEADINGS ===\n")
    for tag, text in headings:
        clean_text = re.sub(r"<[^>]*>", "", text)
        clean_text = html.unescape(clean_text.strip())
        if clean_text:
            out.write(f"{tag.upper()}: {clean_text}\n")
            
    out.write("\n=== PARAGRAPHS ===\n")
    for p in paragraphs:
        clean_text = re.sub(r"<[^>]*>", "", p)
        clean_text = html.unescape(clean_text.strip())
        # Collapse whitespace
        clean_text = re.sub(r"\s+", " ", clean_text)
        if len(clean_text) > 20:
            out.write(f"- {clean_text}\n")

print("Saved output to", output_path)
