from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    env: str
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()

"""
What it does (The breakdown)

    Look for a file: It looks for a file named .env in your project folder.

    Read and Match: It looks for lines in that file that match the names app_name, env, and log_level.

    Validate: It checks that the data is the right type. For example, if app_name is missing in your .env file, the program will crash immediately with a helpful error rather than failing later mysteriously.

    Set Defaults: If log_level isn't found in the file, it automatically sets it to "INFO".
"""