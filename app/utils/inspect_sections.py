import re

file_path = r"C:\Users\leonm\.gemini\antigravity\brain\a8c93ce7-ccfa-491f-b041-00a844471bbb\.system_generated\steps\8\content.md"
output_path = r"c:\Users\leonm\Desktop\Devine adventures\app\utils\sections_output.txt"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Clean up script/style
content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)

with open(output_path, "w", encoding="utf-8") as out:
    # Find "Membership Advantage"
    idx = content.find("The Membership Advantage")
    if idx != -1:
        out.write("=== MEMBERSHIP SECTION (surrounding 2500 chars) ===\n")
        out.write(content[idx-500:idx+2500])
        out.write("\n\n" + "="*40 + "\n\n")

    # Find "Adventure Awaits"
    idx2 = content.find("Adventure Awaits")
    if idx2 != -1:
        out.write("=== ADVENTURE AWAITS SECTION (surrounding 2500 chars) ===\n")
        out.write(content[idx2-500:idx2+2500])
        out.write("\n\n" + "="*40 + "\n\n")

print("Saved output to", output_path)
