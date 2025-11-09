@echo off
chcp 65001 >nul
title 🧩 INSTALLATION PIPELINE RUBIK

echo ============================================================
echo     🚀 Installation du pipeline Rubik's Cube (Windows)
echo ============================================================
echo.

REM --- Exécution du script PowerShell principal ---
if exist ".\0_install_pipeline.ps1" (
    echo ⚙️  Lancement de 0_install_pipeline.ps1 ...
    powershell -ExecutionPolicy Bypass -File ".\0_install_pipeline.ps1"
) else (
    echo ❌ Fichier 0_install_pipeline.ps1 introuvable.
    pause
    exit /b 1
)

echo.
echo ✅ Installation terminée.
echo ============================================================
pause
