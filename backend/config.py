from typing import List, Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    upload_dir: str = "uploads"
    max_file_size: int = 2 * 1024 * 1024 * 1024
    cors_origins: List[str] = ["http://localhost:3000", "https://neurosim.vercel.app"]

    # TRIBE v2 settings
    tribe_use_real: bool = False
    tribe_model_name: str = "facebook/tribev2"
    tribe_cache_folder: str = "./cache/tribev2"
    hf_token: Optional[str] = None

    # MiroFish settings
    mirofish_use_real: bool = False
    mirofish_api_url: str = "http://localhost:5001"
    mirofish_llm_api_key: Optional[str] = None
    mirofish_llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    mirofish_llm_model: str = "qwen-plus"
    mirofish_zep_api_key: Optional[str] = None

    # Stage-Gate
    stage_gate_threshold: float = 0.4

    # Premium GPU Tier
    premium_enabled: bool = False
    premium_price_monthly: int = 29
    premium_price_yearly: int = 290
    premium_max_analyses_free: int = 10
    gpu_provider: str = "modal"
    gpu_model: str = "a10g"
    gpu_timeout_seconds: int = 60
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_monthly: str = ""
    stripe_price_id_yearly: str = ""

    # Email (SMTP) — used by digest delivery
    email_host: str = ""
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = "NeuroSim <digest@neurosim.ai>"
    email_from_address: str = "digest@neurosim.ai"

    # Supabase
    supabase_jwt_secret: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # YouTube Data API v3
    youtube_api_key: str = ""

    # Sentry (error tracking)
    sentry_dsn: str = ""
    sentry_environment: str = "development"

    # PostHog (product analytics)
    posthog_api_key: str = ""
    posthog_host: str = "https://us.i.posthog.com"

    # API versioning
    api_version: str = "v1"

    model_config = ConfigDict(env_file=".env")


settings = Settings()
