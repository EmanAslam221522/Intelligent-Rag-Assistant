import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional
import logging
from urllib.parse import urlparse, urljoin
import time

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.timeout = 30
    
    def scrape_url(self, url: str) -> Optional[Dict]:
        """Scrape content from a URL"""
        try:
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError("Invalid URL format")
            
            # Make request
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content
            content = self._extract_content(soup, url)
            
            if not content or len(content.get('text', '').strip()) < 100:
                raise ValueError("Insufficient content extracted from URL")
            
            return content
            
        except requests.RequestException as e:
            logging.error(f"Request error for URL {url}: {str(e)}")
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            logging.error(f"Error scraping URL {url}: {str(e)}")
            raise Exception(f"Failed to scrape URL: {str(e)}")
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract meaningful content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Try to find main content using common selectors
        content_selectors = [
            'article',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.main-content',
            'main',
            '.container',
            '#content',
            '.post',
            '.blog-post'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(main_content.get_text().strip()) > 200:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract text content
        text_content = self._clean_text(main_content.get_text())
        
        # Extract metadata
        metadata = self._extract_metadata(soup)
        
        return {
            'title': title,
            'text': text_content,
            'url': url,
            'metadata': metadata,
            'scraped_at': time.time()
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title = None
        
        # Try different title selectors
        title_selectors = ['title', 'h1', '.title', '.post-title', '.entry-title']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 3:
                    break
        
        return title or "Untitled"
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'Advertisement',
            r'Subscribe',
            r'Newsletter',
            r'Follow us',
            r'Share this',
            r'Cookie policy',
            r'Privacy policy',
            r'Terms of service'
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '')
        
        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = meta_keywords.get('content', '')
        
        # Extract author
        author_selectors = [
            'meta[name="author"]',
            '.author',
            '.byline',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                metadata['author'] = author_elem.get('content') or author_elem.get_text()
                break
        
        # Extract publication date
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            '.date',
            '.published',
            '.publish-date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                metadata['published_date'] = date_elem.get('content') or date_elem.get_text()
                break
        
        return metadata
    
    def scrape_multiple_urls(self, urls: list) -> Dict[str, Dict]:
        """Scrape multiple URLs with rate limiting"""
        results = {}
        
        for i, url in enumerate(urls):
            try:
                results[url] = self.scrape_url(url)
                
                # Rate limiting - wait between requests
                if i < len(urls) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                results[url] = {'error': str(e)}
        
        return results
    
    def is_scrapable(self, url: str) -> bool:
        """Check if URL is likely scrapable"""
        try:
            # Quick HEAD request to check if accessible
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False


