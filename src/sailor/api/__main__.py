"""
Run the Sailor API server.
"""

import argparse
from .server import run_server


def main():
    """Main entry point for API server."""
    parser = argparse.ArgumentParser(description="Sailor API Server")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Sailor API server on {args.host}:{args.port}")
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()