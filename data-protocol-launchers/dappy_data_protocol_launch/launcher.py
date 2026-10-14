"""Launchers for database query, RPC, and protocol inspection tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-data-protocol-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_pg_explain() -> int:
    psql = shutil.which("psql")
    program = _program()
    if psql and program and os.path.isfile(program):
        query = open(program, encoding="utf-8", errors="replace").read()
        db = os.environ.get("PGDATABASE", "postgres")
        return _run([psql, "-d", db, "-c", f"EXPLAIN ANALYZE {query}"])
    if psql:
        return _run([psql, "-c", "SELECT * FROM pg_stat_statements LIMIT 10;"])
    return _info(
        "pg_stat_statements / EXPLAIN",
        [
            "PostgreSQL query debugger — execution plans and bottlenecks.",
            "CREATE EXTENSION pg_stat_statements;",
            "EXPLAIN (ANALYZE, BUFFERS) SELECT …",
            "Pass .sql file as program for EXPLAIN ANALYZE.",
        ],
    )


def launch_grpcurl_bloomrpc() -> int:
    grpcurl = shutil.which("grpcurl")
    program = _program()
    if grpcurl:
        host = os.environ.get("GRPC_HOST", "localhost:50051")
        if program and os.path.isfile(program):
            return _run([grpcurl, "-plaintext", "-d", open(program).read(), host, "list"])
        return _run([grpcurl, "-plaintext", host, "list"])
    bloom = os.environ.get("BLOOMRPC") or shutil.which("bloomrpc")
    if bloom:
        return _run([bloom])
    return _info(
        "grpcurl / BloomRPC",
        [
            "gRPC service inspection and debugging.",
            "go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest",
            "grpcurl -plaintext localhost:50051 list",
            "BloomRPC: GUI client for protobuf services.",
        ],
    )


def launch_kafka_console() -> int:
    for tool in ("kafka-console-consumer", "kafka-console-producer", "kcat"):
        path = shutil.which(tool)
        if path:
            broker = os.environ.get("KAFKA_BROKER", "localhost:9092")
            topic = os.environ.get("KAFKA_TOPIC", "test")
            if "consumer" in tool or tool == "kcat":
                return _run([path, "--bootstrap-server", broker, "--topic", topic, "--from-beginning"] if "kafka" in tool else [path, "-b", broker, "-t", topic, "-C"])
            return _run([path, "--bootstrap-server", broker, "--topic", topic])
    return _info(
        "Kafka Console",
        [
            "Debug event-driven microservices via Kafka CLI.",
            "kafka-console-consumer --bootstrap-server localhost:9092 --topic foo",
            "kafka-consumer-groups --describe --group mygroup",
            "Alt: kcat (kafkacat)",
        ],
    )


def launch_redis_cli_debug() -> int:
    redis = shutil.which("redis-cli")
    if not redis:
        return _info("Redis CLI", ["Install redis-cli package."], code=1)
    mode = os.environ.get("REDIS_MODE", "monitor")
    host = os.environ.get("REDIS_HOST", "127.0.0.1")
    port = os.environ.get("REDIS_PORT", "6379")
    key = _program() or os.environ.get("REDIS_KEY", "")
    if mode == "monitor":
        return _run([redis, "-h", host, "-p", port, "MONITOR"])
    if key:
        return _run([redis, "-h", host, "-p", port, "DEBUG", "OBJECT", key])
    return _run([redis, "-h", host, "-p", port, "INFO"])


_HANDLERS = {
    "pg-explain": launch_pg_explain,
    "grpcurl-bloomrpc": launch_grpcurl_bloomrpc,
    "kafka-console": launch_kafka_console,
    "redis-cli-debug": launch_redis_cli_debug,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-data-protocol-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
