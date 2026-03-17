"""Services for building executive campaign diagnosis summaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.services.recommendations import RecommendationsService


class CampaignDiagnosisService:
    """Aggregate findings and recommendations into campaign-level summaries."""

    def __init__(
        self,
        recommendations_service: RecommendationsService | None = None,
    ) -> None:
        self.recommendations_service = recommendations_service or RecommendationsService()

    def build_campaign_diagnosis(
        self,
        snapshot: dict[str, Any],
        findings_payload: dict[str, Any],
        recommendations_payload: dict[str, Any] | None = None,
        campaign_id: str | None = None,
    ) -> dict[str, Any]:
        """Return a campaign diagnosis summary for one or more campaigns."""

        findings = list(findings_payload.get("findings", []))
        recommendations = recommendations_payload or self.recommendations_service.build_recommendations(
            findings=findings,
        )

        metrics_by_campaign = self._group_metrics(snapshot.get("campaign_metrics", []))
        campaigns = self._group_campaigns(snapshot.get("campaigns", []))
        findings_by_campaign = self._group_findings(findings)
        recommendations_by_campaign = self._group_recommendations(
            recommendations.get("recommendations", []),
        )

        selected_campaign_ids = list(campaigns.keys() | metrics_by_campaign.keys() | findings_by_campaign.keys())
        if campaign_id is not None:
            selected_campaign_ids = [value for value in selected_campaign_ids if value == campaign_id]

        diagnosis_rows = [
            self._build_campaign_row(
                campaign_key=campaign_key,
                campaign_info=campaigns.get(campaign_key, {}),
                metrics=metrics_by_campaign.get(campaign_key, []),
                findings=findings_by_campaign.get(campaign_key, []),
                recommendations=recommendations_by_campaign.get(campaign_key, []),
            )
            for campaign_key in sorted(selected_campaign_ids)
        ]

        return {
            "dry_run": True,
            "date_range": {
                "date_from": snapshot.get("date_from"),
                "date_to": snapshot.get("date_to"),
            },
            "summary": {
                "campaign_count": len(diagnosis_rows),
                "finding_count": len(findings),
                "diagnosed_campaign_id": campaign_id,
            },
            "overview": self._build_overview(diagnosis_rows, campaign_id),
            "campaigns": diagnosis_rows,
        }

    def _group_campaigns(self, campaigns: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for campaign in campaigns:
            campaign_key = str(campaign.get("campaign_id"))
            grouped[campaign_key] = campaign
        return grouped

    def _group_metrics(
        self,
        campaign_metrics: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for metric_row in campaign_metrics:
            campaign_key = str(metric_row.get("campaign_id"))
            grouped[campaign_key].append(metric_row)
        return grouped

    def _group_findings(
        self,
        findings: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for finding in findings:
            metadata = finding.get("metadata", {})
            campaign_key = str(
                metadata.get("campaign_id")
                or finding.get("campaign_id")
                or metadata.get("campaign_name")
                or finding.get("campaign_name")
                or "unknown"
            )
            grouped[campaign_key].append(finding)
        return grouped

    def _group_recommendations(
        self,
        recommendations: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for recommendation in recommendations:
            campaign_key = str(
                recommendation.get("campaign_id")
                or recommendation.get("campaign_name")
                or "unknown"
            )
            grouped[campaign_key].append(recommendation)
        return grouped

    def _build_campaign_row(
        self,
        campaign_key: str,
        campaign_info: dict[str, Any],
        metrics: list[dict[str, Any]],
        findings: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        deduped_findings = self._deduplicate_findings(findings)
        total_cost = round(sum(self._to_float(metric.get("cost")) for metric in metrics), 2)
        total_conversions = round(
            sum(self._to_float(metric.get("conversions")) for metric in metrics),
            2,
        )
        total_impressions = sum(int(self._to_float(metric.get("impressions"))) for metric in metrics)
        total_clicks = sum(int(self._to_float(metric.get("clicks"))) for metric in metrics)
        average_ctr = round((total_clicks / total_impressions) * 100, 2) if total_impressions else 0.0
        average_cpc = round(total_cost / total_clicks, 2) if total_clicks else 0.0

        campaign_name = str(
            campaign_info.get("campaign_name")
            or self._campaign_name_from_findings(findings)
            or f"Campaign {campaign_key}"
        )

        top_issues = self._build_top_issues(deduped_findings)
        top_waste_search_terms = self._build_top_waste_search_terms(findings)
        recommended_priorities = self._build_recommended_priorities(recommendations)

        return {
            "campaign_id": campaign_info.get("campaign_id") or campaign_key,
            "campaign_name": campaign_name,
            "overall_status": self._overall_status(deduped_findings),
            "total_cost": total_cost,
            "total_conversions": total_conversions,
            "average_ctr": average_ctr,
            "average_cpc": average_cpc,
            "top_issues": top_issues,
            "top_waste_search_terms": top_waste_search_terms,
            "recommended_priorities": recommended_priorities,
        }

    def _deduplicate_findings(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}

        for finding in findings:
            code = str(finding.get("code", "unknown"))
            metadata = finding.get("metadata", {})
            current = deduped.get(code)
            clicks = self._to_float(metadata.get("clicks"))

            if current is None:
                deduped[code] = {
                    "code": code,
                    "severity": str(finding.get("severity", "medium")),
                    "message": str(finding.get("message", "")),
                    "count": 1,
                    "max_clicks": clicks,
                    "campaign_name": metadata.get("campaign_name") or finding.get("campaign_name"),
                }
                continue

            current["count"] += 1
            current["max_clicks"] = max(self._to_float(current.get("max_clicks")), clicks)

        return sorted(
            deduped.values(),
            key=lambda finding: (
                -self._severity_score(str(finding.get("severity", "medium"))),
                -int(finding.get("count", 0)),
                -self._to_float(finding.get("max_clicks")),
            ),
        )

    def _build_top_issues(self, deduped_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "code": finding["code"],
                "severity": finding["severity"],
                "count": finding["count"],
                "summary": finding["message"],
            }
            for finding in deduped_findings[:3]
        ]

    def _build_top_waste_search_terms(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        terms: dict[str, dict[str, Any]] = {}

        for finding in findings:
            if finding.get("code") != "search_term_without_conversions":
                continue

            metadata = finding.get("metadata", {})
            search_term = str(metadata.get("search_term", "")).strip()
            if not search_term:
                continue

            current = terms.get(search_term)
            clicks = self._to_float(metadata.get("clicks"))
            conversions = self._to_float(metadata.get("conversions"))

            if current is None:
                terms[search_term] = {
                    "search_term": search_term,
                    "clicks": int(clicks),
                    "conversions": conversions,
                }
                continue

            current["clicks"] = max(int(current.get("clicks", 0)), int(clicks))
            current["conversions"] = min(self._to_float(current.get("conversions")), conversions)

        return sorted(
            terms.values(),
            key=lambda item: (-int(item.get("clicks", 0)), item["search_term"]),
        )[:5]

    def _build_recommended_priorities(
        self,
        recommendations: list[dict[str, Any]],
    ) -> list[str]:
        best_by_action: dict[str, int] = {}

        for recommendation in recommendations:
            action_type = str(recommendation.get("action_type", "manual_review"))
            priority_score = int(recommendation.get("priority_score", 0))
            current = best_by_action.get(action_type)
            if current is None or priority_score > current:
                best_by_action[action_type] = priority_score

        return [
            action_type
            for action_type, _ in sorted(
                best_by_action.items(),
                key=lambda item: (-item[1], item[0]),
            )[:3]
        ]

    def _overall_status(self, deduped_findings: list[dict[str, Any]]) -> str:
        codes = {str(finding.get("code")) for finding in deduped_findings}

        if "spend_without_conversions" in codes:
            return "critical"

        if "low_ctr" in codes and "high_average_cpc" in codes:
            return "critical"

        if codes & {"low_ctr", "high_average_cpc", "search_term_without_conversions", "paused_campaign"}:
            return "warning"

        return "healthy"

    def _build_overview(
        self,
        campaigns: list[dict[str, Any]],
        campaign_id: str | None,
    ) -> str:
        if not campaigns:
            if campaign_id is not None:
                return f"No diagnosis data was produced for campaign {campaign_id}."
            return "No campaign diagnosis data was produced for the requested date range."

        critical_count = sum(1 for campaign in campaigns if campaign["overall_status"] == "critical")
        warning_count = sum(1 for campaign in campaigns if campaign["overall_status"] == "warning")

        return (
            f"Built diagnosis summary for {len(campaigns)} campaigns: "
            f"{critical_count} critical and {warning_count} warning."
        )

    def _campaign_name_from_findings(self, findings: list[dict[str, Any]]) -> str | None:
        for finding in findings:
            metadata = finding.get("metadata", {})
            campaign_name = metadata.get("campaign_name") or finding.get("campaign_name")
            if campaign_name:
                return str(campaign_name)
        return None

    @staticmethod
    def _severity_score(severity: str) -> int:
        return {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
        }.get(severity, 0)

    @staticmethod
    def _to_float(value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default