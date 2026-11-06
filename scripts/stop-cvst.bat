@echo off
REM Stop everything started by start-cvst.bat
for %%T in ("CVST Backend" "CVST Frontend" "CVST Celery") do (
  taskkill /fi "WINDOWTITLE eq %%~T*" /t /f >nul 2>nul && echo Stopped %%~T
)
