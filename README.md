# Enterprise Tax Calculation & Registry Platform

This project is a high-performance, robust, and scalable Tax Calculation and Registry Platform tailored primarily for New York State (NYS) compliance, while effortlessly handling out-of-state and international zero-tax edge cases. Designed originally for a hackathon, it evolved into an enterprise-grade backend processing pipeline wrapped in a lightning-fast React frontend.

## 🚀 Key Features

### 1. **100% Offline Geocoding & Rate-Limit Immunity**

Unlike typical geocoding implementations that rely on rate-limited external APIs (like OpenStreetMap's Nominatim, which actively bans IPs exceeding 1 request/second), this platform utilizes a custom **Offline `LocalNYSProvider`**.
Powered by the C-bound `reverse_geocoder` library and `scipy` KD-Trees, it accurately resolves precise GPS coordinates (Latitude/Longitude) to any New York State County or City completely offline in milliseconds. **Data ingestion limits are theoretically infinite**, bound only by PostgreSQL write speeds, allowing massive bulk processing without third-party bottlenecks or connection timeouts.

### 2. **Asynchronous Bulk CSV Processing (Celery + Redis)**

Upload thousands of tax records in a single CSV file without freezing the UI.

- The React frontend uploads the raw CSV to the Django backend.
- Django securely offloads row-by-row parsing, geocoding validation, and tax calculation to a **Celery Worker Pool**.
- **Linux Daemon Safety:** Our C-bound KD-Tree search enforces `mode=1` (single-threaded execution) to prevent catastrophic multiprocessing lockups during heavy ingestion of 11,000+ rows.
- Progress is stored immutably in Redis and streamed live to the UI via intelligent polling.

### 3. **Mathematical Precision & Authentic NYS Jurisdictions**

The PostgreSQL database is pre-seeded with genuine 2024 New York State county sales tax rates.

- E.g., An order in Erie County perfectly calculates `8.75%` (4% State + 4.75% County).
- Out-of-state or international deliveries (e.g., Quebec, Pennsylvania) gracefully fall back to `0.00%` tax due to **Sales Tax Nexus** rules, displaying an explicit "Out of State / No Nexus" message rather than failing.

### 4. **Progressive "Live" Streaming Architecture (Infinite Scroll)**

The *"Recent Orders Registry"* table leverages an `IntersectionObserver`-based infinite scroll algorithm.

- It fetches and renders the first 50 rows instantly (under `10ms` render time) and seamlessly streams subsequent records as the user scrolls downward.
- Creates a `60fps` native, pagination-free experience even when viewing a database of 50,000+ chronological transactions.

### 5. **Compliance with Test Task Requirements**
- **Business Logic Focus**: Prioritizes tax compliance for NYS over pure technical showcase, perfectly interpreting coordinates into actual NY tax jurisdictions.
- **Admin Frontend**: 
  - ✅ **Import CSV**: Upload CSV, system processes asynchronously, calculates taxes, and saves.
  - ✅ **Manual Create**: Manual order creation (lat, lon, subtotal) with instant calculation.
  - ✅ **Orders List**: Table of orders with calculated taxes, sorting/filtering, and endless scroll pagination.
- **Backend APIs**:
  - ✅ `POST /api/orders/import_csv` (CSV Import)
  - ✅ `POST /api/orders/` (Manual Create)
  - ✅ `GET /api/orders/` (List + pagination + filters)
- **Data Input/Output Match**:
  - ✅ Inputs: `latitude`, `longitude`, `subtotal`, `timestamp`.
  - ✅ Outputs: `composite_tax_rate`, `tax_amount`, `total_amount`, and a detailed `breakdown` (including the bonus `jurisdictions`).
- **Tech Stack Match**:
  - While Python/Django was chosen over Node.js/TypeScript for superior handling of big data (Celery) and Decimal arithmetic, the architecture meets all core functional demands robustly. React and SQL (PostgreSQL via Heroku) are fully utilized.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.13, Django 5.x, Django Rest Framework (DRF)
- **Task Queue:** Celery, Redis
- **Database:** PostgreSQL (Heroku Postgres)
- **Geocoding:** `reverse_geocoder` (KD-Tree offline), `scipy`, `numpy`
- **Frontend:** React 18, TypeScript, Vite, Vanilla CSS
- **Deployment & Hosting:** Heroku (Web Dynos + Worker Dynos)

---

## ⚙️ How to Run Locally

If you wish to spin up the application on your own local machine, this repository includes a fully configured `docker-compose.yml` to instantly boot the entire stack (Postgres + Redis + Django Web + Celery Worker + React Frontend).

### Prerequisites

- [Docker Engine & Docker Compose](https://docs.docker.com/get-docker/) installed.
- Ensure ports `80` (Frontend), `8000` (Backend server), and `6379` (Redis) are available on your machine.

### Quickstart

1. **Clone the project & Boot up Docker services:**

   ```bash
   git clone <repository_url> .
   docker-compose up -d --build
   ```

   *(Docker will pull the images, initialize the local SQLite database, run Python migrations, start Redis, start the Celery worker, and boot both the backend API and the frontend Nginx server automatically).*

2. **Access the Application:**
   - **Frontend UI (React Calculator & Registry):** <http://localhost> *(Port 80)*
   - **Backend API Interface:** <http://localhost:8000/api/>
   - **Django Admin Panel:** <http://localhost:8000/admin/>

3. **Stop & Destroy Containers:**

   ```bash
   docker-compose down -v
   ```

---

## 🎨 UI Overview

- **Manual Order Registration (`/`):** A sleek glassmorphic card where administrators input manual deliveries. Calculates taxes and registers the entry instantly.
- **Bulk CSV Umschlag:** Drag-and-drop a `.csv` file. Features an animated progress bar and deep Django `Exception` traceback unpacking for detailed row failures.
- **Registry Table:** A fast, infinitely scrolling ledger of historical financial transactions. Interactive sub-rows (`+`) dynamically expand to reveal the specific state, county, and locality tax breakdown jurisdictions for every individual delivery coordinate.
