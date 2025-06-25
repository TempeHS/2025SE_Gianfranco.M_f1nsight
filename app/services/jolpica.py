import requests
import time
from typing import Dict, List, Optional
from functools import lru_cache
from datetime import datetime

API_BASE_URL = "https://api.jolpi.ca/ergast/f1"

# Cache for storing API responses
_cache = {}
_cache_duration = 3600  # Cache duration in seconds

def _get_cache(key: str) -> Optional[Dict]:
    """Get a value from cache if it exists and is not expired"""
    if key in _cache:
        timestamp, data = _cache[key]
        if time.time() - timestamp < _cache_duration:
            return data
        else:
            del _cache[key]
    return None

def _set_cache(key: str, value: Dict):
    """Set a value in cache with current timestamp"""
    _cache[key] = (time.time(), value)

def _make_request(url: str, max_retries: int = 3, delay: float = 2.0) -> Optional[Dict]:
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
            time.sleep(delay * (attempt + 1))  # Progressive delay
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            _set_cache(cache_key, data)  # Cache the response
            return data
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Error making request to {url}: {e}")
                return None
            time.sleep(delay * (attempt + 2))  # Longer delay between retries
    return None

@lru_cache(maxsize=1)  # Only cache the latest year list
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
            return sorted(years, reverse=True)  # Most recent first
        return []
    except Exception as e:
        print(f"Error getting available years: {e}")
        return []

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
                    driver_standings[driver_id] = {
                        'position': standing['position'],
                        'points': standing['points'],
                        'wins': standing['wins'],
                        'constructor': standing['Constructors'][0]['name'] if standing.get('Constructors') else None
                    }
        
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
                    'code': driver.get('code', ''),
                    'number': driver.get('permanentNumber', '')
                }
                
                # Add standings information if available
                if driver_id in driver_standings:
                    driver_info.update(driver_standings[driver_id])
                
                matching_drivers.append(driver_info)
        
        # Sort by position if available, otherwise by name
        return sorted(matching_drivers, 
                     key=lambda x: (int(x.get('position', '999')), x['name']))
        
    except Exception as e:
        print(f"Error searching drivers: {e}")
        return []

@lru_cache(maxsize=128)
def get_driver_profile(driver_id: str, year: Optional[str] = None) -> Optional[Dict]:
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
            'code': driver.get('code', ''),
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
        
        # Get career statistics with cache
        career_url = f"{API_BASE_URL}/drivers/{driver_id}/results.json?limit=1000"
        career_data = _make_request(career_url)
        
        if career_data and 'MRData' in career_data:
            races = career_data['MRData'].get('RaceTable', {}).get('Races', [])
            career_stats = {
                'totalRaces': len(races),
                'totalWins': sum(1 for race in races for result in race.get('Results', []) 
                               if result.get('position') == '1'),
                'totalPodiums': sum(1 for race in races for result in race.get('Results', [])
                                  if result.get('position') in ['1', '2', '3']),
                'bestFinish': min((result.get('position', '999') for race in races 
                                 for result in race.get('Results', [])), default='N/A'),
                'firstRace': races[0]['season'] if races else 'N/A',
                'lastRace': races[-1]['season'] if races else 'N/A'
            }
            profile['careerStats'] = career_stats
            
        return profile
        
    except Exception as e:
        print(f"Error getting driver profile: {e}")
        return None
