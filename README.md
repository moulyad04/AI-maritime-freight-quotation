# Agentic AI for Maritime Freight Pricing and Route Optimization

A full-stack web app that produces priced, risk-checked freight quotations for container shipments. Several rule-based "agents" work together: route selection, pricing, weather risk, customs validation, a combined shipment risk report, and a margin calculation. Customers request quotes, and an admin reviews, edits, accepts or rejects them.

Built as an Infosys virtual internship project (Milestones 1 and 2).

---

## Features

**Customer**
- Create an account and log in
- Choose origin, destination, cargo type and number of containers (dropdowns are built from the route data)
- See only the customs documents that apply to the chosen cargo and destination, and tick the ones you already have
- Get a quotation with the recommended route, price, transit time, alternative routes, a weather assessment, a customs check and an overall risk level
- See a history of your own quotations and their status

**Admin**
- Sees every quotation from every customer
- Filters quotations by date
- Edits a quotation's route, containers, price and transit days
- Accepts or rejects quotations
- Opens a full internal breakdown, including cost and margin figures
- Sees summary cards (total, pending, accepted, rejected, total value)

Margin and cost figures are never sent to customers. The backend removes them from every customer response, so they cannot be read from the browser's network tab either.

---

## How a quotation is built

```
Customer request
      |
  Route Agent        scores every matching route and picks the best one
      |
  Pricing Agent      adds fuel, port and risk surcharges, then applies the demand factor
      |
  Weather Agent      rates weather risk for the chosen route
      |
  Customs Agent      checks required documents against the ones the customer has
      |
  Shipment Risk      combines weather and customs into one overall risk level
      |
  Margin Agent       applies the target margin plus a small uplift for risky shipments
      |
  Final quotation
```

**Route score** (higher is better): transit time 40%, distance 25%, transshipments 35%.

**Pricing:**
```
operating cost  = base freight + fuel surcharge + port charge + risk surcharge
adjusted cost   = operating cost x demand factor
final price     = adjusted cost x (1 + (target margin + risk uplift) / 100)
```
The risk uplift is 0% for LOW, 2% for MEDIUM and 5% for HIGH overall risk.

**Weather risk:** wind, wave height, visibility and storm probability each score 1 to 3 points. A total of 10 or more is HIGH, 7 to 9 is MEDIUM, and below 7 is LOW.

**Customs risk:** starts from a base level for the cargo type (for example Chemicals start at HIGH), then rises as required documents are missing.

---

## Tech stack

| Part | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn, pandas, Pydantic |
| Database | SQLite (users and quotations), CSV files (routes, pricing, weather) |
| Frontend | React (Vite) |
| Auth | Salted PBKDF2 password hashing and bearer tokens |

---

## Project structure

```
infosys1/
├── backend/
│   ├── main.py                       API endpoints
│   ├── generate_datasets.py          builds the 250-row CSV datasets
│   └── app/
│       ├── models.py                 request models
│       ├── agents/
│       │   ├── route_agent.py
│       │   ├── pricing_agent.py
│       │   ├── weather_agent.py
│       │   ├── customs_agent.py
│       │   └── margin_agent.py
│       ├── services/
│       │   ├── quotation_service.py  runs the full agent pipeline
│       │   ├── quotation_store.py    saves quotations to SQLite
│       │   ├── shipment_risk_service.py
│       │   ├── customer_view.py      strips internal figures for customers
│       │   └── auth_service.py
│       └── data/
│           ├── routes.csv
│           ├── pricing.csv
│           └── weather.csv
└── frontend/
    └── src/
        ├── App.jsx                   customer dashboard
        ├── AdminDashboard.jsx
        ├── AuthPage.jsx
        ├── QuotationDetails.jsx
        ├── App.css
        └── services/
            ├── authApi.js
            └── routeApi.js
```

---

## Getting started

You need Python 3.9 or newer and Node.js 16 or newer.

### 1. Backend

```bash
cd backend
pip install fastapi uvicorn pandas pydantic
python generate_datasets.py        # only needed if the CSV files are missing
python -m uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API docs are at `http://127.0.0.1:8000/docs`.

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

Both servers must be running at the same time.

### 3. Log in

- **Customer:** use "Create an account" on the first screen.
- **Admin:** log in with `admin` / `admin123`. This account is created automatically on the first run.

---

## API overview

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/signup` | public | Create a customer account |
| POST | `/api/auth/login` | public | Log in |
| POST | `/api/auth/logout` | logged in | Log out |
| GET | `/api/options` | logged in | Ports, lanes and cargo types for the form |
| GET | `/api/customs/required` | logged in | Documents required for a cargo and destination |
| GET | `/api/weather/{route_id}` | logged in | Weather assessment for a route |
| POST | `/api/routes/analyze` | logged in | Route analysis only |
| POST | `/api/quotations/generate` | logged in | Generate and save a quotation |
| GET | `/api/quotations/mine` | logged in | Your own quotations |
| GET | `/api/quotations` | admin | All quotations (optional `?date=YYYY-MM-DD`) |
| PUT | `/api/quotations/{id}` | admin | Edit a quotation |
| POST | `/api/quotations/{id}/decision` | admin | Accept or reject a quotation |

---

## Datasets

`routes.csv`, `pricing.csv` and `weather.csv` each hold 250 rows. The first 10 rows of each are the original hand-written sample rows. The rest are generated by `generate_datasets.py` using a fixed random seed, so everyone gets the same files. **The generated values are illustrative sample data, not real market data.**

To regenerate them:
```bash
cd backend
python generate_datasets.py
```

---

## Notes and limitations

- **Demo-level security.** The admin password is hardcoded, and login sessions are kept in memory, so they reset whenever the backend restarts. After a restart, log out and log back in. Before any real deployment, use a proper user store, JWT tokens, secrets from environment variables, and HTTPS.
- **Customs rules are simplified.** The document requirements per cargo type and destination are sample rules for this project, not real customs advice.
- **Documents are self-declared.** Customers tick the documents they have. Nothing is uploaded or verified.
- **Sample data.** Prices, distances and weather values are synthetic.

---


## Author

Moulya D, Infosys Virtual Internship, Batch 3.
