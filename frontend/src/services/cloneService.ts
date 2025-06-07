export interface CloneResult {
  html: string;
  originalUrl: string;
  timestamp: string;
  screenshot?: string;
  processingTime?: number;
}

export interface CloneProgress {
  step: string;
  progress: number;
}


interface ScrapingResult {
  url: string;
  title: string;
  html: string;
  screenshot?: string;
  styles: Array<{
    type: 'external' | 'inline';
    href?: string;
    content?: string;
    rules: number;
  }>;
  assets: Array<{
    type: 'image' | 'background-image' | 'font';
    src: string;
    alt?: string;
    width?: number;
    height?: number;
    element?: string;
  }>;
  meta_data: Record<string, any>;
  dom_structure?: any;
  status: string;
  processing_time: number;
}
// Backend clone request/response interfaces
interface CloneRequest {
  context: Record<string, any>;
}

interface CloneResponse {
  cloned_html: string;
}

type ProgressCallback = (step: string) => void;

// const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE_URL = 'http://localhost:8000';

export async function cloneWebsite(
  url: string, 
  onProgress?: ProgressCallback
): Promise<CloneResult> {
  try {
    // Step 1: Start scraping with FastAPI backend
    onProgress?.('Scraping website...');
    
    const scrapeResponse = await fetch(`${API_BASE_URL}/scrape`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url,
        include_screenshot: true,
        include_dom: true,
        include_assets: true,
        include_styles: true,
        timeout: 30,
        viewport_width: 1920,
        viewport_height: 1080
      }),
    });

    if (!scrapeResponse.ok) {
      const errorData = await scrapeResponse.json();
      throw new Error(`Scraping failed: ${errorData.detail || scrapeResponse.statusText}`);
    }

    const scrapeData: ScrapingResult = await scrapeResponse.json();

    // Check if scraping was successful
    if (scrapeData.status !== 'success') {
      throw new Error(`Scraping failed: ${scrapeData.status}`);
    }

    // Step 2: Process with AI (you'll implement this endpoint later)
    onProgress?.('Processing with AI...');
    
    // For now, we'll create a basic clone using the scraped data
    // Later you can add an AI processing endpoint
    const clonedHtml = await processScrapedData(scrapeData);
    
    return {
      html: clonedHtml,
      originalUrl: url,
      timestamp: new Date().toISOString(),
      screenshot: scrapeData.screenshot,
      processingTime: scrapeData.processing_time,
    };

  } catch (error) {
    console.error('Clone service error:', error);
    throw error;
  }
}

// export async function cloneWebsite(
//   url: string, 
//   onProgress?: ProgressCallback
// ): Promise<CloneResult> {
//   try {
//     // Step 1: Start scraping with FastAPI backend
//     onProgress?.('Scraping website...');
    
//     const scrapeResponse = await fetch(`${API_BASE_URL}/scrape`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         url: url,
//         include_screenshot: true,
//         include_dom: true,
//         include_assets: true,
//         include_styles: true,
//         timeout: 30,
//         viewport_width: 1920,
//         viewport_height: 1080
//       }),
//     });

//     if (!scrapeResponse.ok) {
//       const errorData = await scrapeResponse.json();
//       throw new Error(`Scraping failed: ${errorData.detail || scrapeResponse.statusText}`);
//     }

//     const scrapeData: ScrapingResult = await scrapeResponse.json();

//     // Check if scraping was successful
//     if (scrapeData.status !== 'success') {
//       throw new Error(`Scraping failed: ${scrapeData.status}`);
//     }

//     // Step 2: Process with AI using the /clone endpoint
//     onProgress?.('Processing with AI...');
    
//     const cloneResponse = await fetch(`${API_BASE_URL}/clone`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         context: {
//           url: scrapeData.url,
//           title: scrapeData.title,
//           html: scrapeData.html,
//           styles: scrapeData.styles,
//           assets: scrapeData.assets,
//           meta_data: scrapeData.meta_data,
//           dom_structure: scrapeData.dom_structure,
//           screenshot: scrapeData.screenshot
//         }
//       } as CloneRequest),
//     });

//     if (!cloneResponse.ok) {
//       const errorData = await cloneResponse.json();
//       throw new Error(`AI processing failed: ${errorData.detail || cloneResponse.statusText}`);
//     }

//     const cloneData: CloneResponse = await cloneResponse.json();
    
//     onProgress?.('AI processing complete!');
    
//     return {
//       html: cloneData.cloned_html,
//       originalUrl: url,
//       timestamp: new Date().toISOString(),
//       screenshot: scrapeData.screenshot,
//       processingTime: scrapeData.processing_time,
//     };

//   } catch (error) {
//     console.error('Clone service error:', error);
//     throw error;
//   }
// }

// Helper function to process scraped data into cloned HTML
async function processScrapedData(scrapeData: ScrapingResult): Promise<string> {
  // Extract key information
  const { title, html, styles, assets, meta_data } = scrapeData;
  
  
  let clonedHtml = html;
  
  // Add some basic optimizations
  clonedHtml = cleanHtml(clonedHtml);
  
  return clonedHtml;
}

// Basic HTML cleaning function
function cleanHtml(html: string): string {
  // Remove potentially problematic scripts
  let cleaned = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  
  // Remove external tracking scripts
  cleaned = cleaned.replace(/google-analytics|googletagmanager|facebook|twitter\.com\/widgets/gi, '');
  
  // Add meta viewport if missing
  if (!cleaned.includes('viewport')) {
    cleaned = cleaned.replace(
      '<head>',
      '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
    );
  }
  
  return cleaned;
}

// Health check for the scraper service
export async function checkScraperHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

