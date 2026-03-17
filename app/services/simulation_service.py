"""Read-only simulation service for optimization actions."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.services.action_engine import ActionEngine


class SimulationService:
    """Build a UI-friendly simulation payload from findings and actions."""

    ANALYZER_TO_ACTION_ENGINE_MAP = {
        "spend_without_conversions": "high_spend_no_conversions",
        "low_ctr": "low_ctr",
        "high_average_cpc": "high_average_cpc",
        "search_term_without_conversions": "irrelevant_search_term_spend",
        "paused_campaign": "paused_campaign",
    }

    def __init__(self, action_engine: ActionEngine | None = None) -> None:
        self.action_engine = action_engine or ActionEngine()

    def simulate(
        self,
        findings: list[dict[str, Any]] | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Return a read-only simulation payload for UI or API consumers.

        Accepts analyzer findings, normalized action-engine findings,
        direct actions, or any combination of them.
        """
        source_findings = findings or []
        source_actions = actions or []

        normalized_findings = [
            self._normalize_finding(finding) for finding in source_findings
        ]
        generated_actions = (
            self.action_engine.generate_actions(normalized_findings)
            if normalized_findings
            else []
        )

        merged_actions = self._merge_actions(source_actions, generated_actions)
        campaign_context = self._build_campaign_context(source_findings, merged_actions)
        prioritized_actions = self._build_prioritized_actions(
            merged_actions,
            campaign_context,
        )
        campaign_summaries = self._build_campaign_summaries(
            campaign_context,
            source_findings,
            prioritized_actions,
        )

        return {
            "simulation": True,
            "execution_mode": "dry_run",
            "summary": {
                "campaign_count": len(campaign_summaries),
                "finding_count": len(source_findings),
                "provided_action_count": len(source_actions),
                "generated_action_count": len(generated_actions),
                "final_action_count": len(prioritized_actions),
                "highest_priority": prioritized_actions[0]["priority"]
                if prioritized_actions
                else 0,
                "requires_human_review": any(
                    action.get("requires_review", False)
                    for action in prioritized_actions
                ),
            },
            "overview": self._build_overview(campaign_summaries, prioritized_actions),
            "campaigns": campaign_summaries,
            "prioritized_actions": prioritized_actions,
        }

    def _normalize_finding(self, finding: dict[str, Any]) -> dict[str, Any]:
        """Convert heterogeneous finding payloads into the action engine contract."""

        if "type" in finding and "entity" in finding and "entity_id" in finding:
            normalized = dict(finding)
            normalized.setdefault("severity", "medium")
            normalized.setdefault(
                "confidence",
                self._confidence_from_severity(
                    str(normalized.get("severity", "medium"))
                ),
            )
            normalized.setdefault("metrics", {})
            return normalized

        metadata = finding.get("metadata", {})
        code = str(finding.get("code", finding.get("type", "unknown")))
        severity = str(finding.get("severity", "medium")).lower()

        campaign_id = self._first_non_empty(
            metadata.get("campaign_id"),
            finding.get("campaign_id"),
        )
        campaign_name = self._first_non_empty(
            metadata.get("campaign_name"),
            finding.get("campaign_name"),
        )
        search_term = self._first_non_empty(
            metadata.get("search_term"),
            finding.get("search_term"),
        )

        if code == "search_term_without_conversions":
            entity = "search_term"
            entity_id = search_term or campaign_id or campaign_name or "unknown-search-term"
        else:
            entity = "campaign"
            entity_id = campaign_id or campaign_name or code

        return {
            "type": self.ANALYZER_TO_ACTION_ENGINE_MAP.get(code, code),
            "entity": entity,
            "entity_id": str(entity_id),
            "campaign_id": str(campaign_id) if campaign_id else None,
            "severity": severity,
            "confidence": self._confidence_from_severity(severity),
            "metrics": self._extract_metrics(metadata),
            "search_term": search_term,
            "message": finding.get("message"),
            "campaign_name": campaign_name,
            "metadata": metadata,
        }

    def _extract_metrics(self, metadata: dict[str, Any]) -> dict[str, Any]:
        metrics: dict[str, Any] = {}

        metric_map = {
            "ctr": "ctr",
            "cost": "cost",
            "conversions": "conversions",
            "clicks": "clicks",
            "average_cpc": "cpc",
            "cpc": "cpc",
            "lost_impression_share_budget": "lost_impression_share_budget",
            "lost_impression_share_rank": "lost_impression_share_rank",
        }

        for source_key, target_key in metric_map.items():
            value = metadata.get(source_key)
            if value is not None:
                metrics[target_key] = value

        return metrics

    def _merge_actions(
        self,
        provided_actions: list[dict[str, Any]],
        generated_actions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        best_by_key: dict[tuple[str, str, str, str | None], dict[str, Any]] = {}

        for raw_action in [*provided_actions, *generated_actions]:
            action = self._normalize_action(raw_action)
            key = (
                action["action_type"],
                action["entity"],
                action["entity_id"],
                action.get("campaign_id"),
            )
            current = best_by_key.get(key)
            if current is None or action["priority"] > current["priority"]:
                best_by_key[key] = action

        return sorted(
            best_by_key.values(),
            key=lambda action: (
                -int(action.get("priority", 0)),
                -self.action_engine.RESTRICTIVENESS_ORDER.get(
                    action.get("action_type", ""),
                    0,
                ),
            ),
        )

    def _normalize_action(self, action: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(action)
        normalized["action_type"] = str(
            normalized.get("action_type", "flag_for_manual_review")
        )
        normalized["entity"] = str(normalized.get("entity", "campaign"))
        normalized["entity_id"] = str(
            normalized.get("entity_id")
            or normalized.get("campaign_id")
            or normalized["action_type"]
        )
        normalized["campaign_id"] = self._string_or_none(normalized.get("campaign_id"))
        normalized["priority"] = self._safe_int(normalized.get("priority"), default=50)
        normalized["reason"] = str(normalized.get("reason", "No reason provided."))
        normalized["source_finding_type"] = str(
            normalized.get("source_finding_type", "manual_input")
        )
        normalized["params"] = dict(normalized.get("params", {}))
        normalized["requires_review"] = bool(normalized.get("requires_review", True))
        normalized["simulation_only"] = True
        return normalized

    def _campaign_key_from_finding(self, finding: dict[str, Any]) -> str | None:
        metadata = finding.get("metadata", {})
        return self._first_non_empty(
            metadata.get("campaign_id"),
            finding.get("campaign_id"),
            metadata.get("campaign_name"),
            finding.get("campaign_name"),
        )

    def _campaign_key_from_action(self, action: dict[str, Any]) -> str | None:
        return self._first_non_empty(
            action.get("campaign_id"),
            action.get("campaign_name"),
            action.get("params", {}).get("campaign_name")
            if isinstance(action.get("params"), dict)
            else None,
            action.get("entity_id") if action.get("entity") == "campaign" else None,
        )

    def _build_campaign_context(
        self,
        findings: list[dict[str, Any]],
        actions: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        campaign_context: dict[str, dict[str, Any]] = {}

        for finding in findings:
            metadata = finding.get("metadata", {})
            campaign_id = self._first_non_empty(
                metadata.get("campaign_id"),
                finding.get("campaign_id"),
            )
            campaign_name = self._first_non_empty(
                metadata.get("campaign_name"),
                finding.get("campaign_name"),
            )
            key = self._first_non_empty(campaign_id, campaign_name)
            if not key:
                continue

            campaign_context[str(key)] = {
                "campaign_id": str(campaign_id) if campaign_id else None,
                "campaign_name": str(campaign_name or f"Campaign {key}"),
            }

        for action in actions:
            key = self._campaign_key_from_action(action)
            if not key:
                continue

            campaign_name = self._string_or_none(
                action.get("params", {}).get("campaign_name")
                if isinstance(action.get("params"), dict)
                else None
            )

            existing = campaign_context.get(str(key), {})
            campaign_context[str(key)] = {
                "campaign_id": self._string_or_none(action.get("campaign_id"))
                or existing.get("campaign_id"),
                "campaign_name": campaign_name
                or existing.get("campaign_name")
                or self._default_campaign_name(action),
            }

        return campaign_context

    def _build_prioritized_actions(
        self,
        actions: list[dict[str, Any]],
        campaign_context: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        prioritized_actions: list[dict[str, Any]] = []

        for rank, action in enumerate(actions, start=1):
            campaign_key = self._campaign_key_from_action(action)
            campaign_info = campaign_context.get(str(campaign_key), {}) if campaign_key else {}
            campaign_name = campaign_info.get("campaign_name") or self._default_campaign_name(action)

            prioritized_actions.append(
                {
                    "rank": rank,
                    "campaign_id": campaign_info.get("campaign_id")
                    or action.get("campaign_id"),
                    "campaign_name": campaign_name,
                    "action_type": action["action_type"],
                    "action_label": self._action_label(action),
                    "priority": action["priority"],
                    "priority_label": self._priority_label(action["priority"]),
                    "reason": action["reason"],
                    "explanation": self._action_explanation(action, campaign_name),
                    "entity": action["entity"],
                    "entity_id": action["entity_id"],
                    "source_finding_type": action["source_finding_type"],
                    "params": action["params"],
                    "requires_review": action["requires_review"],
                    "simulation_only": True,
                }
            )

        return prioritized_actions

    def _build_campaign_summaries(
        self,
        campaign_context: dict[str, dict[str, Any]],
        findings: list[dict[str, Any]],
        prioritized_actions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        findings_by_campaign: dict[str, list[dict[str, Any]]] = defaultdict(list)
        actions_by_campaign: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for finding in findings:
            key = self._campaign_key_from_finding(finding)
            if key:
                findings_by_campaign[str(key)].append(finding)

        for action in prioritized_actions:
            key = self._campaign_key_from_action(action)
            if key:
                actions_by_campaign[str(key)].append(action)

        summary_keys = (
            set(campaign_context.keys())
            | set(findings_by_campaign.keys())
            | set(actions_by_campaign.keys())
        )

        campaign_summaries: list[dict[str, Any]] = []

        for key in sorted(
            summary_keys,
            key=lambda item: (
                -max(
                    [a.get("priority", 0) for a in actions_by_campaign.get(item, [])] or [0]
                ),
                str(item),
            ),
        ):
            info = campaign_context.get(key, {})
            campaign_findings = findings_by_campaign.get(key, [])
            campaign_actions = actions_by_campaign.get(key, [])
            top_priority = max(
                [action.get("priority", 0) for action in campaign_actions] or [0]
            )

            campaign_name = info.get("campaign_name") or f"Campaign {key}"

            campaign_summaries.append(
                {
                    "campaign_id": info.get("campaign_id") or key,
                    "campaign_name": campaign_name,
                    "finding_count": len(campaign_findings),
                    "action_count": len(campaign_actions),
                    "highest_priority": top_priority,
                    "status": self._campaign_status(
                        top_priority,
                        len(campaign_actions),
                        len(campaign_findings),
                    ),
                    "summary_text": self._campaign_summary_text(
                        campaign_name,
                        len(campaign_findings),
                        campaign_actions,
                    ),
                    "top_actions": campaign_actions[:3],
                }
            )

        return campaign_summaries

    def _build_overview(
        self,
        campaign_summaries: list[dict[str, Any]],
        prioritized_actions: list[dict[str, Any]],
    ) -> str:
        if not prioritized_actions:
            return (
                "No prioritized actions were generated. "
                "The simulation is informational only."
            )

        top_action = prioritized_actions[0]
        return (
            f"Simulation generated {len(prioritized_actions)} prioritized actions across "
            f"{len(campaign_summaries)} campaigns. Top action: {top_action['action_label']} "
            f"for {top_action['campaign_name']} with priority {top_action['priority']}."
        )

    def _action_label(self, action: dict[str, Any]) -> str:
        params = action.get("params", {})
        percentage = params.get("percentage")

        labels = {
            "pause_keyword": "Pause keyword",
            "add_negative_keyword": "Add negative keyword",
            "decrease_bid": (
                f"Decrease bid {percentage}%" if percentage else "Decrease bid"
            ),
            "increase_bid": (
                f"Increase bid {percentage}%" if percentage else "Increase bid"
            ),
            "decrease_budget": (
                f"Decrease budget {percentage}%" if percentage else "Decrease budget"
            ),
            "increase_budget": (
                f"Increase budget {percentage}%" if percentage else "Increase budget"
            ),
            "review_search_terms": "Review search terms",
            "review_ad_copy": "Review ad copy",
            "review_landing_page": "Review landing page",
            "flag_for_manual_review": "Manual review required",
        }

        return labels.get(
            action["action_type"],
            action["action_type"].replace("_", " ").title(),
        )

    def _action_explanation(self, action: dict[str, Any], campaign_name: str) -> str:
        action_type = action["action_type"]
        params = action.get("params", {})
        percentage = params.get("percentage")
        negative_keyword = params.get("negative_keyword")
        target_label = self._entity_label(action)

        explanations = {
            "pause_keyword": (
                f"The simulation suggests pausing {target_label} in {campaign_name} because the current signal "
                f"indicates inefficient spend. This is a proposed action only and will not be sent to Google Ads."
            ),
            "add_negative_keyword": (
                f"The simulation suggests adding '{negative_keyword}' as a negative keyword in {campaign_name} "
                f"to block low-intent traffic. No live account change will be executed."
            ),
            "decrease_bid": (
                f"The simulation suggests reducing the bid for {target_label} in {campaign_name}"
                f"{f' by {percentage}%' if percentage else ''} to control cost while performance is reviewed."
            ),
            "increase_bid": (
                f"The simulation suggests increasing the bid for {target_label} in {campaign_name}"
                f"{f' by {percentage}%' if percentage else ''} to recover impression share lost by rank."
            ),
            "decrease_budget": (
                f"The simulation suggests lowering the budget in {campaign_name}"
                f"{f' by {percentage}%' if percentage else ''} until traffic quality is validated."
            ),
            "increase_budget": (
                f"The simulation suggests increasing the budget in {campaign_name}"
                f"{f' by {percentage}%' if percentage else ''} because the campaign appears constrained by budget."
            ),
            "review_search_terms": (
                f"The simulation recommends reviewing search terms in {campaign_name} to identify related queries "
                f"that may be draining spend without enough intent."
            ),
            "review_ad_copy": (
                f"The simulation recommends reviewing ad copy in {campaign_name} because CTR signals suggest the "
                f"message may not be matching user intent well enough."
            ),
            "review_landing_page": (
                f"The simulation recommends validating the landing page experience for {campaign_name} before any "
                f"account change is applied."
            ),
            "flag_for_manual_review": (
                f"The simulation flagged {campaign_name} for manual review because the finding requires human "
                f"validation before deciding on a live optimization."
            ),
        }

        base_explanation = explanations.get(
            action_type,
            f"The simulation proposes '{action_type}' for {campaign_name}. This is a dry-run recommendation only.",
        )
        return f"{base_explanation} Reason: {action['reason']}"

    def _campaign_summary_text(
        self,
        campaign_name: str,
        finding_count: int,
        actions: list[dict[str, Any]],
    ) -> str:
        if not actions and finding_count == 0:
            return (
                f"{campaign_name} has no findings or simulated actions "
                f"in the current payload."
            )

        if not actions:
            return (
                f"{campaign_name} has {finding_count} findings but no "
                f"prioritized actions yet."
            )

        top_action = actions[0]
        return (
            f"{campaign_name} has {finding_count} findings and {len(actions)} simulated actions. "
            f"Highest priority: {top_action['action_label']} ({top_action['priority']})."
        )

    def _campaign_status(
        self,
        top_priority: int,
        action_count: int,
        finding_count: int,
    ) -> str:
        if top_priority >= 85:
            return "critical_attention"
        if top_priority >= 65:
            return "attention_required"
        if action_count > 0 or finding_count > 0:
            return "monitor"
        return "stable"

    def _priority_label(self, priority: int) -> str:
        if priority >= 85:
            return "critical"
        if priority >= 70:
            return "high"
        if priority >= 45:
            return "medium"
        return "low"

    def _default_campaign_name(self, action: dict[str, Any]) -> str:
        campaign_id = action.get("campaign_id")
        if campaign_id:
            return f"Campaign {campaign_id}"
        return (
            f"{action.get('entity', 'Entity').title()} "
            f"{action.get('entity_id', 'unknown')}"
        )

    def _entity_label(self, action: dict[str, Any]) -> str:
        entity = action.get("entity", "entity")
        entity_id = action.get("entity_id", "unknown")
        if entity == "campaign":
            return f"campaign {entity_id}"
        if entity == "keyword":
            return f"keyword {entity_id}"
        if entity == "search_term":
            return f"search term {entity_id}"
        return f"{entity} {entity_id}"

    def _confidence_from_severity(self, severity: str) -> float:
        return {
            "low": 0.55,
            "medium": 0.70,
            "high": 0.85,
            "critical": 0.95,
        }.get(severity.lower(), 0.65)

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _string_or_none(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _first_non_empty(self, *values: Any) -> str | None:
        for value in values:
            normalized = self._string_or_none(value)
            if normalized is not None:
                return normalized
        return None