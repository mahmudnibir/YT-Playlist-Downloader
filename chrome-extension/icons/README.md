# YouTube Downloader Pro - Extension Icons

Since actual image files cannot be created via text, here are the icon specifications and sources:

## Required Icons:
- icon16.png (16x16) - Toolbar icon
- icon48.png (48x48) - Extension management page
- icon128.png (128x128) - Chrome Web Store and installation

## Design Specifications:
- **Theme**: Professional red and white design
- **Style**: Modern, clean, minimalist
- **Primary Color**: YouTube Red (#FF0000)
- **Secondary Color**: White (#FFFFFF)
- **Background**: Transparent or subtle gradient

## Icon Concepts:
1. **Download Arrow + Play Button**: Downward arrow combined with YouTube play triangle
2. **YT + Down Arrow**: "YT" text with download arrow
3. **Video + Download**: Video frame icon with download indicator

## SVG Template (for conversion to PNG):
```svg
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FF0000;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#CC0000;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Background circle -->
  <circle cx="64" cy="64" r="60" fill="url(#bg)" stroke="#FFFFFF" stroke-width="4"/>
  
  <!-- Play button triangle -->
  <polygon points="45,35 45,93 90,64" fill="#FFFFFF"/>
  
  <!-- Download arrow -->
  <path d="M64 20 L64 55 M50 45 L64 59 L78 45" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  
  <!-- Base line -->
  <line x1="45" y1="105" x2="83" y2="105" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
</svg>
```

## How to Create Icons:
1. Use the SVG template above
2. Convert to PNG at required sizes using:
   - Online converters (svg2png.com)
   - GIMP/Photoshop
   - Command line tools (inkscape, imagemagick)

## Alternative Sources:
- Use icon generators like favicon.io
- Professional icon packs from Flaticon
- Create using Canva or Figma

## Temporary Solution:
For testing, you can use any PNG files renamed to the required names.
The extension will work without icons, they'll just appear as default puzzle piece icons.

## File Structure:
```
chrome-extension/
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

Place your PNG icon files in the icons/ directory with these exact names.