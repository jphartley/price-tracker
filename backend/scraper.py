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
        self.browser = None
        self.context = None
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is from Paul Smith website"""
        return self.base_domain in url.lower()
    
    async def _ensure_browser(self):
        """Ensure browser is running and ready"""
        if self.browser is None or not self.browser.is_connected():
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows'
                ]
            )
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Referer": "https://www.google.com/"
                }
            )

    async def scrape_product(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape product name and price from Paul Smith URL"""
        if not self.is_valid_url(url):
            logger.warning(f"Invalid URL: {url}")
            return None
            
        try:
            await self._ensure_browser()
            page = await self.context.new_page()
            
            logger.info(f"Navigating to: {url}")
            # Optimize page load - don't wait for all network activity
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Quick check for page load completion
            try:
                await page.wait_for_selector("h1", timeout=5000)
            except:
                logger.warning("Page might not be fully loaded, continuing anyway")
            
            # Fast product name extraction
            product_name = None
            name_selectors = [
                "h1",  # Start with most common first
                "h1[data-testid='pdp-product-title']",
                ".pdp-product-title",
                "h1.pdp-title",
                ".product-title h1",
                ".product-name h1"
            ]
            
            for selector in name_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        product_name = (await element.inner_text()).strip()
                        if product_name:  # Only break if we got actual text
                            logger.info(f"Found product name: {product_name}")
                            break
                except:
                    continue
            
            # Fast price extraction - try direct page content search first
            price_text = None
            page_content = await page.content()
            
            # Look for price patterns in page content (fastest method)
            price_patterns = [
                r'\$(\d{1,3}(?:,\d{3})*\.?\d{0,2})',  # $313.00
                r'£(\d{1,3}(?:,\d{3})*\.?\d{0,2})',   # £140.00
                r'€(\d{1,3}(?:,\d{3})*\.?\d{0,2})',   # €38.00
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    currency_symbol = pattern[2]  # Extract currency symbol from pattern
                    price_text = f"{currency_symbol}{matches[0]}"  # Add currency symbol back
                    logger.info(f"Found price via regex: {price_text}")
                    break
            
            # Fallback to DOM selectors only if regex fails
            if not price_text:
                logger.info("Trying DOM price selectors...")
                price_selectors = [
                    ".price", ".current-price", ".product-price", 
                    "[data-testid='price']", "span[class*='price']"
                ]
                
                for selector in price_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements[:3]:  # Check first 3 matches only
                            text = await element.inner_text()
                            if text and any(symbol in text for symbol in ['£', '$', '€']):
                                price_text = text.strip()
                                logger.info(f"Found price with selector: {price_text}")
                                break
                        if price_text:
                            break
                    except:
                        continue
            
            await page.close()
            
            if not product_name:
                logger.error("Could not find product name")
                return None
            
            # Extract numeric price from text
            price = self.extract_price(price_text) if price_text else None
            
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

    async def close(self):
        """Close browser and cleanup resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from price text"""
        if not price_text:
            return None
            
        logger.info(f"Extracting price from: '{price_text[:200]}...'")  # Truncate long text for logging
        
        # Find price patterns with currency symbols (most reliable)
        currency_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*\.?\d{0,2})', # $1,234.56 or $1234.56
            r'£(\d{1,3}(?:,\d{3})*\.?\d{0,2})',  # £1,234.56 or £1234.56
            r'€(\d{1,3}(?:,\d{3})*\.?\d{0,2})',  # €1,234.56 or €1234.56
        ]
        
        # Try currency patterns first (most reliable)
        for pattern in currency_patterns:
            matches = re.findall(pattern, price_text)
            if matches:
                price_str = matches[0]  # Take the first match
                try:
                    # Remove comma thousands separators
                    price_str = price_str.replace(',', '')
                    price = float(price_str)
                    logger.info(f"Extracted price with currency: {price}")
                    return price
                except ValueError as e:
                    logger.warning(f"Could not convert '{price_str}' to float: {e}")
                    continue
        
        # Fallback to number-only patterns
        number_patterns = [
            r'(\d{1,3}(?:,\d{3})*\.\d{2})',   # 1,234.56 (must have 2 decimal places)
            r'(\d{3,}\.?\d{0,2})',            # 123.45 or 123 (at least 3 digits)
            r'(\d+,\d{2})'                    # European format 123,45
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, price_text)
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
                    # Only accept reasonable prices (between $1 and $10,000)
                    if 1 <= price <= 10000:
                        logger.info(f"Extracted price: {price}")
                        return price
                except ValueError as e:
                    logger.warning(f"Could not convert '{price_str}' to float: {e}")
                    continue
        
        logger.warning(f"No valid price found in text")
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