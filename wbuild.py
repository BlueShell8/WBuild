import os
import subprocess

def run_build():
    project_dir = os.getcwd()
    
    # Check for configuration file
    if not os.path.exists(os.path.join(project_dir, "wbuild")):
        print(f"[WBuild] Error: Configuration 'wbuild' not found.")
        return

    # Get devkitPro path from system environment variables only
    base = os.environ.get("DEVKITPRO")
    
    if not base:
        print("ERROR: DEVKITPRO environment variable not found.")
        print("Please ensure devkitPro is installed and the system variable is set.")
        return

    # Construct paths based on the system variable
    devkitppc = os.path.normpath(f"{base}/devkitPPC")
    libogc = os.path.normpath(f"{base}/libogc")
    tools_bin = os.path.normpath(f"{base}/tools/bin")

    config = {}
    with open(os.path.join(project_dir, "wbuild"), "r") as f:
        raw = f.read().replace("\n", " ").replace("\r", " ")
        if "name:" in raw and "source:" in raw:
            # Simple split logic to extract name and source list
            config["name"] = raw.split("name:")[1].split("source:")[0].strip()
            config["source"] = raw.split("source:")[1].strip()

    name = config.get("name", "Project")
    sources = [s.strip() for s in config.get("source", "").split(",") if s.strip()]
    
    if not sources:
        print("ERROR: No source files specified in 'wbuild' file.")
        return

    # Use g++ for both C and C++ support
    gpp = os.path.join(devkitppc, "bin", "powerpc-eabi-g++.exe")
    elf2dol = os.path.join(tools_bin, "elf2dol.exe")

    # Safety check if compiler exists
    if not os.path.exists(gpp):
        print(f"ERROR: Compiler not found at: {gpp}")
        return

    # Build command with C++ compatibility flags
    cmd = [
        f'"{gpp}"', "-O2", "-mrvl", "-mcpu=750", "-meabi", "-mhard-float",
        "-fno-exceptions", "-fno-rtti",
        f'-I"{project_dir}"',
        f'-I"{project_dir}/grrlib_files"',
        f'-I"{libogc}/include"',
        f'-L"{libogc}/lib/wii"'
    ]
    
    # Add source files
    cmd += [f'"{s}"' for s in sources]
    
    # Linking libraries
    cmd += [
        "-lgrrlib", "-lpng", "-ljpeg", "-lz", 
        "-lasnd", "-logc", "-lm", "-o", f"{name}.elf"
    ]

    print(f"-> [WBuild] Compiling {name}...")
    
    # Run compilation
    compile_proc = subprocess.run(" ".join(cmd), shell=True)
    
    if compile_proc.returncode == 0:
        print(f"-> [WBuild] Creating {name}.dol...")
        
        # Convert to DOL format
        dol_proc = subprocess.run(f'"{elf2dol}" "{name}.elf" "{name}.dol"', shell=True)
        
        if dol_proc.returncode == 0:
            if os.path.exists(f"{name}.elf"): 
                os.remove(f"{name}.elf")
            print(f"SUCCESS: '{name}.dol' created.")
        else:
            print("ERROR: elf2dol conversion failed.")
    else:
        print("ERROR: Compilation failed. Check your code and paths.")

if __name__ == "__main__":
    run_build()
