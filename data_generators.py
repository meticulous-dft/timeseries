"""Data generators for creating realistic time series metrics."""

import math
import random
from datetime import datetime
from typing import Any, Dict

from faker import Faker

from models import HostTags, Region

fake = Faker()


class HostGenerator:
    """Generates realistic host metadata."""

    # Static choices for host attributes
    OS_CHOICES = [
        "Ubuntu16.10",
        "Ubuntu16.04LTS",
        "Ubuntu15.10",
        "CentOS7",
        "RHEL8",
        "Amazon Linux 2",
    ]
    ARCH_CHOICES = ["x64", "x86", "arm64"]
    TEAM_CHOICES = ["SF", "NYC", "LON", "CHI", "TKY", "SYD", "BER", "TOR"]
    SERVICE_ENVIRONMENT_CHOICES = ["production", "staging", "test", "development", "qa"]

    # Additional choices for new metadata fields
    INSTANCE_TYPES = [
        "t3.micro",
        "t3.small",
        "t3.medium",
        "t3.large",
        "m5.large",
        "m5.xlarge",
        "c5.large",
        "r5.large",
    ]
    INSTANCE_SIZES = ["micro", "small", "medium", "large", "xlarge", "2xlarge"]
    STORAGE_TYPES = ["gp3", "gp2", "io1", "io2", "st1", "sc1"]
    NETWORK_INTERFACES = ["eth0", "ens5", "enp0s3", "wlan0"]
    NODE_ROLES = ["master", "worker", "etcd", "ingress", "storage"]
    COMPLIANCE_LEVELS = ["SOC2", "PCI-DSS", "HIPAA", "ISO27001", "FedRAMP"]
    PATCH_GROUPS = ["critical", "standard", "delayed", "manual"]
    MAINTENANCE_WINDOWS = [
        "sunday-2am",
        "saturday-3am",
        "weekday-11pm",
        "monthly-first-sunday",
    ]
    CPU_MODELS = [
        "Intel Xeon E5-2686 v4",
        "Intel Xeon Platinum 8175M",
        "AMD EPYC 7571",
        "ARM Graviton2",
    ]

    # Region to datacenter mapping
    REGION_DATACENTERS = {
        Region.US_EAST_1: ["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1e"],
        Region.US_WEST_1: ["us-west-1a", "us-west-1b"],
        Region.US_WEST_2: ["us-west-2a", "us-west-2b", "us-west-2c"],
        Region.EU_WEST_1: ["eu-west-1a", "eu-west-1b", "eu-west-1c"],
        Region.EU_CENTRAL_1: ["eu-central-1a", "eu-central-1b"],
        Region.AP_SOUTHEAST_1: ["ap-southeast-1a", "ap-southeast-1b"],
        Region.AP_SOUTHEAST_2: ["ap-southeast-2a", "ap-southeast-2b"],
        Region.AP_NORTHEAST_1: ["ap-northeast-1a", "ap-northeast-1c"],
        Region.SA_EAST_1: ["sa-east-1a", "sa-east-1b", "sa-east-1c"],
    }

    @classmethod
    def generate_host_tags(cls, host_id: int) -> HostTags:
        """Generate host metadata tags."""
        region = random.choice(list(Region))
        datacenter = random.choice(cls.REGION_DATACENTERS[region])
        instance_type = random.choice(cls.INSTANCE_TYPES)
        cpu_model = random.choice(cls.CPU_MODELS)

        # Derive some fields from instance type
        if "micro" in instance_type:
            cpu_cores, memory_gb, storage_size = 1, 1, 8
        elif "small" in instance_type:
            cpu_cores, memory_gb, storage_size = 1, 2, 20
        elif "medium" in instance_type:
            cpu_cores, memory_gb, storage_size = 2, 4, 30
        elif "large" in instance_type:
            cpu_cores, memory_gb, storage_size = 2, 8, 50
        else:
            cpu_cores, memory_gb, storage_size = 4, 16, 100

        return HostTags(
            hostname=f"host_{host_id}",
            region=region.value,
            datacenter=datacenter,
            rack=str(random.randint(1, 100)),
            os=random.choice(cls.OS_CHOICES),
            arch=random.choice(cls.ARCH_CHOICES),
            team=random.choice(cls.TEAM_CHOICES),
            service=str(random.randint(1, 20)),
            service_version=str(random.randint(1, 2)),
            service_environment=random.choice(cls.SERVICE_ENVIRONMENT_CHOICES),
            # Additional infrastructure metadata
            instance_type=instance_type,
            instance_size=random.choice(cls.INSTANCE_SIZES),
            availability_zone=f"{region.value}{random.choice(['a', 'b', 'c'])}",
            vpc_id=f"vpc-{fake.hexify(text='^^^^^^^^')}",
            subnet_id=f"subnet-{fake.hexify(text='^^^^^^^^')}",
            security_groups=[
                f"sg-{fake.hexify(text='^^^^^^^^')}"
                for _ in range(random.randint(1, 3))
            ],
            # Hardware specifications
            cpu_cores=cpu_cores,
            cpu_model=cpu_model,
            memory_gb=memory_gb,
            storage_type=random.choice(cls.STORAGE_TYPES),
            storage_size_gb=storage_size,
            network_interface=random.choice(cls.NETWORK_INTERFACES),
            # Operational metadata
            deployment_id=f"deploy-{fake.hexify(text='^^^^^^^^')}",
            cluster_name=f"cluster-{random.choice(['prod', 'staging', 'dev'])}-{random.randint(1, 5)}",
            node_role=random.choice(cls.NODE_ROLES),
            monitoring_enabled=random.choice([True, False]),
            backup_enabled=random.choice([True, False]),
            auto_scaling_group=f"asg-{fake.word()}-{random.randint(1, 10)}",
            # Cost and billing
            cost_center=f"CC-{random.randint(1000, 9999)}",
            project_code=f"PROJ-{fake.word().upper()}-{random.randint(100, 999)}",
            owner=fake.email(),
            billing_tag=f"billing-{fake.word()}",
            # Compliance and security
            compliance_level=random.choice(cls.COMPLIANCE_LEVELS),
            encryption_enabled=random.choice([True, False]),
            patch_group=random.choice(cls.PATCH_GROUPS),
            maintenance_window=random.choice(cls.MAINTENANCE_WINDOWS),
        )


class MetricGenerator:
    """Base class for metric generators with realistic patterns."""

    def __init__(self, host_id: int, base_timestamp: datetime):
        self.host_id = host_id
        self.base_timestamp = base_timestamp
        self.random = random.Random(host_id)  # Deterministic randomness per host

    def add_noise(self, value: float, noise_factor: float = 0.1) -> float:
        """Add realistic noise to a metric value."""
        noise = self.random.gauss(0, value * noise_factor)
        return max(0, value + noise)

    def generate_seasonal_pattern(
        self, timestamp: datetime, base_value: float, amplitude: float = 0.2
    ) -> float:
        """Generate seasonal patterns (daily/weekly cycles)."""
        # Daily pattern (peak during business hours)
        hour_of_day = timestamp.hour
        daily_factor = 1 + amplitude * math.sin((hour_of_day - 6) * math.pi / 12)

        # Weekly pattern (lower on weekends)
        day_of_week = timestamp.weekday()
        weekly_factor = 0.7 if day_of_week >= 5 else 1.0

        return base_value * daily_factor * weekly_factor


class CPUMetricGenerator(MetricGenerator):
    """Generates realistic CPU metrics."""

    def generate(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate CPU metrics for a given timestamp."""
        # Base CPU usage with seasonal patterns
        base_usage = self.generate_seasonal_pattern(timestamp, 30.0, 0.3)
        base_usage = self.add_noise(base_usage, 0.2)

        # Ensure CPU percentages add up to 100%
        usage_user = max(5.0, min(80.0, base_usage))
        usage_system = max(2.0, min(20.0, base_usage * 0.3))
        usage_iowait = max(0.0, min(10.0, self.random.uniform(0, 5)))
        usage_nice = max(0.0, min(5.0, self.random.uniform(0, 2)))
        usage_irq = max(0.0, min(2.0, self.random.uniform(0, 1)))
        usage_softirq = max(0.0, min(2.0, self.random.uniform(0, 1)))
        usage_steal = max(0.0, min(5.0, self.random.uniform(0, 2)))
        usage_guest = max(0.0, min(5.0, self.random.uniform(0, 2)))
        usage_guest_nice = max(0.0, min(2.0, self.random.uniform(0, 1)))

        # Calculate idle to make total = 100%
        used_total = (
            usage_user
            + usage_system
            + usage_iowait
            + usage_nice
            + usage_irq
            + usage_softirq
            + usage_steal
            + usage_guest
            + usage_guest_nice
        )
        usage_idle = max(0.0, 100.0 - used_total)

        # Additional CPU metrics
        load_1m = self.add_noise(base_usage / 20.0, 0.3)
        load_5m = self.add_noise(load_1m * 0.9, 0.2)
        load_15m = self.add_noise(load_5m * 0.8, 0.1)

        cpu_count = self.random.choice([1, 2, 4, 8, 16])
        cpu_freq = self.random.uniform(2000, 3500)  # MHz
        cpu_temp = self.add_noise(45.0, 0.3)  # Celsius

        context_switches = int(self.add_noise(50000, 0.5))
        interrupts = int(self.add_noise(10000, 0.4))
        processes_running = self.random.randint(1, 20)
        processes_blocked = self.random.randint(0, 5)

        # Per-core utilization
        per_core_util = [
            max(0.0, min(100.0, self.add_noise(base_usage, 0.3)))
            for _ in range(cpu_count)
        ]

        return {
            "usage_user": round(usage_user, 2),
            "usage_system": round(usage_system, 2),
            "usage_idle": round(usage_idle, 2),
            "usage_nice": round(usage_nice, 2),
            "usage_iowait": round(usage_iowait, 2),
            "usage_irq": round(usage_irq, 2),
            "usage_softirq": round(usage_softirq, 2),
            "usage_steal": round(usage_steal, 2),
            "usage_guest": round(usage_guest, 2),
            "usage_guest_nice": round(usage_guest_nice, 2),
            # Additional CPU metrics
            "load_average_1m": round(load_1m, 2),
            "load_average_5m": round(load_5m, 2),
            "load_average_15m": round(load_15m, 2),
            "cpu_count": cpu_count,
            "cpu_frequency_mhz": round(cpu_freq, 1),
            "cpu_temperature_celsius": round(max(20.0, min(85.0, cpu_temp)), 1),
            "context_switches_per_sec": max(0, context_switches),
            "interrupts_per_sec": max(0, interrupts),
            "processes_running": processes_running,
            "processes_blocked": processes_blocked,
            "cpu_utilization_per_core": [round(u, 2) for u in per_core_util],
        }


class MemoryMetricGenerator(MetricGenerator):
    """Generates realistic memory metrics."""

    def __init__(self, host_id: int, base_timestamp: datetime):
        super().__init__(host_id, base_timestamp)
        # Each host has a fixed total memory
        self.total_memory = self.random.choice(
            [
                8 * 1024**3,  # 8GB
                16 * 1024**3,  # 16GB
                32 * 1024**3,  # 32GB
                64 * 1024**3,  # 64GB
            ]
        )

    def generate(self, timestamp: datetime) -> Dict[str, int | float]:
        """Generate memory metrics for a given timestamp."""
        # Memory usage with seasonal patterns
        base_usage_percent = self.generate_seasonal_pattern(timestamp, 60.0, 0.2)
        base_usage_percent = max(
            20.0, min(90.0, self.add_noise(base_usage_percent, 0.1))
        )

        used = int(self.total_memory * base_usage_percent / 100)
        cached = int(self.total_memory * self.random.uniform(0.05, 0.15))
        buffered = int(self.total_memory * self.random.uniform(0.02, 0.08))
        available = self.total_memory - used
        free = available - cached - buffered

        return {
            "total": self.total_memory,
            "available": max(0, available),
            "used": used,
            "free": max(0, free),
            "cached": cached,
            "buffered": buffered,
            "used_percent": round(base_usage_percent, 2),
            "available_percent": round((available / self.total_memory) * 100, 2),
        }


class DiskMetricGenerator(MetricGenerator):
    """Generates realistic disk usage metrics."""

    def __init__(self, host_id: int, base_timestamp: datetime):
        super().__init__(host_id, base_timestamp)
        # Each host has a fixed disk size
        self.total_disk = self.random.choice(
            [
                100 * 1024**3,  # 100GB
                500 * 1024**3,  # 500GB
                1 * 1024**4,  # 1TB
                2 * 1024**4,  # 2TB
            ]
        )
        self.inodes_total = self.random.randint(1000000, 10000000)

    def generate(self, timestamp: datetime) -> Dict[str, int | float]:
        """Generate disk metrics for a given timestamp."""
        # Disk usage grows slowly over time
        days_since_start = (timestamp - self.base_timestamp).days
        growth_factor = 1 + (days_since_start * 0.001)  # 0.1% growth per day

        base_usage_percent = min(85.0, 40.0 * growth_factor)
        base_usage_percent = self.add_noise(base_usage_percent, 0.05)

        used = int(self.total_disk * base_usage_percent / 100)
        free = self.total_disk - used

        inodes_used = int(self.inodes_total * base_usage_percent / 100)
        inodes_free = self.inodes_total - inodes_used

        return {
            "total": self.total_disk,
            "free": free,
            "used": used,
            "used_percent": round(base_usage_percent, 2),
            "inodes_total": self.inodes_total,
            "inodes_free": inodes_free,
            "inodes_used": inodes_used,
        }


class NetworkMetricGenerator(MetricGenerator):
    """Generates realistic network metrics."""

    def __init__(self, host_id: int, base_timestamp: datetime):
        super().__init__(host_id, base_timestamp)
        self.cumulative_bytes_sent = 0
        self.cumulative_bytes_recv = 0
        self.cumulative_packets_sent = 0
        self.cumulative_packets_recv = 0

    def generate(self, timestamp: datetime) -> Dict[str, int]:
        """Generate network metrics for a given timestamp."""
        # Network activity with seasonal patterns
        base_activity = self.generate_seasonal_pattern(
            timestamp, 1000000, 0.4
        )  # 1MB base

        bytes_sent_delta = int(self.add_noise(base_activity, 0.3))
        bytes_recv_delta = int(
            self.add_noise(base_activity * 1.5, 0.3)
        )  # More incoming

        self.cumulative_bytes_sent += bytes_sent_delta
        self.cumulative_bytes_recv += bytes_recv_delta

        # Packets (roughly 1500 bytes per packet)
        packets_sent_delta = max(1, bytes_sent_delta // 1500)
        packets_recv_delta = max(1, bytes_recv_delta // 1500)

        self.cumulative_packets_sent += packets_sent_delta
        self.cumulative_packets_recv += packets_recv_delta

        return {
            "bytes_sent": self.cumulative_bytes_sent,
            "bytes_recv": self.cumulative_bytes_recv,
            "packets_sent": self.cumulative_packets_sent,
            "packets_recv": self.cumulative_packets_recv,
            "err_in": self.random.randint(0, 5),
            "err_out": self.random.randint(0, 5),
            "drop_in": self.random.randint(0, 10),
            "drop_out": self.random.randint(0, 10),
        }


class ApplicationMetricGenerator(MetricGenerator):
    """Generates realistic application-specific metrics."""

    def generate_nginx_metrics(self, timestamp: datetime) -> Dict[str, int]:
        """Generate Nginx web server metrics."""
        base_requests = self.generate_seasonal_pattern(timestamp, 1000, 0.5)
        base_requests = int(self.add_noise(base_requests, 0.3))

        return {
            "accepts": base_requests,
            "active": self.random.randint(1, 50),
            "handled": base_requests,
            "reading": self.random.randint(0, 10),
            "requests": base_requests,
            "waiting": self.random.randint(0, 20),
            "writing": self.random.randint(0, 15),
        }

    def generate_postgresql_metrics(self, timestamp: datetime) -> Dict[str, int]:
        """Generate PostgreSQL database metrics."""
        base_activity = self.generate_seasonal_pattern(timestamp, 100, 0.4)
        base_activity = int(self.add_noise(base_activity, 0.2))

        return {
            "numbackends": self.random.randint(1, 20),
            "xact_commit": base_activity * 10,
            "xact_rollback": max(0, int(base_activity * 0.1)),
            "blks_read": base_activity * 50,
            "blks_hit": base_activity * 500,
            "tup_returned": base_activity * 100,
            "tup_fetched": base_activity * 80,
            "tup_inserted": base_activity * 5,
            "tup_updated": base_activity * 3,
            "tup_deleted": max(0, int(base_activity * 0.5)),
        }

    def generate_redis_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate Redis cache metrics."""
        base_memory = 1024 * 1024 * 100  # 100MB base
        memory_usage = int(self.generate_seasonal_pattern(timestamp, base_memory, 0.3))

        return {
            "connected_clients": self.random.randint(1, 100),
            "used_memory": memory_usage,
            "used_memory_rss": int(memory_usage * 1.2),
            "used_memory_peak": int(memory_usage * 1.5),
            "used_memory_lua": self.random.randint(1000, 10000),
            "rdb_changes_since_last_save": self.random.randint(0, 1000),
            "instantaneous_ops_per_sec": self.random.randint(0, 1000),
            "instantaneous_input_kbps": round(self.random.uniform(0, 100), 2),
            "instantaneous_output_kbps": round(self.random.uniform(0, 100), 2),
            "rejected_connections": self.random.randint(0, 5),
        }

    def generate_kernel_metrics(self, timestamp: datetime) -> Dict[str, int]:
        """Generate kernel-related metrics."""
        return {
            "boot_time": int(self.base_timestamp.timestamp()),
            "interrupts": self.random.randint(1000000, 10000000),
            "context_switches": self.random.randint(100000, 1000000),
            "processes_forked": self.random.randint(1000, 10000),
            "disk_pages_in": self.random.randint(1000, 100000),
            "disk_pages_out": self.random.randint(1000, 100000),
        }

    def generate_diskio_metrics(self, timestamp: datetime) -> Dict[str, int]:
        """Generate disk I/O metrics."""
        base_io = self.generate_seasonal_pattern(timestamp, 1000, 0.3)
        base_io = int(self.add_noise(base_io, 0.2))

        return {
            "reads": base_io,
            "writes": int(base_io * 0.7),
            "read_bytes": base_io * 4096,  # 4KB per read
            "write_bytes": int(base_io * 0.7 * 4096),
            "read_time": base_io * 10,  # ms
            "write_time": int(base_io * 0.7 * 15),  # ms
            "io_time": base_io * 12,  # ms
        }

    def generate_process_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate process-related metrics."""
        base_processes = self.generate_seasonal_pattern(timestamp, 150, 0.2)
        total_processes = int(self.add_noise(base_processes, 0.1))

        return {
            "total_processes": max(50, total_processes),
            "running_processes": self.random.randint(1, 10),
            "sleeping_processes": int(total_processes * 0.8),
            "stopped_processes": self.random.randint(0, 2),
            "zombie_processes": self.random.randint(0, 1),
            "threads_total": total_processes * self.random.randint(2, 8),
            "forks_per_sec": round(self.random.uniform(0.5, 5.0), 2),
            "context_switches_per_sec": round(self.random.uniform(1000, 10000), 2),
        }

    def generate_filesystem_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate file system metrics."""
        max_files = 65536
        open_files = int(
            self.generate_seasonal_pattern(timestamp, max_files * 0.3, 0.2)
        )

        return {
            "open_files": max(100, open_files),
            "max_open_files": max_files,
            "open_files_percent": round((open_files / max_files) * 100, 2),
            "file_descriptors_used": open_files * 2,
            "file_descriptors_max": max_files * 4,
            "dentries": self.random.randint(10000, 100000),
            "inodes_cached": self.random.randint(5000, 50000),
        }

    def generate_system_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate system-wide metrics."""
        uptime_days = (timestamp - self.base_timestamp).days
        uptime_seconds = uptime_days * 24 * 3600 + self.random.randint(0, 86400)

        return {
            "uptime_seconds": uptime_seconds,
            "boot_time": int(self.base_timestamp.timestamp()),
            "users_logged_in": self.random.randint(1, 10),
            "system_calls_per_sec": round(self.random.uniform(1000, 50000), 2),
            "page_faults_per_sec": round(self.random.uniform(100, 5000), 2),
            "major_page_faults_per_sec": round(self.random.uniform(1, 100), 2),
            "entropy_available": self.random.randint(1000, 4096),
        }

    def generate_docker_metrics(self, timestamp: datetime) -> Dict[str, Any]:
        """Generate Docker container metrics."""
        containers_running = self.random.randint(0, 20)
        memory_limit = 1024 * 1024 * 1024  # 1GB
        memory_usage = int(
            self.generate_seasonal_pattern(timestamp, memory_limit * 0.6, 0.3)
        )

        return {
            "containers_running": containers_running,
            "containers_paused": self.random.randint(0, 2),
            "containers_stopped": self.random.randint(0, 5),
            "images_total": self.random.randint(5, 50),
            "volumes_total": self.random.randint(0, 10),
            "networks_total": self.random.randint(1, 5),
            "cpu_usage_percent": round(self.random.uniform(0, 80), 2),
            "memory_usage_bytes": memory_usage,
            "memory_limit_bytes": memory_limit,
            "network_rx_bytes": self.random.randint(1000000, 100000000),
            "network_tx_bytes": self.random.randint(1000000, 100000000),
            "block_read_bytes": self.random.randint(1000000, 50000000),
            "block_write_bytes": self.random.randint(1000000, 50000000),
        }
