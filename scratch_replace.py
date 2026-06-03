import os

def replace_imports_in_dir(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "from backend.app" in content or "import backend.app" in content:
                    new_content = content.replace("from backend.app", "from app")
                    new_content = new_content.replace("import backend.app", "import app")
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Fixed: {filepath}")

replace_imports_in_dir(r"d:\Projects\Startup\MasterQ - Teacher Assitant App\backend")
