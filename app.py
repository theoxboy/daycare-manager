# app.py (Version avec CRUD complet et API Présence/Documents)

import os
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory
import json
from werkzeug.utils import secure_filename
import time
import datetime
import calendar

# --- Configuration de Flask ---
app = Flask(__name__, template_folder='.', static_folder='uploads')
app.config['DATABASE'] = 'daycare.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.json.ensure_ascii = False

# Créer le dossier uploads s'il n'existe pas
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
        print(f"Dossier créé : {app.config['UPLOAD_FOLDER']}")
    except OSError as e:
        print(f"Erreur lors de la création du dossier {app.config['UPLOAD_FOLDER']}: {e}")
        exit(1)

# --- Fonctions de Base de Données ---

def get_db():
    """Établit une connexion à la base de données."""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        raise

def init_db():
    """Initialise le schéma de la base de données (crée les tables)."""
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        # Table Enfants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS children (
                id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL, last_name TEXT NOT NULL, dob TEXT,
                parent_id INTEGER, emergency_contact TEXT, allergies TEXT, notes TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
                FOREIGN KEY (parent_id) REFERENCES parents (id) ON DELETE SET NULL )
        ''')
        # Table Parents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parents ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                phone TEXT, email TEXT UNIQUE, address TEXT )
        ''')
        # Table Revenus
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS income ( id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
                source TEXT NOT NULL, amount REAL NOT NULL CHECK(amount >= 0), related_child_id INTEGER,
                related_parent_id INTEGER, description TEXT, bc_month TEXT,
                FOREIGN KEY (related_child_id) REFERENCES children (id) ON DELETE SET NULL,
                FOREIGN KEY (related_parent_id) REFERENCES parents (id) ON DELETE SET NULL )
        ''')
        # Table Dépenses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses ( id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
                category TEXT NOT NULL, amount REAL NOT NULL CHECK(amount >= 0), vendor TEXT, description TEXT,
                receipt_filename TEXT,
                is_personal INTEGER DEFAULT 0 CHECK(is_personal IN (0, 1)) )
        ''')
        # Table Présences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance ( id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
                child_id INTEGER NOT NULL, status TEXT NOT NULL, notes TEXT, UNIQUE(date, child_id),
                FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE )
        ''')
        # Table Documents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents ( id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
                description TEXT, upload_date TEXT NOT NULL, filename TEXT NOT NULL UNIQUE, filepath TEXT NOT NULL )
        ''')
        # Table Paramètres
        cursor.execute(''' CREATE TABLE IF NOT EXISTS settings ( key TEXT PRIMARY KEY, value TEXT ) ''')
        # Paramètres par défaut
        default_settings = { 'daycare_name': 'اسم الحضانة الافتراضي', 'daycare_type': 'rsge', 'home_usage': '80', 'car_usage': '20', 'neq_number': '', 'insurance_policy_number': '', 'insurance_expiry_date': '' }
        for key, value in default_settings.items():
             cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
        db.commit()
        print("Base de données initialisée avec succès.")
    except sqlite3.Error as e:
        print(f"Erreur d'initialisation de la base de données : {e}")
        if db: db.rollback()
    finally:
        if db: db.close()

# --- Helper Functions (Get by ID) ---
def get_child_by_id(child_id):
     db = None; conn_created = False
     try:
         db = get_db(); conn_created=True; cursor = db.cursor(); cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,)); child = cursor.fetchone(); db.close(); conn_created=False
         return dict(child) if child else None
     except Exception as e: print(f"Erreur get_child_by_id: {e}"); return None
     finally:
         if conn_created and db: db.close()

def get_parent_by_id(parent_id):
     db = None; conn_created = False
     try:
         db = get_db(); conn_created=True; cursor = db.cursor(); cursor.execute("SELECT * FROM parents WHERE id = ?", (parent_id,)); parent = cursor.fetchone(); db.close(); conn_created=False
         return dict(parent) if parent else None
     except Exception as e: print(f"Erreur get_parent_by_id: {e}"); return None
     finally:
         if conn_created and db: db.close()

def get_income_by_id(income_id):
     db = None; conn_created = False
     try:
         db = get_db(); conn_created=True; cursor = db.cursor(); cursor.execute("SELECT * FROM income WHERE id = ?", (income_id,)); income = cursor.fetchone(); db.close(); conn_created=False
         return dict(income) if income else None
     except Exception as e: print(f"Erreur get_income_by_id: {e}"); return None
     finally:
         if conn_created and db: db.close()

def get_expense_by_id(expense_id):
     db = None; conn_created = False
     try:
         db = get_db(); conn_created=True; cursor = db.cursor(); cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)); expense = cursor.fetchone(); db.close(); conn_created=False
         return dict(expense) if expense else None
     except Exception as e: print(f"Erreur get_expense_by_id: {e}"); return None
     finally:
         if conn_created and db: db.close()

def get_document_by_id(doc_id):
     db = None; conn_created = False
     try:
         db = get_db(); conn_created=True; cursor = db.cursor(); cursor.execute("SELECT id, type, description, upload_date, filename FROM documents WHERE id = ?", (doc_id,)); doc = cursor.fetchone(); db.close(); conn_created=False
         return dict(doc) if doc else None
     except Exception as e: print(f"Erreur get_document_by_id: {e}"); return None
     finally:
         if conn_created and db: db.close()

# --- Routes API ---

@app.route('/')
def index():
    return render_template('index.html')

# --- API Résumé Dashboard ---
@app.route('/api/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    db = None
    try:
        today = datetime.date.today()
        first_day_str = today.replace(day=1).strftime('%Y-%m-%d')
        last_day_num = calendar.monthrange(today.year, today.month)[1]
        last_day_str = today.replace(day=last_day_num).strftime('%Y-%m-%d')
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT SUM(amount) FROM income WHERE date >= ? AND date <= ?", (first_day_str, last_day_str))
        monthly_income = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date >= ? AND date <= ? AND is_personal = 0", (first_day_str, last_day_str))
        monthly_expenses = cursor.fetchone()[0] or 0
        db.close(); db = None
        return jsonify({"monthly_income": monthly_income, "monthly_expenses": monthly_expenses})
    except Exception as e:
        print(f"Erreur get_dashboard_summary : {e}")
        if db: db.close()
        return jsonify({"monthly_income": 0, "monthly_expenses": 0, "error": str(e)}), 500

# --- API Enfants ---
@app.route('/api/children', methods=['GET'])
def get_children():
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute("SELECT * FROM children ORDER BY last_name, first_name"); children = [dict(row) for row in cursor.fetchall()]; db.close()
        return jsonify(children)
    except Exception as e: print(f"Erreur get_children : {e}"); return jsonify({"error": "Erreur serveur lors de la récupération des enfants"}), 500

@app.route('/api/children/<int:child_id>', methods=['GET'])
def get_single_child(child_id):
    child = get_child_by_id(child_id)
    if child: return jsonify(child)
    else: return jsonify({"error": "Enfant non trouvé"}), 404

@app.route('/api/children', methods=['POST'])
def add_child():
    data = request.get_json(); db = None
    if not data or not data.get('firstName') or not data.get('lastName'): return jsonify({"error": "Prénom et nom requis"}), 400
    parent_id = data.get('parentId'); parent_id = int(parent_id) if parent_id else None
    sql = ''' INSERT INTO children(first_name, last_name, dob, parent_id, emergency_contact, allergies, notes, status) VALUES(?,?,?,?,?,?,?,?) '''
    params = ( data['firstName'], data['lastName'], data.get('dob'), parent_id, data.get('emergencyContact'), data.get('allergies'), data.get('notes'), 'active' )
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit(); new_child_id = cursor.lastrowid; db.close(); db = None
        new_child = get_child_by_id(new_child_id)
        return jsonify(new_child if new_child else {"id": new_child_id, "message": "Enfant ajouté"}), 201
    except sqlite3.IntegrityError as e:
        if db: db.rollback(); db.close(); print(f"Erreur intégrité add_child : {e}"); return jsonify({"error": f"Donnée invalide (ex: parentId inexistant?): {e}"}), 400
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur add_child : {e}"); return jsonify({"error": "Erreur serveur lors de l'ajout de l'enfant"}), 500

@app.route('/api/children/<int:child_id>', methods=['PUT'])
def update_child(child_id):
    data = request.get_json(); db = None
    if not data: return jsonify({"error": "Données manquantes"}), 400
    parent_id = data.get('parentId'); parent_id = int(parent_id) if parent_id else None
    sql = ''' UPDATE children SET first_name=?, last_name=?, dob=?, parent_id=?, emergency_contact=?, allergies=?, notes=? WHERE id=? '''
    params = ( data.get('firstName'), data.get('lastName'), data.get('dob'), parent_id, data.get('emergencyContact'), data.get('allergies'), data.get('notes'), child_id )
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Enfant non trouvé"}), 404
        db.close(); db = None
        updated_child = get_child_by_id(child_id)
        return jsonify(updated_child), 200
    except sqlite3.IntegrityError as e:
        if db: db.rollback(); db.close(); print(f"Erreur intégrité update_child : {e}"); return jsonify({"error": f"Donnée invalide (ex: parentId inexistant?): {e}"}), 400
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur update_child : {e}"); return jsonify({"error": "Erreur serveur lors de la mise à jour de l'enfant"}), 500

@app.route('/api/children/<int:child_id>/status', methods=['PUT'])
def update_child_status(child_id):
    data = request.get_json(); db = None
    new_status = data.get('status')
    if new_status not in ['active', 'inactive']: return jsonify({"error": "Statut invalide"}), 400
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute("UPDATE children SET status=? WHERE id=?", (new_status, child_id)); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Enfant non trouvé"}), 404
        db.close(); db = None
        return jsonify({"message": f"Statut de l'enfant {child_id} mis à jour à {new_status}"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur update_child_status : {e}"); return jsonify({"error": "Erreur serveur lors de la mise à jour du statut"}), 500

@app.route('/api/children/<int:child_id>', methods=['DELETE'])
def delete_child(child_id):
    db = None
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute("DELETE FROM children WHERE id=?", (child_id,)); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Enfant non trouvé"}), 404
        db.close(); db = None
        return jsonify({"message": f"Enfant {child_id} supprimé"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur delete_child : {e}"); return jsonify({"error": "Erreur serveur lors de la suppression de l'enfant"}), 500

# --- API Parents ---
@app.route('/api/parents', methods=['GET'])
def get_parents():
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute("SELECT * FROM parents ORDER BY name"); parents = [dict(row) for row in cursor.fetchall()]; db.close()
        return jsonify(parents)
    except Exception as e: print(f"Erreur get_parents : {e}"); return jsonify({"error": "Erreur serveur lors de la récupération des parents"}), 500

@app.route('/api/parents/<int:parent_id>', methods=['GET'])
def get_single_parent(parent_id):
    parent = get_parent_by_id(parent_id)
    if parent: return jsonify(parent)
    else: return jsonify({"error": "Parent non trouvé"}), 404

@app.route('/api/parents', methods=['POST'])
def add_parent():
    data = request.get_json(); db = None
    if not data or not data.get('name'): return jsonify({"error": "Nom du parent requis"}), 400
    sql = ''' INSERT INTO parents(name, phone, email, address) VALUES(?,?,?,?) '''
    params = (data['name'], data.get('phone'), data.get('email'), data.get('address'))
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit(); new_parent_id = cursor.lastrowid; db.close(); db = None
        new_parent = get_parent_by_id(new_parent_id)
        return jsonify(new_parent if new_parent else {"id": new_parent_id, "message": "Parent ajouté"}), 201
    except sqlite3.IntegrityError as e:
        if db: db.rollback(); db.close(); print(f"Erreur intégrité add_parent : {e}"); return jsonify({"error": f"Impossible d'ajouter le parent. L'email existe peut-être déjà: {e}"}), 409
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur add_parent : {e}"); return jsonify({"error": "Erreur serveur lors de l'ajout du parent"}), 500

@app.route('/api/parents/<int:parent_id>', methods=['PUT'])
def update_parent(parent_id):
    data = request.get_json(); db = None
    if not data: return jsonify({"error": "Données manquantes"}), 400
    sql = ''' UPDATE parents SET name=?, phone=?, email=?, address=? WHERE id=? '''
    params = ( data.get('name'), data.get('phone'), data.get('email'), data.get('address'), parent_id )
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Parent non trouvé"}), 404
        db.close(); db = None
        updated_parent = get_parent_by_id(parent_id)
        return jsonify(updated_parent), 200
    except sqlite3.IntegrityError as e:
        if db: db.rollback(); db.close(); print(f"Erreur intégrité update_parent : {e}"); return jsonify({"error": f"Impossible de mettre à jour. L'email existe peut-être déjà pour un autre parent: {e}"}), 409
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur update_parent : {e}"); return jsonify({"error": "Erreur serveur lors de la mise à jour du parent"}), 500

@app.route('/api/parents/<int:parent_id>', methods=['DELETE'])
def delete_parent(parent_id):
    db = None
    try:
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM children WHERE parent_id = ?", (parent_id,))
        count = cursor.fetchone()[0]
        if count > 0: db.close(); return jsonify({"error": "Impossible de supprimer le parent car il est lié à un ou plusieurs enfants."}), 409
        cursor.execute("DELETE FROM parents WHERE id=?", (parent_id,)); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Parent non trouvé"}), 404
        db.close(); db = None
        return jsonify({"message": f"Parent {parent_id} supprimé"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur delete_parent : {e}"); return jsonify({"error": "Erreur serveur lors de la suppression du parent"}), 500


# --- API Revenus ---
@app.route('/api/income', methods=['GET'])
def get_income():
    date_from = request.args.get('from'); date_to = request.args.get('to'); source = request.args.get('source')
    query = "SELECT i.*, c.first_name, c.last_name FROM income i LEFT JOIN children c ON i.related_child_id = c.id WHERE 1=1"
    params = []
    if date_from: query += " AND i.date >= ?"; params.append(date_from)
    if date_to: query += " AND i.date <= ?"; params.append(date_to)
    if source: query += " AND i.source = ?"; params.append(source)
    query += " ORDER BY i.date DESC"
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(query, params); income_records = [dict(row) for row in cursor.fetchall()]; db.close()
        return jsonify(income_records)
    except Exception as e: print(f"Erreur get_income : {e}"); return jsonify({"error": "Erreur serveur lors de la récupération des revenus"}), 500

@app.route('/api/income/<int:income_id>', methods=['GET'])
def get_single_income(income_id):
     income = get_income_by_id(income_id)
     if income: return jsonify(income)
     else: return jsonify({"error": "Revenu non trouvé"}), 404

@app.route('/api/income', methods=['POST'])
def add_income():
    data = request.get_json(); db = None
    if not data or not data.get('date') or not data.get('source') or data.get('amount') is None: return jsonify({"error": "Champs requis manquants : date, source, amount"}), 400
    try: amount = float(data['amount']); assert amount >= 0
    except (ValueError, AssertionError): return jsonify({"error": "Montant invalide ou négatif"}), 400
    child_id = data.get('relatedChildId') or None; parent_id = data.get('relatedParentId') or None
    sql = ''' INSERT INTO income(date, source, amount, related_child_id, related_parent_id, description, bc_month) VALUES(?,?,?,?,?,?,?) '''
    params = (data['date'], data['source'], amount, child_id, parent_id, data.get('description'), data.get('bcMonth'))
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit(); new_id = cursor.lastrowid; db.close(); db = None
        new_income = get_income_by_id(new_id)
        return jsonify(new_income if new_income else {"id": new_id, "message": "Revenu ajouté"}), 201
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur add_income : {e}"); return jsonify({"error": "Erreur serveur lors de l'ajout du revenu"}), 500

@app.route('/api/income/<int:income_id>', methods=['PUT'])
def update_income(income_id):
    data = request.get_json(); db = None
    if not data: return jsonify({"error": "Données manquantes"}), 400
    try: amount = float(data['amount']); assert amount >= 0
    except (ValueError, AssertionError): return jsonify({"error": "Montant invalide ou négatif"}), 400
    child_id = data.get('relatedChildId') or None; parent_id = data.get('relatedParentId') or None
    sql = ''' UPDATE income SET date=?, source=?, amount=?, related_child_id=?, related_parent_id=?, description=?, bc_month=? WHERE id=? '''
    params = ( data.get('date'), data.get('source'), amount, child_id, parent_id, data.get('description'), data.get('bcMonth'), income_id )
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Revenu non trouvé"}), 404
        db.close(); db = None
        updated_income = get_income_by_id(income_id)
        return jsonify(updated_income), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur update_income : {e}"); return jsonify({"error": "Erreur serveur lors de la mise à jour du revenu"}), 500

@app.route('/api/income/<int:income_id>', methods=['DELETE'])
def delete_income(income_id):
    db = None
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute("DELETE FROM income WHERE id=?", (income_id,)); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Revenu non trouvé"}), 404
        db.close(); db = None
        return jsonify({"message": f"Revenu {income_id} supprimé"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur delete_income : {e}"); return jsonify({"error": "Erreur serveur lors de la suppression du revenu"}), 500


# --- API Dépenses ---
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    date_from = request.args.get('from'); date_to = request.args.get('to'); category = request.args.get('category')
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if date_from: query += " AND date >= ?"; params.append(date_from)
    if date_to: query += " AND date <= ?"; params.append(date_to)
    if category: query += " AND category = ?"; params.append(category)
    query += " ORDER BY date DESC"
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(query, params); expenses = [dict(row) for row in cursor.fetchall()]; db.close()
        return jsonify(expenses)
    except Exception as e: print(f"Erreur get_expenses : {e}"); return jsonify({"error": "Erreur serveur lors de la récupération des dépenses"}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['GET'])
def get_single_expense(expense_id):
     expense = get_expense_by_id(expense_id)
     if expense: return jsonify(expense)
     else: return jsonify({"error": "Dépense non trouvée"}), 404

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    if 'date' not in request.form or 'category' not in request.form or 'amount' not in request.form: return jsonify({"error": "Champs requis manquants : date, category, amount"}), 400
    try: amount = float(request.form['amount']); assert amount >= 0
    except (ValueError, AssertionError): return jsonify({"error": "Montant invalide ou négatif"}), 400
    date = request.form['date']; category = request.form['category']; vendor = request.form.get('vendor'); description = request.form.get('description')
    is_personal = 1 if request.form.get('is_personal') == 'true' else 0; receipt_filename = None
    if 'receipt' in request.files:
        file = request.files['receipt']
        if file and file.filename:
            try:
                filename_base, filename_ext = os.path.splitext(file.filename); timestamp = int(time.time())
                receipt_filename = f"{secure_filename(filename_base)}_{timestamp}{filename_ext}"
                receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename); file.save(receipt_path)
                print(f"Reçu sauvegardé : {receipt_filename}")
            except Exception as e: print(f"Erreur sauvegarde reçu : {e}"); return jsonify({"error": f"Impossible de sauvegarder le fichier reçu : {e}"}), 500
    sql = ''' INSERT INTO expenses(date, category, amount, vendor, description, receipt_filename, is_personal) VALUES(?,?,?,?,?,?,?) '''
    params = (date, category, amount, vendor, description, receipt_filename, is_personal); db = None
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit(); new_id = cursor.lastrowid; db.close(); db = None
        new_expense = get_expense_by_id(new_id)
        return jsonify(new_expense if new_expense else {"id": new_id, "message": "Dépense ajoutée"}), 201
    except Exception as e:
        if db: db.rollback()
        if receipt_filename: # Cleanup orphaned file
             receipt_path_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
             if os.path.exists(receipt_path_to_delete):
                 try: os.remove(receipt_path_to_delete); print(f"Fichier reçu orphelin supprimé: {receipt_filename}")
                 except OSError as remove_error: print(f"Erreur suppression fichier orphelin {receipt_filename}: {remove_error}")
        print(f"Erreur add_expense : {e}"); return jsonify({"error": "Erreur serveur lors de l'ajout de la dépense"}), 500
    finally:
         if db: db.close()

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    # Note: This version does not handle changing the receipt file
    data = request.get_json(); db = None
    if not data: return jsonify({"error": "Données manquantes"}), 400
    try: amount = float(data['amount']); assert amount >= 0
    except (ValueError, AssertionError): return jsonify({"error": "Montant invalide ou négatif"}), 400
    is_personal = 1 if data.get('is_personal') else 0 # Assuming JS sends boolean or null
    sql = ''' UPDATE expenses SET date=?, category=?, amount=?, vendor=?, description=?, is_personal=? WHERE id=? '''
    params = ( data.get('date'), data.get('category'), amount, data.get('vendor'), data.get('description'), is_personal, expense_id )
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Dépense non trouvée"}), 404
        db.close(); db = None
        updated_expense = get_expense_by_id(expense_id)
        return jsonify(updated_expense), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur update_expense : {e}"); return jsonify({"error": "Erreur serveur lors de la mise à jour de la dépense"}), 500

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    db = None; filename_to_delete = None
    try:
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT receipt_filename FROM expenses WHERE id = ?", (expense_id,)); result = cursor.fetchone()
        if result: filename_to_delete = result['receipt_filename']
        else: db.close(); return jsonify({"error": "Dépense non trouvée"}), 404
        cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,)); db.commit(); db.close(); db = None
        if filename_to_delete:
            filepath_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete)
            if os.path.exists(filepath_to_delete):
                try: os.remove(filepath_to_delete); print(f"Fichier reçu supprimé : {filename_to_delete}")
                except OSError as e: print(f"Erreur suppression fichier reçu {filename_to_delete}: {e}")
            else: print(f"Fichier reçu non trouvé pour suppression : {filename_to_delete}")
        return jsonify({"message": f"Dépense {expense_id} supprimée"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur delete_expense : {e}"); return jsonify({"error": "Erreur serveur lors de la suppression de la dépense"}), 500

# --- API Présences ---
@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    date = request.args.get('date')
    if not date: return jsonify({"error": "Paramètre 'date' manquant"}), 400
    db = None
    try:
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT child_id, status, notes FROM attendance WHERE date = ?", (date,))
        attendance_records = {row['child_id']: dict(row) for row in cursor.fetchall()}
        db.close(); db = None
        return jsonify(attendance_records)
    except Exception as e:
        if db: db.close(); print(f"Erreur get_attendance : {e}"); return jsonify({"error": "Erreur serveur lors de la récupération des présences"}), 500

@app.route('/api/attendance', methods=['POST'])
def save_attendance():
    data = request.get_json(); db = None
    if not data or 'date' not in data or 'attendance' not in data: return jsonify({"error": "Données manquantes : date ou attendance"}), 400
    attendance_date = data['date']; attendance_records = data['attendance']
    try:
        db = get_db(); cursor = db.cursor()
        for child_id_str, record in attendance_records.items():
            try:
                child_id = int(child_id_str); status = record.get('status'); notes = record.get('notes')
                if not status: continue
                cursor.execute('INSERT OR REPLACE INTO attendance (date, child_id, status, notes) VALUES (?, ?, ?, ?)', (attendance_date, child_id, status, notes))
            except ValueError: print(f"ID enfant invalide reçu : {child_id_str}"); continue
            except Exception as inner_e: print(f"Erreur traitement enregistrement présence pour enfant {child_id_str}: {inner_e}")
        db.commit(); db.close(); db = None
        return jsonify({"message": "Présences enregistrées avec succès"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur save_attendance : {e}"); return jsonify({"error": "Erreur serveur lors de l'enregistrement des présences"}), 500

# --- API Documents ---
@app.route('/api/documents', methods=['GET'])
def get_documents():
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute("SELECT id, type, description, upload_date, filename FROM documents ORDER BY upload_date DESC"); documents = [dict(row) for row in cursor.fetchall()]; db.close()
        return jsonify(documents)
    except Exception as e: print(f"Erreur get_documents : {e}"); return jsonify({"error": "Erreur serveur lors de la récupération des documents"}), 500

@app.route('/api/documents/<int:doc_id>', methods=['GET'])
def get_single_document(doc_id):
     doc = get_document_by_id(doc_id)
     if doc: return jsonify(doc)
     else: return jsonify({"error": "Document non trouvé"}), 404

@app.route('/api/documents', methods=['POST'])
def add_document():
    if 'type' not in request.form or 'document' not in request.files: return jsonify({"error": "Type de document et fichier requis"}), 400
    doc_type = request.form['type']; description = request.form.get('description'); file = request.files['document']
    if file.filename == '': return jsonify({"error": "Aucun fichier sélectionné"}), 400
    doc_filename = None; doc_filepath_full = None
    if file:
        try:
            filename_base, filename_ext = os.path.splitext(file.filename); timestamp = int(time.time())
            doc_filename = f"doc_{secure_filename(filename_base)}_{timestamp}{filename_ext}"
            doc_filepath_full = os.path.join(app.config['UPLOAD_FOLDER'], doc_filename); file.save(doc_filepath_full)
            print(f"Document sauvegardé : {doc_filename}")
        except Exception as e: print(f"Erreur sauvegarde document : {e}"); return jsonify({"error": f"Impossible de sauvegarder le fichier document : {e}"}), 500
    upload_date = datetime.date.today().strftime('%Y-%m-%d'); filepath_relative = doc_filename
    sql = ''' INSERT INTO documents(type, description, upload_date, filename, filepath) VALUES(?,?,?,?,?) '''
    params = (doc_type, description, upload_date, doc_filename, filepath_relative); db = None
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit(); new_id = cursor.lastrowid; db.close(); db = None
        new_doc = get_document_by_id(new_id)
        return jsonify(new_doc if new_doc else {"id": new_id, "message": "Document ajouté"}), 201
    except Exception as e:
        if db: db.rollback()
        if doc_filepath_full and os.path.exists(doc_filepath_full):
             try: os.remove(doc_filepath_full); print(f"Fichier document orphelin supprimé: {doc_filename}")
             except OSError as remove_error: print(f"Erreur suppression fichier orphelin {doc_filename}: {remove_error}")
        print(f"Erreur add_document : {e}"); return jsonify({"error": "Erreur serveur lors de l'ajout du document"}), 500
    finally:
         if db: db.close()

@app.route('/api/documents/<int:doc_id>', methods=['PUT'])
def update_document(doc_id):
    # Allows updating type and description, not the file itself
    data = request.get_json(); db = None
    if not data: return jsonify({"error": "Données manquantes"}), 400
    sql = ''' UPDATE documents SET type=?, description=? WHERE id=? '''
    params = ( data.get('type'), data.get('description'), doc_id )
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute(sql, params); db.commit()
        if cursor.rowcount == 0: db.close(); return jsonify({"error": "Document non trouvé"}), 404
        db.close(); db = None
        updated_doc = get_document_by_id(doc_id)
        return jsonify(updated_doc), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur update_document : {e}"); return jsonify({"error": "Erreur serveur lors de la mise à jour du document"}), 500

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    db = None; filename_to_delete = None
    try:
        db = get_db(); cursor = db.cursor()
        cursor.execute("SELECT filename FROM documents WHERE id = ?", (doc_id,)); result = cursor.fetchone()
        if result: filename_to_delete = result['filename']
        else: db.close(); return jsonify({"error": "Document non trouvé"}), 404
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,)); db.commit(); db.close(); db = None
        if filename_to_delete:
            filepath_to_delete = os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete)
            if os.path.exists(filepath_to_delete):
                try: os.remove(filepath_to_delete); print(f"Fichier document supprimé : {filename_to_delete}")
                except OSError as e: print(f"Erreur lors de la suppression du fichier {filename_to_delete}: {e}")
            else: print(f"Fichier document non trouvé pour suppression : {filename_to_delete}")
        return jsonify({"message": "Document supprimé avec succès"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur delete_document : {e}"); return jsonify({"error": "Erreur serveur lors de la suppression du document"}), 500


# --- API Paramètres ---
@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        db = get_db(); cursor = db.cursor(); cursor.execute("SELECT key, value FROM settings"); settings = {row['key']: row['value'] for row in cursor.fetchall()}; db.close()
        return jsonify(settings)
    except Exception as e: print(f"Erreur get_settings : {e}"); return jsonify({"error": "Erreur serveur lors de la récupération des paramètres"}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.get_json(); db = None
    if not data: return jsonify({"error": "Aucune donnée fournie"}), 400
    try:
        db = get_db(); cursor = db.cursor()
        for key, value in data.items():
            if not isinstance(key, str) or not key.replace('_', '').isalnum(): print(f"Clé de paramètre invalide : {key}"); continue
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        db.commit(); db.close(); db = None
        return jsonify({"message": "Paramètres mis à jour avec succès"}), 200
    except Exception as e:
        if db: db.rollback(); db.close(); print(f"Erreur update_settings : {e}"); return jsonify({"error": "Erreur serveur lors de la mise à jour des paramètres"}), 500

# --- Route pour servir les fichiers téléversés ---
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        safe_filename = secure_filename(filename)
        return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename, as_attachment=False)
    except FileNotFoundError: print(f"Fichier non trouvé : {filename}"); return jsonify({"error": "Fichier non trouvé"}), 404
    except Exception as e: print(f"Erreur service fichier {filename}: {e}"); return jsonify({"error": "Erreur lors de la récupération du fichier"}), 500

# --- Exécution principale ---
if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']): print("Fichier de base de données non trouvé, initialisation..."); init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)