from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Ambiente
    env: str = "dev"
    
    # Banco de dados
    database_url: str = "sqlite:///./mundo_invest.db"
    auto_create_tables: bool = False
    db_echo: bool = False
    
    # Pipefy
    pipefy_token: str = ""
    pipefy_pipe_id: str = "302428309"
    pipefy_graphql_url: str = "https://api.pipefy.com/graphql"
    
    # Segurança
    webhook_secret: str = ""
    admin_token: str = ""
    
    # App
    app_version: str = "2.2.0"
    
    @property
    def is_production(self) -> bool:
        return self.env.lower() not in {"dev", "local", "test"}
    
    @property
    def is_development(self) -> bool:
        return self.env.lower() in {"dev", "local"}
    
    def validate_critical_production(self) -> None:
        \"\"\"Valida configurações críticas em produção\"\"\"
        if self.is_production:
            if not self.pipefy_token:
                raise ValueError("PIPEFY_TOKEN é obrigatório em produção")
            if not self.webhook_secret:
                raise ValueError("WEBHOOK_SECRET é obrigatório em produção")
            if not self.admin_token:
                raise ValueError("ADMIN_TOKEN é obrigatório em produção")
            if self.auto_create_tables:
                raise ValueError("AUTO_CREATE_TABLES deve ser false em produção")

settings = Settings()
