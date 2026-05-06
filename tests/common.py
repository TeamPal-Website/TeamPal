"""Shared payloads for integration tests (must satisfy profile_incomplete checks)."""

COMPLETE_PROFILE_JSON = {
    'first_name': 'Иван',
    'last_name': 'Петров',
    'age': 25,
    'gender': 'male',
    'contacts': {
        'phone': '+79991234567',
        'telegram': '@tp_testuser',
        'github': 'https://github.com/tp-test-user',
    },
}
