# 📺 Intégration de l'Écran TFT au Pipeline Robot

*Consignes pour intégrer l'écran

------------------------------------------------------------------------

## 🎯 Objectif

Faire de l'écran (`Ecran/`) le **main du robot**.

Le pipeline existant :

capture → detection → conversion → solve → execute

ne doit **pas être modifié**.

L'écran reçoit les événements de progression via un listener RBX et
affiche :

-   **line1** : texte court (ex: `20% capture`)
-   **line2** : message (ex: `Capturing U (1/6)`)
-   **pct** : progression (0.0 → 1.0)

------------------------------------------------------------------------

# 🔐 1) Lancement de l'écran (IMPORTANT)

Le robot utilise :

-   GPIO\
-   NeoPixel\
-   SPI

➡️ Le programme doit être lancé avec **sudo**.

Créer un script :

## `3_main_ecran.sh`

``` bash
#!/bin/bash
VENV_PY="$HOME/rubik-env/bin/python3"
cd "$HOME/rubiks-robot" || exit 1
sudo -E "$VENV_PY" -m Ecran.main
```

Puis exécuter :

``` bash
chmod +x 3_main_ecran.sh
./3_main_ecran.sh
```

------------------------------------------------------------------------

# ⚙ 2) Modifications dans `Ecran/main.py`

## Ajouter en haut du fichier :

``` python
import threading

from rbx_ui_state_store import RBXScreenStateStore
from rbx_ui_listener import make_rbx_ui_listener
from main_robot_solveur import main as robot_main
```

## Dans `RubikGUI.__init__` :

``` python
self.rbx_store = RBXScreenStateStore()
self.rbx_listener = make_rbx_ui_listener(self.rbx_store)
```

------------------------------------------------------------------------

# ▶ 3) Ajouter la fonction `start_robot`

``` python
def start_robot(self, do_execute=True):

    def _run():
        robot_main(
            tmp_folder="tmp",
            debug="text",
            do_solve=True,
            do_execute=do_execute,
            extra_listeners=[self.rbx_listener],
        )

    threading.Thread(target=_run, daemon=True).start()
```

------------------------------------------------------------------------

# 📊 4) Écran Pipeline / Progression

``` python
st = self.app.rbx_store.get()
```

Afficher :

-   `st.line1`
-   `st.line2`
-   barre basée sur `st.pct`

Exemple :

``` python
filled = int(bar_width * st.pct)
```

------------------------------------------------------------------------

# 🟢 5) Bouton START

``` python
self.app.set_screen("pipeline")
self.app.start_robot(do_execute=True)
```

------------------------------------------------------------------------

# ✅ Résultat attendu

-   L'écran démarre sur le menu\
-   Appui sur START → passage à l'écran pipeline\
-   Le pipeline tourne dans un thread\
-   Affichage temps réel (% + message + barre)

------------------------------------------------------------------------

# 🛠 Dépannage

**Import error**\
→ Lancer avec : `python -m Ecran.main`

**Rien ne s'affiche**\
→ Vérifier que `extra_listeners=[self.rbx_listener]` est bien passé

**Erreur hardware**\
→ Vérifier lancement avec `sudo -E`
