"""Batch processing engine for high-performance data insertion."""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from config import data_config
from data_engine import TimeSeriesDataGenerator
from mongodb_client import MongoDBTimeSeriesClient

logger = logging.getLogger(__name__)


@dataclass
class BatchStats:
    """Statistics for batch processing."""

    batches_processed: int = 0
    batches_failed: int = 0
    total_documents_inserted: int = 0
    total_bytes_inserted: int = 0
    total_processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        total_batches = self.batches_processed + self.batches_failed
        if total_batches > 0:
            return (self.batches_processed / total_batches) * 100
        return 0.0

    @property
    def avg_batch_time(self) -> float:
        if self.batches_processed > 0:
            return self.total_processing_time / self.batches_processed
        return 0.0

    @property
    def documents_per_second(self) -> float:
        if self.total_processing_time > 0:
            return self.total_documents_inserted / self.total_processing_time
        return 0.0


class BatchProcessor:
    """High-performance batch processor for MongoDB insertions."""

    def __init__(
        self,
        mongodb_client: MongoDBTimeSeriesClient,
        data_generator: TimeSeriesDataGenerator,
    ):
        self.mongodb_client = mongodb_client
        self.data_generator = data_generator
        self.stats = BatchStats()

        self._stop_event = threading.Event()
        self._stats_lock = threading.Lock()

        # Configuration
        self.batch_size = data_config.batch_size
        self.num_workers = data_config.parallel_workers

        logger.info(
            f"Batch processor initialized: batch_size={self.batch_size}, workers={self.num_workers}"
        )

    def process_batch(self, batch_data: List[Dict[str, Any]]) -> bool:
        """Process a single batch of documents."""
        if not batch_data:
            return True

        start_time = time.time()

        try:
            # Insert batch into MongoDB
            success = self.mongodb_client.insert_documents(batch_data)

            processing_time = time.time() - start_time

            # Update statistics
            with self._stats_lock:
                if success:
                    self.stats.batches_processed += 1
                    self.stats.total_documents_inserted += len(batch_data)

                    # Calculate batch size in bytes
                    import json

                    batch_bytes = sum(
                        len(json.dumps(doc, default=str).encode("utf-8"))
                        for doc in batch_data
                    )
                    self.stats.total_bytes_inserted += batch_bytes
                else:
                    self.stats.batches_failed += 1

                self.stats.total_processing_time += processing_time

            if success:
                logger.debug(
                    f"Batch processed successfully: {len(batch_data)} documents in {processing_time:.2f}s"
                )
            else:
                logger.error(f"Batch processing failed: {len(batch_data)} documents")

            return success

        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            with self._stats_lock:
                self.stats.batches_failed += 1
            return False

    def generate_and_process_batches(
        self,
        total_documents: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """Generate and process batches in parallel."""
        logger.info(f"Starting batch processing: {total_documents} documents")

        try:
            documents_processed = 0

            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = []

                while (
                    documents_processed < total_documents
                    and not self._stop_event.is_set()
                ):
                    # Calculate batch size for this iteration
                    remaining_docs = total_documents - documents_processed
                    current_batch_size = min(self.batch_size, remaining_docs)

                    # Generate batch
                    batch_data = self.data_generator.generate_batch(current_batch_size)

                    if not batch_data:
                        logger.warning("Generated empty batch, stopping")
                        break

                    # Submit batch for processing
                    future = executor.submit(self.process_batch, batch_data)
                    futures.append(future)

                    documents_processed += len(batch_data)

                    # Process completed futures
                    completed_futures = []
                    for future in futures:
                        if future.done():
                            completed_futures.append(future)
                            try:
                                future.result()  # This will raise any exceptions
                            except Exception as e:
                                logger.error(f"Batch processing error: {e}")

                    # Remove completed futures
                    for future in completed_futures:
                        futures.remove(future)

                    # Simple progress logging
                    if (
                        documents_processed % (self.batch_size * 10) == 0
                    ):  # Every 10 batches
                        print(f"Processed {documents_processed:,} documents...")

                # Wait for remaining futures to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Final batch processing error: {e}")

            logger.info("Batch processing completed")
            return True

        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return False

        finally:
            pass

    def process_time_series_data(
        self,
        host_count: int,
        time_range_hours: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """Process time series data for specific hosts and time range."""
        from datetime import timedelta

        logger.info(
            f"Processing time series data: {host_count} hosts, {time_range_hours} hours"
        )

        # Calculate time range
        start_time = self.data_generator.start_time
        end_time = start_time + timedelta(hours=time_range_hours)

        # Split hosts into batches for parallel processing
        host_batches = [
            list(range(i, min(i + 10, host_count))) for i in range(0, host_count, 10)
        ]

        total_batches = len(host_batches)
        processed_batches = 0

        try:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = []

                for host_batch in host_batches:
                    if self._stop_event.is_set():
                        break

                    # Generate time series batch
                    future = executor.submit(
                        self._process_host_time_series_batch,
                        host_batch,
                        start_time,
                        end_time,
                    )
                    futures.append(future)

                # Process completed futures
                for future in as_completed(futures):
                    try:
                        future.result()
                        processed_batches += 1

                        if processed_batches % 5 == 0:  # Every 5 batches
                            print(
                                f"Processed {processed_batches}/{total_batches} host batches..."
                            )

                    except Exception as e:
                        logger.error(f"Time series batch processing error: {e}")

            return True

        except Exception as e:
            logger.error(f"Error in time series processing: {e}")
            return False

        finally:
            pass

    def _process_host_time_series_batch(
        self, host_ids: List[int], start_time, end_time
    ) -> bool:
        """Process time series data for a batch of hosts."""
        try:
            # Generate documents for this host batch
            documents = self.data_generator.generate_time_series_batch(
                host_ids, start_time, end_time
            )

            # Process in smaller chunks if needed
            chunk_size = self.batch_size
            for i in range(0, len(documents), chunk_size):
                chunk = documents[i : i + chunk_size]
                success = self.process_batch(chunk)

                if not success:
                    logger.error(f"Failed to process chunk for hosts {host_ids}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error processing host batch {host_ids}: {e}")
            return False

    def stop(self):
        """Stop batch processing."""
        self._stop_event.set()
        logger.info("Batch processor stop requested")

    def get_stats(self) -> BatchStats:
        """Get current batch processing statistics."""
        with self._stats_lock:
            return self.stats
