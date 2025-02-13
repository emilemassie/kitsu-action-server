import os
import shutil

def remove_pycache(root_folder):
    for dirpath, dirnames, filenames in os.walk(root_folder):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                print(f"Removed: {pycache_path}")
            except Exception as e:
                print(f"Failed to remove {pycache_path}: {e}")

if __name__ == "__main__":
    folder_to_clean = input("Enter the folder path to clean: ")
    if os.path.isdir(folder_to_clean):
        remove_pycache(folder_to_clean)
    else:
        print("Invalid folder path.")
