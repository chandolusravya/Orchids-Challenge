// types/index.ts
export interface ScrapeData {
  html: string;
  css: string[];
  images: string[];
  metadata: {
    title: string;
    description: string;
    viewport: string;
  };
  screenshot?: string;
  dom_structure: any;
}

export interface CloneRequest {
  url: string;
  scrapeData: ScrapeData;
}

export interface CloneResponse {
  html: string;
  success: boolean;
  message?: string;
  processing_time?: number;
}

export interface ApiError {
  error: string;
  details?: string;
  code?: number;
}