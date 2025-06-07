// src/services/scraperService.ts ---redundant file to delete
interface ScrapingOptions {
  includeScreenshot?: boolean;
  includeDom?: boolean;
  includeAssets?: boolean;
  includeStyles?: boolean;
  timeout?: number;
  waitForSelector?: string;
  viewportWidth?: number;
  viewportHeight?: number;
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
  metaData: Record<string, any>;
  domStructure?: {
    tag: string;
    id?: string;
    classes: string[];
    attributes: Record<string, string>;
    children: any[];
    text?: string;
  };
  status: string;
  processingTime: number;
}

class ScraperService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_SCRAPER_API_URL || 'http://localhost:8000';
  }

  async scrapeWebsite(url: string, options: ScrapingOptions = {}): Promise<ScrapingResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          include_screenshot: options.includeScreenshot ?? true,
          include_dom: options.includeDom ?? true,
          include_assets: options.includeAssets ?? true,
          include_styles: options.includeStyles ?? true,
          timeout: options.timeout ?? 30,
          wait_for_selector: options.waitForSelector,
          viewport_width: options.viewportWidth ?? 1920,
          viewport_height: options.viewportHeight ?? 1080,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Scraping failed');
      }

      const result: ScrapingResult = await response.json();
      return result;
    } catch (error) {
      console.error('Scraping error:', error);
      throw new Error(error instanceof Error ? error.message : 'Unknown scraping error');
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Utility methods for processing scraped data
  extractImages(result: ScrapingResult): string[] {
    return result.assets
      .filter(asset => asset.type === 'image')
      .map(asset => asset.src);
  }

  extractColors(result: ScrapingResult): string[] {
    // Extract colors from CSS styles
    const colors: string[] = [];
    result.styles.forEach(style => {
      if (style.content) {
        const colorRegex = /#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})|rgb\([^)]+\)|rgba\([^)]+\)/g;
        const matches = style.content.match(colorRegex);
        if (matches) {
          colors.push(...matches);
        }
      }
    });
    return [...new Set(colors)]; // Remove duplicates
  }

  extractFonts(result: ScrapingResult): string[] {
    const fonts: string[] = [];
    result.styles.forEach(style => {
      if (style.content) {
        const fontRegex = /font-family:\s*([^;}]+)/g;
        let match;
        while ((match = fontRegex.exec(style.content)) !== null) {
          fonts.push(match[1].trim().replace(/['"]/g, ''));
        }
      }
    });
    return [...new Set(fonts)];
  }

  getScreenshotDataUrl(result: ScrapingResult): string | null {
    if (!result.screenshot) return null;
    return `data:image/png;base64,${result.screenshot}`;
  }
}

export const scraperService = new ScraperService();
export type { ScrapingResult, ScrapingOptions };