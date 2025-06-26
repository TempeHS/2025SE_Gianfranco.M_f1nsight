import requests
import time
from typing import Dict, List, Optional
from functools import lru_cache
from datetime import datetime

API_BASE_URL = "https://api.jolpi.ca/ergast/f1"

# CACHE SETTINGS
_cache = {}
_cache_duration = 3600  # CACHE DURATION IN SECONDS
_long_cache_duration = 86400  # 24 HOURS FOR RARELY CHANGING DATA LIKE CAREER STATS

def _get_cache(key: str, long_term: bool = False) -> Optional[Dict]:
    """Get a value from cache if it exists and is not expired"""
    if key in _cache:
        timestamp, data = _cache[key]
        duration = _long_cache_duration if long_term else _cache_duration
        if time.time() - timestamp < duration:
            return data
        else:
            del _cache[key]
    return None

def _set_cache(key: str, value: Dict, long_term: bool = False):
    """Set a value in cache with current timestamp"""
    _cache[key] = (time.time(), value)

def _make_request(url: str, max_retries: int = 3, delay: float = 0.5) -> Optional[Dict]:
    """
    Make an API request with retry logic, rate limiting, and caching.
    """
    # Check cache first
    cache_key = url
    cached_data = _get_cache(cache_key)
    if cached_data:
        return cached_data

    for attempt in range(max_retries):
        try:
            # Only delay after first attempt
            if attempt > 0:
                time.sleep(delay * attempt)
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            _set_cache(cache_key, data)  # Cache the response
            return data
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Error making request to {url}: {e}")
                return None
            time.sleep(delay * (attempt + 1))  # Longer delay between retries
    return None

@lru_cache(maxsize=1)  # CACHE LATEST YEAR LIST
def get_available_years() -> List[str]:
    """
    Get a list of available F1 seasons.
    Returns a list of years in descending order.
    """
    try:
        url = f"{API_BASE_URL}/seasons.json?limit=100"
        data = _make_request(url)
        
        if data and 'MRData' in data and 'SeasonTable' in data['MRData']:
            seasons = data['MRData']['SeasonTable'].get('Seasons', [])
            years = [season['season'] for season in seasons]
            return sorted(years, reverse=True)  # MOST RECENT FIRST
        return []
    except Exception as e:
        print(f"Error getting available years: {e}")
        return []

@lru_cache(maxsize=100)
def _generate_driver_code(given_name: str, family_name: str) -> str:
    """
    Generate a driver code from their name when not provided by the API.
    For historical drivers where code is not available.
    """
    # FOR SINGLE WORD NAMES, USE FIRST 3 LETTERS
    if not given_name or not family_name:
        full_name = (given_name or '') + (family_name or '')
        return full_name[:3].upper() if full_name else ''
    
    # Try to create a 3-letter code from initials and surname
    if len(family_name) >= 2:
        return family_name[:3].upper()
    
    # Fallback: combine initials
    return (given_name[0] + family_name[0]).upper()

@lru_cache(maxsize=100)
def search_drivers(year: str, query: str = "") -> List[Dict]:
    """
    Search for F1 drivers in a specific year.
    Args:
        year: The F1 season year to search in
        query: Optional search string to filter drivers
    Returns:
        list: A list of matching drivers with their basic information
    """
    try:
        url = f"{API_BASE_URL}/{year}/drivers.json"
        data = _make_request(url)
        
        if not data or 'MRData' not in data:
            return []
            
        drivers = data['MRData']['DriverTable'].get('Drivers', [])
        if not drivers:
            return []
        
        # Get standings for this year to include current position/points
        standings_url = f"{API_BASE_URL}/{year}/driverStandings.json"
        standings_data = _make_request(standings_url)
        
        # Create a map of driver standings
        driver_standings = {}
        if standings_data and 'MRData' in standings_data:
            standings_list = standings_data['MRData']['StandingsTable'].get('StandingsLists', [])
            if standings_list:
                for standing in standings_list[0].get('DriverStandings', []):
                    driver_id = standing['Driver']['driverId']
                    try:
                        driver_standings[driver_id] = {
                            'position': standing.get('position', '0'),
                            'points': standing.get('points', '0'),
                            'wins': standing.get('wins', '0'),
                            'constructor': standing['Constructors'][0]['name'] if standing.get('Constructors') else None
                        }
                    except (KeyError, IndexError):
                        # Skip this standing if data is incomplete
                        continue
        
        matching_drivers = []
        query = query.lower()
        
        for driver in drivers:
            if (not query or
                query in driver['givenName'].lower() or 
                query in driver['familyName'].lower() or 
                query in f"{driver['givenName']} {driver['familyName']}".lower()):
                
                driver_id = driver['driverId']
                driver_info = {
                    'id': driver_id,
                    'name': f"{driver['givenName']} {driver['familyName']}",
                    'nationality': driver['nationality'],
                    'dateOfBirth': driver['dateOfBirth'],
                    'wikiUrl': driver.get('url', ''),
                    'code': driver.get('code') or _generate_driver_code(driver['givenName'], driver['familyName']),
                    'number': driver.get('permanentNumber', '')
                }
                
                # Add standings information if available
                if driver_id in driver_standings:
                    driver_info.update(driver_standings[driver_id])
                else:
                    # Add default values if standings not available
                    driver_info.update({
                        'position': '0',
                        'points': '0',
                        'wins': '0',
                        'constructor': None
                    })
                
                matching_drivers.append(driver_info)
        
        # Sort by position if available, otherwise by name
        # Use a safer sorting approach that handles missing or invalid values
        def sort_key(x):
            try:
                pos = int(x.get('position', '0'))
                # Move position 0 to the end by treating it as infinity
                if pos == 0:
                    pos = float('inf')
            except (ValueError, TypeError):
                pos = float('inf')
            return (pos, x['name'])
            
        return sorted(matching_drivers, key=sort_key)
        
    except Exception as e:
        print(f"Error searching drivers: {e}")
        return []

@lru_cache(maxsize=128)
def get_driver_profile(driver_id: str, year: Optional[str] = None, load_career_stats: bool = True) -> Optional[Dict]:
    """
    Get detailed profile information for a specific driver.
    Uses caching to minimize API calls.
    If year is provided, includes statistics for that specific season.
    """
    try:
        # Get basic driver info
        url = f"{API_BASE_URL}/drivers/{driver_id}.json"
        data = _make_request(url)
        
        if not data or 'MRData' not in data:
            return None
            
        driver_data = data['MRData']['DriverTable'].get('Drivers', [])
        if not driver_data:
            return None
            
        driver = driver_data[0]
        profile = {
            'id': driver['driverId'],
            'name': f"{driver['givenName']} {driver['familyName']}",
            'givenName': driver['givenName'],
            'familyName': driver['familyName'],
            'nationality': driver['nationality'],
            'dateOfBirth': driver['dateOfBirth'],
            'wikiUrl': driver.get('url', ''),
            'code': driver.get('code') or _generate_driver_code(driver['givenName'], driver['familyName']),
            'number': driver.get('permanentNumber', ''),
            'seasons': {}
        }
        
        
        # Get seasons statistics if year is provided
        if year:
            standings_url = f"{API_BASE_URL}/{year}/drivers/{driver_id}/driverStandings.json"
            standings_data = _make_request(standings_url)
            
            if standings_data and 'MRData' in standings_data:
                standings_lists = standings_data['MRData']['StandingsTable'].get('StandingsLists', [])
                if standings_lists:
                    standings = standings_lists[0].get('DriverStandings', [])
                    if standings:
                        season_stats = standings[0]
                        profile['seasons'][year] = {
                            'position': season_stats['position'],
                            'points': season_stats['points'],
                            'wins': season_stats['wins'],
                            'constructor': season_stats['Constructors'][0]['name'] if season_stats.get('Constructors') else None
                        }
            
            # Get next and previous drivers in standings
            all_drivers = search_drivers(year)
            if all_drivers:
                # Sort drivers by position
                sorted_drivers = sorted(all_drivers, key=lambda x: int(x.get('position', '999')))
                
                # Find the current driver in the list
                current_index = next((i for i, d in enumerate(sorted_drivers) if d['id'] == driver_id), -1)
                
                if current_index != -1:
                    # Get previous driver
                    if current_index > 0:
                        profile['prev_driver'] = {
                            'id': sorted_drivers[current_index - 1]['id'],
                            'name': sorted_drivers[current_index - 1]['name'],
                            'position': sorted_drivers[current_index - 1]['position']
                        }
                    
                    # Get next driver
                    if current_index < len(sorted_drivers) - 1:
                        profile['next_driver'] = {
                            'id': sorted_drivers[current_index + 1]['id'],
                            'name': sorted_drivers[current_index + 1]['name'],
                            'position': sorted_drivers[current_index + 1]['position']
                        }
        
        # Get career statistics only if requested
        if load_career_stats:
            # Check cache first for quick loading
            cache_key = f"career_stats_{driver_id}"
            cached_stats = _get_cache(cache_key, long_term=True)
            
            if cached_stats:
                profile['careerStats'] = cached_stats
            else:
                # Load basic stats if not all available yet
                profile['careerStats'] = {
                    'totalRaces': 0,
                    'totalWins': 0,
                    'totalPodiums': 0,
                    'bestFinish': 'N/A',
                    'firstRace': 'N/A',
                    'lastRace': 'N/A'
                }
            
        return profile
        
    except Exception as e:
        print(f"Error getting driver profile: {e}")
        return None

def _get_driver_career_stats(driver_id: str) -> Dict:
    """
    # GET COMPLETE DRIVER CAREER STATISTICS
    # FETCHES ALL SEASONS DATA FOR MORE ACCURATE RESULTS
    """
    try:
        # Check cache first for career stats (using long-term cache)
        cache_key = f"career_stats_{driver_id}"
        cached_stats = _get_cache(cache_key, long_term=True)
        if cached_stats:
            return cached_stats
            
        # First get all seasons the driver participated in
        seasons_url = f"{API_BASE_URL}/drivers/{driver_id}/seasons.json"
        seasons_data = _make_request(seasons_url)
        
        if not seasons_data or 'MRData' not in seasons_data:
            return None
            
        seasons = seasons_data['MRData']['SeasonTable'].get('Seasons', [])
        if not seasons:
            return None
            
        # Variables to track career stats
        total_races = 0
        total_wins = 0
        total_podiums = 0
        best_finish = 999
        first_race = None
        last_race = None
        
        # Get results for each season separately
        for season in seasons:
            season_year = season['season']
            season_url = f"{API_BASE_URL}/{season_year}/drivers/{driver_id}/results.json"
            season_data = _make_request(season_url)
            
            if not season_data or 'MRData' not in season_data:
                continue
                
            races = season_data['MRData']['RaceTable'].get('Races', [])
            if not races:
                continue
                
            # Update stats for this season
            total_races += len(races)
            
            for race in races:
                for result in race.get('Results', []):
                    position = result.get('position')
                    if position == '1':
                        total_wins += 1
                    if position in ['1', '2', '3']:
                        total_podiums += 1
                    try:
                        pos_int = int(position)
                        best_finish = min(best_finish, pos_int)
                    except (ValueError, TypeError):
                        pass
            
            # Track first and last season
            if first_race is None or season_year < first_race:
                first_race = season_year
            if last_race is None or season_year > last_race:
                last_race = season_year
        
        # Format best finish (convert 999 to N/A if no valid positions were found)
        best_finish_str = str(best_finish) if best_finish < 999 else 'N/A'
        
        career_stats = {
            'totalRaces': total_races,
            'totalWins': total_wins,
            'totalPodiums': total_podiums,
            'bestFinish': best_finish_str,
            'firstRace': first_race if first_race else 'N/A',
            'lastRace': last_race if last_race else 'N/A'
        }
        
        # Cache the results (long-term)
        _set_cache(cache_key, career_stats, long_term=True)
        
        return career_stats
        
    except Exception as e:
        print(f"Error getting career statistics: {e}")
        return {
            'totalRaces': 0,
            'totalWins': 0,
            'totalPodiums': 0,
            'bestFinish': 'N/A',
            'firstRace': 'N/A',
            'lastRace': 'N/A'
        }

@lru_cache(maxsize=100)
def get_driver_results(driver_id: str, year: str) -> List[Dict]:
    """
    Get race results for a specific driver in a specific season
    """
    try:
        url = f"{API_BASE_URL}/{year}/drivers/{driver_id}/results.json"
        data = _make_request(url)
        
        if not data or 'MRData' not in data:
            return []
        
        races = data['MRData']['RaceTable'].get('Races', [])
        if not races:
            return []
        
        results = []
        for race in races:
            race_results = race.get('Results', [])
            if not race_results:
                continue
            
            result = race_results[0]  # There should be only one result per race for this driver
            
            # Get country code
            country = race['Circuit']['Location']['country']
            country_code = get_country_code(country)
            
            result_info = {
                'round': race['round'],
                'raceName': race['raceName'],
                'circuitName': race['Circuit']['circuitName'],
                'date': race['date'],
                'country': country,
                'countryCode': country_code,
                'grid': result.get('grid', 'N/A'),
                'position': result.get('position', 'N/A'),
                'points': result.get('points', '0'),
                'status': result.get('status', 'Unknown'),
                'constructor': result['Constructor']['name'] if 'Constructor' in result else 'Unknown'
            }
            
            results.append(result_info)
        
        return results
    
    except Exception as e:
        print(f"Error getting driver results: {e}")
        return []
        
    except Exception as e:
        print(f"Error getting races for season {year}: {e}")
        return []

@lru_cache(maxsize=100)
def get_race_results(year: str, round_number: str) -> Dict:
    """
    Get detailed results for a specific race.
    Args:
        year: The F1 season year
        round_number: The round number of the race
    Returns:
        dict: Race details including results
    """
    try:
        url = f"{API_BASE_URL}/{year}/{round_number}/results.json"
        data = _make_request(url)
        
        if not data or 'MRData' not in data:
            return {}
            
        races = data['MRData']['RaceTable'].get('Races', [])
        if not races:
            # Get race info from season if no results exist
            season_url = f"{API_BASE_URL}/{year}.json"
            season_data = _make_request(season_url)
            
            if season_data and 'MRData' in season_data:
                all_races = season_data['MRData']['RaceTable'].get('Races', [])
                future_races = [r for r in all_races if r['round'] == round_number]
                
                if future_races:
                    race = future_races[0]
                    # Format date for comparison
                    race_date = race['date']
                    race_time = race.get('time', '00:00:00Z')
                    race_datetime_str = f"{race_date}T{race_time.replace('Z', '')}"
                    
                    # Convert to datetime object for comparison
                    try:
                        race_datetime = datetime.fromisoformat(race_datetime_str)
                        current_time = datetime.now()
                        
                        race_info = {
                            'round': race['round'],
                            'raceName': race['raceName'],
                            'circuitName': race['Circuit']['circuitName'],
                            'circuitId': race['Circuit']['circuitId'],
                            'country': race['Circuit']['Location']['country'],
                            'countryCode': get_country_code(race['Circuit']['Location']['country']),
                            'locality': race['Circuit']['Location']['locality'],
                            'date': race['date'],
                            'time': race.get('time', ''),
                            'url': race.get('url', ''),
                            'season': race['season'],
                            'isFutureRace': race_datetime > current_time,
                            'raceDateTime': race_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')
                        }
                        return race_info
                    except (ValueError, TypeError):
                        # If date parsing fails, just mark as future race
                        race_info = {
                            'round': race['round'],
                            'raceName': race['raceName'],
                            'circuitName': race['Circuit']['circuitName'],
                            'circuitId': race['Circuit']['circuitId'],
                            'country': race['Circuit']['Location']['country'],
                            'countryCode': get_country_code(race['Circuit']['Location']['country']),
                            'locality': race['Circuit']['Location']['locality'],
                            'date': race['date'],
                            'time': race.get('time', ''),
                            'url': race.get('url', ''),
                            'season': race['season'],
                            'isFutureRace': True
                        }
                        return race_info
            
            return {}
        
        race = races[0]
        race_info = {
            'round': race['round'],
            'raceName': race['raceName'],
            'circuitName': race['Circuit']['circuitName'],
            'circuitId': race['Circuit']['circuitId'],
            'country': race['Circuit']['Location']['country'],
            'countryCode': get_country_code(race['Circuit']['Location']['country']),
            'locality': race['Circuit']['Location']['locality'],
            'date': race['date'],
            'time': race.get('time', ''),
            'url': race.get('url', ''),
            'season': race['season'],
            'results': [],
            'isFutureRace': False
        }
        
        for result in race.get('Results', []):
            driver = result['Driver']
            constructor = result['Constructor']
            
            result_info = {
                'position': result['position'],
                'driverName': f"{driver['givenName']} {driver['familyName']}",
                'driverId': driver['driverId'],
                'driverCode': driver.get('code', ''),
                'driverNumber': driver.get('permanentNumber', ''),
                'constructorName': constructor['name'],
                'constructorId': constructor['constructorId'],
                'grid': result.get('grid', ''),
                'laps': result.get('laps', ''),
                'status': result.get('status', ''),
                'points': result.get('points', '0'),
                'time': result.get('Time', {}).get('time', '') if 'Time' in result else '',
                'fastestLap': result.get('FastestLap', {}).get('rank', '') if 'FastestLap' in result else '',
                'fastestLapTime': result.get('FastestLap', {}).get('Time', {}).get('time', '') if 'FastestLap' in result else ''
            }
            race_info['results'].append(result_info)
        
        return race_info
        
    except Exception as e:
        print(f"Error getting race results for {year} round {round_number}: {e}")
        return {}

def get_country_code(country_name: str) -> str:
    """
    Convert a country name to its ISO 3166-1 alpha-2 code for flag display.
    Args:
        country_name: The name of the country
    Returns:
        str: The two-letter country code or empty string if not found
    """
    # Map of country names to ISO codes
    country_map = {
        'Abu Dhabi': 'ae',  # United Arab Emirates
        'Argentina': 'ar',
        'Australia': 'au',
        'Austria': 'at',
        'Azerbaijan': 'az',
        'Bahrain': 'bh',
        'Belgium': 'be',
        'Brazil': 'br',
        'Canada': 'ca',
        'China': 'cn',
        'France': 'fr',
        'Germany': 'de',
        'Hungary': 'hu',
        'India': 'in',
        'Italy': 'it',
        'Japan': 'jp',
        'Korea': 'kr',
        'Malaysia': 'my',
        'Mexico': 'mx',
        'Monaco': 'mc',
        'Morocco': 'ma',
        'Netherlands': 'nl',
        'Portugal': 'pt',
        'Qatar': 'qa',
        'Russia': 'ru',
        'Saudi Arabia': 'sa',
        'Singapore': 'sg',
        'South Africa': 'za',
        'Spain': 'es',
        'Sweden': 'se',
        'Switzerland': 'ch',
        'Turkey': 'tr',
        'UK': 'gb',
        'United Kingdom': 'gb',
        'Great Britain': 'gb',
        'USA': 'us',
        'United States': 'us',
        'Vietnam': 'vn',
        'Emilia Romagna': 'it',  # Special cases for regions
        'Styria': 'at',
        'Tuscany': 'it',
        'Miami': 'us',
        'Las Vegas': 'us',
        'Sakhir': 'bh',
        'Europe': 'eu',
        'San Marino': 'sm',
        'UAE': 'ae',
        'United Arab Emirates': 'ae',
        'Czech Republic': 'cz',
        'Czechoslovakia': 'cz',
        'Finland': 'fi',
        'Ireland': 'ie',
        'New Zealand': 'nz',
        'Poland': 'pl',
        'United States of America': 'us',
        'America': 'us',
        'Denmark': 'dk',
        'Australia/Pacific': 'au',
        'Catalunya': 'es',
        'Imola': 'it',
        'Zandvoort': 'nl',
        'Monza': 'it',
        'Silverstone': 'gb'
    }
    
    return country_map.get(country_name, '')

@lru_cache(maxsize=100)
def get_races_by_season(year: str) -> List[Dict]:
    """
    Get all races for a specific F1 season.
    Args:
        year: The F1 season year
    Returns:
        list: A list of races with their basic information
    """
    try:
        url = f"{API_BASE_URL}/{year}.json"
        data = _make_request(url)
        
        if not data or 'MRData' not in data:
            return []
            
        races = data['MRData']['RaceTable'].get('Races', [])
        if not races:
            return []
        
        race_list = []
        for race in races:
            country = race['Circuit']['Location']['country']
            country_code = get_country_code(country)
            
            race_info = {
                'round': race['round'],
                'raceName': race['raceName'],
                'circuitName': race['Circuit']['circuitName'],
                'circuitId': race['Circuit']['circuitId'],
                'country': country,
                'countryCode': country_code,
                'locality': race['Circuit']['Location']['locality'],
                'date': race['date'],
                'time': race.get('time', ''),
                'url': race.get('url', ''),
                'season': race['season']
            }
            race_list.append(race_info)
        
        return race_list
    
    except Exception as e:
        print(f"Error getting races for season {year}: {e}")
        return []
