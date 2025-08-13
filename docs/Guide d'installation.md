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


## 4. Création d'un exécutable autonome avec PyInstaller

### 4.1 Installation de PyInstaller

```bash
pip install pyinstaller
```

### 4.2 Construction

```bash
pyinstaller --onefile --name="DoublonsIDPP" --icon="icon.png" gui_doublons_idpp.py
```

Résultat principal : `dist/DoublonsIDPP`.

