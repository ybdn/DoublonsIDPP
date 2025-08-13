#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Graphique pour le Traitement des Doublons IDPP

Copyright (c) 2025 GND Yoann BAUDRIN - Pôle Judiciaire de la Gendarmerie Nationale (PJGN)
Département du Fichier Automatisé des Empreintes Digitales (FAED)

TOUS DROITS RÉSERVÉS
"""

import sys
import os
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QTextEdit, QProgressBar, QMessageBox, QGroupBox,
                             QLineEdit, QFrame, QSpacerItem, QSizePolicy,
                             QScrollArea)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSettings
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
import math
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

# Importer le module de traitement existant
try:
    from script_doublons_idpp import traiter_doublons, lire_fichier_csv
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print("Assurez-vous que script_doublons_idpp.py est dans le même dossier.")
    sys.exit(1)


class TraitementThread(QThread):
    """Thread pour exécuter le traitement des doublons en arrière-plan"""
    
    # Signaux pour communiquer avec l'interface
    finished_signal = pyqtSignal(bool, str)  # succès, message
    progress_signal = pyqtSignal(str)  # message de progression
    
    def __init__(self, chemin_fichier, dossier_exports):
        super().__init__()
        self.chemin_fichier = chemin_fichier
        self.dossier_exports = dossier_exports
        
    def run(self):
        """Exécute le traitement des doublons"""
        try:
            self.progress_signal.emit("Démarrage du traitement...")
            
            # Exécuter le traitement
            df_traite = traiter_doublons(self.chemin_fichier, self.dossier_exports)
            
            if df_traite is not None:
                self.progress_signal.emit("Traitement terminé avec succès!")
                self.finished_signal.emit(True, "Traitement des doublons terminé avec succès!")
            else:
                self.finished_signal.emit(False, "Erreur lors du traitement des doublons.")
                
        except Exception as e:
            error_msg = f"Erreur lors du traitement: {str(e)}"
            self.progress_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg)


class DoublonsIDPPGUI(QMainWindow):
    """Interface graphique principale pour le traitement des doublons IDPP"""
    
    def __init__(self):
        super().__init__()
        self.chemin_fichier_csv = ""
        self.dossier_exports = ""
        self.traitement_thread = None
        self.current_theme = "system"  # system | light | dark
        self.settings = QSettings("PJGN", "DoublonsIDPP")

        self.init_ui()
        self.load_settings()
        self.apply_theme(self.current_theme)
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        # Fenêtre
        self.setWindowTitle("DoublonsIDPP • Détection de doublons")
        self.setGeometry(100, 100, 960, 680)
        self.setMinimumSize(840, 620)
        self.setWindowIcon(QIcon.fromTheme("view-filter"))
        self.statusBar().showMessage("Prêt")

    # Plus de bouton de bascule de thème: l'application suit le thème système

        # Structure centrale avec scroll
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget); root_layout.setContentsMargins(0,0,0,0); root_layout.setSpacing(0)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root_layout.addWidget(self.scroll_area)
        self.scroll_content = QWidget(); self.scroll_area.setWidget(self.scroll_content)
        main_layout = QVBoxLayout(self.scroll_content); main_layout.setSpacing(28); main_layout.setContentsMargins(32,28,32,28)
        self.main_layout = main_layout

        # Header
        header = QFrame(); header.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header); header_layout.setContentsMargins(20,14,20,14); header_layout.setSpacing(16)
        title_box = QVBoxLayout()
        title_label = QLabel("DoublonsIDPP")
        title_font = QFont(); title_font.setPointSize(20); title_font.setBold(True)
        title_label.setFont(title_font); title_label.setObjectName("AppTitle")
        subtitle_label = QLabel("Analyse et traitement moderne des doublons de signalisations"); subtitle_label.setObjectName("AppSubtitle")
        title_box.addWidget(title_label); title_box.addWidget(subtitle_label)
        header_layout.addLayout(title_box)
        header_layout.addItem(QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
    # En-tête sans bouton bascule de thème
        main_layout.addWidget(header)

        # Groupe CSV
        csv_group = QGroupBox("1. Sélection du fichier CSV à traiter")
        csv_layout = QVBoxLayout(csv_group); csv_layout.setSpacing(12); csv_layout.setContentsMargins(18,16,18,16)
        csv_selection_layout = QHBoxLayout()
        self.csv_path_edit = QLineEdit(); self.csv_path_edit.setPlaceholderText("Aucun fichier sélectionné..."); self.csv_path_edit.setReadOnly(True)
        csv_selection_layout.addWidget(self.csv_path_edit)
        self.btn_select_csv = QPushButton("Parcourir...")
        self.btn_select_csv.clicked.connect(self.select_csv_file)
        self.btn_select_csv.setStyleSheet("""QPushButton { background-color:#0066cc; color:#fff; border:none; padding:8px 16px; border-radius:4px; font-weight:bold; } QPushButton:hover { background-color:#0052a3; }""")
        csv_selection_layout.addWidget(self.btn_select_csv)
        csv_layout.addLayout(csv_selection_layout)
        self.csv_info_label = QLabel("Sélectionnez un fichier CSV contenant les signalisations à analyser."); self.csv_info_label.setObjectName("InfoLabel")
        csv_layout.addWidget(self.csv_info_label)
        main_layout.addWidget(csv_group)

        # Groupe export
        export_group = QGroupBox("2. Destination des fichiers d'export")
        export_layout = QVBoxLayout(export_group); export_layout.setSpacing(12); export_layout.setContentsMargins(18,16,18,16)
        export_selection_layout = QHBoxLayout()
        self.export_path_edit = QLineEdit(); self.export_path_edit.setPlaceholderText("Aucun dossier sélectionné..."); self.export_path_edit.setReadOnly(True)
        export_selection_layout.addWidget(self.export_path_edit)
        self.btn_select_export = QPushButton("Parcourir...")
        self.btn_select_export.clicked.connect(self.select_export_directory)
        self.btn_select_export.setStyleSheet("""QPushButton { background-color:#0066cc; color:#fff; border:none; padding:8px 16px; border-radius:4px; font-weight:bold; } QPushButton:hover { background-color:#0052a3; }""")
        export_selection_layout.addWidget(self.btn_select_export)
        export_layout.addLayout(export_selection_layout)
        self.export_info_label = QLabel("Choisissez le dossier où seront enregistrés les rapports d'analyse."); self.export_info_label.setObjectName("InfoLabel")
        export_layout.addWidget(self.export_info_label)
        main_layout.addWidget(export_group)

        # Groupe traitement
        process_group = QGroupBox("3. Lancement du traitement")
        process_layout = QVBoxLayout(process_group); process_layout.setSpacing(14); process_layout.setContentsMargins(18,18,18,18)
        self.btn_process = QPushButton("Lancer l'analyse des doublons")
        self.btn_process.clicked.connect(self.start_processing)
        self.btn_process.setEnabled(False); self.btn_process.setMinimumHeight(40)
        self.btn_process.setStyleSheet("""QPushButton { background-color:#28a745; color:#fff; border:none; padding:12px 24px; border-radius:6px; font-weight:bold; font-size:14px; } QPushButton:hover { background-color:#1e7e34; } QPushButton:disabled { background-color:#cccccc; color:#666666; }""")
        process_layout.addWidget(self.btn_process)
        self.progress_bar = QProgressBar(); self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""QProgressBar { border:2px solid #cccccc; border-radius:5px; text-align:center; } QProgressBar::chunk { background-color:#0066cc; border-radius:3px; }""")
        process_layout.addWidget(self.progress_bar)
        main_layout.addWidget(process_group)

        # Groupe logs
        logs_group = QGroupBox("Journal d'activité")
        logs_layout = QVBoxLayout(logs_group); logs_layout.setSpacing(10); logs_layout.setContentsMargins(18,16,18,16)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True); self.log_text.setMinimumHeight(180)
        # Style du journal: suppression de la dépendance stricte à JetBrains Mono
        # Une tentative de chargement optionnelle est faite plus bas (méthode load_optional_mono_font)
        self.log_text.setStyleSheet(
            "QTextEdit { background-color: rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.12); border-radius:6px; "
            "font-family: 'Menlo','SF Mono','Courier New',monospace; font-size:11px; padding:6px; }"
        )
        # Chargement optionnel d'une police JetBrains Mono locale si disponible
        self.load_optional_mono_font()
        self.log_message("Interface initialisée. Prêt à traiter les doublons.")
        logs_layout.addWidget(self.log_text)
        logs_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_layout.addWidget(logs_group, 1)

        # Footer
        footer_label = QLabel("© 2025 GND Yoann BAUDRIN - PJGN/FAED • v1.0"); footer_label.setAlignment(Qt.AlignCenter); footer_label.setObjectName("FooterLabel")
        main_layout.addWidget(footer_label)

        # Initialisations finales
        self.check_ready_to_process()
        self.apply_card_effects([csv_group, export_group, process_group, logs_group])
        self._responsive_groups = [csv_group, export_group, process_group, logs_group]
        self._responsive_group_layouts = [csv_layout, export_layout, process_layout, logs_layout]
        self.apply_responsive_metrics(self.width())

    def load_optional_mono_font(self):
        """Charge JetBrains Mono si un fichier .ttf est présent dans un dossier 'fonts' à la racine.
        Ne fait rien en cas d'échec. Permet de réduire l'avertissement Qt.
        """
        try:
            from PyQt5.QtGui import QFontDatabase
            base_dir = os.path.dirname(os.path.abspath(__file__))
            fonts_dir = os.path.join(base_dir, 'fonts')
            if not os.path.isdir(fonts_dir):
                return
            loaded_any = False
            for fname in os.listdir(fonts_dir):
                if fname.lower().startswith('jetbrainsmono') and fname.lower().endswith('.ttf'):
                    path = os.path.join(fonts_dir, fname)
                    if QFontDatabase.addApplicationFont(path) != -1:
                        loaded_any = True
            if loaded_any:
                # Appliquer JetBrains Mono comme première option désormais disponible
                base_style = (
                    "QTextEdit { background-color: rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.12); border-radius:6px; "
                    "font-family: 'JetBrains Mono','Menlo','SF Mono','Courier New',monospace; font-size:11px; padding:6px; }"
                )
                self.log_text.setStyleSheet(base_style)
        except Exception as e:
            # Log discret dans la sortie standard pour debug, sans interrompre l'UI
            print(f"[INFO] Impossible de charger JetBrains Mono optionnelle: {e}")

    def apply_responsive_metrics(self, width):
        """Adapte dynamiquement marges / espacements selon largeur."""
        if width < 700:
            outer_m = (12, 12, 12, 12)
            spacing = 12
            group_m = (12, 10, 12, 10)
        elif width < 900:
            outer_m = (20, 20, 20, 20)
            spacing = 18
            group_m = (14, 12, 14, 12)
        elif width < 1200:
            outer_m = (32, 28, 32, 28)
            spacing = 24
            group_m = (18, 16, 18, 16)
        else:
            outer_m = (72, 40, 72, 48)
            spacing = 36
            group_m = (22, 18, 22, 18)
        self.main_layout.setContentsMargins(*outer_m)
        self.main_layout.setSpacing(spacing)
        for lay in self._responsive_group_layouts:
            lay.setContentsMargins(*group_m)
        # Ajustement rayon ombre léger selon taille
        for g in self._responsive_groups:
            eff = g.graphicsEffect()
            if eff:
                eff.setBlurRadius(18 if width < 900 else 24)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.apply_responsive_metrics(event.size().width())
        except Exception:
            pass
    
    def apply_card_effects(self, widgets):
        """Ajoute une ombre portée légère aux cadres."""
        # Choisir la couleur d'ombre selon le thème effectif (prend en compte le mode système)
        effective_theme = self.get_effective_theme()
        for w in widgets:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(20)
            effect.setXOffset(0)
            effect.setYOffset(4)
            # Couleur adaptée selon thème
            if effective_theme == "dark":
                effect.setColor(QColor(0, 0, 0, 160))
            else:
                effect.setColor(QColor(0, 0, 0, 50))
            w.setGraphicsEffect(effect)
    
    # La bascule de thème a été retirée: on respecte le thème système uniquement
    
    def apply_theme(self, theme):
        """Applique un thème système (par défaut) ou clair/sombre moderne."""
        # Utilitaire: ajustement de couleur hex pour hover/pressed
        def _adjust_hex_color(hex_color: str, factor: float) -> str:
            """Assombrit (<1) ou éclaircit (>1) une couleur hex (#RRGGBB)."""
            try:
                hex_color = hex_color.lstrip('#')
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                def clamp(v):
                    return max(0, min(255, int(v)))
                if factor >= 1:
                    # éclaircir vers 255
                    r = clamp(r + (255 - r) * (factor - 1))
                    g = clamp(g + (255 - g) * (factor - 1))
                    b = clamp(b + (255 - b) * (factor - 1))
                else:
                    # assombrir
                    r = clamp(r * factor)
                    g = clamp(g * factor)
                    b = clamp(b * factor)
                return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                return hex_color if hex_color.startswith('#') else f"#{hex_color}"

        # Détection du thème effectif pour certains comportements
        effective_theme = self.get_effective_theme()

        if theme == "system":
            # Respect du thème de l'OS: retirer les stylesheets custom
            self.setStyleSheet("")
            try:
                self.btn_select_csv.setStyleSheet("")
                self.btn_select_export.setStyleSheet("")
                self.btn_process.setStyleSheet("")
                self.log_text.setStyleSheet("")
                if hasattr(self, "progress_bar") and self.progress_bar:
                    self.progress_bar.setStyleSheet("")
            except Exception:
                pass
            # Mettre à jour les ombres selon le thème effectif du système
            self.apply_card_effects([*self.findChildren(QGroupBox)])
            return
        accent = "#1d72b8"
        danger = "#dc3545"
        success = "#2e8540"
        warning = "#f0ad4e"
        if theme == "dark":
            bg = "#12181f"
            surface = "#1e2731"
            border = "#2e3a47"
            text = "#e5ecf1"
            secondary = "#96a3b0"
            header_grad = "linear-gradient(45deg, #203040, #162029)"
        else:
            bg = "#f4f6f9"
            surface = "#ffffff"
            border = "#d0d7de"
            text = "#1f2d3d"
            secondary = "#5f6b76"
            header_grad = "linear-gradient(90deg, #1d72b8, #2396ef)"

        # Remplacer les fonctions non supportées par Qt (shade) par des couleurs calculées
        hover = _adjust_hex_color(accent, 1.08)  # légèrement plus clair
        pressed = _adjust_hex_color(accent, 0.85)  # légèrement plus sombre
        stylesheet = f"""
        QMainWindow {{ background: {bg}; }}
        #HeaderFrame {{
            background: {header_grad};
            border-radius: 14px;
            color: #ffffff;
        }}
        #AppTitle {{ color: #ffffff; letter-spacing:0.5px; }}
        #AppSubtitle {{ color: rgba(255,255,255,0.85); font-size:12px; }}
        QGroupBox {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 12px;
            margin-top: 16px;
            font-weight:600;
            padding: 16px 16px 12px 16px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 2px 6px 4px 6px;
            color: {text};
            background: transparent;
        }}
        QLabel {{ color: {text}; }}
        #InfoLabel {{ color: {secondary}; font-style:italic; }}
        #FooterLabel {{ color: {secondary}; font-size:11px; margin-top:8px; }}
        QLineEdit {{
            background: {surface};
            border: 2px solid {border};
            border-radius: 8px;
            padding: 8px 10px;
            color: {text};
            selection-background-color: {accent};
            selection-color: #ffffff;
        }}
        QLineEdit:focus {{ border-color: {accent}; }}
        QPushButton {{
            border-radius: 8px;
            padding: 8px 18px;
            font-weight:600;
            background: {accent};
            color: #ffffff;
        }}
    QPushButton:hover:!disabled {{ background: {hover}; }}
    QPushButton:pressed {{ background: {pressed}; }}
        QPushButton:disabled {{ background: {border}; color: {secondary}; }}
        QProgressBar {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 8px;
            text-align: center;
            color: {text};
        }}
        QProgressBar::chunk {{
            background: {accent};
            border-radius: 6px;
        }}
        QMessageBox {{ background: {surface}; }}
        QScrollBar:vertical {{
            background: transparent; width:10px; margin:2px; border-radius:5px;
        }}
        QScrollBar::handle:vertical {{ background: {border}; border-radius:5px; min-height:24px; }}
        QScrollBar::handle:vertical:hover {{ background: {accent}; }}
        QTextEdit {{ color: {text}; }}
        """
        self.setStyleSheet(stylesheet)
        # Boutons spécifiques (process already styled in init but we override partly)
        # Coloration dynamique des labels d'état
        if "valide" in self.csv_info_label.text().lower():
            self.csv_info_label.setStyleSheet(f"color: {success}; font-style:italic;")
        if "rapports" in self.export_info_label.text().lower():
            self.export_info_label.setStyleSheet(f"color: {success}; font-style:italic;")
        # Ajuster ombres
        self.apply_card_effects([*self.findChildren(QGroupBox)])
    # Icône de bascule supprimée

    def get_effective_theme(self) -> str:
        """Retourne 'dark' ou 'light' en fonction du choix utilisateur et du système."""
        if self.current_theme in ("dark", "light"):
            return self.current_theme
        # Détecter le thème système via la palette Qt (Linux/Ubuntu inclus)
        try:
            pal = QApplication.instance().palette()
            # Utiliser la couleur de fenêtre comme référence
            color = pal.color(QPalette.Window)
            # Luminance perceptuelle
            luminance = (0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF())
            return "dark" if luminance < 0.5 else "light"
        except Exception:
            return "light"
    
    def load_settings(self):
        """Charge les préférences utilisateur (chemins & thème)."""
        last_csv = self.settings.value("last_csv", "")
        last_export = self.settings.value("last_export", "")
        # Thème: toujours système
        self.current_theme = "system"
        if last_csv and os.path.exists(last_csv):
            self.chemin_fichier_csv = last_csv
            self.csv_path_edit.setText(last_csv)
        if last_export and os.path.isdir(last_export):
            self.dossier_exports = last_export
            self.export_path_edit.setText(last_export)
        self.check_ready_to_process()
    
    def save_settings(self):
        self.settings.setValue("last_csv", self.chemin_fichier_csv)
        self.settings.setValue("last_export", self.dossier_exports)
    # Plus de thème à enregistrer
        
    def log_message(self, message):
        """Ajoute un message au journal d'activité"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll vers le bas
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def select_csv_file(self):
        """Ouvre un dialogue pour sélectionner le fichier CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le fichier CSV des signalisations",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.chemin_fichier_csv = file_path
            self.csv_path_edit.setText(file_path)
            self.log_message(f"Fichier CSV sélectionné: {os.path.basename(file_path)}")
            
            # Vérifier le fichier
            try:
                df = lire_fichier_csv(file_path)
                if df is not None:
                    nb_lignes = len(df)
                    self.csv_info_label.setText(f"Fichier valide: {nb_lignes} signalisations détectées.")
                    # style dynamique dans apply_theme
                    self.log_message(f"Fichier valide: {nb_lignes} signalisations trouvées.")
                else:
                    self.csv_info_label.setText("Erreur: Impossible de lire le fichier CSV.")
                    self.csv_info_label.setStyleSheet("color: #dc3545; font-style: italic;")
                    self.log_message("Erreur: Fichier CSV invalide ou illisible.")
            except Exception as e:
                self.csv_info_label.setText(f"Erreur: {str(e)}")
                self.csv_info_label.setStyleSheet("color: #dc3545; font-style: italic;")
                self.log_message(f"Erreur lors de la vérification du fichier: {str(e)}")
            
            self.check_ready_to_process()
            self.save_settings()
            
    def select_export_directory(self):
        """Ouvre un dialogue pour sélectionner le dossier d'export"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de destination des exports"
        )
        
        if directory:
            self.dossier_exports = directory
            self.export_path_edit.setText(directory)
            self.log_message(f"Dossier d'export sélectionné: {directory}")
            self.export_info_label.setText(f"Les rapports seront enregistrés dans: {directory}")
            self.export_info_label.setStyleSheet("color: #28a745; font-style: italic;")
            self.check_ready_to_process()
            self.save_settings()
            
    def check_ready_to_process(self):
        """Vérifie si tous les éléments sont prêts pour le traitement"""
        if self.chemin_fichier_csv and self.dossier_exports:
            self.btn_process.setEnabled(True)
            self.log_message("Prêt à lancer le traitement.")
        else:
            self.btn_process.setEnabled(False)
            
    def start_processing(self):
        """Lance le traitement des doublons"""
        if not self.chemin_fichier_csv or not self.dossier_exports:
            QMessageBox.warning(self, "Paramètres manquants", 
                              "Veuillez sélectionner un fichier CSV et un dossier d'export.")
            return
            
        # Vérifier que le fichier existe encore
        if not os.path.exists(self.chemin_fichier_csv):
            QMessageBox.critical(self, "Fichier introuvable", 
                               "Le fichier CSV sélectionné n'existe plus.")
            return
            
        # Désactiver l'interface pendant le traitement
        self.set_interface_enabled(False)
        
        # Afficher la barre de progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        
        self.log_message("=" * 50)
        self.log_message("DÉBUT DU TRAITEMENT DES DOUBLONS")
        self.log_message(f"Fichier: {os.path.basename(self.chemin_fichier_csv)}")
        self.log_message(f"Export: {self.dossier_exports}")
        self.log_message("=" * 50)
        
        # Créer et lancer le thread de traitement
        self.traitement_thread = TraitementThread(self.chemin_fichier_csv, self.dossier_exports)
        self.traitement_thread.progress_signal.connect(self.update_progress)
        self.traitement_thread.finished_signal.connect(self.processing_finished)
        self.traitement_thread.start()
        
    def set_interface_enabled(self, enabled):
        """Active/désactive les éléments de l'interface"""
        self.btn_select_csv.setEnabled(enabled)
        self.btn_select_export.setEnabled(enabled)
        # Garantir un bool strict (et non la dernière chaîne évaluée) pour setEnabled
        self.btn_process.setEnabled(bool(enabled and self.chemin_fichier_csv and self.dossier_exports))
        
    def update_progress(self, message):
        """Met à jour le journal avec les messages de progression"""
        self.log_message(message)
        
    def processing_finished(self, success, message):
        """Appelé lorsque le traitement est terminé"""
        # Masquer la barre de progression
        self.progress_bar.setVisible(False)
        
        # Réactiver l'interface
        self.set_interface_enabled(True)
        
        if success:
            self.log_message("=" * 50)
            self.log_message("TRAITEMENT TERMINÉ AVEC SUCCÈS!")
            self.log_message("Les fichiers de rapport ont été générés.")
            self.log_message("=" * 50)
            self.statusBar().showMessage("Traitement terminé avec succès", 5000)
            
            # Afficher une boîte de dialogue de succès
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Traitement terminé")
            msg_box.setText("Le traitement des doublons est terminé avec succès!")
            msg_box.setInformativeText(f"Les fichiers de rapport ont été générés dans:\n{self.dossier_exports}")
            
            # Bouton pour ouvrir le dossier
            open_button = msg_box.addButton("Ouvrir le dossier", QMessageBox.ActionRole)
            msg_box.addButton(QMessageBox.Ok)
            
            msg_box.exec_()
            
            # Si l'utilisateur clique sur "Ouvrir le dossier"
            if msg_box.clickedButton() == open_button:
                self.open_export_directory()
                
        else:
            self.log_message("=" * 50)
            self.log_message("ERREUR LORS DU TRAITEMENT!")
            self.log_message(message)
            self.log_message("=" * 50)
            self.statusBar().showMessage("Erreur de traitement", 5000)
            
            QMessageBox.critical(self, "Erreur de traitement", 
                               f"Une erreur est survenue lors du traitement:\n\n{message}")
                               
    def open_export_directory(self):
        """Ouvre le dossier d'export dans l'explorateur de fichiers"""
        try:
            if sys.platform == "linux":
                os.system(f'xdg-open "{self.dossier_exports}"')
            elif sys.platform == "darwin":  # macOS
                os.system(f'open "{self.dossier_exports}"')
            elif sys.platform == "win32":  # Windows
                os.system(f'explorer "{self.dossier_exports}"')
        except Exception as e:
            self.log_message(f"Impossible d'ouvrir le dossier: {str(e)}")
            
    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        if self.traitement_thread and self.traitement_thread.isRunning():
            reply = QMessageBox.question(self, "Traitement en cours",
                                       "Un traitement est en cours. Voulez-vous vraiment quitter?",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
                
            # Arrêter le thread de traitement
            self.traitement_thread.terminate()
            self.traitement_thread.wait()
            
        event.accept()


def main():
    """Fonction principale"""
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    # Configurer l'application
    app.setApplicationName("DoublonsIDPP")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("PJGN/FAED")
    
    # Ne pas imposer de style global pour respecter le thème système
    
    try:
        # Créer et afficher la fenêtre principale
        window = DoublonsIDPPGUI()
        window.show()
        
        # Démarrer la boucle d'événements
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()