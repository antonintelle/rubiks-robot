# ============================================================================
#  robot_moves.py
#  ----------------
#  Objectif :
#     Implémenter la traduction entre les mouvements Singmaster standards
#     (U, R, F, L, B, D avec variantes ', 2) et les commandes réelles
#     utilisables par le robot Rubik's Cube.
#
#  Fonctions principales :
#     - rotate_face(face, turns=1, clockwise=True) :
#         Primitive bas niveau pour tourner une face donnée.
#         (À remplacer par commandes réelles des moteurs/servos).
#
#     - execute_solution(solution, progress_callback, stop_flag) :
#         Exécute directement une solution en notation Singmaster.
#         Supporte callbacks de progression et arrêt d'urgence.
#         Exemple : "U R2 F' L B D" → appels à rotate_face().
#
#     - convert_to_robot_singmaster(solution) :
#         Convertit une solution Singmaster standard en séquence
#         de mouvements compatibles avec le robot, limité aux rotations :
#             * mouvements réels : D, D', D2
#             * rotations globales : x, x', x2, z, z'
#         Exemple : "U" → "x2 D x2"
#
#  Entrées :
#     - solution : chaîne de mouvements en notation Singmaster
#
#  Sorties :
#     - Exécution des mouvements via rotate_face()
#     - Callbacks de progression pour le GUI
#
#  Extensions possibles :
#     - Intégrer une API matérielle pour piloter servos/stepper
#     - Optimiser la séquence (réduire le nombre de rotations globales)
#
# ============================================================================

import time


def rotate_face(face: str, turns: int = 1, clockwise: bool = True):
    """
    Primitive bas niveau : tourner une face donnée.
    
    Args:
        face: 'U','R','F','D','L','B' ou 'x','z' (rotations globales)
        turns: nombre de quarts de tour (1=90°, 2=180°)
        clockwise: True=horaire, False=antihoraire
    
    TODO: Remplacer par les commandes réelles moteurs/servos
    """
    direction = "CW" if clockwise else "CCW"
    print(f"→ Rotation face {face}, {turns}×90° {direction}")
    
    # Simulation d'un délai d'exécution
    # À REMPLACER par l'attente du signal "mouvement terminé" du robot
    time.sleep(0.5)  # 300ms par mouvement


def execute_solution(solution: str, progress_callback=None, stop_flag=None):
    """
    Exécute une solution (suite de mouvements Singmaster) avec callbacks.
    
    Args:
        solution: ex. "U R2 F' L B D"
        progress_callback: fonction appelée à chaque mouvement
                          callback(current, total, move, next_move, status)
                          status: "executing", "completed", "finished", "stopped"
        stop_flag: threading.Event() pour arrêt d'urgence
    
    Returns:
        bool: True si terminé, False si arrêté
    """
    # Convertir en mouvements admissibles par le robot
    solution_admissible = convert_to_robot_singmaster(solution)
    print(f"Solution pour le robot = {solution_admissible}")
    
    moves = solution_admissible.split()
    total = len(moves)
    
    for i, move in enumerate(moves):
        # ========================================
        # VÉRIFIER ARRÊT D'URGENCE
        # ========================================
        if stop_flag and stop_flag.is_set():
            if progress_callback:
                progress_callback(i, total, move, None, "stopped")
            print("🔴 ARRÊT D'URGENCE - Séquence interrompue")
            return False
        
        # ========================================
        # NOTIFIER DÉBUT DU MOUVEMENT
        # ========================================
        next_move = moves[i+1] if i+1 < total else None
        if progress_callback:
            progress_callback(i+1, total, move, next_move, "executing")
        
        # ========================================
        # EXÉCUTER LE MOUVEMENT
        # ========================================
        face = move[0]
        
        if len(move) == 1:
            # Quart de tour horaire
            rotate_face(face, turns=1, clockwise=True)
        elif move[1] == "2":
            # Demi-tour
            rotate_face(face, turns=2, clockwise=True)
        elif move[1] == "'":
            # Quart de tour antihoraire
            rotate_face(face, turns=1, clockwise=False)
        
        # ========================================
        # NOTIFIER FIN DU MOUVEMENT
        # ========================================
        if progress_callback:
            progress_callback(i+1, total, move, next_move, "completed")
    
    # ========================================
    # SÉQUENCE TERMINÉE
    # ========================================
    if progress_callback:
        progress_callback(total, total, None, None, "finished")
    
    print("✅ Séquence de mouvements terminée")
    return True


def convert_to_robot_singmaster(solution: str) -> str:
    """
    Transforme une solution Singmaster classique (U, R, F, L, B, D)
    en une séquence équivalente utilisable par le robot.
    
    Le robot est limité dans ses mouvements :
    - Mouvements réels : D, D', D2 uniquement (face du bas)
    - Rotations globales : x, x', x2, z, z' (réorienter le cube)
    
    Args:
        solution: ex. "U R2 F' L B D"
    
    Returns:
        str: solution traduite, ex. "x2 D x2 z D2 z' ..."
    
    Exemple :
        "U"  → "x2 D x2"  (rotation x2, face D, rotation inverse x2)
        "R"  → "z D z'"   (rotation z, face D, rotation inverse z')
        "D"  → "D"        (déjà en bas, direct)
    """
    # Table de correspondance : quelle rotation pour mettre la face en position D
    rotations = {
        "D": "keep",  # déjà en bas
        "U": "x2",    # haut → bas (rotation 180° sur axe X)
        "F": "x'",    # face avant → bas (rotation -90° sur axe X)
        "B": "x",     # face arrière → bas (rotation +90° sur axe X)
        "R": "z",     # face droite → bas (rotation +90° sur axe Z)
        "L": "z'",    # face gauche → bas (rotation -90° sur axe Z)
    }
    
    # Rotations inverses pour revenir à l'orientation initiale
    inverse = {
        "x": "x'",
        "x'": "x",
        "x2": "x2",
        "z": "z'",
        "z'": "z"
    }
    
    robot_moves = []
    
    for move in solution.split():
        face = move[0]
        suffix = move[1:] if len(move) > 1 else ""
        
        # 1️⃣ RÉORIENTATION si nécessaire
        if rotations[face] != "keep":
            robot_moves.append(rotations[face])
        
        # 2️⃣ EXÉCUTION avec D/D'/D2
        if suffix == "2":
            robot_moves.append("D2")
        elif suffix == "'":
            robot_moves.append("D'")
        else:
            robot_moves.append("D")
        
        # 3️⃣ RETOUR à l'orientation initiale
        if rotations[face] != "keep":
            robot_moves.append(inverse[rotations[face]])
    
    return " ".join(robot_moves)


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("TEST robot_moves.py")
    print("="*60)
    
    # Test de conversion
    print("\n1️⃣ Test de conversion:")
    solution_test = "U R2 F' L B D"
    print(f"Solution originale: {solution_test}")
    converted = convert_to_robot_singmaster(solution_test)
    print(f"Solution robot: {converted}")
    
    # Test d'exécution avec callback
    print("\n2️⃣ Test d'exécution avec callback:")
    
    def test_callback(current, total, move, next_move, status):
        if status == "executing":
            print(f"  [{current}/{total}] Exécution: {move} (suivant: {next_move})")
        elif status == "completed":
            print(f"  [{current}/{total}] ✅ {move} terminé")
        elif status == "finished":
            print(f"  ✅ Séquence complète terminée ({total} mouvements)")
    
    execute_solution("U R F", progress_callback=test_callback)
    
    print("\n3️⃣ Test arrêt d'urgence:")
    import threading
    
    stop = threading.Event()
    
    def test_with_stop():
        # Arrêter après 1.5 secondes
        time.sleep(1.5)
        print("\n🔴 Activation arrêt d'urgence...")
        stop.set()
    
    # Lancer l'arrêt en parallèle
    stop_thread = threading.Thread(target=test_with_stop)
    stop_thread.start()
    
    # Exécuter une longue séquence
    execute_solution("U R F L B D U' R' F' L'", 
                    progress_callback=test_callback,
                    stop_flag=stop)
    
    stop_thread.join()
    print("\n✅ Tests terminés")