@echo off
title SMOUT Compiler (WinPython Portable)
echo ===========================================
echo     COMPILATION AVEC WINPYTHON PORTABLE
echo ===========================================

set WPY_PATH=D:\Logitiels portables\WPy64-31241
set PYTHON_EXE=%WPY_PATH%\python-3.12.4.amd64\python.exe

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del /q main.spec

echo Verification de PyInstaller et Requests...
"%PYTHON_EXE%" -m pip install pyinstaller requests --quiet

echo Generation de l'EXE unique...
"%PYTHON_EXE%" -m PyInstaller --noconsole --onefile ^
 --add-data "fichiers;fichiers" ^
 --icon="fichiers/logo.ico" ^
 main.py

if exist dist\main.exe (
    ren dist\main.exe SMOUT.exe
    echo TERMINE : Ton jeu est pret dans 'dist' !
) else (
    echo [ERREUR] La compilation a echoue.
)
pause