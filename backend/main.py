import secrets

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    RouteRequest,
    QuotationRequest,
    SignupRequest,
    LoginRequest,
    DecisionRequest,
    QuotationUpdateRequest,
)
from app.agents.route_agent import RouteAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.customs_agent import CustomsAgent
from app.services.quotation_service import QuotationService
from app.services.quotation_store import QuotationStore
from app.services.auth_service import AuthService
from app.services.customer_view import customer_quotation, customer_record
from app.services.freight_intelligence_service import FreightIntelligenceService

app = FastAPI(
    title="Agentic Maritime Brokerage Platform",
    description="AI-powered maritime freight quotation platform",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

route_agent = RouteAgent()
weather_agent = WeatherAgent()
customs_agent = CustomsAgent()
quotation_service = QuotationService()
intelligence_service = FreightIntelligenceService(quotation_service)
quotation_store = QuotationStore()
auth_service = AuthService()

auth_service.seed_default_admin()

# In-memory session store: token -> {"username": ..., "role": ...}
# Tokens reset whenever the server restarts.
ACTIVE_TOKENS = {}


def require_auth(authorization: str = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.split(" ", 1)[1]
    session = ACTIVE_TOKENS.get(token)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please log in again."
        )

    return session


def require_admin(session: dict = Depends(require_auth)):
    if session["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return session


@app.get("/")
def home():
    return {
        "message": "Agentic Maritime Brokerage API is running",
        "project": "Maritime Freight Quotation Platform",
        "milestone": "Milestone 3 - Freight Intelligence Engine"
    }


# ------------------------------------------------------------------ auth

@app.post("/api/auth/signup")
def signup(request: SignupRequest):
    try:
        auth_service.create_user(request.username, request.password, role="customer")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    token = secrets.token_hex(16)
    ACTIVE_TOKENS[token] = {"username": request.username, "role": "customer"}

    return {
        "status": "success",
        "message": "Account created successfully",
        "token": token,
        "username": request.username,
        "role": "customer"
    }


@app.post("/api/auth/login")
def login(request: LoginRequest):
    role = auth_service.verify_user(request.username, request.password)
    if role is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_hex(16)
    ACTIVE_TOKENS[token] = {"username": request.username, "role": role}

    return {
        "status": "success",
        "token": token,
        "username": request.username,
        "role": role
    }


@app.post("/api/auth/logout")
def logout(authorization: str = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        ACTIVE_TOKENS.pop(authorization.split(" ", 1)[1], None)
    return {"status": "success", "message": "Logged out"}


# -------------------------------------------------------------- reference

@app.get("/api/options")
def get_options(session: dict = Depends(require_auth)):
    """Dropdown data for the quotation form, built from routes.csv."""
    routes = route_agent.routes
    lanes = {}
    for origin, group in routes.groupby("origin"):
        lanes[origin] = sorted(group["destination"].unique().tolist())

    return {
        "origins": sorted(lanes.keys()),
        "lanes": lanes,
        "cargo_types": [
            "General", "Textiles", "Electronics", "Machinery",
            "Automotive", "Perishables", "Chemicals"
        ],
        "documents": CustomsAgent.ALL_DOCUMENTS,
        "total_routes": int(len(routes)),
    }


@app.get("/api/weather/{route_id}")
def get_weather(route_id: str, session: dict = Depends(require_auth)):
    result = weather_agent.assess_weather(route_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/api/customs/required")
def customs_required(
    cargo_type: str,
    destination: str,
    session: dict = Depends(require_auth)
):
    """Which customs documents this cargo + destination needs."""
    return {
        "cargo_type": cargo_type,
        "destination": destination,
        "required_documents": customs_agent.required_documents(cargo_type, destination),
    }


# ------------------------------------------------------------- quotations

@app.post("/api/routes/analyze")
def analyze_route(request: RouteRequest, session: dict = Depends(require_auth)):
    return route_agent.analyze_route(
        origin=request.origin,
        destination=request.destination,
        cargo_type=request.cargo_type,
        containers=request.containers
    )


@app.post("/api/quotations/generate")
def generate_quotation(
    request: QuotationRequest,
    session: dict = Depends(require_auth)
):
    result = quotation_service.generate_quotation(
        origin=request.origin,
        destination=request.destination,
        cargo_type=request.cargo_type,
        containers=request.containers,
        documents_ready=request.documents_ready
    )

    if result["status"] != "success":
        return result

    # Save the full internal data (admins need it) ...
    quotation_id = quotation_store.save(session["username"], result)
    result["id"] = quotation_id
    result["quotation_status"] = "pending"

    # ... but customers never receive margin / cost figures.
    if session["role"] == "admin":
        return result
    return customer_quotation(result)


@app.post("/api/intelligence/generate")
def generate_intelligence(
    request: QuotationRequest,
    session: dict = Depends(require_auth)
):
    """Unified route + pricing + risk view. Cost/profit only for admins."""
    return intelligence_service.generate_freight_intelligence(
        origin=request.origin,
        destination=request.destination,
        cargo_type=request.cargo_type,
        containers=request.containers,
        documents_ready=request.documents_ready,
        is_admin=(session["role"] == "admin"),
    )


@app.get("/api/quotations/mine")
def my_quotations(session: dict = Depends(require_auth)):
    rows = quotation_store.list_by_user(session["username"])
    return [customer_record(row) for row in rows]


@app.get("/api/quotations")
def all_quotations(date: str = None, session: dict = Depends(require_admin)):
    """Optional ?date=YYYY-MM-DD filter."""
    return quotation_store.list_all(date=date)


@app.post("/api/quotations/{quotation_id}/decision")
def decide_quotation(
    quotation_id: int,
    request: DecisionRequest,
    session: dict = Depends(require_admin)
):
    updated = quotation_store.update_status(quotation_id, request.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return updated


@app.put("/api/quotations/{quotation_id}")
def update_quotation(
    quotation_id: int,
    request: QuotationUpdateRequest,
    session: dict = Depends(require_admin)
):
    updated = quotation_store.update_fields(quotation_id, request.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return updated