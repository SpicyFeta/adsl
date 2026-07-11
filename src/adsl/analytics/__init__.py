# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Advanced analytics and automated insights for ADR-009 run bundles."""

from adsl.analytics.bottlenecks import detect_bottlenecks, detect_vulnerabilities
from adsl.analytics.cross_run import detect_cross_run_patterns
from adsl.analytics.format import format_insights_markdown, format_insights_summary
from adsl.analytics.red_patterns import analyze_red_patterns
from adsl.analytics.recommendations import build_actionable_recommendations
from adsl.analytics.report import INSIGHTS_SCHEMA_VERSION, generate_insights_report
from adsl.analytics.risk import score_corridor_risks, score_node_risks, score_route_risks
from adsl.analytics.what_if import WHAT_IF_SCHEMA_VERSION, compare_what_if

__all__ = [
    "INSIGHTS_SCHEMA_VERSION",
    "WHAT_IF_SCHEMA_VERSION",
    "generate_insights_report",
    "compare_what_if",
    "detect_cross_run_patterns",
    "build_actionable_recommendations",
    "detect_bottlenecks",
    "detect_vulnerabilities",
    "score_node_risks",
    "score_route_risks",
    "score_corridor_risks",
    "analyze_red_patterns",
    "format_insights_markdown",
    "format_insights_summary",
]