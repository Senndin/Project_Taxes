# NY State Sales Tax Calculation Service

## Prerequisites
Ensure the following are installed on your MacOS environment:
1. **Python 3.10+**
2. **Docker** (For running Redis locally) or `redis-server` installed via Homebrew.
3. **cURL** or Postman (for testing the API).

---

## 🚀 Step 1: Clone the Repository and Setup Environment

1. Navigate to the project folder (or create it):
   ```bash
   cd /Users/denischernokur/Documents/programming/Hackaton/Project_Taxes
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   *(If you haven't already, ensure Django, DRF, Celery, Redis, etc., are installed)*
   ```bash
   pip install django djangorestframework celery redis psycopg2-binary requests django-environ
   ```

---

## 🚀 Step 2: Configure Environment Variables

1. Inside your project root directory, ensure you have a `.env` file containing the following configurations.
   *(This configures Django to run in debug mode, use SQLite locally, and connect to a local Redis instance)*

   Create or verify `.env`:
   ```env
   DEBUG=True
   SECRET_KEY=django-insecure-local-dev-key
   DATABASE_URL=sqlite:///db.sqlite3
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/1
   ```

---

## 🚀 Step 3: Initialize the Database

1. Apply the Django migrations. This initializes your local SQLite database with all the models (`Order`, `TaxRateAdmin`, `GeocodeCache`, `ImportJob`):

   ```bash
   # Make sure your virtual environment is still activated
   python manage.py makemigrations
   python manage.py migrate
   ```

2. *(Optional)* Create an admin superuser to manage `TaxRateAdmin` records manually:
   ```bash
   python manage.py createsuperuser
   ```

---

## 🚀 Step 4: Start Redis (Message Broker)

Celery requires Redis to act as a message broker to assign background CSV import tasks.

**Option A (Using Docker - Recommended):**
Open a new terminal window and run:
```bash
docker run -d -p 6379:6379 redis:alpine
```

**Option B (Using Homebrew natively on Mac):**
```bash
brew install redis
brew services start redis
```

---

## 🚀 Step 5: Start the Background Worker (Celery)

To process bulk CSV uploads in the background, you must start the Celery worker process.
1. Open a **second** terminal window.
2. Navigate to the project root and activate exactly the same virtual environment.
3. Start the worker:

```bash
cd /Users/denischernokur/Documents/programming/Hackaton/Project_Taxes
source .venv/bin/activate

# Execute the celery worker
celery -A config worker -l info
```
*You should see a splash screen saying `[config] v5.x.x` indicating Celery successfully connected to Redis.*

---

## 🚀 Step 6: Start the Django API Server

You now need the web server that receives your REST API requests.
1. Open a **third** terminal window. 
2. Activate the virtual environment.
3. Start the Django webserver:

```bash
cd /Users/denischernokur/Documents/programming/Hackaton/Project_Taxes
source .venv/bin/activate

python manage.py runserver
```

*(You will see `Starting development server at http://127.0.0.1:8000/`)*

---

## 🚀 Step 7: Testing the Built Application

With your API Server (Step 6) and Celery Worker (Step 5) running concurrently, you can now interact with the system.

### 1. Calculate a Single Order
Send a JSON payload to the `/api/orders/` endpoint.

```bash
curl -s -X POST http://127.0.0.1:8000/api/orders/ \
     -H "Content-Type: application/json" \
     -d '{
           "lat": 40.650002,
           "lon": -73.949997,
           "subtotal": "100.00"
         }'
```

### 2. Import a Bulk CSV
Create a dummy CSV file (e.g. `import.csv` with lat, lon, subtotal headers) and send it as a multipart form:

```bash
curl -X POST http://127.0.0.1:8000/api/orders/import_csv/ \
     -F "file=@import.csv"
```
*Wait a few seconds for the background worker to process it. It will return a `job_id`.*

### 3. Check CSV Import Status
Use the `job_id` (e.g., `1`) to check if the bulk import succeeded:

```bash
curl -X GET http://127.0.0.1:8000/api/imports/1/
```

> **Note on Nominatim API rate limits:**
> Since this relies on a free, public OSM Geocoder out-of-the-box (`NominatimProvider`), excessive requests during testing might temporarily return HTTP 403 (Forbidden) if OpenStreetMap blacklists your IP. If you see HTTP 403 in your error reports, it means the app is functionally perfect, but the third-party proxy blocked you. During heavy local testing, it is recommended to substitute the mock provider we used in `test_service.py`.
