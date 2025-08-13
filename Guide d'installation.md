# Guide d'installation

Ce document décrit plusieurs méthodes d'installation et de déploiement de l'application **DoublonsIDPP** (GUI PyQt5) selon les besoins : usage ponctuel, environnement isolé, création d'un exécutable PyInstaller et intégration au menu des applications (fichier `.desktop`).

---

## 1. Prérequis généraux

| Composant                  | Version conseillée        | Vérification               | Installation (Ubuntu/Debian)       |
| -------------------------- | ------------------------- | -------------------------- | ---------------------------------- |
| OS                         | Ubuntu 22.04+ / 24.04 LTS | `lsb_release -ds`          | -                                  |
| Python                     | 3.10+ (3.12 OK)           | `python3 --version`        | `sudo apt install python3`         |
| Pip                        | À jour                    | `python3 -m pip --version` | `sudo apt install python3-pip`     |
| Outils build (pour wheels) | build-essential           | `dpkg -l build-essential`  | `sudo apt install build-essential` |
| Git (si clonage)           | 2.x                       | `git --version`            | `sudo apt install git`             |

Dépendances Python (installées via `requirements.txt`) : `numpy`, `pandas`, `PyQt5`.

---

## 2. Récupération du code

### Clonage via Git (recommandé)

```bash
git clone https://github.com/ybdn/DoublonsIDPP.git
cd DoublonsIDPP
```

### Méthode archive (sans Git)

1. Télécharger l'archive ZIP depuis GitHub.
2. Extraire le dossier.
3. Ouvrir un terminal dans le dossier extrait.

---

## 3. Méthode rapide (installation utilisateur directe)

Installation locale des dépendances dans l'espace utilisateur :

```bash
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements.txt
```

Lancement :

```bash
./run_gui.sh
# ou
python3 gui_doublons_idpp.py
```

---

## 4. Utilisation avec environnement virtuel (propre et reproductible)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python gui_doublons_idpp.py
```

Sortir de l'environnement : `deactivate`.

Pour usage ultérieur :

```bash
source .venv/bin/activate
python gui_doublons_idpp.py
```

---

## 5. Création d'un exécutable autonome avec PyInstaller

### 5.1 Installation de PyInstaller

Dans l'environnement (virtuel de préférence) :

```bash
pip install pyinstaller
```

### 5.2 Construction

```bash
pyinstaller \
  --name DoublonsIDPP \
  --onefile \
  --windowed \
  --icon icons/icon.png \
  gui_doublons_idpp.py
```

Résultat principal : `dist/DoublonsIDPP`.

### 5.3 Test rapide

```bash
./dist/DoublonsIDPP
```

### 5.4 Réduction de taille (optionnel)

- Supprimer caches : `find dist/DoublonsIDPP -name "__pycache__" -type d -exec rm -rf {} +`
- Ajouter `--strip` (Linux) pour enlever symboles de debug.

### 5.5 Spécialisation avec un fichier .spec

Lancer une première fois PyInstaller (génère `DoublonsIDPP.spec`), puis éditer pour rajouter éventuellement des ressources (fonts, etc.). Ensuite :

```bash
pyinstaller DoublonsIDPP.spec
```

---

## 6. Installation système de l'exécutable

Supposons que vous souhaitiez installer dans `/opt/doublons-idpp/` et exposer un lanceur dans le PATH.

```bash
sudo mkdir -p /opt/doublons-idpp
sudo cp dist/DoublonsIDPP /opt/doublons-idpp/doublons-idpp
sudo chmod 755 /opt/doublons-idpp/doublons-idpp

# Wrapper symbolique dans /usr/local/bin
sudo ln -sf /opt/doublons-idpp/doublons-idpp /usr/local/bin/doublons-idpp
```

Vérification :

```bash
doublons-idpp --help 2>/dev/null || echo "Exécutable accessible (même sans --help explicite)"
```

---

## 7. Icône et intégration graphique (.desktop)

### 7.1 Installation de l'icône

Taille recommandée : 128x128 ou 256x256.

```bash
sudo install -Dm644 icons/icon.png /usr/share/icons/hicolor/128x128/apps/doublons-idpp.png
# (Optionnel) autres tailles si disponibles
sudo gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
```

### 7.2 Fichier .desktop (mode système)

Créer `/usr/share/applications/doublons-idpp.desktop` :

```ini
[Desktop Entry]
Type=Application
Version=1.5
Name=Doublons IDPP
GenericName=Détection de doublons
Comment=Interface graphique pour le traitement des doublons de signalisations
Comment[en]=GUI for duplicate reports processing
Exec=doublons-idpp %F
TryExec=doublons-idpp
Icon=doublons-idpp
Terminal=false
Categories=Office;Development;
StartupNotify=true
```

Puis :

```bash
sudo update-desktop-database /usr/share/applications 2>/dev/null || true
```

### 7.3 Installation utilisateur (sans sudo)

```bash
mkdir -p ~/.local/share/applications ~/.local/share/icons/hicolor/128x128/apps
cp icons/icon.png ~/.local/share/icons/hicolor/128x128/apps/doublons-idpp.png
cp DoublonsIDPP.desktop ~/.local/share/applications/doublons-idpp.desktop
sed -i "s#^Exec=.*#Exec=$HOME/.local/bin/doublons-idpp#" ~/.local/share/applications/doublons-idpp.desktop || true
sed -i "s#^Icon=.*#Icon=doublons-idpp#" ~/.local/share/applications/doublons-idpp.desktop || true
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```

Assurez-vous que l'exécutable est accessible : placez-le dans `~/.local/bin/` (et que ce dossier est dans votre PATH).

---

## 8. Mises à jour

### Depuis Git

```bash
cd DoublonsIDPP
git pull
pip install -r requirements.txt --user --upgrade
```

Si vous utilisez PyInstaller, reconstruisez l'exécutable.

### Remplacement exécutable système

```bash
sudo cp dist/DoublonsIDPP /opt/doublons-idpp/doublons-idpp
```

---

## 9. Désinstallation

Mode utilisateur :

```bash
rm -f ~/.local/share/applications/doublons-idpp.desktop
rm -f ~/.local/share/icons/hicolor/128x128/apps/doublons-idpp.png
rm -f ~/.local/bin/doublons-idpp
```

Mode système :

```bash
sudo rm -f /usr/share/applications/doublons-idpp.desktop
sudo rm -f /usr/share/icons/hicolor/128x128/apps/doublons-idpp.png
sudo rm -f /usr/local/bin/doublons-idpp
sudo rm -rf /opt/doublons-idpp
sudo update-desktop-database /usr/share/applications 2>/dev/null || true
```

---

## 10. Vérifications de bon fonctionnement

| Vérification         | Commande / Action              | Résultat attendu            |
| -------------------- | ------------------------------ | --------------------------- |
| Lancement direct     | `python3 gui_doublons_idpp.py` | Fenêtre GUI affichée        |
| Lancement exécutable | `./dist/DoublonsIDPP`          | GUI OK                      |
| Icône                | Ouvrir menu applications       | Icône personnalisée visible |
| Chemins export       | Sélection dans l'UI            | Fichiers rapports générés   |

---

## 11. Dépannage rapide

| Problème                                  | Cause probable                            | Solution                                                      |
| ----------------------------------------- | ----------------------------------------- | ------------------------------------------------------------- |
| GUI ne se lance pas (ModuleNotFoundError) | Dépendances manquantes                    | Réinstaller `pip install -r requirements.txt`                 |
| Police warnings Qt                        | Police JetBrains Mono absente             | Ignorer (optionnel) ou ajouter dans dossier `fonts/`          |
| Pas d'icône menu                          | Chemin icône / cache non rafraîchi        | Vérifier `Icon=`, exécuter `gtk-update-icon-cache`            |
| Fenêtre lente au démarrage                | Environnement réseau/cloud (Google Drive) | Copier projet localement (ex: `~/Applications/doublonsidpp/`) |
| Erreur d'accès export                     | Permissions dossier                       | Choisir un dossier utilisateur accessible                     |

Test dépendances Python :

```bash
python3 -c "import PyQt5.QtWidgets; import pandas; import numpy; print('Dépendances OK')"
```

---

## 12. Bonnes pratiques de déploiement interne

- Éviter l'exécution depuis un dossier synchronisé (latence / locks).
- Versionner un fichier CHANGELOG pour suivi interne.
- Signer les exécutables si politique sécurité interne stricte.
- Automatiser la construction via un script CI (GitHub Actions) produisant l'exécutable + artefacts.
- Conserver un hash (SHA256) de l'exécutable distribué.

---

## 13. Exemple de script d'installation (système) automatisé

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=DoublonsIDPP
INSTALL_DIR=/opt/doublons-idpp
BIN_LINK=/usr/local/bin/doublons-idpp
DESKTOP_FILE=/usr/share/applications/doublons-idpp.desktop
ICON_SRC=icons/icon.png
ICON_DST=/usr/share/icons/hicolor/128x128/apps/doublons-idpp.png

# 1. Build
pyinstaller --name "$APP" --onefile --windowed --icon "$ICON_SRC" gui_doublons_idpp.py

# 2. Install binary
sudo mkdir -p "$INSTALL_DIR"
sudo cp dist/$APP "$INSTALL_DIR/doublons-idpp"
sudo chmod 755 "$INSTALL_DIR/doublons-idpp"

# 3. Symlink
sudo ln -sf "$INSTALL_DIR/doublons-idpp" "$BIN_LINK"

# 4. Icon
sudo install -Dm644 "$ICON_SRC" "$ICON_DST"

# 5. Desktop entry
sudo tee "$DESKTOP_FILE" >/dev/null <<'EOF'
[Desktop Entry]
Type=Application
Version=1.5
Name=Doublons IDPP
GenericName=Détection de doublons
Comment=Interface graphique pour le traitement des doublons de signalisations
Exec=doublons-idpp %F
TryExec=doublons-idpp
Icon=doublons-idpp
Terminal=false
Categories=Office;Development;
StartupNotify=true
EOF

sudo update-desktop-database /usr/share/applications 2>/dev/null || true

echo "Installation terminée. Lancez: doublons-idpp"
```

---

## 14. Sécurité et conformité

- Vérifier l'intégrité des CSV entrants (pas de formules / injections si ré-ouverture dans Excel).
- Les chemins d'exports doivent respecter les politiques internes (pas de partage non autorisé).
- Journalisation : les logs sont dans la fenêtre; si besoin d'archivage, rediriger la sortie standard (`./dist/DoublonsIDPP > log.txt 2>&1`).

---

## 15. Questions fréquentes (FAQ)

Q: Puis-je lancer depuis Windows ?  
R: Le code Python (PyQt5) est portable. Il faudra reconstruire un exécutable (PyInstaller sous Windows) ou installer Python + dépendances.

Q: Faut-il conserver `run_gui.sh` après création de l'exécutable ?  
R: Non, seulement utile pour exécution directe du code source.

Q: Comment changer le nom affiché dans le menu ?  
R: Modifier `Name=` et éventuellement `GenericName=` dans le `.desktop` puis rafraîchir la base.

---

## 16. Support

Pour toute question : PJGN / FAED (Développeur : Yoann BAUDRIN). Distribution interne—ne pas diffuser sans autorisation.

---

Fin du guide.
