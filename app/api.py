import httpx
import certifi
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("VIDEO_FETCHER_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


async def get_movies(page=1):
    url = f"{BASE_URL}/movie/now_playing"
    params = {"api_key": API_KEY, "language": "ru-RU", "page": page}

    async with httpx.AsyncClient(verify=certifi.where()) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        return [
            {
                "id": str(item["id"]),
                "title": item["title"],
                "description": item["overview"],
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{item['poster_path']}"
                    if item.get("poster_path")
                    else None
                ),
            }
            for item in results
        ]
