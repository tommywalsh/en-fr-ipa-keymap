from pathlib import Path
import os
import shutil
import subprocess
import xml.etree.ElementTree as Et
import sys

XKB_ROOT = "/usr/share/X11/xkb"
EVDEV_DIR = "rules"
EVDEV_FILENAME = "evdev.xml"
SYMBOLS_DIR = "symbols"
SYMBOLS_FILENAME = "us"

BACKUP_SUFFIX = ".original"

INGESTION_DIR = "ingested"
GENERATION_DIR = "generated"

SYSTEM_SYMBOL_FILE = Path(XKB_ROOT, SYMBOLS_DIR, SYMBOLS_FILENAME)
SYSTEM_EVDEV_FILE = Path(XKB_ROOT, EVDEV_DIR, EVDEV_FILENAME)
BACKUP_SYMBOL_FILE = Path(XKB_ROOT, SYMBOLS_DIR, SYMBOLS_FILENAME + BACKUP_SUFFIX)
BACKUP_EVDEV_FILE = Path(XKB_ROOT, EVDEV_DIR, EVDEV_FILENAME + BACKUP_SUFFIX)
INGESTED_SYMBOL_FILE = Path(INGESTION_DIR, SYMBOLS_FILENAME)
INGESTED_EVDEV_FILE = Path(INGESTION_DIR, EVDEV_FILENAME)
GENERATED_SYMBOL_FILE = Path(GENERATION_DIR, SYMBOLS_FILENAME)
GENERATED_EVDEV_FILE = Path(GENERATION_DIR, EVDEV_FILENAME)


def system_is_supported():
    return os.path.isfile(SYSTEM_SYMBOL_FILE) and os.path.isfile(SYSTEM_EVDEV_FILE)


def has_been_ingested():
    return os.path.isfile(INGESTED_EVDEV_FILE) and os.path.isfile(INGESTED_SYMBOL_FILE)


def force_ingest():
    assert system_is_supported()
    shutil.copy(SYSTEM_EVDEV_FILE, INGESTED_EVDEV_FILE)
    shutil.copy(SYSTEM_SYMBOL_FILE, INGESTED_SYMBOL_FILE)


def ingest_if_necessary():
    if not has_been_ingested():
        force_ingest()


def generate_symbol_file():
    # This'll only work on posix-like systems, but the whole point is to create an X11 file, so that's fine
    with open(GENERATED_SYMBOL_FILE, "w") as outfile:
        subprocess.run(["cat", INGESTED_SYMBOL_FILE, "custom.keymap"], stdout=outfile, check=True)


def find_us_layout_variant_list(tree):
    root = tree.getroot()
    layouts = root.find("layoutList")
    for layout in layouts.findall("layout"):
        config = layout.find("configItem")
        name = config.find("name")
        if name.text == "us":
            return layout.find("variantList")


def add_custom_variant_to_list(variant_list):
    new_variant = Et.SubElement(variant_list, "variant")
    config = Et.SubElement(new_variant, "configItem")
    name = Et.SubElement(config, "name")
    name.text = "us-fr-ipa"
    desc = Et.SubElement(config, "description")
    desc.text = "American English, plus French and IPA"


def generate_evdev_file():
    comment_parser = Et.XMLParser(target=Et.TreeBuilder(insert_comments=True))
    tree = Et.parse(INGESTED_EVDEV_FILE, comment_parser)
    us_variant_list = find_us_layout_variant_list(tree)
    add_custom_variant_to_list(us_variant_list)
    # Note: any DOCTYPE tag is NOT PRESERVED!
    tree.write(GENERATED_EVDEV_FILE, xml_declaration=True, encoding="UTF-8")


def is_generated():
    return os.path.exists(GENERATED_SYMBOL_FILE) and os.path.exists(GENERATED_EVDEV_FILE)


def generate_files():
    generate_symbol_file()
    generate_evdev_file()


def is_backed_up():
    return os.path.exists(BACKUP_EVDEV_FILE) and os.path.exists(BACKUP_SYMBOL_FILE)


def force_backup():
    shutil.copy(INGESTED_EVDEV_FILE, BACKUP_EVDEV_FILE)
    shutil.copy(INGESTED_SYMBOL_FILE, BACKUP_SYMBOL_FILE)


def backup_if_necessary():
    if not is_backed_up():
        force_backup()


def install_generated_files():
    assert is_backed_up()
    shutil.copy(GENERATED_EVDEV_FILE, SYSTEM_EVDEV_FILE)
    shutil.copy(GENERATED_SYMBOL_FILE, SYSTEM_SYMBOL_FILE)


def prep_dirs_if_necessary():
    for p in [INGESTION_DIR, GENERATION_DIR]:
        if not os.path.exists(p):
            os.makedirs(p)


def build():
    prep_dirs_if_necessary()
    ingest_if_necessary()
    generate_files()


def install():
    assert(is_generated())
    backup_if_necessary()
    install_generated_files()


assert(len(sys.argv) == 2)
cmd = sys.argv[1]
if cmd == "build":
    build()
else:
    assert (cmd == "install")
    install()