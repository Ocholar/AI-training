import os

files_to_remove = [
    "generate_agri_briefs.py",
    "generate_decomp.py",
    "generate_oracle.py",
    "regions_sample.json",
    "regions_sample_utf8.json",
    "output.json" # Not needed for submission
]

for f in files_to_remove:
    path = os.path.join(r"C:\Users\Administrator\harbor\agri-logistics-planning", f)
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed {f}")

# Ensure LF line endings for all relevant files
extensions = [".sh", ".py", ".json", ".md", ".toml", ".yaml", "Dockerfile"]
for root, dirs, files in os.walk(r"C:\Users\Administrator\harbor\agri-logistics-planning"):
    if "execution_logs" in root:
        continue
    for f in files:
        if any(f.endswith(ext) or f == "Dockerfile" for ext in extensions):
            path = os.path.join(root, f)
            with open(path, 'rb') as open_file:
                content = open_file.read()
            
            # Replace CRLF with LF
            new_content = content.replace(b'\r\n', b'\n')
            
            if new_content != content:
                with open(path, 'wb') as open_file:
                    open_file.write(new_content)
                print(f"Converted {f} to LF")
