// components/FeatureCards.tsx
import { Globe, Copy, Download } from 'lucide-react';

export default function FeatureCards() {
  const features = [
    {
      icon: Globe,
      title: 'Smart Scraping',
      description: 'Advanced web scraping with anti-bot protection using Browserbase',
      color: 'blue'
    },
    {
      icon: Copy,
      title: 'AI Cloning',
      description: 'Claude and GPT powered design replication',
      color: 'blue'
    },
    {
      icon: Download,
      title: 'Export Ready',
      description: 'Download clean, production-ready HTML',
      color: 'blue'
    }
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-600',
      purple: 'bg-purple-100 text-purple-600',
      green: 'bg-green-100 text-green-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {features.map((feature, index) => {
        const Icon = feature.icon;
        return (
          <div 
            key={index}
            className="bg-white rounded-xl p-4 shadow-sm border border-gray-200/50"
          >
            <div className={`w-8 h-8 ${getColorClasses(feature.color)} rounded-lg flex items-center justify-center mb-3`}>
              <Icon className="w-4 h-4" />
            </div>
            <h3 className="font-medium text-gray-900 mb-1">{feature.title}</h3>
            <p className="text-sm text-gray-600">{feature.description}</p>
          </div>
        );
      })}
    </div>
  );
}