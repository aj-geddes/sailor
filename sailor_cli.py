#!/usr/bin/env python3
"""
Sailor CLI - Command-line tool for documentation-as-code pipelines
Processes Mermaid diagrams in markdown files and generates images
"""

import argparse
import asyncio
import os
import re
import sys
import base64
import hashlib
import json
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from datetime import datetime
# Optional import for watch mode
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

# Add sailor_mcp to path
sys.path.append(os.path.dirname(__file__))

from sailor_mcp.validators import MermaidValidator
from sailor_mcp.renderer import MermaidRenderer

class DiagramCache:
    """Cache for tracking diagram changes and avoiding reprocessing"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / '.sailor-cache.json'
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_hash(self, content: str) -> str:
        """Get hash of content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def needs_update(self, key: str, content: str) -> bool:
        """Check if content has changed"""
        content_hash = self.get_hash(content)
        return self.cache.get(key) != content_hash
    
    def update(self, key: str, content: str):
        """Update cache entry"""
        self.cache[key] = self.get_hash(content)
        self._save_cache()


class MarkdownWatcher(FileSystemEventHandler):
    """Watch for changes in markdown files"""
    
    def __init__(self, cli, input_dir: Path, output_dir: Path, **kwargs):
        self.cli = cli
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.kwargs = kwargs
        self.debounce_time = 1.0  # seconds
        self.pending_files = set()
        self.last_change = {}
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            # Debounce to avoid multiple events
            current_time = time.time()
            if event.src_path in self.last_change:
                if current_time - self.last_change[event.src_path] < self.debounce_time:
                    return
            
            self.last_change[event.src_path] = current_time
            self.pending_files.add(Path(event.src_path))
            
            # Process after debounce period
            asyncio.create_task(self._process_pending())
    
    async def _process_pending(self):
        """Process pending file changes"""
        await asyncio.sleep(self.debounce_time)
        
        if self.pending_files:
            files = list(self.pending_files)
            self.pending_files.clear()
            
            print(f"\n🔄 Detected changes in {len(files)} file(s)")
            for file_path in files:
                await self.cli.process_markdown_file(
                    file_path, self.output_dir, **self.kwargs
                )


class SailorCLI:
    """CLI for processing Mermaid diagrams in documentation"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.validator = MermaidValidator()
        self.renderer = MermaidRenderer()
        self.processed_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.cache = DiagramCache(cache_dir or Path('.sailor-cache')) if cache_dir else None
        self.start_time = time.time()
    
    async def process_markdown_file(self, file_path: Path, output_dir: Path, 
                                   format: str = "png", theme: str = "default",
                                   validate_only: bool = False, 
                                   transparent: bool = False,
                                   force_regenerate: bool = False) -> List[str]:
        """Process a single markdown file and extract/render Mermaid diagrams."""
        relative_path = file_path.relative_to(Path.cwd()) if file_path.is_absolute() else file_path
        print(f"📄 Processing: {relative_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            self.error_count += 1
            return []
        
        # Find all Mermaid code blocks
        mermaid_pattern = r'```mermaid\n(.*?)\n```'
        matches = list(re.finditer(mermaid_pattern, content, re.DOTALL))
        
        if not matches:
            print(f"  ℹ️  No Mermaid diagrams found")
            return []
        
        generated_files = []
        
        for i, match in enumerate(matches):
            mermaid_code = match.group(1).strip()
            diagram_line = content[:match.start()].count('\n') + 1
            
            # Create unique cache key
            cache_key = f"{file_path}:{i}:{format}:{theme}"
            
            # Check cache if enabled
            if self.cache and not force_regenerate and not validate_only:
                if not self.cache.needs_update(cache_key, mermaid_code):
                    print(f"  ⏭️  Diagram {i+1} unchanged, skipping")
                    self.skipped_count += 1
                    # Still add to generated files list
                    base_name = file_path.stem
                    output_filename = f"{base_name}_diagram_{i+1}.{format}"
                    output_path = output_dir / output_filename
                    if output_path.exists():
                        generated_files.append(str(output_path))
                    continue
            
            # Validate the diagram
            validation = self.validator.validate(mermaid_code)
            
            if not validation.is_valid:
                error_msg = validation.errors[0].message if validation.errors else "Unknown error"
                print(f"  ❌ Diagram {i+1} (line {diagram_line}): {error_msg}")
                if validation.errors[0].suggestion:
                    print(f"     💡 Suggestion: {validation.errors[0].suggestion}")
                self.error_count += 1
                continue
            
            if validate_only:
                print(f"  ✅ Diagram {i+1} is valid")
                self.processed_count += 1
                continue
            
            # Generate output filename
            base_name = file_path.stem
            output_filename = f"{base_name}_diagram_{i+1}.{format}"
            output_path = output_dir / output_filename
            
            # Create relative path for output
            relative_output = output_path.relative_to(Path.cwd()) if output_path.is_absolute() else output_path
            
            try:
                # Render the diagram
                result = await self.renderer.render(
                    code=mermaid_code,
                    theme=theme,
                    output_format=format,
                    transparent_background=transparent
                )
                
                if result.success:
                    # Save the image
                    image_data = base64.b64decode(result.data)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"  ✅ Generated: {relative_output}")
                    generated_files.append(str(output_path))
                    self.processed_count += 1
                    
                    # Update cache
                    if self.cache:
                        self.cache.update(cache_key, mermaid_code)
                else:
                    print(f"  ❌ Rendering failed: {result.error}")
                    self.error_count += 1
                    
            except Exception as e:
                print(f"  ❌ Unexpected error: {e}")
                self.error_count += 1
        
        return generated_files
    
    async def process_directory(self, input_dir: Path, output_dir: Path, 
                               pattern: str = "**/*.md", **kwargs) -> None:
        """Process all markdown files in a directory."""
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all markdown files
        md_files = list(input_dir.glob(pattern))
        print(f"🔍 Found {len(md_files)} markdown files")
        
        all_generated = []
        
        for md_file in md_files:
            # Create subdirectory structure in output
            relative_path = md_file.relative_to(input_dir)
            file_output_dir = output_dir / relative_path.parent
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            generated = await self.process_markdown_file(
                md_file, file_output_dir, **kwargs
            )
            all_generated.extend(generated)
        
        # Generate index file
        await self.generate_index(output_dir, all_generated)
        
        print(f"\n✨ Processing complete!")
        print(f"  📊 Diagrams processed: {self.processed_count}")
        print(f"  ❌ Errors: {self.error_count}")
    
    async def generate_index(self, output_dir: Path, generated_files: List[str]) -> None:
        """Generate an index.html file listing all generated diagrams."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Sailor Generated Diagrams</title>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 20px; }
        .diagram { margin: 20px 0; border: 1px solid #ddd; padding: 10px; }
        img { max-width: 100%; height: auto; }
        h1 { color: #2c3e50; }
        .metadata { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>🚢 Sailor Generated Diagrams</h1>
    <p class="metadata">Generated {count} diagrams</p>
    <div class="diagrams">
"""
        
        for file_path in generated_files:
            relative_path = Path(file_path).relative_to(output_dir)
            html_content += f"""
        <div class="diagram">
            <h3>{relative_path.stem}</h3>
            <img src="{relative_path}" alt="{relative_path.stem}">
            <p class="metadata">{relative_path}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        index_path = output_dir / "index.html"
        with open(index_path, 'w') as f:
            f.write(html_content.format(count=len(generated_files)))
        
        print(f"  📄 Generated index: {index_path}")
    
    async def process_stdin(self, output_file: str, **kwargs) -> None:
        """Process Mermaid code from stdin."""
        mermaid_code = sys.stdin.read()
        
        # Validate
        validation = self.validator.validate(mermaid_code)
        if not validation.is_valid:
            print(f"❌ Validation failed: {validation.errors[0].message}")
            sys.exit(1)
        
        # Render
        result = await self.renderer.render(code=mermaid_code, **kwargs)
        
        if result.success:
            image_data = base64.b64decode(result.data)
            with open(output_file, 'wb') as f:
                f.write(image_data)
            print(f"✅ Generated: {output_file}")
        else:
            print(f"❌ Rendering failed: {result.error}")
            sys.exit(1)
    
    async def cleanup(self):
        """Clean up resources."""
        await self.renderer.close()

async def main():
    parser = argparse.ArgumentParser(
        description='Sailor CLI - Process Mermaid diagrams for documentation pipelines',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all markdown files in docs/
  sailor-cli docs/ output/
  
  # Process with specific theme
  sailor-cli docs/ output/ --theme dark
  
  # Process single file
  sailor-cli --file README.md --output diagrams/
  
  # Process from stdin
  echo "flowchart TD\\n  A --> B" | sailor-cli --stdin --output diagram.png
  
  # Use in GitHub Actions
  sailor-cli . docs/diagrams/ --format png --theme default
        """
    )
    
    parser.add_argument('input_dir', nargs='?', help='Input directory containing markdown files')
    parser.add_argument('output_dir', nargs='?', help='Output directory for generated images')
    parser.add_argument('--file', help='Process a single file')
    parser.add_argument('--output', help='Output file/directory')
    parser.add_argument('--format', choices=['png', 'svg', 'pdf'], default='png', 
                       help='Output format (default: png)')
    parser.add_argument('--theme', choices=['default', 'dark', 'forest', 'neutral'], 
                       default='default', help='Mermaid theme (default: default)')
    parser.add_argument('--pattern', default='**/*.md', 
                       help='File pattern for finding markdown files (default: **/*.md)')
    parser.add_argument('--stdin', action='store_true', 
                       help='Read Mermaid code from stdin')
    
    args = parser.parse_args()
    
    cli = SailorCLI()
    
    try:
        if args.stdin:
            if not args.output:
                parser.error("--output is required when using --stdin")
            await cli.process_stdin(args.output, format=args.format, theme=args.theme)
        
        elif args.file:
            if not args.output:
                parser.error("--output is required when using --file")
            
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            await cli.process_markdown_file(
                Path(args.file), output_dir, 
                format=args.format, theme=args.theme
            )
        
        else:
            if not args.input_dir or not args.output_dir:
                parser.error("input_dir and output_dir are required")
            
            await cli.process_directory(
                Path(args.input_dir), Path(args.output_dir),
                pattern=args.pattern, format=args.format, theme=args.theme
            )
    
    finally:
        await cli.cleanup()

if __name__ == "__main__":
    asyncio.run(main())