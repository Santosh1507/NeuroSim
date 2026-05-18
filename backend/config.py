from typing import Optional, List
from pydantic_settings import BaseSettings
import json

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
    
    class Config:
        env_file = ".env"

settings = Settings()
