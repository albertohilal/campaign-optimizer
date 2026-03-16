"""Services for turning campaign snapshots into actionable findings."""

from __future__ import annotations

from typing import Any


class AnalyzerService:
    """Analyze normalized campaign snapshots and produce simple findings."""

    @staticmethod
    def _to_float(value: object, default: float = 0.0) -> float:
        """Return a float value for numeric comparisons used by the rules."""

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def analyze_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Return a summary and explicit findings for the provided snapshot."""

        campaigns = snapshot.get("campaigns", [])
        campaign_metrics = snapshot.get("campaign_metrics", [])
        search_terms = snapshot.get("search_terms", [])

        findings: list[dict[str, Any]] = []

        for campaign in campaigns:
            campaign_name = str(campaign.get("campaign_name", "Unknown campaign"))
            status = str(campaign.get("status", "")).upper()

            if status == "PAUSED":
                findings.append(
                    {
                        "code": "paused_campaign",
                        "severity": "low",
                        "message": f"Campaign '{campaign_name}' is paused and may not be contributing current performance data.",
                        "metadata": {
                            "campaign_id": campaign.get("campaign_id"),
                            "campaign_name": campaign_name,
                            "status": status,
                        },
                    }
                )

        for metric_row in campaign_metrics:
            campaign_name = str(metric_row.get("campaign_name", "Unknown campaign"))
            cost = self._to_float(metric_row.get("cost"))
            conversions = self._to_float(metric_row.get("conversions"))
            ctr = self._to_float(metric_row.get("ctr"))
            average_cpc = self._to_float(metric_row.get("average_cpc"))

            if conversions <= 0 and cost > 0:
                findings.append(
                    {
                        "code": "spend_without_conversions",
                        "severity": "high",
                        "message": f"Campaign '{campaign_name}' spent budget without generating conversions.",
                        "metadata": {
                            "campaign_id": metric_row.get("campaign_id"),
                            "campaign_name": campaign_name,
                            "cost": cost,
                            "conversions": conversions,
                        },
                    }
                )

            if ctr < 5:
                findings.append(
                    {
                        "code": "low_ctr",
                        "severity": "medium",
                        "message": f"Campaign '{campaign_name}' has a low click-through rate.",
                        "metadata": {
                            "campaign_id": metric_row.get("campaign_id"),
                            "campaign_name": campaign_name,
                            "ctr": ctr,
                        },
                    }
                )

            if average_cpc > 180:
                findings.append(
                    {
                        "code": "high_average_cpc",
                        "severity": "medium",
                        "message": f"Campaign '{campaign_name}' has a high average CPC.",
                        "metadata": {
                            "campaign_id": metric_row.get("campaign_id"),
                            "campaign_name": campaign_name,
                            "average_cpc": average_cpc,
                        },
                    }
                )

        for search_term_row in search_terms:
            clicks = self._to_float(search_term_row.get("clicks"))
            conversions = self._to_float(search_term_row.get("conversions"))

            if clicks > 0 and conversions == 0:
                search_term = str(search_term_row.get("search_term", "Unknown search term"))
                findings.append(
                    {
                        "code": "search_term_without_conversions",
                        "severity": "medium",
                        "message": f"Search term '{search_term}' generated clicks without conversions.",
                        "metadata": {
                            "campaign_id": search_term_row.get("campaign_id"),
                            "search_term": search_term,
                            "clicks": clicks,
                            "conversions": conversions,
                        },
                    }
                )

        return {
            "summary": {
                "campaign_count": len(campaigns),
                "metric_rows": len(campaign_metrics),
                "search_term_rows": len(search_terms),
            },
            "findings": findings,
        }