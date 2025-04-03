# Garderieapp2 – Application de gestion pour services de garde (RSGE/SGMF)

> Développé de A à Z par **OMAR EL IDRISSI**  
> 📸 [Instagram](https://www.instagram.com/theoxboy/) • 🌐 [Portfolio](http://www.omarelidrissi.com)

## 📌 Description
Garderieapp2 est une application web locale développée en **Python (Flask)** avec une interface utilisateur en **HTML/TailwindCSS**. Elle permet la gestion administrative et financière d’un service de garde au Québec, incluant la gestion des enfants, présences, dépenses, revenus, rappels, et documents justificatifs.

## ✨ Fonctionnalités principales
- Dashboard interactif
- Gestion des enfants et des parents
- Suivi des présences journalières
- Suivi des revenus et dépenses
- Téléversement de fichiers (reçus et documents)
- Estimation des taxes (TPS, TVQ, RRQ, RQAP)
- Rappels avec sanctions

## 🛠️ Technologies utilisées
- Backend : Python (Flask)
- Frontend : HTML, TailwindCSS, JavaScript
- Base de données : SQLite
- Téléversement de fichiers : dossier `uploads/`

## 📂 Arborescence du projet

```
Garderieapp2/
├── app.py               # Backend Flask
├── index.html           # Interface utilisateur
├── daycare.db           # Base de données SQLite
├── uploads/             # Fichiers téléversés (reçus, documents)
├── Lancer_Garderie.cmd  # Lanceur Windows
├── README.md            # Fichier de documentation
├── .gitignore           # Fichiers/dossiers à ignorer
└── requirements.txt     # Dépendances Python
```

## 🚀 Lancer l'application

### 1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

### 2. Lancer l'application :
- Sous Windows : double-cliquer sur `Lancer_Garderie.cmd`
- Sinon :
```bash
python app.py
```

### 3. Accès :
Ouvrir votre navigateur à l’adresse :
```
http://127.0.0.1:5000
```

## 🔐 Améliorations futures
- Ajout d’une authentification
- Ajout d’une interface de recherche et de filtrage avancée
- Possibilité de générer des rapports PDF

---

🧠 Projet conçu et développé intégralement par [**OMAR EL IDRISSI**](http://www.omarelidrissi.com)  
📲 Suivez-moi sur [Instagram](https://www.instagram.com/theoxboy/)  
🎯 Merci d’utiliser Garderieapp2 ! Vos retours sont les bienvenus.