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
                             QLineEdit, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

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
        
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("DoublonsIDPP - Traitement des Doublons de Signalisations")
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title_label = QLabel("DoublonsIDPP - Traitement des Doublons")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #003366; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Sous-titre
        subtitle_label = QLabel("Interface graphique pour l'analyse et le traitement des doublons de signalisations")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)
        
        # Ligne de séparation
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Section 1: Sélection du fichier CSV
        csv_group = QGroupBox("1. Sélection du fichier CSV à traiter")
        csv_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        csv_layout = QVBoxLayout(csv_group)
        
        csv_selection_layout = QHBoxLayout()
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setPlaceholderText("Aucun fichier sélectionné...")
        self.csv_path_edit.setReadOnly(True)
        csv_selection_layout.addWidget(self.csv_path_edit)
        
        self.btn_select_csv = QPushButton("Parcourir...")
        self.btn_select_csv.clicked.connect(self.select_csv_file)
        self.btn_select_csv.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        csv_selection_layout.addWidget(self.btn_select_csv)
        
        csv_layout.addLayout(csv_selection_layout)
        
        # Informations sur le fichier CSV
        self.csv_info_label = QLabel("Sélectionnez un fichier CSV contenant les signalisations à analyser.")
        self.csv_info_label.setStyleSheet("color: #666666; font-style: italic;")
        csv_layout.addWidget(self.csv_info_label)
        
        main_layout.addWidget(csv_group)
        
        # Section 2: Destination des exports
        export_group = QGroupBox("2. Destination des fichiers d'export")
        export_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        export_layout = QVBoxLayout(export_group)
        
        export_selection_layout = QHBoxLayout()
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setPlaceholderText("Aucun dossier sélectionné...")
        self.export_path_edit.setReadOnly(True)
        export_selection_layout.addWidget(self.export_path_edit)
        
        self.btn_select_export = QPushButton("Parcourir...")
        self.btn_select_export.clicked.connect(self.select_export_directory)
        self.btn_select_export.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        export_selection_layout.addWidget(self.btn_select_export)
        
        export_layout.addLayout(export_selection_layout)
        
        # Informations sur l'export
        self.export_info_label = QLabel("Choisissez le dossier où seront enregistrés les rapports d'analyse.")
        self.export_info_label.setStyleSheet("color: #666666; font-style: italic;")
        export_layout.addWidget(self.export_info_label)
        
        main_layout.addWidget(export_group)
        
        # Section 3: Lancement du traitement
        process_group = QGroupBox("3. Lancement du traitement")
        process_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        process_layout = QVBoxLayout(process_group)
        
        # Bouton de traitement
        self.btn_process = QPushButton("Lancer l'analyse des doublons")
        self.btn_process.clicked.connect(self.start_processing)
        self.btn_process.setEnabled(False)
        self.btn_process.setMinimumHeight(40)
        self.btn_process.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        process_layout.addWidget(self.btn_process)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 3px;
            }
        """)
        process_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(process_group)
        
        # Zone de logs
        logs_group = QGroupBox("Journal d'activité")
        logs_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        logs_layout = QVBoxLayout(logs_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        self.log_message("Interface initialisée. Prêt à traiter les doublons.")
        logs_layout.addWidget(self.log_text)
        
        main_layout.addWidget(logs_group)
        
        # Footer
        footer_label = QLabel("© 2025 GND Yoann BAUDRIN - PJGN/FAED")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #999999; font-size: 10px; margin-top: 10px;")
        main_layout.addWidget(footer_label)
        
        # Vérifier les fichiers à l'initialisation
        self.check_ready_to_process()
        
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
                    self.csv_info_label.setStyleSheet("color: #28a745; font-style: italic;")
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
        self.btn_process.setEnabled(enabled and self.chemin_fichier_csv and self.dossier_exports)
        
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