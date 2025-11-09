@echo off
chcp 65001 >nul
title 🤖 Mode Robot - Rubik's Cube

echo ============================================================
echo     🚀 Lancement du solveur Rubik's Cube (mode robot)
echo ============================================================
echo.

REM --- Activation de l'environnement virtuel ---
if exist ".\env\Scripts\activate.bat" (
    call .\env\Scripts\activate.bat
) else (
    echo ❌ Environnement virtuel non trouvé : .\env
    echo ➡️  Lance d'abord 0_install_pipeline.bat
    echo.
    pause
    exit /b 1
)

REM --- Lancement du script Python ---
echo 🧩 Démarrage du script main_robot_solveur.py ...
echo.
python main_robot_solveur.py

REM --- Désactivation propre ---
call deactivate
echo.
echo ✅ Fin du mode robot Rubik's Cube.
echo ============================================================
pause
