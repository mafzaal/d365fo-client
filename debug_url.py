#!/usr/bin/env python3
"""Debug script to check URL generation."""

from src.d365fo_client.query import QueryBuilder

# Test URL generation for entity by key
base_url = "http://localhost:8000"
entity_name = "Customers"
key = "US-001"

url = QueryBuilder.build_entity_url(base_url, entity_name, key)
print(f"Generated URL: {url}")

# What should match the pattern /data/{entity}({key})
# Expected: /data/Customers('US-001')