"""Configuration settings for MongoDB Time Series Data Generator."""

import os

try:
    from pydantic import Field, validator
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()


class MongoConfig(BaseSettings):
    """MongoDB connection configuration."""

    connection_string: str = Field(
        default_factory=lambda: os.getenv(
            "MONGODB_CONNECTION_STRING", "mongodb://localhost:27017"
        ),
        description="MongoDB connection string",
    )
    database_name: str = Field(
        default="tsbs_benchmark", description="Database name for time series data"
    )
    collection_name: str = Field(
        default="devops_metrics", description="Collection name for time series data"
    )

    class Config:
        env_prefix = "MONGO_"


class DataGenerationConfig(BaseSettings):
    """Data generation configuration."""

    # Data volume settings
    total_documents: int = Field(
        default=1000000, description="Total number of documents to generate"
    )
    document_size_kb: float = Field(
        default=1.0, description="Target document size in KB (uniformly distributed)"
    )
    document_size_variance: float = Field(
        default=0.2,
        description="Variance in document size (0.0 = no variance, 1.0 = high variance)",
    )

    # Time series settings
    start_time: str = Field(
        default="2024-01-01T00:00:00Z",
        description="Start time for time series data (ISO format)",
    )
    end_time: str = Field(
        default="2024-12-31T23:59:59Z",
        description="End time for time series data (ISO format)",
    )
    time_interval_seconds: int = Field(
        default=60, description="Time interval between measurements in seconds"
    )

    # Host/device settings
    host_count: int = Field(
        default=1000, description="Number of simulated hosts/devices"
    )
    metrics_per_host: int = Field(
        default=9, description="Number of different metric types per host"
    )

    # Performance settings
    batch_size: int = Field(
        default=1000, description="Number of documents to insert in each batch"
    )
    parallel_workers: int = Field(
        default=4, description="Number of parallel worker threads"
    )

    class Config:
        env_prefix = "DATA_"


class AppConfig(BaseSettings):
    """Application configuration."""

    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    progress_update_interval: int = Field(
        default=10000, description="Progress update interval in documents"
    )
    enable_sharding: bool = Field(
        default=True, description="Enable MongoDB sharding for time series collection"
    )
    create_indexes: bool = Field(
        default=True, description="Create recommended indexes for time series queries"
    )

    class Config:
        env_prefix = "APP_"


# Global configuration instances
mongo_config = MongoConfig()
data_config = DataGenerationConfig()
app_config = AppConfig()
