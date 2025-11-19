// Sailor Mermaid Diagram Generator Frontend

class SailorApp {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.initializeMermaid();
    }

    initializeElements() {
        this.elements = {
            description: document.getElementById('description'),
            mermaidCode: document.getElementById('mermaidCode'),
            diagramType: document.getElementById('diagramType'),
            theme: document.getElementById('theme'),
            generateBtn: document.getElementById('generateBtn'),
            validateBtn: document.getElementById('validateBtn'),
            renderBtn: document.getElementById('renderBtn'),
            preview: document.getElementById('preview'),
            validationResults: document.getElementById('validationResults'),
            darkModeToggle: document.getElementById('darkModeToggle'),
            configToggle: document.getElementById('configToggle'),
            configPanel: document.getElementById('configPanel'),
            curveStyle: document.getElementById('curveStyle'),
            flowDirection: document.getElementById('flowDirection'),
            nodeSpacing: document.getElementById('nodeSpacing'),
            rankSpacing: document.getElementById('rankSpacing'),
            useMaxWidth: document.getElementById('useMaxWidth'),
            applyConfig: document.getElementById('applyConfig'),
            resetConfig: document.getElementById('resetConfig')
        };
        
        // Default Mermaid config
        this.defaultConfig = {
            theme: 'default',
            themeVariables: {
                primaryColor: '#3498db',
                primaryTextColor: '#fff',
                primaryBorderColor: '#2980b9',
                lineColor: '#5D8AA8',
                secondaryColor: '#ecf0f1',
                tertiaryColor: '#95a5a6'
            },
            flowchart: {
                curve: 'basis',
                nodeSpacing: 50,
                rankSpacing: 50,
                useMaxWidth: true
            },
            securityLevel: 'loose'
        };
        
        this.currentConfig = JSON.parse(JSON.stringify(this.defaultConfig));
    }

    bindEvents() {
        this.elements.generateBtn.addEventListener('click', () => this.generateDiagram());
        this.elements.validateBtn.addEventListener('click', () => this.validateDiagram());
        this.elements.renderBtn.addEventListener('click', () => this.renderDiagram());
        this.elements.mermaidCode.addEventListener('input', () => this.debouncePreview());
        this.elements.theme.addEventListener('change', () => this.updateTheme());
        this.elements.diagramType.addEventListener('change', () => this.loadTemplate());
        if (this.elements.darkModeToggle) {
            this.elements.darkModeToggle.addEventListener('click', () => this.toggleDarkMode());
        }
        if (this.elements.configToggle) {
            this.elements.configToggle.addEventListener('click', () => this.toggleConfigPanel());
        }
        
        // Config panel events
        if (this.elements.applyConfig) {
            this.elements.applyConfig.addEventListener('click', () => this.applyConfiguration());
        }
        if (this.elements.resetConfig) {
            this.elements.resetConfig.addEventListener('click', () => this.resetConfiguration());
        }
        if (this.elements.nodeSpacing) {
            this.elements.nodeSpacing.addEventListener('input', (e) => {
                const valueSpan = document.getElementById('nodeSpacingValue');
                if (valueSpan) valueSpan.textContent = e.target.value;
            });
        }
        if (this.elements.rankSpacing) {
            this.elements.rankSpacing.addEventListener('input', (e) => {
                const valueSpan = document.getElementById('rankSpacingValue');
                if (valueSpan) valueSpan.textContent = e.target.value;
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to validate
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.validateDiagram();
        }
        
        // Ctrl/Cmd + G to generate
        if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
            e.preventDefault();
            this.elements.description.focus();
        }
        
        // Ctrl/Cmd + D for dark mode
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            this.toggleDarkMode();
        }
    }

    initializeMermaid() {
        // Check for saved dark mode preference
        const darkMode = localStorage.getItem('darkMode') === 'true';
        if (darkMode) {
            document.body.classList.add('dark-mode');
        }
        
        mermaid.initialize({
            startOnLoad: false,
            theme: darkMode ? 'dark' : 'default',
            securityLevel: 'loose'
        });
        this.renderPreview();
    }

    updateTheme() {
        const theme = this.elements.theme.value;
        mermaid.initialize({
            startOnLoad: false,
            theme: theme,
            securityLevel: 'loose'
        });
        this.renderPreview();
    }

    loadTemplate() {
        const diagramType = this.elements.diagramType.value;
        const template = this.getTemplateForType(diagramType);
        
        // Only load template if the code area is empty or contains another template
        const currentCode = this.elements.mermaidCode.value.trim();
        if (!currentCode || this.isTemplate(currentCode)) {
            this.elements.mermaidCode.value = template;
            this.renderPreview();
        }
    }

    isTemplate(code) {
        // Check if the current code exactly matches one of our templates
        const templates = Object.values(this.getAllTemplates());
        return templates.some(template => code.trim() === template.trim());
    }
    
    getAllTemplates() {
        return {
            flowchart: this.getTemplateForType('flowchart'),
            sequence: this.getTemplateForType('sequence'),
            class: this.getTemplateForType('class'),
            state: this.getTemplateForType('state'),
            gantt: this.getTemplateForType('gantt'),
            pie: this.getTemplateForType('pie'),
            erDiagram: this.getTemplateForType('erDiagram')
        };
    }

    getTemplateForType(type) {
        const templates = {
            flowchart: `flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E`,
            
            sequence: `sequenceDiagram
    participant Alice
    participant Bob
    Alice->>Bob: Hello Bob!
    Bob-->>Alice: Hi Alice!
    Alice->>Bob: How are you?
    Bob-->>Alice: I'm good, thanks!`,
            
            class: `classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +String breed
        +bark()
    }
    class Cat {
        +String color
        +meow()
    }
    Animal <|-- Dog
    Animal <|-- Cat`,
            
            state: `stateDiagram-v2
    [*] --> State1
    State1 --> State2 : Transition
    State2 --> State3 : Event
    State3 --> State1 : Reset
    State3 --> [*]`,
            
            gantt: `gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
    Task 1           :a1, 2024-01-01, 30d
    Task 2           :after a1, 20d
    section Phase 2
    Task 3           :2024-02-01, 12d
    Task 4           :24d`,
            
            pie: `pie title Distribution
    "Category 1" : 30
    "Category 2" : 20
    "Category 3" : 25
    "Category 4" : 25`,
            
            erDiagram: `erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINEITEM : contains
    CUSTOMER {
        string name
        string customerNumber PK
        string email
        string phone
    }
    ORDER {
        int orderNumber PK
        string customerNumber FK
        date orderDate
        string status
    }
    LINEITEM {
        int orderNumber FK
        int lineNumber PK
        int quantity
        float price
    }`
        };
        
        return templates[type] || templates.flowchart;
    }
    
    toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        
        // Save preference
        localStorage.setItem('darkMode', isDarkMode);
        
        // Update Mermaid theme
        const theme = this.elements.theme.value;
        mermaid.initialize({
            startOnLoad: false,
            theme: isDarkMode ? 'dark' : theme,
            securityLevel: 'loose'
        });
        
        // Re-render preview
        this.renderPreview();
    }
    
    toggleConfigPanel() {
        this.elements.configPanel.classList.toggle('active');
    }
    
    applyConfiguration() {
        // Update config based on form values
        this.currentConfig.flowchart.curve = this.elements.curveStyle.value;
        this.currentConfig.flowchart.nodeSpacing = parseInt(this.elements.nodeSpacing.value);
        this.currentConfig.flowchart.rankSpacing = parseInt(this.elements.rankSpacing.value);
        this.currentConfig.flowchart.useMaxWidth = this.elements.useMaxWidth.checked;
        
        // Update flow direction in code if it's a flowchart
        if (this.elements.diagramType.value === 'flowchart') {
            const direction = this.elements.flowDirection.value;
            const code = this.elements.mermaidCode.value;
            const updatedCode = code.replace(/flowchart\s+\w+/, `flowchart ${direction}`);
            if (updatedCode !== code) {
                this.elements.mermaidCode.value = updatedCode;
            }
        }
        
        // Reinitialize mermaid with new config
        const isDarkMode = document.body.classList.contains('dark-mode');
        const theme = this.elements.theme.value;
        
        mermaid.initialize({
            ...this.currentConfig,
            theme: isDarkMode ? 'dark' : theme
        });
        
        this.renderPreview();
        this.showValidationMessage('Configuration applied successfully!', 'success');
    }
    
    resetConfiguration() {
        // Reset to defaults
        this.currentConfig = JSON.parse(JSON.stringify(this.defaultConfig));
        
        // Reset form values
        this.elements.curveStyle.value = 'basis';
        this.elements.flowDirection.value = 'TD';
        this.elements.nodeSpacing.value = '50';
        this.elements.rankSpacing.value = '50';
        this.elements.useMaxWidth.checked = true;
        document.getElementById('nodeSpacingValue').textContent = '50';
        document.getElementById('rankSpacingValue').textContent = '50';
        
        // Reinitialize mermaid
        const isDarkMode = document.body.classList.contains('dark-mode');
        const theme = this.elements.theme.value;
        
        mermaid.initialize({
            ...this.currentConfig,
            theme: isDarkMode ? 'dark' : theme
        });
        
        this.renderPreview();
        this.showValidationMessage('Configuration reset to defaults!', 'success');
    }

    async generateDiagram() {
        const description = this.elements.description.value.trim();
        const diagramType = this.elements.diagramType.value;
        const theme = this.elements.theme.value;

        if (!description) {
            this.showValidationMessage('Please enter a description.', 'error');
            return;
        }

        this.setLoading(this.elements.generateBtn, true);
        this.clearValidation();

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    description: description,
                    type: diagramType,
                    theme: theme
                })
            });

            const result = await response.json();

            if (result.success) {
                this.elements.mermaidCode.value = result.code;
                this.renderPreview();
                this.showValidationMessage('Diagram generated successfully!', 'success');
            } else {
                const errors = result.errors.join(', ');
                this.showValidationMessage(`Generation failed: ${errors}`, 'error');
            }
        } catch (error) {
            this.showValidationMessage(`Error: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.elements.generateBtn, false);
        }
    }

    async validateDiagram() {
        const code = this.elements.mermaidCode.value.trim();

        if (!code) {
            this.showValidationMessage('Please enter Mermaid code to validate.', 'error');
            return;
        }

        this.setLoading(this.elements.validateBtn, true);
        this.clearValidation();

        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code: code })
            });

            const result = await response.json();

            if (result.valid) {
                this.showValidationMessage('Code is valid!', 'success');
            } else {
                result.errors.forEach(error => {
                    this.showValidationMessage(error, 'error');
                });
            }

            if (result.warnings && result.warnings.length > 0) {
                result.warnings.forEach(warning => {
                    this.showValidationMessage(warning, 'warning');
                });
            }
        } catch (error) {
            this.showValidationMessage(`Validation error: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.elements.validateBtn, false);
        }
    }

    async renderDiagram() {
        const code = this.elements.mermaidCode.value.trim();
        const theme = this.elements.theme.value;

        if (!code) {
            this.showValidationMessage('Please enter Mermaid code to render.', 'error');
            return;
        }

        this.setLoading(this.elements.renderBtn, true);
        this.clearValidation();

        try {
            const response = await fetch('/api/render', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: code,
                    theme: theme,
                    format: 'png'
                })
            });

            const result = await response.json();

            if (result.success && result.data) {
                // Create download link for rendered image
                const link = document.createElement('a');
                link.href = `data:image/png;base64,${result.data}`;
                link.download = 'diagram.png';
                link.click();
                this.showValidationMessage('Diagram rendered and downloaded!', 'success');
            } else {
                this.showValidationMessage(`Render failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showValidationMessage(`Render error: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.elements.renderBtn, false);
        }
    }

    renderPreview() {
        const code = this.elements.mermaidCode.value.trim();
        
        if (!code) {
            this.elements.preview.innerHTML = '<div class="empty">Enter Mermaid code to see preview</div>';
            return;
        }

        try {
            // Clear previous content
            this.elements.preview.innerHTML = '';
            
            // Create container for mermaid
            const container = document.createElement('div');
            container.className = 'mermaid';
            container.textContent = code;
            this.elements.preview.appendChild(container);

            // Render with mermaid
            mermaid.init(undefined, container);
        } catch (error) {
            this.elements.preview.innerHTML = `<div class="validation-error">Preview error: ${error.message}</div>`;
        }
    }

    debouncePreview() {
        clearTimeout(this.previewTimeout);
        this.previewTimeout = setTimeout(() => {
            this.renderPreview();
        }, 500);
    }

    showValidationMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `validation-message validation-${type}`;
        
        // Create message content without emoji (CSS handles it)
        const textSpan = document.createElement('span');
        textSpan.textContent = message;
        messageDiv.appendChild(textSpan);
        
        this.elements.validationResults.appendChild(messageDiv);
        
        // Auto-clear success messages after 5 seconds with fade out
        if (type === 'success') {
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.style.opacity = '0';
                    messageDiv.style.transform = 'translateX(20px)';
                    setTimeout(() => {
                        if (messageDiv.parentNode) {
                            messageDiv.parentNode.removeChild(messageDiv);
                        }
                    }, 300);
                }
            }, 5000);
        }
    }

    clearValidation() {
        this.elements.validationResults.innerHTML = '';
    }

    setLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = '<span class="spinner"></span> Loading...';
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText;
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new SailorApp();
    window.sailorApp = app; // Make app available globally for debugging
    
    // Load initial template
    app.loadTemplate();
});