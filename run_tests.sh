#!/bin/bash
# [Automation Script] Authored by Anton Mislawsky

echo "--- RUNNING BACKEND TESTS ---"
export PYTHONPATH=.
pytest tests/backend

echo ""
echo "--- RUNNING FRONTEND TESTS ---"
cd webapp/frontend
# Note: In real CI we would run 'npm test'
# For now, we just verify vitest is configured
if [ -f "node_modules/.bin/vitest" ]; then
  npm test run
else
  echo "Skipping frontend tests (dependencies not installed)"
fi

echo ""
echo "--- TESTING COMPLETE ---"
