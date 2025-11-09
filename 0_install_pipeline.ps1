# ========================================================
# SCRIPT D'INSTALLATION PIPELINE COMPLET RUBIK + GUI ROBOT
# Version Windows - utilise requirements_windows.txt
# ========================================================

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Installation Pipeline Complet Rubik" -ForegroundColor Cyan
Write-Host "  + Interface GUI Robot (Windows)" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Vérifier Python
Write-Host "[1/7] Verification Python..." -ForegroundColor Yellow
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Erreur - Python non trouve`n" -ForegroundColor Red
    Write-Host "Installez Python depuis https://www.python.org/downloads/`n" -ForegroundColor Yellow
    exit
}
Write-Host "  OK - $pythonCheck`n" -ForegroundColor Green

# Vérifier Tkinter (inclus avec Python sur Windows)
Write-Host "[2/7] Verification Tkinter..." -ForegroundColor Yellow
$tkinterCheck = python -c "import tkinter; print('OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Erreur - Tkinter non trouve`n" -ForegroundColor Red
    Write-Host "Reinstallez Python avec l'option 'tcl/tk and IDLE'`n" -ForegroundColor Yellow
    exit
}
Write-Host "  OK - Tkinter disponible`n" -ForegroundColor Green

# ========================================================
# VÉRIFIER REQUIREMENTS_WINDOWS.TXT
# ========================================================
Write-Host "[3/7] Verification fichier requirements..." -ForegroundColor Yellow

$requirementsFile = ".\requirements_windows.txt"

if (-not (Test-Path $requirementsFile)) {
    Write-Host "  Avertissement - requirements_windows.txt non trouve" -ForegroundColor Yellow
    
    # Vérifier si requirements.txt existe
    if (Test-Path ".\requirements.txt") {
        Write-Host "  Fichier requirements.txt trouve (version Raspberry Pi)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "ATTENTION : Sur Windows, utilisez requirements_windows.txt" -ForegroundColor Red
        Write-Host "qui contient opencv-python au lieu de python3-opencv`n" -ForegroundColor Red
        
        $choix = Read-Host "Continuer avec requirements.txt quand meme ? (O/N)"
        if ($choix -eq "O" -or $choix -eq "o") {
            $requirementsFile = ".\requirements.txt"
            Write-Host "  OK - Utilisation de requirements.txt`n" -ForegroundColor Yellow
        } else {
            Write-Host ""
            Write-Host "Installation annulee" -ForegroundColor Red
            Write-Host "Telechargez requirements_windows.txt avant de continuer`n" -ForegroundColor Yellow
            exit
        }
    } else {
        Write-Host "  Erreur - Aucun fichier requirements trouve`n" -ForegroundColor Red
        Write-Host "Telechargez requirements_windows.txt dans ce dossier`n" -ForegroundColor Yellow
        exit
    }
} else {
    Write-Host "  OK - requirements_windows.txt trouve`n" -ForegroundColor Green
}

# ========================================================
# GESTION ENVIRONNEMENT EXISTANT (RÉENTRANCE)
# ========================================================
$envExists = Test-Path ".\env"
$recreateEnv = $false
$skipInstall = $false

if ($envExists) {
    Write-Host "`n============================================" -ForegroundColor Yellow
    Write-Host "  Environnement virtuel existant detecte !" -ForegroundColor Yellow
    Write-Host "============================================`n" -ForegroundColor Yellow
    
    Write-Host "Que voulez-vous faire ?" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [1] Mettre a jour les dependances seulement" -ForegroundColor White
    Write-Host "      (Rapide - recommande si juste ajout de modules)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  [2] Recreer completement l'environnement" -ForegroundColor White
    Write-Host "      (Long - si problemes ou changement Python)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  [3] Annuler et quitter" -ForegroundColor White
    Write-Host ""
    
    do {
        $choix = Read-Host "Votre choix (1/2/3)"
    } while ($choix -notin @("1", "2", "3"))
    
    switch ($choix) {
        "1" {
            Write-Host "`nMode : Mise a jour des dependances uniquement" -ForegroundColor Green
            $recreateEnv = $false
            $skipInstall = $false
        }
        "2" {
            Write-Host "`nMode : Recreation complete de l'environnement" -ForegroundColor Green
            Write-Host "Suppression de l'ancien environnement..." -ForegroundColor Yellow
            Remove-Item ".\env" -Recurse -Force
            $recreateEnv = $true
            $skipInstall = $false
        }
        "3" {
            Write-Host "`nInstallation annulee" -ForegroundColor Yellow
            exit
        }
    }
    Write-Host ""
}

# ========================================================
# CRÉATION ENVIRONNEMENT (si nécessaire)
# ========================================================
if (-not $envExists -or $recreateEnv) {
    Write-Host "[4/7] Creation environnement virtuel..." -ForegroundColor Yellow
    python -m venv env
    if (Test-Path ".\env\Scripts\Activate.ps1") {
        Write-Host "  OK - Environnement cree`n" -ForegroundColor Green
    } else {
        Write-Host "  Erreur - Creation echouee`n" -ForegroundColor Red
        exit
    }
} else {
    Write-Host "[4/7] Environnement virtuel..." -ForegroundColor Yellow
    Write-Host "  OK - Environnement existant conserve`n" -ForegroundColor Green
}

# ========================================================
# ACTIVATION ENVIRONNEMENT
# ========================================================
Write-Host "[5/7] Activation environnement..." -ForegroundColor Yellow
& ".\env\Scripts\Activate.ps1"
Write-Host "  OK - Active`n" -ForegroundColor Green

# ========================================================
# MISE À JOUR PIP (toujours faire)
# ========================================================
Write-Host "[6/7] Mise a jour pip, setuptools, wheel..." -ForegroundColor Yellow
Write-Host "  (Cela peut prendre quelques secondes)" -ForegroundColor Gray
Write-Host ""
& ".\env\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK - Outils mis a jour`n" -ForegroundColor Green
} else {
    Write-Host "  Avertissement - Mise a jour partielle`n" -ForegroundColor Yellow
}

# ========================================================
# INSTALLATION DÉPENDANCES
# ========================================================
if (-not $skipInstall) {
    Write-Host "[7/7] Installation des dependances..." -ForegroundColor Yellow
    Write-Host "  Fichier utilise : $requirementsFile" -ForegroundColor Cyan
    Write-Host "  (Cela peut prendre plusieurs minutes)" -ForegroundColor Gray
    Write-Host ""

    $requirements = Get-Content $requirementsFile
    Write-Host "  Dependances a installer :" -ForegroundColor Cyan
    foreach ($req in $requirements) {
        if ($req -and -not $req.StartsWith("#") -and -not $req.StartsWith("sudo") -and $req.Trim() -ne "") {
            Write-Host "    - $req" -ForegroundColor Gray
        }
    }
    Write-Host ""

    & ".\env\Scripts\pip.exe" install -r $requirementsFile

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  OK - Dependances installees`n" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  Erreur - Installation echouee`n" -ForegroundColor Red
        Write-Host "  Vous pouvez relancer ce script pour reessayer`n" -ForegroundColor Yellow
        exit
    }
} else {
    Write-Host "[7/7] Installation des dependances..." -ForegroundColor Yellow
    Write-Host "  OK - Etape ignoree`n" -ForegroundColor Green
}

# ========================================================
# CRÉATION DOSSIERS
# ========================================================
Write-Host "Creation des dossiers necessaires..." -ForegroundColor Yellow
if (-not (Test-Path ".\tmp")) {
    New-Item -ItemType Directory -Path ".\tmp" | Out-Null
    Write-Host "  OK - Dossier tmp cree" -ForegroundColor Green
} else {
    Write-Host "  OK - Dossier tmp existe" -ForegroundColor Green
}

if (-not (Test-Path ".\logs")) {
    New-Item -ItemType Directory -Path ".\logs" | Out-Null
    Write-Host "  OK - Dossier logs cree" -ForegroundColor Green
} else {
    Write-Host "  OK - Dossier logs existe" -ForegroundColor Green
}
Write-Host ""

# ========================================================
# VÉRIFICATION MODULES CRITIQUES
# ========================================================
Write-Host "Verification des modules critiques..." -ForegroundColor Yellow
$modules = @(
    @{Name="numpy"; Import="numpy"},
    @{Name="opencv"; Import="cv2"},
    @{Name="matplotlib"; Import="matplotlib"},
    @{Name="tkinter"; Import="tkinter"},
    @{Name="Pillow"; Import="PIL"},
    @{Name="kociemba"; Import="kociemba"},
    @{Name="ultralytics"; Import="ultralytics"},
    @{Name="colorama"; Import="colorama"}
)

$allOk = $true
foreach ($mod in $modules) {
    $check = & ".\env\Scripts\python.exe" -c "import $($mod.Import); print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK - $($mod.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ERREUR - $($mod.Name)" -ForegroundColor Red
        $allOk = $false
    }
}
Write-Host ""

if (-not $allOk) {
    Write-Host "ATTENTION : Certains modules sont manquants !" -ForegroundColor Red
    Write-Host "Relancez le script avec l'option [2] (Recreation complete)`n" -ForegroundColor Yellow
}

# ========================================================
# CRÉATION SCRIPTS (toujours recréer)
# ========================================================
Write-Host "Creation/Mise a jour des scripts..." -ForegroundColor Yellow
Write-Host ""

# Script d'activation
"# Activer environnement Pipeline Rubik" > ".\activate_env.ps1"
"Set-Location `"$PWD`"" >> ".\activate_env.ps1"
"Write-Host `"Activation environnement Pipeline...`" -ForegroundColor Cyan" >> ".\activate_env.ps1"
"& `".\env\Scripts\Activate.ps1`"" >> ".\activate_env.ps1"
"Write-Host `"Environnement active !`" -ForegroundColor Green" >> ".\activate_env.ps1"
"Write-Host `"`"" >> ".\activate_env.ps1"
Write-Host "  OK - activate_env.ps1" -ForegroundColor Green

# Script text_gui.py
"@echo off" | Out-File -FilePath ".\1_text_gui.bat" -Encoding ASCII
"call .\env\Scripts\activate.bat" | Out-File -FilePath ".\1_text_gui.bat" -Append -Encoding ASCII
"python text_gui.py" | Out-File -FilePath ".\1_text_gui.bat" -Append -Encoding ASCII
"pause" | Out-File -FilePath ".\1_text_gui.bat" -Append -Encoding ASCII
Write-Host "  OK - 1_text_gui.bat" -ForegroundColor Green

# Script tkinter_gui_robot.py
"@echo off" | Out-File -FilePath ".\2_gui_robot.bat" -Encoding ASCII
"call .\env\Scripts\activate.bat" | Out-File -FilePath ".\2_gui_robot.bat" -Append -Encoding ASCII
"python tkinter_gui_robot.py" | Out-File -FilePath ".\2_gui_robot.bat" -Append -Encoding ASCII
"pause" | Out-File -FilePath ".\2_gui_robot.bat" -Append -Encoding ASCII
Write-Host "  OK - 2_gui_robot.bat" -ForegroundColor Green

# Script de vérification
"@echo off" | Out-File -FilePath ".\0_check_dependencies.bat" -Encoding ASCII
"call .\env\Scripts\activate.bat" | Out-File -FilePath ".\0_check_dependencies.bat" -Append -Encoding ASCII
"python check_dependencies.py" | Out-File -FilePath ".\0_check_dependencies.bat" -Append -Encoding ASCII
"pause" | Out-File -FilePath ".\0_check_dependencies.bat" -Append -Encoding ASCII
Write-Host "  OK - 0_check_dependencies.bat" -ForegroundColor Green
Write-Host ""

# ========================================================
# RÉSUMÉ
# ========================================================
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION/MISE A JOUR TERMINEE !" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Plateforme      : Windows" -ForegroundColor Yellow
Write-Host "Environnement   : $PWD\env" -ForegroundColor Yellow
Write-Host "Requirements    : $requirementsFile" -ForegroundColor Yellow
Write-Host ""

Write-Host "Scripts disponibles :" -ForegroundColor Yellow
Write-Host ""
Write-Host "  VERIFICATION :" -ForegroundColor Cyan
Write-Host "   .\0_check_dependencies.bat  - Verifier les dependances" -ForegroundColor White
Write-Host ""
Write-Host "  INTERFACES :" -ForegroundColor Cyan
Write-Host "   .\1_text_gui.bat            - Interface texte (developpement)" -ForegroundColor White
Write-Host "   .\2_gui_robot.bat           - Interface GUI robot (production)" -ForegroundColor White
Write-Host ""
Write-Host "  ANCIENS SCRIPTS :" -ForegroundColor Cyan
Write-Host "   .\main_menu_solveur.bat     - Menu principal (si existe)" -ForegroundColor White
Write-Host "   .\main_robot_solveur.bat    - Robot solveur (si existe)" -ForegroundColor White
Write-Host ""
Write-Host "  UTILITAIRE :" -ForegroundColor Cyan
Write-Host "   .\activate_env.ps1          - Activer l'environnement" -ForegroundColor White
Write-Host ""

Write-Host "Utilisation rapide :" -ForegroundColor Yellow
Write-Host "   1. Double-cliquez sur 0_check_dependencies.bat" -ForegroundColor Cyan
Write-Host "   2. Si tout est OK, lancez :" -ForegroundColor Cyan
Write-Host "      - 1_text_gui.bat (dev) ou" -ForegroundColor Cyan
Write-Host "      - 2_gui_robot.bat (production)" -ForegroundColor Cyan
Write-Host ""

# ========================================================
# VÉRIFICATION FICHIERS PROJET
# ========================================================
Write-Host "Fichiers du projet :" -ForegroundColor Yellow
$files = @(
    "robot_moves.py",
    "robot_solver.py",
    "tkinter_gui_robot.py",
    "text_gui.py",
    "check_dependencies.py",
    "requirements_windows.txt"
)

$missingFiles = @()
foreach ($file in $files) {
    if (Test-Path ".\$file") {
        Write-Host "  OK - $file" -ForegroundColor Green
    } else {
        Write-Host "  MANQUANT - $file" -ForegroundColor Red
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "ATTENTION : Fichiers manquants !" -ForegroundColor Red
    Write-Host "Telechargez ces fichiers avant de lancer les interfaces.`n" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Dossiers :" -ForegroundColor Yellow
Get-ChildItem . -Directory | Select-Object Name | Format-Table -AutoSize

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
if ($allOk -and $missingFiles.Count -eq 0) {
    Write-Host "Installation reussie - Tout est pret !" -ForegroundColor Green
} elseif (-not $allOk) {
    Write-Host "Installation terminee avec avertissements" -ForegroundColor Yellow
    Write-Host "Relancez le script pour corriger les problemes" -ForegroundColor Yellow
} else {
    Write-Host "Installation terminee - Fichiers manquants" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "PROCHAINE ETAPE : Verifier les dependances" -ForegroundColor Yellow
Write-Host "   .\0_check_dependencies.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour relancer ce script : .\0_install_pipeline.ps1" -ForegroundColor Gray
Write-Host ""
