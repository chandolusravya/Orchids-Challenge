# Orchids SWE Intern Challenge 

 Goal: A web app that will take in any given public website URL, scrape the website for useful design context, and give it to an LLM model to replicate the website in HTML. The goal is to create an HTML website that is as aesthetically similar as possible to the given website at the specified URL. 


This project consists of a backend built with FastAPI and a frontend built with Next.js and TypeScript.

## 🛠 Tech Stack

### Frontend
- **Next.js** – React-based framework for server-side rendering and routing  
- **Lucide React** – Icon library for clean and customizable UI elements  
- **Tailwind CSS** – Utility-first CSS framework for rapid UI development  

### Backend
- **FastAPI** – High-performance Python web framework for building APIs  
- **LLM Integration** – GPT (OpenAI), Claude (Anthropic) for LLM workflows  
- **Web Scraping** – Browserbase + Playwright for headless browser automation


## Backend

The backend uses `uv` for package management.

### Installation

To install the backend dependencies, run the following command in the backend project directory:

```bash
uv sync
```

### Running the Backend

To run the backend development server, use the following command:

```bash
uv run fastapi dev
```

## Frontend

The frontend is built with Next.js and TypeScript.

### Installation

To install the frontend dependencies, navigate to the frontend project directory and run:

```bash
npm install
```

### Running the Frontend

To start the frontend development server, run:

```bash
npm run dev
```
### Project Structure - frontend
<pre> 
    src/
    ├── app/
    │   ├── layout.tsx          # Root layout with metadata
    │   ├── page.tsx            # Main page component
    │   └── globals.css         # Global styles
    ├── components/
    │   ├── WebsiteCloner.tsx   # Main container component
    │   ├── Header.tsx          # Navigation header
    │   ├── CloneForm.tsx       # URL input form
    │   ├── PreviewPanel.tsx    # HTML preview iframe
    │   └── FeatureCards.tsx    # Feature showcase cards
    ├── services/
    │   └── cloneService.ts     # API service layer
    ├── types/
    │   └── index.ts            # TypeScript definitions

</pre>
