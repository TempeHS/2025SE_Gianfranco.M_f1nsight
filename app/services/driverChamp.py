import requests
from datetime import datetime
import asyncio
import aiohttp
from functools import lru_cache
from app import cache
from app.services.jolpica import get_races_by_season

class driverStandings:
    """
    # SERVICE FOR FETCHING F1 DATA FROM JOLPICA-F1 API
    """
    BASE_URL = "https://api.jolpi.ca/ergast/f1"

    # 2025 F1 RACE CALENDAR - Used as fallback if API fails
    RACE_CALENDAR_2025 = {
        1: "Bahrain",
        2: "Saudi Arabia",
        3: "Australia", 
        4: "Japan",
        5: "China",
        6: "Miami",
        7: "Imola",
        8: "Monaco",
        9: "Spain",
        10: "Canada",
        11: "Austria",
        12: "Great Britain",
        13: "Hungary",
        14: "Belgium",
        15: "Netherlands",
        16: "Italy",
        17: "Azerbaijan",
        18: "Singapore",
        19: "USA",  # Austin
        20: "Mexico",
        21: "Brazil",
        22: "Las Vegas",
        23: "Qatar",
        24: "Abu Dhabi"
    }

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
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
            response = requests.get(url, timeout=5)  # Add timeout
            response.raise_for_status()
            data = response.json()
            
            # DATA STRUCTURE VALIDATIE
            if not all(key in data for key in ['MRData']):
                return []
                
            standings_table = data['MRData'].get('StandingsTable', {})
            lists = standings_table.get('StandingsLists', [])
            
            if not lists:
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
                        'constructor': constructor.get('name', 'Unknown'),
                        'driverId': driver.get('driverId', '')
                    })
                except Exception:
                    continue
            
            return formatted_standings
            
        except requests.exceptions.RequestException:
            return []
        except Exception:
            return []

    @staticmethod
    @cache.memoize(timeout=3600)  # Cache for 1 hour
    def get_available_seasons():
        """
        # FETCH ALL AVAILABLE SEASONS FOR DROPDOWN
        """
        try:
            url = f"{driverStandings.BASE_URL}/seasons/?limit=100"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            seasons = data['MRData']['SeasonTable']['Seasons']
            return sorted([int(season['season']) for season in seasons], reverse=True)
        except Exception:
            return []

    @staticmethod
    @cache.memoize(timeout=3600)  # Cache for 1 hour
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
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if 'MRData' not in data or 'DriverTable' not in data['MRData']:
                return []
                
            drivers = data['MRData']['DriverTable']['Drivers']
            return [f"{driver['givenName']} {driver['familyName']}" for driver in drivers]
        except Exception as e:
            print(f"Error fetching driver list: {e}")
            return []

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_races_for_year(year=None):
        """
        # GET ALL RACES FOR A GIVEN SEASON
        # RETURNS A LIST OF RACE OBJECTS WITH NAMES AND ROUNDS
        """
        try:
            year = int(year) if year is not None else datetime.now().year
        except (ValueError, TypeError):
            year = datetime.now().year
            
        # Use the jolpica service to get race information
        races = get_races_by_season(str(year))
        if not races:
            # Fall back to our static calendar if API fails
            return [{"round": str(r), "raceName": n} for r, n in driverStandings.RACE_CALENDAR_2025.items()]
            
        return races

    @staticmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_driver_points(driver_name, year=None):
        """
        # GET POINTS PROGRESSION FOR A DRIVER THROUGHOUT THE SEASON
        """
        try:
            year = int(year) if year is not None else datetime.now().year
        except (ValueError, TypeError):
            year = datetime.now().year

        # First get all races for the season to ensure we have proper order
        all_races = driverStandings.get_races_for_year(year)
        
        # Sort races by round number
        all_races.sort(key=lambda r: int(r['round']))
            
        # Directly fetch individual race results to ensure we get complete data
        points = []
        race_names = []
        cumulative_points = 0
        
        # Clear cache to ensure fresh data
        cache.delete_memoized(driverStandings.get_driver_points)
        
        # Process each race individually to avoid data inconsistencies
        for race in all_races:
            race_round = race['round']
            
            # Skip future races (if race date is in the future)
            race_date = race.get('date')
            if race_date:
                try:
                    race_datetime = datetime.fromisoformat(race_date)
                    if race_datetime > datetime.now():
                        continue
                except (ValueError, TypeError):
                    pass  # If date parsing fails, include the race
            
            # Fetch this specific race result
            race_url = f"{driverStandings.BASE_URL}/{year}/{race_round}/results.json"
            try:
                race_response = requests.get(race_url, timeout=5)
                race_response.raise_for_status()
                race_data = race_response.json()
                
                if 'MRData' in race_data and 'RaceTable' in race_data['MRData']:
                    race_results = race_data['MRData']['RaceTable'].get('Races', [])
                    
                    points_earned = 0
                    if race_results:
                        # Look for the driver in this race's results
                        for result in race_results[0].get('Results', []):
                            driver = result['Driver']
                            full_name = f"{driver['givenName']} {driver['familyName']}"
                            if full_name.strip() == driver_name.strip():
                                try:
                                    points_earned = float(result.get('points', 0))
                                    print(f"Found {driver_name} in race {race_round} with {points_earned} points")
                                except (ValueError, TypeError):
                                    points_earned = 0
                                break
                    
                    # Add points to cumulative total
                    cumulative_points += points_earned
                    points.append(cumulative_points)
                    
                    # Add race name (use circuit locality or race name for shorter display)
                    race_display_name = race.get('locality', race.get('raceName', f"Race {race_round}"))
                    race_names.append(race_display_name)
                    
                    print(f"Race {race_round} ({race_display_name}): {points_earned} points, cumulative: {cumulative_points}")
                
            except Exception as e:
                print(f"Error fetching results for race {race_round}: {e}")
                # Still add the race but with 0 points for this driver
                race_display_name = race.get('locality', race.get('raceName', f"Race {race_round}"))
                race_names.append(race_display_name)
                points.append(cumulative_points)  # Keep previous total
        
        print(f"Final data for {driver_name}: {len(race_names)} races, {len(points)} points entries")
        print(f"Races: {race_names}")
        print(f"Points: {points}")
        
        return {
            'points': points,
            'races': race_names
        }

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
            for round_num in range(1, 10):  # 9 SO FAR.. NEED TO EDIT
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
            "Monaco",
            "Spain"
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

