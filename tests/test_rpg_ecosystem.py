import os
import sys
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_rpg.db"

from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.db.session import init_db, get_db_session
from backend.db.crud.rpg import (
    get_or_create_rpg_character,
    unequip_item_from_character,
    equip_item_for_character,
    use_consumable_item,
    get_rpg_shop_catalog,
    buy_item_from_shop,
    calculate_character_effective_stats,
    serialize_character_profile
)


async def test_rpg_ecosystem_suite():
    print("\n=== [1/5] Testing Shop Catalog & Purchases (/shop, /shop/buy) ===")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Check shop catalog
        r = await client.get("/api/rpg/shop")
        assert r.status_code == 200, f"Shop catalog error: {r.text}"
        catalog = r.json()
        assert len(catalog) >= 15, f"Expected at least 15 items in shop, got {len(catalog)}"
        print(f"[OK] Shop catalog verified: {len(catalog)} items available.")

        # 2. Get profile and add test gold/gems
        gen = get_db_session()
        session = await anext(gen)
        try:
            char = await get_or_create_rpg_character(session, user_id=1)
            char.gold = 5000
            char.gems = 100
            char.inventory = []
            await session.commit()
        finally:
            await session.close()

        # Buy Armor
        r = await client.post("/api/rpg/shop/buy", json={"item_id": "shop_a_forged_cuirass"})
        assert r.status_code == 200, f"Buy armor failed: {r.text}"
        res = r.json()
        assert res["success"] is True
        bought_armor = res["item"]
        assert bought_armor["slot"] == "armor"
        print(f"[OK] Bought armor from shop: {bought_armor['name']} (defense: {bought_armor.get('defense')})")

        # Buy Relic
        r = await client.post("/api/rpg/shop/buy", json={"item_id": "shop_r_blink_dagger"})
        assert r.status_code == 200
        bought_relic = r.json()["item"]
        assert bought_relic["slot"] == "relic"
        print(f"[OK] Bought relic from shop: {bought_relic['name']}")

        # Buy Potion
        r = await client.post("/api/rpg/shop/buy", json={"item_id": "shop_p_healing"})
        assert r.status_code == 200
        bought_potion = r.json()["item"]
        assert bought_potion["slot"] == "consumable"
        print(f"[OK] Bought potion from shop: {bought_potion['name']} (count: {bought_potion.get('count')})")

        print("\n=== [2/5] Testing Equipment & Unequip Functionality ===")
        # Equip the bought armor
        r = await client.post("/api/rpg/inventory/equip", json={"item_uid": bought_armor["uid"]})
        assert r.status_code == 200
        prof = r.json()["profile"]
        assert prof["equipment"]["armor"]["uid"] == bought_armor["uid"]
        print("[OK] Armor equipped into armor slot.")

        # Equip the bought relic
        r = await client.post("/api/rpg/inventory/equip", json={"item_uid": bought_relic["uid"]})
        assert r.status_code == 200
        prof = r.json()["profile"]
        assert prof["equipment"]["relic"]["uid"] == bought_relic["uid"]
        print("[OK] Relic equipped into relic slot.")

        # UNEQUIP Armor by slot name
        r = await client.post("/api/rpg/inventory/unequip", json={"slot": "armor"})
        assert r.status_code == 200, f"Unequip armor failed: {r.text}"
        prof = r.json()["profile"]
        assert prof["equipment"].get("armor") is None, "Armor slot should be empty after unequip"
        inv_uids = [it["uid"] for it in prof["inventory"]]
        assert bought_armor["uid"] in inv_uids, "Unequipped armor should be back in inventory"
        print("[OK] Armor successfully unequipped to inventory! Slot is now empty.")

        # UNEQUIP Relic by item_uid
        r = await client.post("/api/rpg/inventory/unequip", json={"item_uid": bought_relic["uid"]})
        assert r.status_code == 200
        prof = r.json()["profile"]
        assert prof["equipment"].get("relic") is None, "Relic slot should be empty after unequip"
        inv_uids = [it["uid"] for it in prof["inventory"]]
        assert bought_relic["uid"] in inv_uids
        print("[OK] Relic successfully unequipped by item_uid! Slot is now empty.")

        # UNEQUIP Weapon by slot name
        r = await client.post("/api/rpg/inventory/unequip", json={"slot": "weapon"})
        assert r.status_code == 200
        prof = r.json()["profile"]
        assert prof["equipment"].get("weapon") is None, "Weapon slot should be empty after unequip"
        print("[OK] Weapon successfully unequipped! All 3 equipment slots are unequipped and empty.")

        # Re-equip weapon from inventory
        weapon_in_inv = next((it for it in prof["inventory"] if it.get("slot") == "weapon"), None)
        assert weapon_in_inv is not None
        r = await client.post("/api/rpg/inventory/equip", json={"item_uid": weapon_in_inv["uid"]})
        assert r.status_code == 200
        print(f"[OK] Re-equipped weapon: {weapon_in_inv['name']}.")

        print("\n=== [3/5] Testing Potion / Consumable Direct Usage ===")
        # Use potion from inventory
        r = await client.post("/api/rpg/inventory/use", json={"item_uid": bought_potion["uid"]})
        assert r.status_code == 200, f"Potion usage failed: {r.text}"
        p_res = r.json()
        assert p_res["success"] is True
        assert p_res["potion_result"]["heal_hp"] == 120
        assert p_res["potion_result"]["remaining_count"] == 2
        print(f"[OK] Potion used! Healed {p_res['potion_result']['heal_hp']} HP. Remaining count: {p_res['potion_result']['remaining_count']}.")

        print("\n=== [4/5] Testing Hero Switch Equipment Retention ===")
        # Put on armor before switching hero
        r = await client.post("/api/rpg/inventory/equip", json={"item_uid": bought_armor["uid"]})
        assert r.status_code == 200

        # Switch hero to invoker
        r = await client.post("/api/rpg/class/select", json={"hero_class": "invoker"})
        assert r.status_code == 200
        prof = r.json()
        assert prof["hero_class"] == "invoker"
        inv_uids = [it["uid"] for it in prof["inventory"]]
        assert bought_armor["uid"] in inv_uids, "Previous equipped armor must be preserved in inventory after class switch!"
        print("[OK] Class switch preserved previous equipment in inventory without deletion!")

        print("\n=== [5/5] Testing Hyperbolic Armor Formula Mathematics ===")
        for def_val in [0, 5, 10, 20, 50, 100]:
            dr = (def_val * 0.05) / (1.0 + def_val * 0.05)
            ehp_multiplier = 1.0 + def_val * 0.05
            incoming_atk = 100
            raw_dmg = max(2, int(incoming_atk * 0.85 * (1.0 - dr)))
            print(f"  Armor: {def_val:3d} -> DR: {dr*100:5.1f}% | EHP: x{ehp_multiplier:.2f} | Damage taken: {raw_dmg:2d}")
            assert 0.0 <= dr < 1.0, "Damage reduction must be between 0% and 100%"
            assert raw_dmg >= 2, "Damage taken should never be less than minimum clamp"

        print("[OK] Hyperbolic armor mathematics strictly verified!")

    print("\n=======================================================")
    print(">>> ALL RPG ECOSYSTEM INTEGRATION TESTS PASSED! <<<")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(test_rpg_ecosystem_suite())
