import os
import unicodedata
import re

def to_snake_case(name):
    # Normalize unicode characters (e.g., ç -> c, ã -> a)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Convert to lowercase
    name = name.lower()
    # Replace non-alphanumeric characters with underscores
    name = re.sub(r'[^a-z0-9]', '_', name)
    # Remove duplicate underscores
    name = re.sub(r'_+', '_', name)
    # Strip leading/trailing underscores
    name = name.strip('_')
    return name

def rename_files():
    target_dir = '/Users/gabrielramos/docx_tool/Administrativo'

    if not os.path.exists(target_dir):
        print(f"Directory not found: {target_dir}")
        return

    files = os.listdir(target_dir)
    print(f"Found {len(files)} files in {target_dir}")

    for filename in files:
        if filename.startswith('.'): # Skip hidden files
            continue

        # Split extension
        name, ext = os.path.splitext(filename)

        # Convert name to snake_case
        new_name = to_snake_case(name)

        # Reassemble
        new_filename = f"{new_name}{ext}"

        if new_filename != filename:
            old_path = os.path.join(target_dir, filename)
            new_path = os.path.join(target_dir, new_filename)

            # Handle potential collisions (though unlikely with this specific set)
            if os.path.exists(new_path):
                print(f"Skipping {filename} -> {new_filename} (Target exists)")
                continue

            print(f"Renaming: {filename} -> {new_filename}")
            os.rename(old_path, new_path)

if __name__ == "__main__":
    rename_files()
