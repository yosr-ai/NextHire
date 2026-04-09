import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

try:
    import psycopg2
    import_error = None
except ImportError as e:
    psycopg2 = None
    import_error = str(e)

# ==========================================
# SCRIPT DE CRÉATION DE LA BASE DE DONNÉES
# ==========================================
# Ce fichier crée TOUTES les tables nécessaires pour les 6 sprints du projet.
# On l'exécute UNE SEULE FOIS au début (ou quand on veut tout réinitialiser).

IS_POSTGRES = 'DATABASE_URL' in os.environ

if IS_POSTGRES:
    print("Initiating PostgreSQL Database...")
    if not psycopg2:
        print("Error: psycopg2 is not installed!")
        sys.exit(1)
    connexion = psycopg2.connect(os.environ['DATABASE_URL'])
    curseur = connexion.cursor()
    # PostgreSQL syntax
    TYPE_SERIAL = "SERIAL PRIMARY KEY"
    TYPE_DATETIME_DEFAULT = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    
    # Drop existing tables to refresh content
    curseur.execute("DROP TABLE IF EXISTS entretiens, candidatures, offres, utilisateurs CASCADE;")
else:
    print("Initiating SQLite Database...")
    db_path = os.environ.get('DATABASE_PATH', 'recrutement_simple.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Ancienne base supprimée ({db_path}).")
    connexion = sqlite3.connect(db_path)
    curseur = connexion.cursor()
    # SQLite syntax
    TYPE_SERIAL = "INTEGER PRIMARY KEY AUTOINCREMENT"
    TYPE_DATETIME_DEFAULT = "TEXT DEFAULT (datetime('now'))"

def execute(query, params=()):
    if IS_POSTGRES:
        curseur.execute(query.replace('?', '%s'), params)
    else:
        curseur.execute(query, params)

def executemany(query, params_list):
    if IS_POSTGRES:
        curseur.executemany(query.replace('?', '%s'), params_list)
    else:
        curseur.executemany(query, params_list)

# ==========================================
# SPRINT 1 : TABLE DES UTILISATEURS
# ==========================================
execute(f'''
CREATE TABLE IF NOT EXISTS utilisateurs (
    id              {TYPE_SERIAL},
    nom_utilisateur TEXT NOT NULL UNIQUE,
    email           TEXT NOT NULL UNIQUE,
    mot_de_passe    TEXT NOT NULL,
    role            TEXT NOT NULL,
    profil_cv       TEXT,
    telephone       TEXT,
    date_creation   {TYPE_DATETIME_DEFAULT}
)
''')

# ==========================================
# SPRINT 2 : TABLE DES OFFRES D'EMPLOI
# ==========================================
execute(f'''
CREATE TABLE IF NOT EXISTS offres (
    id              {TYPE_SERIAL},
    titre           TEXT NOT NULL,
    description     TEXT NOT NULL,
    localisation    TEXT,
    type_contrat    TEXT,
    salaire         TEXT,
    statut          TEXT DEFAULT 'Ouverte',
    recruteur_id    INTEGER NOT NULL,
    date_creation   {TYPE_DATETIME_DEFAULT},
    FOREIGN KEY(recruteur_id) REFERENCES utilisateurs(id)
)
''')

# ==========================================
# SPRINT 3 : TABLE DES CANDIDATURES
# ==========================================
execute(f'''
CREATE TABLE IF NOT EXISTS candidatures (
    id              {TYPE_SERIAL},
    candidat_id     INTEGER NOT NULL,
    offre_id        INTEGER NOT NULL,
    lettre_motivation TEXT,
    statut          TEXT DEFAULT 'En attente',
    date_postulation {TYPE_DATETIME_DEFAULT},
    FOREIGN KEY(candidat_id) REFERENCES utilisateurs(id),
    FOREIGN KEY(offre_id) REFERENCES offres(id),
    UNIQUE(candidat_id, offre_id)
)
''')

# ==========================================
# SPRINT 4 : TABLE DES ENTRETIENS
# ==========================================
execute(f'''
CREATE TABLE IF NOT EXISTS entretiens (
    id              {TYPE_SERIAL},
    candidature_id  INTEGER NOT NULL,
    date_entretien  TEXT NOT NULL,
    lieu            TEXT,
    notes           TEXT,
    date_creation   {TYPE_DATETIME_DEFAULT},
    FOREIGN KEY(candidature_id) REFERENCES candidatures(id)
)
''')

# ==========================================
# DONNÉES DE DÉMONSTRATION (optionnel)
# ==========================================
comptes_test = [
    ('admin',     'admin@nexthire.com',     generate_password_hash('admin123'),     'Admin',     None, None),
    ('rh_marie',  'marie@nexthire.com',     generate_password_hash('rh123'),        'RH',        None, None),
    ('recruteur1','recruteur@nexthire.com', generate_password_hash('recruteur123'), 'Recruteur', None, '0600000001'),
    ('candidat1', 'alice@email.com',        generate_password_hash('alice123'),     'Candidat',
        'Je suis développeuse web junior passionnée par Python et Flask. '
        'Diplômée en informatique, je cherche un stage ou CDI dans le développement back-end.',
        '0666111222'),
]

executemany(
    'INSERT INTO utilisateurs (nom_utilisateur, email, mot_de_passe, role, profil_cv, telephone) VALUES (?,?,?,?,?,?)',
    comptes_test
)

# On crée 2 offres de démonstration
execute(
    'INSERT INTO offres (titre, description, localisation, type_contrat, salaire, recruteur_id) VALUES (?,?,?,?,?,?)',
    ('Développeur Python Junior',
     'Nous recherchons un développeur Python passionné pour rejoindre notre équipe agile. '
     'Vous travaillerez sur des projets Flask/Django. Connaissance de SQLite ou MySQL appréciée.',
     'Casablanca', 'CDI', '8 000 - 12 000 MAD/mois', 3)
)
execute(
    'INSERT INTO offres (titre, description, localisation, type_contrat, salaire, recruteur_id) VALUES (?,?,?,?,?,?)',
    ('Analyste RH - Gestion des talents',
     'Poste d\'analyste RH pour accompagner nos processus de recrutement et de formation. '
     'Bonne maîtrise d\'Excel et des outils RH. Expérience minimum 1 an souhaitée.',
     'Rabat', 'CDI', '7 000 - 9 000 MAD/mois', 3)
)

# On valide tout et on ferme
connexion.commit()
connexion.close()

print("=" * 50)
print("Base de donnees creee avec succes !")
print("   Tables : utilisateurs, offres, candidatures, entretiens")
print()
print("--- Comptes de demonstration ---")
print("  Admin     : admin@nexthire.com       / admin123")
print("  RH        : marie@nexthire.com       / rh123")
print("  Recruteur : recruteur@nexthire.com   / recruteur123")
print("  Candidat  : alice@email.com          / alice123")
print("=" * 50)
