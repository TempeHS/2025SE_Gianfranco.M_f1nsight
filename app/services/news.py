from newsapi import NewsApiClient
from datetime import datetime, timedelta
import os

_news_service = None

def get_news_service():
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service

class NewsService:
    # BASE DOMAINS FOR F1 NEWS SOURCES
    F1_DOMAINS = 'formula1.com,motorsport.com,racefans.net,crash.net,the-race.com,gpfans.com'

    def __init__(self):
        api_key = os.environ.get('NEWS_API_KEY')
        if not api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.api = NewsApiClient(api_key=api_key)

    def get_f1_news(self, sources=None, page_size=30, page=1):
        """Get F1 news from specified sources."""
        try:
            # GET NEWS FROM LAST 30 DAYS
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # SIMPLER QUERY TO GET MORE RESULTS
            query = 'Formula 1 OR Formula One OR F1'
            
            # HANDLE SOURCE FILTERING
            if sources:
                source_domain_map = {
                    'formula1': 'formula1.com',
                    'motorsport': 'motorsport.com',
                    'racefans': 'racefans.net',
                    'crash': 'crash.net',
                    'therace': 'the-race.com',
                    'gpfans': 'gpfans.com'
                }
                selected_domains = [source_domain_map[s] for s in sources.split(',') if s in source_domain_map]
                domains = ','.join(selected_domains) if selected_domains else self.F1_DOMAINS
            else:
                domains = self.F1_DOMAINS

            # DEBUG PRINT DOMAINS
            print(f"Using domains: {domains}")
            
            response = self.api.get_everything(
                q=query,
                domains=domains,
                language='en',
                from_param=from_date,
                sort_by='publishedAt',
                page_size=page_size,
                page=int(page)
            )
            
            articles = response.get('articles', [])
            
            # DEBUG PRINT ARTICLE COUNT
            print(f"Found {len(articles)} articles")
            
            return {'status': 'success', 'articles': articles}
        except Exception as e:
            # DEBUG PRINT ERROR
            print(f"Error fetching news: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    F1_SOURCES = [
        {'id': 'formula1', 'name': 'Formula1.com'},
        {'id': 'motorsport', 'name': 'Motorsport.com'},
        {'id': 'racefans', 'name': 'RaceFans.net'},
        {'id': 'crash', 'name': 'Crash.net'},
        {'id': 'therace', 'name': 'The Race'},
        {'id': 'gpfans', 'name': 'GPFans'}
    ]

    def get_available_sources(self):
        """Get available sources from our trusted F1 domains"""
        return {'status': 'success', 'sources': self.F1_SOURCES}
