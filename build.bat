@echo off
echo Установка PyInstaller...
pip install pyinstaller

echo.
echo Сборка исполняемого файла...
pyinstaller SvedUch.spec

echo.
echo Готово! Исполняемый файл находится в папке dist\SvedUch.exe
pause
