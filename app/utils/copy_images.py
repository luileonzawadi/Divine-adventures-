import os
import shutil

src_dir = r"c:\Users\leonm\Desktop\Devine adventures"
dest_dir = r"c:\Users\leonm\Desktop\Devine adventures\app\static\images"

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
    print("Created directory:", dest_dir)

files = os.listdir(src_dir)
image_idx = 1

copied_files = []

for file in files:
    if file.endswith(".jpeg") or file.endswith(".jpg") or file.endswith(".png"):
        # Skip if it is the logo or already processed
        if "Logo" in file:
            dest_logo = os.path.join(dest_dir, "logo.png")
            shutil.copy2(os.path.join(src_dir, file), dest_logo)
            print(f"Copied Logo to {dest_logo}")
            continue
            
        src_path = os.path.join(src_dir, file)
        ext = os.path.splitext(file)[1].lower()
        dest_filename = f"adventure_{image_idx}{ext}"
        dest_path = os.path.join(dest_dir, dest_filename)
        
        shutil.copy2(src_path, dest_path)
        copied_files.append((file, dest_filename))
        image_idx += 1

print(f"Successfully copied {len(copied_files)} images to {dest_dir}")
for src, dest in copied_files[:10]:
    print(f"  {src} -> {dest}")
if len(copied_files) > 10:
    print(f"  ... and {len(copied_files) - 10} more")
