
import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
}

export const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ chart, className = '' }) => {
  const divRef = useRef<HTMLDivElement>(null);
  const [rendered, setRendered] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        securityLevel: 'loose',
        htmlLabels: true,
        curve: 'basis',
        useMaxWidth: true,
        suppressErrorRendering: true,
      });
    } catch (e) {
      console.log('Mermaid already initialized');
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    
    const render = async () => {
      if (!divRef.current || !chart.trim()) {
        return;
      }

      divRef.current.innerHTML = '';
      setError(null);
      
      try {
        const uniqueId = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(uniqueId, chart);
        
        if (isMounted && divRef.current) {
          divRef.current.innerHTML = svg;
          setRendered(true);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        console.error('Mermaid rendering error:', err);
        
        if (isMounted && divRef.current) {
          setError(errorMsg);
          divRef.current.innerHTML = `
            <div class="p-4 bg-slate-800 rounded-lg border border-slate-600">
              <h3 class="text-red-400 font-semibold mb-2">⚠️ 图表渲染失败</h3>
              <p class="text-slate-300 text-sm mb-2">${errorMsg}</p>
              <div class="bg-slate-900 p-3 rounded text-xs text-slate-400 mt-2">
                <p class="mb-1">图表代码：</p>
                <pre class="whitespace-pre-wrap max-h-32 overflow-y-auto">${chart}</pre>
              </div>
            </div>
          `;
        }
      }
    };

    render();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  return (
    <div className="space-y-2">
      <div
        ref={divRef}
        className={`w-full overflow-auto mermaid-container ${className}`}
        style={{ minHeight: '300px' }}
      />
      {!rendered && !error && (
        <div className="flex items-center justify-center h-32 text-slate-500">
          <div className="animate-pulse">正在渲染图表...</div>
        </div>
      )}
    </div>
  );
};

