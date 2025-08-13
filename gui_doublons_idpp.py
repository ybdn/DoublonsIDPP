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
                             QLineEdit, QFrame, QSpacerItem, QSizePolicy, QAction,
                             QScrollArea)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSettings, QPointF, QRectF
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QPen, QBrush, QPainterPath
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
        self.current_theme = "light"  # light | dark
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

        # Action raccourci thème
        theme_action = QAction("Basculer thème clair/sombre", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        self.addAction(theme_action)

        # Bouton toggle thème
        self.btn_toggle_theme = QPushButton()
        self.btn_toggle_theme.setToolTip("Basculer thème clair / sombre (Ctrl+T)")
        self.btn_toggle_theme.setFixedSize(40, 40)
        self.btn_toggle_theme.clicked.connect(self.toggle_theme)
        self.btn_toggle_theme.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_theme.setStyleSheet(
            "QPushButton { border: none; background: transparent; }"
            "QPushButton:hover { background: rgba(255,255,255,0.08); border-radius:20px; }"
        )
        self.update_theme_icon()

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
        header_layout.addWidget(self.btn_toggle_theme)
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
        self.log_text.setStyleSheet("""QTextEdit { background-color:rgba(0,0,0,0.03); border:1px solid rgba(0,0,0,0.12); border-radius:6px; font-family:'JetBrains Mono','Courier New',monospace; font-size:11px; padding:6px; }""")
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
        for w in widgets:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(20)
            effect.setXOffset(0)
            effect.setYOffset(4)
            # Couleur adaptée selon thème
            if self.current_theme == "dark":
                effect.setColor(QColor(0, 0, 0, 160))
            else:
                effect.setColor(QColor(0, 0, 0, 50))
            w.setGraphicsEffect(effect)
    
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(self.current_theme)
        self.apply_card_effects([
            *self.findChildren(QGroupBox)
        ])
        self.update_theme_icon()
        self.statusBar().showMessage(f"Thème {self.current_theme}", 3000)
        self.save_settings()
    
    def apply_theme(self, theme):
        """Applique un thème clair ou sombre moderne."""
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
        QPushButton:hover:!disabled {{ background: shade({accent}, 110); }}
        QPushButton:pressed {{ background: shade({accent}, 130); }}
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

    def build_theme_icon(self, theme: str) -> QIcon:
        """Construit un QIcon (soleil ou lune) en vectoriel simple selon le thème cible."""
        size = 64
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)

        if theme == "dark":
            # Afficher une lune (croissant clair) pour indiquer qu'on peut aller vers le thème clair
            outer_rect = QRectF(size*0.18, size*0.14, size*0.56, size*0.56)
            inner_rect = QRectF(size*0.34, size*0.14, size*0.56, size*0.56)
            path_outer = QPainterPath(); path_outer.addEllipse(outer_rect)
            path_inner = QPainterPath(); path_inner.addEllipse(inner_rect)
            crescent = path_outer.subtracted(path_inner)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255,255,255))
            painter.drawPath(crescent)
        else:
            # Soleil (indique possibilité basculer sombre)
            center = QPointF(size/2, size/2)
            radius = size * 0.22
            core_color = QColor(255, 191, 0)
            painter.setPen(Qt.NoPen)
            painter.setBrush(core_color)
            painter.drawEllipse(QRectF(center.x()-radius, center.y()-radius, radius*2, radius*2))
            # Rayons
            painter.setPen(QPen(core_color, size*0.05, Qt.SolidLine, Qt.RoundCap))
            for i in range(12):
                angle = 2 * math.pi * i / 12
                r1 = radius + size*0.06
                r2 = radius + size*0.18
                p1 = QPointF(center.x() + r1*math.cos(angle), center.y() + r1*math.sin(angle))
                p2 = QPointF(center.x() + r2*math.cos(angle), center.y() + r2*math.sin(angle))
                painter.drawLine(p1, p2)

        painter.end()
        return QIcon(pm)

    def update_theme_icon(self):
        self.btn_toggle_theme.setIcon(self.build_theme_icon(self.current_theme))
        self.btn_toggle_theme.setIconSize(self.btn_toggle_theme.size()*0.6)
    
    def load_settings(self):
        """Charge les préférences utilisateur (chemins & thème)."""
        last_csv = self.settings.value("last_csv", "")
        last_export = self.settings.value("last_export", "")
        theme = self.settings.value("theme", "light")
        self.current_theme = theme
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
        self.settings.setValue("theme", self.current_theme)
        
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
    
    # Définir le style global
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ffffff;
        }
        QGroupBox {
            margin-top: 10px;
            padding-top: 10px;
            border: 2px solid #cccccc;
            border-radius: 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QLineEdit {
            padding: 8px;
            border: 2px solid #dee2e6;
            border-radius: 4px;
            font-size: 12px;
        }
        QLineEdit:focus {
            border-color: #0066cc;
        }
    """)
    
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