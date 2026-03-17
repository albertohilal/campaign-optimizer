from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Action:
    action_type: str
    entity: str
    entity_id: str
    campaign_id: str | None
    priority: int
    reason: str
    source_finding_type: str
    params: dict[str, Any] = field(default_factory=dict)
    requires_review: bool = True


class ActionEngine:
    """
    Convert findings into prioritized optimization actions.

    This engine is deterministic and read-only by itself: it only returns
    proposed actions. Execution against Google Ads should happen elsewhere.
    """

    RESTRICTIVENESS_ORDER = {
        "pause_keyword": 100,
        "add_negative_keyword": 90,
        "decrease_bid": 70,
        "decrease_budget": 60,
        "increase_bid": 40,
        "increase_budget": 30,
        "review_search_terms": 20,
        "review_ad_copy": 10,
        "review_landing_page": 10,
        "flag_for_manual_review": 5,
    }

    def generate_actions(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raw_actions: list[Action] = []

        for finding in findings:
            raw_actions.extend(self._actions_from_finding(finding))

        deduped = self._deduplicate_actions(raw_actions)
        resolved = self._resolve_conflicts(deduped)
        sorted_actions = sorted(
            resolved,
            key=lambda action: (
                -action.priority,
                -self.RESTRICTIVENESS_ORDER.get(action.action_type, 0),
            ),
        )
        return [self._to_dict(action) for action in sorted_actions]

    def _actions_from_finding(self, finding: dict[str, Any]) -> list[Action]:
        finding_type = finding.get("type")
        entity = finding.get("entity", "unknown")
        entity_id = finding.get("entity_id", "unknown")
        campaign_id = finding.get("campaign_id")
        metrics = finding.get("metrics", {})
        confidence = float(finding.get("confidence", 0.5))
        severity = str(finding.get("severity", "medium"))

        if finding_type == "high_cpc_low_conversion":
            return self._rule_high_cpc_low_conversion(
                entity, entity_id, campaign_id, metrics, confidence, severity
            )

        if finding_type == "high_average_cpc":
            return self._rule_high_average_cpc(
                entity, entity_id, campaign_id, metrics, confidence, severity
            )

        if finding_type == "low_ctr":
            return self._rule_low_ctr(
                entity, entity_id, campaign_id, metrics, confidence, severity
            )

        if finding_type == "irrelevant_search_term_spend":
            return self._rule_irrelevant_search_term_spend(
                entity,
                entity_id,
                campaign_id,
                metrics,
                confidence,
                severity,
                finding,
            )

        if finding_type == "budget_limited":
            return self._rule_budget_limited(
                entity, entity_id, campaign_id, metrics, confidence, severity
            )

        if finding_type == "rank_limited":
            return self._rule_rank_limited(
                entity, entity_id, campaign_id, metrics, confidence, severity
            )

        if finding_type == "high_spend_no_conversions":
            return self._rule_high_spend_no_conversions(
                entity, entity_id, campaign_id, metrics, confidence, severity
            )

        if finding_type == "paused_campaign":
            return [
                Action(
                    action_type="flag_for_manual_review",
                    entity=entity,
                    entity_id=entity_id,
                    campaign_id=campaign_id,
                    priority=self._priority(35, severity, confidence),
                    reason="Campaign is paused; automatic optimization should be reviewed manually.",
                    source_finding_type="paused_campaign",
                    params={},
                    requires_review=True,
                )
            ]

        return [
            Action(
                action_type="flag_for_manual_review",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=30,
                reason=f"Unhandled finding type: {finding_type}",
                source_finding_type=str(finding_type or "unknown"),
                params={"original_finding": finding},
                requires_review=True,
            )
        ]

    def _rule_high_cpc_low_conversion(
        self,
        entity: str,
        entity_id: str,
        campaign_id: str | None,
        metrics: dict[str, Any],
        confidence: float,
        severity: str,
    ) -> list[Action]:
        cpc = float(metrics.get("cpc", 0))
        conversions = float(metrics.get("conversions", 0))
        clicks = int(metrics.get("clicks", 0))

        if conversions == 0 and clicks >= 20:
            return [
                Action(
                    action_type="pause_keyword",
                    entity=entity,
                    entity_id=entity_id,
                    campaign_id=campaign_id,
                    priority=self._priority(95, severity, confidence),
                    reason=f"CPC alto ({cpc}) con 0 conversiones y {clicks} clicks",
                    source_finding_type="high_cpc_low_conversion",
                    requires_review=True,
                )
            ]

        return [
            Action(
                action_type="decrease_bid",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(82, severity, confidence),
                reason=f"CPC alto ({cpc}) con performance insuficiente",
                source_finding_type="high_cpc_low_conversion",
                params={"percentage": 10},
                requires_review=True,
            )
        ]

    def _rule_high_average_cpc(
        self,
        entity: str,
        entity_id: str,
        campaign_id: str | None,
        metrics: dict[str, Any],
        confidence: float,
        severity: str,
    ) -> list[Action]:
        cpc = float(metrics.get("cpc", 0))

        return [
            Action(
                action_type="decrease_bid",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(72, severity, confidence),
                reason=f"Average CPC alto detectado ({cpc}). Conviene moderar puja y revisar eficiencia.",
                source_finding_type="high_average_cpc",
                params={"percentage": 10},
                requires_review=True,
            ),
            Action(
                action_type="flag_for_manual_review",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(58, severity, confidence),
                reason="High average CPC should be reviewed before stronger actions are applied.",
                source_finding_type="high_average_cpc",
                params={},
                requires_review=True,
            ),
        ]

    def _rule_low_ctr(
        self,
        entity: str,
        entity_id: str,
        campaign_id: str | None,
        metrics: dict[str, Any],
        confidence: float,
        severity: str,
    ) -> list[Action]:
        ctr = float(metrics.get("ctr", 0))

        return [
            Action(
                action_type="review_ad_copy",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(65, severity, confidence),
                reason=f"CTR bajo detectado ({ctr:.2f}%)",
                source_finding_type="low_ctr",
                requires_review=True,
            )
        ]

    def _rule_irrelevant_search_term_spend(
        self,
        entity: str,
        entity_id: str,
        campaign_id: str | None,
        metrics: dict[str, Any],
        confidence: float,
        severity: str,
        finding: dict[str, Any],
    ) -> list[Action]:
        search_term = finding.get("search_term", "")

        return [
            Action(
                action_type="add_negative_keyword",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(92, severity, confidence),
                reason=f"Término irrelevante con gasto: {search_term}",
                source_finding_type="irrelevant_search_term_spend",
                params={"negative_keyword": search_term},
                requires_review=True,
            ),
            Action(
                action_type="review_search_terms",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(70, severity, confidence),
                reason="Revisar términos de búsqueda relacionados",
                source_finding_type="irrelevant_search_term_spend",
                requires_review=True,
            ),
        ]

    def _rule_budget_limited(
        self,
        entity: str,
        entity_id: str,
        campaign_id: str | None,
        metrics: dict[str, Any],
        confidence: float,
        severity: str,
    ) -> list[Action]:
        lost_is_budget = float(metrics.get("lost_impression_share_budget", 0))

        return [
            Action(
                action_type="increase_budget",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(78, severity, confidence),
                reason=f"Campaña limitada por presupuesto ({lost_is_budget:.2f}%)",
                source_finding_type="budget_limited",
                params={"percentage": 15},
                requires_review=True,
            )
        ]

    def _rule_rank_limited(
        self,
        entity: str,
        entity_id: str,
        campaign_id: str | None,
        metrics: dict[str, Any],
        confidence: float,
        severity: str,
    ) -> list[Action]:
        lost_is_rank = float(metrics.get("lost_impression_share_rank", 0))

        return [
            Action(
                action_type="increase_bid",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(74, severity, confidence),
                reason=f"Campaña limitada por ranking ({lost_is_rank:.2f}%)",
                source_finding_type="rank_limited",
                params={"percentage": 10},
                requires_review=True,
            )
        ]

    def _rule_high_spend_no_conversions(
        self,
        entity: str,
        entity_id: str,
        campaign_id: str | None,
        metrics: dict[str, Any],
        confidence: float,
        severity: str,
    ) -> list[Action]:
        cost = float(metrics.get("cost", 0))
        clicks = int(metrics.get("clicks", 0))

        return [
            Action(
                action_type="flag_for_manual_review",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(93, severity, confidence),
                reason=f"Gasto alto sin conversiones. Cost={cost}, clicks={clicks}",
                source_finding_type="high_spend_no_conversions",
                requires_review=True,
            ),
            Action(
                action_type="decrease_budget",
                entity=entity,
                entity_id=entity_id,
                campaign_id=campaign_id,
                priority=self._priority(80, severity, confidence),
                reason="Reducir presupuesto hasta revisar calidad del tráfico",
                source_finding_type="high_spend_no_conversions",
                params={"percentage": 10},
                requires_review=True,
            ),
        ]

    def _deduplicate_actions(self, actions: list[Action]) -> list[Action]:
        best_by_key: dict[tuple[str, str, str], Action] = {}

        for action in actions:
            key = (action.action_type, action.entity, action.entity_id)
            current = best_by_key.get(key)
            if current is None or action.priority > current.priority:
                best_by_key[key] = action

        return list(best_by_key.values())

    def _resolve_conflicts(self, actions: list[Action]) -> list[Action]:
        grouped: dict[tuple[str, str], list[Action]] = {}

        for action in actions:
            key = (action.entity, action.entity_id)
            grouped.setdefault(key, []).append(action)

        resolved: list[Action] = []

        for entity_actions in grouped.values():
            strongest = max(
                entity_actions,
                key=lambda action: (
                    self.RESTRICTIVENESS_ORDER.get(action.action_type, 0),
                    action.priority,
                ),
            )

            incompatible = {
                "pause_keyword": {"increase_bid", "decrease_bid", "review_ad_copy"},
                "add_negative_keyword": set(),
                "decrease_bid": {"increase_bid"},
                "increase_bid": {"decrease_bid"},
                "decrease_budget": {"increase_budget"},
                "increase_budget": {"decrease_budget"},
            }

            kept: list[Action] = []
            for action in entity_actions:
                if action == strongest:
                    kept.append(action)
                    continue

                blocked = incompatible.get(strongest.action_type, set())
                if action.action_type in blocked:
                    continue

                kept.append(action)

            resolved.extend(kept)

        return resolved

    def _priority(self, base: int, severity: str, confidence: float) -> int:
        severity_bonus = {
            "low": -5,
            "medium": 0,
            "high": 5,
            "critical": 10,
        }.get(str(severity).lower(), 0)

        confidence_bonus = int((confidence - 0.5) * 20)
        priority = base + severity_bonus + confidence_bonus
        return max(0, min(100, priority))

    def _to_dict(self, action: Action) -> dict[str, Any]:
        return {
            "action_type": action.action_type,
            "entity": action.entity,
            "entity_id": action.entity_id,
            "campaign_id": action.campaign_id,
            "priority": action.priority,
            "reason": action.reason,
            "source_finding_type": action.source_finding_type,
            "params": action.params,
            "requires_review": action.requires_review,
        }