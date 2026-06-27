@echo off
python "%~dp0pyer_gui.py" cmd %*
if exist "%~dp0pyer_next.bat" (
    call "%~dp0pyer_next.bat"
    del "%~dp0pyer_next.bat"
)
