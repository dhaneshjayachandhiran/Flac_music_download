import os
import shutil
import re
from collections import defaultdict

# Input and output folders
source_folder = "/home/dhanesh/Music/Flac_songs"
destination_folder = "/home/dhanesh/Music/final flac"

# Create destination if not exists
os.makedirs(destination_folder, exist_ok=True)

# Regex to match "song(1).flac", "song(2).flac", etc.
duplicate_pattern = re.compile(r"(.*?)(\(\d+\))?\.flac$", re.IGNORECASE)

# To track duplicates
duplicates = defaultdict(list)

for file in os.listdir(source_folder):
    if file.lower().endswith(".flac"):
        match = duplicate_pattern.match(file)
        if match:
            base_name = match.group(1).strip()  # Song name without (n)
            original_name = base_name + ".flac"
            full_path = os.path.join(source_folder, file)

            if file == original_name:
                # Copy only the original one (no (n) in filename)
                dest_path = os.path.join(destination_folder, file)
                if not os.path.exists(dest_path):  # Avoid overwriting
                    shutil.copy2(full_path, dest_path)
            else:
                # It's a duplicate
                duplicates[original_name].append(file)

# Print report
print("Duplicate Report:\n")
for original, dups in duplicates.items():
    print(f"{original} has {len(dups)} duplicates: {', '.join(dups)}")

print("\n✅ Unique songs copied to:", destination_folder)
