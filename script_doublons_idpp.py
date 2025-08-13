#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traitement des Doublons IDPP - Module principal

Copyright (c) 2025 GND Yoann BAUDRIN - Pôle Judiciaire de la Gendarmerie Nationale (PJGN)
Département du Fichier Automatisé des Empreintes Digitales (FAED)

TOUS DROITS RÉSERVÉS
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import shutil

# Définir les chemins des dossiers
script_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(script_path)
BACKUPS_DIR = os.path.join(root_path, "data", "backups")
EXPORTS_BASE_DIR = os.path.join(root_path, "data", "exports")  # Répertoire par défaut

def lire_fichier_csv(chemin_fichier):
    """
    Lit le fichier CSV des signalisations.
    """
    try:
        # Lecture du fichier CSV
        df = pd.read_csv(chemin_fichier, sep=',', encoding='utf-8')
        print(f"Fichier chargé avec succès : {len(df)} signalisations trouvées.")
        return df
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {e}")
        return None

def regrouper_doublons(df):
    """
    Regroupe les signalisations qui respectent les 3 critères de doublon:
    - Même identifiant GASPARD (IDPP)
    - Même numéro de personne
    - Même identité (nom, prénom, date de naissance)
    
    Retourne un dictionnaire où la clé est un tuple (identifiant_gaspard, numero_personne, identité)
    et la valeur est un DataFrame contenant les signalisations correspondantes.
    """
    groupes = {}
    
    # S'assurer que les colonnes nécessaires existent
    colonnes_requises = ['IDENTIFIANT_GASPARD', 'NUMERO_PERSONNE', 'NOM', 'PRENOM', 'DATE_NAISSANCE_MIN']
    colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]
    
    if colonnes_manquantes:
        print(f"Erreur: Les colonnes suivantes sont manquantes: {', '.join(colonnes_manquantes)}")
        return groupes
    
    # Normalisation des données pour la comparaison
    # Convertir les valeurs numériques en chaînes pour éviter les problèmes de type dans la clé de groupe
    df['IDENTIFIANT_GASPARD_NORM'] = df['IDENTIFIANT_GASPARD'].astype(str)
    df['NUMERO_PERSONNE_NORM'] = df['NUMERO_PERSONNE'].astype(str)
    
    # Normaliser les noms et prénoms (majuscules, suppression des espaces superflus)
    df['NOM_NORM'] = df['NOM'].astype(str).str.upper().str.strip()
    df['PRENOM_NORM'] = df['PRENOM'].astype(str).str.upper().str.strip()
    df['DATE_NAISSANCE_NORM'] = df['DATE_NAISSANCE_MIN'].astype(str).str.strip()
    
    # Création d'une clé composite pour le regroupement
    df['cle_groupe'] = df.apply(
        lambda row: (
            row['IDENTIFIANT_GASPARD_NORM'],
            row['NUMERO_PERSONNE_NORM'],
            (row['NOM_NORM'], row['PRENOM_NORM'], row['DATE_NAISSANCE_NORM'])
        ), 
        axis=1
    )
    
    # Groupement par clé composite
    groupes_df = df.groupby('cle_groupe')
    
    # Filtrer pour ne garder que les groupes avec plus d'une signalisation (doublons)
    for nom_groupe, groupe in groupes_df:
        if len(groupe) > 1:
            groupes[nom_groupe] = groupe
    
    print(f"{len(groupes)} groupes de doublons identifiés.")
    return groupes

def appliquer_tri_1(groupe):
    """
    Tri 1 : Correspondance numéro signalisation/numéro personne
    Si NUMERO_SIGNALISATION = NUMERO_PERSONNE pour une ou plusieurs signalisations:
    - Conserver cette/ces signalisation(s)
    - Marquer toutes les autres du groupe comme "à supprimer"
    """
    # Initialiser la colonne A_SUPPRIMER à True (supposons tout supprimer par défaut)
    groupe['A_SUPPRIMER'] = True
    
    # Identifier les signalisations où NUMERO_SIGNALISATION = NUMERO_PERSONNE
    correspondance = groupe['NUMERO_SIGNALISATION'] == groupe['NUMERO_PERSONNE']
    
    # Si au moins une signalisation respecte ce critère
    if correspondance.any():
        # Marquer ces signalisations comme "à conserver"
        groupe.loc[correspondance, 'A_SUPPRIMER'] = False
        # Décision prise, retourner le groupe
        groupe['REGLE_APPLIQUEE'] = "Tri 1: Correspondance exacte entre numéro de signalisation et numéro de personne"
        groupe.loc[correspondance, 'DETAIL_REGLE'] = "La signalisation est conservée car son numéro de signalisation est identique à son numéro de personne."
        groupe.loc[~correspondance, 'DETAIL_REGLE'] = "Une autre signalisation a créé le numéro de personne."
        return groupe, True
    
    # Si aucune correspondance, marquer toutes comme "à examiner" (None pour le moment)
    groupe['A_SUPPRIMER'] = None
    return groupe, False

def extraire_una_concatane(una):
    """
    Extrait l'UNA concaténé (sans les '/') à partir du NUM_PROCEDURE.
    Exemple: "00116/00149/2024" → "00116001492024"
    """
    if pd.isna(una) or not isinstance(una, str):
        return ""
    
    # Supprimer les "/" et concaténer
    return una.replace('/', '')

def appliquer_tri_2(groupe):
    """
    Tri 2 : Cohérence entre UNA et IDPP
    Si le Tri 1 n'a pas résolu le doublon:
    - Pour chaque signalisation, extraire l'UNA (NUM_PROCEDURE)
    - Supprimer les "/" de l'UNA pour concaténer les numéros
    - Vérifier si cet UNA concaténé est contenu dans l'IDPP
    - Si certaines signalisations ont leur UNA dans leur IDPP et d'autres non,
      conserver celles où l'UNA est contenu dans l'IDPP
    """
    # Vérifier si le tri est nécessaire (si A_SUPPRIMER contient None)
    if not (groupe['A_SUPPRIMER'].isna().any()):
        return groupe, True
    
    # Extraire UNA concaténé pour chaque signalisation
    groupe['UNA_CONCATANE'] = groupe['NUM_PROCEDURE'].apply(extraire_una_concatane)
    
    # Vérifier si l'UNA concaténé est contenu dans l'IDPP
    groupe['UNA_DANS_IDPP'] = groupe.apply(
        lambda row: row['UNA_CONCATANE'] in str(row['IDENTIFIANT_GASPARD']) if row['UNA_CONCATANE'] else False,
        axis=1
    )
    
    # Si certaines signalisations ont leur UNA dans l'IDPP et d'autres non
    if groupe['UNA_DANS_IDPP'].any() and not groupe['UNA_DANS_IDPP'].all():
        # Marquer à conserver celles dont l'UNA est dans l'IDPP
        groupe.loc[groupe['UNA_DANS_IDPP'], 'A_SUPPRIMER'] = False
        # Marquer à supprimer les autres
        groupe.loc[~groupe['UNA_DANS_IDPP'], 'A_SUPPRIMER'] = True
        groupe['REGLE_APPLIQUEE'] = "Tri 2: Cohérence entre numéro de procédure (UNA) et identifiant GASPARD (IDPP)"
        groupe.loc[groupe['UNA_DANS_IDPP'], 'DETAIL_REGLE'] = "La signalisation est conservée car son numéro de procédure est inclus dans son identifiant GASPARD."
        groupe.loc[~groupe['UNA_DANS_IDPP'], 'DETAIL_REGLE'] = "L'UNA ne correspond pas à l'IDPP."
        return groupe, True
    
    # Si toutes ont ou n'ont pas de photo, continuer au tri suivant
    return groupe, False

def convertir_date(date_str):
    """
    Convertit une date au format JJ/MM/AA ou JJ/MM/AAAA en objet datetime.
    Gère également les formats alternatifs potentiels.
    """
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    
    # Suppression des espaces supplémentaires
    date_str = date_str.strip()
    
    # Liste des formats à essayer
    formats = [
        "%d/%m/%y",    # Format JJ/MM/AA
        "%d/%m/%Y",    # Format JJ/MM/AAAA
        "%Y-%m-%d",    # Format ISO
        "%d-%m-%Y",    # Format JJ-MM-AAAA
        "%d-%m-%y",    # Format JJ-MM-AA
        "%d.%m.%Y",    # Format JJ.MM.AAAA
        "%d.%m.%y",    # Format JJ.MM.AA
        "%Y/%m/%d",    # Format AAAA/MM/JJ
        "%Y%m%d",      # Format AAAAMMJJ (sans séparateurs)
        "%d%m%Y",      # Format JJMMAAAA (sans séparateurs)
        "%d%m%y"       # Format JJMMAA (sans séparateurs)
    ]
    
    # Essayer chaque format
    for format_date in formats:
        try:
            return datetime.strptime(date_str, format_date)
        except ValueError:
            continue
    
    # Si aucun format standard ne fonctionne, essayer des approches plus spécifiques
    
    # Vérifier si la chaîne contient uniquement des chiffres (format potentiellement numérique)
    if date_str.isdigit():
        # Pour les formats numériques comme '20220131'
        if len(date_str) == 8:
            try:
                annee = int(date_str[:4])
                mois = int(date_str[4:6])
                jour = int(date_str[6:8])
                if 1 <= mois <= 12 and 1 <= jour <= 31:  # Validation basique
                    return datetime(annee, mois, jour)
            except ValueError:
                pass
    
    # Si aucun format ne fonctionne, on retourne None et on log l'erreur
    print(f"Erreur de conversion de date pour '{date_str}', format non reconnu")
    return None

def appliquer_tri_3(groupe):
    """
    Tri 3 : Critères temporels et présence de photos
    Si le Tri 2 n'a pas résolu le doublon et que les signalisations ont le même UNA:
    - Si dates de création différentes: conserver la signalisation la plus ANCIENNE
    - Si dates identiques: conserver les signalisations avec photo (NUMERO_CLICHE non null)
    - Si toutes ont ou n'ont pas de photo: conserver celle avec le plus petit NUMERO_SIGNALISATION
      (plus le numéro de signalisation est petit, plus la signalisation est ancienne)
    """
    # Vérifier si le tri est nécessaire
    if not (groupe['A_SUPPRIMER'].isna().any()):
        return groupe, True
    
    # Debug: Afficher le nombre de signalisations dans le groupe
    num_signalisations = len(groupe)
    id_groupe = groupe['ID_GROUPE'].iloc[0] if 'ID_GROUPE' in groupe.columns else "Inconnu"
    print(f"\nDébut Tri 3 pour groupe {id_groupe} avec {num_signalisations} signalisations")
    
    # Afficher les dates de création originales pour debug
    print("Dates originales:")
    for index, row in groupe.iterrows():
        num_sig = row['NUMERO_SIGNALISATION']
        date_orig = row['DATE_CREATION_FAED']
        print(f"  - Signalisation {num_sig}: Date originale = '{date_orig}'")
    
    # Convertir les dates de création en format datetime
    groupe['DATE_CREATION_FAED_DT'] = groupe['DATE_CREATION_FAED'].apply(convertir_date)
    
    # Afficher les dates après conversion pour debug
    print("Dates après conversion:")
    for index, row in groupe.iterrows():
        num_sig = row['NUMERO_SIGNALISATION']
        date_conv = row['DATE_CREATION_FAED_DT']
        date_str = date_conv.strftime("%d/%m/%Y") if date_conv else "NON CONVERTIE"
        print(f"  - Signalisation {num_sig}: Date convertie = {date_str}")
    
    # 3.1 Vérifier si elles ont des dates de création différentes
    dates_uniques = groupe['DATE_CREATION_FAED_DT'].dropna().unique()
    
    print(f"Nombre de dates uniques: {len(dates_uniques)}")
    
    if len(dates_uniques) > 1:
        # Conserver la signalisation la plus ancienne
        date_min = min(dates_uniques)
        #date_min_str = date_min.strftime("%d/%m/%Y") if date_min else "inconnue"
        # Ligne corrigée
        date_min_str = pd.Timestamp(date_min).strftime("%d/%m/%Y") if pd.notna(date_min) else "inconnue"
        
        print(f"Application du Tri 3.1: Date la plus ancienne = {date_min_str}")
        
        groupe.loc[groupe['DATE_CREATION_FAED_DT'] == date_min, 'A_SUPPRIMER'] = False
        groupe.loc[groupe['DATE_CREATION_FAED_DT'] != date_min, 'A_SUPPRIMER'] = True
        
        groupe['REGLE_APPLIQUEE'] = "Tri 3.1: Conservation de la signalisation la plus ancienne"
        groupe.loc[groupe['DATE_CREATION_FAED_DT'] == date_min, 'DETAIL_REGLE'] = f"La signalisation est conservée car c'est la plus ancienne (date de création: {date_min_str})."
        groupe.loc[groupe['DATE_CREATION_FAED_DT'] != date_min, 'DETAIL_REGLE'] = "La signalisation est plus récente que l'autre."
        
        print("Tri 3.1 appliqué avec succès")
        return groupe, True
    
    print("Tri 3.1 non applicable, passage au Tri 3.2")
    
    # 3.2 Si dates identiques, vérifier la présence de photos
    photos_presentes = ~pd.isna(groupe['NUMERO_CLICHE']) & (groupe['NUMERO_CLICHE'] != '')
    
    # Debug des numéros de cliché
    print("Statut des photos:")
    for index, row in groupe.iterrows():
        num_sig = row['NUMERO_SIGNALISATION']
        num_cliche = row['NUMERO_CLICHE'] if not pd.isna(row['NUMERO_CLICHE']) else "Aucune photo"
        has_photo = "OUI" if not pd.isna(row['NUMERO_CLICHE']) and row['NUMERO_CLICHE'] != '' else "NON"
        print(f"  - Signalisation {num_sig}: Photo = {has_photo}, Numéro cliché = '{num_cliche}'")
    
    if photos_presentes.any() and not photos_presentes.all():
        print("Application du Tri 3.2: Certaines signalisations ont des photos, d'autres non")
        
        # Conserver les signalisations avec photo
        groupe.loc[photos_presentes, 'A_SUPPRIMER'] = False
        groupe.loc[~photos_presentes, 'A_SUPPRIMER'] = True
        
        groupe['REGLE_APPLIQUEE'] = "Tri 3.2: Conservation des signalisations avec photo"
        groupe.loc[photos_presentes, 'DETAIL_REGLE'] = "La signalisation est conservée car elle possède une photo."
        groupe.loc[~photos_presentes, 'DETAIL_REGLE'] = "La signalisation n'a pas de photo comparée à l'autre."
        
        print("Tri 3.2 appliqué avec succès")
        return groupe, True
    
    print("Tri 3.2 non applicable, passage au Tri 3.3")
    
    # 3.3 Si toutes ont ou n'ont pas de photo, conserver celle avec le plus petit NUMERO_SIGNALISATION
    min_num_signalisation = groupe['NUMERO_SIGNALISATION'].min()
    groupe.loc[groupe['NUMERO_SIGNALISATION'] == min_num_signalisation, 'A_SUPPRIMER'] = False
    groupe.loc[groupe['NUMERO_SIGNALISATION'] != min_num_signalisation, 'A_SUPPRIMER'] = True
    
    groupe['REGLE_APPLIQUEE'] = "Tri 3.3: Conservation de la signalisation avec le plus petit numéro"
    groupe.loc[groupe['NUMERO_SIGNALISATION'] == min_num_signalisation, 'DETAIL_REGLE'] = f"La signalisation est conservée car elle a le plus petit numéro de signalisation ({min_num_signalisation})."
    groupe.loc[groupe['NUMERO_SIGNALISATION'] != min_num_signalisation, 'DETAIL_REGLE'] = "Doublons parfaits, suppression par numéro de signalisation plus récent."
    
    return groupe, True

def sauvegarder_donnees_originales(df, nom_fichier_original):
    """
    Crée une sauvegarde du DataFrame original avant traitement.
    """
    try:
        # Créer le répertoire backups s'il n'existe pas
        if not os.path.exists(BACKUPS_DIR):
            os.makedirs(BACKUPS_DIR)
        
        # Nom du fichier de sauvegarde avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_sauvegarde = os.path.join(BACKUPS_DIR, f"backup_{timestamp}_{os.path.basename(nom_fichier_original)}")
        
        # Sauvegarde du DataFrame
        df.to_csv(nom_sauvegarde, index=False, encoding='utf-8')
        print(f"Sauvegarde des données originales créée: {nom_sauvegarde}")
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données originales: {e}")
        return False

def filtrer_idpp_pn(df):
    """
    Sépare les signalisations en deux groupes: 
    - Celles avec IDPP commençant par 'GN' (à traiter)
    - Celles avec IDPP commençant par 'PN' (à exclure)
    """
    # Convertir IDENTIFIANT_GASPARD en chaîne si ce n'est pas déjà le cas
    df['IDENTIFIANT_GASPARD'] = df['IDENTIFIANT_GASPARD'].astype(str)
    
    # Créer des masques pour les signalisations GN et PN
    masque_gn = df['IDENTIFIANT_GASPARD'].str.startswith('GN')
    masque_pn = df['IDENTIFIANT_GASPARD'].str.startswith('PN')
    
    # Sélectionner les sous-ensembles
    df_gn = df[masque_gn].copy()
    df_pn = df[masque_pn].copy()
    
    # Les autres signalisations (ni GN ni PN)
    df_autres = df[~(masque_gn | masque_pn)].copy()
    
    # Combiner GN et autres (tout ce qui n'est pas PN)
    df_a_traiter = pd.concat([df_gn, df_autres])
    
    # Marquer les signalisations PN comme "à supprimer" avec un motif spécifique
    df_pn['A_SUPPRIMER'] = True
    df_pn['REGLE_APPLIQUEE'] = "Exclusion automatique des IDPP commençant par PN"
    df_pn['DETAIL_REGLE'] = "Cette signalisation est automatiquement exclue car son identifiant GASPARD commence par 'PN'."
    df_pn['ID_GROUPE'] = "Exclus_PN"  # Assigner un ID_GROUPE spécifique
    
    # Nombre de signalisations dans chaque catégorie
    nb_gn = len(df_gn)
    nb_pn = len(df_pn)
    nb_autres = len(df_autres)
    
    print(f"Répartition des signalisations:")
    print(f"- IDPP commençant par GN: {nb_gn} signalisations (à traiter)")
    print(f"- IDPP commençant par PN: {nb_pn} signalisations (exclues)")
    print(f"- Autres formats d'IDPP: {nb_autres} signalisations (à traiter)")
    
    return df_a_traiter, df_pn, nb_gn, nb_pn, nb_autres

def traiter_doublons(chemin_fichier):
    """
    Fonction principale pour traiter les doublons selon l'algorithme spécifié.
    """
    # 1. Lecture du fichier CSV
    df = lire_fichier_csv(chemin_fichier)
    if df is None:
        return
    
    # Stocker le nom du fichier original dans les attributs du DataFrame
    df.name = chemin_fichier
    
    # 1.1 Sauvegarde des données originales
    sauvegarder_donnees_originales(df, chemin_fichier)
    
    # 1.2 Filtrer les signalisations PN (à exclure du traitement)
    df_a_traiter, df_pn, nb_gn, nb_pn, nb_autres = filtrer_idpp_pn(df)
    
    # Initialiser les colonnes pour le traitement
    df_a_traiter['A_SUPPRIMER'] = False
    df_a_traiter['REGLE_APPLIQUEE'] = "Signalisation unique (pas de doublon)"
    df_a_traiter['DETAIL_REGLE'] = "Cette signalisation est conservée car elle n'a pas de doublon."
    df_a_traiter['ID_GROUPE'] = "Aucun"  # Initialiser l'identifiant de groupe
    
    # 2. Regroupement des doublons
    groupes_doublons = regrouper_doublons(df_a_traiter)
    
    # 3. Traitement des groupes de doublons
    groupes_traites = []
    
    # Compteurs pour savoir combien de groupes sont résolus par chaque tri
    compteur_tri_1 = 0
    compteur_tri_2 = 0
    compteur_tri_3_1 = 0
    compteur_tri_3_2 = 0
    compteur_tri_3_3 = 0
    
    total_groupes = len(groupes_doublons)
    for i, (cle_groupe, groupe) in enumerate(groupes_doublons.items(), 1):
        if i % 10 == 0 or i == total_groupes:
            print(f"Traitement des doublons: {i}/{total_groupes} groupes ({(i/total_groupes)*100:.1f}%)")
        
        # Assigner un identifiant unique au groupe pour faciliter l'analyse
        id_groupe = f"Groupe_{i}"
        groupe['ID_GROUPE'] = id_groupe
        
        # Appliquer les règles hiérarchiques
        # Tri 1
        groupe, resolu = appliquer_tri_1(groupe)
        if resolu:
            compteur_tri_1 += 1
        
        # Tri 2 (si nécessaire)
        if not resolu:
            groupe, resolu = appliquer_tri_2(groupe)
            if resolu:
                compteur_tri_2 += 1
        
        # Tri 3 (si nécessaire)
        if not resolu:
            # Sauvegarde temporaire avant le tri 3 pour debug
            groupe_avant_tri3 = groupe.copy()
            
            groupe, resolu = appliquer_tri_3(groupe)
            
            # Déterminer quel sous-tri a été appliqué
            if resolu:
                if "Tri 3.1:" in groupe['REGLE_APPLIQUEE'].iloc[0]:
                    compteur_tri_3_1 += 1
                elif "Tri 3.2:" in groupe['REGLE_APPLIQUEE'].iloc[0]:
                    compteur_tri_3_2 += 1
                else:
                    compteur_tri_3_3 += 1
        
        groupes_traites.append(groupe)
    
    print("\nRÉPARTITION DES TRIS APPLIQUÉS:")
    print(f"- Groupes résolus par Tri 1: {compteur_tri_1}")
    print(f"- Groupes résolus par Tri 2: {compteur_tri_2}")
    print(f"- Groupes résolus par Tri 3.1 (dates différentes): {compteur_tri_3_1}")
    print(f"- Groupes résolus par Tri 3.2 (présence photos): {compteur_tri_3_2}")
    print(f"- Groupes résolus par Tri 3.3 (numéro signalisation): {compteur_tri_3_3}")
    
    # 4. Reconstituer le DataFrame complet
    # Identifier les signalisations qui n'ont pas de doublons
    cles_groupes_doublons = set()
    for cle in groupes_doublons.keys():
        # Extraire l'identifiant GASPARD de la clé du groupe
        identifiant_gaspard = cle[0]
        cles_groupes_doublons.add(identifiant_gaspard)
    
    # Filtrer les signalisations sans doublons (en utilisant IDENTIFIANT_GASPARD_NORM si disponible)
    if 'IDENTIFIANT_GASPARD_NORM' in df_a_traiter.columns:
        signalisations_sans_doublons = df_a_traiter[~df_a_traiter['IDENTIFIANT_GASPARD_NORM'].isin(cles_groupes_doublons)]
    else:
        signalisations_sans_doublons = df_a_traiter[~df_a_traiter['IDENTIFIANT_GASPARD'].isin(cles_groupes_doublons)]
    
    # Concaténer les signalisations sans doublons, les groupes traités, et les signalisations PN exclues
    if groupes_traites:
        df_traite = pd.concat([signalisations_sans_doublons] + groupes_traites + [df_pn])
    else:
        df_traite = pd.concat([signalisations_sans_doublons, df_pn])
    
    # Stocker les statistiques pour le résumé
    df_traite.attrs['nb_gn'] = nb_gn
    df_traite.attrs['nb_pn'] = nb_pn
    df_traite.attrs['nb_autres'] = nb_autres
    df_traite.name = chemin_fichier
    
    # 5. Générer les résultats
    generer_resultats(df_traite)
    
    return df_traite

def ajouter_entete_csv(nom_fichier, titre, description):
    """
    Ajoute un en-tête explicatif à un fichier CSV existant.
    L'en-tête est ajouté sous forme de commentaire avec le caractère #.
    """
    try:
        # Lire le contenu actuel du fichier
        with open(nom_fichier, 'r', encoding='utf-8') as file:
            contenu = file.read()
        
        # Créer l'en-tête avec des commentaires
        date_traitement = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        entete = f"# {titre}\n"
        entete += f"# Traitement effectué le {date_traitement}\n"
        entete += f"# {description}\n#\n"
        
        # Réécrire le fichier avec l'en-tête
        with open(nom_fichier, 'w', encoding='utf-8') as file:
            file.write(entete + contenu)
            
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'en-tête au fichier {nom_fichier}: {e}")
        return False

def demander_dossier_export():
    """
    Demande à l'utilisateur où enregistrer les exports.
    Retourne le chemin du dossier choisi.
    """
    print("\nOù souhaitez-vous enregistrer les exports?")
    print(f"1. Dossier par défaut ({EXPORTS_BASE_DIR})")
    print("2. Choisir un autre dossier")
    
    while True:
        choix = input("Votre choix (1 ou 2): ")
        
        if choix == "1":
            # Créer le répertoire d'exports par défaut s'il n'existe pas
            if not os.path.exists(EXPORTS_BASE_DIR):
                os.makedirs(EXPORTS_BASE_DIR)
            return EXPORTS_BASE_DIR
        
        elif choix == "2":
            # Demander le chemin d'un dossier
            chemin = input("Entrez le chemin complet du dossier où enregistrer les exports: ")
            
            # Vérifier si le chemin existe, sinon le créer
            if not os.path.exists(chemin):
                try:
                    os.makedirs(chemin)
                    print(f"Dossier créé: {chemin}")
                except Exception as e:
                    print(f"Erreur lors de la création du dossier: {e}")
                    continue
            
            # Vérifier si on a les droits d'écriture
            if not os.access(chemin, os.W_OK):
                print(f"Erreur: Vous n'avez pas les droits d'écriture dans ce dossier.")
                continue
                
            return chemin
        
        else:
            print("Choix invalide. Veuillez entrer 1 ou 2.")

def generer_resultats(df):
    """
    Génère trois fichiers en sortie:
    1. Un rapport des signalisations conservées avec motifs de conservation
    2. Un rapport des signalisations doublons avec motifs de classement
    3. Un fichier CSV contenant uniquement les NUMERO_SIGNALISATION à supprimer
    """
    # Demander à l'utilisateur où enregistrer les exports
    dossier_exports_base = demander_dossier_export()
    
    # Créer un timestamp pour les noms de fichiers et un format plus lisible
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    date_lisible = datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    # Créer un dossier pour les exports avec le timestamp dans le dossier choisi
    dossier_exports = os.path.join(dossier_exports_base, timestamp)
    if not os.path.exists(dossier_exports):
        os.makedirs(dossier_exports)
    print(f"Dossier d'exports créé: {dossier_exports}")
    
    # Compter les signalisations PN exclues pour les statistiques informatives
    signalisations_pn = df[df['ID_GROUPE'] == "Exclus_PN"]
    nb_pn_exclus = len(signalisations_pn)
    
    # Filtrer les signalisations PN pour les exclure des statistiques
    df_sans_pn = df[df['ID_GROUPE'] != "Exclus_PN"].copy()
    
    # Colonnes à inclure dans les rapports détaillés
    colonnes_rapport_detaille = [
        'NUMERO_SIGNALISATION', 'NUMERO_PERSONNE', 'IDENTIFIANT_GASPARD',
        'NOM', 'PRENOM', 'DATE_NAISSANCE_MIN', 'DATE_CREATION_FAED',
        'NUM_PROCEDURE', 'NUMERO_CLICHE', 'ID_GROUPE', 'REGLE_APPLIQUEE', 'DETAIL_REGLE'
    ]
    
    # S'assurer que toutes les colonnes existent
    colonnes_disponibles = [col for col in colonnes_rapport_detaille if col in df_sans_pn.columns]
    
    # 1. Rapport des signalisations conservées
    signalisations_conservees = df_sans_pn[df_sans_pn['A_SUPPRIMER'] == False]
    rapport_conservees = signalisations_conservees[colonnes_disponibles]
    
    # Trier le rapport des conservées par ID_GROUPE pour faciliter l'analyse
    if 'ID_GROUPE' in rapport_conservees.columns:
        rapport_conservees = rapport_conservees.sort_values(by=['ID_GROUPE', 'NUMERO_SIGNALISATION'])
    
    nom_fichier_conservees = f'RAPPORT_Signalisations_Conservees_{timestamp}.csv'
    chemin_complet_conservees = os.path.join(dossier_exports, nom_fichier_conservees)
    rapport_conservees.to_csv(chemin_complet_conservees, index=False, encoding='utf-8')
    
    # Ajouter un en-tête explicatif
    description_conservees = (
        "Ce fichier contient toutes les signalisations qui ont été CONSERVÉES après analyse des doublons.\n"
        "# La colonne 'REGLE_APPLIQUEE' indique la règle qui a été utilisée pour conserver cette signalisation.\n"
        "# La colonne 'DETAIL_REGLE' fournit une explication détaillée de la décision.\n"
        "# La colonne 'ID_GROUPE' permet d'identifier les groupes de doublons (même valeur = même groupe)."
    )
    ajouter_entete_csv(chemin_complet_conservees, "SIGNALISATIONS CONSERVÉES", description_conservees)
    print(f"Rapport des signalisations conservées généré: {chemin_complet_conservees} ({len(rapport_conservees)} signalisations)")
    
    # 2. Rapport des signalisations considérées comme doublons (sans PN)
    signalisations_doublons = df_sans_pn[df_sans_pn['A_SUPPRIMER'] == True]
    rapport_doublons = signalisations_doublons[colonnes_disponibles]
    
    # Trier le rapport des doublons par ID_GROUPE pour faciliter l'analyse
    if 'ID_GROUPE' in rapport_doublons.columns:
        rapport_doublons = rapport_doublons.sort_values(by=['ID_GROUPE', 'NUMERO_SIGNALISATION'])
    
    nom_fichier_doublons = f'RAPPORT_Signalisations_A_Supprimer_{timestamp}.csv'
    chemin_complet_doublons = os.path.join(dossier_exports, nom_fichier_doublons)
    rapport_doublons.to_csv(chemin_complet_doublons, index=False, encoding='utf-8')
    
    # Ajouter un en-tête explicatif
    description_doublons = (
        "Ce fichier contient toutes les signalisations qui ont été marquées comme DOUBLONS et qui doivent être SUPPRIMÉES.\n"
        "# La colonne 'REGLE_APPLIQUEE' indique la règle qui a déterminé que cette signalisation est un doublon.\n"
        "# La colonne 'DETAIL_REGLE' fournit une explication détaillée de la décision.\n"
        "# La colonne 'ID_GROUPE' permet d'identifier les groupes de doublons (même valeur = même groupe).\n"
        "# Note: Les signalisations avec IDPP commençant par 'PN' ne sont pas incluses dans ce rapport."
    )
    ajouter_entete_csv(chemin_complet_doublons, "SIGNALISATIONS À SUPPRIMER", description_doublons)
    print(f"Rapport des signalisations à supprimer généré: {chemin_complet_doublons} ({len(rapport_doublons)} signalisations)")
    
    # 3. Liste simplifiée des numéros de signalisation à supprimer (pour import dans le système)
    nom_fichier_liste = f'LISTE_Numeros_Signalisations_A_Supprimer_{timestamp}.csv'
    chemin_complet_liste = os.path.join(dossier_exports, nom_fichier_liste)
    
    # Créer un DataFrame simplifié avec moins de colonnes pour l'importation dans les systèmes
    colonnes_liste = ['NUMERO_SIGNALISATION', 'IDENTIFIANT_GASPARD', 'NOM', 'PRENOM', 'REGLE_APPLIQUEE']
    colonnes_liste_disponibles = [col for col in colonnes_liste if col in df_sans_pn.columns]
    
    df_liste = df_sans_pn[df_sans_pn['A_SUPPRIMER'] == True][colonnes_liste_disponibles]
    df_liste.to_csv(chemin_complet_liste, index=False, encoding='utf-8')
    
    # Ajouter un en-tête explicatif
    description_liste = (
        "Ce fichier contient uniquement les NUMÉROS DE SIGNALISATION à supprimer.\n"
        "# Il est conçu pour être facilement importé dans votre système de gestion.\n"
        "# Pour plus de détails sur les raisons de suppression, consultez le fichier de rapport complet.\n"
        "# Note: Les signalisations avec IDPP commençant par 'PN' ne sont pas incluses dans cette liste."
    )
    ajouter_entete_csv(chemin_complet_liste, "LISTE DES NUMÉROS DE SIGNALISATION À SUPPRIMER", description_liste)
    print(f"Liste des signalisations à supprimer générée: {chemin_complet_liste} ({len(df_liste)} signalisations)")
    
    # Statistiques sur les groupes de doublons (sans compter les PN)
    groupes_avec_doublons = df_sans_pn[df_sans_pn['ID_GROUPE'] != "Aucun"]['ID_GROUPE'].unique()
    nb_groupes = len(groupes_avec_doublons)
    
    # Récupérer les statistiques sur les signalisations GN/autres (sans PN)
    nb_gn = df.attrs.get('nb_gn', 0)
    nb_pn = df.attrs.get('nb_pn', 0)
    nb_autres = df.attrs.get('nb_autres', 0)
    
    # Résumé par règle appliquée (sans les règles PN)
    print("\nDÉTAIL DES RÈGLES APPLIQUÉES (hors PN):")
    regles_appliquees = df_sans_pn['REGLE_APPLIQUEE'].value_counts()
    for regle, count in regles_appliquees.items():
        print(f"- {regle}: {count} signalisations")
    
    # Résumé global (sans PN)
    total_sans_pn = len(df_sans_pn)
    a_supprimer_sans_pn = len(df_sans_pn[df_sans_pn['A_SUPPRIMER'] == True])
    a_conserver_sans_pn = total_sans_pn - a_supprimer_sans_pn
    
    # Pour information uniquement, garder le total avec PN
    total_avec_pn = len(df)
    
    # 4. Création d'un résumé au format PDF-friendly (HTML)
    nom_fichier_resume = f'RESUME_Traitement_Doublons_{timestamp}.html'
    chemin_complet_resume = os.path.join(dossier_exports, nom_fichier_resume)
    
    # Générer le contenu HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Résumé du traitement des doublons</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #003366; }}
        h2 {{ color: #0066cc; margin-top: 20px; }}
        .stats {{ margin: 20px 0; }}
        .stats table {{ border-collapse: collapse; width: 100%; }}
        .stats th, .stats td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .stats th {{ background-color: #f2f2f2; }}
        .files {{ margin: 20px 0; }}
        .files table {{ border-collapse: collapse; width: 100%; }}
        .files th, .files td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .files th {{ background-color: #f2f2f2; }}
        .rules {{ margin: 20px 0; }}
        .rules table {{ border-collapse: collapse; width: 100%; }}
        .rules th, .rules td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .rules th {{ background-color: #f2f2f2; }}
        .footer {{ margin-top: 30px; font-size: 0.8em; color: #666; }}
        .note {{ color: #cc0000; margin: 15px 0; }}
    </style>
</head>
<body>
    <h1>Résumé du traitement des doublons de signalisations</h1>
    <p><strong>Date du traitement:</strong> {date_lisible}</p>
    <p><strong>Fichier traité:</strong> {os.path.basename(df.name) if hasattr(df, 'name') else 'Inconnu'}</p>
    
    <div class="note">
        <p><strong>Note importante:</strong> Les {nb_pn_exclus} signalisations avec IDPP commençant par 'PN' ont été exclues des statistiques et des rapports de suppression.</p>
    </div>
    
    <h2>Statistiques globales (hors PN)</h2>
    <div class="stats">
        <table>
            <tr>
                <th>Catégorie</th>
                <th>Nombre</th>
                <th>Pourcentage</th>
            </tr>
            <tr>
                <td>Total des signalisations (hors PN)</td>
                <td>{total_sans_pn}</td>
                <td>100%</td>
            </tr>
            <tr>
                <td>Signalisations à conserver</td>
                <td>{a_conserver_sans_pn}</td>
                <td>{a_conserver_sans_pn/total_sans_pn*100:.1f}%</td>
            </tr>
            <tr>
                <td>Signalisations à supprimer</td>
                <td>{a_supprimer_sans_pn}</td>
                <td>{a_supprimer_sans_pn/total_sans_pn*100:.1f}%</td>
            </tr>
            <tr>
                <td>Nombre de groupes de doublons identifiés</td>
                <td>{nb_groupes}</td>
                <td>-</td>
            </tr>
        </table>
    </div>
    
    <h2>Répartition par type d'identifiant GASPARD</h2>
    <div class="stats">
        <table>
            <tr>
                <th>Type d'IDPP</th>
                <th>Nombre</th>
                <th>Pourcentage du total général</th>
                <th>Traitement</th>
            </tr>
            <tr>
                <td>IDPP commençant par GN</td>
                <td>{nb_gn}</td>
                <td>{nb_gn/total_avec_pn*100:.1f}%</td>
                <td>Analysés pour doublons</td>
            </tr>
            <tr>
                <td>IDPP commençant par PN</td>
                <td>{nb_pn}</td>
                <td>{nb_pn/total_avec_pn*100:.1f}%</td>
                <td>Exclus automatiquement</td>
            </tr>
            <tr>
                <td>Autres formats d'IDPP</td>
                <td>{nb_autres}</td>
                <td>{nb_autres/total_avec_pn*100:.1f}%</td>
                <td>Analysés pour doublons</td>
            </tr>
        </table>
    </div>
    
    <h2>Détail des règles appliquées (hors PN)</h2>
    <div class="rules">
        <table>
            <tr>
                <th>Règle</th>
                <th>Nombre</th>
                <th>Pourcentage</th>
            </tr>
"""
    
    # Ajouter chaque règle avec son compte
    for regle, count in regles_appliquees.items():
        pourcentage = count/total_sans_pn*100 if total_sans_pn > 0 else 0
        html_content += f"""
            <tr>
                <td>{regle}</td>
                <td>{count}</td>
                <td>{pourcentage:.1f}%</td>
            </tr>"""
    
    html_content += """
        </table>
    </div>
    
    <h2>Fichiers générés</h2>
    <div class="files">
        <table>
            <tr>
                <th>Fichier</th>
                <th>Description</th>
                <th>Nombre d'enregistrements</th>
            </tr>"""
    
    html_content += f"""
            <tr>
                <td>{nom_fichier_conservees}</td>
                <td>Rapport détaillé des signalisations conservées</td>
                <td>{len(rapport_conservees)}</td>
            </tr>
            <tr>
                <td>{nom_fichier_doublons}</td>
                <td>Rapport détaillé des signalisations à supprimer</td>
                <td>{len(rapport_doublons)}</td>
            </tr>
            <tr>
                <td>{nom_fichier_liste}</td>
                <td>Liste simplifiée des numéros de signalisation à supprimer</td>
                <td>{len(df_liste)}</td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Ce rapport a été généré automatiquement par le script de traitement des doublons de signalisations développé par le GND Yoann BAUDRIN.</p>
        <p>Pôle Judiciaire de la Gendarmerie Nationale - Département du Fichier Automatisé des Empreintes Digitales.</p>
        <p>Tous les fichiers se trouvent dans le dossier: {dossier_exports}</p>
    </div>
</body>
</html>"""
    
    # Enregistrer le fichier HTML
    with open(chemin_complet_resume, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Résumé HTML du traitement généré: {chemin_complet_resume}")
    
    # 5. Créer aussi un fichier de résumé texte pour compatibilité
    nom_fichier_resume_txt = f'RESUME_Traitement_Doublons_{timestamp}.txt'
    chemin_complet_resume_txt = os.path.join(dossier_exports, nom_fichier_resume_txt)
    
    with open(chemin_complet_resume_txt, 'w', encoding='utf-8') as f:
        f.write(f"RÉSUMÉ DU TRAITEMENT DES DOUBLONS IDPP - {date_lisible}\n")
        f.write("="*80 + "\n\n")
        
        f.write("INFORMATIONS GÉNÉRALES\n")
        f.write("-"*80 + "\n")
        f.write(f"Fichier traité: {os.path.basename(df.name) if hasattr(df, 'name') else 'Inconnu'}\n")
        f.write(f"Date et heure du traitement: {date_lisible}\n")
        f.write(f"Dossier des exports: {dossier_exports}\n")
        f.write(f"Note: Les {nb_pn_exclus} signalisations avec IDPP commençant par 'PN' ont été exclues des statistiques.\n\n")
        
        f.write("STATISTIQUES GLOBALES (HORS PN)\n")
        f.write("-"*80 + "\n")
        f.write(f"Total des signalisations (hors PN): {total_sans_pn}\n")
        f.write(f"Signalisations à conserver: {a_conserver_sans_pn} ({a_conserver_sans_pn/total_sans_pn*100:.1f}%)\n" if total_sans_pn > 0 else "Signalisations à conserver: 0 (0.0%)\n")
        f.write(f"Signalisations à supprimer: {a_supprimer_sans_pn} ({a_supprimer_sans_pn/total_sans_pn*100:.1f}%)\n" if total_sans_pn > 0 else "Signalisations à supprimer: 0 (0.0%)\n")
        f.write(f"Nombre de groupes de doublons identifiés: {nb_groupes}\n\n")
        
        f.write("RÉPARTITION PAR TYPE D'IDENTIFIANT GASPARD\n")
        f.write("-"*80 + "\n")
        f.write(f"- Signalisations GN: {nb_gn} ({nb_gn/total_avec_pn*100:.1f}% du total général) - Analysées pour doublons\n" if total_avec_pn > 0 else "- Signalisations GN: 0 (0.0%)\n")
        f.write(f"- Signalisations PN: {nb_pn} ({nb_pn/total_avec_pn*100:.1f}% du total général) - Exclues automatiquement\n" if total_avec_pn > 0 else "- Signalisations PN: 0 (0.0%)\n")
        if nb_autres > 0:
            f.write(f"- Autres formats d'IDPP: {nb_autres} ({nb_autres/total_avec_pn*100:.1f}% du total général) - Analysées pour doublons\n" if total_avec_pn > 0 else f"- Autres formats d'IDPP: {nb_autres} (0.0%)\n")
        
        f.write("\nDÉTAIL DES RÈGLES APPLIQUÉES (HORS PN)\n")
        f.write("-"*80 + "\n")
        for regle, count in regles_appliquees.items():
            pourcentage = count/total_sans_pn*100 if total_sans_pn > 0 else 0
            f.write(f"- {regle}: {count} signalisations ({pourcentage:.1f}%)\n")
        
        f.write("\nFICHIERS GÉNÉRÉS\n")
        f.write("-"*80 + "\n")
        f.write(f"1. {nom_fichier_conservees}\n   - Rapport détaillé des signalisations conservées ({len(rapport_conservees)} signalisations)\n\n")
        f.write(f"2. {nom_fichier_doublons}\n   - Rapport détaillé des signalisations à supprimer ({len(rapport_doublons)} signalisations)\n\n")
        f.write(f"3. {nom_fichier_liste}\n   - Liste simplifiée des numéros de signalisation à supprimer ({len(df_liste)} signalisations)\n\n")
        f.write(f"4. {nom_fichier_resume}\n   - Résumé du traitement au format HTML (plus lisible)\n\n")
        
        f.write("="*80 + "\n")
        f.write("Ce rapport a été généré automatiquement par le script de traitement des doublons de signalisations développé par le GND Yoann BAUDRIN.\n")
        f.write("Pôle Judiciaire de la Gendarmerie Nationale - Département du Fichier Automatisé des Empreintes Digitales.\n")
    
    print(f"Résumé texte du traitement généré: {chemin_complet_resume_txt}")
    
    print("\nTRAITEMENT TERMINÉ AVEC SUCCÈS !")
    print("="*80)
    print(f"Fichier traité: {os.path.basename(df.name) if hasattr(df, 'name') else 'Inconnu'}")
    print(f"Note: Les {nb_pn_exclus} signalisations PN ont été exclues des statistiques.")
    print(f"Total des signalisations (hors PN): {total_sans_pn}")
    print(f"Signalisations à conserver: {a_conserver_sans_pn} ({a_conserver_sans_pn/total_sans_pn*100:.1f}%)" if total_sans_pn > 0 else "Signalisations à conserver: 0 (0.0%)")
    print(f"Signalisations à supprimer: {a_supprimer_sans_pn} ({a_supprimer_sans_pn/total_sans_pn*100:.1f}%)" if total_sans_pn > 0 else "Signalisations à supprimer: 0 (0.0%)")
    print("="*80)
    print(f"Tous les fichiers générés ont été placés dans le dossier: {dossier_exports}")
    print("Pour consulter les résultats détaillés, ouvrez le fichier de résumé HTML généré.")

def demander_fichier_csv():
    """
    Demande à l'utilisateur de choisir un fichier CSV à traiter.
    Retourne le chemin du fichier sélectionné.
    """
    # Obtenir la liste des fichiers CSV dans le répertoire courant
    fichiers_csv = [f for f in os.listdir() if f.endswith('.csv')]
    
    if not fichiers_csv:
        print("Aucun fichier CSV trouvé dans le répertoire actuel.")
        chemin_manuel = input("Veuillez entrer le chemin complet d'un fichier CSV à traiter: ")
        return chemin_manuel
    
    # Afficher la liste des fichiers CSV disponibles
    print("\nFichiers CSV disponibles:")
    for i, fichier in enumerate(fichiers_csv, 1):
        print(f"{i}. {fichier}")
    
    # Demander à l'utilisateur de choisir un fichier
    while True:
        try:
            choix = input("\nChoisissez un fichier (numéro) ou entrez le chemin d'un autre fichier: ")
            
            # Vérifier si l'entrée est un nombre correspondant à l'index
            if choix.isdigit() and 1 <= int(choix) <= len(fichiers_csv):
                return fichiers_csv[int(choix) - 1]
            
            # Sinon, considérer l'entrée comme un chemin de fichier
            elif os.path.exists(choix) and choix.endswith('.csv'):
                return choix
            
            # Si l'utilisateur entre juste un nom de fichier sans chemin
            elif choix.endswith('.csv') and os.path.exists(choix):
                return choix
            
            else:
                print("Choix invalide. Veuillez réessayer.")
        
        except Exception as e:
            print(f"Erreur: {e}. Veuillez réessayer.")

# Point d'entrée du script
if __name__ == "__main__":
    print("="*80)
    print("TRAITEMENT DES DOUBLONS DE SIGNALISATIONS")
    print("="*80)
    
    # Demander à l'utilisateur de choisir le fichier CSV à traiter
    chemin_fichier = demander_fichier_csv()
    
    print(f"Démarrage du traitement des doublons dans le fichier '{chemin_fichier}'...")
    print("-"*80)
    
    df_final = traiter_doublons(chemin_fichier)
    
    if df_final is not None:
        print("\nVous pouvez maintenant utiliser les fichiers générés pour mettre à jour votre base de signalisations.")
        print("L'analyse des doublons est terminée.")