# MongoDB Time Series Data Generator

A high-performance Python application for generating realistic time series data to test MongoDB Atlas performance. Based on the TSBS (Time Series Benchmark Suite) DevOps use case, this tool can generate terabytes of data with configurable document sizes and realistic patterns.

## Features

- **Realistic Time Series Data**: Generates DevOps metrics (CPU, memory, disk, network, applications) with seasonal patterns
- **Configurable Document Size**: Control document size with uniform distribution and variance
- **High Performance**: Multi-threaded batch processing with adaptive throttling
- **MongoDB Time Series Collections**: Proper time series collection setup with sharding support
- **Comprehensive Monitoring**: Real-time performance metrics and system resource monitoring
- **Flexible Configuration**: Environment variables, CLI options, and configuration files
- **Production Ready**: Error handling, logging, progress tracking, and graceful shutdown

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd timeseries

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Configuration

Copy the example environment file and configure your MongoDB connection:

```bash
cp .env.example .env
```

Edit `.env` with your MongoDB Atlas connection string:

```env
MONGODB_CONNECTION_STRING=<your-mongodb-atlas-connection-string>
```

Replace `<your-mongodb-atlas-connection-string>` with your actual MongoDB Atlas connection string from your cluster's "Connect" dialog.

### 3. Generate Data

```bash
# Generate 1 million documents with default settings
python main.py generate

# Generate 10 million documents with custom settings
python main.py generate --total-docs 10000000 --doc-size-kb 2.0 --host-count 5000

# Dry run to test configuration without inserting data
python main.py generate --dry-run
```

## Configuration Options

### Environment Variables

| Variable                      | Default                     | Description                      |
| ----------------------------- | --------------------------- | -------------------------------- |
| `MONGODB_CONNECTION_STRING`   | `mongodb://localhost:27017` | MongoDB connection string        |
| `MONGO_DATABASE_NAME`         | `tsbs_benchmark`            | Database name                    |
| `MONGO_COLLECTION_NAME`       | `devops_metrics`            | Collection name                  |
| `DATA_TOTAL_DOCUMENTS`        | `1000000`                   | Total documents to generate      |
| `DATA_DOCUMENT_SIZE_KB`       | `1.0`                       | Target document size in KB       |
| `DATA_DOCUMENT_SIZE_VARIANCE` | `0.2`                       | Document size variance (0.0-1.0) |
| `DATA_HOST_COUNT`             | `1000`                      | Number of simulated hosts        |
| `DATA_BATCH_SIZE`             | `1000`                      | Batch size for insertions        |
| `DATA_PARALLEL_WORKERS`       | `4`                         | Number of parallel workers       |
| `APP_ENABLE_SHARDING`         | `true`                      | Enable MongoDB sharding          |
| `APP_CREATE_INDEXES`          | `true`                      | Create recommended indexes       |

### CLI Options

```bash
python main.py generate --help
```

Options:

- `--total-docs`: Total number of documents to generate
- `--doc-size-kb`: Target document size in KB
- `--host-count`: Number of simulated hosts
- `--batch-size`: Batch size for insertions
- `--workers`: Number of parallel workers
- `--drop-collection`: Drop existing collection before generating
- `--dry-run`: Generate data without inserting to database

## Data Model

The generated data follows the TSBS DevOps format with MongoDB time series collection structure:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "metadata": {
    "hostname": "host_1",
    "region": "us-east-1",
    "datacenter": "us-east-1a",
    "rack": "42",
    "os": "Ubuntu16.04LTS",
    "arch": "x64",
    "team": "NYC",
    "service": "web",
    "service_version": "1",
    "service_environment": "production"
  },
  "measurement": "cpu",
  "fields": {
    "usage_user": 45.2,
    "usage_system": 12.8,
    "usage_idle": 41.5,
    "usage_iowait": 0.5
  },
  "padding": "random_string_for_size_control"
}
```

### Metric Types

- **CPU**: User, system, idle, iowait, irq, softirq, steal, guest, guest_nice
- **Memory**: Total, available, used, free, cached, buffered, percentages
- **Disk**: Total, free, used, used_percent, inodes
- **Disk I/O**: Reads, writes, read_bytes, write_bytes, read_time, write_time
- **Network**: Bytes sent/received, packets sent/received, errors, drops
- **Kernel**: Boot time, interrupts, context switches, processes forked
- **Nginx**: Accepts, active, handled, reading, requests, waiting, writing
- **PostgreSQL**: Backends, transactions, blocks, tuples
- **Redis**: Clients, memory usage, operations, connections

## Performance Optimization

### MongoDB Configuration

For optimal performance, ensure your MongoDB Atlas cluster has:

1. **Appropriate Cluster Size**: Use M30 or larger for serious testing
2. **Sharding Enabled**: The tool automatically configures sharding
3. **Proper Indexes**: Indexes are created automatically
4. **Write Concern**: Uses `w: majority` for durability

### Application Tuning

```bash
# High-throughput configuration
export DATA_BATCH_SIZE=5000
export DATA_PARALLEL_WORKERS=8
export DATA_DOCUMENT_SIZE_KB=0.5

# Memory-intensive configuration
export DATA_BATCH_SIZE=1000
export DATA_PARALLEL_WORKERS=4
export DATA_DOCUMENT_SIZE_KB=5.0
```

### System Requirements

- **CPU**: 4+ cores recommended for parallel processing
- **Memory**: 8GB+ RAM for large batch sizes
- **Network**: High bandwidth connection to MongoDB Atlas
- **Disk**: SSD recommended for temporary storage

## Monitoring and Metrics

### Real-time Monitoring

The application provides comprehensive monitoring:

```bash
# View collection statistics
python main.py stats

# Monitor during generation (built-in logging)
python main.py generate --total-docs 1000000
```

### Performance Metrics

- **Insertion Rate**: Documents per second
- **Throughput**: MB/s data transfer
- **Resource Usage**: CPU, memory, disk I/O, network
- **Batch Statistics**: Success rate, average batch time
- **Collection Stats**: Document count, storage size, index size

## Advanced Usage

### Large Scale Testing

For terabyte-scale testing:

```bash
# Generate 1 billion documents (~1TB of data)
python main.py generate \
  --total-docs 1000000000 \
  --doc-size-kb 1.0 \
  --host-count 10000 \
  --batch-size 10000 \
  --workers 16
```

### Custom Time Ranges

Configure time ranges in `.env`:

```env
DATA_START_TIME=2023-01-01T00:00:00Z
DATA_END_TIME=2024-12-31T23:59:59Z
DATA_TIME_INTERVAL_SECONDS=60
```

### Sharding Configuration

The tool automatically configures sharding with:

- Shard key: `{metadata.hostname: "hashed", timestamp: 1}`
- Optimal distribution across shards
- Time-based and host-based queries

## Troubleshooting

### Common Issues

1. **Connection Timeout**

   ```bash
   # Increase connection timeout by adding connectTimeoutMS parameter to your connection string
   # Example: add "?connectTimeoutMS=30000" to your MongoDB connection string
   ```

2. **Memory Issues**

   ```bash
   # Reduce batch size and workers
   export DATA_BATCH_SIZE=500
   export DATA_PARALLEL_WORKERS=2
   ```

3. **Slow Performance**
   ```bash
   # Check MongoDB cluster size and network latency
   # Consider using a larger Atlas cluster (M30+)
   # Ensure proper indexing is enabled
   ```

### Logging

Enable debug logging:

```bash
python main.py --log-level DEBUG generate
```

## Best Practices

1. **Start Small**: Test with small datasets before scaling up
2. **Monitor Resources**: Watch CPU, memory, and network usage
3. **Use Appropriate Cluster Size**: M30+ for production testing
4. **Enable Sharding**: For datasets > 100GB
5. **Batch Size Tuning**: Start with 1000, adjust based on performance
6. **Network Optimization**: Use MongoDB Atlas in the same region

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review MongoDB Atlas documentation
