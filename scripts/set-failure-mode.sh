#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
MODE="${1:-success}"

VALID_MODES=(success slow timeout rate_limited server_error malformed_response retrieval_error)

case " ${VALID_MODES[*]} " in
  *" ${MODE} "*) ;;
  *)
    echo "Usage: $0 {success|slow|timeout|rate_limited|server_error|malformed_response|retrieval_error}" >&2
    exit 1
    ;;
esac

echo "Setting failure mode to: ${MODE}"
curl --fail-with-body --silent --show-error \
  -X POST "${API_URL}/test/failure-mode" \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"${MODE}\"}"
echo
echo "Failure mode updated."
