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
        # Jolpica-F1 API endpoint for driver standings (trailing slash required)
        url = f"{driverStandings.BASE_URL}/{year}/driverstandings/"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            # Navigate to the correct structure
            lists = data['MRData']['StandingsTable']['StandingsLists']
            if not lists:
                return []
            drivers = lists[0]['DriverStandings']
            return [{
                'position': d['position'],
                'points': d['points'],
                'driver': f"{d['Driver']['givenName']} {d['Driver']['familyName']}",
                'constructor': d['Constructors'][0]['name']
            } for d in drivers]
        except Exception as e:
            print(f"Error fetching standings: {e}")
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
            # Convert to int for sorting, then back to str for dropdown
            return sorted([int(season['season']) for season in seasons], reverse=True)
        except Exception as e:
            print(f"Error fetching seasons: {e}")
            return []