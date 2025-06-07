from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
import base64
from urllib.parse import urljoin, urlparse
import time
import os
from datetime import datetime
import json

# For cloud browser solutions
import requests
from playwright.async_api import async_playwright

app = FastAPI(title="Website Scraper API", 
              description="A starter FastAPI template for the Orchids Challenge backend", 
              version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ScrapingRequest(BaseModel):
    url: HttpUrl
    include_screenshot: bool = True
    include_dom: bool = True
    include_assets: bool = True
    include_styles: bool = True
    timeout: int = 30
    # wait_for_selector: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080

class ScrapingResult(BaseModel):
    url: str
    title: str
    html: str
    screenshot: Optional[str] = None
    styles: List[Dict[str, Any]] = []
    assets: List[Dict[str, Any]] = []
    meta_data: Dict[str, Any] = {}
    dom_structure: Optional[Dict[str, Any]] = None
    status: str
    processing_time: float

load_dotenv()

class WebsiteScraper:
    def __init__(self):
        self.browserbase_api_key = os.getenv("BROWSERBASE_API_KEY")
        print("printing:",self.browserbase_api_key)
        self.use_cloud_browser = bool(self.browserbase_api_key)
        print("cloud: ",self.use_cloud_browser)
        
    async def scrape_website(self, request: ScrapingRequest) -> ScrapingResult:
        start_time = time.time()
        
        try:
            if self.use_cloud_browser:
                result = await self._scrape_with_playwright(request)
            else:
                result = await self._scrape_with_playwright(request)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            result.status = "success"
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ScrapingResult(
                url=str(request.url),
                title="Error",
                html="",
                status=f"error: {str(e)}",
                processing_time=processing_time
            )

    

    async def _scrape_with_playwright(self, request: ScrapingRequest) -> ScrapingResult:
        """Use local Playwright browser"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            page = await browser.new_page(
                viewport={
                    'width': request.viewport_width,
                    'height': request.viewport_height
                }
            )
            
            # Set user agent to avoid blocks
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            try:
                # Navigate with retry logic
                for attempt in range(3):
                    try:
                        await page.goto(str(request.url), 
                                      timeout=request.timeout * 1000,
                                      wait_until="networkidle")
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        await asyncio.sleep(2)
                
                # Wait for selector if specified
                # if request.wait_for_selector:
                #     await page.wait_for_selector(request.wait_for_selector, timeout=10000)
                
                # Extract data
                title = await page.title()
                html = await page.content()
                
                # Screenshot
                screenshot = None
                if request.include_screenshot:
                    screenshot_bytes = await page.screenshot(full_page=True)
                    screenshot = base64.b64encode(screenshot_bytes).decode()
                
                # Styles
                styles = []
                if request.include_styles:
                    styles = await self._extract_styles(page)
                
                # Assets
                assets = []
                if request.include_assets:
                    assets = await self._extract_assets(page, str(request.url))
                
                # DOM structure
                dom_structure = None
                if request.include_dom:
                    dom_structure = await self._extract_dom_structure(page)
                
                # Meta data
                meta_data = await self._extract_meta_data(page)
                
            finally:
                await browser.close()
        
        return ScrapingResult(
            url=str(request.url),
            title=title,
            html=html,
            screenshot=screenshot,
            styles=styles,
            assets=assets,
            meta_data=meta_data,
            dom_structure=dom_structure,
            status="success",
            processing_time=0  # Will be set by caller
        )

    async def _extract_styles(self, page) -> List[Dict[str, Any]]:
        """Extract CSS styles from the page"""
        styles = []
        
        # Get all stylesheets
        stylesheets = await page.evaluate("""
            () => {
                const sheets = [];
                for (let sheet of document.styleSheets) {
                    try {
                        if (sheet.href) {
                            sheets.push({
                                type: 'external',
                                href: sheet.href,
                                rules: sheet.cssRules ? sheet.cssRules.length : 0
                            });
                        } else {
                            sheets.push({
                                type: 'inline',
                                content: sheet.ownerNode ? sheet.ownerNode.textContent : '',
                                rules: sheet.cssRules ? sheet.cssRules.length : 0
                            });
                        }
                    } catch (e) {
                        // Cross-origin stylesheet, skip
                    }
                }
                return sheets;
            }
        """)
        
        return stylesheets

    async def _extract_assets(self, page, base_url: str) -> List[Dict[str, Any]]:
        """Extract assets (images, fonts, etc.) from the page"""
        assets = await page.evaluate("""
            () => {
                const assets = [];
                
                // Images
                document.querySelectorAll('img').forEach(img => {
                    if (img.src) {
                        assets.push({
                            type: 'image',
                            src: img.src,
                            alt: img.alt || '',
                            width: img.naturalWidth,
                            height: img.naturalHeight
                        });
                    }
                });
                
                // Background images
                const elements = document.querySelectorAll('*');
                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const bgImage = style.backgroundImage;
                    if (bgImage && bgImage !== 'none') {
                        const match = bgImage.match(/url\\("?([^"]*)"?\\)/);
                        if (match) {
                            assets.push({
                                type: 'background-image',
                                src: match[1],
                                element: el.tagName
                            });
                        }
                    }
                });
                
                // Fonts
                document.querySelectorAll('link[rel="stylesheet"], style').forEach(el => {
                    if (el.href && el.href.includes('fonts')) {
                        assets.push({
                            type: 'font',
                            src: el.href
                        });
                    }
                });
                
                return assets;
            }
        """)
        
        return assets

    async def _extract_dom_structure(self, page) -> Dict[str, Any]:
        """Extract simplified DOM structure"""
        dom = await page.evaluate("""
            () => {
                function extractElement(element, depth = 0) {
                    if (depth > 10) return null; // Prevent infinite recursion
                    
                    const result = {
                        tag: element.tagName?.toLowerCase(),
                        id: element.id || null,
                        classes: element.className ? element.className.split(' ') : [],
                        attributes: {},
                        children: []
                    };
                    
                    // Extract important attributes
                    const importantAttrs = ['src', 'href', 'alt', 'title', 'data-*'];
                    for (let attr of element.attributes || []) {
                        if (importantAttrs.some(important => 
                            attr.name === important || attr.name.startsWith('data-'))) {
                            result.attributes[attr.name] = attr.value;
                        }
                    }
                    
                    // Extract text content (if no children)
                    if (element.children.length === 0 && element.textContent) {
                        result.text = element.textContent.trim().substring(0, 100);
                    }
                    
                    // Extract children (limit to important elements)
                    const importantTags = ['div', 'section', 'article', 'header', 'footer', 'nav', 'main', 'aside', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'img', 'a', 'button'];
                    for (let child of element.children) {
                        if (importantTags.includes(child.tagName?.toLowerCase())) {
                            const childResult = extractElement(child, depth + 1);
                            if (childResult) {
                                result.children.push(childResult);
                            }
                        }
                    }
                    
                    return result;
                }
                
                return extractElement(document.body);
            }
        """)
        
        return dom

    async def _extract_meta_data(self, page) -> Dict[str, Any]:
        """Extract meta data from the page"""
        meta = await page.evaluate("""
            () => {
                const meta = {};
                
                // Basic meta tags
                document.querySelectorAll('meta').forEach(tag => {
                    const name = tag.getAttribute('name') || tag.getAttribute('property');
                    const content = tag.getAttribute('content');
                    if (name && content) {
                        meta[name] = content;
                    }
                });
                
                // Title
                meta.title = document.title;
                
                // Favicon
                const favicon = document.querySelector('link[rel="icon"], link[rel="shortcut icon"]');
                if (favicon) {
                    meta.favicon = favicon.href;
                }
                
                // Viewport
                const viewport = document.querySelector('meta[name="viewport"]');
                if (viewport) {
                    meta.viewport = viewport.content;
                }
                
                // Color scheme
                const colorScheme = document.querySelector('meta[name="color-scheme"]');
                if (colorScheme) {
                    meta.colorScheme = colorScheme.content;
                }
                
                return meta;
            }
        """)
        
        return meta

# Initialize scraper
scraper = WebsiteScraper()

@app.post("/api/scrape", response_model=ScrapingResult)
async def scrape_website(request: ScrapingRequest):
    """Scrape a website and return structured data"""
    try:
        result = await scraper.scrape_website(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Website Scraper API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



