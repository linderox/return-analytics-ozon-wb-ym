# Marketplace Returns SaaS - Test Execution Report
Generated on: Thu Jun 25 09:18:23 UTC 2026

## Summary
- **Unit Tests**: PASSED
- **Marketplace Integration**: PASSED

## 1. Unit Tests Results
```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/jules/.pyenv/versions/3.12.13/bin/python
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
plugins: mock-3.15.1, anyio-4.14.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 10 items / 1 deselected / 9 selected

tests/test_shops.py::test_create_wb_shop_success PASSED                  [ 11%]
tests/test_shops.py::test_create_ozon_shop_success PASSED                [ 22%]
tests/test_shops.py::test_create_ym_shop_success PASSED                  [ 33%]
tests/test_shops.py::test_create_shop_invalid_marketplace PASSED         [ 44%]
tests/test_shops.py::test_admin_create_shop PASSED                       [ 55%]
tests/test_auth.py::test_get_profile_unauthorized PASSED                 [ 66%]
tests/test_auth.py::test_yandex_auth_redirect PASSED                     [ 77%]
tests/test_auth.py::test_google_login_flow_mock PASSED                   [ 88%]
tests/test_auth.py::test_admin_create_user PASSED                        [100%]

=============================== warnings summary ===============================
../home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/fastapi/testclient.py:1
  /home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================== 9 passed, 1 deselected, 1 warning in 0.97s ==================
```

## 2. Integration Tests Results
```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/jules/.pyenv/versions/3.12.13/bin/python
cachedir: .pytest_cache
rootdir: /app
configfile: pytest.ini
plugins: mock-3.15.1, anyio-4.14.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 3 items

tests/test_tokens.py::test_wb_token_validation PASSED                    [ 33%]
tests/test_tokens.py::test_ym_token_validation PASSED                    [ 66%]
tests/test_tokens.py::test_ozon_token_validation PASSED                  [100%]

=============================== warnings summary ===============================
../home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/fastapi/testclient.py:1
  /home/jules/.pyenv/versions/3.12.13/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
========================= 3 passed, 1 warning in 2.11s =========================
```
