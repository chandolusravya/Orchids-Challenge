# from fastapi import FastAPI

# app = FastAPI()


# @app.get("/")
# def read_root():
#     return {"message": "Hello World"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import playwright
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import base64
from urllib.parse import urljoin, urlparse
import time
import os
from datetime import datetime
import json
from .llm_workflow_updated import generate_cloned_html, extract_visual_context

# For cloud browser solutions
import requests
from playwright.sync_api import Playwright, sync_playwright
from browserbase import Browserbase
from fastapi import Body


app = FastAPI(title="Website Scraper API", 
              description="AI-Powered Website Cloning API", 
              version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
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
    viewport_width: int = 1920
    viewport_height: int = 1080
    wait_for_load: bool = True

class ScrapingResult(BaseModel):
    url: str
    title: str
    html: str
    screenshot: Optional[str] = None
    styles: List[Dict[str, Any]] = []
    assets: List[Dict[str, Any]] = []
    meta_data: Dict[str, Any] = {}
    dom_structure: Optional[Dict[str, Any]] = None
    visual_context: Optional[Dict[str, Any]] = None
    status: str
    processing_time: float

class CloneRequest(BaseModel):
    url: Optional[HttpUrl] = None
    context: Optional[Dict[str, Any]] = None
    enhance_quality: bool = True

class CloneResponse(BaseModel):
    cloned_html: str
    status: str
    processing_time: float

load_dotenv()

class WebsiteScraper:
    def __init__(self):
        self.browserbase_api_key = os.getenv("BROWSERBASE_API_KEY")
        self.browserbase_project_id = os.getenv("BROWSERBASE_PROJECT_ID")
        self.use_cloud_browser = bool(self.browserbase_api_key and self.browserbase_project_id)
        print(f"Using cloud browser: {self.use_cloud_browser}")
        
    def scrape_website(self, request: ScrapingRequest) -> ScrapingResult:
        start_time = time.time()
        
        try:
            if self.use_cloud_browser:
                with sync_playwright() as playwright:
                    result = self._scrape_with_browserbase(request, playwright)
            else:
                result = self._scrape_with_playwright(request)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            result.status = "success"
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"Scraping error: {str(e)}")
            return ScrapingResult(
                url=str(request.url),
                title="Error",
                html="",
                status=f"error: {str(e)}",
                processing_time=processing_time
            )

    def _scrape_with_browserbase(self, request: ScrapingRequest, playwright: Playwright) -> ScrapingResult:
        """Use Browserbase cloud browser service with official SDK"""
        
        # Initialize Browserbase client
        bb = Browserbase(api_key=self.browserbase_api_key)
        
        try:
            # Create a session
            session = bb.sessions.create(
                project_id=self.browserbase_project_id
            )
            
            print("Session replay URL:", f"https://browserbase.com/sessions/{session.id}")
            
            # Connect to the remote session
            chromium = playwright.chromium
            browser = chromium.connect_over_cdp(session.connect_url)
            context = browser.contexts[0]
            page = context.pages[0]
            
            # Set viewport
            page.set_viewport_size({
                'width': request.viewport_width,
                'height': request.viewport_height
            })
                
            try:
                # Navigate to URL with better error handling
                print(f"Navigating to: {request.url}")
                page.goto(str(request.url), 
                         timeout=request.timeout * 1000,
                         wait_until="domcontentloaded")
                
                # Wait for page to stabilize
                if request.wait_for_load:
                    page.wait_for_timeout(3000)  # Wait 3 seconds for dynamic content
                
                # Extract data
                title = page.title()
                html = page.content()
                
                print(f"Page loaded successfully. Title: {title}")
                
                # Screenshot
                screenshot = None
                if request.include_screenshot:
                    try:
                        screenshot_bytes = page.screenshot(full_page=True)
                        screenshot = base64.b64encode(screenshot_bytes).decode()
                        print("Screenshot captured")
                    except Exception as e:
                        print(f"Screenshot failed: {str(e)}")
                
                # Styles
                styles = []
                if request.include_styles:
                    styles = self._extract_styles(page)
                    print(f"Extracted {len(styles)} stylesheets")
                
                # Assets
                assets = []
                if request.include_assets:
                    assets = self._extract_assets(page, str(request.url))
                    print(f"Extracted {len(assets)} assets")
                
                # DOM structure
                dom_structure = None
                if request.include_dom:
                    dom_structure = self._extract_dom_structure(page)
                    print("DOM structure extracted")
                
                # Meta data and visual context
                meta_data = self._extract_meta_data(page)
                visual_context = None
                
                try:
                    visual_context = extract_visual_context(page)
                    print("Visual context extracted")
                except Exception as e:
                    print(f"Visual context extraction failed: {str(e)}")
                
            finally:
                # Clean up: close browser connection
                try:
                    page.close()
                    browser.close()
                    print(f"Closed browser for session: {session.id}")
                except Exception as cleanup_error:
                    print(f"Cleanup warning: {cleanup_error}")
                
        except Exception as e:
            print(f"Error in Browserbase scraping: {str(e)}")
            raise e
        
        return ScrapingResult(
            url=str(request.url),
            title=title,
            html=html,
            screenshot=screenshot,
            styles=styles,
            assets=assets,
            meta_data=meta_data,
            dom_structure=dom_structure,
            visual_context=visual_context,
            status="success",
            processing_time=0  # Will be set by caller
        )

    def _scrape_with_playwright(self, request: ScrapingRequest) -> ScrapingResult:
        """Use local Playwright browser with enhanced error handling"""
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = browser.new_context(
                viewport={
                    'width': request.viewport_width,
                    'height': request.viewport_height
                },
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            try:
                # Navigate with retry logic
                print(f"Navigating to: {request.url}")
                for attempt in range(3):
                    try:
                        page.goto(str(request.url), 
                                 timeout=request.timeout * 1000,
                                 wait_until="domcontentloaded")
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        print(f"Navigation attempt {attempt + 1} failed, retrying...")
                        time.sleep(2)
                
                # Wait for page to stabilize
                if request.wait_for_load:
                    page.wait_for_timeout(3000)
                
                # Extract data
                title = page.title()
                html = page.content()
                
                print(f"Page loaded successfully. Title: {title}")
                
                # Screenshot
                screenshot = None
                if request.include_screenshot:
                    try:
                        screenshot_bytes = page.screenshot(full_page=True)
                        screenshot = base64.b64encode(screenshot_bytes).decode()
                        print("Screenshot captured")
                    except Exception as e:
                        print(f"Screenshot failed: {str(e)}")
                
                # Styles
                styles = []
                if request.include_styles:
                    styles = self._extract_styles(page)
                    print(f"Extracted {len(styles)} stylesheets")
                
                # Assets
                assets = []
                if request.include_assets:
                    assets = self._extract_assets(page, str(request.url))
                    print(f"Extracted {len(assets)} assets")
                
                # DOM structure
                dom_structure = None
                if request.include_dom:
                    dom_structure = self._extract_dom_structure(page)
                    print("DOM structure extracted")
                
                # Meta data and visual context
                meta_data = self._extract_meta_data(page)
                visual_context = None
                
                try:
                    visual_context = extract_visual_context(page)
                    print("Visual context extracted")
                except Exception as e:
                    print(f"Visual context extraction failed: {str(e)}")
                
            finally:
                browser.close()
        
        return ScrapingResult(
            url=str(request.url),
            title=title,
            html=html,
            screenshot=screenshot,
            styles=styles,
            assets=assets,
            meta_data=meta_data,
            dom_structure=dom_structure,
            visual_context=visual_context,
            status="success",
            processing_time=0
        )

    def _extract_styles(self, page) -> List[Dict[str, Any]]:
        """Extract CSS styles from the page with better error handling"""
        try:
            stylesheets = page.evaluate("""
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
                                const content = sheet.ownerNode ? sheet.ownerNode.textContent : '';
                                if (content.trim()) {
                                    sheets.push({
                                        type: 'inline',
                                        content: content.substring(0, 5000), // Limit size
                                        rules: sheet.cssRules ? sheet.cssRules.length : 0
                                    });
                                }
                            }
                        } catch (e) {
                            // Cross-origin stylesheet, skip
                        }
                    }
                    return sheets;
                }
            """)
            return stylesheets
        except Exception as e:
            print(f"Style extraction error: {str(e)}")
            return []

    def _extract_assets(self, page, base_url: str) -> List[Dict[str, Any]]:
        """Extract assets with better error handling"""
        try:
            assets = page.evaluate("""
                () => {
                    const assets = [];
                    
                    // Images
                    document.querySelectorAll('img').forEach(img => {
                        if (img.src && img.src.startsWith('http')) {
                            assets.push({
                                type: 'image',
                                src: img.src,
                                alt: img.alt || '',
                                width: img.naturalWidth || img.width,
                                height: img.naturalHeight || img.height,
                                className: img.className,
                                id: img.id
                            });
                        }
                    });
                    
                    // Background images
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none' && bgImage.includes('url(')) {
                            const match = bgImage.match(/url\\(["']?([^"'\\)]+)["']?\\)/);
                            if (match && match[1].startsWith('http')) {
                                assets.push({
                                    type: 'background-image',
                                    src: match[1],
                                    element: el.tagName,
                                    className: el.className
                                });
                            }
                        }
                    });
                    
                    // Fonts
                    document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                        if (link.href && (link.href.includes('fonts') || link.href.includes('font'))) {
                            assets.push({
                                type: 'font',
                                src: link.href
                            });
                        }
                    });
                    
                    return assets;
                }
            """)
            return assets
        except Exception as e:
            print(f"Asset extraction error: {str(e)}")
            return []

    def _extract_dom_structure(self, page) -> Dict[str, Any]:
        """Extract DOM structure with better error handling"""
        try:
            dom = page.evaluate("""
                () => {
                    function extractElement(element, depth = 0) {
                        if (depth > 8) return null; // Prevent deep recursion
                        
                        const result = {
                            tag: element.tagName?.toLowerCase(),
                            id: element.id || null,
                            classes: element.className ? element.className.split(' ').filter(c => c) : [],
                            attributes: {},
                            children: []
                        };
                        
                        // Extract important attributes
                        const importantAttrs = ['src', 'href', 'alt', 'title', 'type', 'name', 'value'];
                        for (let attr of element.attributes || []) {
                            if (importantAttrs.includes(attr.name) || attr.name.startsWith('data-')) {
                                result.attributes[attr.name] = attr.value;
                            }
                        }
                        
                        // Extract text content for leaf nodes
                        if (element.children.length === 0 && element.textContent) {
                            const text = element.textContent.trim();
                            if (text && text.length < 200) {
                                result.text = text;
                            }
                        }
                        
                        // Process children
                        for (let child of element.children) {
                            const childResult = extractElement(child, depth + 1);
                            if (childResult) {
                                result.children.push(childResult);
                            }
                        }
                        
                        return result;
                    }
                    
                    return extractElement(document.body);
                }
            """)
            return dom
        except Exception as e:
            print(f"DOM extraction error: {str(e)}")
            return {}

    def _extract_meta_data(self, page) -> Dict[str, Any]:
        """Extract metadata from the page"""
        try:
            meta_data = page.evaluate("""
                () => {
                    const meta = {};
                    
                    // Basic meta tags
                    const description = document.querySelector('meta[name="description"]');
                    if (description) meta.description = description.content;
                    
                    const keywords = document.querySelector('meta[name="keywords"]');
                    if (keywords) meta.keywords = keywords.content;
                    
                    const author = document.querySelector('meta[name="author"]');
                    if (author) meta.author = author.content;
                    
                    // Open Graph
                    const ogTitle = document.querySelector('meta[property="og:title"]');
                    if (ogTitle) meta.og_title = ogTitle.content;
                    
                    const ogDescription = document.querySelector('meta[property="og:description"]');
                    if (ogDescription) meta.og_description = ogDescription.content;
                    
                    const ogImage = document.querySelector('meta[property="og:image"]');
                    if (ogImage) meta.og_image = ogImage.content;
                    
                    // Twitter Card
                    const twitterCard = document.querySelector('meta[name="twitter:card"]');
                    if (twitterCard) meta.twitter_card = twitterCard.content;
                    
                    // Viewport
                    const viewport = document.querySelector('meta[name="viewport"]');
                    if (viewport) meta.viewport = viewport.content;
                    
                    // Favicon
                    const favicon = document.querySelector('link[rel="icon"]') || 
                                   document.querySelector('link[rel="shortcut icon"]');
                    if (favicon) meta.favicon = favicon.href;
                    
                    // Canonical URL
                    const canonical = document.querySelector('link[rel="canonical"]');
                    if (canonical) meta.canonical = canonical.href;
                    
                    return meta;
                }
            """)
            return meta_data
        except Exception as e:
            print(f"Meta data extraction error: {str(e)}")
            return {}


# Initialize scraper
scraper = WebsiteScraper()

# API Endpoints
@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint with API documentation"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Website Scraper API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #007acc; }
            code { background: #e1e1e1; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🕷️ Website Scraper API</h1>
        <p>AI-Powered Website Cloning API v2.0.0</p>
        
        <h2>Available Endpoints:</h2>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <code>/</code> - This documentation page</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">POST</span> <code>/scrape</code> - Scrape a website and extract comprehensive data</p>
            <p><strong>Body:</strong> ScrapingRequest JSON</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">POST</span> <code>/clone</code> - Generate an HTML clone of a website</p>
            <p><strong>Body:</strong> CloneRequest JSON</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">POST</span> <code>/scrape-and-clone</code> - Scrape and clone in one step</p>
            <p><strong>Body:</strong> ScrapingRequest JSON</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <code>/health</code> - Health check endpoint</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <code>/docs</code> - Interactive API documentation (Swagger)</p>
        </div>
        
        <h2>Features:</h2>
        <ul>
            <li>🖼️ Full-page screenshots</li>
            <li>🎨 CSS extraction and analysis</li>
            <li>📱 Responsive design detection</li>
            <li>🎭 AI-powered HTML cloning</li>
            <li>🔍 Visual context extraction</li>
            <li>☁️ Cloud browser support (Browserbase)</li>
            <li>🚀 High-performance scraping</li>
        </ul>
        
        <p><strong>Powered by:</strong> Playwright, FastAPI, and Claude/GPT AI models</p>
    </body>
    </html>
    """

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "cloud_browser_enabled": scraper.use_cloud_browser
    }

@app.post("/scrape", response_model=ScrapingResult)
def scrape_website(request: ScrapingRequest):
    """
    Scrape a website and extract comprehensive data including:
    - HTML content
    - Screenshots
    - CSS styles
    - Assets (images, fonts, etc.)
    - DOM structure
    - Visual context
    - Metadata
    """
    try:
        print(f"Scraping request for: {request.url}")
        result = scraper.scrape_website(request)
        print(f"Scraping completed in {result.processing_time:.2f}s")
        return result
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.post("/clone", response_model=CloneResponse)
def clone_website(request: CloneRequest):
    """
    Generate an HTML clone of a website using AI.
    Provide either a URL to scrape first, or pre-scraped context data.
    """
    start_time = time.time()
    
    try:
        # If URL is provided, scrape it first
        if request.url:
            print(f"Scraping for cloning: {request.url}")
            scrape_request = ScrapingRequest(
                url=request.url,
                include_screenshot=True,
                include_dom=True,
                include_assets=True,
                include_styles=True,
                wait_for_load=True
            )
            scrape_result = scraper.scrape_website(scrape_request)
            
            if scrape_result.status.startswith("error"):
                raise HTTPException(status_code=500, detail=f"Scraping failed: {scrape_result.status}")
            
            # Convert scraping result to context
            context = {
                "title": scrape_result.title,
                "html": scrape_result.html,
                "meta_data": scrape_result.meta_data,
                "dom_structure": scrape_result.dom_structure,
                "visual_context": scrape_result.visual_context,
                "styles": scrape_result.styles,
                "assets": scrape_result.assets
            }
        elif request.context:
            context = request.context
        else:
            raise HTTPException(status_code=400, detail="Either 'url' or 'context' must be provided")
        
        # Generate HTML clone
        print("Generating HTML clone with LLM...")
        cloned_html = generate_cloned_html(context)
        
        processing_time = time.time() - start_time
        print(f"Cloning completed in {processing_time:.2f}s")
        
        return CloneResponse(
            cloned_html=cloned_html,
            status="success",
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"Cloning failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cloning failed: {str(e)}")

@app.post("/scrape-and-clone")
def scrape_and_clone_website(request: ScrapingRequest):
    """
    Scrape a website and immediately generate an HTML clone.
    This is a convenience endpoint that combines both operations.
    """
    start_time = time.time()
    
    try:
        # First scrape the website
        print(f"Scraping and cloning: {request.url}")
        scrape_result = scraper.scrape_website(request)
        
        if scrape_result.status.startswith("error"):
            raise HTTPException(status_code=500, detail=f"Scraping failed: {scrape_result.status}")
        
        # Convert to context for cloning
        context = {
            "title": scrape_result.title,
            "html": scrape_result.html,
            "meta_data": scrape_result.meta_data,
            "dom_structure": scrape_result.dom_structure,
            "visual_context": scrape_result.visual_context,
            "styles": scrape_result.styles,
            "assets": scrape_result.assets
        }
        
        # Generate HTML clone
        print("Generating HTML clone...")
        cloned_html = generate_cloned_html(context)
        
        processing_time = time.time() - start_time
        print(f"Scrape and clone completed in {processing_time:.2f}s")
        
        return {
            "scrape_result": scrape_result,
            "clone_result": {
                "cloned_html": cloned_html,
                "status": "success",
                "processing_time": processing_time
            },
            "total_processing_time": processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"Scrape and clone failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

@app.post("/preview-clone", response_class=HTMLResponse)
def preview_clone(request: CloneRequest):
    """
    Generate and preview an HTML clone directly in the browser.
    Returns the cloned HTML for immediate viewing.
    """
    try:
        # Generate the clone
        clone_response = clone_website(request)
        
        if clone_response.status == "success":
            return HTMLResponse(content=clone_response.cloned_html)
        else:
            return HTMLResponse(
                content=f"<html><body><h1>Clone Generation Failed</h1><p>{clone_response.status}</p></body></html>",
                status_code=500
            )
            
    except Exception as e:
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>",
            status_code=500
        )

# Error handlers
@app.exception_handler(404)
def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "available_endpoints": ["/", "/scrape", "/clone", "/scrape-and-clone", "/health", "/docs"]}

@app.exception_handler(500)
def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": str(exc)}

# Startup event
@app.on_event("startup")
def startup_event():
    print("🕷️ Website Scraper API v2.0.0 starting up...")
    print(f"Cloud browser enabled: {scraper.use_cloud_browser}")
    if scraper.use_cloud_browser:
        print("Using Browserbase for browser automation")
    else:
        print("Using local Playwright browser")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)