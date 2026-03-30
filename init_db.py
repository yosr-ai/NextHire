import sqlite3
import os
from werkzeug.security import generate_password_hash

# ==========================================
# SCRIPT DE CRÉATION DE LA BASE DE DONNÉES
# ==========================================
# Ce fichier crée TOUTES les tables nécessaires pour les 6 sprints du projet.
# On l'exécute UNE SEULE FOIS au début (ou quand on veut tout réinitialiser).

# Supprime l'ancienne base pour repartir à zéro
if os.path.exists('recrutement_simple.db'):
    os.remove('recrutement_simple.db')
    print("Ancienne base supprimée.")

# --- Connexion à la nouvelle base ---
connexion = sqlite3.connect('recrutement_simple.db')
curseur = connexion.cursor()

# ==========================================
# SPRINT 1 : TABLE DES UTILISATEURS
# ==========================================
# Cette table stocke tous les comptes du système.
# 'role' peut être : 'Candidat', 'Recruteur', 'RH', 'Admin'
curseur.execute('''
CREATE TABLE IF NOT EXISTS utilisateurs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_utilisateur TEXT NOT NULL UNIQUE,
    email           TEXT NOT NULL UNIQUE,
    mot_de_passe    TEXT NOT NULL,
    role            TEXT NOT NULL,
    profil_cv       TEXT,       -- Sprint 3 : CV texte du candidat
    telephone       TEXT,       -- Sprint 3 : Téléphone du candidat
    date_creation   TEXT DEFAULT (datetime('now'))
)
''')

# ==========================================
# SPRINT 2 : TABLE DES OFFRES D'EMPLOI
# ==========================================
# Chaque offre est créée par un Recruteur.
# 'statut' peut être : 'Ouverte', 'Fermée'
curseur.execute('''
CREATE TABLE IF NOT EXISTS offres (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    titre           TEXT NOT NULL,
    description     TEXT NOT NULL,
    localisation    TEXT,           -- Ex: "Paris", "Casablanca", "Télétravail"
    type_contrat    TEXT,           -- Ex: "CDI", "CDD", "Stage", "Alternance"
    salaire         TEXT,           -- Ex: "30 000 - 35 000 MAD/an"
    statut          TEXT DEFAULT 'Ouverte', -- 'Ouverte' ou 'Fermée'
    recruteur_id    INTEGER NOT NULL,
    date_creation   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(recruteur_id) REFERENCES utilisateurs(id)
)
''')

# ==========================================
# SPRINT 3 : TABLE DES CANDIDATURES
# ==========================================
# Un candidat postule à une offre => une ligne ici.
# 'statut' peut être : 'En attente', 'Accepté', 'Refusé', 'Entretien planifié'
curseur.execute('''
CREATE TABLE IF NOT EXISTS candidatures (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    candidat_id     INTEGER NOT NULL,
    offre_id        INTEGER NOT NULL,
    lettre_motivation TEXT,  -- Lettre de motivation du candidat
    statut          TEXT DEFAULT 'En attente',
    date_postulation TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(candidat_id) REFERENCES utilisateurs(id),
    FOREIGN KEY(offre_id) REFERENCES offres(id),
    UNIQUE(candidat_id, offre_id) -- Un candidat ne peut postuler qu'une fois par offre
)
''')

# ==========================================
# SPRINT 4 : TABLE DES ENTRETIENS
# ==========================================
# Le recruteur ou RH peut planifier un entretien pour une candidature.
curseur.execute('''
CREATE TABLE IF NOT EXISTS entretiens (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    candidature_id  INTEGER NOT NULL,
    date_entretien  TEXT NOT NULL,  -- Format : 'YYYY-MM-DD HH:MM'
    lieu            TEXT,           -- Ex: "Salle A", "Google Meet", "Teams"
    notes           TEXT,           -- Notes / évaluation après l'entretien
    date_creation   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(candidature_id) REFERENCES candidatures(id)
)
''')

# ==========================================
# DONNÉES DE DÉMONSTRATION (optionnel)
# ==========================================
# On crée 4 comptes de test pour chaque rôle

comptes_test = [
    ('admin',     'admin@nexthire.com',     generate_password_hash('admin123'),     'Admin',     None, None),
    ('rh_marie',  'marie@nexthire.com',     generate_password_hash('rh123'),        'RH',        None, None),
    ('recruteur1','recruteur@nexthire.com', generate_password_hash('recruteur123'), 'Recruteur', None, '0600000001'),
    ('candidat1', 'alice@email.com',        generate_password_hash('alice123'),     'Candidat',
        'Je suis développeuse web junior passionnée par Python et Flask. '
        'Diplômée en informatique, je cherche un stage ou CDI dans le développement back-end.',
        '0666111222'),
]

curseur.executemany(
    'INSERT INTO utilisateurs (nom_utilisateur, email, mot_de_passe, role, profil_cv, telephone) VALUES (?,?,?,?,?,?)',
    comptes_test
)

# On crée 2 offres de démonstration
curseur.execute(
    'INSERT INTO offres (titre, description, localisation, type_contrat, salaire, recruteur_id) VALUES (?,?,?,?,?,?)',
    ('Développeur Python Junior',
     'Nous recherchons un développeur Python passionné pour rejoindre notre équipe agile. '
     'Vous travaillerez sur des projets Flask/Django. Connaissance de SQLite ou MySQL appréciée.',
     'Casablanca', 'CDI', '8 000 - 12 000 MAD/mois', 3)
)
curseur.execute(
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

