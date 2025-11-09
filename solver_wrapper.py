# solver_wrapper.py
#
# RÉSUMÉ : Wrapper générique pour différents solveurs de Rubik's Cube.
# Actuellement supporte :
#    - kociemba (pip install kociemba)
#    - Kociemba two phase (pip install RubikTwoPhase)
#
# Objectif :
#    Fournir une interface unifiée pour différents solveurs de cube,
#    avec sélection dynamique de l’algorithme à employer.
#
# Important :
#    → Dans cette version, le module "twophase" n’est PAS importé au démarrage,
#      pour éviter les temps de chargement ou erreurs sur des systèmes sans RubikTwoPhase.
#      Il n’est chargé qu’à la demande, si l’utilisateur choisit la méthode "k2".
#
# ============================================================================

# ---------------------------------------------------------------------------
# Import du solveur standard Kociemba
# (chargé au démarrage car léger et souvent installé)
# ---------------------------------------------------------------------------
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
