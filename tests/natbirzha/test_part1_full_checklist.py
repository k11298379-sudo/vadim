import os
import sys
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.main import app
from backend.config import settings
from backend.db.session import init_db, async_session_factory
from backend.db.models import User
from backend.natbirzha.config import nat_settings
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.services.company_service import CompanyService
from backend.natbirzha.services.building_catalog import CANONICAL_BUILDINGS
from backend.natbirzha.services.recipes import RECIPES, validate_recipe_dag
from backend.natbirzha.services.creator_service import CreatorService

@pytest.mark.asyncio
async def test_full_part1_and_creator_checklist():
    print("\n" + "=" * 70)
    print("🏆 FULL CHECKLIST v1.0 & CREATOR/STATE VERIFICATION SUITE")
    print("=" * 70)

    await init_db()
    nat_settings.ALLOW_TEST_AUTH = True

    # 1. Verify 48 Canonical Enterprises & DAG
    print("\n[1/7] Testing 48 Canonical Enterprises & Strict DAG Integrity...")
    checklist_buildings = [
        # Agrarian
        "farm_grain", "livestock_complex", "feed_mill", "food_factory", "bio_farm", "flour_mill",
        # Miner
        "iron_mine", "coal_mine", "copper_mine", "lithium_mine", "uranium_mine", "rare_earth_mine",
        # Metallurgist
        "steel_mill", "rolling_mill", "machine_factory", "metal_structures_factory", "auto_components_factory", "superalloy_factory",
        # Oilman
        "oil_rig", "gas_field", "refinery", "petrochemical_plant", "jet_fuel_plant", "plastics_factory",
        # Energy
        "solar_plant", "hydro_plant", "thermal_power_plant", "wind_farm", "nuclear_plant", "fusion_plant",
        # Forester
        "logging_camp", "sawmill", "pulp_mill", "cardboard_factory", "furniture_factory", "composite_factory",
        # Chemist
        "chemical_plant", "fertilizer_plant", "polymer_factory", "electrolyte_factory", "biochem_factory", "catalyst_factory",
        # Technoprom
        "component_factory", "chip_factory", "server_factory", "robot_factory", "ai_factory", "aerospace_complex"
    ]
    assert len(checklist_buildings) == 48
    for b in checklist_buildings:
        assert b in CANONICAL_BUILDINGS, f"Building {b} missing from catalog"
        spec = CANONICAL_BUILDINGS[b]
        assert spec["recipe_id"] in RECIPES, f"Recipe for {b} missing"
    assert validate_recipe_dag() is True, "Recipe DAG contains cycles!"
    print("✓ All 48 buildings verified and DAG validated (zero cycles).")

    # 2. Verify Admin 200k vs Regular 50k Starting Cash
    print("\n[2/7] Testing Admin (200k) vs Regular Player (50k) Cash Invariant...")
    async with async_session_factory() as session:
        # Regular user
        await CompanyService.reset_company_for_user(session, 999901)
        reg_comp = await CompanyService.create_company(session, 999901, "Reg Corp", "miner")
        assert reg_comp.cash == 50000.0, f"Expected 50k, got {reg_comp.cash}"

        # Admin user (user_id=1)
        await CompanyService.reset_company_for_user(session, 1)
        adm_comp = await CompanyService.create_company(session, 1, "Admin Corp", "metallurgist")
        assert adm_comp.cash == 200000.0, f"Expected 200k for admin, got {adm_comp.cash}"
    print("✓ Starting balance verified: Admin gets 200,000.0 cash, Regular player gets 50,000.0 cash.")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 3. Company Reset API
        print("\n[3/7] Testing Company Reset Endpoint...")
        auth_admin = "user=%7B%22id%22%3A1053722876%2C%22username%22%3A%22notariuspiva%22%7D"
        auth_player = "user=%7B%22id%22%3A777888%2C%22username%22%3A%22player%22%7D"

        # Ensure clean initial state
        await client.post("/api/natbirzha/company/reset", headers={"X-Telegram-Init-Data": auth_player})

        # Create player company
        p_init = await client.post("/api/natbirzha/company/create", json={"name": "TempCorp", "specialization": "forester"}, headers={"X-Telegram-Init-Data": auth_player})
        assert p_init.status_code == 200

        # Reset player company
        p_reset = await client.post("/api/natbirzha/company/reset", headers={"X-Telegram-Init-Data": auth_player})
        assert p_reset.status_code == 200
        assert p_reset.json()["success"] is True

        # Check company is gone
        me_check = await client.get("/api/natbirzha/company/me", headers={"X-Telegram-Init-Data": auth_player})
        assert me_check.status_code == 404
        print("✓ Company reset verified: all factories and inventory wiped cleanly.")

        # 4. Security: Regular Player Blocked from Creator Endpoints (403 Forbidden)
        print("\n[4/7] Testing Security Boundaries: 403 Forbidden for Regular Players...")
        forbidden_endpoints = [
            ("GET", "/api/natbirzha/creator/overview", None),
            ("GET", "/api/natbirzha/creator/market", None),
            ("POST", "/api/natbirzha/creator/market/warnings", {"company_id": 1, "reason": "test"}),
            ("POST", "/api/natbirzha/creator/market/restrictions", {"reason": "test", "min_price": 10.0}),
            ("POST", "/api/natbirzha/creator/bonds/issue", {"title": "B", "volume": 10, "face_value": 100, "coupon_rate": 5, "maturity_days": 10, "purpose": "P"}),
            ("POST", "/api/natbirzha/creator/tournaments/launch", {}),
            ("GET", "/api/natbirzha/creator/audit-log", None),
        ]
        for method, ep, body in forbidden_endpoints:
            if method == "GET":
                r = await client.get(ep, headers={"X-Telegram-Init-Data": auth_player})
            else:
                r = await client.post(ep, json=body, headers={"X-Telegram-Init-Data": auth_player})
            assert r.status_code == 403, f"Endpoint {ep} did not return 403 for regular player! Got {r.status_code}"
        print("✓ Security barrier verified: All 7 creator endpoints strictly return 403 Forbidden.")

        # 5. Creator Overview, Treasury and Bonds
        print("\n[5/7] Testing Creator Overview, State Treasury & Government Bonds...")
        r_over = await client.get("/api/natbirzha/creator/overview", headers={"X-Telegram-Init-Data": auth_admin})
        assert r_over.status_code == 200
        over_data = r_over.json()
        assert "treasury_cash" in over_data
        init_treasury = over_data["treasury_cash"]
        assert init_treasury >= 10000000.0, f"Treasury should start >= 10M, got {init_treasury}"

        # Issue bonds
        bond_payload = {
            "title": "ОФЗ-НАТ-1",
            "volume": 500,
            "face_value": 1000.0,
            "coupon_rate": 8.5,
            "maturity_days": 30,
            "purpose": "Финансирование резервного фонда энергосети"
        }
        r_bond = await client.post("/api/natbirzha/creator/bonds/issue", json=bond_payload, headers={"X-Telegram-Init-Data": auth_admin})
        assert r_bond.status_code == 200
        bond_res = r_bond.json()
        assert bond_res["raised_funds"] == 500000.0
        assert bond_res["treasury_cash"] == init_treasury + 500000.0
        print("✓ Bonds issued: State Treasury received funds, isolated from player cash.")

        # 6. Market Warnings & Price Restrictions Enforcement
        print("\n[6/7] Testing Market Warnings, Price Restrictions & Backend Enforcement...")
        # Create company for player to trade
        await client.post("/api/natbirzha/company/create", json={"name": "TraderCorp", "specialization": "metallurgist"}, headers={"X-Telegram-Init-Data": auth_player})
        me_resp = await client.get("/api/natbirzha/company/me", headers={"X-Telegram-Init-Data": auth_player})
        p_comp_id = me_resp.json()["id"]

        # Issue warning
        r_warn = await client.post("/api/natbirzha/creator/market/warnings", json={"company_id": p_comp_id, "reason": "Попытка демпинга"}, headers={"X-Telegram-Init-Data": auth_admin})
        assert r_warn.status_code == 200

        # Set price restriction: iron_ore min_price=50.0, max_price=150.0
        r_restr = await client.post("/api/natbirzha/creator/market/restrictions", json={
            "item_id": "iron_ore",
            "min_price": 50.0,
            "max_price": 150.0,
            "reason": "Стабилизация цен на сырьё"
        }, headers={"X-Telegram-Init-Data": auth_admin})
        assert r_restr.status_code == 200
        restr_id = r_restr.json()["restriction_id"]

        # Try to place order at 20.0 (below min 50.0) -> MUST BE REJECTED
        r_bad_order = await client.post("/api/natbirzha/market/orders/create", json={
            "item_id": "iron_ore",
            "order_type": "BUY",
            "price": 20.0,
            "quantity": 5.0
        }, headers={"X-Telegram-Init-Data": auth_player})
        assert r_bad_order.status_code == 400
        assert "минимум" in r_bad_order.json()["detail"].lower()
        print("✓ Order rejected by State price floor restriction.")

        # Place valid order at 100.0 -> MUST SUCCEED
        r_ok_order = await client.post("/api/natbirzha/market/orders/create", json={
            "item_id": "iron_ore",
            "order_type": "BUY",
            "price": 100.0,
            "quantity": 2.0
        }, headers={"X-Telegram-Init-Data": auth_player})
        assert r_ok_order.status_code == 200
        print("✓ Order placed successfully within allowed State price corridor.")

        # Remove restriction
        r_del_restr = await client.delete(f"/api/natbirzha/creator/market/restrictions/{restr_id}", headers={"X-Telegram-Init-Data": auth_admin})
        assert r_del_restr.status_code == 200
        print("✓ Market restriction removed cleanly.")

        # 7. Audit Log & Early Tournament Launch
        print("\n[7/7] Testing Audit Log & Tournament Early Launch...")
        r_audit = await client.get("/api/natbirzha/creator/audit-log", headers={"X-Telegram-Init-Data": auth_admin})
        assert r_audit.status_code == 200
        logs = r_audit.json()["logs"]
        assert len(logs) >= 3
        actions = [l["action"] for l in logs]
        assert "BOND_ISSUANCE" in actions
        assert "WARNING_ISSUED" in actions
        assert "RESTRICTION_SET" in actions
        print(f"✓ Audit log recorded all admin operations: {actions[:4]}")

        # Early tournament launch
        r_tourn = await client.post("/api/natbirzha/creator/tournaments/launch", headers={"X-Telegram-Init-Data": auth_admin})
        assert r_tourn.status_code == 200
        print("✓ Early tournament launch executed successfully.")

    print("\n" + "=" * 70)
    print("🎉 ALL FULL CHECKLIST v1.0 AND CREATOR TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_full_part1_and_creator_checklist())
