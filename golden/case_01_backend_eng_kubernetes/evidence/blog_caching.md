# Building a caching layer that doesn't lie

When we redesigned TechCorp's caching layer, the key insight was honoring
cache invalidation events across regions. We chose a two-tier scheme...
