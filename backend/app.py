from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory, render_template_string
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import os
from dotenv import load_dotenv
import openai
from anthropic import Anthropic
from authlib.integrations.flask_client import OAuth
import json
import logging
import traceback
import time
import signal
from functools import wraps

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MIDDLEWARE & DECORATORS ====================

def validate_json(required_fields=None, optional_fields=None, max_length=None):
    """
    Decorator for validating JSON request data

    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        max_length: Dict of field_name: max_length for string fields
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check content type
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400

            data = request.get_json()
            if data is None:
                return jsonify({"error": "Invalid JSON"}), 400

            # Validate required fields
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

            # Validate field lengths
            if max_length:
                for field, max_len in max_length.items():
                    if field in data and isinstance(data[field], str):
                        if len(data[field]) > max_len:
                            return jsonify({
                                "error": f"Field '{field}' exceeds maximum length of {max_len}"
                            }), 400

            # Validate only allowed fields
            if required_fields or optional_fields:
                allowed = set(required_fields or []) | set(optional_fields or [])
                extra = set(data.keys()) - allowed
                if extra:
                    logger.warning(f"Extra fields provided: {extra}")

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def timeout_handler(signum, frame):
    """Handle timeout signal"""
    raise TimeoutError("Request timed out")

def with_timeout(seconds=30):
    """
    Decorator to add timeout to request handling
    Note: Only works on Unix systems
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip timeout on Windows
            if os.name == 'nt':
                return f(*args, **kwargs)

            # Set timeout alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)

            try:
                result = f(*args, **kwargs)
            except TimeoutError:
                logger.error(f"Request timeout after {seconds}s: {request.path}")
                return jsonify({"error": f"Request timeout after {seconds} seconds"}), 504
            finally:
                # Restore old signal handler and cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return result
        return decorated_function
    return decorator

app = Flask(__name__)

# Secure SECRET_KEY configuration
# In production, SECRET_KEY MUST be set via environment variable
# In development, we generate a random key if not provided
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    if FLASK_ENV == 'production':
        logger.error("CRITICAL: SECRET_KEY environment variable is not set in production!")
        logger.error("Set SECRET_KEY to a secure random value before starting the application.")
        logger.error("Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'")
        raise RuntimeError(
            "SECRET_KEY must be set in production environment. "
            "Set the SECRET_KEY environment variable to a secure random value."
        )
    else:
        # Development mode: generate a random key for this session
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        logger.warning("=" * 80)
        logger.warning("WARNING: Using auto-generated SECRET_KEY for development session")
        logger.warning("This is ONLY safe for development. Set SECRET_KEY env var for production.")
        logger.warning("=" * 80)

app.secret_key = SECRET_KEY

# Secure CORS configuration
# Allow specific origins only - configure via CORS_ORIGINS env var
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').strip()
if CORS_ORIGINS:
    # Parse comma-separated list of allowed origins
    allowed_origins = [origin.strip() for origin in CORS_ORIGINS.split(',') if origin.strip()]
    logger.info(f"CORS configured for origins: {allowed_origins}")
else:
    # Default safe origins for development
    if FLASK_ENV == 'development':
        allowed_origins = [
            'http://localhost:3000',
            'http://localhost:5000',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5000'
        ]
        logger.warning("Using default CORS origins for development. Set CORS_ORIGINS env var for production.")
    else:
        # Production: empty list means no CORS (same-origin only)
        allowed_origins = []
        logger.warning("CORS_ORIGINS not set in production - CORS disabled (same-origin only)")

CORS(app,
     origins=allowed_origins if allowed_origins else None,
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     max_age=3600)

# Rate limiting configuration
# Protects against API abuse and excessive AI API costs
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get('RATE_LIMIT_STORAGE_URI', 'memory://'),
    strategy="fixed-window",
    # Add headers to response
    headers_enabled=True,
    # Swallow errors in case of storage issues (fail open in dev, but log)
    swallow_errors=FLASK_ENV == 'development'
)
logger.info(f"Rate limiting enabled: 200/day, 50/hour per IP")

# Security headers configuration
# Protects against XSS, clickjacking, and other web vulnerabilities
if FLASK_ENV == 'production':
    # Production: Strict security headers
    csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            'https://cdn.jsdelivr.net',
            'https://cdnjs.cloudflare.com',
            "'unsafe-inline'"  # Needed for Mermaid.js
        ],
        'style-src': [
            "'self'",
            'https://cdnjs.cloudflare.com',
            "'unsafe-inline'"
        ],
        'img-src': ["'self'", 'data:', 'https:'],
        'font-src': ["'self'", 'https://cdnjs.cloudflare.com'],
        'connect-src': ["'self'"],
    }

    Talisman(
        app,
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,  # 1 year
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        referrer_policy='strict-origin-when-cross-origin',
        feature_policy={
            'geolocation': "'none'",
            'camera': "'none'",
            'microphone': "'none'",
        }
    )
    logger.info("Security headers enabled (Talisman) - Production mode")
else:
    # Development: Relaxed for local development
    Talisman(
        app,
        force_https=False,
        content_security_policy=False,  # Disable CSP in dev for easier debugging
        strict_transport_security=False
    )
    logger.info("Security headers enabled (Talisman) - Development mode (relaxed)")

# OAuth setup
oauth = OAuth(app)

# Google OAuth for Anthropic passthrough
google_oauth = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Mermaid knowledge base
MERMAID_KNOWLEDGE = """
Mermaid is a diagramming and charting tool that uses text-based syntax. Here are the main diagram types and their syntax:

1. Flowchart:
```mermaid
graph TD
    A[Start] --> B{Is it?}
    B -->|Yes| C[OK]
    B -->|No| D[End]
```

2. Sequence Diagram:
```mermaid
sequenceDiagram
    Alice->>John: Hello John
    John-->>Alice: Hi Alice
```

3. Class Diagram:
```mermaid
classDiagram
    Animal <|-- Duck
    Animal : +int age
    Animal : +String gender
    Duck : +String beakColor
```

4. State Diagram:
```mermaid
stateDiagram-v2
    [*] --> Still
    Still --> Moving
    Moving --> Still
    Moving --> [*]
```

5. Entity Relationship Diagram:
```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```

6. Gantt Chart:
```mermaid
gantt
    title A Gantt Diagram
    dateFormat  YYYY-MM-DD
    section Section
    A task           :a1, 2024-01-01, 30d
    Another task     :after a1, 20d
```

7. Pie Chart:
```mermaid
pie title Pets adopted
    "Dogs" : 386
    "Cats" : 85
    "Rats" : 15
```

8. Git Graph:
```mermaid
gitGraph
    commit
    branch develop
    checkout develop
    commit
    checkout main
    merge develop
```
"""

@app.route('/api/health', methods=['GET'])
def health():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "sailor-backend",
        "version": "2.0.0"
    })

@app.route('/api/health/detailed', methods=['GET'])
def health_detailed():
    """Detailed health check with dependency verification"""
    health_status = {
        "status": "healthy",
        "service": "sailor-backend",
        "version": "2.0.0",
        "timestamp": time.time(),
        "environment": FLASK_ENV,
        "checks": {}
    }

    # Check Flask app
    health_status["checks"]["flask"] = {
        "status": "ok",
        "message": "Flask application running"
    }

    # Check rate limiter
    try:
        # Try to access rate limiter storage
        _ = limiter.storage
        health_status["checks"]["rate_limiter"] = {
            "status": "ok",
            "message": "Rate limiter operational"
        }
    except Exception as e:
        health_status["checks"]["rate_limiter"] = {
            "status": "degraded",
            "message": f"Rate limiter issue: {str(e)}"
        }
        health_status["status"] = "degraded"

    # Check configuration
    config_issues = []
    if not SECRET_KEY or (FLASK_ENV == 'production' and len(SECRET_KEY) < 32):
        config_issues.append("SECRET_KEY not properly configured")
    if FLASK_ENV == 'production' and not CORS_ORIGINS:
        config_issues.append("CORS_ORIGINS not set in production")

    if config_issues:
        health_status["checks"]["configuration"] = {
            "status": "warning",
            "issues": config_issues
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    else:
        health_status["checks"]["configuration"] = {
            "status": "ok",
            "message": "Configuration validated"
        }

    # Overall status
    statuses = [check.get("status") for check in health_status["checks"].values()]
    if "error" in statuses:
        health_status["status"] = "unhealthy"
        return jsonify(health_status), 503
    elif "degraded" in statuses or "warning" in statuses:
        health_status["status"] = "degraded"
        return jsonify(health_status), 200
    else:
        return jsonify(health_status), 200

@app.route('/api/health/live', methods=['GET'])
def health_live():
    """Liveness probe - is the app running?"""
    return jsonify({"status": "alive"}), 200

@app.route('/api/health/ready', methods=['GET'])
def health_ready():
    """Readiness probe - can the app serve requests?"""
    # Check if critical dependencies are available
    try:
        # Verify app is configured
        if not SECRET_KEY:
            return jsonify({"status": "not ready", "reason": "SECRET_KEY not set"}), 503

        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "reason": str(e)}), 503

@app.route('/api/validate-key', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json(
    required_fields=['api_key', 'provider'],
    max_length={'api_key': 500, 'provider': 50}
)
@with_timeout(10)
def validate_api_key():
    try:
        data = request.json
        api_key = data.get('api_key', '')
        provider = data.get('provider', 'openai')
        
        logger.info(f"Validating API key for provider: {provider}")
        
        if not api_key:
            return jsonify({"valid": False, "error": "No API key provided"}), 400
        
        try:
            if provider == 'openai':
                # Test OpenAI API key
                client = openai.OpenAI(api_key=api_key)
                # Make a minimal API call to validate the key
                client.models.list(limit=1)
                logger.info("OpenAI API key is valid")
                return jsonify({"valid": True, "provider": "openai"})
                
            elif provider == 'anthropic':
                # Test Anthropic API key
                client = Anthropic(api_key=api_key)
                # Make a minimal API call to validate the key
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                logger.info("Anthropic API key is valid")
                return jsonify({"valid": True, "provider": "anthropic"})
                
            else:
                return jsonify({"valid": False, "error": "Invalid provider"}), 400
                
        except Exception as e:
            logger.warning(f"API key validation failed: {str(e)}")
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return jsonify({"valid": False, "error": "Invalid API key"})
            else:
                return jsonify({"valid": False, "error": f"Validation error: {str(e)}"})
                
    except Exception as e:
        logger.error(f"Unexpected error in validate_api_key: {str(e)}")
        return jsonify({"valid": False, "error": "Unexpected error during validation"}), 500

@app.route('/api/generate-mermaid', methods=['POST'])
@limiter.limit("10 per minute;30 per hour;100 per day")
@validate_json(
    required_fields=['input'],
    optional_fields=['api_key', 'provider'],
    max_length={'input': 10000, 'api_key': 500, 'provider': 50}
)
@with_timeout(60)
def generate_mermaid():
    try:
        data = request.json
        logger.debug(f"Received request data: {data}")
        
        user_input = data.get('input', '')
        api_key = data.get('api_key', '')
        provider = data.get('provider', 'openai')
        
        logger.info(f"Processing request - Provider: {provider}, Input length: {len(user_input)}, Has API key: {bool(api_key)}")
        
        if not user_input:
            logger.warning("No input provided")
            return jsonify({"error": "No input provided"}), 400
        
        if not api_key and provider not in session.get('authenticated_providers', []):
            logger.warning("No API key or OAuth authentication")
            return jsonify({"error": "API key required or OAuth authentication needed"}), 401
        
        try:
            if provider == 'openai':
                logger.info("Generating with OpenAI")
                response = generate_with_openai(user_input, api_key)
            elif provider == 'anthropic':
                logger.info("Generating with Anthropic")
                response = generate_with_anthropic(user_input, api_key)
            else:
                logger.error(f"Invalid provider: {provider}")
                return jsonify({"error": "Invalid provider"}), 400
            
            logger.info("Successfully generated Mermaid code")
            return jsonify({
                "mermaid_code": response,
                "success": True
            })
        except Exception as e:
            logger.error(f"Error generating Mermaid code: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in generate_mermaid: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def generate_with_openai(user_input, api_key):
    client = openai.OpenAI(api_key=api_key or session.get('openai_token'))
    
    prompt = f"""You are an expert in Mermaid diagram syntax. Based on the following user request, generate appropriate Mermaid diagram code.

User request: {user_input}

Mermaid Knowledge Base:
{MERMAID_KNOWLEDGE}

Please provide only the Mermaid code without any explanation or markdown code blocks."""
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a Mermaid diagram expert. Generate only valid Mermaid syntax."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

def generate_with_anthropic(user_input, api_key):
    try:
        # SECURITY: Never log API keys, even partially
        logger.debug(f"Creating Anthropic client with API key: {'***set***' if api_key else 'not set'}")

        # Create client with only the api_key parameter
        client = Anthropic(api_key=api_key or session.get('anthropic_token'))

        logger.debug("Anthropic client created successfully")
        
        prompt = f"""You are an expert in Mermaid diagram syntax. Based on the following user request, generate appropriate Mermaid diagram code.

User request: {user_input}

Mermaid Knowledge Base:
{MERMAID_KNOWLEDGE}

Please provide only the Mermaid code without any explanation or markdown code blocks."""
        
        logger.debug(f"Sending request to Anthropic API with prompt length: {len(prompt)}")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        logger.debug("Received response from Anthropic API")
        
        result = response.content[0].text.strip()
        logger.debug(f"Generated Mermaid code length: {len(result)}")
        
        return result
    except Exception as e:
        logger.error(f"Error in generate_with_anthropic: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(traceback.format_exc())
        raise

@app.route('/api/auth/google/login')
def google_login():
    try:
        redirect_uri = url_for('google_callback', _external=True)
        # Add Anthropic-specific parameters for passthrough auth
        return google_oauth.authorize_redirect(
            redirect_uri,
            prompt='select_account',
            # Additional params for Anthropic integration
            state=json.dumps({
                'provider': 'anthropic',
                'timestamp': str(int(time.time()))
            })
        )
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        return jsonify({"error": f"OAuth not configured: {str(e)}"}), 500

@app.route('/api/auth/google/callback')
def google_callback():
    try:
        token = google_oauth.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            session['google_email'] = user_info.get('email')
            session['google_name'] = user_info.get('name')
            session['google_authenticated'] = True
            
            # Here you would typically check if this Google account
            # has an associated Anthropic account and handle the passthrough
            logger.info(f"Google auth successful for: {user_info.get('email')}")
            
            # For now, we'll mark as authenticated
            session['authenticated_providers'] = ['anthropic-google']
        
        # Redirect to frontend with success
        return redirect('http://localhost:3000/auth-success')
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return redirect('http://localhost:3000/auth-error')

@app.route('/api/auth/status')
def auth_status():
    return jsonify({
        "authenticated_providers": session.get('authenticated_providers', [])
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)