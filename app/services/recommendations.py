"""Services for turning findings and simulated actions into recommendations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.services.simulation_service import SimulationService


class RecommendationsService:
    """Build a stable, UI-friendly recommendations payload in dry-run mode."""

    def __init__(self, simulation_service: SimulationService | None = None) -> None:
        self.simulation_service = simulation_service or SimulationService()

    def build_recommendations(
        self,
        findings: list[dict[str, Any]] | None = None,
        simulation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return dry-run recommendations derived from findings and simulated actions."""

        source_findings = findings or []
        simulation_payload = simulation or self.simulation_service.simulate(
            findings=source_findings,
        )

        prioritized_actions = list(simulation_payload.get("prioritized_actions", []))
        recommendations = [
            self._recommendation_from_action(action) for action in prioritized_actions
        ]
        campaigns = self._build_campaign_recommendations(
            simulation_payload.get("campaigns", []),
            recommendations,
            source_findings,
        )

        return {
            "dry_run": True,
            "summary": {
                "finding_count": len(source_findings),
                "recommendation_count": len(recommendations),
                "campaign_count": len(campaigns),
                "highest_priority": recommendations[0]["priority_score"]
                if recommendations
                else 0,
                "requires_human_review": any(
                    recommendation["requires_review"]
                    for recommendation in recommendations
                ),
            },
            "overview": self._build_overview(campaigns, recommendations),
            "campaigns": campaigns,
            "recommendations": recommendations,
        }

    def _recommendation_from_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Convert a prioritized simulated action into a recommendation row."""

        campaign_key = action.get("campaign_id") or action.get("campaign_name") or "unknown"
        action_type = str(action.get("action_type", "manual_review"))
        rank = int(action.get("rank", 0))

        return {
            "recommendation_id": f"{campaign_key}:{action_type}:{rank}",
            "campaign_id": action.get("campaign_id"),
            "campaign_name": action.get("campaign_name"),
            "priority": action.get("priority_label", "medium"),
            "priority_score": int(action.get("priority", 0)),
            "title": action.get("action_label", "Manual review required"),
            "detail": action.get("explanation") or action.get("reason", ""),
            "reason": action.get("reason", ""),
            "action_type": action_type,
            "source_finding_type": action.get("source_finding_type", "unknown"),
            "requires_review": bool(action.get("requires_review", True)),
            "dry_run": True,
        }

    def _build_campaign_recommendations(
        self,
        campaign_summaries: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return recommendation summaries grouped by campaign."""

        recommendations_by_campaign: dict[str, list[dict[str, Any]]] = defaultdict(list)
        finding_counts: dict[str, int] = defaultdict(int)
        campaign_lookup: dict[str, dict[str, Any]] = {}

        for campaign in campaign_summaries:
            key = str(campaign.get("campaign_id") or campaign.get("campaign_name") or "unknown")
            campaign_lookup[key] = campaign

        for recommendation in recommendations:
            key = str(
                recommendation.get("campaign_id")
                or recommendation.get("campaign_name")
                or "unknown"
            )
            recommendations_by_campaign[key].append(recommendation)

        for finding in findings:
            metadata = finding.get("metadata", {})
            key = str(
                metadata.get("campaign_id")
                or metadata.get("campaign_name")
                or finding.get("campaign_id")
                or finding.get("campaign_name")
                or "unknown"
            )
            finding_counts[key] += 1

        grouped_campaigns: list[dict[str, Any]] = []

        for key in sorted(
            set(campaign_lookup) | set(recommendations_by_campaign) | set(finding_counts),
            key=lambda item: (
                -max(
                    [r.get("priority_score", 0) for r in recommendations_by_campaign.get(item, [])]
                    or [0]
                ),
                item,
            ),
        ):
            recommendation_rows = recommendations_by_campaign.get(key, [])
            campaign_summary = campaign_lookup.get(key, {})
            campaign_name = (
                campaign_summary.get("campaign_name")
                or (recommendation_rows[0].get("campaign_name") if recommendation_rows else None)
                or f"Campaign {key}"
            )
            highest_priority = max(
                [recommendation.get("priority_score", 0) for recommendation in recommendation_rows]
                or [0]
            )

            grouped_campaigns.append(
                {
                    "campaign_id": campaign_summary.get("campaign_id")
                    or (recommendation_rows[0].get("campaign_id") if recommendation_rows else key),
                    "campaign_name": campaign_name,
                    "finding_count": finding_counts.get(key, campaign_summary.get("finding_count", 0)),
                    "recommendation_count": len(recommendation_rows),
                    "highest_priority": highest_priority,
                    "summary_text": self._campaign_summary_text(
                        campaign_name,
                        finding_counts.get(key, campaign_summary.get("finding_count", 0)),
                        recommendation_rows,
                    ),
                    "top_recommendations": recommendation_rows[:3],
                }
            )

        return grouped_campaigns

    def _build_overview(
        self,
        campaigns: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> str:
        """Return a readable overview sentence for API or UI headers."""

        if not recommendations:
            return (
                "No recommendations were generated. The current analysis remains in dry-run mode."
            )

        top_recommendation = recommendations[0]
        return (
            f"Generated {len(recommendations)} dry-run recommendations across {len(campaigns)} campaigns. "
            f"Top recommendation: {top_recommendation['title']} for "
            f"{top_recommendation['campaign_name']} with {top_recommendation['priority']} priority."
        )

    def _campaign_summary_text(
        self,
        campaign_name: str,
        finding_count: int,
        recommendations: list[dict[str, Any]],
    ) -> str:
        """Return a short campaign narrative for recommendation cards."""

        if not recommendations:
            return (
                f"{campaign_name} has {finding_count} findings and no recommendations yet."
            )

        top_recommendation = recommendations[0]
        return (
            f"{campaign_name} has {finding_count} findings and {len(recommendations)} dry-run recommendations. "
            f"Top recommendation: {top_recommendation['title']} "
            f"({top_recommendation['priority_score']})."
        )