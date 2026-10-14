"""Launchers for cloud APM, error tracking, and non-breaking live debug tools."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


def _program() -> str:
    return os.environ.get("DAPPY_PROGRAM", "")


def _info(name: str, lines: list[str], code: int = 0) -> int:
    sys.stderr.write(f"dappy-observability-launch [{name}]\n")
    for line in lines:
        sys.stderr.write(f"  {line}\n")
    return code


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def launch_lightrun() -> int:
    agent = os.environ.get("LIGHTRUN_AGENT_JAR") or os.environ.get("LIGHTRUN_SERVER")
    if agent and os.path.isfile(agent):
        program = _program()
        java = shutil.which("java") or "java"
        args = [java, f"-agentpath:{agent}"]
        if program:
            args.append(program)
        return _run(args)
    return _info(
        "Lightrun",
        [
            "Non-breaking live debugging for microservices/Kubernetes.",
            "Install Lightrun agent in your service, then attach via IDE plugin.",
            "Env: LIGHTRUN_SERVER, LIGHTRUN_AGENT_JAR, LIGHTRUN_API_KEY",
            "Docs: https://docs.lightrun.com/",
        ],
    )


def launch_sentry() -> int:
    cli = shutil.which("sentry-cli")
    org = os.environ.get("SENTRY_ORG")
    project = os.environ.get("SENTRY_PROJECT")
    if cli and org and project:
        return _run([cli, "issues", "list", "--org", org, "--project", project])
    dsn = os.environ.get("SENTRY_DSN")
    if dsn:
        return _info(
            "Sentry",
            [
                f"DSN configured ({dsn[:32]}…).",
                "Use sentry-cli or Sentry UI for stack traces.",
                "Set SENTRY_ORG + SENTRY_PROJECT + sentry-cli for CLI listing.",
            ],
        )
    return _info(
        "Sentry",
        [
            "Error tracking and crash reporting.",
            "Env: SENTRY_DSN, SENTRY_ORG, SENTRY_PROJECT, SENTRY_AUTH_TOKEN",
            "Install: npm i -g @sentry/cli  or  pip install sentry-cli",
            "Docs: https://docs.sentry.io/",
        ],
    )


def launch_datadog_apm() -> int:
    dd_ci = shutil.which("datadog-ci")
    if dd_ci:
        return _run([dd_ci, "version"])
    agent_host = os.environ.get("DD_AGENT_HOST", "127.0.0.1")
    trace_port = os.environ.get("DD_TRACE_AGENT_PORT", "8126")
    api_key = os.environ.get("DD_API_KEY")
    lines = [
        "Datadog APM / Live Debugger — enterprise monitoring and live code snapshots.",
        f"Trace agent: {agent_host}:{trace_port}",
        "Env: DD_API_KEY, DD_SERVICE, DD_ENV, DD_VERSION, DD_TRACE_DEBUG=1",
        "Enable Live Debugger in Datadog UI (Security → App and API Protection).",
        "Docs: https://docs.datadoghq.com/tracing/",
    ]
    if api_key:
        lines.insert(1, "DD_API_KEY is set — configure dd-trace in your app.")
    return _info("Datadog APM", lines)


def launch_rollbar() -> int:
    token = os.environ.get("ROLLBAR_ACCESS_TOKEN")
    program = _program()
    if token and program:
        try:
            with open(program, encoding="utf-8", errors="replace") as fh:
                payload = json.dumps(
                    {
                        "access_token": token,
                        "data": {
                            "environment": os.environ.get("ROLLBAR_ENV", "production"),
                            "body": {"message": {"body": fh.read()[:4000]}},
                        },
                    }
                ).encode()
            req = urllib.request.Request(
                "https://api.rollbar.com/api/1/item/",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                sys.stderr.write(f"Rollbar: submitted ({resp.status})\n")
                return 0
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            return _info("Rollbar", [f"API error: {exc}"], code=1)
    return _info(
        "Rollbar",
        [
            "Automated error monitoring and stack analysis.",
            "Env: ROLLBAR_ACCESS_TOKEN, ROLLBAR_ENV",
            "Point program at a log/stack file to POST via API, or use Rollbar SDK.",
            "Docs: https://docs.rollbar.com/",
        ],
    )


def launch_bugsnag() -> int:
    api_key = os.environ.get("BUGSNAG_API_KEY")
    if api_key:
        return _info(
            "Bugsnag",
            [
                f"BUGSNAG_API_KEY set ({api_key[:8]}…).",
                "Integrate bugsnag SDK in your app for crash capture.",
                "Dashboard: https://app.bugsnag.com/",
            ],
        )
    return _info(
        "Bugsnag",
        [
            "Application stability and crash monitoring.",
            "Env: BUGSNAG_API_KEY",
            "Docs: https://docs.bugsnag.com/",
        ],
    )


def launch_airbrake() -> int:
    project_id = os.environ.get("AIRBRAKE_PROJECT_ID")
    project_key = os.environ.get("AIRBRAKE_PROJECT_KEY")
    if project_id and project_key:
        return _info(
            "Airbrake",
            [
                f"Project {project_id} configured.",
                "Use airbrake-js/py/ruby SDK or notifier CLI.",
                "Docs: https://docs.airbrake.io/",
            ],
        )
    return _info(
        "Airbrake",
        [
            "Cloud exception and error tracking.",
            "Env: AIRBRAKE_PROJECT_ID, AIRBRAKE_PROJECT_KEY",
            "Docs: https://docs.airbrake.io/",
        ],
    )


def launch_raygun() -> int:
    api_key = os.environ.get("RAYGUN_API_KEY")
    if api_key:
        return _info(
            "Raygun",
            [
                f"RAYGUN_API_KEY set ({api_key[:8]}…).",
                "Crash reporting + Real User Monitoring via Raygun4* SDKs.",
                "Dashboard: https://app.raygun.com/",
            ],
        )
    return _info(
        "Raygun",
        [
            "Crash reporting and RUM.",
            "Env: RAYGUN_API_KEY",
            "Docs: https://raygun.com/documentation/",
        ],
    )


def launch_new_relic_apm() -> int:
    for cmd in ("newrelic", "newrelic-admin"):
        path = shutil.which(cmd)
        if path:
            if cmd == "newrelic":
                return _run([path, "profiles", "list"])
            return _run([path, "run-program", "echo", "newrelic-agent-ready"])
    license_key = os.environ.get("NEW_RELIC_LICENSE_KEY")
    lines = [
        "New Relic APM — performance and error debugging in cloud.",
        "Env: NEW_RELIC_LICENSE_KEY, NEW_RELIC_APP_NAME",
        "Install: pip install newrelic  or  npm i newrelic",
        "Docs: https://docs.newrelic.com/docs/apm/",
    ]
    if license_key:
        lines.insert(1, "NEW_RELIC_LICENSE_KEY is set — wrap app with newrelic-admin run-program.")
    return _info("New Relic APM", lines)


def launch_dynatrace() -> int:
    url = os.environ.get("DT_TENANT_URL") or os.environ.get("DYNATRACE_ENVIRONMENT_URL")
    token = os.environ.get("DT_API_TOKEN") or os.environ.get("DYNATRACE_API_TOKEN")
    if url and token:
        return _info(
            "Dynatrace",
            [
                f"Tenant: {url}",
                "OneAgent + Davis AI APM — use Dynatrace UI for live debugging.",
                "Enable code-level insights in Smartscape / distributed traces.",
            ],
        )
    return _info(
        "Dynatrace",
        [
            "AI-powered APM and live debugging platform.",
            "Env: DT_TENANT_URL, DT_API_TOKEN (or DYNATRACE_* variants)",
            "Docs: https://docs.dynatrace.com/",
        ],
    )


def launch_instana() -> int:
    endpoint = os.environ.get("INSTANA_AGENT_ENDPOINT", "127.0.0.1:42699")
    key = os.environ.get("INSTANA_AGENT_KEY")
    lines = [
        "Instana — automated application observability.",
        f"Agent endpoint (default): {endpoint}",
        "Env: INSTANA_AGENT_KEY, INSTANA_SERVICE_NAME",
        "Attach Instana agent to JVM/Node/Go process — no breakpoints required.",
        "Docs: https://www.ibm.com/docs/en/instana-observability/",
    ]
    if key:
        lines.insert(1, "INSTANA_AGENT_KEY is set.")
    return _info("Instana", lines)


def launch_elastic_apm() -> int:
    server_url = os.environ.get("ELASTIC_APM_SERVER_URL", "http://127.0.0.1:8200")
    secret = os.environ.get("ELASTIC_APM_SECRET_TOKEN")
    kibana = os.environ.get("KIBANA_URL")
    lines = [
        "Elastic APM (ELK) — logs, traces, and errors in Elasticsearch/Kibana.",
        f"APM server: {server_url}",
        "Env: ELASTIC_APM_SERVER_URL, ELASTIC_APM_SECRET_TOKEN, ELASTIC_APM_SERVICE_NAME",
        "Stack traces: Kibana → Observability → APM → Errors",
    ]
    if secret:
        lines.insert(2, "ELASTIC_APM_SECRET_TOKEN is set.")
    if kibana:
        lines.append(f"Kibana: {kibana}")
    return _info("Elastic APM", lines)


_HANDLERS = {
    "lightrun": launch_lightrun,
    "sentry": launch_sentry,
    "datadog-apm": launch_datadog_apm,
    "rollbar": launch_rollbar,
    "bugsnag": launch_bugsnag,
    "airbrake": launch_airbrake,
    "raygun": launch_raygun,
    "new-relic-apm": launch_new_relic_apm,
    "dynatrace": launch_dynatrace,
    "instana": launch_instana,
    "elastic-apm": launch_elastic_apm,
}


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = _HANDLERS.get(tool)
    if not handler:
        sys.stderr.write(f"dappy-observability-launch: unknown `{tool}`\n")
        raise SystemExit(1)
    raise SystemExit(handler())


if __name__ == "__main__":
    main()
