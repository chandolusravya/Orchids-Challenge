// components/PreviewPanel.tsx
import { Globe, Copy, Download } from 'lucide-react';

interface PreviewPanelProps {
  clonedHtml: string;
  onCopy: () => void;
  onDownload: () => void;
}

export default function PreviewPanel({ 
  clonedHtml, 
  onCopy, 
  onDownload 
}: PreviewPanelProps) {
  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200/50 overflow-hidden">
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200/50">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Preview</h2>
          {clonedHtml && (
            <div className="flex space-x-2">
              <button
                onClick={onCopy}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
                title="Copy HTML"
              >
                <Copy className="w-4 h-4" />
              </button>
              <button
                onClick={onDownload}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
                title="Download HTML"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
      
      <div className="h-96 lg:h-[600px]">
        {clonedHtml ? (
          <iframe
            srcDoc={clonedHtml}
            className="w-full h-full border-0"
            title="Cloned Website Preview"
          />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Globe className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium mb-2">No preview yet</p>
              <p className="text-sm">Enter a URL and click on "Clone Website" to see the result</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}