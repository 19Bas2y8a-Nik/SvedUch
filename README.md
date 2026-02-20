# SvedUch
Журнал завуча

## Установка

Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

Запустите приложение:
```bash
python main.py
```

## Сборка исполняемого файла

### Windows
Запустите скрипт сборки:
```bash
build.bat
```

### Linux/Mac
Запустите скрипт сборки:
```bash
chmod +x build.sh
./build.sh
```

### Ручная сборка
Или используйте PyInstaller с проектным spec-файлом (имя exe и версия берутся из `version.py`):
```bash
pip install pyinstaller
pyinstaller SvedUch.spec
```

Исполняемый файл будет в папке `dist` с именем вида `SvedUch-<версия>.exe` (версия задаётся в `version.py`).

## Сборка инсталлятора (Windows)

1. Соберите exe (см. выше): `pyinstaller SvedUch.spec`
2. Установите [Inno Setup 6](https://jrsoftware.org/isinfo.php)
3. Запустите сборку инсталлятора:
```bash
python build_installer.py
```

Инсталлятор будет создан в папке `installer_output` с именем `SvedUch-<версия>-Setup.exe`. Версия берётся из `version.py`. В состав установки входит удаление программы (секция Uninstall).
