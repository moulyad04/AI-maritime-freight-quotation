import os
import json
import sqlite3
import datetime


class QuotationStore:
    """
    Persists every generated quotation to SQLite so admins can review,
    edit, accept, or reject them later.

    _init_db() also upgrades an older quotations.db automatically by adding
    any columns it is missing, so you do not need to delete the database.
    """

    NEW_COLUMNS = {
        "weather_risk": "TEXT DEFAULT ''",
        "customs_risk": "TEXT DEFAULT ''",
        "overall_risk": "TEXT DEFAULT ''",
        "details_json": "TEXT DEFAULT ''",
    }

    def __init__(self):
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(current_file)
            )
        )
        self.db_path = os.path.join(project_root, "app", "data", "quotations.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                cargo_type TEXT NOT NULL,
                containers INTEGER NOT NULL,
                recommended_route TEXT,
                route_score REAL,
                transit_time_days INTEGER,
                freight_per_container_usd REAL,
                total_freight_usd REAL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
            """
        )

        existing = {row[1] for row in conn.execute("PRAGMA table_info(quotations)")}
        for column, definition in self.NEW_COLUMNS.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE quotations ADD COLUMN {column} {definition}")

        conn.commit()
        conn.close()

    @staticmethod
    def _format(row):
        record = dict(row)
        raw = record.pop("details_json", "") or ""
        try:
            record["details"] = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            record["details"] = None
        return record

    def save(self, username: str, quotation: dict) -> int:
        risk = quotation.get("risk_report", {})
        details = {
            "route": {
                "route_type": quotation.get("route_type"),
                "distance_nm": quotation.get("distance_nm"),
                "transshipments": quotation.get("transshipments"),
                "base_freight_usd": quotation.get("base_freight_usd"),
            },
            "pricing": quotation.get("pricing"),
            "weather": quotation.get("weather"),
            "customs": quotation.get("customs"),
            "risk_report": risk,
            "margin": quotation.get("margin"),
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            INSERT INTO quotations (
                username, origin, destination, cargo_type, containers,
                recommended_route, route_score, transit_time_days,
                freight_per_container_usd, total_freight_usd,
                status, created_at,
                weather_risk, customs_risk, overall_risk, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                quotation["origin"],
                quotation["destination"],
                quotation["cargo_type"],
                quotation["containers"],
                quotation["recommended_route"],
                quotation["route_score"],
                quotation["transit_time_days"],
                quotation["freight_per_container_usd"],
                quotation["total_freight_usd"],
                "pending",
                datetime.datetime.utcnow().isoformat(),
                risk.get("weather_risk", ""),
                risk.get("customs_risk", ""),
                risk.get("overall_risk", ""),
                json.dumps(details, default=str),
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def list_all(self, date: str = None):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        if date:
            rows = conn.execute(
                "SELECT * FROM quotations WHERE substr(created_at, 1, 10) = ? ORDER BY id DESC",
                (date,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quotations ORDER BY id DESC"
            ).fetchall()

        conn.close()
        return [self._format(row) for row in rows]

    def list_by_user(self, username: str):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM quotations WHERE username = ? ORDER BY id DESC",
            (username,),
        ).fetchall()
        conn.close()
        return [self._format(row) for row in rows]

    def _get(self, conn, quotation_id):
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM quotations WHERE id = ?", (quotation_id,)
        ).fetchone()
        return self._format(row) if row else None

    def update_fields(self, quotation_id: int, fields: dict):
        allowed_columns = {
            "recommended_route",
            "containers",
            "freight_per_container_usd",
            "total_freight_usd",
            "transit_time_days",
        }
        updates = {
            k: v for k, v in fields.items()
            if k in allowed_columns and v is not None
        }

        conn = sqlite3.connect(self.db_path)
        if not updates:
            result = self._get(conn, quotation_id)
            conn.close()
            return result

        set_clause = ", ".join(f"{col} = ?" for col in updates)
        cursor = conn.execute(
            f"UPDATE quotations SET {set_clause} WHERE id = ?",
            list(updates.values()) + [quotation_id],
        )
        conn.commit()
        result = self._get(conn, quotation_id) if cursor.rowcount > 0 else None
        conn.close()
        return result

    def update_status(self, quotation_id: int, status: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "UPDATE quotations SET status = ? WHERE id = ?",
            (status, quotation_id),
        )
        conn.commit()
        result = self._get(conn, quotation_id) if cursor.rowcount > 0 else None
        conn.close()
        return result

    