---
layout: default
title: "Sailor Showcase - Screenshots of Every Feature"
description: "See Sailor in action: flowcharts, sequence diagrams, Gantt charts, four themes, hand-drawn mode, direction control, AI generation, and responsive mobile layout."
image:
  path: /sailor/screenshots/07-hand-drawn-look.png
  alt: Sailor editor showing a hand-drawn flowchart with Forest theme
---

# Sailor Showcase

See what Sailor can do. Every screenshot below was captured from a live instance of the Sailor web UI.

---

## The Editor

Sailor gives you a split-pane interface: a code editor on the left with syntax highlighting (CodeMirror), a live preview in the center, and style controls on the right. The bottom panel lets you describe diagrams in plain English and generate them with AI.

<div class="screenshot-container">
  <img src="screenshots/01-default-view.png" alt="Sailor default view showing the split-pane editor with code, preview, and style controls" loading="lazy">
  <p class="screenshot-caption">The main interface with a simple flowchart loaded</p>
</div>

---

## Diagram Types

Sailor supports all major Mermaid diagram types out of the box. Click an example button and the code + preview update instantly.

### Flowcharts

Decision trees, process flows, and workflows with branching logic. Supports rectangles, rounded boxes, diamonds, and labeled edges.

<div class="screenshot-container">
  <img src="screenshots/02-flowchart-example.png" alt="Flowchart example showing a Christmas shopping decision tree" loading="lazy">
  <p class="screenshot-caption">Flowchart with decision nodes, labeled edges, and multiple branches</p>
</div>

### Sequence Diagrams

Model interactions between participants over time. Supports synchronous calls, async responses, and different arrow styles.

<div class="screenshot-container">
  <img src="screenshots/03-sequence-diagram.png" alt="Sequence diagram showing Alice, Bob, and John communicating" loading="lazy">
  <p class="screenshot-caption">Sequence diagram with multiple participants and message types</p>
</div>

### Gantt Charts

Plan and visualize project timelines with tasks, dependencies, and sections.

<div class="screenshot-container">
  <img src="screenshots/04-gantt-chart.png" alt="Gantt chart showing project timeline with multiple sections" loading="lazy">
  <p class="screenshot-caption">Gantt chart with task dependencies and date-based scheduling</p>
</div>

---

## Themes

Switch between four built-in Mermaid themes to match your project's style. The preview background adapts automatically.

### Dark Theme

High-contrast diagrams on a dark background, ideal for dark-mode presentations.

<div class="screenshot-container">
  <img src="screenshots/05-dark-theme.png" alt="Dark theme with white nodes on dark background" loading="lazy">
  <p class="screenshot-caption">Dark theme - clean, high-contrast rendering</p>
</div>

### Forest Theme

A nature-inspired green palette with warm tones.

<div class="screenshot-container">
  <img src="screenshots/06-forest-theme.png" alt="Forest theme with green-tinted nodes" loading="lazy">
  <p class="screenshot-caption">Forest theme - green palette for a natural feel</p>
</div>

---

## Hand-Drawn Look

Toggle between Classic and Hand-Drawn rendering. Hand-Drawn mode gives diagrams a sketch-like, whiteboard aesthetic.

<div class="screenshot-container">
  <img src="screenshots/07-hand-drawn-look.png" alt="Hand-drawn rendering style with sketchy edges and fills" loading="lazy">
  <p class="screenshot-caption">Hand-Drawn look combined with Forest theme for a whiteboard feel</p>
</div>

---

## Direction Control

Change the flow direction of your diagrams: Top-to-Bottom, Bottom-to-Top, Left-to-Right, or Right-to-Left. The code updates automatically.

<div class="screenshot-container">
  <img src="screenshots/08-left-to-right.png" alt="Left-to-right flowchart layout" loading="lazy">
  <p class="screenshot-caption">Left-to-Right layout - great for horizontal process flows</p>
</div>

---

## Responsive Design

Sailor works on screens of every size. On mobile, panels stack vertically and controls reflow into a compact grid.

<div class="screenshot-container screenshot-mobile">
  <img src="screenshots/09-mobile-responsive.png" alt="Sailor on a mobile viewport with stacked panels" loading="lazy">
  <p class="screenshot-caption">Mobile view (375px) - fully responsive layout</p>
</div>

---

## AI-Powered Generation

Type a plain-English description in the bottom panel, connect your OpenAI or Anthropic API key, and click **Generate Diagram**. Sailor sends your description to the AI and renders the result instantly.

Supported providers:
- **OpenAI** (GPT-4)
- **Anthropic** (Claude 3.5 Sonnet)

---

## MCP Server Integration

Beyond the web UI, Sailor runs as an MCP (Model Context Protocol) server that integrates directly with Claude Desktop. This gives you 11 tools for diagram generation, validation, rendering, and analysis -- all through natural language conversation.

| Tool | Description |
|------|-------------|
| `validate_and_render_mermaid` | Validate and render Mermaid code to PNG |
| `get_diagram` | Retrieve a rendered diagram by file ID |
| `request_mermaid_generation` | Generate Mermaid code from a description |
| `get_mermaid_examples` | Browse example diagrams |
| `get_diagram_template` | Get customizable starter templates |
| `get_syntax_help` | Syntax reference for any diagram type |
| `analyze_diagram_code` | Analyze code and suggest improvements |
| `suggest_diagram_improvements` | Get targeted improvement suggestions |
| `health_check` | Check server health |
| `server_status` | Full server status report |

---

## Additional Features

- **Copy Code** -- one-click copy of Mermaid source to clipboard
- **Copy Image** -- export the rendered diagram as a high-resolution PNG
- **Export Background** -- choose transparent or white background for exports
- **Real-time Preview** -- diagrams re-render as you type with 500ms debounce
- **API Key Validation** -- keys are verified against the provider before use
- **Rate Limiting** -- built-in protection against API abuse
- **Docker Deployment** -- ship as a container with `docker-compose up`

---

<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #0066cc 0%, #1e90ff 100%); border-radius: 8px; color: white; margin: 2rem 0;">
  <h2 style="color: white; border: none; margin-bottom: 1rem;">Ready to try it?</h2>
  <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">Get Sailor running in minutes.</p>
  <a href="setup-guide" style="display: inline-block; background: white; color: #0066cc; padding: 0.75rem 2rem; border-radius: 4px; text-decoration: none; font-weight: bold;">
    Setup Guide
  </a>
</div>
