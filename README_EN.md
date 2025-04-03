# Garderieapp2 – Management App for Quebec Home Daycare Services (RSGE/SGMF)

> Fully developed from scratch by **OMAR EL IDRISSI**  
> 📸 [Instagram](https://www.instagram.com/theoxboy/) • 🌐 [Portfolio](http://www.omarelidrissi.com)

## 📌 Description
**Garderieapp2** is a fully functional web-based platform for managing home daycare operations in Quebec. Built with **Python (Flask)** for the backend and **HTML/TailwindCSS** for the frontend, it provides tools for administrators to manage children, parents, attendance, financial records, reminders, and tax estimations.

## ✨ Features
- Interactive dashboard overview
- Manage children and parents profiles
- Daily attendance tracking
- Income and expenses records
- Upload and manage documents (invoices, certificates, etc.)
- Tax estimation for QPP, QPIP, TPS, TVQ
- Automatic reminders and alerts

## 🛠️ Tech Stack
- **Backend**: Python (Flask)
- **Frontend**: HTML + TailwindCSS + Vanilla JS
- **Database**: SQLite
- **File uploads**: Stored in `/uploads` directory

## 📂 Project Structure

```
Garderieapp2/
├── app.py               # Flask backend (API and DB logic)
├── index.html           # HTML dashboard UI
├── daycare.db           # SQLite database
├── uploads/             # Uploaded files (receipts, docs)
├── Lancer_Garderie.cmd  # Windows launcher script
├── README.md            # Project documentation
├── .gitignore           # Ignored files
└── requirements.txt     # Python dependencies
```

## 🚀 Getting Started

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the application:
- On Windows: double-click `Lancer_Garderie.cmd`
- On other systems:
```bash
python app.py
```

### 3. Open in browser:
```
http://127.0.0.1:5000
```

## 🔐 Future Improvements
- Add login and authentication system
- Enable report export (PDF or CSV)
- Monthly summary and statistics per child
- Add advanced search and filtering tools

---

🧠 Project fully designed and built by [**OMAR EL IDRISSI**](http://www.omarelidrissi.com)  
📲 Follow on [Instagram](https://www.instagram.com/theoxboy/)  
💬 Feedback and contributions are welcome!