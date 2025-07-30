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
            
            # Fast price extraction - detect both sale price and original price
            sale_price_text = None
            original_price_text = None
            detected_currency = None
            page_content = await page.content()
            
            # First, try to find sale price using specific selectors
            logger.info("Looking for sale price selectors...")
            sale_price_selectors = [
                ".sale-price", ".current-price", ".discounted-price", ".final-price",
                ".price-sale", ".price-current", ".price-now", ".price-final",
                "[data-testid='sale-price']", "[data-testid='current-price']",
                ".price.sale", ".price.current", ".price.discounted",
                ".product-price-sale", ".product-price-current",
                "span[class*='sale-price']", "span[class*='current-price']",
                "div[class*='sale-price']", "div[class*='current-price']"
            ]
            
            for selector in sale_price_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements[:2]:  # Check first 2 matches only
                        text = await element.inner_text()
                        if text and any(symbol in text for symbol in ['£', '$', '€']):
                            sale_price_text = text.strip()
                            detected_currency = self.extract_currency(sale_price_text)
                            logger.info(f"Found SALE price with selector '{selector}': {sale_price_text}")
                            break
                    if sale_price_text:
                        break
                except:
                    continue
            
            # Look for original price selectors (crossed out, struck through, etc.)
            logger.info("Looking for original price selectors...")
            original_price_selectors = [
                ".original-price", ".was-price", ".strike-through", ".crossed-out",
                ".price-was", ".price-original", ".price-before", ".regular-price",
                "[data-testid='original-price']", "[data-testid='was-price']",
                ".price.original", ".price.was", ".price.before",
                "span[class*='original-price']", "span[class*='was-price']",
                "div[class*='original-price']", "div[class*='was-price']",
                "del", "s", ".strikethrough", "[style*='text-decoration: line-through']"
            ]
            
            for selector in original_price_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements[:2]:  # Check first 2 matches only
                        text = await element.inner_text()
                        if text and any(symbol in text for symbol in ['£', '$', '€']):
                            original_price_text = text.strip()
                            logger.info(f"Found ORIGINAL price with selector '{selector}': {original_price_text}")
                            break
                    if original_price_text:
                        break
                except:
                    continue
            
            # Advanced price detection focusing on product area
            if not sale_price_text or not original_price_text:
                logger.info("Looking for product-specific price patterns...")
                
                # Try to find prices near the product name or in product context
                product_name_lower = product_name.lower() if product_name else ""
                
                # Look for price patterns within a reasonable distance of product-related content
                product_context_patterns = [
                    # Prices near product, price, or sale keywords with limited character distance
                    rf'(?i)(?:.{{0,200}}(?:price|cost|£|$|€).{{0,50}}([£$€]\d{{1,3}}(?:,\d{{3}})*\.?\d{{0,2}}))',
                    rf'(?i)(?:([£$€]\d{{1,3}}(?:,\d{{3}})*\.?\d{{0,2}}).{{0,50}}(?:price|cost))',
                    # Look for consecutive prices (often sale + original)
                    rf'([£$€]\d{{1,3}}(?:,\d{{3}})*\.?\d{{0,2}}).{{0,100}}([£$€]\d{{1,3}}(?:,\d{{3}})*\.?\d{{0,2}})',
                ]
                
                found_price_pairs = []
                for pattern in product_context_patterns:
                    matches = re.findall(pattern, page_content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        if isinstance(match, tuple) and len(match) == 2:
                            # Two prices found together
                            price1 = self.extract_price(match[0])
                            price2 = self.extract_price(match[1])
                            if price1 and price2 and price1 != price2 and 1 <= min(price1, price2) <= 1000:
                                found_price_pairs.append((match[0], price1, match[1], price2))
                                logger.info(f"Found price pair: {match[0]} and {match[1]}")
                        elif isinstance(match, str):
                            # Single price found
                            price = self.extract_price(match)
                            if price and 1 <= price <= 1000:
                                if not sale_price_text:
                                    sale_price_text = match
                                    detected_currency = self.extract_currency(match)
                                    logger.info(f"Found single price in context: {match}")
                
                # If we found price pairs, use the first pair (assuming it's for this product)
                if found_price_pairs and not sale_price_text:
                    pair = found_price_pairs[0]
                    price1_val, price2_val = pair[1], pair[3]
                    
                    # Use lower price as sale price, higher as original
                    if price1_val < price2_val:
                        sale_price_text = pair[0]
                        original_price_text = pair[2]
                    else:
                        sale_price_text = pair[2]
                        original_price_text = pair[0]
                    
                    detected_currency = self.extract_currency(sale_price_text)
                    logger.info(f"Using price pair - Sale: {sale_price_text}, Original: {original_price_text}")
            
            # Fallback: Look for sale price patterns in context
            if not sale_price_text:
                logger.info("Looking for sale prices in page content...")
                
                # Look for sale price patterns in context
                sale_context_patterns = [
                    r'(?:sale|now|discounted?|reduced?|special|offer)[^£$€]*([£$€]\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                    r'([£$€]\d{1,3}(?:,\d{3})*\.?\d{0,2})[^£$€]*(?:sale|now|discounted?|reduced?)',
                ]
                
                for pattern in sale_context_patterns:
                    matches = re.findall(pattern, page_content, re.IGNORECASE)
                    if matches:
                        sale_price_text = matches[0]
                        detected_currency = self.extract_currency(sale_price_text)
                        logger.info(f"Found SALE price with context pattern: {sale_price_text}")
                        break
            
            # Fallback: Look for original price patterns in context (was, originally, etc.)
            if not original_price_text:
                logger.info("Looking for original prices in page content...")
                
                # Look for original price patterns in context
                original_context_patterns = [
                    r'(?:was|originally|before|regular|rrp)[^£$€]*([£$€]\d{1,3}(?:,\d{3})*\.?\d{0,2})',
                    r'([£$€]\d{1,3}(?:,\d{3})*\.?\d{0,2})[^£$€]*(?:was|originally|before|regular|rrp)',
                    r'<del[^>]*>.*?([£$€]\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?</del>',  # Strikethrough tags
                    r'<s[^>]*>.*?([£$€]\d{1,3}(?:,\d{3})*\.?\d{0,2}).*?</s>',      # Strikethrough tags
                ]
                
                for pattern in original_context_patterns:
                    matches = re.findall(pattern, page_content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        original_price_text = matches[0]
                        logger.info(f"Found ORIGINAL price with context pattern: {original_price_text}")
                        break
            
            # If still no prices found, fall back to general price patterns
            if not sale_price_text and not original_price_text:
                logger.info("No specific prices found, looking for general prices...")
                
                # Look for price patterns with currency symbols
                currency_patterns = [
                    (r'\$(\d{1,3}(?:,\d{3})*\.?\d{0,2})', '$', 'USD'),  # $313.00
                    (r'£(\d{1,3}(?:,\d{3})*\.?\d{0,2})', '£', 'GBP'),   # £140.00
                    (r'€(\d{1,3}(?:,\d{3})*\.?\d{0,2})', '€', 'EUR'),   # €38.00
                ]
                
                found_prices = []
                for pattern, symbol, currency in currency_patterns:
                    matches = re.findall(pattern, page_content)
                    if matches:
                        for match in matches:
                            found_prices.append((f"{symbol}{match}", currency, float(match.replace(',', ''))))
                
                # Choose prices from found matches
                if found_prices:
                    # Remove duplicates and sort by frequency and context
                    unique_prices = {}
                    for price_str, currency, value in found_prices:
                        key = (value, currency)
                        if key not in unique_prices:
                            unique_prices[key] = []
                        unique_prices[key].append(price_str)
                    
                    # Convert back to list and sort by frequency, then by value
                    price_candidates = [(value, currency, texts[0], len(texts)) for (value, currency), texts in unique_prices.items()]
                    
                    # If we have multiple prices, assign lowest as sale price and highest as original
                    if len(price_candidates) > 1:
                        price_candidates.sort(key=lambda x: x[0])  # Sort by value (lowest first)
                        sale_price_text = price_candidates[0][2]  # Lowest price (likely sale)
                        original_price_text = price_candidates[-1][2]  # Highest price (likely original)
                        detected_currency = price_candidates[0][1]
                        logger.info(f"Multiple prices found - Sale: {sale_price_text}, Original: {original_price_text}")
                    else:
                        # Only one price found, use it as the current price
                        sale_price_text = price_candidates[0][2]
                        detected_currency = price_candidates[0][1]
                        logger.info(f"Single price found: {sale_price_text}")
                    
                    logger.info(f"All found prices: {[(f'{p[2]} {p[1]}', f'freq:{p[3]}') for p in price_candidates]}")  # Show all with frequency
            
            # Final fallback to general DOM selectors
            if not sale_price_text:
                logger.info("Trying general DOM price selectors...")
                price_selectors = [
                    ".price", ".current-price", ".product-price", 
                    "[data-testid='price']", "span[class*='price']",
                    ".price-current", ".price-now"
                ]
                
                for selector in price_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements[:3]:  # Check first 3 matches only
                            text = await element.inner_text()
                            if text and any(symbol in text for symbol in ['£', '$', '€']):
                                sale_price_text = text.strip()
                                detected_currency = self.extract_currency(sale_price_text)
                                logger.info(f"Found price with general selector: {sale_price_text}")
                                break
                        if sale_price_text:
                            break
                    except:
                        continue
            
            await page.close()
            
            if not product_name:
                logger.error("Could not find product name")
                return None
            
            # Extract numeric prices from text
            current_price = self.extract_price(sale_price_text) if sale_price_text else None
            original_price = self.extract_price(original_price_text) if original_price_text else None
            
            # If we have both prices but current is higher than original, swap them
            if current_price and original_price and current_price > original_price:
                current_price, original_price = original_price, current_price
                logger.info("Swapped prices as current was higher than original")
            
            # If we only have one price, use it as the current price
            if not current_price:
                current_price = original_price
                original_price = None
            
            # Use detected currency if available, otherwise fall back to extraction
            final_currency = detected_currency if detected_currency else (
                self.extract_currency(sale_price_text or original_price_text) if (sale_price_text or original_price_text) else "GBP"
            )
            
            result = {
                "name": product_name,
                "price": current_price,  # Current/sale price
                "original_price": original_price,  # Original price if different
                "currency": final_currency
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