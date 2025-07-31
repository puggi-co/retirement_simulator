import os

def create_init_files(base_dir):
    for root, dirs, files in os.walk(base_dir):
        if "__pycache__" in root:
            continue
        init_file = os.path.join(root, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("")
            print(f"Created: {init_file}")

create_init_files("src")
