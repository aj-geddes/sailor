"""MCP Server implementation for Sailor Site using FastMCP

This server can be deployed remotely (e.g., Railway) and includes:
- Environment-based configuration (PORT, HOST)
- Health check endpoint for load balancers
- Rate limiting to prevent abuse
- Request tracking and metrics
"""
import asyncio
import logging
import os
import time
import uuid
import tempfile
import threading
from collections import defaultdict
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json

from fastmcp import FastMCP

from .validators import MermaidValidator
from .renderer import MermaidRenderer, MermaidConfig, get_renderer, cleanup_renderer
from .prompts import PromptGenerator
from .mermaid_resources import MermaidResources
from .logging_config import get_logger

# Get logger
logger = get_logger(__name__)

# Environment configuration
PORT = int(os.environ.get("PORT", os.environ.get("MCP_PORT", "8000")))
HOST = os.environ.get("HOST", os.environ.get("MCP_HOST", "0.0.0.0"))
LOG_LEVEL = os.environ.get("SAILOR_LOG_LEVEL", "INFO")

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "100"))  # requests per window
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))  # window in seconds
RATE_LIMIT_RENDER = int(os.environ.get("RATE_LIMIT_RENDER", "20"))  # render requests per window (more expensive)

# Create FastMCP server instance
mcp = FastMCP("sailor-mermaid", version="2.0.0")


# ==================== RATE LIMITING ====================

class RateLimiter:
    """Simple in-memory rate limiter for abuse protection"""

    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.render_requests: Dict[str, List[float]] = defaultdict(list)

    def _clean_old_requests(self, requests: List[float], window: int) -> List[float]:
        """Remove requests outside the current window"""
        cutoff = time.time() - window
        return [r for r in requests if r > cutoff]

    def check_rate_limit(self, client_id: str, is_render: bool = False) -> tuple[bool, str]:
        """
        Check if request is within rate limits.
        Returns (allowed, message)
        """
        now = time.time()

        # Clean and check general rate limit
        self.requests[client_id] = self._clean_old_requests(
            self.requests[client_id], RATE_LIMIT_WINDOW
        )

        if len(self.requests[client_id]) >= RATE_LIMIT_REQUESTS:
            return False, f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s"

        # For render requests, also check render-specific limit
        if is_render:
            self.render_requests[client_id] = self._clean_old_requests(
                self.render_requests[client_id], RATE_LIMIT_WINDOW
            )

            if len(self.render_requests[client_id]) >= RATE_LIMIT_RENDER:
                return False, f"Render rate limit exceeded. Max {RATE_LIMIT_RENDER} renders per {RATE_LIMIT_WINDOW}s"

            self.render_requests[client_id].append(now)

        self.requests[client_id].append(now)
        return True, "OK"

    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics"""
        now = time.time()
        active_clients = 0
        total_requests = 0

        for client_id, requests in self.requests.items():
            recent = [r for r in requests if r > now - RATE_LIMIT_WINDOW]
            if recent:
                active_clients += 1
                total_requests += len(recent)

        return {
            "active_clients": active_clients,
            "total_requests_in_window": total_requests,
            "window_seconds": RATE_LIMIT_WINDOW,
            "limit_per_client": RATE_LIMIT_REQUESTS,
            "render_limit_per_client": RATE_LIMIT_RENDER,
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


# ==================== TEMP FILE STORE (One-Time Downloads) ====================

@dataclass
class TempFile:
    """Metadata for a temporary download file"""
    file_path: str
    created_at: float
    file_format: str
    downloaded: bool = False


class TempFileStore:
    """
    Manages temporary files for one-time downloads.
    - Files are deleted after first download
    - Files expire after 30 minutes
    - Automatic cleanup runs periodically
    """

    EXPIRY_SECONDS = 30 * 60  # 30 minutes
    CLEANUP_INTERVAL = 5 * 60  # Run cleanup every 5 minutes

    def __init__(self):
        self.files: Dict[str, TempFile] = {}
        self.lock = threading.Lock()
        self.temp_dir = tempfile.mkdtemp(prefix="sailor_")
        self._start_cleanup_thread()
        logger.info(f"TempFileStore initialized at {self.temp_dir}")

    def _start_cleanup_thread(self):
        """Start background thread to clean up expired files"""
        def cleanup_loop():
            while True:
                time.sleep(self.CLEANUP_INTERVAL)
                self._cleanup_expired()

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def _cleanup_expired(self):
        """Remove expired files"""
        now = time.time()
        expired = []

        with self.lock:
            for file_id, temp_file in self.files.items():
                if now - temp_file.created_at > self.EXPIRY_SECONDS:
                    expired.append(file_id)

            for file_id in expired:
                self._delete_file(file_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired temp files")

    def _delete_file(self, file_id: str):
        """Delete a file (must hold lock)"""
        if file_id in self.files:
            temp_file = self.files[file_id]
            try:
                if os.path.exists(temp_file.file_path):
                    os.remove(temp_file.file_path)
            except Exception as e:
                logger.error(f"Failed to delete temp file {file_id}: {e}")
            del self.files[file_id]

    def store(self, data: bytes, file_format: str = "png") -> str:
        """
        Store file data and return a unique download ID.
        Returns the file_id (UUID) for the download URL.
        """
        file_id = str(uuid.uuid4())
        file_path = os.path.join(self.temp_dir, f"{file_id}.{file_format}")

        with open(file_path, 'wb') as f:
            f.write(data)

        with self.lock:
            self.files[file_id] = TempFile(
                file_path=file_path,
                created_at=time.time(),
                file_format=file_format
            )

        logger.info(f"Stored temp file {file_id} ({len(data)} bytes)")
        return file_id

    def retrieve(self, file_id: str) -> Optional[tuple[bytes, str]]:
        """
        Retrieve file data by ID. Returns (data, format) or None.
        File is deleted after retrieval (one-time download).
        """
        with self.lock:
            if file_id not in self.files:
                return None

            temp_file = self.files[file_id]

            # Check if expired
            if time.time() - temp_file.created_at > self.EXPIRY_SECONDS:
                self._delete_file(file_id)
                return None

            # Check if already downloaded
            if temp_file.downloaded:
                self._delete_file(file_id)
                return None

            # Read file data
            try:
                with open(temp_file.file_path, 'rb') as f:
                    data = f.read()
                file_format = temp_file.file_format

                # Mark as downloaded and delete
                self._delete_file(file_id)

                logger.info(f"Retrieved and deleted temp file {file_id}")
                return data, file_format
            except Exception as e:
                logger.error(f"Failed to retrieve temp file {file_id}: {e}")
                self._delete_file(file_id)
                return None

    def get_stats(self) -> Dict[str, Any]:
        """Get current store statistics"""
        with self.lock:
            return {
                "active_files": len(self.files),
                "temp_directory": self.temp_dir,
                "expiry_minutes": self.EXPIRY_SECONDS // 60,
            }


# Global temp file store instance
temp_file_store = TempFileStore()


# Request metrics
metrics = {
    "total_requests": 0,
    "successful_renders": 0,
    "failed_renders": 0,
    "rate_limited": 0,
    "start_time": time.time(),
}

# Global resources
resources = MermaidResources()
renderer = None


# ==================== CUSTOM HTTP ROUTES ====================

from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse


@mcp.custom_route("/download/{file_id}.{format}", methods=["GET"])
async def download_file(request: Request) -> Response:
    """
    One-time download endpoint for rendered diagrams.
    Files are deleted after first download or after 30 minutes.
    """
    file_id = request.path_params.get("file_id", "")
    file_format = request.path_params.get("format", "png")

    # Validate file_id is a valid UUID format
    try:
        uuid.UUID(file_id)
    except ValueError:
        return PlainTextResponse("Invalid file ID", status_code=400)

    # Retrieve and delete file (one-time download)
    result = temp_file_store.retrieve(file_id)

    if result is None:
        return PlainTextResponse(
            "File not found, expired, or already downloaded",
            status_code=404
        )

    data, stored_format = result

    # Set appropriate content type
    content_types = {
        "png": "image/png",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
    }
    content_type = content_types.get(stored_format, "application/octet-stream")

    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="diagram.{stored_format}"',
            "Cache-Control": "no-store, no-cache, must-revalidate",
        }
    )


# ==================== TOOLS ====================

# Tool: Health Check
@mcp.tool(description="Check server health and get status information")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for load balancers and monitoring"""
    global renderer

    uptime = time.time() - metrics["start_time"]

    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": round(uptime, 2),
        "metrics": {
            "total_requests": metrics["total_requests"],
            "successful_renders": metrics["successful_renders"],
            "failed_renders": metrics["failed_renders"],
            "rate_limited": metrics["rate_limited"],
        },
        "rate_limiter": rate_limiter.get_stats(),
        "temp_file_store": temp_file_store.get_stats(),
        "renderer_initialized": renderer is not None,
        "environment": {
            "host": HOST,
            "port": PORT,
        }
    }

    return health_status


# Tool: Server Status (alias for external monitoring)
@mcp.tool(description="Get detailed server status and metrics")
async def server_status() -> Dict[str, Any]:
    """Detailed server status for monitoring dashboards"""
    return await health_check()


# Tool: Request Mermaid Generation
@mcp.tool(description="Request the calling LLM to generate Mermaid code based on requirements")
async def request_mermaid_generation(
    description: str,
    diagram_type: str = "flowchart",
    requirements: List[str] = None,
    style: Dict[str, str] = None
) -> str:
    """Handle request for Mermaid generation"""
    requirements = requirements or []
    style = style or {}

    # Build the request for the calling LLM
    prompt = f"""Please generate Mermaid diagram code for the following request:

Description: {description}
Diagram Type: {diagram_type}
"""

    if requirements:
        prompt += f"\nSpecific Requirements:\n" + "\n".join(f"- {req}" for req in requirements)

    if style:
        prompt += f"\n\nStyle Preferences:\n"
        for key, value in style.items():
            prompt += f"- {key}: {value}\n"

    # Add guidelines
    prompt += f"""

Guidelines for {diagram_type} diagrams:
- Use clear, descriptive labels
- Ensure proper syntax for {diagram_type}
- Include appropriate connections/relationships
- For flowcharts/graphs, specify direction (TD, LR, etc.)
- Keep the diagram well-organized and readable

Please respond with ONLY the Mermaid code, no explanations or markdown blocks."""

    # Add example
    examples = _get_example_code()
    if diagram_type in examples:
        prompt += f"\n\nExample {diagram_type}:\n{examples[diagram_type]}"

    return prompt


# Tool: Validate and Render Mermaid
@mcp.tool(description="Validate Mermaid code and render it as an image if valid")
async def validate_and_render_mermaid(
    code: str,
    fix_errors: bool = True,
    style: Dict[str, str] = None,
    format: str = "png",
    client_id: str = "default",
    output_path: str = None
) -> Dict[str, Any]:
    """Handle validation and rendering of Mermaid code"""
    global renderer

    # Update metrics
    metrics["total_requests"] += 1

    # Check rate limit (render is expensive)
    allowed, message = rate_limiter.check_rate_limit(client_id, is_render=True)
    if not allowed:
        metrics["rate_limited"] += 1
        logger.warning(f"Rate limit exceeded for client {client_id}")
        return {
            "error": message,
            "rate_limited": True,
            "retry_after_seconds": RATE_LIMIT_WINDOW
        }

    code = code.strip()
    style = style or {}

    # Remove markdown code blocks if present
    if code.startswith('```'):
        lines = code.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1] == '```':
            lines = lines[:-1]
        code = '\n'.join(lines)

    # Validate the code
    validation = MermaidValidator.validate(code)

    if not validation['valid'] and fix_errors:
        # Attempt to fix common issues
        code = MermaidValidator.fix_common_errors(code)
        validation = MermaidValidator.validate(code)

    if not validation['valid']:
        error_msg = "## Mermaid Code Validation Failed\n\n"
        error_msg += "### Errors:\n" + "\n".join(f"- {e}" for e in validation['errors'])
        if validation['warnings']:
            error_msg += "\n\n### Warnings:\n" + "\n".join(f"- {w}" for w in validation['warnings'])
        error_msg += f"\n\n### Code provided:\n```mermaid\n{code}\n```"

        return {"error": error_msg, "valid": False}

    # Create config from style
    config = MermaidConfig(
        theme=style.get('theme', 'default'),
        look=style.get('look', 'classic'),
        background=style.get('background', 'transparent')
    )

    # Render the diagram
    try:
        global renderer
        if not renderer:
            logger.info("Initializing renderer on first use...")
            renderer = await get_renderer()

        images = await renderer.render(code, config, format)

        # Update success metrics
        metrics["successful_renders"] += 1

        import base64

        saved_files = {}
        download_urls = {}

        # Get base URL for download links (for remote deployment)
        base_url = os.environ.get("SAILOR_BASE_URL", "").rstrip("/")

        for img_format, img_data in images.items():
            decoded_data = base64.b64decode(img_data)

            # If output_path provided, try to save locally
            if output_path:
                if img_format == "png":
                    file_path = output_path if output_path.endswith('.png') else f"{output_path}.png"
                elif img_format == "svg":
                    file_path = output_path.replace('.png', '.svg') if output_path.endswith('.png') else f"{output_path}.svg"
                else:
                    file_path = f"{output_path}.{img_format}"

                try:
                    with open(file_path, 'wb') as f:
                        f.write(decoded_data)
                    saved_files[img_format] = file_path
                    logger.info(f"Saved {img_format} to {file_path}")
                    continue  # Successfully saved locally, skip temp store
                except Exception as e:
                    logger.warning(f"Could not save to {file_path}: {e} - using temp download instead")

            # Store in temp file store and generate download URL
            file_id = temp_file_store.store(decoded_data, img_format)
            if base_url:
                download_urls[img_format] = f"{base_url}/download/{file_id}.{img_format}"
            else:
                download_urls[img_format] = f"/download/{file_id}.{img_format}"
            logger.info(f"Created one-time download URL for {img_format}: {file_id}")

        # Create response
        result = {
            "valid": True,
            "diagram_type": validation['diagram_type'],
            "line_count": validation['line_count'],
            "theme": config.theme,
            "style": config.look,
            "background": config.background,
        }

        # Add file paths and/or download URLs
        if saved_files:
            result["saved_files"] = saved_files
        if download_urls:
            result["download_urls"] = download_urls
            result["download_note"] = "One-time download links. URLs expire after 30 minutes or first download."

        if validation['warnings']:
            result["warnings"] = validation['warnings']

        return result

    except Exception as e:
        # Update failure metrics
        metrics["failed_renders"] += 1
        logger.error(f"Rendering error: {e}", exc_info=True)
        return {
            "error": f"Rendering failed: {str(e)}\n\nCode was valid but could not be rendered.",
            "valid": True,
            "rendering_failed": True
        }


# Tool: Get Mermaid Examples
@mcp.tool(description="Get examples of different Mermaid diagram types")
async def get_mermaid_examples(
    diagram_type: str = "all",
    complexity: str = "all",
    search_keywords: str = ""
) -> Dict[str, Any]:
    """Handle request for examples using comprehensive resource library"""

    # Use comprehensive resource library
    if search_keywords:
        examples = resources.search_examples(search_keywords)
        if not examples:
            return {"error": f"No examples found for keywords: {search_keywords}"}
    elif complexity != 'all':
        examples = resources.get_examples_by_complexity(complexity)
        if diagram_type != 'all':
            examples = [ex for ex in examples if ex.category == diagram_type]
    elif diagram_type == 'all':
        examples = []
        for category in resources.examples.keys():
            examples.extend(resources.get_examples_by_category(category))
    else:
        examples = resources.get_examples_by_category(diagram_type)

    if not examples:
        return {"error": f"No examples found for {diagram_type} with complexity {complexity}"}

    # Build comprehensive response
    result = {
        "diagram_type": diagram_type,
        "complexity": complexity,
        "search_keywords": search_keywords,
        "count": len(examples),
        "examples": []
    }

    for example in examples[:5]:  # Limit to 5 examples
        result["examples"].append({
            "name": example.name,
            "category": example.category,
            "complexity": example.complexity,
            "description": example.description,
            "features": example.features,
            "use_cases": example.use_cases,
            "code": example.code
        })

    return result


# Tool: Get Diagram Template
@mcp.tool(description="Get a customizable template for quick diagram generation")
async def get_diagram_template(
    template_name: str,
    diagram_type: str = "flowchart",
    fill_variables: Dict[str, str] = None
) -> Dict[str, Any]:
    """Handle request for diagram templates"""
    fill_variables = fill_variables or {}

    # Get template from resources
    template = resources.get_template(template_name, diagram_type)

    if not template:
        # List available templates
        available = []
        for category, templates in resources.templates.items():
            for tmpl in templates:
                available.append(f"{category}: {tmpl.name}")

        return {
            "error": f"Template '{template_name}' not found",
            "available_templates": available
        }

    result = {
        "name": template.name,
        "description": template.description,
        "variables": template.variables,
        "template": template.template
    }

    if fill_variables:
        # Fill template with provided variables
        filled_code = resources.fill_template(template, fill_variables)
        result["filled_code"] = filled_code
    elif template.example_vars:
        # Show template with example variables
        example_code = resources.fill_template(template, template.example_vars)
        result["example_code"] = example_code
        result["example_vars"] = template.example_vars

    return result


# Tool: Get Syntax Help
@mcp.tool(description="Get syntax reference and help for Mermaid diagram types")
async def get_syntax_help(
    diagram_type: str,
    topic: str = None,
    generate_reference: bool = False
) -> Dict[str, Any]:
    """Handle syntax help requests"""

    if generate_reference:
        # Generate complete quick reference
        reference = resources.generate_quick_reference(diagram_type)
        return {"diagram_type": diagram_type, "reference": reference}

    # Get specific syntax help
    syntax_help = resources.get_syntax_help(diagram_type, topic)

    if not syntax_help:
        return {
            "error": f"No syntax help available for {diagram_type}" +
                    (f" topic '{topic}'" if topic else "")
        }

    result = {
        "diagram_type": diagram_type,
        "topic": topic,
        "syntax": syntax_help
    }

    # Add best practices
    practices = resources.get_best_practices(diagram_type)
    if practices:
        result["best_practices"] = practices[:5]  # Limit to 5 practices

    return result


# Tool: Analyze Diagram Code
@mcp.tool(description="Analyze Mermaid code and provide improvement suggestions")
async def analyze_diagram_code(
    code: str,
    focus_areas: List[str] = None
) -> Dict[str, Any]:
    """Analyze Mermaid code and provide suggestions"""
    focus_areas = focus_areas or ['syntax', 'best_practices']

    # Validate syntax first
    validation = MermaidValidator.validate(code)

    result = {
        "is_valid": validation.get('valid', False),
        "diagram_type": validation.get('diagram_type', 'unknown'),
        "line_count": validation['line_count'],
        "errors": validation.get('errors', []),
        "warnings": validation.get('warnings', []),
        "analysis": {}
    }

    # Detect diagram type for specific advice
    diagram_type = validation['diagram_type']

    if 'best_practices' in focus_areas:
        practices = resources.get_best_practices(diagram_type)
        if practices:
            result["analysis"]["best_practices"] = practices[:7]

    if 'readability' in focus_areas:
        readability_issues = []
        lines = code.split('\n')
        if len(lines) > 50:
            readability_issues.append("Consider breaking complex diagram into smaller sub-diagrams")
        if any(len(line) > 100 for line in lines):
            readability_issues.append("Some lines are very long - consider shorter labels")
        if code.count('-->') > 20:
            readability_issues.append("Many connections detected - ensure clear visual hierarchy")
        if not any(word in code.lower() for word in ['title', 'subgraph', 'section']):
            readability_issues.append("Consider adding title or grouping elements for clarity")
        result["analysis"]["readability"] = readability_issues

    if 'styling' in focus_areas:
        styling_recommendations = [
            "Use consistent naming conventions",
            "Consider adding colors for different types of elements"
        ]
        if diagram_type == 'flowchart':
            styling_recommendations.append("Use subgraphs to group related processes")
        elif diagram_type == 'sequence':
            styling_recommendations.append("Use notes to explain complex interactions")
        result["analysis"]["styling"] = styling_recommendations

    return result


# Tool: Suggest Diagram Improvements
@mcp.tool(description="Get suggestions for improving an existing diagram")
async def suggest_diagram_improvements(
    current_code: str,
    improvement_goals: List[str] = None,
    target_audience: str = "general"
) -> Dict[str, Any]:
    """Suggest improvements for existing diagrams"""
    improvement_goals = improvement_goals or ['clarity']

    # First analyze the current code
    validation = MermaidValidator.validate(current_code)
    diagram_type = validation['diagram_type']

    result = {
        "diagram_type": diagram_type,
        "target_audience": target_audience,
        "improvement_goals": improvement_goals,
        "suggestions": {}
    }

    # Get a better example of the same type
    examples = resources.get_examples_by_category(diagram_type)
    if examples:
        # Find a good example to reference
        for example in examples:
            if example.complexity in ['intermediate', 'advanced']:
                result["reference_example"] = {
                    "name": example.name,
                    "description": example.description,
                    "features": example.features
                }
                break

    if 'clarity' in improvement_goals:
        result["suggestions"]["clarity"] = [
            "Use descriptive, consistent naming",
            "Add a title to explain the diagram's purpose",
            "Group related elements using subgraphs or sections",
            "Ensure logical flow from start to end"
        ]

    if 'visual_appeal' in improvement_goals:
        result["suggestions"]["visual_appeal"] = [
            f"Consider using the '{diagram_type}' theme for better visual hierarchy",
            "Use consistent colors for similar elements",
            "Balance the layout to avoid crowding"
        ]
        if diagram_type == 'flowchart':
            result["suggestions"]["visual_appeal"].append("Try the hand-drawn look for informal presentations")

    if 'completeness' in improvement_goals:
        completeness_suggestions = []
        if diagram_type == 'flowchart':
            completeness_suggestions.extend([
                "Include error handling paths",
                "Show all possible decision outcomes",
                "Add start and end points"
            ])
        elif diagram_type == 'sequence':
            completeness_suggestions.extend([
                "Show return messages",
                "Include error scenarios",
                "Add activation boxes for clarity"
            ])
        elif diagram_type == 'class':
            completeness_suggestions.extend([
                "Include method parameters and return types",
                "Show all important relationships",
                "Add visibility modifiers"
            ])
        result["suggestions"]["completeness"] = completeness_suggestions

    # Audience-specific suggestions
    audience_suggestions = []
    if target_audience == 'technical':
        audience_suggestions.extend([
            "Include technical details and specific terms",
            "Show implementation details where relevant",
            "Use precise, unambiguous labels"
        ])
    elif target_audience == 'business':
        audience_suggestions.extend([
            "Focus on business processes and outcomes",
            "Use business terminology, avoid technical jargon",
            "Highlight decision points and approvals"
        ])
    elif target_audience == 'presentation':
        audience_suggestions.extend([
            "Simplify for high-level overview",
            "Use larger, readable fonts",
            "Minimize text, focus on visual flow",
            "Consider hand-drawn style for engagement"
        ])
    else:  # general
        audience_suggestions.extend([
            "Balance detail with simplicity",
            "Define any technical terms used",
            "Use intuitive symbols and shapes"
        ])
    result["suggestions"]["audience"] = audience_suggestions

    # Add a relevant template suggestion
    templates = resources.templates.get(diagram_type, [])
    if templates:
        result["template_suggestion"] = {
            "name": templates[0].name,
            "description": templates[0].description
        }

    return result


# Prompt: Flowchart Wizard
@mcp.prompt(description="Interactive wizard to create a flowchart diagram")
async def flowchart_wizard(process_name: str = "Process", complexity: str = "medium") -> str:
    """Generate flowchart wizard prompt"""
    return PromptGenerator.get_flowchart_prompt(process_name, complexity)


# Prompt: Sequence Diagram Wizard
@mcp.prompt(description="Guide for creating sequence diagrams")
async def sequence_diagram_wizard(scenario: str = "interaction", participants: str = "3") -> str:
    """Generate sequence diagram wizard prompt"""
    return PromptGenerator.get_sequence_prompt(scenario, participants)


# Prompt: Architecture Diagram
@mcp.prompt(description="Create system architecture diagrams")
async def architecture_diagram(system_name: str = "System", components: str = "") -> str:
    """Generate architecture diagram prompt"""
    component_list = components.split(',') if components else []
    return PromptGenerator.get_architecture_prompt(system_name, component_list)


# Prompt: Data Visualization
@mcp.prompt(description="Create charts and data visualizations")
async def data_visualization(data_type: str = "data", title: str = "Data Visualization") -> str:
    """Generate data visualization prompt"""
    return PromptGenerator.get_data_viz_prompt(data_type, title)


# Prompt: Project Timeline
@mcp.prompt(description="Create Gantt charts for project planning")
async def project_timeline(project_name: str = "Project", duration: str = "3 months") -> str:
    """Generate project timeline prompt"""
    return PromptGenerator.get_gantt_prompt(project_name, duration)


# Prompt: State Diagram Wizard
@mcp.prompt(description="Create state machine diagrams for system behavior")
async def state_diagram_wizard(system_name: str = "System", initial_state: str = None) -> str:
    """Generate state diagram wizard prompt"""
    return PromptGenerator.get_state_diagram_prompt(system_name)


# Prompt: ER Diagram Wizard
@mcp.prompt(description="Design entity-relationship diagrams for databases")
async def er_diagram_wizard(domain: str = "Database", complexity: str = "medium") -> str:
    """Generate ER diagram wizard prompt"""
    return PromptGenerator.get_er_diagram_prompt(domain)


# Prompt: Class Diagram Wizard
@mcp.prompt(description="Create class diagrams for object-oriented design")
async def class_diagram_wizard(system_name: str = "System", design_pattern: str = None) -> str:
    """Generate class diagram wizard prompt"""
    return PromptGenerator.get_class_diagram_prompt(system_name)


# Prompt: Mindmap Wizard
@mcp.prompt(description="Create mindmaps for brainstorming and concept organization")
async def mindmap_wizard(central_topic: str = "Topic", purpose: str = "brainstorming") -> str:
    """Generate mindmap wizard prompt"""
    return PromptGenerator.get_mindmap_prompt(central_topic)


# Prompt: User Journey Wizard
@mcp.prompt(description="Map customer or user journeys")
async def user_journey_wizard(journey_name: str = "User Journey", user_type: str = "customer") -> str:
    """Generate user journey wizard prompt"""
    return f"""Let's create a user journey map for "{journey_name}". Please provide:

1. **User Type**: Who is the user? ({user_type})

2. **Journey Stages**: What are the main phases?
   Example: "Awareness → Consideration → Purchase → Onboarding → Usage → Support"

3. **Touchpoints**: Where does the user interact with your system/service?
   Example: "Website, Mobile app, Email, Phone support, Physical store"

4. **User Actions**: What does the user do at each stage?
   Example: "Research options, Compare features, Read reviews, Make purchase"

5. **Emotions**: How does the user feel? (1-5 scale)
   Example: "Excited: 5, Confused: 2, Satisfied: 4"

6. **Pain Points**: What frustrates the user?
   Example: "Complex registration, Slow loading, Unclear pricing"

7. **Opportunities**: Where can you improve the experience?

Share these details for a comprehensive journey map."""


# Prompt: Troubleshooting Flowchart
@mcp.prompt(description="Create diagnostic and troubleshooting flowcharts")
async def troubleshooting_flowchart(problem_area: str = "System Issue", complexity: str = "basic") -> str:
    """Generate troubleshooting flowchart prompt"""
    return f"""Let's create a troubleshooting flowchart for "{problem_area}". Please provide:

1. **Initial Problem**: What issue are users experiencing?
   Example: "System won't start", "App crashes", "Login fails"

2. **Diagnostic Questions**: What should be checked first?
   Example: "Is the power on?", "Is network connected?", "Are credentials correct?"

3. **Common Causes**: List the most frequent root causes
   Example: "Network timeout", "Invalid credentials", "Server overload"

4. **Quick Fixes**: Simple solutions to try first
   Example: "Restart application", "Clear cache", "Check connection"

5. **Escalation Points**: When should it go to next level support?
   Example: "After 3 failed attempts", "If hardware issue suspected"

6. **Resolution Steps**: Detailed fix procedures
   Example: "Reset password → Verify email → Login again"

Provide these details for a comprehensive troubleshooting guide."""


# ==================== HELPER FUNCTIONS ====================

def _get_example_code() -> Dict[str, str]:
    """Get example Mermaid code for different diagram types"""
    return {
        "flowchart": """graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> E[Fix issues]
    E --> B
    C --> F[Deploy]""",

        "sequence": """sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Database

    User->>Frontend: Submit form
    Frontend->>Backend: POST /api/data
    Backend->>Database: INSERT query
    Database-->>Backend: Success
    Backend-->>Frontend: 200 OK
    Frontend-->>User: Show success""",

        "gantt": """gantt
    title Project Schedule
    dateFormat YYYY-MM-DD
    section Planning
    Requirements :done, req, 2024-01-01, 7d
    Design :done, design, after req, 10d
    section Development
    Backend :active, backend, 2024-01-20, 20d
    Frontend :frontend, after backend, 15d
    section Testing
    Unit tests :test1, 2024-02-15, 10d
    Integration :test2, after test1, 7d""",

        "class": """classDiagram
    class User {
        -String id
        -String email
        +String name
        +login(password)
        +logout()
    }
    class Admin {
        +String role
        +manageUsers()
    }
    class Customer {
        -String customerId
        +placeOrder()
        +viewOrders()
    }
    User <|-- Admin
    User <|-- Customer""",

        "state": """stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : Start
    Processing --> Success : Complete
    Processing --> Error : Fail
    Success --> [*]
    Error --> Idle : Retry
    Error --> [*] : Give up""",

        "er": """erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    CUSTOMER {
        string id PK
        string name
        string email UK
    }
    ORDER {
        string id PK
        date orderDate
        string customerId FK
    }
    LINE-ITEM {
        string id PK
        number quantity
        number price
        string orderId FK
        string productId FK
    }""",

        "pie": """pie title Browser Usage Stats
    "Chrome" : 65
    "Firefox" : 20
    "Safari" : 10
    "Edge" : 5""",

        "mindmap": """mindmap
  root((Sailor Site))
    Features
      AI Generation
        OpenAI
        Anthropic
      Live Preview
      Style Controls
        Themes
        Looks
          Classic
          HandDrawn
    Benefits
      No API needed
      Professional diagrams
      Easy to use
    Use Cases
      Documentation
      Architecture
      Planning"""
    }


# ==================== ENTRY POINTS ====================

def main_stdio():
    """Entry point for stdio transport (for setup.py console_scripts)"""
    logger.info("Starting Sailor MCP Server (stdio)...")
    logger.info("Get a picture of your Mermaid! 🧜‍♀️")
    mcp.run()  # Default transport is stdio


def main_http():
    """Entry point for Streamable HTTP transport (for setup.py console_scripts)

    Supports environment variables for Railway and other PaaS:
    - PORT: Server port (Railway sets this automatically)
    - HOST: Server host (default: 0.0.0.0)
    - RATE_LIMIT_REQUESTS: Max requests per window (default: 100)
    - RATE_LIMIT_WINDOW: Rate limit window in seconds (default: 60)
    - RATE_LIMIT_RENDER: Max render requests per window (default: 20)
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Sailor MCP Server - Mermaid diagram generation via MCP protocol"
    )
    parser.add_argument(
        "--host",
        default=HOST,
        help=f"Server host (default: {HOST}, or HOST env var)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=PORT,
        help=f"Server port (default: {PORT}, or PORT env var)"
    )
    parser.add_argument(
        "--transport",
        default=os.environ.get("MCP_TRANSPORT_TYPE", "http"),
        choices=["http", "streamable-http", "sse"],
        help="Transport type (default: http - enables custom routes like /download)"
    )

    args = parser.parse_args()

    # Map transport names to FastMCP transport values
    # Note: "http" enables custom routes, "streamable-http" may not
    transport_map = {
        "http": "http",
        "streamable-http": "streamable-http",
        "sse": "sse"
    }
    transport = transport_map.get(args.transport, "http")

    logger.info("=" * 60)
    logger.info("Sailor MCP Server v2.0.0 - Remote Mermaid Diagram Service")
    logger.info("=" * 60)
    logger.info(f"Transport: {transport}")
    logger.info(f"Listening: {args.host}:{args.port}")
    logger.info(f"Rate Limits: {RATE_LIMIT_REQUESTS} req/{RATE_LIMIT_WINDOW}s, {RATE_LIMIT_RENDER} renders/{RATE_LIMIT_WINDOW}s")
    logger.info("Get a picture of your Mermaid! 🧜‍♀️")
    logger.info("=" * 60)

    # Just run the MCP server normally - custom routes should be included
    # via the @mcp.custom_route decorator defined earlier in this file
    mcp.run(transport=transport, host=args.host, port=args.port)


# ==================== MAIN ====================

if __name__ == "__main__":
    import sys

    # Determine transport mode
    if "--http" in sys.argv or os.environ.get("MCP_TRANSPORT") == "http":
        # Use HTTP entry point (delegates to main_http)
        main_http()
    else:
        # Use stdio entry point (delegates to main_stdio)
        main_stdio()