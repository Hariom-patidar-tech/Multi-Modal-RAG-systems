import requests
from bs4 import BeautifulSoup
from app.core.logger import logger

class WebsiteLoader:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def load(self, url: str) -> str:
        
        logger.info(self.headers)
        logger.info(f"Fetching content from website: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status() 
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            unwanted_elements = [
                "script", "style", "noscript", "header", 
                "footer", "nav", "aside", "form"
            ]
            for element in soup(unwanted_elements):
                element.decompose()
            
          
            main_content = soup.find("main") or soup.find("article") or soup
            
            text = main_content.get_text(separator="\n", strip=True)
            
            clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
            final_text = "\n".join(clean_lines)
            
            logger.info(f"Successfully scraped and cleaned text from {url} ({len(final_text)} characters)")
            return final_text

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch website content from {url}: {str(e)}")
            raise Exception(f"Website extraction failed: {str(e)}")