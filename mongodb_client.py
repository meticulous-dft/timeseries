"""MongoDB client for time series data operations."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pymongo
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from pymongo.database import Database
from config import mongo_config, app_config

logger = logging.getLogger(__name__)


class MongoDBTimeSeriesClient:
    """MongoDB client optimized for time series operations."""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            logger.info(f"Connecting to MongoDB: {mongo_config.database_name}")
            
            # Create client with optimized settings for bulk operations
            self.client = MongoClient(
                mongo_config.connection_string,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                waitQueueTimeoutMS=5000,
                serverSelectionTimeoutMS=10000,
                socketTimeoutMS=20000,
                connectTimeoutMS=20000,
                retryWrites=True,
                w="majority",
                readPreference="primary"
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.database = self.client[mongo_config.database_name]
            self.collection = self.database[mongo_config.collection_name]
            
            self._connected = True
            logger.info("Successfully connected to MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        return self._connected and self.client is not None
    
    def create_time_series_collection(self) -> bool:
        """Create time series collection with proper configuration."""
        try:
            if not self.is_connected():
                raise Exception("Not connected to MongoDB")
            
            # Check if collection already exists
            if mongo_config.collection_name in self.database.list_collection_names():
                logger.info(f"Collection {mongo_config.collection_name} already exists")
                return True
            
            # Create time series collection
            logger.info(f"Creating time series collection: {mongo_config.collection_name}")
            
            self.database.create_collection(
                mongo_config.collection_name,
                timeseries={
                    "timeField": "timestamp",
                    "metaField": "metadata",
                    "granularity": "minutes"  # Optimized for minute-level data
                }
            )
            
            logger.info("Time series collection created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create time series collection: {e}")
            return False
    
    def create_indexes(self) -> bool:
        """Create recommended indexes for time series queries."""
        try:
            if not self.is_connected():
                raise Exception("Not connected to MongoDB")
            
            logger.info("Creating indexes for time series collection")
            
            # Compound index on metadata fields for efficient querying
            self.collection.create_index([
                ("metadata.hostname", 1),
                ("timestamp", 1)
            ], name="hostname_timestamp_idx")
            
            self.collection.create_index([
                ("metadata.region", 1),
                ("metadata.datacenter", 1),
                ("timestamp", 1)
            ], name="region_datacenter_timestamp_idx")
            
            self.collection.create_index([
                ("metadata.service", 1),
                ("metadata.service_environment", 1),
                ("timestamp", 1)
            ], name="service_environment_timestamp_idx")
            
            self.collection.create_index([
                ("measurement", 1),
                ("timestamp", 1)
            ], name="measurement_timestamp_idx")
            
            # Index for time range queries
            self.collection.create_index([
                ("timestamp", 1)
            ], name="timestamp_idx")
            
            logger.info("Indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False
    
    def setup_sharding(self) -> bool:
        """Setup sharding for the time series collection."""
        try:
            if not self.is_connected():
                raise Exception("Not connected to MongoDB")
            
            if not app_config.enable_sharding:
                logger.info("Sharding disabled in configuration")
                return True
            
            logger.info("Setting up sharding for time series collection")
            
            # Enable sharding on database
            try:
                self.client.admin.command("enableSharding", mongo_config.database_name)
            except errors.OperationFailure as e:
                if "already enabled" not in str(e):
                    raise
            
            # Shard the collection using compound shard key
            # This distributes data across shards based on hostname and timestamp
            shard_key = {
                "metadata.hostname": "hashed",
                "timestamp": 1
            }
            
            try:
                self.client.admin.command(
                    "shardCollection",
                    f"{mongo_config.database_name}.{mongo_config.collection_name}",
                    key=shard_key
                )
                logger.info("Sharding configured successfully")
            except errors.OperationFailure as e:
                if "already sharded" not in str(e):
                    logger.warning(f"Sharding setup failed (may not be available): {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup sharding: {e}")
            return False
    
    def insert_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Insert documents in batch."""
        try:
            if not self.is_connected():
                raise Exception("Not connected to MongoDB")
            
            if not documents:
                return True
            
            # Use ordered=False for better performance
            result = self.collection.insert_many(documents, ordered=False)
            
            if len(result.inserted_ids) != len(documents):
                logger.warning(f"Expected {len(documents)} inserts, got {len(result.inserted_ids)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert documents: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            if not self.is_connected():
                return {}
            
            stats = self.database.command("collStats", mongo_config.collection_name)
            return {
                "document_count": stats.get("count", 0),
                "size_bytes": stats.get("size", 0),
                "storage_size_bytes": stats.get("storageSize", 0),
                "avg_document_size": stats.get("avgObjSize", 0),
                "indexes": stats.get("nindexes", 0),
                "index_size_bytes": stats.get("totalIndexSize", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def drop_collection(self) -> bool:
        """Drop the time series collection."""
        try:
            if not self.is_connected():
                raise Exception("Not connected to MongoDB")
            
            self.collection.drop()
            logger.info(f"Collection {mongo_config.collection_name} dropped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop collection: {e}")
            return False
