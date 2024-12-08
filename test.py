import os
import asyncio
from custom_components.neakasa.api import NeakasaAPI
from aiohttp import ClientSession

async def main():
    session = ClientSession()
    api = NeakasaAPI(session)
    
    await api.connect(os.environ['TEST_USERNAME'], os.environ['TEST_PASSWORD'])

    devices = await api.getDevices()
    print(devices)

    await api._session.close()
asyncio.run(main())