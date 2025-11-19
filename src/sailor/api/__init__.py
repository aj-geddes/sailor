"""
Sailor API module for web frontend integration.
"""

from .server import create_app
from .models import *

__all__ = ["create_app"]