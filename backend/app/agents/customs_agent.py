class CustomsAgent:
    """
    Customs Validation Workflow: checks which documents a shipment needs
    (based on cargo type and destination), compares them with the documents
    the customer says they already have, and flags anything missing.

    The rules below are simplified sample rules for this project, not a
    substitute for real customs advice.
    """

    LEVELS = ["LOW", "MEDIUM", "HIGH"]

    ALL_DOCUMENTS = [
        "Commercial Invoice",
        "Packing List",
        "Certificate of Origin",
        "Import Licence",
        "Type Approval Certificate",
        "Health / Phytosanitary Certificate",
        "Hazmat Declaration (IMDG)",
        "EORI Number",
        "ISF Filing",
    ]

    CARGO_RULES = {
        "general": {
            "base": "LOW",
            "docs": ["Commercial Invoice", "Packing List"],
        },
        "textiles": {
            "base": "LOW",
            "docs": ["Commercial Invoice", "Packing List", "Certificate of Origin"],
        },
        "electronics": {
            "base": "LOW",
            "docs": ["Commercial Invoice", "Packing List", "Certificate of Origin"],
        },
        "machinery": {
            "base": "MEDIUM",
            "docs": ["Commercial Invoice", "Packing List", "Import Licence"],
        },
        "automotive": {
            "base": "MEDIUM",
            "docs": ["Commercial Invoice", "Packing List", "Type Approval Certificate"],
        },
        "perishables": {
            "base": "MEDIUM",
            "docs": [
                "Commercial Invoice",
                "Packing List",
                "Health / Phytosanitary Certificate",
            ],
        },
        "chemicals": {
            "base": "HIGH",
            "docs": ["Commercial Invoice", "Packing List", "Hazmat Declaration (IMDG)"],
        },
    }

    EU_UK_PORTS = {"rotterdam", "hamburg", "antwerp", "felixstowe", "genoa", "piraeus"}
    US_PORTS = {"new york", "los angeles"}

    def _rule(self, cargo_type):
        return self.CARGO_RULES.get(
            cargo_type.strip().lower(), self.CARGO_RULES["general"]
        )

    def required_documents(self, cargo_type, destination):
        """Documents customs will ask for on this cargo + destination."""
        required = list(self._rule(cargo_type)["docs"])
        dest = destination.strip().lower()
        if dest in self.EU_UK_PORTS:
            required.append("EORI Number")
        if dest in self.US_PORTS:
            required.append("ISF Filing")
        return required

    def validate_shipment(self, cargo_type, destination, containers, documents_ready=None):
        documents_ready = documents_ready or []
        ready_lookup = {d.strip().lower() for d in documents_ready}

        rule = self._rule(cargo_type)
        required = self.required_documents(cargo_type, destination)

        missing = [d for d in required if d.lower() not in ready_lookup]
        provided = [d for d in required if d.lower() in ready_lookup]

        issues = [f"Missing required document: {d}" for d in missing]
        if cargo_type.strip().lower() == "chemicals":
            issues.append(
                "Dangerous goods: carrier acceptance and IMDG-compliant packaging are required."
            )
        if containers >= 50:
            issues.append(
                "Large shipment: a higher chance of customs inspection is likely."
            )

        # Start from the cargo's base risk, then escalate for missing documents.
        level_index = self.LEVELS.index(rule["base"])
        if len(missing) >= 1:
            level_index += 1
        if len(missing) >= 3:
            level_index += 1
        customs_risk = self.LEVELS[min(level_index, 2)]

        clearance_days = {"LOW": 1, "MEDIUM": 3, "HIGH": 5}[customs_risk]

        return {
            "status": "success",
            "cargo_type": cargo_type,
            "destination": destination,
            "required_documents": required,
            "provided_documents": provided,
            "missing_documents": missing,
            "issues": issues,
            "validation_status": "READY" if not missing else "ACTION REQUIRED",
            "customs_risk": customs_risk,
            "estimated_clearance_days": clearance_days,
        }