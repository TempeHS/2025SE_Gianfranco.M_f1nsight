import requests
from datetime import datetime

class driverStandings:
    """
    # SERVICE FOR FETCHING F1 DATA FROM ERGAST API
    """
    BASE_URL = "http://ergast.com/api/f1"

    @staticmethod
    def get_driver_standings(year=None):
        """
        # FETCH CURRENT DRIVER STANDINGS
        # IF NO YEAR PROVIDED, USE CURRENT YEAR
        """
        if not year:
            year = datetime.now().year
            
        url = f"{driverStandings.BASE_URL}/{year}/driverStandings.json"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
            
            return [{
                'position': item['position'],
                'points': item['points'],
                'driver': f"{item['Driver']['givenName']} {item['Driver']['familyName']}",
                'constructor': item['Constructors'][0]['name']
            } for item in standings]
            
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return []