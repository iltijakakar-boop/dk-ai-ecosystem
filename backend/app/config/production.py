from app.config.settings import Settings

class ProductionSettings(Settings):
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

prod_settings = ProductionSettings()
