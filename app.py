# ==========================================
# APP.PY — CŒUR DU SYSTÈME NEXTHIRE
# Sprints 1 à 6 complets
# ==========================================
#
# Flask = notre framework web (comme une "boîte à outils" pour créer des sites)
# request = pour lire les données envoyées par les formulaires
# render_template = pour afficher un fichier HTML
# redirect, url_for = pour envoyer l'utilisateur vers une autre page
# session = pour "mémoriser" qui est connecté (comme un badge d'accès)
# flash = pour afficher des messages temporaires ("Inscription réussie !")
#
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
try:
    import psycopg2
    import psycopg2.extras
    import_error = None
except ImportError as e:
    psycopg2 = None
    import_error = str(e)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# -------------------------------------------------------
# INITIALISATION DE L'APPLICATION
# -------------------------------------------------------
app = Flask(__name__, template_folder='app/html', static_folder='app')
app.secret_key = "nexthire_cle_secrete_2026"

# Configuration des Sessions : expire à la fermeture du navigateur
app.config['SESSION_PERMANENT'] = False


# Filtre Jinja2 personnalisé pour formater les dates (compatible SQLite et Postgres)
def format_date(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:10]
    return value.strftime("%Y-%m-%d")

app.jinja_env.filters['date_short'] = format_date

# -------------------------------------------------------
# FONCTION UTILITAIRE : Connexion à la base de données
# -------------------------------------------------------
IS_POSTGRES = 'DATABASE_URL' in os.environ

class DBConnection:
    def __init__(self):
        if IS_POSTGRES:
            if not psycopg2:
                raise RuntimeError(f"psycopg2 is not installed or failed to load: {import_error}")
            try:
                # Log connection attempt
                print("--- Database: Attempting to connect to PostgreSQL... ---")
                self.conn = psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=5)
                print("--- Database: Connection SUCCESSFUL! ---")
            except Exception as e:
                print(f"--- Database CONNECTION ERROR: {str(e)} ---")
                raise e
        else:
            db_path = os.environ.get('DATABASE_PATH', 'recrutement_simple.db')
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row

    def execute(self, query, params=()):
        if IS_POSTGRES:
            # PostgreSQL requires %s instead of ? for parameterized queries
            pg_query = query.replace('?', '%s')
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(pg_query, params)
            return cur
        else:
            return self.conn.execute(query, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    return DBConnection()

# -------------------------------------------------------
# PROTECTION DES PAGES
# -------------------------------------------------------
from functools import wraps

def login_requis(roles_autorises=None):
    """
    Décorateur pour vérifier si l'utilisateur est connecté et si son rôle est autorisé.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'utilisateur_id' not in session:
                flash("Veuillez vous connecter pour accéder à cette page.", "danger")
                return redirect(url_for('connexion'))
            if roles_autorises and session.get('role') not in roles_autorises:
                flash("Vous n'avez pas la permission d'accéder à cette page.", "danger")
                return redirect(url_for('tableau_de_bord'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================
# ============================================================
# SPRINT 1 — AUTHENTIFICATION & GESTION DES UTILISATEURS
# ============================================================
# ============================================================

# -------------------------------------------------------
# ROUTE 1 : Page d'Accueil  →  /
# -------------------------------------------------------
@app.route('/')
def accueil():
    """Affiche la page d'accueil publique du site."""
    return render_template('index.html')


# -------------------------------------------------------
# ROUTE 2 : Inscription  →  /register
# -------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def inscription():
    """
    GET  → Affiche le formulaire d'inscription.
    POST → Récupère les données du formulaire et crée le compte.
    """
    if request.method == 'POST':
        # On lit les données du formulaire HTML (les 'name' des inputs)
        nom       = request.form['username']
        email     = request.form['email']
        mdp       = request.form['password']
        mdp_conf  = request.form['confirm_password']
        role      = 'Candidat' # Par défaut, tout le monde s'inscrit en tant que Candidat
        telephone = request.form.get('telephone', '')  # .get() → valeur vide si absent

        # SÉCURITÉ : Vérification que les deux mots de passe correspondent
        if mdp != mdp_conf:
            flash("Erreur : les mots de passe ne correspondent pas.", "danger")
            return redirect(url_for('inscription'))

        # SÉCURITÉ : On ne stocke JAMAIS le mot de passe en clair !
        # generate_password_hash() le transforme en une longue chaîne illisible (hash)
        mdp_hache = generate_password_hash(mdp)

        conn = get_db_connection()
        try:
            # INSERT INTO = ajouter une nouvelle ligne dans la table utilisateurs
            # Les '?' sont des paramètres (protection contre l'injection SQL)
            conn.execute(
                'INSERT INTO utilisateurs (nom_utilisateur, email, mot_de_passe, role, telephone) VALUES (?,?,?,?,?)',
                (nom, email, mdp_hache, role, telephone)
            )
            conn.commit()
            flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('connexion'))

        except (sqlite3.IntegrityError, Exception) as e:
            # Cette erreur arrive si l'email ou le nom est déjà pris (UNIQUE dans la table)
            # Ou toute autre erreur avec la base de données
            flash("Erreur : cet email ou ce nom d'utilisateur est déjà utilisé.", "danger")
        finally:
            conn.close()  # TOUJOURS fermer la connexion, même en cas d'erreur

    return render_template('register.html')


# -------------------------------------------------------
# ROUTE 3 : Connexion  →  /login
# -------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def connexion():
    """
    POST → Vérifie email + mot de passe, crée la session si OK.
    Session = mémoire temporaire stockée côté serveur pour cet utilisateur.
    """
    if request.method == 'POST':
        email_saisi = request.form['email']
        mdp_saisi   = request.form['password']

        conn = get_db_connection()
        # SELECT * = chercher un utilisateur avec cet email exact
        utilisateur = conn.execute(
            'SELECT * FROM utilisateurs WHERE email = ?', (email_saisi,)
        ).fetchone()
        conn.close()

        # check_password_hash compare le mot de passe saisi avec le hash stocké
        if utilisateur and check_password_hash(utilisateur['mot_de_passe'], mdp_saisi):
            # ✅ Connexion réussie : on mémorise l'utilisateur dans la session
            session['utilisateur_id']  = utilisateur['id']
            session['nom_utilisateur'] = utilisateur['nom_utilisateur']
            session['role']            = utilisateur['role']
            flash(f"Bienvenue, {utilisateur['nom_utilisateur']} ! 👋", "success")
            return redirect(url_for('tableau_de_bord'))
        else:
            flash("Email ou mot de passe incorrect.", "danger")

    return render_template('login.html')


# -------------------------------------------------------
# ROUTE 4 : Déconnexion  →  /logout
# -------------------------------------------------------
@app.route('/logout')
def deconnexion():
    """Vide la session (déconnecte l'utilisateur) et redirige vers l'accueil."""
    session.clear()
    flash("Vous avez été déconnecté avec succès.", "info")
    return redirect(url_for('accueil'))


# ============================================================
# ============================================================
# SPRINT 2 — GESTION DES OFFRES D'EMPLOI
# ============================================================
# ============================================================

# -------------------------------------------------------
# ROUTE 5 : Liste publique des offres  →  /offres
# -------------------------------------------------------
@app.route('/offres')
def liste_offres():
    """
    Page publique (visible par tout le monde, même sans connexion).
    Affiche toutes les offres ouvertes avec une option de recherche.
    """
    # On récupère les paramètres de l'URL (?recherche=python&contrat=CDI)
    recherche = request.args.get('recherche', '').strip()
    contrat   = request.args.get('contrat', '').strip()

    conn = get_db_connection()

    # Construction de la requête SQL avec filtres dynamiques
    # JOIN permet de récupérer le nom du recruteur en même temps que l'offre
    sql = '''
        SELECT offres.*, utilisateurs.nom_utilisateur as recruteur_nom
        FROM offres
        JOIN utilisateurs ON offres.recruteur_id = utilisateurs.id
        WHERE offres.statut = 'Ouverte'
    '''
    params = []

    if recherche:
        # LIKE '%mot%' cherche si le mot apparaît n'importe où dans le titre/description
        sql += ' AND (offres.titre LIKE ? OR offres.description LIKE ? OR offres.localisation LIKE ?)'
        params.extend([f'%{recherche}%', f'%{recherche}%', f'%{recherche}%'])

    if contrat:
        sql += ' AND offres.type_contrat = ?'
        params.append(contrat)

    sql += ' ORDER BY offres.date_creation DESC'  # Les plus récentes en premier

    offres = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template('offres.html', offres=offres, recherche=recherche, contrat=contrat)


# -------------------------------------------------------
# ROUTE 6 : Détail d'une offre  →  /offre/<id>
# -------------------------------------------------------
@app.route('/offre/<int:offre_id>')
def detail_offre(offre_id):
    """
    Affiche le détail complet d'une offre.
    Les <int:offre_id> dans l'URL sont des paramètres dynamiques.
    Ex: /offre/3 → offre_id = 3
    """
    conn = get_db_connection()

    offre = conn.execute(
        '''SELECT offres.*, utilisateurs.nom_utilisateur as recruteur_nom
           FROM offres
           JOIN utilisateurs ON offres.recruteur_id = utilisateurs.id
           WHERE offres.id = ?''',
        (offre_id,)
    ).fetchone()

    # Vérifier si le candidat a déjà postulé
    deja_postule = False
    if session.get('role') == 'Candidat':
        candidature = conn.execute(
            'SELECT id FROM candidatures WHERE candidat_id = ? AND offre_id = ?',
            (session['utilisateur_id'], offre_id)
        ).fetchone()
        deja_postule = candidature is not None

    conn.close()

    if not offre:
        flash("Cette offre n'existe pas.", "danger")
        return redirect(url_for('liste_offres'))

    return render_template('offre_detail.html', offre=offre, deja_postule=deja_postule)


# -------------------------------------------------------
# ROUTE 7 : Publier une offre (Recruteur)  →  /publier_offre
# -------------------------------------------------------
@app.route('/publier_offre', methods=['GET', 'POST'])
def publier_offre():
    """Formulaire pour créer une nouvelle offre d'emploi (Recruteur uniquement)."""
    if 'utilisateur_id' not in session:
        return redirect(url_for('connexion'))
    if session.get('role') != 'Recruteur':
        flash("Seuls les recruteurs peuvent publier des offres.", "danger")
        return redirect(url_for('tableau_de_bord'))

    if request.method == 'POST':
        titre       = request.form['titre']
        description = request.form['description']
        localisation = request.form.get('localisation', '')
        type_contrat = request.form.get('type_contrat', '')
        salaire = request.form.get('salaire', '')

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO offres (titre, description, localisation, type_contrat, salaire, recruteur_id) VALUES (?,?,?,?,?,?)',
            (titre, description, localisation, type_contrat, salaire, session['utilisateur_id'])
        )
        conn.commit()
        conn.close()
        flash("✅ Offre publiée avec succès !", "success")
        return redirect(url_for('tableau_de_bord'))

    return render_template('publier_offre.html')


# -------------------------------------------------------
# ROUTE 8 : Modifier une offre (Recruteur)  →  /modifier_offre/<id>
# -------------------------------------------------------
@app.route('/modifier_offre/<int:offre_id>', methods=['GET', 'POST'])
def modifier_offre(offre_id):
    """Permet au recruteur propriétaire de modifier son offre."""
    if 'utilisateur_id' not in session or session.get('role') != 'Recruteur':
        return redirect(url_for('connexion'))

    conn = get_db_connection()
    offre = conn.execute(
        'SELECT * FROM offres WHERE id = ? AND recruteur_id = ?',
        (offre_id, session['utilisateur_id'])
    ).fetchone()

    if not offre:
        conn.close()
        flash("Offre introuvable ou vous n'êtes pas autorisé.", "danger")
        return redirect(url_for('tableau_de_bord'))

    if request.method == 'POST':
        titre        = request.form['titre']
        description  = request.form['description']
        localisation = request.form.get('localisation', '')
        type_contrat = request.form.get('type_contrat', '')
        salaire      = request.form.get('salaire', '')
        statut       = request.form.get('statut', 'Ouverte')

        conn.execute(
            '''UPDATE offres SET titre=?, description=?, localisation=?, type_contrat=?, salaire=?, statut=?
               WHERE id=? AND recruteur_id=?''',
            (titre, description, localisation, type_contrat, salaire, statut, offre_id, session['utilisateur_id'])
        )
        conn.commit()
        conn.close()
        flash("✅ Offre modifiée avec succès !", "success")
        return redirect(url_for('tableau_de_bord'))

    conn.close()
    return render_template('modifier_offre.html', offre=offre)


# -------------------------------------------------------
# ROUTE 9 : Supprimer une offre (Recruteur)  →  /supprimer_offre/<id>
# -------------------------------------------------------
@app.route('/supprimer_offre/<int:offre_id>', methods=['POST'])
def supprimer_offre(offre_id):
    """Supprime une offre (et ses candidatures liées) si le recruteur en est l'auteur."""
    if 'utilisateur_id' not in session or session.get('role') != 'Recruteur':
        return redirect(url_for('connexion'))

    conn = get_db_connection()
    # D'abord, supprimer les candidatures liées à cette offre
    conn.execute('DELETE FROM candidatures WHERE offre_id = ?', (offre_id,))
    # Ensuite supprimer l'offre elle-même (seulement si le recruteur en est l'auteur)
    conn.execute(
        'DELETE FROM offres WHERE id = ? AND recruteur_id = ?',
        (offre_id, session['utilisateur_id'])
    )
    conn.commit()
    conn.close()
    flash("Offre supprimée.", "info")
    return redirect(url_for('tableau_de_bord'))


# ============================================================
# ============================================================
# SPRINT 3 — GESTION DES CANDIDATURES
# ============================================================
# ============================================================

# -------------------------------------------------------
# ROUTE 10 : Postuler à une offre (Candidat)  →  /postuler/<offre_id>
# -------------------------------------------------------
@app.route('/postuler/<int:offre_id>', methods=['POST'])
def postuler(offre_id):
    """
    Le candidat envoie sa candidature pour une offre donnée.
    On empêche de postuler deux fois grâce à la contrainte UNIQUE en base.
    """
    if session.get('role') != 'Candidat':
        flash("Seuls les candidats peuvent postuler.", "danger")
        return redirect(url_for('detail_offre', offre_id=offre_id))

    lettre = request.form.get('lettre_motivation', '')

    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO candidatures (candidat_id, offre_id, lettre_motivation) VALUES (?,?,?)',
            (session['utilisateur_id'], offre_id, lettre)
        )
        conn.commit()
        flash("✅ Votre candidature a été envoyée avec succès !", "success")
    except sqlite3.IntegrityError:
        # La contrainte UNIQUE(candidat_id, offre_id) a bloqué l'insertion
        flash("Vous avez déjà postulé à cette offre.", "danger")
    finally:
        conn.close()

    return redirect(url_for('tableau_de_bord'))


# -------------------------------------------------------
# ROUTE 11 : Mettre à jour le profil/CV (Candidat)  →  /ajouter_cv
# -------------------------------------------------------
@app.route('/ajouter_cv', methods=['POST'])
def ajouter_cv():
    """
    Le candidat enregistre ou modifie son texte de profil/CV.
    UPDATE = modifier une ligne existante dans la base.
    """
    if session.get('role') != 'Candidat':
        return redirect(url_for('tableau_de_bord'))

    cv_texte  = request.form.get('cv_texte', '')
    telephone = request.form.get('telephone', '')

    conn = get_db_connection()
    conn.execute(
        'UPDATE utilisateurs SET profil_cv = ?, telephone = ? WHERE id = ?',
        (cv_texte, telephone, session['utilisateur_id'])
    )
    conn.commit()
    conn.close()
    flash("✅ Votre profil a été mis à jour !", "success")
    return redirect(url_for('tableau_de_bord'))


# ============================================================
# ============================================================
# SPRINT 4 — SUIVI DU PROCESSUS DE RECRUTEMENT
# ============================================================
# ============================================================

# -------------------------------------------------------
# ROUTE 12 : Changer le statut d'une candidature  →  /changer_statut/<id>
# -------------------------------------------------------
@app.route('/changer_statut/<int:candidature_id>', methods=['POST'])
def changer_statut(candidature_id):
    """
    Le Recruteur ou RH peut changer le statut d'une candidature :
    'En attente'  →  'Accepté' / 'Refusé' / 'Entretien planifié'
    """
    if session.get('role') not in ('Recruteur', 'RH', 'Admin'):
        flash("Permission refusée.", "danger")
        return redirect(url_for('tableau_de_bord'))

    nouveau_statut = request.form.get('statut')

    conn = get_db_connection()
    conn.execute(
        'UPDATE candidatures SET statut = ? WHERE id = ?',
        (nouveau_statut, candidature_id)
    )
    conn.commit()
    conn.close()
    flash(f"Statut mis à jour : {nouveau_statut}", "success")
    return redirect(url_for('tableau_de_bord'))


# -------------------------------------------------------
# ROUTE 13 : Planifier un entretien  →  /planifier_entretien/<candidature_id>
# -------------------------------------------------------
@app.route('/planifier_entretien/<int:candidature_id>', methods=['POST'])
def planifier_entretien(candidature_id):
    """
    Le Recruteur ou RH planifie un entretien pour une candidature.
    On met aussi à jour le statut de la candidature à 'Entretien planifié'.
    """
    if session.get('role') not in ('Recruteur', 'RH'):
        flash("Permission refusée.", "danger")
        return redirect(url_for('tableau_de_bord'))

    date_entretien = request.form.get('date_entretien')
    lieu           = request.form.get('lieu', '')

    conn = get_db_connection()
    # Ajouter l'entretien dans la table entretiens
    conn.execute(
        'INSERT INTO entretiens (candidature_id, date_entretien, lieu) VALUES (?,?,?)',
        (candidature_id, date_entretien, lieu)
    )
    # Mettre à jour le statut de la candidature
    conn.execute(
        "UPDATE candidatures SET statut = 'Entretien planifié' WHERE id = ?",
        (candidature_id,)
    )
    conn.commit()
    conn.close()
    flash("✅ Entretien planifié avec succès !", "success")
    return redirect(url_for('tableau_de_bord'))


# -------------------------------------------------------
# ROUTE 14 : Ajouter des notes d'évaluation  →  /evaluer/<entretien_id>
# -------------------------------------------------------
@app.route('/evaluer/<int:entretien_id>', methods=['POST'])
def evaluer(entretien_id):
    """Le recruteur ajoute ses notes d'évaluation après l'entretien."""
    if session.get('role') not in ('Recruteur', 'RH'):
        return redirect(url_for('tableau_de_bord'))

    notes = request.form.get('notes', '')
    conn = get_db_connection()
    conn.execute('UPDATE entretiens SET notes = ? WHERE id = ?', (notes, entretien_id))
    conn.commit()
    conn.close()
    flash("✅ Évaluation sauvegardée !", "success")
    return redirect(url_for('tableau_de_bord'))


# ============================================================
# ============================================================
# SPRINT 5 — TABLEAU DE BORD PRINCIPAL (ALL ROLES)
# ============================================================
# ============================================================

# -------------------------------------------------------
# ROUTE 15 : Tableau de bord  →  /dashboard
# -------------------------------------------------------
@app.route('/dashboard')
def tableau_de_bord():
    if 'utilisateur_id' not in session:
        flash("Veuillez vous connecter pour accéder à cette page.", "danger")
        return redirect(url_for('connexion'))

    try:
        conn     = get_db_connection()
        role     = session.get('role')
        uid      = session['utilisateur_id']
        donnees  = {}

        if role == 'Candidat':
            u = conn.execute('SELECT * FROM utilisateurs WHERE id = ?', (uid,)).fetchone()
            donnees['profil_cv'] = u['profil_cv'] or ''
            donnees['telephone'] = u['telephone'] or ''
            donnees['candidatures'] = conn.execute('''
                SELECT c.id, c.offre_id, c.date_postulation, c.statut, 
                       o.titre as offre_titre, o.localisation, o.type_contrat
                FROM candidatures c
                JOIN offres o ON c.offre_id = o.id
                WHERE c.candidat_id = ?
                ORDER BY c.date_postulation DESC''', (uid,)).fetchall()
            donnees['stats'] = {
                'total': len(donnees['candidatures']),
                'en_attente': sum(1 for c in donnees['candidatures'] if c['statut'] == 'En attente'),
                'accepte': sum(1 for c in donnees['candidatures'] if c['statut'] == 'Accepté'),
                'refuse': sum(1 for c in donnees['candidatures'] if c['statut'] == 'Refusé'),
                'entretien': sum(1 for c in donnees['candidatures'] if c['statut'] == 'Entretien planifié')
            }
            donnees['entretiens'] = conn.execute('''
                SELECT e.id, e.date_entretien, e.lieu, e.notes, o.titre as offre_titre
                FROM entretiens e
                JOIN candidatures c ON e.candidature_id = c.id
                JOIN offres o ON c.offre_id = o.id
                WHERE c.candidat_id = ?
                ORDER BY e.date_entretien ASC''', (uid,)).fetchall()

        elif role == 'Recruteur':
            donnees['offres'] = conn.execute('SELECT * FROM offres WHERE recruteur_id = ? ORDER BY date_creation DESC', (uid,)).fetchall()
            donnees['candidatures'] = conn.execute('''
                SELECT c.id, c.statut, c.date_postulation, 
                       u.nom_utilisateur as candidat_nom, u.email as candidat_email, 
                       u.telephone, u.profil_cv, o.titre as offre_titre, o.id as offre_id
                FROM candidatures c
                JOIN utilisateurs u ON c.candidat_id = u.id
                JOIN offres o ON c.offre_id = o.id
                WHERE o.recruteur_id = ?
                ORDER BY c.date_postulation DESC''', (uid,)).fetchall()
            donnees['entretiens'] = conn.execute('''
                SELECT e.id, e.date_entretien, e.lieu, u.nom_utilisateur as candidat_nom, o.titre as offre_titre
                FROM entretiens e
                JOIN candidatures c ON e.candidature_id = c.id
                JOIN utilisateurs u ON c.candidat_id = u.id
                JOIN offres o ON c.offre_id = o.id
                WHERE o.recruteur_id = ?
                ORDER BY e.date_entretien ASC''', (uid,)).fetchall()
            donnees['stats'] = {
                'total_offres': len(donnees['offres']),
                'offres_ouvertes': sum(1 for o in donnees['offres'] if o['statut'] == 'Ouverte'),
                'total_cands': len(donnees['candidatures']),
                'en_attente': sum(1 for c in donnees['candidatures'] if c['statut'] == 'En attente'),
                'accepte': sum(1 for c in donnees['candidatures'] if c['statut'] == 'Accepté'),
                'refuse': sum(1 for c in donnees['candidatures'] if c['statut'] == 'Refusé'),
                'entretiens': len(donnees['entretiens'])
            }

        elif role == 'RH':
            donnees['candidats'] = conn.execute("SELECT * FROM utilisateurs WHERE role = 'Candidat' ORDER BY date_creation DESC").fetchall()
            donnees['offres'] = conn.execute("SELECT o.*, u.nom_utilisateur as recruteur_nom FROM offres o JOIN utilisateurs u ON o.recruteur_id = u.id ORDER BY o.date_creation DESC").fetchall()
            donnees['candidatures'] = conn.execute("SELECT c.*, u.nom_utilisateur as candidat_nom, u.email as candidat_email, o.titre as offre_titre FROM candidatures c JOIN utilisateurs u ON c.candidat_id = u.id JOIN offres o ON c.offre_id = o.id ORDER BY c.date_postulation DESC").fetchall()
            donnees['entretiens'] = conn.execute("SELECT e.*, u.nom_utilisateur as candidat_nom, o.titre as offre_titre FROM entretiens e JOIN candidatures c ON e.candidature_id = c.id JOIN utilisateurs u ON c.candidat_id = u.id JOIN offres o ON c.offre_id = o.id ORDER BY e.date_entretien ASC").fetchall()
            all_c = donnees['candidatures']
            donnees['stats'] = {
                'total_candidats': len(donnees['candidats']),
                'total_offres': len(donnees['offres']),
                'total_candidatures': len(all_c),
                'en_attente': sum(1 for c in all_c if c['statut'] == 'En attente'),
                'accepte': sum(1 for c in all_c if c['statut'] == 'Accepté'),
                'refuse': sum(1 for c in all_c if c['statut'] == 'Refusé'),
                'entretiens_planifies': len(donnees['entretiens'])
            }

        elif role == 'Admin':
            donnees['utilisateurs'] = conn.execute('SELECT id, nom_utilisateur, email, role, date_creation FROM utilisateurs ORDER BY date_creation DESC').fetchall()
            nb_o = conn.execute("SELECT COUNT(*) FROM offres").fetchone()[0]
            nb_c = conn.execute("SELECT COUNT(*) FROM candidatures").fetchone()[0]
            nb_e = conn.execute("SELECT COUNT(*) FROM entretiens").fetchone()[0]
            roles_stats_rows = conn.execute("SELECT role, COUNT(*) as nb FROM utilisateurs GROUP BY role").fetchall()
            donnees['stats'] = {
                'total_users': len(donnees['utilisateurs']),
                'total_offres': nb_o,
                'total_cands': nb_c,
                'total_entretiens': nb_e,
                'par_role': {r['role']: r['nb'] for r in roles_stats_rows}
            }

        conn.close()
        return render_template('dashboard.html', nom=session.get('nom_utilisateur'), role=role, donnees=donnees)

    except Exception as e:
        if 'conn' in locals(): conn.close()
        import traceback
        print(f"ERROR: {str(e)}
{traceback.format_exc()}")
        flash(f"Erreur d'affichage : {str(e)}", "danger")
        return redirect(url_for('accueil'))

# ============================================================
# ============================================================
# SPRINT 5 — STATISTIQUES & REPORTING
# ============================================================
# ============================================================

# -------------------------------------------------------
# ROUTE 16 : Page de Statistiques  →  /statistiques
# -------------------------------------------------------
@app.route('/statistiques')
def statistiques():
    """
    Page dédiée aux statistiques et rapports.
    Accessible aux Recruteurs, RH et Admin.
    """
    if 'utilisateur_id' not in session:
        return redirect(url_for('connexion'))

    if session.get('role') not in ('Recruteur', 'RH', 'Admin'):
        flash("Accès réservé au personnel RH et Recrutement.", "danger")
        return redirect(url_for('tableau_de_bord'))

    conn = get_db_connection()
    role = session.get('role')
    uid = session['utilisateur_id']
    stats = {}  # type: dict[str, object]

    if role == 'Recruteur':
        # Nombre de candidatures par statut pour ses offres
        stats['par_statut'] = conn.execute(
            '''SELECT candidatures.statut, COUNT(*) as nb
               FROM candidatures
               JOIN offres ON candidatures.offre_id = offres.id
               WHERE offres.recruteur_id = ?
               GROUP BY candidatures.statut''',
            (uid,)
        ).fetchall()

        # Nombre de candidatures par offre
        stats['par_offre'] = conn.execute(
            '''SELECT offres.titre, COUNT(candidatures.id) as nb
               FROM offres
               LEFT JOIN candidatures ON offres.id = candidatures.offre_id
               WHERE offres.recruteur_id = ?
               GROUP BY offres.id, offres.titre
               ORDER BY nb DESC''',
            (uid,)
        ).fetchall()

    elif role in ('RH', 'Admin'):
        # Stats globales
        stats['par_statut'] = conn.execute(
            "SELECT statut, COUNT(*) as nb FROM candidatures GROUP BY statut"
        ).fetchall()

        stats['par_offre'] = conn.execute(
            '''SELECT offres.titre, COUNT(candidatures.id) as nb
               FROM offres
               LEFT JOIN candidatures ON offres.id = candidatures.offre_id
               GROUP BY offres.id, offres.titre
               ORDER BY nb DESC
               LIMIT 10'''
        ).fetchall()

        stats['par_role'] = conn.execute(
            "SELECT role, COUNT(*) as nb FROM utilisateurs GROUP BY role"
        ).fetchall()

        # Offres par type de contrat
        stats['par_contrat'] = conn.execute(
            "SELECT type_contrat, COUNT(*) as nb FROM offres GROUP BY type_contrat"
        ).fetchall()

        # Total général
        stats['totaux'] = {
            'utilisateurs':  conn.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0],
            'offres':        conn.execute("SELECT COUNT(*) FROM offres").fetchone()[0],
            'candidatures':  conn.execute("SELECT COUNT(*) FROM candidatures").fetchone()[0],
            'entretiens':    conn.execute("SELECT COUNT(*) FROM entretiens").fetchone()[0],
            'acceptes':      conn.execute("SELECT COUNT(*) FROM candidatures WHERE statut='Accepté'").fetchone()[0],
            'refuse':        conn.execute("SELECT COUNT(*) FROM candidatures WHERE statut='Refusé'").fetchone()[0],
        }

    conn.close()
    return render_template('statistiques.html', stats=stats, role=role)


# ============================================================
# ============================================================
# SPRINT 6 — ADMIN : GESTION DES UTILISATEURS
# ============================================================
# ============================================================

# -------------------------------------------------------
# ROUTE 17 : Supprimer un utilisateur (Admin)  →  /supprimer_user/<id>
# -------------------------------------------------------
@app.route('/supprimer_user/<int:user_id>', methods=['POST'])
def supprimer_user(user_id):
    """L'administrateur peut supprimer n'importe quel compte utilisateur."""
    if session.get('role') != 'Admin':
        flash("Accès refusé.", "danger")
        return redirect(url_for('tableau_de_bord'))

    if user_id == session['utilisateur_id']:
        flash("Vous ne pouvez pas supprimer votre propre compte !", "danger")
        return redirect(url_for('tableau_de_bord'))

    conn = get_db_connection()
    conn.execute('DELETE FROM utilisateurs WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash("Utilisateur supprimé.", "info")
    return redirect(url_for('tableau_de_bord'))


# -------------------------------------------------------
# ROUTE 18 : Changer le rôle d'un utilisateur (Admin)  →  /changer_role/<id>
# -------------------------------------------------------
@app.route('/changer_role/<int:user_id>', methods=['POST'])
def changer_role(user_id):
    """L'administrateur peut changer le rôle d'un utilisateur."""
    if session.get('role') != 'Admin':
        flash("Accès refusé.", "danger")
        return redirect(url_for('tableau_de_bord'))

    nouveau_role = request.form.get('nouveau_role')
    conn = get_db_connection()
    conn.execute('UPDATE utilisateurs SET role = ? WHERE id = ?', (nouveau_role, user_id))
    conn.commit()
    conn.close()
    flash(f"Rôle modifié : {nouveau_role}", "success")
    return redirect(url_for('tableau_de_bord'))

# ============================================================
# DÉMARRAGE DU SERVEUR
# ============================================================

if __name__ == '__main__':
    # On écoute sur 0.0.0.0 pour être sûr que le site soit accessible
    # même si 'localhost' ne fonctionne pas correctement sur votre machine.
    app.run(debug=True, host='0.0.0.0', port=5000)