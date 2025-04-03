@echo off
REM Ce script lance le serveur Flask pour l'application Garderie.

echo Navigation vers le dossier du projet...
REM Utilise /d pour changer de lecteur si nécessaire
cd "C:\Projets\daycare-manager"

echo Lancement du serveur Python (app.py)...
REM Assurez-vous que python est dans votre PATH
python app.py

echo Le serveur s'est arrete ou n'a pas pu demarrer. Appuyez sur une touche pour fermer cette fenetre.
pause
