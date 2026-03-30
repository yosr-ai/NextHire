# 🚀 Guide Complet du Projet NextHire

Bienvenue dans la documentation officielle du projet **NextHire**. Ce document détaille les rôles des utilisateurs, les étapes de développement (sprints) et les informations d'accès.

---

## 🎭 1. Les Acteurs et leurs Rôles

Le système NextHire est bâti autour de 4 types d'utilisateurs. Chaque rôle a été pensé pour répondre à un besoin précis du processus de recrutement.

### 👤 LE CANDIDAT (Utilisateur Final)
*Le chercheur d'emploi.*
- **Missions** : Consulter les offres, gérer son CV et postuler.
- **Fonctionnalités Clés** :
    - **Recherche par filtre** : Trouver des postes par type de contrat (CDI, Stage) ou par ville.
    - **Espace Profil** : Enregistrer un texte de présentation/CV et son numéro de téléphone.
    - **Suivi en temps réel** : Voir l'évolution de ses candidatures (En attente, Entretien, Refusé, Accepté).

### 🤝 LE RECRUTEUR (Manager Opérationnel)
*La personne qui exprime un besoin et sélectionne les profils.*
- **Missions** : Publier des offres et évaluer les candidats.
- **Fonctionnalités Clés** :
    - **Gestion des Offres** : Créer, modifier et fermer des annonces.
    - **Évaluation** : Consulter les dossiers des candidats et filtrer les meilleurs profils.
    - **Gestion des Entretiens** : Planifier des rendez-vous et ajouter des notes d'entretien directement sur la plateforme.

### 📊 LE RESPONSABLE RH (RH)
*Le superviseur de la stratégie de recrutement.*
- **Missions** : Monitorer l'activité globale et gérer la base de données talents.
- **Fonctionnalités Clés** :
    - **Vision Globale** : Accès à la liste complète de tous les candidats inscrits.
    - **Tableau de Bord Analytique** : Graphiques et indicateurs de performance (KPIs) sur le volume d'offres et de candidatures.

### 🛠️ L'ADMINISTRATEUR (Technique)
*Le gestionnaire de la sécurité et des droits.*
- **Missions** : S'assurer du bon fonctionnement et gérer les comptes.
- **Fonctionnalités Clés** :
    - **Gestion des Rôles** : Pouvoir transformer un utilisateur en RH ou Recruteur.
    - **Modération** : Supprimer des comptes en cas de besoin.

---

## 📅 2. Les 6 Sprints de Développement

Le projet a été réalisé en 6 phases majeures suivant la méthodologie Agile.

| Phase | Sprint | Objectifs Réalisés |
| :--- | :--- | :--- |
| **P1** | **Authentification** | Création des comptes, connexion sécurisée et protection des pages par mot de passe. |
| **P2** | **Offres d'Emploi** | Création du moteur de recherche d'offres et de l'interface de publication pour les recruteurs. |
| **P3** | **Candidatures** | Mise en place du bouton "Postuler" et de la sauvegarde des CV dans la base de données. |
| **P4** | **Suivi & Process** | Développement du système de changement de statut (Accepté/Refusé) et planification des entretiens. |
| **P5** | **Dashboard & Stats** | Création des vues statistiques et des tableaux de bord personnalisés pour chaque rôle. |
| **P6** | **Administration** | Finalisation du panneau de contrôle pour la gestion des utilisateurs et des permissions. |

---

## 🔑 3. Accès de Démonstration (Test)

Utilisez ces comptes pour tester toutes les facettes du projet :

| Rôle | Email | Mot de passe |
| :--- | :--- | :--- |
| **Admin** | `admin@nexthire.com` | `admin123` |
| **RH** | `marie@nexthire.com` | `rh123` |
| **Recruteur** | `recruteur@nexthire.com` | `recruteur123` |
| **Candidat** | `alice@email.com` | `alice123` |

---
*Ce document est stocké dans le dossier `/docs/` du projet.*
