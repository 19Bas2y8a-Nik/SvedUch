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
Или используйте PyInstaller напрямую:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name SvedUch main.py
```

Исполняемый файл будет находиться в папке `dist`.
