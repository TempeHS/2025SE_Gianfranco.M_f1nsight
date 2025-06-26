from flask import Blueprint, render_template, request, jsonify
from app.services.jolpica import search_drivers, get_driver_profile, get_available_years
from datetime import datetime

bp = Blueprint('drivers', __name__)

@bp.route('/search')
def search():
    year = request.args.get('year', str(datetime.now().year))
    query = request.args.get('q', '')
    
    years = get_available_years()
    if not years:
        years = [str(datetime.now().year)]
    
    drivers = search_drivers(year, query) if year else []
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(drivers)
    
    return render_template('drivers/search.html', 
                         drivers=drivers,
                         years=years,
                         selected_year=year,
                         query=query)

@bp.route('/drivers/<driver_id>')
def profile(driver_id):
    year = request.args.get('year', str(datetime.now().year))
    profile = get_driver_profile(driver_id, year, load_career_stats=False)
    
    if not profile:
        return render_template('errors/404.html'), 404
    
    # Get race results for this driver in the specified season
    from app.services.jolpica import get_driver_results
    race_results = get_driver_results(driver_id, year)
    
    return render_template('drivers/profile.html', 
                          profile=profile, 
                          race_results=race_results,
                          year=year)

@bp.route('/drivers/<driver_id>/stats')
def driver_stats(driver_id):
    """Get driver career statistics asynchronously"""
    from app.services.jolpica import _get_driver_career_stats
    
    try:
        stats = _get_driver_career_stats(driver_id)
        if stats:
            return jsonify({'success': True, 'stats': stats})
        else:
            return jsonify({'success': False, 'error': 'Stats not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/drivers/<driver_id>/image')
def driver_image(driver_id):
    """Get optimized driver image from Wikipedia"""
    import requests
    from urllib.parse import unquote
    import re
    from flask import jsonify
    import time
    from functools import lru_cache
    
    # Cache for image URLs
    image_cache = {}
    CACHE_DURATION = 86400  # 24 hours
    
    @lru_cache(maxsize=100)
    def get_wiki_image_url(wiki_url):
        try:
            # Extract title from Wikipedia URL
            title = unquote(wiki_url.split('/')[-1])
            
            # Use Wikipedia's RESTful API for better performance
            api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            response = requests.get(api_url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                # Try to get the best image version
                if 'originalimage' in data and 'source' in data['originalimage']:
                    image_url = data['originalimage']['source']
                    # Convert to thumbnail for faster loading
                    image_url = re.sub(r'/\d+px-', '/320px-', image_url)
                    return image_url
                elif 'thumbnail' in data and 'source' in data['thumbnail']:
                    image_url = data['thumbnail']['source']
                    # Increase thumbnail size for better quality
                    image_url = re.sub(r'/\d+px-', '/320px-', image_url)
                    return image_url
        except Exception as e:
            print(f"Error fetching Wiki image: {e}")
        return None

    try:
        # Get profile to access wiki URL
        profile = get_driver_profile(driver_id, None, load_career_stats=False)
        if not profile or 'wikiUrl' not in profile:
            return jsonify({'success': False, 'error': 'Profile not found'})

        wiki_url = profile['wikiUrl']
        if not wiki_url:
            return jsonify({'success': False, 'error': 'No Wikipedia URL'})

        # Check cache first
        cache_key = f"image_{driver_id}"
        cached = image_cache.get(cache_key)
        if cached and time.time() - cached['timestamp'] < CACHE_DURATION:
            return jsonify({'success': True, 'image_url': cached['url']})

        # Fetch image URL with timeout
        image_url = get_wiki_image_url(wiki_url)
        if image_url:
            # Cache the result
            image_cache[cache_key] = {
                'url': image_url,
                'timestamp': time.time()
            }
            return jsonify({'success': True, 'image_url': image_url})

        return jsonify({'success': False, 'error': 'Image not found'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
