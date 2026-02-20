# -*- coding: utf-8 -*-
"""
Генерирует version_is.issi из version.py и запускает Inno Setup для сборки инсталлятора.
Перед сборкой необходимо собрать exe: pyinstaller SvedUch.spec
"""
import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Сборка инсталлятора SvedUch (Inno Setup)")
    parser.add_argument("--write-issi-only", action="store_true", help="Только записать version_is.issi, не запускать ISCC")
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    sys.path.insert(0, root)
    import version
    app_version = version.__version__

    issi_path = os.path.join(root, "version_is.issi")
    with open(issi_path, "w", encoding="utf-8") as f:
        f.write('#define AppVersion "%s"\n' % app_version)

    if args.write_issi_only:
        print("Записано %s (AppVersion=%s)" % (issi_path, app_version))
        return 0

    exe_name = "SvedUch-%s.exe" % app_version
    dist_path = os.path.join(root, "dist", exe_name)
    if not os.path.isfile(dist_path):
        print("Ошибка: не найден собранный exe: %s" % dist_path)
        print("Сначала выполните: pyinstaller SvedUch.spec")
        return 1

    iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not os.path.isfile(iscc):
        iscc = "ISCC.exe"
    try:
        subprocess.run([iscc, "SvedUch.iss"], check=True)
    except FileNotFoundError:
        print("Не найден Inno Setup (ISCC). Установите Inno Setup 6 или укажите путь в PATH.")
        return 1
    except subprocess.CalledProcessError as e:
        return e.returncode

    print("Инсталлятор: installer_output\\SvedUch-%s-Setup.exe" % app_version)
    return 0

if __name__ == "__main__":
    sys.exit(main())
