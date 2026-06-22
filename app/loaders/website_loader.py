import requests
from bs4 import BeautifulSoup
from app.core.logger import logger

class WebsiteLoader:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        # Professional User-Agent string taaki requests block na hon
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def load(self, url: str) -> str:
        """
        Webpage se HTML content fetch karta hai aur usme se junk elements 
        (scripts, styles, navbars, footers) ko remove karke clean text return karta hai.
        """
        logger.info(self.headers)
        logger.info(f"Fetching content from website: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()  # Check for 404, 500 errors
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Scrap elements aur boilerplate (junk) ko decompose (remove) karein
            unwanted_elements = [
                "script", "style", "noscript", "header", 
                "footer", "nav", "aside", "form"
            ]
            for element in soup(unwanted_elements):
                element.decompose()
            
            # 2. Main content area ko target karne ki koshish karein (Optional optimization)
            # Agar article ya main body milti hai toh text extraction aur behtar ho jata hai
            main_content = soup.find("main") or soup.find("article") or soup
            
            # 3. Clean text extract karein
            text = main_content.get_text(separator="\n", strip=True)
            
            # 4. Multiple consecutive newlines ko single newline se replace karein
            clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
            final_text = "\n".join(clean_lines)
            
            logger.info(f"Successfully scraped and cleaned text from {url} ({len(final_text)} characters)")
            return final_text

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch website content from {url}: {str(e)}")
            raise Exception(f"Website extraction failed: {str(e)}")