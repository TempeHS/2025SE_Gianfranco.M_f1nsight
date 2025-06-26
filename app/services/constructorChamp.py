import requests
from datetime import datetime

class constructorStandings:
    """
    SERVICE FOR FETCHING F1 CONSTRUCTOR DATA FROM JOLPICA-F1 API
    """
    BASE_URL = "https://api.jolpi.ca/ergast/f1"
    
    # Mapping of constructor names from API to folder names
    CONSTRUCTOR_MAPPING = {
        # Current Teams
        'Red Bull': 'Red Bull',
        'Red Bull Racing': 'Red Bull',
        'Red Bull Racing RBPT': 'Red Bull',
        'Mercedes': 'Mercedes',
        'Mercedes F1 Team': 'Mercedes',
        'Mercedes AMG': 'Mercedes',
        'Mercedes GP': 'Mercedes',
        'Ferrari': 'Ferrari',
        'Scuderia Ferrari': 'Ferrari',
        'McLaren': 'McLaren',
        'McLaren Mercedes': 'McLaren',
        'McLaren Honda': 'McLaren',
        'McLaren Renault': 'McLaren',
        'Aston Martin': 'Aston Martin',
        'Aston Martin Aramco': 'Aston Martin',
        'Racing Point': 'Aston Martin',
        'Force India': 'Aston Martin',
        'Alpine F1 Team': 'Alpine F1 Team',
        'Alpine': 'Alpine F1 Team',
        'Renault': 'Alpine F1 Team',
        'Lotus F1': 'Alpine F1 Team',
        'Lotus': 'Alpine F1 Team',
        'Williams': 'Williams',
        'Williams Racing': 'Williams',
        'Williams Mercedes': 'Williams',
        'AlphaTauri': 'RB F1 Team',
        'Toro Rosso': 'RB F1 Team',
        'RB F1 Team': 'RB F1 Team',
        'Visa Cash App RB': 'RB F1 Team',
        'Haas F1 Team': 'Haas F1 Team',
        'Haas': 'Haas F1 Team',
        'Haas Ferrari': 'Haas F1 Team',
        'Alfa Romeo': 'Sauber',
        'Alfa Romeo Racing': 'Sauber',
        'Stake F1 Team': 'Sauber',
        'Kick Sauber': 'Sauber',
        'Sauber': 'Sauber',
        # Historical Teams (using most recent equivalent or generic handling)
        'Lotus Renault': 'Alpine F1 Team',
        'Team Lotus': 'Alpine F1 Team',
        'Virgin': 'Manor',
        'Manor Marussia': 'Manor',
        'Marussia': 'Manor',
        'Brawn': 'Mercedes',
        'Brawn GP': 'Mercedes',
        'Honda': 'Red Bull',
        'BAR': 'Mercedes',
        'Toyota': 'Toyota',
        'BMW Sauber': 'Sauber',
        'Spyker': 'Aston Martin',
        'Spyker MF1': 'Aston Martin',
        'Midland': 'Aston Martin',
        'Jordan': 'Aston Martin',
        'Super Aguri': 'Honda',
        'HRT': 'HRT',
        'Hispania': 'HRT',
        'Caterham': 'Caterham',
        'Jaguar': 'Red Bull',
        'Stewart': 'Red Bull',
        'Prost': 'Prost',
        'Arrows': 'Arrows',
        'Minardi': 'RB F1 Team',
        'Benetton': 'Alpine F1 Team'
    }

    @staticmethod
    def normalize_constructor_name(name):
        """Normalize constructor name to match folder structure"""
        return constructorStandings.CONSTRUCTOR_MAPPING.get(name, name)

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
                    # Check if we have at least the Constructor and basic stats
                    if 'Constructor' not in c or not any(key in c for key in ['position', 'positionText']):
                        continue
                        
                    constructor_name = c['Constructor'].get('name', 'Unknown')
                    normalized_name = constructorStandings.normalize_constructor_name(constructor_name)
                    
                    # Handle position: prefer numeric position, fall back to positionText
                    position = c.get('position')
                    if not position:
                        position_text = c.get('positionText', 'N/A')
                        # Convert positionText to number if possible, otherwise keep as is
                        position = position_text if position_text == '-' else position_text
                    
                    formatted_standings.append({
                        'position': position,
                        'points': c.get('points', '0'),
                        'constructor': normalized_name,
                        'wins': c.get('wins', '0')
                    })
                except Exception as e:
                    print(f"Error processing constructor entry: {e}")
                    continue
                    
            # Sort standings by points if positions are not numeric
            if any(s['position'] == '-' for s in formatted_standings):
                formatted_standings.sort(key=lambda x: float(x['points']), reverse=True)
                # Update positions after sorting
                for idx, standing in enumerate(formatted_standings, 1):
                    if standing['position'] == '-':
                        standing['position'] = str(idx)
            
            return formatted_standings
            
        except Exception as e:
            print(f"Error fetching constructor standings: {e}")
            return []
