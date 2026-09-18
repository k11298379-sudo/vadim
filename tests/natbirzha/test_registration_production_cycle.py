import os, sys, asyncio, hashlib, hmac, json, urllib.parse, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./data/natbirzha_cycle_test.db'
os.environ['BOT_TOKEN'] = '1234567890:ABCdefFakeTestToken'
from sqlalchemy import select
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.db.session import init_db, async_session_factory, engine
from backend.db.models import Base
from backend.natbirzha.config import nat_settings
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.services.production_service import ProductionTickEngine

def headers(tg_id):
    nat_settings.ALLOW_TEST_AUTH = True
    data={'auth_date':str(int(time.time())), 'user':json.dumps({'id':tg_id,'first_name':'CycleTester'},separators=(',',':'))}
    check='\n'.join(f'{k}={v}' for k,v in sorted(data.items()))
    secret=hmac.new(b'WebAppData',nat_settings.TEST_AUTH_SECRET.encode(),hashlib.sha256).digest()
    data['hash']=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    return {'X-Telegram-Init-Data':urllib.parse.urlencode(data)}

async def main():
    await init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all); await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        h=headers(991001)
        assert (await c.post('/api/natbirzha/auth/login',headers=h)).status_code==200
        r=await c.post('/api/natbirzha/company/create',headers=h,json={'name':'Нефтегаз Тест','specialization':'oil_gas'})
        assert r.status_code==200, r.text
        assert r.json()['specialization']=='oilman'
        status=await c.get('/api/natbirzha/production/factories',headers=h)
        f=status.json()['factories'][0]
        assert f['building_type']=='oil_rig', f
        assert f['current_recipe']=='pump_oil_gas', f
        # start, do not instantly produce
        r=await c.post('/api/natbirzha/production/factory/produce',headers=h,json={'factory_id':f['id'],'recipe_id':'pump_oil_gas'})
        assert r.status_code==200 and r.json()['status']=='running', r.text
        assert r.json()['duration_seconds']>=10
        inv=(await c.get('/api/natbirzha/production/inventory',headers=h)).json()['inventory']
        assert not any(x['item_id']=='oil_crude' and x['quantity']>0 for x in inv)
        async with async_session_factory() as s:
            fac=(await s.execute(select(NatFactory).where(NatFactory.id==f['id']))).scalar_one()
            company=(await s.execute(select(NatCompany).where(NatCompany.id==fac.company_id))).scalar_one()
            ready=fac.cycle_ready_at
            result=await ProductionTickEngine.complete_cycle(s,company,fac,ready)
            assert result['success']
            await s.commit()
        inv2=(await c.get('/api/natbirzha/production/inventory',headers=h)).json()['inventory']
        assert any(x['item_id']=='oil_crude' and x['quantity']>0 for x in inv2)
    print('NATBIRZHA registration + timed production cycle: PASS')

if __name__=='__main__': asyncio.run(main())
