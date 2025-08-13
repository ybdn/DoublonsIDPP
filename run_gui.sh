#!/bin/bash
# Lanceur pour l'interface graphique DoublonsIDPP

# Définir le répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Vérifier si Python3 est installé
if ! command -v python3 &> /dev/null; then
    echo "Erreur: Python3 n'est pas installé."
    echo "Veuillez installer Python3 avec: sudo apt install python3"
    exit 1
fi

# Vérifier si pip3 est installé
if ! command -v pip3 &> /dev/null; then
    echo "Erreur: pip3 n'est pas installé."
    echo "Veuillez installer pip3 avec: sudo apt install python3-pip"
    exit 1
fi

# Installer les dépendances si nécessaire
if [ -f "requirements.txt" ]; then
    echo "Vérification des dépendances..."
    pip3 install -r requirements.txt --user --quiet
fi

# Lancer l'interface graphique
echo "Lancement de l'interface graphique DoublonsIDPP..."
python3 gui_doublons_idpp.py