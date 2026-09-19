"""Small repeatable migrations for NATBIRZHA live databases."""

from collections.abc import Awaitable, Callable

from sqlalchemy import text


Migration = Callable[[object], Awaitable[None]]


async def _table_exists(conn, table: str) -> bool:
    if conn.dialect.name == "sqlite":
        row = await conn.execute(
            text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table},
        )
    else:
        row = await conn.execute(
            text("SELECT 1 FROM information_schema.tables WHERE table_schema=current_schema() AND table_name=:name"),
            {"name": table},
        )
    return row.first() is not None


async def _columns(conn, table: str) -> set[str]:
    if not await _table_exists(conn, table):
        return set()
    if conn.dialect.name == "sqlite":
        result = await conn.execute(text(f'PRAGMA table_info("{table}")'))
        return {row[1] for row in result.fetchall()}
    result = await conn.execute(
        text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema=current_schema() AND table_name=:table
        """),
        {"table": table},
    )
    return {row[0] for row in result.fetchall()}


async def _add_columns(conn, table: str, columns: dict[str, str]) -> None:
    if not await _table_exists(conn, table):
        return
    existing = await _columns(conn, table)
    for name, ddl in columns.items():
        if name not in existing:
            await conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {ddl}'))


async def _ensure_version_table(conn) -> None:
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS nat_schema_versions (
            version VARCHAR(80) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))


async def _is_applied(conn, version: str) -> bool:
    result = await conn.execute(
        text("SELECT 1 FROM nat_schema_versions WHERE version=:version"),
        {"version": version},
    )
    return result.first() is not None


async def _mark_applied(conn, version: str) -> None:
    await conn.execute(
        text("INSERT INTO nat_schema_versions (version) VALUES (:version)"),
        {"version": version},
    )


async def _migrate_p2_columns(conn) -> None:
    await _add_columns(conn, "nat_companies", {
        "pvc_balance": "INTEGER NOT NULL DEFAULT 0",
        "military_rating": "INTEGER NOT NULL DEFAULT 1000",
    })
    await _add_columns(conn, "nat_tournaments", {
        "tournament_type": "VARCHAR(20) NOT NULL DEFAULT 'AUTO'",
        "reward_first_pvc": "INTEGER NOT NULL DEFAULT 150",
        "reward_second_pvc": "INTEGER NOT NULL DEFAULT 100",
        "reward_third_pvc": "INTEGER NOT NULL DEFAULT 70",
        "created_by_user_id": "INTEGER",
        "resolved_at": "TIMESTAMP",
    })
    await _add_columns(conn, "nat_tournament_participants", {
        "initial_strength": "BIGINT NOT NULL DEFAULT 0",
        "final_strength": "BIGINT NOT NULL DEFAULT 0",
        "initial_rating": "INTEGER NOT NULL DEFAULT 1000",
        "final_rating": "INTEGER NOT NULL DEFAULT 1000",
        "wins": "INTEGER NOT NULL DEFAULT 0",
        "losses": "INTEGER NOT NULL DEFAULT 0",
        "prize_pvc": "INTEGER NOT NULL DEFAULT 0",
    })


async def _migrate_p2_data(conn) -> None:
    company_columns = await _columns(conn, "nat_companies")
    if {"nat_balance", "pvc_balance"}.issubset(company_columns):
        await conn.execute(text("""
            UPDATE nat_companies
            SET pvc_balance = nat_balance
            WHERE pvc_balance = 0 AND nat_balance <> 0
        """))

    required_tables = {"nat_armies", "nat_army_units"}
    if not all([await _table_exists(conn, table) for table in required_tables]):
        return
    prefix = "INSERT OR IGNORE" if conn.dialect.name == "sqlite" else "INSERT"
    suffix = "" if conn.dialect.name == "sqlite" else " ON CONFLICT (company_id, unit_type) DO NOTHING"
    for legacy_column, unit_type in (
        ("infantry", "infantry"),
        ("tanks", "tanks"),
        ("drones", "drones"),
        ("air_defense", "air_defense"),
    ):
        await conn.execute(text(f"""
            {prefix} INTO nat_army_units
                (company_id, unit_type, quantity, level, readiness, experience, updated_at)
            SELECT company_id, :unit_type, {legacy_column}, 1, 10000, 0, CURRENT_TIMESTAMP
            FROM nat_armies WHERE {legacy_column} > 0
            {suffix}
        """), {"unit_type": unit_type})


async def _migrate_p2_financial_columns(conn) -> None:
    await _add_columns(conn, "nat_state_bonds", {
        "coupon_interval_days": "INTEGER NOT NULL DEFAULT 7",
        "status": "VARCHAR(30) NOT NULL DEFAULT 'OFFERING'",
        "next_coupon_at": "TIMESTAMP",
        "maturity_at": "TIMESTAMP",
        "settled_at": "TIMESTAMP",
    })
    await _add_columns(conn, "nat_state_bond_holdings", {
        "reserved_quantity": "INTEGER NOT NULL DEFAULT 0",
    })
    if await _table_exists(conn, "nat_state_bonds"):
        await conn.execute(text("""
            UPDATE nat_state_bonds
            SET status = CASE
                WHEN is_active = 0 AND remaining_volume = 0 THEN 'ACTIVE'
                WHEN remaining_volume < total_volume THEN 'ACTIVE'
                ELSE 'OFFERING'
            END
            WHERE status IS NULL OR status = '' OR (status = 'OFFERING' AND remaining_volume < total_volume)
        """))
        if conn.dialect.name == "sqlite":
            await conn.execute(text("""
                UPDATE nat_state_bonds
                SET maturity_at = datetime(created_at, '+' || maturity_days || ' days'),
                    next_coupon_at = datetime(
                        created_at,
                        '+' || CASE WHEN maturity_days < coupon_interval_days
                            THEN maturity_days ELSE coupon_interval_days END || ' days'
                    )
                WHERE maturity_at IS NULL OR next_coupon_at IS NULL
            """))
        else:
            await conn.execute(text("""
                UPDATE nat_state_bonds
                SET maturity_at = created_at + maturity_days * INTERVAL '1 day',
                    next_coupon_at = created_at + LEAST(maturity_days, coupon_interval_days) * INTERVAL '1 day'
                WHERE maturity_at IS NULL OR next_coupon_at IS NULL
            """))


MIGRATIONS: tuple[tuple[str, Migration], ...] = (
    ("natbirzha_p2_001", _migrate_p2_columns),
    ("natbirzha_p2_002", _migrate_p2_data),
    ("natbirzha_p2_003_financial_markets", _migrate_p2_financial_columns),
)


async def run_natbirzha_migrations(conn) -> None:
    """Apply every NATBIRZHA migration at most once on the current database."""
    await _ensure_version_table(conn)
    for version, migration in MIGRATIONS:
        if await _is_applied(conn, version):
            continue
        await migration(conn)
        await _mark_applied(conn, version)
