# NAMM GLOBAL – Backend Flask v2

API REST complète pour le service d'import Chine → Afrique.
Architecture refactorisée sur la base du schéma de production.

---

## Stack technique

| Composant | Version |
|-----------|---------|
| Flask | 3.0.3 |
| Flask-SQLAlchemy | 3.1.1 |
| Flask-Migrate (Alembic) | 4.0.7 |
| Flask-JWT-Extended | 4.6.0 |
| Flask-Bcrypt | 1.0.1 |
| Flask-CORS | 4.0.1 |
| PostgreSQL + psycopg2 | — |

---

## Installation

```bash
# 1. Environnement virtuel
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Dépendances
pip install -r requirements.txt

# 3. Variables d'environnement
cp .env.example .env
# Éditer .env avec vos vraies valeurs

# 4. Migrations
flask db init
flask db migrate -m "initial schema"
flask db upgrade

# 5. Données initiales
python seed.py

# 6. Lancer
python run.py
# → http://localhost:5000
```

---

## Variables d'environnement (.env)

```env
DATABASE_URL=postgresql://postgres:MOT_DE_PASSE@localhost:5432/nammglobalBD
SECRET_KEY=une-cle-tres-longue-et-aleatoire
JWT_SECRET_KEY=autre-cle-jwt-longue
FRONTEND_URL=http://localhost:5500
FLASK_ENV=development
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-xxxxx
```

> ⚠️ Si votre mot de passe contient `#`, remplacez-le par `%23` dans l'URL.

---

## Architecture

```
nammglobal-backend/
├── app/
│   ├── __init__.py          ← Factory Flask (CORS, JWT, Migrate, Bcrypt)
│   ├── models/              ← 13 modèles SQLAlchemy
│   │   ├── user.py          ← User (role: client | admin)
│   │   ├── wave.py          ← Vagues de commandes
│   │   ├── request.py       ← Request + RequestItemImage
│   │   ├── quotation.py     ← Quotation + QuotationCost
│   │   ├── order.py         ← Order + OrderTrackingEvent
│   │   ├── payment.py       ← Payment (Flutterwave)
│   │   ├── supplier.py      ← Supplier + SupplierOrder + Items + Tracking
│   │   ├── gallery.py       ← GalleryItem
│   │   ├── notification.py  ← Notification
│   │   ├── pricing.py       ← ServiceFeeRule + ShippingMethod + ProductCategoryRule
│   │   └── stat.py          ← Stat (stats homepage)
│   ├── services/            ← Toute la business logic
│   │   ├── notification_service.py
│   │   ├── pricing_service.py
│   │   ├── request_service.py
│   │   ├── quotation_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   └── supplier_service.py
│   ├── routes/              ← 11 blueprints Flask
│   │   ├── auth.py          ← /api/auth/*
│   │   ├── requests.py      ← /api/requests/*
│   │   ├── quotations.py    ← /api/quotations/*
│   │   ├── orders.py        ← /api/orders/*
│   │   ├── waves.py         ← /api/waves/*
│   │   ├── suppliers.py     ← /api/suppliers/*
│   │   ├── gallery.py       ← /api/gallery/*
│   │   ├── pricing.py       ← /api/pricing/*
│   │   ├── notifications.py ← /api/notifications/*
│   │   ├── stats.py         ← /api/stats/*
│   │   └── users.py         ← /api/users/*
│   └── utils/
│       ├── helpers.py       ← success/error/created, validators
│       └── auth_decorators.py ← @login_required, @admin_required
├── config.py
├── run.py
├── seed.py
└── requirements.txt
```

---

## Workflow métier

```
Client soumet Request
       ↓
Admin analyse → crée Quotation (draft)
       ↓
Admin envoie Quotation au client (sent) → notification push
       ↓
Client accepte Quotation (accepted)
       ↓
Client paie via Flutterwave → POST /api/orders/confirm-payment
       ↓
Order créée automatiquement (confirmed)
       ↓
Admin crée SupplierOrder(s) pour chaque fournisseur
       ↓
Admin met à jour le statut Order (cn_transit → shipping → customs → delivered)
       ↓
Notifications automatiques à chaque étape
```

---

## Routes API complètes

### Auth — `/api/auth`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/register` | — | Inscription client |
| POST | `/login` | — | Connexion (retourne JWT) |
| POST | `/refresh` | Refresh JWT | Renouveler le token |
| POST | `/logout` | JWT | Blacklister le token |
| GET | `/me` | JWT | Profil connecté |
| PATCH | `/profile` | JWT | Modifier son profil |
| GET | `/admin/exists` | — | Admin configuré ? |
| POST | `/admin/setup` | — | Créer le 1er admin |

### Demandes — `/api/requests`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | Client | Mes demandes |
| POST | `/` | Client | Créer une demande |
| GET | `/<id>` | Client | Détail d'une demande |
| POST | `/<id>/cancel` | Client | Annuler une demande |
| GET | `/admin/all` | Admin | Toutes les demandes |
| GET | `/admin/<id>` | Admin | Détail admin |
| PATCH | `/admin/<id>/status` | Admin | Changer le statut |

### Devis — `/api/quotations`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/request/<id>` | Client | Devis de ma demande |
| POST | `/<id>/accept` | Client | Accepter un devis |
| POST | `/<id>/reject` | Client | Refuser un devis |
| POST | `/admin/request/<id>` | Admin | Créer un devis |
| PUT | `/admin/<id>` | Admin | Modifier un devis |
| POST | `/admin/<id>/send` | Admin | Envoyer au client |
| POST | `/admin/compute` | Admin | Calculer les frais d'une ligne |

### Commandes — `/api/orders`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | Client | Mes commandes |
| GET | `/<id>` | Client | Détail d'une commande |
| POST | `/confirm-payment` | Client | Confirmer paiement → créer order |
| GET | `/admin/all` | Admin | Toutes les commandes |
| GET | `/admin/<id>` | Admin | Détail admin |
| PATCH | `/admin/<id>/status` | Admin | Mettre à jour le statut |
| PATCH | `/admin/<id>/tracking-number` | Admin | Numéro de suivi |
| POST | `/webhook/flutterwave` | FLW Secret | Webhook paiement |

### Vagues — `/api/waves`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | — | Liste des vagues actives |
| GET | `/<id>` | — | Détail d'une vague |
| POST | `/` | Admin | Créer une vague |
| PUT | `/<id>` | Admin | Modifier une vague |
| DELETE | `/<id>` | Admin | Désactiver une vague |

### Fournisseurs — `/api/suppliers`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | Admin | Liste des fournisseurs |
| GET | `/<id>` | Admin | Détail fournisseur |
| POST | `/` | Admin | Ajouter un fournisseur |
| PUT | `/<id>` | Admin | Modifier un fournisseur |
| DELETE | `/<id>` | Admin | Supprimer un fournisseur |
| GET | `/orders/order/<id>` | Admin | Commandes fournisseurs d'une order |
| POST | `/orders` | Admin | Créer une commande fournisseur |
| PATCH | `/orders/<id>/status` | Admin | Mettre à jour le statut |

### Galerie — `/api/gallery`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | — | Liste des items publiés |
| GET | `/<id>` | — | Détail d'un item |
| POST | `/` | Admin | Ajouter un item |
| PUT | `/<id>` | Admin | Modifier un item |
| DELETE | `/<id>` | Admin | Dépublier un item |

### Tarification — `/api/pricing`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | — | Config complète |
| GET | `/fees` | — | Frais de service |
| POST | `/fees` | Admin | Ajouter une tranche |
| PUT | `/fees/<id>` | Admin | Modifier une tranche |
| DELETE | `/fees/<id>` | Admin | Supprimer une tranche |
| GET | `/shipping` | — | Modes de transport |
| POST | `/shipping` | Admin | Ajouter un mode |
| PUT | `/shipping/<id>` | Admin | Modifier un mode |
| DELETE | `/shipping/<id>` | Admin | Désactiver un mode |
| GET | `/categories` | — | Catégories produit |
| POST | `/categories` | Admin | Ajouter une catégorie |
| PUT | `/categories/<id>` | Admin | Modifier une catégorie |
| DELETE | `/categories/<id>` | Admin | Supprimer une catégorie |
| PATCH | `/config` | Admin | Config système (maxKg…) |
| POST | `/simulate` | — | Simuler les frais d'un panier |

### Notifications — `/api/notifications`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | Client | Mes notifications |
| PATCH | `/<id>/read` | Client | Marquer comme lue |
| PATCH | `/read-all` | Client | Tout marquer lu |
| DELETE | `/<id>` | Client | Supprimer |

### Stats — `/api/stats`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | — | Stats publiques homepage |
| GET | `/admin` | Admin | Stats dashboard admin |
| GET | `/admin/stats-table` | Admin | Gestion table stats |
| POST | `/admin/stats-table` | Admin | Créer une stat |
| PUT | `/admin/stats-table/<id>` | Admin | Modifier une stat |

### Utilisateurs — `/api/users`

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/` | Admin | Liste des clients |
| GET | `/<id>` | Admin | Détail utilisateur |
| PATCH | `/<id>/deactivate` | Admin | Désactiver un compte |

---

## Exemples d'appels

### Créer le compte admin
```bash
curl -X POST http://localhost:5000/api/auth/admin/setup \
  -H "Content-Type: application/json" \
  -d '{"name":"NAMM Admin","phone":"677000000","password":"monMotDePasse"}'
```

### Connexion et récupération du token
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"677000000","password":"monMotDePasse"}'
# → { "data": { "accessToken": "eyJ..." } }
```

### Créer une demande (client)
```bash
curl -X POST http://localhost:5000/api/requests \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"productName":"Chaussures Nike x10","productLink":"https://1688.com/...","quantity":10}
    ],
    "waveId": "WAVE-002",
    "notes": "Tailles 40 à 45"
  }'
```

### Envoyer un devis (admin)
```bash
curl -X POST http://localhost:5000/api/quotations/admin/request/1 \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "validDays": 7,
    "items": [{
      "requestItemId": 1,
      "productName": "Chaussures Nike x10",
      "quantity": 10,
      "productCost": 185000,
      "shippingCost": 48000,
      "serviceFee": 27750,
      "customsFee": 18600,
      "total": 279350
    }]
  }'
```

---

## Production (Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```
