from prometheus_client import Counter, Histogram

PROBER_CHECKS_TOTAL = Counter(
    'prober_checks_total',
    'Total number of synthetic probe checks',
    ['check_name', 'result']
)

PROBER_CHECK_DURATION_SECONDS = Histogram(
    'prober_check_duration_seconds',
    'Duration of synthetic probe checks in seconds',
    ['check_name']
)