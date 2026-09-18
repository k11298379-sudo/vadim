import os
import sys
import pytest
import asyncio
import json
import hmac
import hashlib
import time

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.db.session import init_db
from backend.natbirzha.config import nat_settings


def create_test_init_data(user_id: int, username: str = "nat_tester") -> str:
    """Generate cryptographically valid initData signed with TEST_AUTH_SECRET."""
    user_data = {"id": user_id, "first_name": "Tester", "username": username}
    user_json = json.dumps(user_data, separators=(',', ':'))
    auth_date = str(int(time.time()))

    params = [
        f"auth_date={auth_date}",
        f"user={user_json}"
    ]
    data_check_string = "\n".join(sorted(params))
    secret_key = hmac.new(b"WebAppData", nat_settings.TEST_AUTH_SECRET.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return f"auth_date={auth_date}&user={user_json}&hash={calc_hash}"


async def test_vertical_playable_slice():
    print("\n" + "=" * 64)
    print("🚀 RUNNING VERTICAL PLAYABLE SLICE INTEGRATION TEST")
    print("=" * 64)

    await init_db()

    user_id = int(time.time()) % 1000000 + 800000
    init_data = create_test_init_data(user_id, f"magnat_steel_{user_id}")
    headers = {
        "X-Telegram-Init-Data": init_data,
        "Content-Type": "application/json"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Login
        print("\n--- [1/7] Strict Telegram initData Authentication ---")
        login_res = await client.post("/api/natbirzha/auth/login", headers=headers)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        login_data = login_res.json()
        assert login_data["authenticated"] is True
        print(f"[OK] Authenticated user_id={login_data['user']['id']}")

        # 2. Company Creation
        print("\n--- [2/7] Company Founding & Specialization ---")
        comp_name = f"Северсталь {user_id}"
        create_res = await client.post(
            "/api/natbirzha/company/create",
            headers={**headers, "Idempotency-Key": f"idemp-create-{user_id}"},
            json={
                "name": comp_name,
                "ticker": f"N{user_id % 1000:03d}",
                "specialization": "metallurgist",
                "territory_hex": "HEX_NORTH_101"
            }
        )
        assert create_res.status_code == 200, f"Company creation failed: {create_res.text}"
        comp = create_res.json()
        assert comp["cash"] == nat_settings.STARTING_CASH
        assert comp["specialization"] == "metallurgist"
        print(f"[OK] Company [{comp['ticker']}] '{comp['name']}' founded with {comp['cash']} cash grant.")

        # 3. Inspect Starter Factory
        print("\n--- [3/7] Inspecting Starter Metallurgy Smelter ---")
        me_res = await client.get("/api/natbirzha/company/me", headers=headers)
        assert me_res.status_code == 200, f"Get company failed: {me_res.text}"
        comp_data = me_res.json()
        assert len(comp_data["factories"]) >= 1, "Starter factory must be created"
        factory = comp_data["factories"][0]
        factory_id = factory["id"]
        assert factory["building_type"] == "smelter"
        assert factory["tier"] == 1
        print(f"[OK] Smelter factory confirmed: id={factory_id}, tier={factory['tier']}.")

        # 4. NPC Resource Purchase (Buy Ore and Coal)
        print("\n--- [4/7] Buying Raw Materials from NPC Liquidity Corridor ---")
        # Buy 10 iron_ore @ 43.75 NPC sell
        buy_ore = await client.post(
            "/api/natbirzha/market/npc/trade",
            headers={**headers, "Idempotency-Key": "idemp-npc-ore-001"},
            json={"item_id": "iron_ore", "action": "buy", "quantity": 10.0}
        )
        assert buy_ore.status_code == 200, f"Buy ore failed: {buy_ore.text}"
        assert buy_ore.json()["unit_price"] == 43.75

        # Buy 5 coal @ 37.50 NPC sell
        buy_coal = await client.post(
            "/api/natbirzha/market/npc/trade",
            headers={**headers, "Idempotency-Key": "idemp-npc-coal-001"},
            json={"item_id": "coal", "action": "buy", "quantity": 5.0}
        )
        assert buy_coal.status_code == 200, f"Buy coal failed: {buy_coal.text}"
        assert buy_coal.json()["unit_price"] == 37.50
        print("[OK] Raw materials purchased: 10 iron_ore, 5 coal.")

        # Check inventory
        comp_status = await client.get("/api/natbirzha/company/me", headers=headers)
        inv = comp_status.json()["inventory"]
        assert inv.get("iron_ore") == 10.0
        assert inv.get("coal") == 5.0
        assert inv.get("steel", 0.0) == 0.0
        print(f"[OK] Verified inventory state: iron_ore=10, coal=5, steel=0.")

        # 5. Production Tick (Single Unified ProductionTickEngine)
        print("\n--- [5/7] Executing Unified ProductionTickEngine ---")
        prod_res = await client.post(
            "/api/natbirzha/production/factory/produce",
            headers={**headers, "Idempotency-Key": "idemp-produce-001"},
            json={"factory_id": factory_id}
        )
        assert prod_res.status_code == 200, f"Production failed: {prod_res.text}"
        pdata = prod_res.json()
        assert pdata["success"] is True
        assert pdata["outputs_produced"]["steel"] == 1.0
        assert pdata["xp_gained"] > 0
        print(f"[OK] Production tick executed: +{pdata['outputs_produced']['steel']} steel, +{pdata['xp_gained']} XP.")

        # Verify inventory and XP updated
        comp_status2 = await client.get("/api/natbirzha/company/me", headers=headers)
        inv2 = comp_status2.json()["inventory"]
        assert inv2.get("steel") == 1.0, f"Expected 1.0 steel, got {inv2.get('steel')}"
        assert inv2.get("iron_ore") == 8.0, f"Expected 8.0 iron_ore, got {inv2.get('iron_ore')}"
        assert inv2.get("coal") == 4.0, f"Expected 4.0 coal, got {inv2.get('coal')}"
        assert comp_status2.json()["xp"] == pdata["xp_gained"], f"Expected {pdata['xp_gained']} XP, got {comp_status2.json()['xp']}"
        print(f"[OK] Resource balances and XP progression confirmed (+{comp_status2.json()['xp']} XP).")

        # 6. Resource Sale to NPC Corridor
        print("\n--- [6/7] Selling Finished Steel to NPC Reserve Floor ---")
        cash_before_sale = comp_status2.json()["cash"]
        sell_res = await client.post(
            "/api/natbirzha/market/npc/trade",
            headers={**headers, "Idempotency-Key": "idemp-npc-steel-sell-001"},
            json={"item_id": "steel", "action": "sell", "quantity": 1.0}
        )
        assert sell_res.status_code == 200, f"Sell steel failed: {sell_res.text}"
        assert sell_res.json()["unit_price"] == 72.0, "NPC steel buy floor must be 72.0 cash"
        
        comp_status3 = await client.get("/api/natbirzha/company/me", headers=headers)
        cash_after_sale = comp_status3.json()["cash"]
        assert round(cash_after_sale - cash_before_sale, 2) == 72.0
        assert comp_status3.json()["inventory"].get("steel") == 0.0
        print(f"[OK] Sold 1 steel to NPC for +72.00 cash. Account credited.")

        # 7. Idempotency Verification
        print("\n--- [7/7] Testing Strict Idempotency & Repeat Protection ---")
        # Repeating identical request with same Idempotency-Key must return same cached response
        repeat_sell = await client.post(
            "/api/natbirzha/market/npc/trade",
            headers={**headers, "Idempotency-Key": "idemp-npc-steel-sell-001"},
            json={"item_id": "steel", "action": "sell", "quantity": 1.0}
        )
        assert repeat_sell.status_code == 200
        # Cash must not have changed
        comp_status4 = await client.get("/api/natbirzha/company/me", headers=headers)
        assert comp_status4.json()["cash"] == cash_after_sale
        print("[OK] Replay protected. Zero double spending.")

    print("\n" + "=" * 64)
    print("🎉 VERTICAL PLAYABLE SLICE PASSED 100% PERFECTLY!")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    asyncio.run(test_vertical_playable_slice())
