import os
import shutil

# Name of the master folder where sorted index images will be stored
INDEXES_ROOT = 'Indexes'

# Create the main 'Indexes' folder in the current directory (if it doesn't exist)
os.makedirs(INDEXES_ROOT, exist_ok=True)

# Read folder names (samples) from folder_list.txt
folder_list = []
with open('folder_list.txt', 'r') as f:
    for line in f:
        name = line.strip()
        if name:
            folder_list.append(name)

# Decide whether to use Corrected_ folders or raw folders
# If ANY Corrected_<folder> exists, we work in "corrected mode" and only use those
corrected_mode = any(os.path.isdir('Corrected_' + fld) for fld in folder_list)

if corrected_mode:
    print("Detected 'Corrected_' folders – using only those.")
else:
    print("No 'Corrected_' folders detected – using original folders from folder_list.txt.")

def safe_copy(src, dst_dir, base_name):
    """
    Copy src into dst_dir with file name base_name + extension.
    If the file already exists, append _1, _2, ... to avoid overwriting.
    """
    os.makedirs(dst_dir, exist_ok=True)
    _, ext = os.path.splitext(src)
    dest = os.path.join(dst_dir, base_name + ext)

    if os.path.exists(dest):
        counter = 1
        while True:
            alt = os.path.join(dst_dir, f"{base_name}_{counter}{ext}")
            if not os.path.exists(alt):
                dest = alt
                break
            counter += 1

    shutil.copy2(src, dest)
    print(f"  Copied: {src}  -->  {dest}")

# Process each folder / sample
for sample_name in folder_list:
    # Determine which folder on disk to use
    if corrected_mode:
        folder = 'Corrected_' + sample_name
    else:
        folder = sample_name

    if not os.path.isdir(folder):
        print(f"Skipping '{sample_name}' (folder '{folder}' not found).")
        continue

    print(f"Processing sample folder: {folder}")

    # Look for Indexes_out and/or Indexes_out_fluorescence inside this folder
    candidate_subfolders = [
        os.path.join(folder, 'Indexes_out'),
        os.path.join(folder, 'Indexes_out_fluorescence')
    ]

    found_any = False

    for idx_folder in candidate_subfolders:
        if not os.path.isdir(idx_folder):
            continue  # skip if this particular index folder doesn't exist

        found_any = True
        print(f"  Found index folder: {idx_folder}")

        # List image files (common image extensions)
        for fname in os.listdir(idx_folder):
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp')):
                continue

            # Determine index name from file name
            # Expected pattern: Image_INDEXNAME.ext
            name_no_ext, _ = os.path.splitext(fname)
            if name_no_ext.startswith('Image_'):
                index_name = name_no_ext[len('Image_'):]
            else:
                # Fallback: use whole name without extension
                index_name = name_no_ext

            # Destination folder for this index
            dest_index_folder = os.path.join(INDEXES_ROOT, index_name)

            # Copy and rename image: use original sample name as base
            src_path = os.path.join(idx_folder, fname)
            safe_copy(src_path, dest_index_folder, sample_name)

    if not found_any:
        print(f"  No 'Indexes_out' or 'Indexes_out_fluorescence' found in '{folder}', skipping.")

print("Done collecting index images into 'Indexes' folder.")
