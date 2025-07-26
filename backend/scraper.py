from playwright.async_api import async_playwright
import re
from typing import Optional, Dict

class PaulSmithScraper:
    def __init__(self):
        self.base_domain = "paulsmith.com"
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is from Paul Smith website"""
        return self.base_domain in url.lower()
    
    async def scrape_product(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape product name and price from Paul Smith URL"""
        if not self.is_valid_url(url):
            return None
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set user agent to avoid detection
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                
                await page.goto(url, wait_until="networkidle")
                
                # Try to find product name - common selectors for fashion sites
                name_selectors = [
                    "h1.product-title",
                    "h1[data-testid='product-title']",
                    ".product-name h1",
                    ".product-title",
                    "h1.pdp-product-name",
                    "h1"  # fallback
                ]
                
                product_name = None
                for selector in name_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            product_name = (await element.inner_text()).strip()
                            break
                    except:
                        continue
                
                # Try to find price - common selectors for fashion sites
                price_selectors = [
                    ".price .current-price",
                    ".price-current",
                    ".product-price",
                    ".price",
                    "[data-testid='price']",
                    ".price-now",
                    ".current-price"
                ]
                
                price_text = None
                for selector in price_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            price_text = (await element.inner_text()).strip()
                            break
                    except:
                        continue
                
                await browser.close()
                
                if not product_name:
                    return None
                
                # Extract numeric price from text
                price = self.extract_price(price_text) if price_text else None
                
                return {
                    "name": product_name,
                    "price": price,
                    "currency": self.extract_currency(price_text) if price_text else "GBP"
                }
                
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from price text"""
        if not price_text:
            return None
            
        # Remove common currency symbols and find numbers
        price_numbers = re.findall(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        
        if price_numbers:
            try:
                return float(price_numbers[0])
            except ValueError:
                return None
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