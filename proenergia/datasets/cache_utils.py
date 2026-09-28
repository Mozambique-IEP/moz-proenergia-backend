"""
Cache utilities for managing scenario summary cache invalidation.

This module provides functions to invalidate cached summary responses
when scenario data or its data model is updated.
"""

import logging
from typing import Iterable

from django.conf import settings
from django.core.cache import cache
from django.db import connection

logger = logging.getLogger(__name__)

SUMMARY_CACHE_PREFIX = "summaries:"


def summary_cache_key(scenario_id: int, query_hash: str) -> str:
    """Build the cache key used for a scenario summaries response."""
    return f"{SUMMARY_CACHE_PREFIX}{scenario_id}:{query_hash}"


def _delete_keys_with_prefix(prefix: str) -> int:
    """
    Delete all cache entries whose key starts with the given (unversioned) prefix.

    Django's database cache backend doesn't support pattern-based deletion,
    so we delete directly from the cache table. The prefix is passed through
    cache.make_key() so it matches the stored key format
    (e.g. ':1:summaries:5:...' with the default KEY_PREFIX and VERSION).

    Returns:
        Number of cache entries deleted
    """
    cache_table = connection.ops.quote_name(settings.CACHES["default"]["LOCATION"])
    stored_prefix = cache.make_key(prefix)
    # Escape LIKE wildcards so the prefix is matched literally
    like_prefix = (
        stored_prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )

    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM {cache_table} WHERE cache_key LIKE %s",
            [f"{like_prefix}%"],
        )
        return cursor.rowcount


def invalidate_scenario_summary_cache(scenario_id: int) -> int:
    """
    Invalidate all cached summary responses for a specific scenario.

    Args:
        scenario_id: The scenario ID for which to invalidate cache

    Returns:
        Number of cache entries deleted
    """
    deleted_count = _delete_keys_with_prefix(f"{SUMMARY_CACHE_PREFIX}{scenario_id}:")

    if deleted_count > 0:
        logger.info(
            f"Invalidated {deleted_count} summary cache entries for scenario {scenario_id}"
        )
    else:
        logger.debug(f"No cache entries found to invalidate for scenario {scenario_id}")

    return deleted_count


def invalidate_scenarios_summary_cache(scenario_ids: Iterable[int]) -> int:
    """
    Invalidate cached summary responses for several scenarios.

    Returns:
        Total number of cache entries deleted
    """
    return sum(
        invalidate_scenario_summary_cache(scenario_id) for scenario_id in scenario_ids
    )


def invalidate_all_summary_cache() -> int:
    """
    Invalidate cached summary responses for all scenarios.

    Only summary entries are removed; other cache entries are left untouched.

    Returns:
        Number of cache entries deleted
    """
    deleted_count = _delete_keys_with_prefix(SUMMARY_CACHE_PREFIX)
    logger.info(f"Invalidated {deleted_count} summary cache entries for all scenarios")
    return deleted_count
