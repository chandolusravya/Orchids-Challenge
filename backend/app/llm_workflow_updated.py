from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
import os
from langchain_anthropic import ChatAnthropic
import json
import re

load_dotenv()

USE_CLAUDE = os.getenv("CLAUDE_API_KEY")
USE_GPT = os.getenv("OPENAI_API_KEY")

if USE_CLAUDE:
    llm = ChatAnthropic(model_name="claude-3-5-sonnet-20241022", temperature=0.1, api_key=USE_CLAUDE)
else:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1, api_key=USE_GPT)

def extract_visual_context(page) -> Dict[str, Any]:
    """Extract comprehensive visual context from the page"""
    visual_context = page.evaluate("""
        () => {
            const context = {
                colors: new Set(),
                fonts: new Set(),
                layout: {},
                elements: [],
                images: [],
                links: []
            };
            
            // Extract color palette with better specificity
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const styles = window.getComputedStyle(el);
                const color = styles.color;
                const bgColor = styles.backgroundColor;
                const borderColor = styles.borderColor;
                
                if (color && color !== 'rgba(0, 0, 0, 0)' && color !== 'rgb(0, 0, 0)') {
                    context.colors.add(color);
                }
                if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'rgb(255, 255, 255)') {
                    context.colors.add(bgColor);
                }
                if (borderColor && borderColor !== 'rgba(0, 0, 0, 0)') {
                    context.colors.add(borderColor);
                }
            });
            
            // Extract fonts with weights and sizes
            const fontInfo = new Set();
            allElements.forEach(el => {
                const styles = window.getComputedStyle(el);
                const fontFamily = styles.fontFamily;
                const fontSize = styles.fontSize;
                const fontWeight = styles.fontWeight;
                if (fontFamily && fontFamily !== 'inherit') {
                    fontInfo.add(`${fontFamily}|${fontSize}|${fontWeight}`);
                }
            });
            context.fonts = Array.from(fontInfo);
            
            // Extract comprehensive layout information
            const body = document.body;
            const bodyStyles = window.getComputedStyle(body);
            context.layout = {
                display: bodyStyles.display,
                flexDirection: bodyStyles.flexDirection,
                justifyContent: bodyStyles.justifyContent,
                alignItems: bodyStyles.alignItems,
                padding: bodyStyles.padding,
                margin: bodyStyles.margin,
                backgroundColor: bodyStyles.backgroundColor,
                width: bodyStyles.width,
                minHeight: bodyStyles.minHeight,
                fontFamily: bodyStyles.fontFamily
            };
            
            // Extract images with better details
            document.querySelectorAll('img').forEach(img => {
                context.images.push({
                    src: img.src,
                    alt: img.alt || '',
                    width: img.width || img.naturalWidth,
                    height: img.height || img.naturalHeight,
                    className: img.className,
                    id: img.id
                });
            });
            
            // Extract navigation links
            document.querySelectorAll('a').forEach(link => {
                if (link.textContent.trim()) {
                    context.links.push({
                        href: link.href,
                        text: link.textContent.trim(),
                        className: link.className,
                        id: link.id
                    });
                }
            });
            
            // Extract key structural elements with precise styling
            const importantSelectors = [
                'header', 'nav', 'main', 'footer', 'section', 'article', 'aside',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div',
                '.hero', '#hero', '.container', '.wrapper', '.navbar', '.header',
                '.footer', '.content', '.main', '.sidebar'
            ];
            
            importantSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach((el, index) => {
                    if (index < 5) { // Limit to prevent overwhelming data
                        const styles = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        context.elements.push({
                            selector: selector,
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            position: {
                                top: rect.top,
                                left: rect.left,
                                width: rect.width,
                                height: rect.height
                            },
                            styles: {
                                display: styles.display,
                                position: styles.position,
                                width: styles.width,
                                height: styles.height,
                                padding: styles.padding,
                                margin: styles.margin,
                                backgroundColor: styles.backgroundColor,
                                color: styles.color,
                                fontSize: styles.fontSize,
                                fontFamily: styles.fontFamily,
                                fontWeight: styles.fontWeight,
                                textAlign: styles.textAlign,
                                border: styles.border,
                                borderRadius: styles.borderRadius,
                                boxShadow: styles.boxShadow,
                                transform: styles.transform,
                                opacity: styles.opacity,
                                zIndex: styles.zIndex,
                                flexDirection: styles.flexDirection,
                                justifyContent: styles.justifyContent,
                                alignItems: styles.alignItems,
                                gridTemplateColumns: styles.gridTemplateColumns,
                                gridTemplateRows: styles.gridTemplateRows
                            },
                            textContent: el.textContent?.substring(0, 200)
                        });
                    }
                });
            });
            
            return {
                colors: Array.from(context.colors),
                fonts: context.fonts,
                layout: context.layout,
                elements: context.elements,
                images: context.images,
                links: context.links.slice(0, 20) // Limit links
            };
        }
    """)
    
    return visual_context

def build_enhanced_prompt(context: Dict[str, Any]) -> str:
    """Build a comprehensive prompt with visual context for better HTML generation"""
    title = context.get("title", "")
    meta = context.get("meta_data", {})
    dom = context.get("dom_structure", {})
    html_content = context.get("html", "")
    
    # Extract visual context
    visual_context = context.get("visual_context", {})
    colors = visual_context.get("colors", [])
    fonts = visual_context.get("fonts", [])
    layout = visual_context.get("layout", {})
    key_elements = visual_context.get("elements", [])
    images = visual_context.get("images", [])
    links = visual_context.get("links", [])
    
    # Clean HTML content and extract key structure
    html_summary = clean_html_for_analysis(html_content)
    
    prompt = f"""
You are a world-class web designer and front-end developer. Your task is to create a pixel-perfect HTML clone of a website based on the comprehensive design context provided.

## WEBSITE INFORMATION:
- Title: {title}
- Meta Description: {meta.get('description', 'N/A')}

## VISUAL DESIGN CONTEXT:
### Color Palette:
{json.dumps(colors[:15], indent=2)}

### Typography:
{json.dumps(fonts[:10], indent=2)}

### Layout Structure:
{json.dumps(layout, indent=2)}

### Key Elements (with precise styling):
{json.dumps(key_elements[:15], indent=2)}

### Images:
{json.dumps(images[:10], indent=2)}

### Navigation Links:
{json.dumps(links[:15], indent=2)}

## ORIGINAL HTML STRUCTURE ANALYSIS:
{html_summary}

## CRITICAL REQUIREMENTS:

1. **EXACT VISUAL REPLICATION**: Create HTML that looks identical to the original
2. **COMPLETE HTML DOCUMENT**: Include <!DOCTYPE html>, <html>, <head>, and <body>
3. **INLINE CSS**: Use <style> tags in <head> - NO external stylesheets
4. **RESPONSIVE DESIGN**: Ensure it works on different screen sizes
5. **SEMANTIC HTML**: Use proper HTML5 semantic elements
6. **NO JAVASCRIPT**: Static HTML/CSS only
7. **PLACEHOLDER IMAGES**: Use https://via.placeholder.com for images with appropriate dimensions
8. **WORKING NAVIGATION**: Include all navigation elements (even if links are placeholder)

## STYLING GUIDELINES:
- Use exact colors from the color palette
- Replicate font families, sizes, and weights precisely
- Match spacing, margins, and padding exactly
- Recreate layouts using modern CSS (Flexbox/Grid)
- Include hover effects and transitions where visible
- Maintain visual hierarchy and typography scale
- Replicate shadows, borders, and visual effects

## OUTPUT FORMAT:
Return ONLY the complete, valid HTML document. No explanations, no code blocks, just the raw HTML.

Generate the pixel-perfect HTML clone now:
"""
    
    return prompt

def clean_html_for_analysis(html_content: str) -> str:
    """Clean and summarize HTML content for better analysis"""
    if not html_content:
        return ""
    
    # Remove script tags and their content
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove style tags (we'll use computed styles instead)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove comments
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
    
    # Remove excessive whitespace
    html_content = re.sub(r'\s+', ' ', html_content)
    
    # Truncate if too long but preserve structure
    if len(html_content) > 3000:
        html_content = html_content[:3000] + "..."
    
    return html_content

def generate_cloned_html(context: Dict[str, Any]) -> str:
    """Generate enhanced HTML with better visual context and error handling"""
    try:
        prompt = build_enhanced_prompt(context)
        
        system_message = """You are an expert web designer and front-end developer specializing in:
- Pixel-perfect website replication
- Modern CSS techniques (Flexbox, Grid, Custom Properties)
- Responsive web design
- HTML5 semantic structure
- Cross-browser compatibility
- Visual design principles

CRITICAL INSTRUCTIONS:
1. Generate COMPLETE, VALID HTML documents only
2. Include ALL CSS inline using <style> tags in <head>
3. Use modern CSS techniques for layouts
4. Replicate colors, fonts, spacing, and layouts exactly
5. Make it responsive and accessible
6. NO external dependencies or JavaScript
7. Return ONLY the HTML code, no explanations

Your output will be directly used as an HTML file, so it must be complete and functional."""

        # Chain the LLM + output parser
        chain = (
            llm
            | StrOutputParser()
        )

        # Run the chain with system and human message
        result = chain.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=prompt)
        ])
        
        # Clean the result
        cleaned = clean_llm_output(result)
        
        # Validate HTML structure
        if not validate_html_structure(cleaned):
            print("Warning: Generated HTML may be incomplete")
        
        # Save to file
        with open("cloned_site.html", "w", encoding="utf-8") as f:
            f.write(cleaned)
        
        print(f"Generated HTML clone ({len(cleaned)} characters)")
        return cleaned
        
    except Exception as e:
        print(f"Error in LLM generation: {str(e)}")
        return generate_fallback_html(context, str(e))

def clean_llm_output(result: str) -> str:
    """Clean and validate LLM output"""
    # Remove markdown code blocks if present
    cleaned = re.sub(r"^```html\n?", "", result.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```$", "", cleaned.strip())
    
    # Ensure it starts with DOCTYPE
    if not cleaned.strip().lower().startswith('<!doctype'):
        cleaned = '<!DOCTYPE html>\n' + cleaned
    
    return cleaned.strip()

def validate_html_structure(html: str) -> bool:
    """Basic validation of HTML structure"""
    required_tags = ['<!doctype', '<html', '<head', '<body']
    html_lower = html.lower()
    
    return all(tag in html_lower for tag in required_tags)

def generate_fallback_html(context: Dict[str, Any], error_msg: str) -> str:
    """Generate a basic fallback HTML when LLM fails"""
    title = context.get("title", "Website Clone")
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .error-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #e74c3c;
            margin-bottom: 20px;
        }}
        .error-message {{
            background: #fdf2f2;
            border: 1px solid #fca5a5;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>Website Clone Generation Failed</h1>
        <p>We encountered an error while generating the website clone.</p>
        <div class="error-message">
            <strong>Error:</strong> {error_msg}
        </div>
        <p>Please try again or contact support if the issue persists.</p>
    </div>
</body>
</html>"""