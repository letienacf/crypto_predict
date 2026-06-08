#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

PORT="${PORT:-5555}"
LOG_FILE="${LOG_FILE:-${FRONTEND_DIR}/frontend-dev.log}"
PID_FILE="${PID_FILE:-${FRONTEND_DIR}/frontend-dev.pid}"

if [[ ! -d "${FRONTEND_DIR}" ]]; then
  echo "Frontend directory not found: ${FRONTEND_DIR}" >&2
  exit 1
fi

if [[ ! -f "${FRONTEND_DIR}/package.json" ]]; then
  echo "package.json not found in: ${FRONTEND_DIR}" >&2
  exit 1
fi

kill_port_processes() {
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -t -iTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    pids="$(fuser "${PORT}"/tcp 2>/dev/null || true)"
  elif command -v ss >/dev/null 2>&1; then
    pids="$(ss -ltnp 2>/dev/null | awk -v p=":${PORT}" '$4 ~ p {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' || true)"
  fi

  if [[ -n "${pids}" ]]; then
    echo "Killing process(es) on port ${PORT}: ${pids}"
    kill -9 ${pids} 2>/dev/null || true
  else
    echo "No process is listening on port ${PORT}."
  fi
}

kill_pid_file_process() {
  if [[ -f "${PID_FILE}" ]]; then
    local old_pid
    old_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${old_pid}" ]] && kill -0 "${old_pid}" 2>/dev/null; then
      echo "Killing previous frontend PID from pid file: ${old_pid}"
      kill -9 "${old_pid}" 2>/dev/null || true
    fi
    rm -f "${PID_FILE}"
  fi
}

kill_port_processes
kill_pid_file_process

cd "${FRONTEND_DIR}"

echo "Starting frontend in background on port ${PORT}..."
nohup npm run dev -- --host 0.0.0.0 --port "${PORT}" > "${LOG_FILE}" 2>&1 < /dev/null &
NEW_PID=$!
echo "${NEW_PID}" > "${PID_FILE}"

echo "Frontend started."
echo "PID: ${NEW_PID}"
echo "Port: ${PORT}"
echo "Log: ${LOG_FILE}"
echo "PID file: ${PID_FILE}"