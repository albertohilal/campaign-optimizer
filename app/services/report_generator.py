"""Services for consolidating analysis artifacts into a report payload."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.recommendations import RecommendationsService
from app.services.simulation_service import SimulationService


class ReportGeneratorService:
    """Build a consolidated dry-run report from analysis artifacts."""

    def __init__(
        self,
        recommendations_service: RecommendationsService | None = None,
        simulation_service: SimulationService | None = None,
    ) -> None:
        self.simulation_service = simulation_service or SimulationService()
        self.recommendations_service = recommendations_service or RecommendationsService(
            simulation_service=self.simulation_service,
        )

    def generate_report(
        self,
        snapshot: dict[str, Any],
        findings_payload: dict[str, Any],
        recommendations_payload: dict[str, Any] | None = None,
        simulation_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a consolidated report payload for UI, API, or later persistence."""

        findings = list(findings_payload.get("findings", []))
        simulation = simulation_payload or self.simulation_service.simulate(
            findings=findings,
        )
        recommendations = recommendations_payload or self.recommendations_service.build_recommendations(
            findings=findings,
            simulation=simulation,
        )

        recommendation_rows = list(recommendations.get("recommendations", []))
        prioritized_actions = list(simulation.get("prioritized_actions", []))

        return {
            "report_type": "analysis_report",
            "execution_mode": "dry_run",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "date_range": {
                "date_from": snapshot.get("date_from"),
                "date_to": snapshot.get("date_to"),
            },
            "summary": {
                "campaign_count": len(snapshot.get("campaigns", [])),
                "finding_count": len(findings),
                "recommendation_count": len(recommendation_rows),
                "simulated_action_count": len(prioritized_actions),
                "dry_run": True,
            },
            "overview": self._build_overview(snapshot, recommendations, simulation),
            "snapshot_summary": self._build_snapshot_summary(snapshot),
            "findings_summary": findings_payload.get("summary", {}),
            "recommendations_summary": recommendations.get("summary", {}),
            "simulation_summary": simulation.get("summary", {}),
            "campaigns": recommendations.get("campaigns", simulation.get("campaigns", [])),
            "findings": findings,
            "recommendations": recommendation_rows,
            "simulation": {
                "overview": simulation.get("overview", ""),
                "prioritized_actions": prioritized_actions,
            },
        }

    def _build_snapshot_summary(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Return a compact snapshot summary suitable for reports."""

        return {
            "date_from": snapshot.get("date_from"),
            "date_to": snapshot.get("date_to"),
            "campaign_count": len(snapshot.get("campaigns", [])),
            "campaign_metric_rows": len(snapshot.get("campaign_metrics", [])),
            "search_term_rows": len(snapshot.get("search_terms", [])),
        }

    def _build_overview(
        self,
        snapshot: dict[str, Any],
        recommendations: dict[str, Any],
        simulation: dict[str, Any],
    ) -> str:
        """Return a report-level overview sentence."""

        recommendation_rows = recommendations.get("recommendations", [])
        if not recommendation_rows:
            return (
                f"Report generated for {len(snapshot.get('campaigns', []))} campaigns with no dry-run recommendations."
            )

        top_recommendation = recommendation_rows[0]
        return (
            f"Report generated for {len(snapshot.get('campaigns', []))} campaigns. "
            f"Top dry-run recommendation: {top_recommendation['title']} for "
            f"{top_recommendation['campaign_name']}. "
            f"Simulation produced {len(simulation.get('prioritized_actions', []))} prioritized actions."
        )