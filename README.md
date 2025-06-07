# Orchids SWE Intern Challenge Template

This project consists of a backend built with FastAPI and a frontend built with Next.js and TypeScript.

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
└── config files...