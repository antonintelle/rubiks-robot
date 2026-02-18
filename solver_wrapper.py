#!/usr/bin/env python3
# ============================================================================
#  solver_wrapper.py
#  -----------------
#  Objectif :
#     Fournir un **wrapper unifié** pour résoudre un Rubik’s Cube à partir d’une
#     chaîne d’état 54 caractères (ordre URFDLB), en pouvant choisir dynamiquement
#     l’algorithme de résolution disponible sur la machine.
#
#  Solveurs supportés :
#     - "kociemba" : solveur standard (pip install kociemba)
#       -> importé au démarrage (léger, généralement présent).
#     - "k2" : Kociemba Two-Phase via RubikTwoPhase (pip install RubikTwoPhase)
#       -> importé **à la demande** (lazy import) pour éviter les temps de chargement
#          ou les erreurs sur les systèmes où le module n’est pas installé.
#
#  Entrées principales (API) :
#     - solve_cube(cube_state: str, method: str = "kociemba") -> str
#         Fonction générique :
#           * method="kociemba" -> solve_with_kociemba()
#           * method="k2"       -> solve_with_kociemba_2_state()
#         Retour : solution en notation Singmaster (ex: "R U R' U' ...").
#
#  Fonctions internes :
#     - solve_with_kociemba(cube_state: str) -> str
#         Appelle kociemba.solve(cube_state) (lève ImportError si kociemba absent).
#
#     - solve_with_kociemba_2_state(cube_state: str) -> str
#         Import dynamique : twophase.solver as sv
#         Appel : sv.solve(cube_state, 21, 5.0)  (max depth 21, timeout 5s)
#         Lève ImportError avec message clair si RubikTwoPhase non installé.
#
#  Exécution directe (__main__) :
#     - Démonstration simple :
#         * résout un cube “déjà résolu” avec kociemba
#         * tente ensuite la résolution via Two-Phase (si installé)
#
#  Notes :
#     - Ce module ne fait aucune validation avancée du cubestring : il suppose que
#       l’appelant fournit une chaîne valide (54 chars, URFDLB, comptages corrects).
#     - L’import lazy de RubikTwoPhase est volontaire pour garder le pipeline rapide
#       et portable.
# ============================================================================


try:
    import kociemba
except ImportError:
    kociemba = None


# ---------------------------------------------------------------------------
# Fonction solve_with_kociemba
# ---------------------------------------------------------------------------
def solve_with_kociemba(cube_state: str) -> str:
    """
    Résout le cube avec l'algorithme de Kociemba standard.
    :param cube_state: chaîne de 54 caractères représentant l'état du cube
    :return: une séquence de mouvements en notation Singmaster
    """
    if not kociemba:
        raise ImportError("Le module 'kociemba' n'est pas installé.")
    return kociemba.solve(cube_state)


# ---------------------------------------------------------------------------
# Fonction solve_with_kociemba_2_state
# ---------------------------------------------------------------------------
def solve_with_kociemba_2_state(cube_state: str) -> str:
    """
    Résout le cube avec la variante Kociemba Two-Phase (RubikTwoPhase).
    ⚠️  Le module n'est pas importé automatiquement au démarrage,
       il est chargé dynamiquement ici, uniquement si nécessaire.
    """
    try:
        import twophase.solver as sv
    except ImportError:
        raise ImportError(
            "Le module 'RubikTwoPhase' (twophase) n'est pas disponible "
            "et ne sera pas chargé automatiquement. "
            "Installe-le avec 'pip install RubikTwoPhase' si tu veux l’utiliser."
        )

    # Paramètres : profondeur maximale = 21, timeout = 5 secondes
    return sv.solve(cube_state, 21, 5.0)


# ---------------------------------------------------------------------------
# Fonction solve_cube
# ---------------------------------------------------------------------------
def solve_cube(cube_state: str, method: str = "kociemba") -> str:
    """
    Fonction générique qui choisit quel solveur utiliser.
    :param cube_state: état du cube en string (URFDLB)
    :param method: 'kociemba' (par défaut) ou 'k2' (Two-Phase)
    :return: solution en notation Singmaster
    """
    if method == "kociemba":
        return solve_with_kociemba(cube_state)
    elif method == "k2":
        return solve_with_kociemba_2_state(cube_state)
    else:
        raise ValueError(f"Solveur '{method}' non supporté pour le moment.")


# ---------------------------------------------------------------------------
# Mode exécution directe (debug manuel)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Exemple d'utilisation
    cube = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    print("État initial :", cube)
    print("\nMéthode : Kociemba standard")
    try:
        solution = solve_cube(cube, method="kociemba")
        print("Solution trouvée :", solution)
    except Exception as e:
        print("Erreur Kociemba :", e)

    print("\nMéthode : Two-Phase (si dispo)")
    try:
        solution2 = solve_cube(cube, method="k2")
        print("Solution trouvée (Two-Phase) :", solution2)
    except Exception as e:
        print("Erreur Two-Phase :", e)
