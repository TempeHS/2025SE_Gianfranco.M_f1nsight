import requests
from datetime import datetime

class driverStandings:
    """
    # SERVICE FOR FETCHING F1 DATA FROM JOLPICA-F1 API
    """
    BASE_URL = "https://api.jolpi.ca/ergast/f1"

    @staticmethod
    def get_driver_standings(year=None):
        """
        # FETCH DRIVER STANDINGS
        # IF NO YEAR PROVIDED, USE CURRENT YEAR
        """
        if not year:
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