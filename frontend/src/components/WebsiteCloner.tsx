// components/WebsiteCloner.tsx
'use client';

import { useState } from 'react';
import Header from './Header';
import CloneForm from './CloneForm';
import PreviewPanel from './PreviewPanel';
import FeatureCards from './FeatureCards';
import { cloneWebsite } from '@/services/cloneService';

export default function WebsiteCloner() {
  const [isCloning, setIsCloning] = useState(false);
  const [clonedHtml, setClonedHtml] = useState('');
  const [error, setError] = useState('');
  const [step, setStep] = useState('');

  const handleClone = async (url: string) => {
    setIsCloning(true);
    setError('');
    setClonedHtml('');
    
    try {
      const result = await cloneWebsite(url, (currentStep) => {
        setStep(currentStep);
      });
      
      setClonedHtml(result.html);
      setStep('Complete!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clone website. Please try again.');
    } finally {
      setIsCloning(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(clonedHtml);
  };

  const downloadHtml = () => {
    const blob = new Blob([clonedHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cloned-website.html';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="space-y-6">
            <CloneForm
              onClone={handleClone}
              isCloning={isCloning}
              error={error}
              step={step}
              isComplete={!!clonedHtml}
            />
            
            <FeatureCards />
          </div>

          {/* Preview Section */}
          <div className="space-y-6">
            <PreviewPanel
              clonedHtml={clonedHtml}
              onCopy={copyToClipboard}
              onDownload={downloadHtml}
            />
          </div>
        </div>
      </div>
    </div>
  );
}