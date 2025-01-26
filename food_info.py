import aiohttp
from config import OPENWEATHER_API_KEY, NINJAS_API_KEY

def calculate_calories(weight, height, age, activity_level):
    return 10 * weight + 6.25 * height - 5 * age + 7.5 * activity_level

async def get_current_temp(city):
    params = {
        'q': city,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.openweathermap.org/data/2.5/weather', params=params) as response:
            answer = await response.json()
    return answer['main']['temp'] 

async def calculate_water(weight, activity_level, city):
    required_water = 30 * weight + 500 * activity_level / 30
    try:
        current_city_temp = await get_current_temp(city=city)
        required_water += 750 * (current_city_temp > 25)
    except Exception as e:
        print(e)
    return required_water

async def get_food_info(product_name):
    params = {
        'action': 'process',
        'search_terms': product_name,
        'json': 'true',
    }
    async with aiohttp.ClientSession() as session:
        async with session.get("https://world.openfoodfacts.org/cgi/search.pl", params=params) as response:
            data = await response.json()
            products = data.get('products', [])
            if products:
                first_product = products[0]
                return first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            return None
    print(f"Ошибка: {response.status_code}")
    return None

async def get_calories_burned(description, weight):
    url = "https://api.api-ninjas.com/v1/caloriesburned"
    headers = {
        "X-Api-Key": NINJAS_API_KEY
    }
    workout_type, time_in_minutes = description.split()
    params = {
        "activity": workout_type,
        "weight": int(weight * 2.20),
        "duration": time_in_minutes
    }
    
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(url, headers=headers, params=params) as response:
            data = await response.json()

    if not data:
        raise ValueError("No activity found")
    calories_burned = data[0]['total_calories']
    return calories_burned
