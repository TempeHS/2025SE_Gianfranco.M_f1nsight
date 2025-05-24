import requests
from datetime import datetime

class constructorStandings:
    """
    SERVICE FOR FETCHING F1 CONSTRUCTOR DATA FROM JOLPICA-F1 API
    """
    BASE_URL = "https://api.jolpi.ca/ergast/f1"

    @staticmethod
    def get_constructor_standings(year=None):
        if not year:
            year = datetime.now().year
        url = f"{constructorStandings.BASE_URL}/{year}/constructorStandings/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not all(key in data for key in ['MRData']):
                print(f"Invalid data structure for year {year}")
                return []
                
            standings_table = data['MRData'].get('StandingsTable', {})
            lists = standings_table.get('StandingsLists', [])
            
            if not lists:
                print(f"No constructor standings found for year {year}")
                return []
                
            constructors = lists[0].get('ConstructorStandings', [])
            
            formatted_standings = []
            for c in constructors:
                try:
                    if not all(key in c for key in ['position', 'points', 'Constructor', 'wins']):
                        continue
                        
                    formatted_standings.append({
                        'position': c.get('position', 'N/A'),
                        'points': c.get('points', '0'),
                        'constructor': c['Constructor'].get('name', 'Unknown'),
                        'wins': c.get('wins', '0')
                    })
                except Exception as e:
                    print(f"Error processing constructor entry: {e}")
                    continue
                    
            return formatted_standings
            
        except Exception as e:
            print(f"Error fetching constructor standings: {e}")
            return []
