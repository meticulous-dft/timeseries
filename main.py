#!/usr/bin/env python3
"""MongoDB Time Series Data Generator - Main CLI Application."""

import logging
import sys
import time

import click
from colorama import Fore, Style, init

from batch_processor import BatchProcessor
from config import app_config, data_config, mongo_config
from data_engine import TimeSeriesDataGenerator
from mongodb_client import MongoDBTimeSeriesClient

# Initialize colorama for cross-platform colored output
init(autoreset=True)


# Setup logging
def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Reduce noise from pymongo
    logging.getLogger("pymongo").setLevel(logging.WARNING)


def print_banner():
    """Print application banner."""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                MongoDB Time Series Data Generator            ║
║                     Performance Testing Tool                 ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


def print_config_summary():
    """Print configuration summary."""
    print(f"\n{Fore.YELLOW}Configuration Summary:{Style.RESET_ALL}")
    print(f"  Database: {mongo_config.database_name}")
    print(f"  Collection: {mongo_config.collection_name}")
    print(f"  Total Documents: {data_config.total_documents:,}")
    print(
        f"  Document Size: {data_config.document_size_kb} KB (±{data_config.document_size_variance * 100:.0f}%)"
    )
    print(f"  Host Count: {data_config.host_count:,}")
    print(f"  Time Range: {data_config.start_time} to {data_config.end_time}")
    print(f"  Batch Size: {data_config.batch_size}")
    print(f"  Parallel Workers: {data_config.parallel_workers}")
    print(f"  Sharding: {'Enabled' if app_config.enable_sharding else 'Disabled'}")
    print(f"  Indexes: {'Enabled' if app_config.create_indexes else 'Disabled'}")


def format_bytes(bytes_value: float) -> str:
    """Format bytes in human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Set logging level",
)
def cli(log_level):
    """MongoDB Time Series Data Generator for performance testing."""
    setup_logging(log_level)


@cli.command()
@click.option("--total-docs", type=int, help="Total number of documents to generate")
@click.option("--doc-size-kb", type=float, help="Target document size in KB")
@click.option("--host-count", type=int, help="Number of simulated hosts")
@click.option("--batch-size", type=int, help="Batch size for insertions")
@click.option("--workers", type=int, help="Number of parallel workers")
@click.option(
    "--drop-collection", is_flag=True, help="Drop existing collection before generating"
)
@click.option(
    "--dry-run", is_flag=True, help="Generate data without inserting to database"
)
def generate(
    total_docs, doc_size_kb, host_count, batch_size, workers, drop_collection, dry_run
):
    """Generate time series data and insert into MongoDB."""

    print_banner()

    # Override config with CLI options
    if total_docs:
        data_config.total_documents = total_docs
    if doc_size_kb:
        data_config.document_size_kb = doc_size_kb
    if host_count:
        data_config.host_count = host_count
    if batch_size:
        data_config.batch_size = batch_size
    if workers:
        data_config.parallel_workers = workers

    print_config_summary()

    if dry_run:
        print(
            f"\n{Fore.YELLOW}DRY RUN MODE - No data will be inserted{Style.RESET_ALL}"
        )

    try:
        # Initialize components
        mongodb_client = MongoDBTimeSeriesClient()
        data_generator = TimeSeriesDataGenerator()

        if not dry_run:
            # Connect to MongoDB
            print(f"\n{Fore.BLUE}Connecting to MongoDB...{Style.RESET_ALL}")
            if not mongodb_client.connect():
                print(f"{Fore.RED}Failed to connect to MongoDB{Style.RESET_ALL}")
                return

            # Drop collection if requested
            if drop_collection:
                print(f"{Fore.YELLOW}Dropping existing collection...{Style.RESET_ALL}")
                mongodb_client.drop_collection()

            # Setup collection
            print(f"{Fore.BLUE}Setting up time series collection...{Style.RESET_ALL}")
            if not mongodb_client.create_time_series_collection():
                print(
                    f"{Fore.RED}Failed to create time series collection{Style.RESET_ALL}"
                )
                return

            # Create indexes
            if app_config.create_indexes:
                print(f"{Fore.BLUE}Creating indexes...{Style.RESET_ALL}")
                mongodb_client.create_indexes()

            # Setup sharding
            if app_config.enable_sharding:
                print(f"{Fore.BLUE}Setting up sharding...{Style.RESET_ALL}")
                mongodb_client.setup_sharding()

        # Initialize batch processor
        batch_processor = BatchProcessor(mongodb_client, data_generator)

        print(f"\n{Fore.GREEN}Starting data generation...{Style.RESET_ALL}")
        start_time = time.time()

        if dry_run:
            # Dry run - just generate data without inserting
            for i in range(0, data_config.total_documents, data_config.batch_size):
                batch_size_actual = min(
                    data_config.batch_size, data_config.total_documents - i
                )
                data_generator.generate_batch(batch_size_actual)
                if i % (data_config.batch_size * 10) == 0:  # Print every 10 batches
                    print(f"Generated {i + batch_size_actual:,} documents...")
            success = True
        else:
            # Generate and insert data
            success = batch_processor.generate_and_process_batches(
                data_config.total_documents,
                None,  # No progress callback
            )
        end_time = time.time()
        duration = end_time - start_time

        # Print results
        print(f"\n{Fore.GREEN}Data generation completed!{Style.RESET_ALL}")

        if not dry_run:
            batch_stats = batch_processor.get_stats()

            print(f"\n{Fore.YELLOW}Performance Statistics:{Style.RESET_ALL}")
            print(f"  Total Duration: {format_duration(duration)}")
            print(f"  Documents Inserted: {batch_stats.total_documents_inserted:,}")
            print(f"  Data Size: {format_bytes(batch_stats.total_bytes_inserted)}")
            print(f"  Insertion Rate: {batch_stats.documents_per_second:.0f} docs/sec")
            print(
                f"  Throughput: {format_bytes(int(batch_stats.total_bytes_inserted / duration))}/sec"
            )
            print(f"  Batch Success Rate: {batch_stats.success_rate:.1f}%")

            # Get collection stats
            collection_stats = mongodb_client.get_collection_stats()
            if collection_stats:
                print(f"\n{Fore.YELLOW}Collection Statistics:{Style.RESET_ALL}")
                print(
                    f"  Document Count: {collection_stats.get('document_count', 0):,}"
                )
                print(
                    f"  Collection Size: {format_bytes(collection_stats.get('size_bytes', 0))}"
                )
                print(
                    f"  Storage Size: {format_bytes(collection_stats.get('storage_size_bytes', 0))}"
                )
                print(
                    f"  Average Document Size: {collection_stats.get('avg_document_size', 0):.0f} bytes"
                )
                print(f"  Index Count: {collection_stats.get('indexes', 0)}")
                print(
                    f"  Index Size: {format_bytes(collection_stats.get('index_size_bytes', 0))}"
                )

        if success:
            print(f"\n{Fore.GREEN}✓ Operation completed successfully{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}✗ Operation completed with errors{Style.RESET_ALL}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation interrupted by user{Style.RESET_ALL}")
        if "batch_processor" in locals():
            batch_processor.stop()
        sys.exit(1)

    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

    finally:
        if "mongodb_client" in locals():
            mongodb_client.disconnect()


@cli.command()
def stats():
    """Show collection statistics."""
    print_banner()

    try:
        mongodb_client = MongoDBTimeSeriesClient()

        print(f"{Fore.BLUE}Connecting to MongoDB...{Style.RESET_ALL}")
        if not mongodb_client.connect():
            print(f"{Fore.RED}Failed to connect to MongoDB{Style.RESET_ALL}")
            return

        collection_stats = mongodb_client.get_collection_stats()

        if not collection_stats:
            print(f"{Fore.YELLOW}No statistics available{Style.RESET_ALL}")
            return

        print(f"\n{Fore.YELLOW}Collection Statistics:{Style.RESET_ALL}")
        print(f"  Database: {mongo_config.database_name}")
        print(f"  Collection: {mongo_config.collection_name}")
        print(f"  Document Count: {collection_stats.get('document_count', 0):,}")
        print(
            f"  Collection Size: {format_bytes(collection_stats.get('size_bytes', 0))}"
        )
        print(
            f"  Storage Size: {format_bytes(collection_stats.get('storage_size_bytes', 0))}"
        )
        print(
            f"  Average Document Size: {collection_stats.get('avg_document_size', 0):.0f} bytes"
        )
        print(f"  Index Count: {collection_stats.get('indexes', 0)}")
        print(
            f"  Index Size: {format_bytes(collection_stats.get('index_size_bytes', 0))}"
        )

    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

    finally:
        if "mongodb_client" in locals():
            mongodb_client.disconnect()


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to drop the collection?")
def drop():
    """Drop the time series collection."""
    print_banner()

    try:
        mongodb_client = MongoDBTimeSeriesClient()

        print(f"{Fore.BLUE}Connecting to MongoDB...{Style.RESET_ALL}")
        if not mongodb_client.connect():
            print(f"{Fore.RED}Failed to connect to MongoDB{Style.RESET_ALL}")
            return

        print(f"{Fore.YELLOW}Dropping collection...{Style.RESET_ALL}")
        if mongodb_client.drop_collection():
            print(f"{Fore.GREEN}✓ Collection dropped successfully{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Failed to drop collection{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

    finally:
        if "mongodb_client" in locals():
            mongodb_client.disconnect()


if __name__ == "__main__":
    cli()
