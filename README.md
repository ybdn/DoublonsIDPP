# DoublonsIDPP

Script de tri des doublons IDPP avec interface graphique PyQt

## Description

DoublonsIDPP est un outil développé pour le Pôle Judiciaire de la Gendarmerie Nationale (PJGN) permettant d'analyser et de traiter les doublons dans les fichiers de signalisations. Il propose maintenant une interface graphique moderne en plus de l'interface en ligne de commande.

## Fonctionnalités

- **Interface graphique PyQt** : Interface simple et épurée pour une utilisation facilitée
- **Détection intelligente des doublons** : Algorithme sophistiqué basé sur 3 critères
- **Rapports détaillés** : Génération automatique de rapports d'analyse
- **Compatibilité Ubuntu** : Testé et optimisé pour Ubuntu 24.04 LTS

## Installation sous Ubuntu

### Prérequis

```bash
# Mettre à jour le système
sudo apt update

# Installer Python3 et pip (généralement déjà installés)
sudo apt install python3 python3-pip

# Installer les dépendances système pour PyQt5
sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets
```

### Installation des dépendances Python

```bash
# Cloner le dépôt
git clone https://github.com/ybdn/DoublonsIDPP.git
cd DoublonsIDPP

# Installer les dépendances Python
pip3 install -r requirements.txt --user
```

### Installation optionnelle sur le bureau (Ubuntu)

Pour ajouter l'application au menu des applications :

```bash
# Copier le fichier .desktop vers les applications
cp DoublonsIDPP.desktop ~/.local/share/applications/

# Mettre à jour la base de données des applications
update-desktop-database ~/.local/share/applications/

# Rendre le lanceur exécutable
chmod +x ~/.local/share/applications/DoublonsIDPP.desktop
```

## Utilisation

### Interface graphique (recommandée)

1. **Lancement simple :**
   ```bash
   ./run_gui.sh
   ```

2. **Lancement manuel :**
   ```bash
   python3 gui_doublons_idpp.py
   ```

3. **Utilisation de l'interface :**
   - Sélectionnez votre fichier CSV dans la section 1
   - Choisissez le dossier de destination des rapports dans la section 2
   - Cliquez sur "Lancer l'analyse des doublons" dans la section 3
   - Suivez la progression dans le journal d'activité

### Interface en ligne de commande

```bash
python3 script_doublons_idpp.py
```

## Format des fichiers d'entrée

Le fichier CSV doit contenir les colonnes suivantes :
- `IDENTIFIANT_GASPARD` : Identifiant IDPP
- `NUMERO_PERSONNE` : Numéro de personne
- `NUMERO_SIGNALISATION` : Numéro de signalisation
- `NOM` : Nom de la personne
- `PRENOM` : Prénom de la personne
- `DATE_NAISSANCE_MIN` : Date de naissance
- `DATE_CREATION_FAED` : Date de création
- `NUM_PROCEDURE` : Numéro de procédure (UNA)
- `NUMERO_CLICHE` : Numéro de cliché photo

## Fichiers de sortie

L'outil génère automatiquement :

1. **Rapport des signalisations conservées** : Détail des signalisations à garder
2. **Rapport des signalisations à supprimer** : Détail des doublons identifiés
3. **Liste des numéros à supprimer** : Fichier simplifié pour import système
4. **Résumé HTML** : Rapport de synthèse avec statistiques
5. **Résumé texte** : Version texte du rapport de synthèse

## Algorithme de détection

L'outil applique 3 règles hiérarchiques :

1. **Tri 1** : Correspondance numéro signalisation/numéro personne
2. **Tri 2** : Cohérence entre UNA et IDPP
3. **Tri 3** : Critères temporels et présence de photos

## Dépannage

### Problèmes d'affichage GUI

Si l'interface graphique ne s'affiche pas :

```bash
# Installer les dépendances d'affichage
sudo apt install python3-pyqt5.qtwidgets python3-pyqt5.qtcore python3-pyqt5.qtgui

# Vérifier l'environnement graphique
echo $DISPLAY
```

### Erreurs de dépendances

```bash
# Réinstaller les dépendances
pip3 install --upgrade -r requirements.txt --user

# Vérifier les installations
python3 -c "import PyQt5.QtWidgets; import pandas; import numpy; print('Toutes les dépendances sont OK')"
```

## Support

Pour toute question ou problème, contactez le développeur :
- **Développeur** : GND Yoann BAUDRIN
- **Organisation** : Pôle Judiciaire de la Gendarmerie Nationale (PJGN)
- **Département** : Fichier Automatisé des Empreintes Digitales (FAED)

## Licence

Tous droits réservés © 2025 PJGN/FAED
