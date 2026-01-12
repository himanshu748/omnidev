"""
OmniDev - Web Scraping Service
Provides browser automation with Selenium and Playwright for web scraping
"""

import asyncio
import base64
from typing import Optional, Dict, Any, Literal
from bs4 import BeautifulSoup
from dataclasses import dataclass
from enum import Enum


class ScraperEngine(str, Enum):
    """Available scraping engines"""
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"


@dataclass
class ScrapeResult:
    """Result of a scraping operation"""
    success: bool
    url: str
    title: str
    html: str
    text: str
    screenshot: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None
    engine: str = "playwright"
    load_time_ms: int = 0


class ScraperService:
    """Web scraping service with Selenium and Playwright support"""
    
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._selenium_driver = None
    
    async def _init_playwright(self):
        """Initialize Playwright browser"""
        if self._playwright is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
                    ]
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Playwright: {e}")
        return self._browser
    
    def _init_selenium(self):
        """Initialize Selenium with undetected-chromedriver"""
        if self._selenium_driver is None:
            try:
                import undetected_chromedriver as uc
                options = uc.ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                self._selenium_driver = uc.Chrome(options=options)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Selenium: {e}")
        return self._selenium_driver
    
    async def scrape_with_playwright(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_time_ms: int = 2000,
        capture_screenshot: bool = False,
        extract_selector: Optional[str] = None,
    ) -> ScrapeResult:
        """
        Scrape a URL using Playwright
        
        Args:
            url: URL to scrape
            wait_for_selector: CSS selector to wait for before scraping
            wait_time_ms: Time to wait for page load in milliseconds
            capture_screenshot: Whether to capture a screenshot
            extract_selector: CSS selector to extract specific content
            
        Returns:
            ScrapeResult with scraped data
        """
        import time
        start_time = time.time()
        
        try:
            browser = await self._init_playwright()
            
            # Create context with stealth settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True,
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """)
            
            page = await context.new_page()
            
            # Navigate to URL
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for specific selector if provided
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=10000)
            else:
                await page.wait_for_timeout(wait_time_ms)
            
            # Get page content
            title = await page.title()
            
            if extract_selector:
                element = await page.query_selector(extract_selector)
                if element:
                    html = await element.inner_html()
                else:
                    html = await page.content()
            else:
                html = await page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            text = soup.get_text(separator='\n', strip=True)
            
            # Capture screenshot if requested
            screenshot_b64 = None
            if capture_screenshot:
                screenshot_bytes = await page.screenshot(full_page=False)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            await context.close()
            
            load_time = int((time.time() - start_time) * 1000)
            
            return ScrapeResult(
                success=True,
                url=url,
                title=title,
                html=html,
                text=text,
                screenshot=screenshot_b64,
                engine="playwright",
                load_time_ms=load_time,
            )
            
        except Exception as e:
            return ScrapeResult(
                success=False,
                url=url,
                title="",
                html="",
                text="",
                error=str(e),
                engine="playwright",
            )
    
    def scrape_with_selenium(
        self,
        url: str,
        wait_time_sec: int = 3,
        capture_screenshot: bool = False,
        extract_selector: Optional[str] = None,
    ) -> ScrapeResult:
        """
        Scrape a URL using Selenium with undetected-chromedriver
        
        Args:
            url: URL to scrape
            wait_time_sec: Time to wait for page load in seconds
            capture_screenshot: Whether to capture a screenshot
            extract_selector: CSS selector to extract specific content
            
        Returns:
            ScrapeResult with scraped data
        """
        import time
        start_time = time.time()
        
        try:
            driver = self._init_selenium()
            
            # Navigate to URL
            driver.get(url)
            time.sleep(wait_time_sec)
            
            # Get page content
            title = driver.title
            
            if extract_selector:
                from selenium.webdriver.common.by import By
                try:
                    element = driver.find_element(By.CSS_SELECTOR, extract_selector)
                    html = element.get_attribute('innerHTML')
                except:
                    html = driver.page_source
            else:
                html = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            text = soup.get_text(separator='\n', strip=True)
            
            # Capture screenshot if requested
            screenshot_b64 = None
            if capture_screenshot:
                screenshot_bytes = driver.get_screenshot_as_png()
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            load_time = int((time.time() - start_time) * 1000)
            
            return ScrapeResult(
                success=True,
                url=url,
                title=title,
                html=html,
                text=text,
                screenshot=screenshot_b64,
                engine="selenium",
                load_time_ms=load_time,
            )
            
        except Exception as e:
            return ScrapeResult(
                success=False,
                url=url,
                title="",
                html="",
                text="",
                error=str(e),
                engine="selenium",
            )
    
    async def scrape(
        self,
        url: str,
        engine: ScraperEngine = ScraperEngine.PLAYWRIGHT,
        wait_time_ms: int = 2000,
        capture_screenshot: bool = False,
        extract_selector: Optional[str] = None,
    ) -> ScrapeResult:
        """
        Scrape a URL using the specified engine
        
        Args:
            url: URL to scrape
            engine: Scraping engine to use (playwright or selenium)
            wait_time_ms: Time to wait for page load
            capture_screenshot: Whether to capture a screenshot
            extract_selector: CSS selector to extract specific content
            
        Returns:
            ScrapeResult with scraped data
        """
        if engine == ScraperEngine.PLAYWRIGHT:
            return await self.scrape_with_playwright(
                url=url,
                wait_time_ms=wait_time_ms,
                capture_screenshot=capture_screenshot,
                extract_selector=extract_selector,
            )
        else:
            # Run Selenium in a thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.scrape_with_selenium(
                    url=url,
                    wait_time_sec=wait_time_ms // 1000,
                    capture_screenshot=capture_screenshot,
                    extract_selector=extract_selector,
                )
            )
    
    async def take_screenshot(self, url: str, engine: ScraperEngine = ScraperEngine.PLAYWRIGHT) -> ScrapeResult:
        """Take a screenshot of a URL"""
        return await self.scrape(url=url, engine=engine, capture_screenshot=True)
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        if self._selenium_driver:
            self._selenium_driver.quit()
            self._selenium_driver = None
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of scraper engines"""
        playwright_available = False
        selenium_available = False
        
        try:
            import playwright
            playwright_available = True
        except ImportError:
            pass
        
        try:
            import undetected_chromedriver
            selenium_available = True
        except ImportError:
            pass
        
        return {
            "playwright": {
                "available": playwright_available,
                "browser_active": self._browser is not None,
            },
            "selenium": {
                "available": selenium_available,
                "driver_active": self._selenium_driver is not None,
            }
        }


# Singleton instance
scraper_service = ScraperService()
