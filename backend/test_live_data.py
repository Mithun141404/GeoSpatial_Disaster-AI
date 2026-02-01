import httpx
import asyncio
import sys

async def test_live_data():
    try:
        print("Fetching live disaster data...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get('http://127.0.0.1:8000/api/disasters/live')
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Retrieved {len(data)} live events.")
                if len(data) > 0:
                    print(f"Sample event: {data[0]['disaster_type']} at {data[0]['location']}")
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_live_data())
