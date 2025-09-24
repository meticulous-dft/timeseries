"""Data models for MongoDB Time Series Data Generator."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics that can be generated."""

    CPU = "cpu"
    MEMORY = "mem"
    DISK = "disk"
    DISKIO = "diskio"
    NETWORK = "net"
    KERNEL = "kernel"
    NGINX = "nginx"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    PROCESS = "process"
    FILESYSTEM = "filesystem"
    SYSTEM = "system"
    DOCKER = "docker"


class Region(str, Enum):
    """AWS-like regions for host simulation."""

    US_EAST_1 = "us-east-1"
    US_WEST_1 = "us-west-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    EU_CENTRAL_1 = "eu-central-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_SOUTHEAST_2 = "ap-southeast-2"
    AP_NORTHEAST_1 = "ap-northeast-1"
    SA_EAST_1 = "sa-east-1"


class HostTags(BaseModel):
    """Host metadata tags following TSBS DevOps format."""

    hostname: str
    region: str
    datacenter: str
    rack: str
    os: str
    arch: str
    team: str
    service: str
    service_version: str
    service_environment: str

    # Additional infrastructure metadata
    instance_type: str
    instance_size: str
    availability_zone: str
    vpc_id: str
    subnet_id: str
    security_groups: List[str]

    # Hardware specifications
    cpu_cores: int
    cpu_model: str
    memory_gb: int
    storage_type: str
    storage_size_gb: int
    network_interface: str

    # Operational metadata
    deployment_id: str
    cluster_name: str
    node_role: str
    monitoring_enabled: bool
    backup_enabled: bool
    auto_scaling_group: str

    # Cost and billing
    cost_center: str
    project_code: str
    owner: str
    billing_tag: str

    # Compliance and security
    compliance_level: str
    encryption_enabled: bool
    patch_group: str
    maintenance_window: str


class CPUMetrics(BaseModel):
    """CPU-related metrics."""

    usage_user: float = Field(ge=0.0, le=100.0)
    usage_system: float = Field(ge=0.0, le=100.0)
    usage_idle: float = Field(ge=0.0, le=100.0)
    usage_nice: float = Field(ge=0.0, le=100.0)
    usage_iowait: float = Field(ge=0.0, le=100.0)
    usage_irq: float = Field(ge=0.0, le=100.0)
    usage_softirq: float = Field(ge=0.0, le=100.0)
    usage_steal: float = Field(ge=0.0, le=100.0)
    usage_guest: float = Field(ge=0.0, le=100.0)
    usage_guest_nice: float = Field(ge=0.0, le=100.0)

    # Additional CPU metrics
    load_average_1m: float = Field(ge=0.0)
    load_average_5m: float = Field(ge=0.0)
    load_average_15m: float = Field(ge=0.0)
    cpu_count: int = Field(ge=1)
    cpu_frequency_mhz: float = Field(ge=0.0)
    cpu_temperature_celsius: float = Field(ge=0.0, le=100.0)
    context_switches_per_sec: int = Field(ge=0)
    interrupts_per_sec: int = Field(ge=0)
    processes_running: int = Field(ge=0)
    processes_blocked: int = Field(ge=0)
    cpu_utilization_per_core: List[float] = Field(default_factory=list)


class MemoryMetrics(BaseModel):
    """Memory-related metrics."""

    total: int = Field(ge=0)
    available: int = Field(ge=0)
    used: int = Field(ge=0)
    free: int = Field(ge=0)
    cached: int = Field(ge=0)
    buffered: int = Field(ge=0)
    used_percent: float = Field(ge=0.0, le=100.0)
    available_percent: float = Field(ge=0.0, le=100.0)

    # Additional memory metrics
    shared: int = Field(ge=0)
    slab: int = Field(ge=0)
    page_tables: int = Field(ge=0)
    swap_total: int = Field(ge=0)
    swap_used: int = Field(ge=0)
    swap_free: int = Field(ge=0)
    swap_used_percent: float = Field(ge=0.0, le=100.0)
    dirty: int = Field(ge=0)
    writeback: int = Field(ge=0)
    mapped: int = Field(ge=0)
    vmalloc_total: int = Field(ge=0)
    vmalloc_used: int = Field(ge=0)
    vmalloc_chunk: int = Field(ge=0)
    huge_pages_total: int = Field(ge=0)
    huge_pages_free: int = Field(ge=0)
    huge_page_size: int = Field(ge=0)
    commit_limit: int = Field(ge=0)
    committed_as: int = Field(ge=0)


class DiskMetrics(BaseModel):
    """Disk usage metrics."""

    total: int = Field(ge=0)
    free: int = Field(ge=0)
    used: int = Field(ge=0)
    used_percent: float = Field(ge=0.0, le=100.0)
    inodes_total: int = Field(ge=0)
    inodes_free: int = Field(ge=0)
    inodes_used: int = Field(ge=0)

    # Additional disk metrics
    inodes_used_percent: float = Field(ge=0.0, le=100.0)
    device_name: str = Field(default="/dev/sda1")
    mount_point: str = Field(default="/")
    filesystem_type: str = Field(default="ext4")
    read_time_ms: int = Field(ge=0)
    write_time_ms: int = Field(ge=0)
    io_time_ms: int = Field(ge=0)
    weighted_io_time_ms: int = Field(ge=0)
    disk_queue_length: int = Field(ge=0)
    disk_service_time_ms: float = Field(ge=0.0)
    disk_utilization_percent: float = Field(ge=0.0, le=100.0)


class DiskIOMetrics(BaseModel):
    """Disk I/O metrics."""

    reads: int = Field(ge=0)
    writes: int = Field(ge=0)
    read_bytes: int = Field(ge=0)
    write_bytes: int = Field(ge=0)
    read_time: int = Field(ge=0)
    write_time: int = Field(ge=0)
    io_time: int = Field(ge=0)


class NetworkMetrics(BaseModel):
    """Network interface metrics."""

    bytes_sent: int = Field(ge=0)
    bytes_recv: int = Field(ge=0)
    packets_sent: int = Field(ge=0)
    packets_recv: int = Field(ge=0)
    err_in: int = Field(ge=0)
    err_out: int = Field(ge=0)
    drop_in: int = Field(ge=0)
    drop_out: int = Field(ge=0)

    # Additional network metrics
    interface_name: str = Field(default="eth0")
    interface_speed_mbps: int = Field(ge=0)
    duplex_mode: str = Field(default="full")
    mtu_size: int = Field(ge=0)
    bytes_sent_per_sec: float = Field(ge=0.0)
    bytes_recv_per_sec: float = Field(ge=0.0)
    packets_sent_per_sec: float = Field(ge=0.0)
    packets_recv_per_sec: float = Field(ge=0.0)
    collisions: int = Field(ge=0)
    multicast: int = Field(ge=0)
    carrier_errors: int = Field(ge=0)
    frame_errors: int = Field(ge=0)
    fifo_errors: int = Field(ge=0)
    compressed_sent: int = Field(ge=0)
    compressed_recv: int = Field(ge=0)
    network_utilization_percent: float = Field(ge=0.0, le=100.0)
    tcp_connections_active: int = Field(ge=0)
    tcp_connections_passive: int = Field(ge=0)
    tcp_retransmissions: int = Field(ge=0)


class KernelMetrics(BaseModel):
    """Kernel-related metrics."""

    boot_time: int = Field(ge=0)
    interrupts: int = Field(ge=0)
    context_switches: int = Field(ge=0)
    processes_forked: int = Field(ge=0)
    disk_pages_in: int = Field(ge=0)
    disk_pages_out: int = Field(ge=0)


class NginxMetrics(BaseModel):
    """Nginx web server metrics."""

    accepts: int = Field(ge=0)
    active: int = Field(ge=0)
    handled: int = Field(ge=0)
    reading: int = Field(ge=0)
    requests: int = Field(ge=0)
    waiting: int = Field(ge=0)
    writing: int = Field(ge=0)


class PostgreSQLMetrics(BaseModel):
    """PostgreSQL database metrics."""

    numbackends: int = Field(ge=0)
    xact_commit: int = Field(ge=0)
    xact_rollback: int = Field(ge=0)
    blks_read: int = Field(ge=0)
    blks_hit: int = Field(ge=0)
    tup_returned: int = Field(ge=0)
    tup_fetched: int = Field(ge=0)
    tup_inserted: int = Field(ge=0)
    tup_updated: int = Field(ge=0)
    tup_deleted: int = Field(ge=0)


class RedisMetrics(BaseModel):
    """Redis cache metrics."""

    connected_clients: int = Field(ge=0)
    used_memory: int = Field(ge=0)
    used_memory_rss: int = Field(ge=0)
    used_memory_peak: int = Field(ge=0)
    used_memory_lua: int = Field(ge=0)
    rdb_changes_since_last_save: int = Field(ge=0)
    instantaneous_ops_per_sec: int = Field(ge=0)
    instantaneous_input_kbps: float = Field(ge=0.0)
    instantaneous_output_kbps: float = Field(ge=0.0)
    rejected_connections: int = Field(ge=0)


class ProcessMetrics(BaseModel):
    """Process-related metrics."""

    total_processes: int = Field(ge=0)
    running_processes: int = Field(ge=0)
    sleeping_processes: int = Field(ge=0)
    stopped_processes: int = Field(ge=0)
    zombie_processes: int = Field(ge=0)
    threads_total: int = Field(ge=0)
    forks_per_sec: float = Field(ge=0.0)
    context_switches_per_sec: float = Field(ge=0.0)


class FileSystemMetrics(BaseModel):
    """File system metrics."""

    open_files: int = Field(ge=0)
    max_open_files: int = Field(ge=0)
    open_files_percent: float = Field(ge=0.0, le=100.0)
    file_descriptors_used: int = Field(ge=0)
    file_descriptors_max: int = Field(ge=0)
    dentries: int = Field(ge=0)
    inodes_cached: int = Field(ge=0)


class SystemMetrics(BaseModel):
    """System-wide metrics."""

    uptime_seconds: int = Field(ge=0)
    boot_time: int = Field(ge=0)
    users_logged_in: int = Field(ge=0)
    system_calls_per_sec: float = Field(ge=0.0)
    page_faults_per_sec: float = Field(ge=0.0)
    major_page_faults_per_sec: float = Field(ge=0.0)
    entropy_available: int = Field(ge=0)


class DockerMetrics(BaseModel):
    """Docker container metrics."""

    containers_running: int = Field(ge=0)
    containers_paused: int = Field(ge=0)
    containers_stopped: int = Field(ge=0)
    images_total: int = Field(ge=0)
    volumes_total: int = Field(ge=0)
    networks_total: int = Field(ge=0)
    cpu_usage_percent: float = Field(ge=0.0, le=100.0)
    memory_usage_bytes: int = Field(ge=0)
    memory_limit_bytes: int = Field(ge=0)
    network_rx_bytes: int = Field(ge=0)
    network_tx_bytes: int = Field(ge=0)
    block_read_bytes: int = Field(ge=0)
    block_write_bytes: int = Field(ge=0)


class TimeSeriesDocument(BaseModel):
    """Main time series document structure for MongoDB."""

    # MongoDB time series required fields
    timestamp: datetime = Field(description="Measurement timestamp")
    metadata: HostTags = Field(description="Host metadata tags")

    # Measurement data - only one metric type per document
    measurement: str = Field(description="Measurement type (cpu, mem, disk, etc.)")
    fields: Dict[str, Union[int, float, str, bool, List[Union[int, float, str]]]] = (
        Field(description="Metric values")
    )

    # Additional fields for document size control
    padding: Optional[str] = Field(
        default=None, description="Padding to control document size"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Convert to MongoDB document format."""
        doc = {
            "timestamp": self.timestamp,
            "metadata": self.metadata.dict(),
            "measurement": self.measurement,
            "fields": self.fields,
        }

        if self.padding:
            doc["padding"] = self.padding

        return doc
