// components/CloneForm.tsx
import { useState } from 'react';
import { Globe, Loader2, ExternalLink, AlertCircle, CheckCircle } from 'lucide-react';

interface CloneFormProps {
  onClone: (url: string) => void;
  isCloning: boolean;
  error: string;
  step: string;
  isComplete: boolean;
}

export default function CloneForm({ 
  onClone, 
  isCloning, 
  error, 
  step, 
  isComplete 
}: CloneFormProps) {
  const [url, setUrl] = useState('');

  const validateUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      return;
    }
    
    if (!validateUrl(url)) {
      return;
    }
    
    onClone(url);
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200/50 p-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          Clone Any Website
        </h1>
        <p className="text-gray-600 text-lg">
          Enter a website URL and our AI will create a pixel-perfect HTML clone
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Website URL
          </label>
          <div className="relative">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
              disabled={isCloning}
              required
            />
            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="absolute right-3 top-3 w-5 h-5 text-gray-400"
              >
                <ExternalLink />
              </a>
            )}
          </div>
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isCloning || !url.trim() || !validateUrl(url)}
          className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-6 rounded-xl font-medium hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {isCloning ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Cloning...</span>
            </>
          ) : (
            <>
              <Globe className="w-5 h-5" />
              <span>Clone Website</span>
            </>
          )}
        </button>
      </form>

      {/* Progress Steps */}
      {isCloning && (
        <div className="bg-gray-50 rounded-xl p-4 mt-4">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            </div>
            <span className="text-sm font-medium text-gray-700">{step}</span>
          </div>
          <div className="mt-3 bg-gray-200 rounded-full h-1">
            <div 
              className="bg-gradient-to-r from-indigo-600 to-purple-600 h-1 rounded-full transition-all duration-500"
              style={{
                width: step === 'Scraping website...' ? '33%' : 
                       step === 'Processing with AI...' ? '66%' : 
                       step === 'Generating HTML...' ? '90%' : '100%'
              }}
            />
          </div>
        </div>
      )}

      {isComplete && (
        <div className="flex items-center space-x-2 text-green-600 bg-green-50 p-3 rounded-lg mt-4">
          <CheckCircle className="w-5 h-5" />
          <span className="text-sm font-medium">Website cloned successfully!</span>
        </div>
      )}
    </div>
  );
}