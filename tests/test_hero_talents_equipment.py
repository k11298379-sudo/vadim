import os
import sys
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_rpg.db"

from backend.db.session import init_db, get_db_session
from backend.db.models import User, RPGCharacter
from backend.db.crud.rpg.character import get_or_create_rpg_character, serialize_character_profile
from backend.db.crud.rpg.talent_tree import (
    get_hero_available_talent_points,
    get_hero_spent_talent_points,
    get_hero_tree,
)
from backend.api.routers.heroes_dota import select_hero_class_endpoint


async def run_tests():
    print("=== [1/2] Testing Talent Persistence & Per-Hero Points ===")
    await init_db()

    async for session in get_db_session():
        # Create test character at level 40
        char = await get_or_create_rpg_character(session, user_id=99991)
        char.level = 40
        char.hero_class = "pudge"
        # Equip custom sword and armor
        char.equipment = {
            "slot_1": {"uid": "epic_blade_1", "name": "Клинок Бессмертия", "slot": "slot_1", "min_atk": 100, "max_atk": 150},
            "slot_2": {"uid": "epic_armor_1", "name": "Броня Титана", "slot": "slot_2", "defense": 80}
        }
        char.inventory = []
        char.talents = {"tree": {}}
        await session.commit()

        # Check total earned points: 40 // 2 = 20 points
        pts_pudge = get_hero_available_talent_points(char, "pudge")
        assert pts_pudge == 20, f"Expected 20 points, got {pts_pudge}"

        # Buy 2 talents on Pudge: atk_1 (cost 1), atk_2 (cost 1) -> 2 points spent
        char.talents = {"tree": {"pudge": {"atk_1": 1, "atk_2": 1}}}
        pts_pudge_after = get_hero_available_talent_points(char, "pudge")
        assert pts_pudge_after == 18, f"Expected 18 points for Pudge, got {pts_pudge_after}"

        # Check Leshrac points (should be full 20 points!)
        pts_leshrac = get_hero_available_talent_points(char, "leshrac")
        assert pts_leshrac == 20, f"Expected 20 points for Leshrac, got {pts_leshrac}"

        # Buy 1 talent on Leshrac: util_1 (cost 1) -> 1 point spent
        char.talents["tree"]["leshrac"] = {"util_1": 1}
        pts_leshrac_after = get_hero_available_talent_points(char, "leshrac")
        assert pts_leshrac_after == 19, f"Expected 19 points for Leshrac, got {pts_leshrac_after}"

        # Pudge should STILL have 18 points!
        assert get_hero_available_talent_points(char, "pudge") == 18

        print("[OK] Per-hero talent calculation strictly verified!")

        print("=== [2/2] Testing Equipment Preservation on Hero Switch ===")
        # Switch to Leshrac via select_hero_class_endpoint
        user_mock = await session.get(User, char.user_id)
        res = await select_hero_class_endpoint(
            payload={"hero_class": "leshrac"},
            user=user_mock,
            session=session
        )
        await session.refresh(char)

        assert char.hero_class == "leshrac"
        # Equipment must NOT be stripped or replaced with starter gear!
        assert char.equipment.get("slot_1", {}).get("uid") == "epic_blade_1", f"Equipment slot 1 was wiped! {char.equipment}"
        assert char.equipment.get("slot_2", {}).get("uid") == "epic_armor_1", f"Equipment slot 2 was wiped! {char.equipment}"
        assert len(char.inventory) == 0, f"Inventory received stripped items! {char.inventory}"

        # Check serialized profile talent points
        assert res["talent_points"] == 19, f"Expected 19 talent points in profile for Leshrac, got {res['talent_points']}"

        # Switch back to Pudge
        res_pudge = await select_hero_class_endpoint(
            payload={"hero_class": "pudge"},
            user=user_mock,
            session=session
        )
        await session.refresh(char)

        assert char.hero_class == "pudge"
        assert char.equipment.get("slot_1", {}).get("uid") == "epic_blade_1"
        assert res_pudge["talent_points"] == 18, f"Expected 18 talent points for Pudge, got {res_pudge['talent_points']}"
        assert char.talents["tree"]["pudge"]["atk_1"] == 1
        assert char.talents["tree"]["pudge"]["atk_2"] == 1
        assert char.talents["tree"]["leshrac"]["util_1"] == 1

        print("[OK] Equipment and talents completely preserved across hero switches!")
        print("\n=== ALL HERO TALENT & EQUIPMENT TESTS PASSED! ZERO ERRORS! ===")


if __name__ == "__main__":
    asyncio.run(run_tests())
