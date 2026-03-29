import json
import re
import subprocess
import shutil
import os
import sys
import glob

# I extracted this process from the actual mBlock 'IDE' (the block coding one) since loading code form the Arduino IDE doesn't work.

def load_config(config_file="vars.json"):
    if not os.path.exists(config_file):
        print(f"ERROR: {config_file} not found in current directory.")
        sys.exit(1)

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse {config_file}: {e}")
        sys.exit(1)


CONFIG = load_config()
USER = CONFIG.get("user")

MBLOCK_DIR        = r"C:\Users\Public\Programs\mblock\resources\ml\v1\external\arduino"
AVR_TOOLCHAIN     = os.path.join(MBLOCK_DIR, "avr-toolchain", "bin")
MBOT_LIB          = os.path.join(MBLOCK_DIR, "mbot", "libmbot.a")

BUILD_DIR         = rf"C:\Users\{USER}\mblock-avr\temp\build"
SRC_DIR           = os.path.join(BUILD_DIR, "src")

SKETCH_FILE       = "sketch.ino"
COM_PORT          = "COM3"
BAUD_RATE         = "115200"

MCU               = "atmega328p"
F_CPU             = "16000000L"


INCLUDES = [
    os.path.join(MBLOCK_DIR, "avr-library", "variants", "standard"),
    os.path.join(MBLOCK_DIR, "avr-library", "cores", "arduino"),
    os.path.join(MBLOCK_DIR, "arduino-libraries", "makeblock", "src"),
    os.path.join(MBLOCK_DIR, "arduino-libraries", "makeblock", "src", "utility", "avr"),
    os.path.join(MBLOCK_DIR, "avr-library", "libraries", "Wire", "src", "utility"),
    os.path.join(MBLOCK_DIR, "avr-library", "libraries", "Wire", "src"),
    os.path.join(MBLOCK_DIR, "avr-library", "libraries", "EEPROM", "src"),
    os.path.join(MBLOCK_DIR, "avr-library", "libraries", "SPI", "src"),
    os.path.join(MBLOCK_DIR, "avr-library", "libraries", "SoftwareSerial", "src"),
    os.path.join(MBLOCK_DIR, "arduino-libraries", "arduino", "Servo", "src"),
    os.path.join(MBLOCK_DIR, "arduino-libraries", "arduino", "Firmata"),
    os.path.join(MBLOCK_DIR, "arduino-libraries", "arduino", "Firmata", "utility"),
    os.path.join(MBLOCK_DIR, "arduino-libraries", "arduino", "Stepper", "src"),
]

COMPILER_FLAGS = [
    "-c", "-g", "-Os", "-w",
    "-std=gnu++11",
    "-fno-exceptions",
    "-ffunction-sections",
    "-fdata-sections",
    "-fno-threadsafe-statics",
    "-MMD",
    f"-mmcu={MCU}",
    f"-DF_CPU={F_CPU}",
    "-DARDUINO=10605",
    "-DARDUINO_AVR_UNO",
    "-DARDUINO_ARCH_AVR",
    "-DMeMbot_H",   # enables mBot-specific defines in MePort.h
]


def run(cmd, label):
    print(f"\n[{label}]")
    print("  " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print(f"ERROR: {label} failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    print(f"  OK")

def include_flags():
    return [flag for path in INCLUDES for flag in ("-I", path)]

def compile_cpp(src, out):
    avr_gpp = os.path.join(AVR_TOOLCHAIN, "avr-g++")
    run(
        [avr_gpp] + COMPILER_FLAGS + include_flags() + [src, "-o", out],
        f"Compiling {os.path.basename(src)}"
    )


def find_makeblock_sources():
    """Only compile makeblock .cpp files directly included by the sketch."""
    makeblock_src = os.path.join(MBLOCK_DIR, "arduino-libraries", "makeblock", "src")

    with open(SKETCH_FILE, "r") as f:
        sketch = f.read()

    # Only look at direct includes in the sketch, not MeMCore.h
    includes = re.findall(r'#include\s*[<"](.*?)[>"]', sketch)

    headers = set(os.path.splitext(os.path.basename(h))[0] for h in includes)
    sources = []
    for header in headers:
        cpp = os.path.join(makeblock_src, header + ".cpp")
        if os.path.exists(cpp):
            sources.append(cpp)
            print(f"  [SCAN] Including: {header}.cpp")

    # Always include MePort since everything depends on it
    meport = os.path.join(makeblock_src, "MePort.cpp")
    if meport not in sources and os.path.exists(meport):
        sources.append(meport)
        print(f"  [SCAN] Including: MePort.cpp (required)")

    print(f"\n[SCAN] Compiling {len(sources)} makeblock source files")
    return sources

def main():
    if not os.path.exists(SKETCH_FILE):
        print(f"ERROR: {SKETCH_FILE} not found in current directory.")
        sys.exit(1)

    print("=" * 60)
    print(f"  mCore Sketch Uploader")
    print(f"  Sketch : {SKETCH_FILE}")
    print(f"  Port   : {COM_PORT}")
    print(f"  MCU    : {MCU}")
    print("=" * 60)

    print("\n[SETUP] Creating build directories...")
    os.makedirs(SRC_DIR, exist_ok=True)
    print(f"  Build dir : {BUILD_DIR}")
    print(f"  Src dir   : {SRC_DIR}")

    # No Arduino.h injection, mBlock sketches already have their own includes
    code_cpp = os.path.join(BUILD_DIR, "code.cpp")
    print(f"\n[SETUP] Copying {SKETCH_FILE} -> code.cpp")
    shutil.copy(SKETCH_FILE, code_cpp)

    compiled_objects = []
    for src in find_makeblock_sources():
        out = os.path.join(SRC_DIR, os.path.basename(src).replace(".cpp", ".o"))
        compile_cpp(src, out)
        compiled_objects.append(out)

    code_obj = os.path.join(BUILD_DIR, "code.o")
    compile_cpp(code_cpp, code_obj)
    compiled_objects.append(code_obj)

    elf_out = os.path.join(BUILD_DIR, "out.elf")
    avr_gcc = os.path.join(AVR_TOOLCHAIN, "avr-gcc")
    run(
        [avr_gcc, "-w", "-Os", "-Wl,--gc-sections",
         f"-mmcu={MCU}", "-o", elf_out]
        + compiled_objects
        + [MBOT_LIB, "-lm"],
        "Linking"
    )

    hex_out = os.path.join(BUILD_DIR, "out.hex")
    avr_objcopy = os.path.join(AVR_TOOLCHAIN, "avr-objcopy")
    run(
        [avr_objcopy, "-O", "ihex", "-R", ".eeprom", elf_out, hex_out],
        "Generating HEX"
    )

    print(f"\n  Build complete -> {hex_out}")

    # Upload via avrdude
    avrdude = os.path.join(AVR_TOOLCHAIN, "avrdude")
    avrdude_conf = os.path.join(AVR_TOOLCHAIN, "..", "etc", "avrdude.conf")

    run(
        [avrdude,
         "-C", avrdude_conf,
         "-v",
         f"-p{MCU}",
         "-carduino",
         f"-P{COM_PORT}",
         f"-b{BAUD_RATE}",
         "-D",
         f"-Uflash:w:{hex_out}:i"],
        "Uploading"
    )

    print("\n" + "=" * 60)
    print("  Upload complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()