import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.config import settings
from backend.db.models import Base

def create_configured_engine():
    raw_url = settings.DATABASE_URL
    if raw_url.startswith("sqlite"):
        os.makedirs("./data", exist_ok=True)
        return create_async_engine(raw_url, echo=False, future=True, pool_pre_ping=True)
    
    # Normalize postgres URL for asyncpg
    url = raw_url
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    
    # Strip query params like sslmode or channel_binding which asyncpg handles via connect_args
    if "?" in url:
        base_url, query = url.split("?", 1)
        params = [p for p in query.split("&") if not p.startswith("sslmode") and not p.startswith("channel_binding")]
        url = base_url + ("?" + "&".join(params) if params else "")

    connect_args = {"ssl": "require"} if ("neon.tech" in url or "sslmode=require" in raw_url or "ssl=require" in raw_url) else {}
    return create_async_engine(
        url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20,
        connect_args=connect_args
    )


engine = create_configured_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            from sqlalchemy import text
            if engine.dialect.name == "sqlite":
                res_hw = await conn.execute(text("PRAGMA table_info(homeworks);"))
                cols_hw = [row[1] for row in res_hw.fetchall()]
                if "assigned_date" not in cols_hw:
                    await conn.execute(text("ALTER TABLE homeworks ADD COLUMN assigned_date DATE;"))

                res_u = await conn.execute(text("PRAGMA table_info(users);"))
                cols_u = [row[1] for row in res_u.fetchall()]
                if "custom_name" not in cols_u:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN custom_name VARCHAR(255);"))
                if "is_tester" not in cols_u:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN is_tester BOOLEAN DEFAULT 0;"))

                res_dg = await conn.execute(text("PRAGMA table_info(duty_groups);"))
                cols_dg = [row[1] for row in res_dg.fetchall()]
                if "member_ids" not in cols_dg:
                    await conn.execute(text("ALTER TABLE duty_groups ADD COLUMN member_ids JSON;"))

                res_df = await conn.execute(text("PRAGMA table_info(daily_facts);"))
                cols_df = [row[1] for row in res_df.fetchall()]
                if "hour" not in cols_df:
                    await conn.execute(text("ALTER TABLE daily_facts ADD COLUMN hour INTEGER DEFAULT 0;"))
                if "minute" not in cols_df:
                    await conn.execute(text("ALTER TABLE daily_facts ADD COLUMN minute INTEGER DEFAULT 0;"))
                await conn.execute(text("DROP INDEX IF EXISTS ix_daily_facts_date;"))
                await conn.execute(text("DROP INDEX IF EXISTS uq_daily_facts_date_hour;"))
                res_gc = await conn.execute(text("PRAGMA table_info(group_chats);"))
                cols_gc = [row[1] for row in res_gc.fetchall()]
                for col in ["topic_hw_id", "topic_schedule_id", "topic_duty_id", "topic_announcements_id"]:
                    if col not in cols_gc:
                        await conn.execute(text(f"ALTER TABLE group_chats ADD COLUMN {col} INTEGER;"))
            else:
                await conn.execute(text("ALTER TABLE homeworks ADD COLUMN IF NOT EXISTS assigned_date DATE;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS custom_name VARCHAR(255);"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_tester BOOLEAN DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE duty_groups ADD COLUMN IF NOT EXISTS member_ids JSONB;"))
                await conn.execute(text("ALTER TABLE daily_facts ADD COLUMN IF NOT EXISTS hour INTEGER DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE daily_facts ADD COLUMN IF NOT EXISTS minute INTEGER DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE group_chats ADD COLUMN IF NOT EXISTS topic_hw_id INTEGER;"))
                await conn.execute(text("ALTER TABLE group_chats ADD COLUMN IF NOT EXISTS topic_schedule_id INTEGER;"))
                await conn.execute(text("ALTER TABLE group_chats ADD COLUMN IF NOT EXISTS topic_duty_id INTEGER;"))
                await conn.execute(text("ALTER TABLE group_chats ADD COLUMN IF NOT EXISTS topic_announcements_id INTEGER;"))
                await conn.execute(text("DROP INDEX IF EXISTS ix_daily_facts_date;"))
                await conn.execute(text("DROP INDEX IF EXISTS uq_daily_facts_date_hour;"))
                await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_daily_facts_date_hour_min ON daily_facts (date, hour, minute);"))
        except Exception as e:
            print(f"init_db migration note: {e}")

    try:
        from backend.db.crud import recalculate_bell_schedule_chain
        async with async_session_factory() as session:
            await recalculate_bell_schedule_chain(session, specific_date=None, from_lesson=2)
    except Exception as e:
        print(f"init_db bell recalculate note: {e}")

    try:
        from backend.bot.services.facts import cleanup_past_facts
        async with async_session_factory() as session:
            await cleanup_past_facts(session)
    except Exception as e:
        print(f"init_db facts cleanup note: {e}")


