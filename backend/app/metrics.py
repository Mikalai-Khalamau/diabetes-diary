from prometheus_client import Counter

GLUCOSE_MEASUREMENTS_TOTAL = Counter(
    'diabetes_glucose_measurements_total',
    'Total number of glucose measurements logged by users',
)

INSULIN_INJECTIONS_TOTAL = Counter(
    'diabetes_insulin_injections_total',
    'Total number of insulin injections logged by users',
    ['insulin_type'],
)

MEAL_EVENTS_TOTAL = Counter(
    'diabetes_meal_events_total',
    'Total number of meal events logged by users',
)

AUTH_ATTEMPTS_TOTAL = Counter(
    'diabetes_auth_attempts_total',
    'Total number of authentication attempts',
    ['status'],
)

USERS_REGISTERED_TOTAL = Counter(
    'diabetes_users_registered_total',
    'Total number of registered users',
)