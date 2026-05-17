"""
Configuration Management
Loads configuration from .env file in project root directory
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
# Path: MiroFish/.env (relative to backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=False)
else:
    # If no .env in root, try to load environment variables (for production)
    load_dotenv(override=False)


def _env(name: str, default=None, aliases=()):
    """Read an environment variable with optional backwards-compatible aliases."""
    for key in (name, *aliases):
        value = os.environ.get(key)
        if value not in (None, ''):
            return value
    return default


def _is_true(value: str) -> bool:
    return str(value).lower() in ('1', 'true', 'yes', 'on')


class Config:
    """Flask configuration class"""

    # Flask configuration
    SECRET_KEY = _env('SECRET_KEY', 'mirofish-secret-key')
    FLASK_ENV = _env('FLASK_ENV', _env('APP_ENV', 'development'))
    IS_PRODUCTION = FLASK_ENV.lower() == 'production' or _is_true(os.environ.get('RENDER', 'false'))
    DEBUG = _env('FLASK_DEBUG', 'False' if IS_PRODUCTION else 'True').lower() == 'true'

    # JSON configuration - disable ASCII escaping to display Chinese directly (not as \uXXXX)
    JSON_AS_ASCII = False

    # LLM configuration (unified OpenAI format)
    LLM_API_KEY = _env('LLM_API_KEY')
    LLM_BASE_URL = _env('LLM_BASE_URL', 'http://localhost:11434/v1')
    LLM_MODEL_NAME = _env('LLM_MODEL_NAME', 'qwen2.5:32b', aliases=('LLM_MODEL',))

    # Neo4j configuration
    NEO4J_URI = _env('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = _env('NEO4J_USER', 'neo4j', aliases=('NEO4J_USERNAME',))
    NEO4J_PASSWORD = _env('NEO4J_PASSWORD', 'mirofish')

    # Embedding configuration
    EMBEDDING_MODEL = _env('EMBEDDING_MODEL', 'nomic-embed-text')
    EMBEDDING_BASE_URL = _env('EMBEDDING_BASE_URL', 'http://localhost:11434')

    # Cloud integrations
    SUPABASE_URL = _env('SUPABASE_URL')
    SUPABASE_SERVICE_ROLE_KEY = _env('SUPABASE_SERVICE_ROLE_KEY')
    FRONTEND_URL = _env('FRONTEND_URL', 'http://localhost:5173')
    GROQ_API_KEY = _env('GROQ_API_KEY')

    # File upload configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Text processing configuration
    DEFAULT_CHUNK_SIZE = 500  # Default chunk size
    DEFAULT_CHUNK_OVERLAP = 50  # Default overlap size

    # OASIS simulation configuration
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    # OASIS platform available actions configuration
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent configuration
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured (set to any non-empty value, e.g. 'ollama')")
        if not cls.NEO4J_URI:
            errors.append("NEO4J_URI not configured")
        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD not configured")
        if cls.IS_PRODUCTION:
            local_markers = ('localhost', '127.0.0.1', '0.0.0.0')
            if any(marker in (cls.LLM_BASE_URL or '') for marker in local_markers):
                errors.append("LLM_BASE_URL points to localhost in production; configure a cloud OpenAI-compatible endpoint")
            if any(marker in (cls.NEO4J_URI or '') for marker in local_markers):
                errors.append("NEO4J_URI points to localhost in production; configure Neo4j Aura with neo4j+s://...")
            if any(marker in (cls.FRONTEND_URL or '') for marker in local_markers):
                errors.append("FRONTEND_URL points to localhost in production; configure the Vercel app origin")
            if not cls.SUPABASE_URL:
                errors.append("SUPABASE_URL not configured")
            if not cls.SUPABASE_SERVICE_ROLE_KEY:
                errors.append("SUPABASE_SERVICE_ROLE_KEY not configured")
        return errors
