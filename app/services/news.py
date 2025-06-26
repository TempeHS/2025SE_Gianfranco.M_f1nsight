from newsapi import NewsApiClient
from datetime import datetime, timedelta
import os
from functools import lru_cache

_news_service = None

def get_news_service():
    global _news_service
    if _news_service is None:
        try:
            _news_service = NewsService()
        except Exception as e:
            print(f"Error initializing NewsService: {e}")
            return None
    return _news_service

class NewsService:
    # BASE DOMAINS FOR F1 NEWS SOURCES
    F1_DOMAINS = 'formula1.com,motorsport.com,autosport.com,espn.com,skysports.com,planetf1.com'
    CACHE_TTL = 300  # 5 MINUTES CACHE
    
    # EXCLUSION KEYWORDS - ARTICLES WITH THESE TERMS WILL BE FILTERED OUT
    EXCLUDE_TERMS = ['MLB', 'baseball', 'pitcher', 'basketball', 'NFL', 'football', 'soccer', 'tennis', 'golf', 'hockey', 'NBA']

    def __init__(self):
        api_key = os.environ.get('NEWS_API_KEY')
        if not api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.api = NewsApiClient(api_key=api_key)

    @lru_cache(maxsize=32)
    def get_f1_news(self, sources=None, page_size=30, page=1):
        """Get F1 news from specified sources with caching."""
        try:
            # VALIDATE PAGE PARAMETER
            page = int(page)

            # GET NEWS FROM LAST 30 DAYS
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # F1 SEARCH QUERY TERMS
            query = 'Formula 1 OR F1 OR Grand Prix OR Racing'

            # HANDLE SOURCE FILTERING
            if sources:
                source_domain_map = {
                    'formula1': 'formula1.com',
                    'motorsport': 'motorsport.com',
                    'autosport': 'autosport.com',
                    'espn': 'espn.com',
                    'skysports': 'skysports.com',
                    'planetf1': 'planetf1.com'
                }
                selected_domains = [source_domain_map[s] for s in sources.split(',') if s in source_domain_map]
                domains = ','.join(selected_domains) if selected_domains else self.F1_DOMAINS
            else:
                domains = self.F1_DOMAINS

            # Try to get news using domains parameter
            try:
                news_response = self.api.get_everything(
                    q=query,
                    domains=domains,
                    from_param=from_date,
                    language='en',
                    sort_by='publishedAt',
                    page_size=page_size * 2,  # FETCH EXTRA ARTICLES FOR FILTERING
                    page=page
                )
            except Exception as api_error:
                # FALLBACK SEARCH IF DOMAIN-SPECIFIC SEARCH FAILS
                print(f"Domain-based search failed, trying general search: {api_error}")
                news_response = self.api.get_top_headlines(
                    q='Formula 1',
                    category='sports',
                    language='en',
                    page_size=page_size * 2,  # FETCH EXTRA ARTICLES FOR FILTERING
                    page=page
                )
                
            # FILTER IRRELEVANT ARTICLES
            filtered_articles = self._filter_articles(news_response.get('articles', []), page_size)
            
            # UPDATE RESPONSE WITH FILTERED ARTICLES
            news_response['articles'] = filtered_articles
            return news_response
        except ValueError:
            raise ValueError("The 'page' parameter must be an integer.")
        except Exception as e:
            print(f"Error fetching news: {e}")
            return {
                'status': 'error',
                'articles': [],
                'totalResults': 0,
                'message': str(e)
            }
    
    def _filter_articles(self, articles, max_results=30):
        """
        Filter articles to remove irrelevant content and duplicates
        
        Args:
            articles: List of article dictionaries from News API
            max_results: Maximum number of articles to return
            
        Returns:
            Filtered list of articles
        """
        if not articles:
            return []
            
        filtered_articles = []
        seen_content = set()  # TRACK SIMILAR CONTENT
        
        for article in articles:
            # SKIP INCOMPLETE ARTICLES
            if not article.get('title') or not article.get('description'):
                continue
                
            # STEP 1: CHECK FOR EXCLUDED TERMS
            should_exclude = False
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = article.get('content', '').lower()
            
            for term in self.EXCLUDE_TERMS:
                if term.lower() in title or term.lower() in description or term.lower() in content:
                    should_exclude = True
                    break
                    
            if should_exclude:
                continue
                
            # STEP 2: CHECK FOR DUPLICATES
            # CREATE CONTENT SIGNATURE
            title_words = set([w.lower() for w in article.get('title', '').split() if len(w) > 3])
            desc_words = set([w.lower() for w in article.get('description', '').split() if len(w) > 3])
            
            # COMBINE SIGNIFICANT WORDS
            content_signature = ' '.join(sorted(list(title_words)[:5] + list(desc_words)[:10]))
            
            # CHECK FOR SIMILAR CONTENT
            is_duplicate = False
            for existing_signature in seen_content:
                # CALCULATE SIMILARITY
                if self._calculate_similarity(content_signature, existing_signature) > 0.7:  # SIMILARITY THRESHOLD
                    is_duplicate = True
                    break
                    
            if is_duplicate:
                continue
                
            # ARTICLE PASSED ALL FILTERS
            seen_content.add(content_signature)
            filtered_articles.append(article)
            
            # ENFORCE MAX RESULTS LIMIT
            if len(filtered_articles) >= max_results:
                break
                
        return filtered_articles
        
    def _calculate_similarity(self, text1, text2):
        """
        Calculate similarity between two text strings
        Returns a value between 0 (completely different) and 1 (identical)
        """
        if not text1 or not text2:
            return 0
            
        # Split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
            
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    F1_SOURCES = [
        {'id': 'formula1', 'name': 'Formula1.com'},
        {'id': 'motorsport', 'name': 'Motorsport.com'},
        {'id': 'autosport', 'name': 'Autosport'},
        {'id': 'espn', 'name': 'ESPN F1'},
        {'id': 'skysports', 'name': 'Sky Sports F1'},
        {'id': 'planetf1', 'name': 'PlanetF1'}
    ]

    def get_available_sources(self):
        """Get available sources from our trusted F1 domains"""
        return {'status': 'success', 'sources': self.F1_SOURCES}
