#!/usr/bin/env python3
"""
Multiprocessing pool management for parallel application processing.

Provides utilities to process applications in parallel using a configurable
number of worker processes. Supports both single-process and multi-process execution.
"""

import os
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional, Dict
from functools import partial


logger = logging.getLogger(__name__)


class ProcessingPool:
    """
    Manages parallel processing of applications using worker pools.

    Supports both multiprocessing (CPU-bound tasks) and threading (I/O-bound tasks).
    Automatically falls back to sequential processing if workers <= 0.

    Usage:
        # CPU-bound processing (text extraction)
        with ProcessingPool(num_workers=4) as pool:
            results = pool.map_unordered(extract_text_worker, applications)

        # I/O-bound processing (Ollama API calls)
        with ProcessingPool(num_workers=4, use_threading=True) as pool:
            results = pool.map_unordered(ollama_worker, applications)

        # Sequential processing (num_workers=0 or None)
        with ProcessingPool(num_workers=0) as pool:
            results = pool.map_unordered(worker_func, applications)
    """

    def __init__(
        self,
        num_workers: Optional[int] = None,
        use_threading: bool = False,
        verbose: bool = True
    ):
        """
        Initialize the processing pool.

        Args:
            num_workers: Number of worker processes/threads.
                        0 or None = sequential processing (no pool)
                        > 0 = use that many workers
                        If None and use_threading=False, defaults to CPU count
            use_threading: If True, use ThreadPoolExecutor (for I/O-bound tasks).
                          If False, use ProcessPoolExecutor (for CPU-bound tasks).
                          Only applies if num_workers > 0.
            verbose: Enable logging of pool status
        """
        self.num_workers = num_workers
        self.use_threading = use_threading
        self.verbose = verbose
        self.executor = None
        self.use_sequential = (num_workers is None or num_workers <= 0)

        # Determine worker count
        if not self.use_sequential and self.num_workers is None:
            self.num_workers = os.cpu_count() or 1

        if self.verbose and not self.use_sequential:
            executor_type = "ThreadPoolExecutor" if use_threading else "ProcessPoolExecutor"
            logger.info(
                f"Initializing {executor_type} with {self.num_workers} workers"
            )
        elif self.verbose and self.use_sequential:
            logger.info("Sequential processing mode (num_workers=0)")

    def __enter__(self):
        """Context manager entry."""
        if not self.use_sequential:
            if self.use_threading:
                self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
            else:
                self.executor = ProcessPoolExecutor(max_workers=self.num_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up executor."""
        if self.executor is not None:
            self.executor.shutdown(wait=True)
            if self.verbose:
                logger.info("Pool executor shut down")

    def map_unordered(
        self,
        func: Callable,
        iterable: List[Any],
        show_progress: bool = False
    ) -> List[Any]:
        """
        Apply function to all items in iterable, returning results as completed.

        Works with both parallel and sequential execution modes.

        Args:
            func: Function to apply to each item
            iterable: List of items to process
            show_progress: If True, print progress updates (requires tqdm)

        Returns:
            List of results (order may differ from input if using parallel execution)
        """
        if self.use_sequential:
            return self._sequential_map(func, iterable, show_progress)
        else:
            return self._parallel_map(func, iterable, show_progress)

    def _sequential_map(
        self,
        func: Callable,
        iterable: List[Any],
        show_progress: bool = False
    ) -> List[Any]:
        """
        Process items sequentially (fallback for num_workers=0).

        Args:
            func: Function to apply
            iterable: Items to process
            show_progress: Show progress updates

        Returns:
            List of results in same order as input
        """
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(iterable, desc="Processing")
            except ImportError:
                logger.warning("tqdm not installed, progress bar disabled")
                iterator = iterable
        else:
            iterator = iterable

        for item in iterator:
            try:
                result = func(item)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {item}: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "item": str(item)
                })

        return results

    def _parallel_map(
        self,
        func: Callable,
        iterable: List[Any],
        show_progress: bool = False
    ) -> List[Any]:
        """
        Process items in parallel using executor.

        Args:
            func: Function to apply
            iterable: Items to process
            show_progress: Show progress updates

        Returns:
            List of results (may be in different order than input)
        """
        results = []
        futures = {
            self.executor.submit(func, item): item
            for item in iterable
        }

        if show_progress:
            try:
                from tqdm import tqdm
                futures_iter = tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Processing"
                )
            except ImportError:
                logger.warning("tqdm not installed, progress bar disabled")
                futures_iter = as_completed(futures)
        else:
            futures_iter = as_completed(futures)

        for future in futures_iter:
            item = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {item}: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "item": str(item)
                })

        return results

    def map_with_callback(
        self,
        func: Callable,
        iterable: List[Any],
        callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> List[Any]:
        """
        Apply function to items with callback for each completed result.

        Useful for progress tracking without tqdm dependency.

        Args:
            func: Function to apply to each item
            iterable: List of items to process
            callback: Function called with each result as it completes
            error_callback: Function called if an error occurs

        Returns:
            List of results
        """
        if self.use_sequential:
            return self._sequential_map_with_callback(
                func, iterable, callback, error_callback
            )
        else:
            return self._parallel_map_with_callback(
                func, iterable, callback, error_callback
            )

    def _sequential_map_with_callback(
        self,
        func: Callable,
        iterable: List[Any],
        callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> List[Any]:
        """Sequential version with callbacks."""
        results = []
        for item in iterable:
            try:
                result = func(item)
                results.append(result)
                if callback:
                    callback(result)
            except Exception as e:
                if error_callback:
                    error_callback(e)
                else:
                    logger.error(f"Error processing {item}: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "item": str(item)
                })
        return results

    def _parallel_map_with_callback(
        self,
        func: Callable,
        iterable: List[Any],
        callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None
    ) -> List[Any]:
        """Parallel version with callbacks."""
        results = []
        futures = {
            self.executor.submit(func, item): item
            for item in iterable
        }

        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                results.append(result)
                if callback:
                    callback(result)
            except Exception as e:
                if error_callback:
                    error_callback(e)
                else:
                    logger.error(f"Error processing {item}: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "item": str(item)
                })
        return results

    @staticmethod
    def get_recommended_worker_count(task_type: str = "cpu_bound") -> int:
        """
        Get recommended number of workers based on task type.

        Args:
            task_type: "cpu_bound" or "io_bound"

        Returns:
            Recommended worker count
        """
        cpu_count = os.cpu_count() or 1

        if task_type == "io_bound":
            # I/O-bound tasks (like API calls) can use more workers
            return cpu_count * 2
        else:
            # CPU-bound tasks (like text extraction) should use CPU count
            return cpu_count
