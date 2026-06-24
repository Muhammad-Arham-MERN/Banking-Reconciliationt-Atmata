@echo off

taskkill /F /IM node.exe
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe

echo All Node and Python processes terminated.
pause