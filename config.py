import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""

    # API Keys
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Using service_role for backend operations
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_PUBLIC_KEY = os.getenv('SUPABASE_PUBLIC_KEY')
    SUPABASE_SECRET_KEY = os.getenv('SUPABASE_SECRET_KEY')
    SUPABASE_STORAGE_BUCKET = os.getenv('SUPABASE_STORAGE_BUCKET', 'memoires')

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')

    # Template
    TEMPLATE_PATH = './templates/template.docx'

    # Application
    APP_URL = os.getenv('APP_URL', 'http://localhost:8000')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required = [
            'CLAUDE_API_KEY',
            'OPENAI_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'DATABASE_URL'
        ]

        missing = [key for key in required if not getattr(cls, key)]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True
