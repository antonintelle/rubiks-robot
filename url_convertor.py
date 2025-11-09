import urllib.parse
import re


def clean_solution(solution: str, method: str) -> str:
    """
    Nettoie la sortie selon la méthode.
    - k2 (RubikTwoPhase) : conserve U1/U2/U3 etc.
    - kociemba : conserve U, U', U2 etc.
    """
    moves = solution.split()

    if method == "k2":
        # Format RubikTwoPhase (U1, U2, U3)
        valid_moves = [m for m in moves if re.match(r"^[URFDLB][123]$", m)]
    else:
        # Format Singmaster (U, U', U2)
        valid_moves = [m for m in moves if re.match(r"^[URFDLB](2|'|)?$", m)]

    return " ".join(valid_moves)


def convert_twophase_to_singmaster(solution: str) -> str:
    """
    Convertit la sortie RubikTwoPhase (U1, U2, U3, ...) en notation Singmaster standard
    """
    mapping = {
        "1": "",   # quart de tour horaire
        "2": "2",  # demi-tour
        "3": "'"   # quart de tour antihoraire
    }

    converted = []
    for move in solution.split():
        face = move[0]      # U, R, F, D, L, B
        suffix = move[1:]   # 1, 2, 3
        converted.append(face + mapping.get(suffix, ""))
    return " ".join(converted)


def convert_to_url(solution: str, method: str = "kociemba", site: str = "alg", cubestring: str = None) -> str:
    """
    Convertit une solution en URL vers différents visualiseurs.
    
    :param solution: chaîne de mouvements
    :param method: "kociemba" ou "k2" (RubikTwoPhase)
    :param site: "alg", "twizzle", ou "visualcube"
    :param cubestring: état complet du cube (utile pour visualcube)
    :return: URL
    """
    # 1. Nettoyage selon méthode
    solution_clean = clean_solution(solution, method)
    print("Solution nettoyée :", solution_clean)

    # 2. Conversion éventuelle
    if method == "k2":
        converted = convert_twophase_to_singmaster(solution_clean)
    else:
        converted = solution_clean
    print("Convertie :", converted)

    # 3. Génération d’URL
    if site == "alg":
        encoded = urllib.parse.quote(converted, safe="")
        return f"https://alg.cubing.net/?alg={encoded}&type=alg"

    elif site == "twizzle":
        encoded = urllib.parse.quote(converted, safe="")
        if cubestring:
            setup = urllib.parse.quote(cubestring, safe="")
            return f"https://alpha.twizzle.net/edit/?setup-alg={setup}&alg={encoded}"
        else:
            return f"https://alpha.twizzle.net/edit/?alg={encoded}"

    elif site == "visualcube":
        if not cubestring:
            raise ValueError("visualcube nécessite un cubestring valide")
        encoded = urllib.parse.quote(cubestring, safe="")
        return f"https://cube.crider.co.uk/visualcube.php?fmt=png&size=400&pzl=3&case={encoded}"

    else:
        raise ValueError(f"Site '{site}' non supporté.")
