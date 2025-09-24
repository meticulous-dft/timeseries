"""Core data generation engine for MongoDB time series data."""

import logging
import random
import string
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

from config import data_config
from data_generators import (
    ApplicationMetricGenerator,
    CPUMetricGenerator,
    DiskMetricGenerator,
    HostGenerator,
    MemoryMetricGenerator,
    NetworkMetricGenerator,
)
from models import TimeSeriesDocument

logger = logging.getLogger(__name__)


@dataclass
class GenerationStats:
    """Statistics for data generation process."""

    total_documents: int = 0
    documents_generated: int = 0
    bytes_generated: int = 0
    start_time: datetime = None
    end_time: datetime = None

    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def documents_per_second(self) -> float:
        if self.duration_seconds > 0:
            return self.documents_generated / self.duration_seconds
        return 0.0

    @property
    def mb_per_second(self) -> float:
        if self.duration_seconds > 0:
            return (self.bytes_generated / 1024 / 1024) / self.duration_seconds
        return 0.0


class DocumentSizeController:
    """Controls document size to meet target requirements."""

    def __init__(self, target_size_kb: float, variance: float = 0.2):
        self.target_size_bytes = int(target_size_kb * 1024)
        self.variance = variance
        self.min_size = int(self.target_size_bytes * (1 - variance))
        self.max_size = int(self.target_size_bytes * (1 + variance))

    def calculate_padding_size(self, base_document: Dict[str, Any]) -> int:
        """Calculate padding needed to reach target document size."""
        import json

        base_size = len(json.dumps(base_document, default=str).encode("utf-8"))

        # Random target size within variance range
        target_size = random.randint(self.min_size, self.max_size)

        padding_needed = max(
            0, target_size - base_size - 20
        )  # 20 bytes for padding field overhead
        return padding_needed

    def generate_padding(self, size: int) -> str:
        """Generate random padding string of specified size."""
        if size <= 0:
            return ""

        # Use a mix of characters to make padding realistic
        chars = (
            string.ascii_letters + string.digits + " " * 10
        )  # More spaces for realism
        return "".join(random.choices(chars, k=size))


class TimeSeriesDataGenerator:
    """Main time series data generator."""

    def __init__(self):
        self.stats = GenerationStats()
        self.size_controller = DocumentSizeController(
            data_config.document_size_kb, data_config.document_size_variance
        )
        self._lock = threading.Lock()

        # Parse time range
        self.start_time = datetime.fromisoformat(
            data_config.start_time.replace("Z", "+00:00")
        )
        self.end_time = datetime.fromisoformat(
            data_config.end_time.replace("Z", "+00:00")
        )
        self.time_interval = timedelta(seconds=data_config.time_interval_seconds)

        # Calculate total time points
        total_duration = self.end_time - self.start_time
        self.total_time_points = int(
            total_duration.total_seconds() / data_config.time_interval_seconds
        )

        logger.info(f"Time range: {self.start_time} to {self.end_time}")
        logger.info(f"Total time points: {self.total_time_points}")
        logger.info(f"Target documents: {data_config.total_documents}")

    def _create_host_generators(self, host_id: int) -> Dict[str, Any]:
        """Create metric generators for a host."""
        generators = {
            "cpu": CPUMetricGenerator(host_id, self.start_time),
            "mem": MemoryMetricGenerator(host_id, self.start_time),
            "disk": DiskMetricGenerator(host_id, self.start_time),
            "net": NetworkMetricGenerator(host_id, self.start_time),
            "app": ApplicationMetricGenerator(host_id, self.start_time),
        }
        return generators

    def generate_document(
        self,
        host_id: int,
        timestamp: datetime,
        metric_type: str,
        generators: Dict[str, Any],
    ) -> TimeSeriesDocument:
        """Generate a single time series document."""

        # Generate host metadata (cached per host)
        host_tags = HostGenerator.generate_host_tags(host_id)

        # Generate metric data based on type
        if metric_type == "cpu":
            fields = generators["cpu"].generate(timestamp)
        elif metric_type == "mem":
            fields = generators["mem"].generate(timestamp)
        elif metric_type == "disk":
            fields = generators["disk"].generate(timestamp)
        elif metric_type == "net":
            fields = generators["net"].generate(timestamp)
        elif metric_type == "diskio":
            fields = generators["app"].generate_diskio_metrics(timestamp)
        elif metric_type == "kernel":
            fields = generators["app"].generate_kernel_metrics(timestamp)
        elif metric_type == "nginx":
            fields = generators["app"].generate_nginx_metrics(timestamp)
        elif metric_type == "postgresql":
            fields = generators["app"].generate_postgresql_metrics(timestamp)
        elif metric_type == "redis":
            fields = generators["app"].generate_redis_metrics(timestamp)
        elif metric_type == "process":
            fields = generators["app"].generate_process_metrics(timestamp)
        elif metric_type == "filesystem":
            fields = generators["app"].generate_filesystem_metrics(timestamp)
        elif metric_type == "system":
            fields = generators["app"].generate_system_metrics(timestamp)
        elif metric_type == "docker":
            fields = generators["app"].generate_docker_metrics(timestamp)
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")

        # Create base document
        doc = TimeSeriesDocument(
            timestamp=timestamp,
            metadata=host_tags,
            measurement=metric_type,
            fields=fields,
        )

        # Add padding to control document size
        base_dict = doc.to_mongo_dict()
        padding_size = self.size_controller.calculate_padding_size(base_dict)

        if padding_size > 0:
            doc.padding = self.size_controller.generate_padding(padding_size)

        return doc

    def generate_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Generate a batch of documents."""
        documents = []
        metric_types = [
            "cpu",
            "mem",
            "disk",
            "net",
            "diskio",
            "kernel",
            "nginx",
            "postgresql",
            "redis",
            "process",
            "filesystem",
            "system",
            "docker",
        ]

        # Create generators for hosts in this batch
        host_generators = {}

        for _ in range(batch_size):
            # Select random host, timestamp, and metric type
            host_id = random.randint(0, data_config.host_count - 1)
            time_offset = random.randint(0, self.total_time_points - 1)
            timestamp = self.start_time + (time_offset * self.time_interval)
            metric_type = random.choice(metric_types)

            # Create generators for this host if not exists
            if host_id not in host_generators:
                host_generators[host_id] = self._create_host_generators(host_id)

            # Generate document
            try:
                doc = self.generate_document(
                    host_id, timestamp, metric_type, host_generators[host_id]
                )
                doc_dict = doc.to_mongo_dict()
                documents.append(doc_dict)

                # Update stats
                with self._lock:
                    self.stats.documents_generated += 1
                    import json

                    doc_size = len(json.dumps(doc_dict, default=str).encode("utf-8"))
                    self.stats.bytes_generated += doc_size

            except Exception as e:
                logger.error(f"Error generating document: {e}")
                continue

        return documents

    def generate_time_series_batch(
        self, host_ids: List[int], start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Generate time series data for specific hosts and time range."""
        documents = []
        metric_types = [
            "cpu",
            "mem",
            "disk",
            "net",
            "diskio",
            "kernel",
            "nginx",
            "postgresql",
            "redis",
            "process",
            "filesystem",
            "system",
            "docker",
        ]

        # Create generators for all hosts
        host_generators = {
            host_id: self._create_host_generators(host_id) for host_id in host_ids
        }

        # Generate documents for each time point
        current_time = start_time
        while current_time <= end_time:
            for host_id in host_ids:
                for metric_type in metric_types:
                    try:
                        doc = self.generate_document(
                            host_id, current_time, metric_type, host_generators[host_id]
                        )
                        documents.append(doc.to_mongo_dict())

                        # Update stats
                        with self._lock:
                            self.stats.documents_generated += 1
                            import json

                            doc_size = len(
                                json.dumps(doc.to_mongo_dict(), default=str).encode(
                                    "utf-8"
                                )
                            )
                            self.stats.bytes_generated += doc_size

                    except Exception as e:
                        logger.error(f"Error generating document: {e}")
                        continue

            current_time += self.time_interval

        return documents

    def get_stats(self) -> GenerationStats:
        """Get current generation statistics."""
        with self._lock:
            return self.stats
