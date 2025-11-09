@echo off
chcp 65001 >nul
title 🧹 Désinstallation du pipeline Rubik's Cube

echo ============================================================
echo     🧱 Désinstallation du pipeline Rubik's Cube
echo ============================================================
echo.

set /p CONFIRM="⚠️  Cette action va supprimer l'environnement Python 'env' et les caches. Continuer ? (O/N) : "
if /I not "%CONFIRM%"=="O" (
    echo ❌ Opération annulée.
    pause
    exit /b 0
)

if exist ".\env" (
    echo 🧱 Suppression de l'environnement virtuel...
    rmdir /s /q ".\env"
) else (
    echo ℹ️  Aucun environnement virtuel trouvé.
)

echo 🧹 Nettoyage des fichiers temporaires...
for /r %%i in (*.pyc) do del /q "%%i"
for /d /r %%i in (__pycache__) do rmdir /s /q "%%i" 2>nul

if exist ".\logs" (
    echo 🗑️  Suppression du dossier logs...
    rmdir /s /q ".\logs"
)

if exist ".\.pytest_cache" (
    echo 🧪 Suppression du cache Pytest...
    rmdir /s /q ".\.pytest_cache"
)

echo.
echo ✅ Désinstallation terminée avec succès.
echo ============================================================
pause
