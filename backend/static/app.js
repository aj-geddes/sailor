// Initialize variables
let editor;
let currentTheme = 'dark';
let currentDirection = 'TB';
let currentLook = 'classic';

// Initialize Mermaid with v11 config
mermaid.initialize({
    startOnLoad: false,
    theme: currentTheme,
    look: currentLook,
    flowchart: {
        curve: 'basis'
    }
});

// Initialize CodeMirror
document.addEventListener('DOMContentLoaded', function() {
    const textArea = document.getElementById('mermaidCode');
    editor = CodeMirror.fromTextArea(textArea, {
        mode: 'markdown',
        theme: 'monokai',
        lineNumbers: true,
        lineWrapping: true,
        autofocus: true
    });

    // Set initial content
    editor.setValue(`graph TD
    A[Start] --> B{Is it?}
    B -->|Yes| C[OK]
    B -->|No| D[End]`);

    // Set up event listeners
    editor.on('change', debounce(renderMermaid, 500));
    
    document.getElementById('theme').addEventListener('change', handleThemeChange);
    document.getElementById('direction').addEventListener('change', handleDirectionChange);
    document.getElementById('look').addEventListener('change', handleLookChange);
    document.getElementById('generateBtn').addEventListener('click', generateDiagram);
    document.getElementById('apiKey').addEventListener('input', debounce(validateApiKey, 1000));
    document.getElementById('provider').addEventListener('change', clearKeyStatus);
    document.getElementById('copyCodeBtn').addEventListener('click', copyCode);
    document.getElementById('copyImageBtn').addEventListener('click', copyImage);

    // Initial render
    renderMermaid();
});

// Render Mermaid diagram
async function renderMermaid() {
    const container = document.getElementById('mermaidPreview');
    let code = editor.getValue();

    // Apply direction
    if (currentDirection !== 'TB') {
        code = code.replace(/graph\s+\w+/, `graph ${currentDirection}`);
        if (!code.includes(`graph ${currentDirection}`)) {
            code = code.replace(/graph/, `graph ${currentDirection}`);
        }
    }

    // Clear previous content
    container.innerHTML = '';

    try {
        // Create a unique ID for this render
        const id = `mermaid-${Date.now()}`;
        
        // Re-initialize mermaid with current settings
        mermaid.initialize({
            startOnLoad: false,
            theme: currentTheme,
            look: currentLook,
            flowchart: {
                curve: 'basis'
            }
        });

        // Render the diagram
        const { svg } = await mermaid.render(id, code);
        container.innerHTML = svg;
    } catch (error) {
        container.innerHTML = `<div style="color: #f44336; padding: 20px;">Error: ${error.message}</div>`;
    }
}

// Handle theme change
function handleThemeChange(e) {
    currentTheme = e.target.value;
    renderMermaid();
}

// Handle direction change
function handleDirectionChange(e) {
    currentDirection = e.target.value;
    renderMermaid();
}

// Handle look change
function handleLookChange(e) {
    currentLook = e.target.value;
    const description = document.getElementById('lookDescription');
    description.textContent = currentLook === 'handDrawn' 
        ? 'Sketch-like, personal touch' 
        : 'Traditional Mermaid style';
    renderMermaid();
}

// Load example diagrams
function loadExample(type) {
    let code = '';
    
    switch(type) {
        case 'flowchart':
            code = `graph TD
    A[Christmas] -->|Get money| B(Go shopping)
    B --> C{Let me think}
    C -->|One| D[Laptop]
    C -->|Two| E[iPhone]
    C -->|Three| F[fa:fa-car Car]`;
            break;
            
        case 'sequence':
            code = `sequenceDiagram
    participant Alice
    participant Bob
    Alice->>John: Hello John, how are you?
    John-->>Alice: Great!
    Alice-)Bob: How about you?
    Bob--)Alice: Also good!`;
            break;
            
        case 'gantt':
            code = `gantt
    title A Gantt Diagram
    dateFormat  YYYY-MM-DD
    section Section
    A task           :a1, 2024-01-01, 30d
    Another task     :after a1  , 20d
    section Another
    Task in sec      :2024-01-12  , 12d
    another task     : 24d`;
            break;
    }
    
    editor.setValue(code);
}

// Generate diagram using AI
async function generateDiagram() {
    const userInput = document.getElementById('userInput').value;
    const apiKey = document.getElementById('apiKey').value;
    const provider = document.getElementById('provider').value;
    
    if (!userInput.trim()) {
        showToast('Please enter a description for your diagram', 'error');
        return;
    }
    
    if (!apiKey) {
        showToast('Please provide an API key', 'error');
        return;
    }
    
    const button = document.getElementById('generateBtn');
    button.disabled = true;
    button.textContent = 'Generating...';
    
    try {
        const response = await fetch('/api/generate-mermaid', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input: userInput,
                api_key: apiKey,
                provider: provider
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            editor.setValue(data.mermaid_code);
            showToast('Diagram generated successfully!', 'success');
        } else {
            showToast(data.error || 'Failed to generate diagram', 'error');
        }
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
    } finally {
        button.disabled = false;
        button.textContent = 'Generate Diagram';
    }
}

// Validate API key
async function validateApiKey() {
    const apiKey = document.getElementById('apiKey').value;
    const provider = document.getElementById('provider').value;
    const status = document.getElementById('keyStatus');
    
    if (!apiKey || apiKey.length < 10) {
        status.textContent = '';
        status.className = 'key-status';
        return;
    }
    
    try {
        const response = await fetch('/api/validate-key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                api_key: apiKey,
                provider: provider
            })
        });
        
        const data = await response.json();
        
        if (data.valid) {
            status.textContent = '✓';
            status.className = 'key-status valid';
        } else {
            status.textContent = '✗';
            status.className = 'key-status invalid';
        }
    } catch (error) {
        status.textContent = '✗';
        status.className = 'key-status invalid';
    }
}

// Clear key status
function clearKeyStatus() {
    const status = document.getElementById('keyStatus');
    status.textContent = '';
    status.className = 'key-status';
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Copy code to clipboard
async function copyCode() {
    const code = editor.getValue();
    const button = document.getElementById('copyCodeBtn');
    const buttonText = button.querySelector('.copy-text');
    
    try {
        await navigator.clipboard.writeText(code);
        button.classList.add('copied');
        buttonText.textContent = 'Copied!';
        
        setTimeout(() => {
            button.classList.remove('copied');
            buttonText.textContent = 'Copy';
        }, 2000);
    } catch (err) {
        showToast('Failed to copy code', 'error');
    }
}

// Copy diagram as image
async function copyImage() {
    const button = document.getElementById('copyImageBtn');
    const buttonText = button.querySelector('.copy-text');
    const svg = document.querySelector('#mermaidPreview svg');
    
    if (!svg) {
        showToast('No diagram to copy', 'error');
        return;
    }
    
    try {
        // Clone the SVG to avoid modifying the original
        const svgClone = svg.cloneNode(true);
        
        // Get computed styles and embed them
        const styleElement = document.createElement('style');
        const allElements = svgClone.querySelectorAll('*');
        const cssText = Array.from(allElements).map(el => {
            const styles = window.getComputedStyle(el);
            const cssProps = ['fill', 'stroke', 'stroke-width', 'font-family', 'font-size', 'font-weight'];
            const inlineStyles = cssProps.map(prop => `${prop}: ${styles.getPropertyValue(prop)}`).join('; ');
            return el.tagName + ' { ' + inlineStyles + ' }';
        }).join('\n');
        styleElement.textContent = cssText;
        svgClone.insertBefore(styleElement, svgClone.firstChild);
        
        // Get SVG dimensions
        const bbox = svg.getBoundingClientRect();
        svgClone.setAttribute('width', bbox.width);
        svgClone.setAttribute('height', bbox.height);
        
        // Create a data URL from the SVG
        const svgData = new XMLSerializer().serializeToString(svgClone);
        const svgDataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgData);
        
        // Create canvas with high resolution (2x for retina displays)
        const scale = 2;
        const canvas = document.createElement('canvas');
        canvas.width = bbox.width * scale;
        canvas.height = bbox.height * scale;
        const ctx = canvas.getContext('2d');
        
        // Set background based on user preference
        const bgOption = document.getElementById('exportBg').value;
        if (bgOption === 'white') {
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
        // Otherwise keep transparent background
        
        // Create image from SVG data URL
        const img = new Image();
        
        // Set crossOrigin to anonymous to handle CORS
        img.crossOrigin = 'anonymous';
        
        img.onload = async function() {
            // Scale for high resolution
            ctx.scale(scale, scale);
            ctx.drawImage(img, 0, 0, bbox.width, bbox.height);
            
            try {
                // Convert to blob
                canvas.toBlob(async (blob) => {
                    if (blob) {
                        // Try to use the Clipboard API
                        if (navigator.clipboard && window.ClipboardItem) {
                            try {
                                const item = new ClipboardItem({ 'image/png': blob });
                                await navigator.clipboard.write([item]);
                                
                                button.classList.add('copied');
                                buttonText.textContent = 'Copied!';
                                showToast('Diagram copied as high-resolution image', 'success');
                                
                                setTimeout(() => {
                                    button.classList.remove('copied');
                                    buttonText.textContent = 'Copy Image';
                                }, 2000);
                            } catch (clipboardErr) {
                                // Fallback to download
                                downloadImage(blob);
                            }
                        } else {
                            // Fallback: download the image
                            downloadImage(blob);
                        }
                    }
                }, 'image/png', 1.0);
            } catch (err) {
                // If toBlob fails, try alternative method
                try {
                    const dataUrl = canvas.toDataURL('image/png', 1.0);
                    const link = document.createElement('a');
                    link.download = 'mermaid-diagram.png';
                    link.href = dataUrl;
                    link.click();
                    showToast('Downloaded as image (copy not supported)', 'info');
                } catch (dataUrlErr) {
                    showToast('Failed to export image', 'error');
                }
            }
        };
        
        img.onerror = function() {
            showToast('Failed to process diagram image', 'error');
        };
        
        img.src = svgDataUrl;
        
    } catch (err) {
        showToast('Failed to copy image: ' + err.message, 'error');
    }
}

// Helper function to download image
function downloadImage(blob) {
    const link = document.createElement('a');
    link.download = 'mermaid-diagram.png';
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
    showToast('Downloaded as image (copy requires HTTPS)', 'info');
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}