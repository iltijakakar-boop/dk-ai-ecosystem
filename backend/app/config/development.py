from app.config.settings import Settings

class DevelopmentSettings(Settings):
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

dev_settings = DevelopmentSettings()
