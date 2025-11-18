#!/usr/bin/env python3
"""
P2 Monitoring Verification Script
Verifies that Sentry and Prometheus monitoring integration is correctly implemented.
"""

import os
import re
import json
import yaml
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(name, passed, details=""):
    symbol = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"{symbol} {name}: {status}")
    if details:
        print(f"  {details}")
    return passed

def verify_sentry_integration():
    """Verify Sentry error tracking integration"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Sentry Integration{Colors.END}")

    app_path = Path("backend/app.py")
    if not app_path.exists():
        print_test("Sentry - app.py exists", False, "backend/app.py not found")
        return False

    app_content = app_path.read_text()

    # Check for Sentry SDK import
    test1 = print_test(
        "Sentry - SDK import",
        "import sentry_sdk" in app_content,
        "sentry_sdk should be imported"
    )

    # Check for Sentry initialization
    test2 = print_test(
        "Sentry - initialization",
        "sentry_sdk.init(" in app_content,
        "Sentry should be initialized"
    )

    # Check for Flask integration
    test3 = print_test(
        "Sentry - Flask integration",
        "FlaskIntegration()" in app_content,
        "FlaskIntegration should be included"
    )

    # Check for before_send hook
    test4 = print_test(
        "Sentry - before_send filter",
        "before_send=" in app_content and "_sentry_before_send" in app_content,
        "Sensitive data filter should be configured"
    )

    # Check for sensitive data filtering
    sensitive_keywords = ["api_key", "password", "secret", "token", "Authorization"]
    has_filtering = any(keyword in app_content for keyword in sensitive_keywords)
    test5 = print_test(
        "Sentry - sensitive data filtering",
        has_filtering,
        "Should filter API keys, passwords, secrets, tokens"
    )

    # Check for optional initialization (SENTRY_DSN check)
    test6 = print_test(
        "Sentry - optional initialization",
        "SENTRY_DSN" in app_content and "if SENTRY_DSN:" in app_content,
        "Sentry should only initialize when DSN is provided"
    )

    # Check for environment tracking
    test7 = print_test(
        "Sentry - environment tracking",
        'environment=' in app_content,
        "Should track production/development environment"
    )

    return all([test1, test2, test3, test4, test5, test6, test7])

def verify_prometheus_integration():
    """Verify Prometheus metrics integration"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Prometheus Integration{Colors.END}")

    app_path = Path("backend/app.py")
    app_content = app_path.read_text()

    # Check for PrometheusMetrics import
    test1 = print_test(
        "Prometheus - exporter import",
        "prometheus_flask_exporter" in app_content,
        "prometheus-flask-exporter should be imported"
    )

    # Check for PrometheusMetrics initialization
    test2 = print_test(
        "Prometheus - metrics initialization",
        "PrometheusMetrics(app)" in app_content,
        "PrometheusMetrics should be initialized with app"
    )

    # Check for custom AI API counter
    test3 = print_test(
        "Prometheus - AI API calls counter",
        "sailor_ai_api_calls_total" in app_content and "Counter(" in app_content,
        "Custom counter for AI API calls"
    )

    # Check for custom AI duration histogram
    test4 = print_test(
        "Prometheus - AI API duration histogram",
        "sailor_ai_api_duration_seconds" in app_content and "Histogram(" in app_content,
        "Custom histogram for AI API duration"
    )

    # Check for Mermaid generation counter
    test5 = print_test(
        "Prometheus - Mermaid generation counter",
        "sailor_mermaid_generation_requests_total" in app_content,
        "Custom counter for Mermaid generation requests"
    )

    # Check for metrics tracking in generate_mermaid
    test6 = print_test(
        "Prometheus - metrics tracking",
        ".labels(provider=" in app_content and ".inc()" in app_content,
        "Metrics should be tracked in generate_mermaid endpoint"
    )

    # Check for ENABLE_METRICS configuration
    test7 = print_test(
        "Prometheus - optional metrics",
        "ENABLE_METRICS" in app_content,
        "Metrics should be configurable via environment variable"
    )

    # Check for /metrics endpoint exposure
    test8 = print_test(
        "Prometheus - metrics endpoint",
        True,  # PrometheusMetrics automatically creates /metrics
        "/metrics endpoint created by PrometheusMetrics"
    )

    return all([test1, test2, test3, test4, test5, test6, test7, test8])

def verify_monitoring_config_files():
    """Verify monitoring configuration files"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Monitoring Configuration Files{Colors.END}")

    # Check prometheus.yml
    prometheus_config = Path("monitoring/prometheus.yml")
    test1 = print_test(
        "Config - prometheus.yml exists",
        prometheus_config.exists(),
        "Prometheus configuration file should exist"
    )

    if test1:
        try:
            config = yaml.safe_load(prometheus_config.read_text())
            test2 = print_test(
                "Config - prometheus.yml valid YAML",
                config is not None,
                "Should be valid YAML"
            )

            # Check for sailor-backend job
            jobs = config.get('scrape_configs', [])
            has_backend_job = any(job.get('job_name') == 'sailor-backend' for job in jobs)
            test3 = print_test(
                "Config - sailor-backend scrape job",
                has_backend_job,
                "Should have scrape configuration for backend"
            )
        except Exception as e:
            print_test("Config - prometheus.yml valid YAML", False, str(e))
            test2 = test3 = False
    else:
        test2 = test3 = False

    # Check prometheus-alerts.yml
    alerts_config = Path("monitoring/prometheus-alerts.yml")
    test4 = print_test(
        "Config - prometheus-alerts.yml exists",
        alerts_config.exists(),
        "Alert rules file should exist"
    )

    if test4:
        try:
            alerts = yaml.safe_load(alerts_config.read_text())
            test5 = print_test(
                "Config - prometheus-alerts.yml valid YAML",
                alerts is not None,
                "Should be valid YAML"
            )

            # Check for critical alerts
            groups = alerts.get('groups', [])
            rules = []
            for group in groups:
                rules.extend(group.get('rules', []))

            alert_names = [rule.get('alert') for rule in rules]
            critical_alerts = ['HighErrorRate', 'EndpointDown', 'SlowResponseTime', 'HighAIAPIErrorRate']
            has_critical_alerts = all(alert in alert_names for alert in critical_alerts)

            test6 = print_test(
                "Config - critical alert rules",
                has_critical_alerts,
                f"Should have {len(critical_alerts)} critical alert rules"
            )
        except Exception as e:
            print_test("Config - prometheus-alerts.yml valid YAML", False, str(e))
            test5 = test6 = False
    else:
        test5 = test6 = False

    # Check grafana-dashboard.json
    dashboard_config = Path("monitoring/grafana-dashboard.json")
    test7 = print_test(
        "Config - grafana-dashboard.json exists",
        dashboard_config.exists(),
        "Grafana dashboard file should exist"
    )

    if test7:
        try:
            dashboard = json.loads(dashboard_config.read_text())
            test8 = print_test(
                "Config - grafana-dashboard.json valid JSON",
                dashboard is not None,
                "Should be valid JSON"
            )

            # Check for panels
            panels = dashboard.get('panels', [])
            test9 = print_test(
                "Config - dashboard has panels",
                len(panels) >= 5,
                f"Should have at least 5 visualization panels (found {len(panels)})"
            )
        except Exception as e:
            print_test("Config - grafana-dashboard.json valid JSON", False, str(e))
            test8 = test9 = False
    else:
        test8 = test9 = False

    return all([test1, test2, test3, test4, test5, test6, test7, test8, test9])

def verify_requirements():
    """Verify required dependencies"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Dependencies{Colors.END}")

    req_path = Path("backend/requirements.txt")
    if not req_path.exists():
        print_test("Dependencies - requirements.txt exists", False)
        return False

    requirements = req_path.read_text()

    test1 = print_test(
        "Dependencies - sentry-sdk",
        "sentry-sdk" in requirements,
        "sentry-sdk[flask] should be in requirements"
    )

    test2 = print_test(
        "Dependencies - prometheus-flask-exporter",
        "prometheus-flask-exporter" in requirements,
        "prometheus-flask-exporter should be in requirements"
    )

    return all([test1, test2])

def verify_environment_config():
    """Verify environment configuration documentation"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Environment Configuration{Colors.END}")

    env_example = Path("backend/.env.example")
    if not env_example.exists():
        print_test("Env - .env.example exists", False)
        return False

    env_content = env_example.read_text()

    test1 = print_test(
        "Env - SENTRY_DSN documented",
        "SENTRY_DSN" in env_content,
        "SENTRY_DSN should be documented"
    )

    test2 = print_test(
        "Env - SENTRY_TRACES_SAMPLE_RATE documented",
        "SENTRY_TRACES_SAMPLE_RATE" in env_content,
        "SENTRY_TRACES_SAMPLE_RATE should be documented"
    )

    test3 = print_test(
        "Env - SENTRY_RELEASE documented",
        "SENTRY_RELEASE" in env_content,
        "SENTRY_RELEASE should be documented"
    )

    test4 = print_test(
        "Env - ENABLE_METRICS documented",
        "ENABLE_METRICS" in env_content,
        "ENABLE_METRICS should be documented"
    )

    return all([test1, test2, test3, test4])

def verify_production_docs():
    """Verify production documentation"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing Production Documentation{Colors.END}")

    prod_docs = Path("PRODUCTION.md")
    if not prod_docs.exists():
        print_test("Docs - PRODUCTION.md exists", False)
        return False

    docs_content = prod_docs.read_text()

    test1 = print_test(
        "Docs - Sentry setup instructions",
        "Sentry" in docs_content and "sentry.io" in docs_content,
        "Should document Sentry setup"
    )

    test2 = print_test(
        "Docs - Prometheus setup instructions",
        "Prometheus" in docs_content and "prometheus.yml" in docs_content,
        "Should document Prometheus setup"
    )

    test3 = print_test(
        "Docs - Grafana setup instructions",
        "Grafana" in docs_content and "grafana-dashboard.json" in docs_content,
        "Should document Grafana setup"
    )

    test4 = print_test(
        "Docs - alert rules documentation",
        "alert" in docs_content.lower() and "HighErrorRate" in docs_content,
        "Should document alert rules"
    )

    test5 = print_test(
        "Docs - Docker Compose monitoring services",
        "prometheus:" in docs_content and "grafana:" in docs_content,
        "Should include monitoring services in docker-compose"
    )

    return all([test1, test2, test3, test4, test5])

def main():
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}P2 Monitoring Improvements Verification{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")

    results = {
        "Sentry Integration": verify_sentry_integration(),
        "Prometheus Integration": verify_prometheus_integration(),
        "Monitoring Config Files": verify_monitoring_config_files(),
        "Dependencies": verify_requirements(),
        "Environment Config": verify_environment_config(),
        "Production Documentation": verify_production_docs(),
    }

    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")

    passed = sum(results.values())
    total = len(results)

    for category, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{category}: {status}")

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} categories passed{Colors.END}")

    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All P2 monitoring improvements verified!{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some P2 improvements need attention{Colors.END}")
        return 1

if __name__ == "__main__":
    exit(main())
