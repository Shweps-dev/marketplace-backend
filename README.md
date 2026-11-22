#  Marketplace Backend

An e-commerce backend built with **Django REST Framework**, **MySQL**, **Celery**, and **Docker**.

##  Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | Django 5 + DRF | Batteries-included, admin panel out of the box |
| Database | MySQL 8.0 | Relational data with complex joins and FK constraints |
| Task Queue | Celery + Redis | Async email sending without blocking HTTP responses |
| Auth | JWT (SimpleJWT) | Stateless authentication, refresh tokens |
| Docs | drf-spectacular | Auto-generated Swagger UI |
| Monitoring | Flower | Real-time Celery task monitoring |
| Container | Docker Compose | One command to run everything |

##  Architecture

```
marketplace/
├── apps/
│   ├── users/          # Custom User model, addresses, JWT auth
│   ├── products/       # Categories (nested), products, reviews, filters
│   ├── cart/           # Shopping cart with stock validation
│   └── orders/         # Orders, status history, Celery email tasks
├── config/
│   ├── settings.py     # All configuration (DB, Celery, JWT, email)
│   ├── celery.py       # Celery app setup
│   └── urls.py         # Root URL router
├── docker-compose.yml  # db + redis + api + celery + flower
└── Dockerfile
```

##  Database Schema (MySQL)

```
users ──────────────────────────────────────────────────┐
  id, email, username, phone, avatar                     │
                                                         │
addresses (FK → users)                                   │
  id, user_id, full_name, street, city, postal_code      │
                                                         │
categories (self-referential FK for nesting)             │
  id, name, slug, parent_id, image                       │
                                                         │
products (FK → categories)                               │
  id, category_id, name, slug, price,                    │
  discount_percent, stock, is_active                     │
                                                         │
product_images (FK → products)                           │
  id, product_id, image, is_main, order                  │
                                                         │
reviews (FK → products, users)                           │
  id, product_id, user_id, rating, comment               │
                                                         │
carts (OneToOne → users)                                 │
  id, user_id                                            │
                                                         │
cart_items (FK → carts, products)                        │
  id, cart_id, product_id, quantity                      │
                                                         │
orders (FK → users, addresses) ─────────────────────────┘
  id, user_id, shipping_address_id,
  status, total_price, notes

order_items (FK → orders, products)
  id, order_id, product_id,
  product_name, price_at_purchase, quantity  ← price snapshot!

order_status_history (FK → orders)
  id, order_id, old_status, new_status, changed_by_id, changed_at
```

##  How Celery Works

```
User places order
       │
       ▼
Django creates Order in MySQL
       │
       ▼
send_order_confirmation_email.delay(order.id)
       │         └── puts task in Redis queue instantly
       │
       ▼
HTTP 201 response ← user gets this immediately, no waiting
       
(meanwhile, in background...)
       
Celery Worker picks up task from Redis
       │
       ▼
Fetches order from MySQL
       │
       ▼
Sends confirmation email
       │
       ▼
Stores result in django_celery_results table
```

##  Quick Start

```bash
git clone https://github.com/Shweps-dev/marketplace-backend.git
cd marketplace
cp .env.example .env
docker-compose up --build
```

Services:
- **API + Swagger**: http://localhost:8001/docs/
- **Django Admin**: http://localhost:8001/admin/
- **Flower (Celery monitor)**: http://localhost:5555/

### Create superuser (for admin panel)

```bash
docker-compose exec api python manage.py createsuperuser
```

##  API Endpoints

### Auth
```
POST /api/v1/auth/register/        Register new user
POST /api/v1/auth/login/           Login → access + refresh tokens
POST /api/v1/auth/token/refresh/   Refresh access token
GET  /api/v1/auth/profile/         Get/update profile
GET  /api/v1/auth/addresses/       List addresses
POST /api/v1/auth/addresses/       Add delivery address
```

### Products
```
GET /api/v1/products/categories/   Category tree (nested)
GET /api/v1/products/              Product list
GET /api/v1/products/?search=iphone&category=1&price_min=100&price_max=999&in_stock=true
GET /api/v1/products/{slug}/       Product detail with images and reviews
GET /api/v1/products/{slug}/reviews/   List reviews
POST /api/v1/products/{slug}/reviews/  Add review (auth required)
```

### Cart
```
GET    /api/v1/cart/               View cart with totals
POST   /api/v1/cart/               Add item to cart
DELETE /api/v1/cart/               Clear cart
PATCH  /api/v1/cart/items/{id}/    Update item quantity
DELETE /api/v1/cart/items/{id}/    Remove item from cart
```

### Orders
```
GET  /api/v1/orders/               Order history
POST /api/v1/orders/               Create order from cart → triggers Celery email
GET  /api/v1/orders/{id}/          Order detail with status history
POST /api/v1/orders/{id}/cancel/   Cancel order
```

##  Filtering & Search

```bash
# Search by name/description
GET /api/v1/products/?search=laptop

# Filter by price range
GET /api/v1/products/?price_min=100&price_max=500

# Only in-stock items
GET /api/v1/products/?in_stock=true

# Only discounted
GET /api/v1/products/?has_discount=true

# Sort by price (ascending)
GET /api/v1/products/?ordering=price

# Sort by newest
GET /api/v1/products/?ordering=-created_at

# Combine
GET /api/v1/products/?category=2&price_max=300&in_stock=true&ordering=price
```

##  Environment Variables

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | Debug mode (True/False) |
| `MYSQL_DATABASE` | Database name |
| `MYSQL_USER` | Database user |
| `MYSQL_PASSWORD` | Database password |
| `REDIS_URL` | Redis connection URL |
| `EMAIL_HOST_USER` | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | Gmail app password |
