# main_robot_solveur.py 
# Création d'une instance du robot puis lancement (run)
#

import time

#from types_shared import FacesDict
from colorama import init, Fore, Style
# Initialisation des couleurs (Windows / Linux / Mac)
init(autoreset=True)

print(Fore.CYAN + "\n" + "=" * 50)
print(Fore.YELLOW + Style.BRIGHT + "SYSTÈME ROBOTIQUE DE RECONNAISSANCE RUBIK'S CUBE")
print(Fore.CYAN + "=" * 50 + Style.RESET_ALL)

from robot_solver import RobotCubeSolver

start_time = time.perf_counter()

solver = RobotCubeSolver(image_folder="tmp", debug="text")
cubestring = solver.run(do_solve=True,do_execute=True)  # renvoie la chaîne 54 URFDLB
#print(cubestring)

end_time = time.perf_counter()
elapsed = end_time - start_time

print(Fore.CYAN + "\n" + "="*60)
print(Fore.YELLOW + Style.BRIGHT + f"FINI en {elapsed:.2f} secondes" + Style.RESET_ALL)
print(Fore.CYAN + "="*60)

