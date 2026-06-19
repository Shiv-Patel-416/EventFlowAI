const fs = require('fs');
let content = fs.readFileSync('presentation/EventFlowAI_Presentation.html', 'utf8');

// Replace CSS classes
content = content.replace(/\.logo-box \{[\s\S]*?\}/, `.logo-box {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(6, 182, 212, 0.2);
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.15);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    position: relative;
    overflow: hidden;
  }
  .logo-box::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom right, rgba(6,182,212,0.1), rgba(37,99,235,0.1));
  }`);

content = content.replace(/\.slide-header \.logo-box-sm \{[\s\S]*?\}/, `.slide-header .logo-box-sm {
    width: 32px; height: 32px; border-radius: 10px;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(6, 182, 212, 0.2);
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.15);
    display: inline-flex; align-items: center; justify-content: center; color: white;
    position: relative; overflow: hidden;
  }
  .slide-header .logo-box-sm::before {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(to bottom right, rgba(6,182,212,0.1), rgba(37,99,235,0.1));
  }`);

// Replace SVG
let newSvg = `<svg viewBox="0 0 24 24" fill="none" style="position: relative; z-index: 10; width: 100%; height: 100%; transform: scale(0.6);">
        <circle cx="12" cy="12" r="8" stroke="#06B6D4" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.6"/>
        <circle cx="12" cy="12" r="4" stroke="#3B82F6" stroke-width="2"/>
        <circle cx="12" cy="12" r="1" fill="#fff" />
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3" stroke="#06B6D4" stroke-width="1.5" stroke-linecap="round" opacity="0.8"/>
      </svg>`;

content = content.replace(/<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\s*<polyline[^>]*><\/polyline>\s*<\/svg>/g, newSvg);

fs.writeFileSync('presentation/EventFlowAI_Presentation.html', content);
console.log('done');
