import pydantic_settings


class Config(pydantic_settings.BaseSettings):
    DAY_FILENAME_TEMPLATE: str = (
        "STAR_{operation_day:%Y%m%d}_{serial}_Day_{now:%Y%m%d%H%M%S}.xml"
    )
    INTERVAL_FILENAME_TEMPLATE: str = (
        "STAR_{operation_day:%Y%m%d}_{serial}_Interval_{now:%Y%m%d%H%M%S}.xml"
    )


settings = Config()
