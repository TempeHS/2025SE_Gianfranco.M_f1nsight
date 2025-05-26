import requests
from datetime import datetime
from functools import lru_cache
import asyncio
import aiohttp

class driverStandings:
    """
    # SERVICE FOR FETCHING F1 DATA FROM JOLPICA-F1 API
    """
    BASE_URL = "https://api.jolpi.ca/ergast/f1"
    _cache = {}  # In-memory cache for API responses

    @staticmethod
    @lru_cache(maxsize=32)  # Cache up to 32 different year combinations
    def get_driver_standings(year=None):
        """
        # FETCH DRIVER STANDINGS
        # IF NO YEAR PROVIDED, USE CURRENT YEAR
        """
        # Ensure year is an integer and defaults to current year
        try:
            year = int(year) if year is not None else datetime.now().year
        except (ValueError, TypeError):
            year = datetime.now().year

        url = f"{driverStandings.BASE_URL}/{year}/driverstandings/"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # DATA STRUCTURE VALIDATIE
            if not all(key in data for key in ['MRData']):
                print(f"Invalid data structure for year {year}")
                return []
                
            standings_table = data['MRData'].get('StandingsTable', {})
            lists = standings_table.get('StandingsLists', [])
            
            if not lists:
                print(f"No standings data found for year {year}")
                return []
                
            drivers = lists[0].get('DriverStandings', [])
            
            formatted_standings = []
            for d in drivers:
                try:
                    # VALIDATE
                    if not all(key in d for key in ['position', 'points', 'Driver', 'Constructors']):
                        continue
                        
                    driver = d['Driver']
                    constructor = d['Constructors'][0] if d['Constructors'] else {'name': 'Unknown'}
                    
                    formatted_standings.append({
                        'position': d.get('position', 'N/A'),
                        'points': d.get('points', '0'),
                        'driver': f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                        'constructor': constructor.get('name', 'Unknown')
                    })
                except Exception as e:
                    print(f"Error processing driver entry: {e}")
                    continue
                    
            return formatted_standings
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching standings: {e}")
            return []
        except ValueError as e:
            print(f"JSON parsing error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching standings: {e}")
            return []

    @staticmethod
    @lru_cache(maxsize=1)  # Cache the seasons list since it rarely changes
    def get_available_seasons():
        """
        # FETCH ALL AVAILABLE SEASONS FOR DROPDOWN (set high limit)
        """
        try:
            url = f"{driverStandings.BASE_URL}/seasons/?limit=100"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            seasons = data['MRData']['SeasonTable']['Seasons']
            # AI SOLUTION FOR SORTING
            return sorted([int(season['season']) for season in seasons], reverse=True)
        except Exception as e:
            print(f"Error fetching seasons: {e}")
            return []

    @staticmethod
    @lru_cache(maxsize=32)  # Cache driver lists per year
    def get_driver_list(year=None):
        """
        # GET LIST OF ALL DRIVERS FOR A GIVEN YEAR
        """
        try:
            year = int(year) if year is not None else datetime.now().year
        except (ValueError, TypeError):
            year = datetime.now().year

        url = f"{driverStandings.BASE_URL}/{year}/drivers"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'MRData' not in data or 'DriverTable' not in data['MRData']:
                print("Invalid data structure for drivers")
                return []
            
            drivers = data['MRData']['DriverTable'].get('Drivers', [])
            return [f"{d['givenName']} {d['familyName']}" for d in drivers]
        except Exception as e:
            print(f"Error fetching driver list: {e}")
            return []

    @staticmethod
    async def _fetch_race_result(session, year, round_num):
        """Helper method to fetch a single race result asynchronously"""
        url = f"{driverStandings.BASE_URL}/{year}/{round_num}/results"
        cache_key = f"race_{year}_{round_num}"
        
        # CHECK CACHE
        if cache_key in driverStandings._cache:
            return driverStandings._cache[cache_key]

        try:
            async with session.get(url) as response:
                data = await response.json()
                if 'MRData' in data and 'RaceTable' in data['MRData']:
                    race = data['MRData']['RaceTable'].get('Races', [])
                    if race:
                        # CACHE RESULT
                        driverStandings._cache[cache_key] = race[0]
                        return race[0]
        except Exception as e:
            print(f"Error fetching round {round_num}: {e}")
        return None

    @staticmethod
    async def get_driver_points_async(driver_name, year=None):
        """
        # Asynchronous version of get_driver_points
        # Returns a dictionary with points array and race names
        """
        try:
            year = int(year) if year is not None else datetime.now().year
        except (ValueError, TypeError):
            year = datetime.now().year

        # FETCH RACE RESULTS
        async with aiohttp.ClientSession() as session:
            tasks = []
            for round_num in range(1, 9):  # 8 SO FAR.. NEED TO EDIT
                task = driverStandings._fetch_race_result(session, year, round_num)
                tasks.append(task)
            
            races = []
            results = await asyncio.gather(*tasks)
            for result in results:
                if result:
                    races.append(result)

        if not races:
            print("No race data found")
            return {'points': [], 'races': []}

        points_by_race = []
        race_names = []
        running_total = 0
        
        # KNOWN RACES
        expected_races = [
            "Australia",
            "China",
            "Japan",  
            "Bahrain",  
            "Saudi Arabia",  
            "Miami", 
            "Imola",
            "Monaco"
        ]
        
        for race in races:
            circuit_name = expected_races[len(race_names)]
            race_names.append(circuit_name)
            
            points_earned = 0
            results = race.get('Results', [])
            
            for result in results:
                driver = result.get('Driver', {})
                full_name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}"
                if full_name.strip() == driver_name.strip():
                    try:
                        points_earned = float(result.get('points', 0))
                    except (ValueError, TypeError):
                        points_earned = 0
                    break
            
            running_total += points_earned
            points_by_race.append(running_total)
        
        return {
            'points': points_by_race,
            'races': race_names
        }

    @staticmethod
    def get_driver_points(driver_name, year=None):
        """
        # Synchronous wrapper for get_driver_points_async
        # Returns a dictionary with points array and race names
        """
        return asyncio.run(driverStandings.get_driver_points_async(driver_name, year))

