# Sailor UI - User Experience Design

## Vision
Create the most intuitive and delightful Mermaid diagram creation experience that feels like magic.

## User Journey

### 1. **Instant Start** (0-5 seconds)
- Land on a clean, beautiful interface
- See a live diagram already rendered as an example
- One-click to start creating

### 2. **Natural Language Input**
- Large, friendly text area: "Describe what you want to diagram..."
- Real-time AI suggestions as they type
- Smart templates: "Looks like you're creating a flowchart..."

### 3. **Live Preview Magic**
- Split-screen: Natural language → Mermaid code → Live diagram
- Smooth animations as diagram updates
- Instant validation with friendly error hints

### 4. **Smart Assistance**
- AI-powered suggestions: "Add a decision node?"
- Context-aware tools appear when needed
- One-click diagram type switching

### 5. **Beautiful Themes**
- Visual theme picker with live preview
- Custom color palettes
- Export presets (presentation, documentation, dark mode)

### 6. **Collaboration Features**
- Share live diagram with a link
- Real-time collaborative editing
- Version history with visual diff

## Core UI Components

### Main Canvas
```
┌─────────────────────────────────────────────────────────────┐
│  🧜‍♀️ Sailor                                    [Export] [Share] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐ │
│  │ Describe your        │  │                             │ │
│  │ diagram...          │  │      [Live Diagram]         │ │
│  │                     │  │                             │ │
│  │ [AI Assist ✨]      │  │                             │ │
│  └─────────────────────┘  └─────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ graph TD                                             │   │
│  │   A[Start] --> B{Decision}                           │   │
│  │   B -->|Yes| C[Success]                             │   │
│  │   B -->|No| D[Try Again]                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Flowchart] [Sequence] [Class] [State] [ER] [Gantt]       │
└─────────────────────────────────────────────────────────────┘
```

### Key Interactions

1. **Smart Input Box**
   - Placeholder examples that cycle
   - Auto-complete for diagram elements
   - Natural language processing

2. **Live Code Editor**
   - Syntax highlighting
   - Auto-completion
   - Error underlining with fixes

3. **Theme Selector**
   - Visual swatches
   - Instant preview
   - Save custom themes

4. **Export Options**
   - PNG/SVG/PDF
   - Copy to clipboard
   - Direct integration (Notion, Confluence, GitHub)

## Technical Architecture for UX

### Frontend (Svelte)
- **Instant feedback**: WebSocket connection to MCP server
- **Smooth animations**: Svelte transitions
- **Offline capable**: PWA with service workers
- **Responsive**: Works perfectly on mobile

### MCP Server
- **Fast rendering**: Cached diagram rendering
- **Smart suggestions**: AI-powered completions
- **Real-time validation**: Instant feedback

### Performance Goals
- First meaningful paint: < 1 second
- Time to interactive: < 2 seconds
- Diagram update latency: < 100ms
- Export generation: < 2 seconds

## Accessibility
- Full keyboard navigation
- Screen reader support
- High contrast mode
- Configurable font sizes

## Mobile Experience
- Touch-optimized controls
- Pinch to zoom diagrams
- Swipe between views
- Voice input support