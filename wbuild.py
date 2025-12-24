import os
import subprocess
import json
import sys

# Speichert Einstellungen im Benutzerordner (vermeidet PermissionError)
USER_HOME = os.path.expanduser("~")
CONFIG_DIR = os.path.join(USER_HOME, ".wbuild")
CONFIG_PATH = os.path.join(CONFIG_DIR, "wbuild_settings.json")

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

def get_sdk_paths():
    sdk_bin = None
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            try:
                sdk_bin = json.load(f).get("sdk_path")
            except:
                sdk_bin = None

    if not sdk_bin or not os.path.exists(os.path.join(sdk_bin, "powerpc-eabi-gcc.exe")):
        standard_paths = ["C:\\devkitPro\\devkitPPC\\bin", "D:\\devkitPro\\devkitPPC\\bin"]
        for p in standard_paths:
            if os.path.exists(os.path.join(p, "powerpc-eabi-gcc.exe")):
                sdk_bin = p
                break
    
    if not sdk_bin:
        print("\n[WBuild] devkitPPC not found!")
        sdk_bin = input("Please enter the path to devkitPPC/bin: ").strip().replace('"', '')
    
    with open(CONFIG_PATH, "w") as f:
        json.dump({"sdk_path": sdk_bin}, f)
    
    return sdk_bin

def find_elf2dol(sdk_bin):
    path1 = os.path.join(sdk_bin, "elf2dol.exe")
    if os.path.exists(path1): return path1
    devkit_pro_root = os.path.dirname(os.path.dirname(sdk_bin))
    path2 = os.path.join(devkit_pro_root, "tools", "bin", "elf2dol.exe")
    return path2 if os.path.exists(path2) else None

def run_build():
    if not os.path.exists("wbuild"):
        print("\n[WBuild] No 'wbuild' configuration file found.")
        print("Create a file named 'wbuild' with: source: main.c")
        return

    sdk_bin = get_sdk_paths()
    libogc_path = os.path.join(os.path.dirname(os.path.dirname(sdk_bin)), "libogc")

    config = {}
    with open("wbuild", "r") as f:
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                config[k.strip().lower()] = v.strip()

    source_input = config.get("source")
    if not source_input:
        print("[Error] No source files defined in 'wbuild'.")
        return

    source_files = [f.strip() for f in source_input.split(",")]
    name = config.get("name", "game")
    gcc = os.path.join(sdk_bin, "powerpc-eabi-gcc.exe")
    elf2dol = find_elf2dol(sdk_bin)

    print(f"-> Compiling {name} from {', '.join(source_files)}...")
    compile_cmd = [
        f'"{gcc}"', "-O2", "-mrvl", "-mcpu=750", "-meabi", "-mhard-float",
        f'-I"{os.path.join(libogc_path, "include")}"',
        f'-L"{os.path.join(libogc_path, "lib", "wii")}"'
    ]
    
    for s in source_files:
        compile_cmd.append(f'"{s}"')
        
    compile_cmd += ["-lwiiuse", "-lbte", "-logc", "-lm", "-o", f'"{name}.elf"']

    if subprocess.run(" ".join(compile_cmd), shell=True).returncode == 0:
        if subprocess.run(f'"{elf2dol}" "{name}.elf" "{name}.dol"', shell=True).returncode == 0:
            if os.path.exists(f"{name}.elf"): os.remove(f"{name}.elf")
            print(f"✅ Success! Created {name}.dol")
        else:
            print("❌ Error during DOL conversion.")
    else:
        print("❌ Compilation failed.")

if __name__ == "__main__":
    run_build()