from playwright.async_api import async_playwright
import re
import logging
from typing import Optional, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaulSmithScraper:
    def __init__(self):
        self.base_domain = "paulsmith.com"
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is from Paul Smith website"""
        return self.base_domain in url.lower()
    
    async def scrape_product(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape product name and price from Paul Smith URL"""
        if not self.is_valid_url(url):
            logger.warning(f"Invalid URL: {url}")
            return None
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set comprehensive headers to avoid detection
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://www.google.com/",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                })
                
                logger.info(f"Navigating to: {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Wait a bit for dynamic content
                await page.wait_for_timeout(2000)
                
                # Try to find product name - Paul Smith specific selectors
                name_selectors = [
                    "h1[data-testid='pdp-product-title']",
                    ".pdp-product-title",
                    "h1.pdp-title",
                    ".product-title h1",
                    ".product-name h1",
                    "h1.product-title",
                    "[data-testid='product-title']",
                    "h1"  # fallback
                ]
                
                product_name = None
                for selector in name_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            product_name = (await element.inner_text()).strip()
                            logger.info(f"Found product name with selector '{selector}': {product_name}")
                            break
                    except:
                        continue
                
                # Try to find price - Paul Smith specific selectors
                price_selectors = [
                    "[data-testid='pdp-price']",
                    ".pdp-price",
                    ".price-display",
                    ".product-price .current-price",
                    ".current-price",
                    ".price-current",
                    ".product-price",
                    ".price",
                    "[data-testid='price']",
                    ".price-now",
                    "span[class*='price']",
                    "[class*='price'][class*='current']"
                ]
                
                price_text = None
                price_selector_used = None
                
                for selector in price_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            price_text = (await element.inner_text()).strip()
                            if price_text:  # Only break if we actually got text
                                price_selector_used = selector
                                logger.info(f"Found price with selector '{selector}': {price_text}")
                                break
                    except:
                        continue
                
                # If no price found with specific selectors, try broader search
                if not price_text:
                    logger.info("Trying broader price search...")
                    try:
                        # Look for any element containing currency symbols
                        currency_elements = await page.query_selector_all("span, div, p, td")
                        for element in currency_elements[:50]:  # Limit search to avoid performance issues
                            try:
                                text = await element.inner_text()
                                if text and any(symbol in text for symbol in ['£', '$', '€']) and re.search(r'\d+[,.]?\d*', text):
                                    price_text = text.strip()
                                    logger.info(f"Found price via currency search: {price_text}")
                                    break
                            except:
                                continue
                    except Exception as e:
                        logger.warning(f"Broader price search failed: {e}")
                
                # Log page content for debugging if no price found
                if not price_text:
                    logger.warning("No price found. Checking page content...")
                    page_content = await page.content()
                    # Look for price patterns in the full page content
                    price_patterns = [
                        r'£\s*\d+[,.]?\d*',
                        r'\$\s*\d+[,.]?\d*',
                        r'€\s*\d+[,.]?\d*',
                        r'"price"[^}]*"value"[^}]*(\d+[,.]?\d*)',
                        r'data-price[^>]*(\d+[,.]?\d*)',
                        r'price[^>]*>.*?(£|\$|€)\s*(\d+[,.]?\d*)'
                    ]
                    
                    for pattern in price_patterns:
                        matches = re.findall(pattern, page_content, re.IGNORECASE)
                        if matches:
                            price_text = matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])
                            logger.info(f"Found price via regex pattern '{pattern}': {price_text}")
                            break
                
                await browser.close()
                
                if not product_name:
                    logger.error("Could not find product name")
                    return None
                
                # Extract numeric price from text
                price = self.extract_price(price_text) if price_text else None
                
                if price is None:
                    logger.error(f"Could not extract price from text: '{price_text}'")
                
                result = {
                    "name": product_name,
                    "price": price,
                    "currency": self.extract_currency(price_text) if price_text else "GBP"
                }
                
                logger.info(f"Scraping result: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from price text"""
        if not price_text:
            return None
            
        logger.info(f"Extracting price from: '{price_text}'")
        
        # Remove currency symbols and extra whitespace
        cleaned_text = re.sub(r'[£$€]', '', price_text).strip()
        
        # Find price patterns - handle commas as thousands separators
        price_patterns = [
            r'(\d{1,3}(?:,\d{3})*\.?\d{0,2})',  # 1,234.56 or 1234.56
            r'(\d+\.?\d{0,2})',                  # 123.45 or 123
            r'(\d+,\d{2})'                       # European format 123,45
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, cleaned_text)
            if matches:
                price_str = matches[0]
                try:
                    # Handle European comma decimal separator
                    if ',' in price_str and '.' not in price_str and len(price_str.split(',')[1]) == 2:
                        price_str = price_str.replace(',', '.')
                    else:
                        # Remove comma thousands separators
                        price_str = price_str.replace(',', '')
                    
                    price = float(price_str)
                    logger.info(f"Extracted price: {price}")
                    return price
                except ValueError as e:
                    logger.warning(f"Could not convert '{price_str}' to float: {e}")
                    continue
        
        logger.warning(f"No valid price found in: '{price_text}'")
        return None
    
    def extract_currency(self, price_text: str) -> str:
        """Extract currency from price text"""
        if not price_text:
            return "GBP"
            
        if "£" in price_text:
            return "GBP"
        elif "$" in price_text:
            return "USD"
        elif "€" in price_text:
            return "EUR"
        else:
            return "GBP"  # Default for Paul Smith