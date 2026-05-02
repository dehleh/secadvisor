"""Scoring engine — translates assessment responses into control and framework scores.

The maturity model:
  0  Not implemented / unknown
  1  Ad-hoc / informal
  2  Partially implemented
  3  Implemented consistently
  4  Optimized / monitored

Controls accumulate a weighted average of question scores referencing them.
Framework scores are the average of their constituent control scores,
expressed as 0-100.

The architecture mirrors SimCheck's risk scoring: a clean interface over a
rule-based implementation today, easily substituted with an ML scorer later
without changing call sites.
"""
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.services.questionnaire.schema import (
    ControlRef,
    Question,
    QuestionnaireVersion,
    QuestionType,
    ScoringRule,
)


MAX_MATURITY = 4
MIN_MATURITY = 0


@dataclass
class ControlScore:
    framework: str
    code: str
    maturity: float  # 0-4, may be fractional after weighted averaging
    weight_sum: float  # total weight contributed
    contributing_questions: list[str] = field(default_factory=list)

    @property
    def maturity_pct(self) -> int:
        """Maturity as a 0-100 percentage."""
        return round((self.maturity / MAX_MATURITY) * 100)


@dataclass
class FrameworkScore:
    framework: str
    score: int  # 0-100
    controls_assessed: int
    controls_total: int  # populated when control library is available
    avg_maturity: float

    @property
    def coverage_pct(self) -> int:
        if self.controls_total == 0:
            return 0
        return round((self.controls_assessed / self.controls_total) * 100)


@dataclass
class ScoringResult:
    overall_risk_score: int  # 0-100, higher = lower risk (i.e. better posture)
    framework_scores: dict[str, FrameworkScore]
    control_scores: dict[tuple[str, str], ControlScore]  # (framework, code) -> score
    response_count: int

    def get_framework(self, code: str) -> FrameworkScore | None:
        return self.framework_scores.get(code)


# --- Scoring rule application --------------------------------------------------


def _score_response(question: Question, value: Any) -> int | None:
    """Apply a question's ScoringRule to a response. Returns 0-MAX_MATURITY or None."""
    rule = question.scoring
    if rule is None or value is None:
        return None

    if question.type == QuestionType.BOOLEAN:
        key = "true" if value else "false"
        return rule.response_score.get(key)

    if question.type in (QuestionType.SINGLE_SELECT, QuestionType.SCALE):
        return rule.response_score.get(str(value))

    if question.type == QuestionType.MULTI_SELECT:
        if not isinstance(value, list) or not value:
            return None
        # Sum contributions, cap at MAX_MATURITY
        total = sum(rule.response_score.get(v, 0) for v in value)
        return min(total, MAX_MATURITY)

    return None


# --- The scoring engine -------------------------------------------------------


class ScoringEngine(ABC):
    """Interface for scoring assessment responses.

    Substitutable: a rules-based implementation today; an ML model could
    drop in later (e.g., learn calibrations from auditor outcomes) without
    touching consumers.
    """

    @abstractmethod
    def score(
        self,
        questionnaire: QuestionnaireVersion,
        responses: dict[str, Any],
    ) -> ScoringResult: ...


class RuleBasedScorer(ScoringEngine):
    """Deterministic scorer driven by ScoringRules on each Question.

    Algorithm:
      1. For each question with a scoring rule and a response, compute its
         maturity contribution (0-4).
      2. For each ControlRef on the question, add (maturity * weight) to that
         control's total, and weight to its weight_sum.
      3. Per control: maturity = total / weight_sum.
      4. Per framework: average maturity across all assessed controls,
         expressed as a 0-100 score.
      5. Overall risk score: weighted average of framework scores (equal
         weights for now; future: weight by company's target frameworks).
    """

    def score(
        self,
        questionnaire: QuestionnaireVersion,
        responses: dict[str, Any],
    ) -> ScoringResult:
        # (framework, code) -> [(maturity, weight, question_id), ...]
        contributions: dict[tuple[str, str], list[tuple[int, float, str]]] = defaultdict(list)

        responded = 0
        for question in questionnaire.all_questions():
            value = responses.get(question.id)
            if value is None or (isinstance(value, list) and not value):
                continue
            responded += 1

            score = _score_response(question, value)
            if score is None:
                continue
            weight = question.scoring.weight if question.scoring else 1.0
            for ref in question.control_refs:
                contributions[(ref.framework, ref.code)].append(
                    (score, weight, question.id)
                )

        # Aggregate per control
        control_scores: dict[tuple[str, str], ControlScore] = {}
        for (framework, code), entries in contributions.items():
            weight_sum = sum(w for _, w, _ in entries)
            if weight_sum == 0:
                continue
            weighted_maturity = sum(s * w for s, w, _ in entries) / weight_sum
            control_scores[(framework, code)] = ControlScore(
                framework=framework,
                code=code,
                maturity=weighted_maturity,
                weight_sum=weight_sum,
                contributing_questions=[qid for _, _, qid in entries],
            )

        # Aggregate per framework
        per_framework: dict[str, list[float]] = defaultdict(list)
        for (framework, _code), cs in control_scores.items():
            per_framework[framework].append(cs.maturity)

        framework_scores: dict[str, FrameworkScore] = {}
        for framework, maturities in per_framework.items():
            avg = sum(maturities) / len(maturities)
            framework_scores[framework] = FrameworkScore(
                framework=framework,
                score=round((avg / MAX_MATURITY) * 100),
                controls_assessed=len(maturities),
                controls_total=0,  # filled in by the API layer when control library is available
                avg_maturity=avg,
            )

        # Overall risk score: simple equal-weight average of framework scores
        if framework_scores:
            overall = round(
                sum(fs.score for fs in framework_scores.values()) / len(framework_scores)
            )
        else:
            overall = 0

        return ScoringResult(
            overall_risk_score=overall,
            framework_scores=framework_scores,
            control_scores=control_scores,
            response_count=responded,
        )


# Default scorer — swap to ML in the future without changing call sites
default_scorer: ScoringEngine = RuleBasedScorer()
