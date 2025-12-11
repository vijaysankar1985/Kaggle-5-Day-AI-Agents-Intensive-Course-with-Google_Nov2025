import os
import glob

def list_code_files(directory_path: str) -> list[str]:
    """
    Scans a directory for code files, IGNORING virtual envs and system folders.
    """
    print(f"👀 Tool Triggered: Scanning '{directory_path}'...")
    
    # IGNORE these folders to prevent noise
    ignore_dirs = {
        "lib", "site-packages", "bin", "include", "scripts", 
        "__pycache__", ".git", ".idea", ".vscode", "venv", "env", "docuops"
    }
    
    extensions = ["*.js", "*.ts", "*.md", "*.py"]
    found_files = []
    
    # Walk through the directory manually to control what we visit
    for root, dirs, files in os.walk(directory_path):
        # Filter out ignored directories in-place
        dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs and not d.startswith('.')]
        
        for file in files:
            if any(file.endswith(ext.replace("*", "")) for ext in extensions):
                # Add the relative path so it's readable
                rel_path = os.path.relpath(os.path.join(root, file), directory_path)
                found_files.append(rel_path)
        
    if not found_files:
        return ["No relevant code files found."]
        
    # Return a clean list, limited to top 20 to avoid token limits
    return found_files[:20]