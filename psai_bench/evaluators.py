"""API evaluators for running frontier models on PSAI-Bench scenarios.

Each evaluator takes a PSAI-Bench alert, sends it to a model API, and returns
a standardized output dict. The system prompt instructs the model to act as
a security AI triage system.

Usage:
    from psai_bench.evaluators import ClaudeEvaluator, GPT4oEvaluator
    evaluator = ClaudeEvaluator(api_key="sk-...")
    result = evaluator.evaluate(scenario)

Environment variables:
    ANTHROPIC_API_KEY - for Claude
    OPENAI_API_KEY - for GPT-4o
    GOOGLE_API_KEY - for Gemini
"""

import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path

SYSTEM_PROMPT = """You are an AI security triage system for critical infrastructure sites. Your job is to analyze security alerts and classify them.

For each alert, you must:
1. Analyze all provided information (description, zone, device history, weather, time, recent events)
2. Classify the alert as one of: THREAT, SUSPICIOUS, or BENIGN
3. Provide a confidence score from 0.0 to 1.0
4. Explain your reasoning in detail

Definitions:
- THREAT: High confidence unauthorized activity requiring immediate response (dispatch guards, activate deterrents, notify operator)
- SUSPICIOUS: Ambiguous situation warranting operator review within SLA
- BENIGN: Normal environmental, wildlife, or authorized activity (auto-suppress, no action needed)

Important:
- A missed threat is much worse than a false alarm. When uncertain, lean toward SUSPICIOUS rather than BENIGN.
- But don't flag everything as SUSPICIOUS. You must make definitive calls when the evidence is clear.
- Consider the device's false positive rate, zone sensitivity, time of day, and recent activity patterns.
- Your confidence score should be calibrated: 0.8 confidence means you expect to be right ~80% of the time.

Respond with ONLY a JSON object in this exact format:
{
    "verdict": "THREAT" or "SUSPICIOUS" or "BENIGN",
    "confidence": 0.0 to 1.0,
    "reasoning": "Your detailed explanation (minimum 20 words)",
    "factors_considered": ["list", "of", "key", "factors"]
}"""


def _format_alert_for_prompt(scenario: dict) -> str:
    """Format a PSAI-Bench alert as a readable prompt for an LLM.

    Strips the _meta field (ground truth) so the model never sees the answer.
    """
    # Deep copy without _meta
    alert = {k: v for k, v in scenario.items() if k != "_meta"}

    # Also strip visual_data for metadata track (it's null anyway)
    if alert.get("track") == "metadata":
        alert.pop("visual_data", None)

    return (
        "Analyze this security alert and provide your triage decision:\n\n"
        f"```json\n{json.dumps(alert, indent=2, default=str)}\n```"
    )


def _parse_model_response(text: str, alert_id: str, latency_ms: int, model_info: dict) -> dict:
    """Parse a model's JSON response into a PSAI-Bench output dict.

    Handles common issues: markdown code blocks, extra text around JSON, etc.
    """
    # Strip markdown code blocks
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening ```json or ```
        lines = cleaned.split("\n")
        lines = lines[1:]  # remove first line (```)
        # Remove closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    # Try to find JSON object in the text
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start >= 0 and end > start:
        cleaned = cleaned[start:end]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Model didn't return valid JSON; create a fallback
        return {
            "alert_id": alert_id,
            "verdict": "SUSPICIOUS",  # default to safe option
            "confidence": 0.5,
            "reasoning": f"Model response was not valid JSON. Raw: {text[:200]}",
            "factors_considered": ["parse_error"],
            "processing_time_ms": latency_ms,
            "model_info": model_info,
            "_parse_error": True,
        }

    # Validate and normalize
    verdict = parsed.get("verdict", "SUSPICIOUS").upper()
    if verdict not in ("THREAT", "SUSPICIOUS", "BENIGN"):
        verdict = "SUSPICIOUS"

    confidence = parsed.get("confidence", 0.5)
    if not isinstance(confidence, (int, float)):
        confidence = 0.5
    confidence = max(0.0, min(1.0, float(confidence)))

    reasoning = parsed.get("reasoning", "No reasoning provided")
    factors = parsed.get("factors_considered", [])

    return {
        "alert_id": alert_id,
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": reasoning,
        "factors_considered": factors,
        "processing_time_ms": latency_ms,
        "model_info": model_info,
    }


class BaseEvaluator(ABC):
    """Base class for model evaluators."""

    def __init__(self, model_name: str, provider: str):
        self.model_name = model_name
        self.provider = provider
        self._request_count = 0
        self._total_cost = 0.0

    @abstractmethod
    def _call_api(self, prompt: str) -> tuple[str, int, float]:
        """Call the model API.

        Returns:
            (response_text, latency_ms, estimated_cost_usd)
        """
        pass

    def evaluate(self, scenario: dict) -> dict:
        """Evaluate a single scenario."""
        prompt = _format_alert_for_prompt(scenario)
        response_text, latency_ms, cost = self._call_api(prompt)
        self._request_count += 1
        self._total_cost += cost

        return _parse_model_response(
            response_text,
            scenario["alert_id"],
            latency_ms,
            {
                "name": self.model_name,
                "version": "api",
                "provider": self.provider,
                "estimated_cost_usd": cost,
            },
        )

    def evaluate_batch(
        self,
        scenarios: list[dict],
        progress: bool = True,
        delay_seconds: float = 0.0,
    ) -> list[dict]:
        """Evaluate a batch of scenarios with optional rate limiting."""
        results = []
        total = len(scenarios)

        for i, s in enumerate(scenarios):
            if progress and (i % 50 == 0 or i == total - 1):
                print(
                    f"  [{self.model_name}] {i+1}/{total} "
                    f"(${self._total_cost:.3f} total)"
                )

            try:
                result = self.evaluate(s)
            except Exception as e:
                # On API error, record as SUSPICIOUS with low confidence
                result = {
                    "alert_id": s["alert_id"],
                    "verdict": "SUSPICIOUS",
                    "confidence": 0.5,
                    "reasoning": f"API error: {str(e)[:200]}",
                    "factors_considered": ["api_error"],
                    "processing_time_ms": 0,
                    "model_info": {
                        "name": self.model_name,
                        "version": "api",
                        "provider": self.provider,
                        "estimated_cost_usd": 0,
                    },
                    "_api_error": True,
                }

            results.append(result)

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        print(
            f"  [{self.model_name}] Complete. "
            f"{total} scenarios, ${self._total_cost:.3f} total cost, "
            f"{sum(1 for r in results if r.get('_api_error')) } errors, "
            f"{sum(1 for r in results if r.get('_parse_error'))} parse failures"
        )
        return results


class ClaudeEvaluator(BaseEvaluator):
    """Evaluate using Anthropic Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        super().__init__(model, "anthropic")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.model = model

        import anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def _call_api(self, prompt: str) -> tuple[str, int, float]:
        start = time.time()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = int((time.time() - start) * 1000)

        text = response.content[0].text
        # Rough cost estimate based on token counts
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        # Sonnet pricing: $3/M input, $15/M output
        cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000

        return text, latency_ms, cost


class GPT4oEvaluator(BaseEvaluator):
    """Evaluate using OpenAI GPT-4o API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
    ):
        super().__init__(model, "openai")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        self.model = model

        import openai
        self.client = openai.OpenAI(api_key=self.api_key)

    def _call_api(self, prompt: str) -> tuple[str, int, float]:
        start = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        latency_ms = int((time.time() - start) * 1000)

        text = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        # GPT-4o pricing: $2.50/M input, $10/M output
        cost = (input_tokens * 2.5 + output_tokens * 10) / 1_000_000

        return text, latency_ms, cost


class GeminiEvaluator(BaseEvaluator):
    """Evaluate using Google Gemini API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
    ):
        super().__init__(model, "google")
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        self.model = model

        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def _call_api(self, prompt: str) -> tuple[str, int, float]:
        start = time.time()
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
        )
        latency_ms = int((time.time() - start) * 1000)

        text = response.text
        # Gemini Flash pricing: $0.075/M input, $0.30/M output (very cheap)
        input_tokens = response.usage_metadata.prompt_token_count or 0
        output_tokens = response.usage_metadata.candidates_token_count or 0
        cost = (input_tokens * 0.075 + output_tokens * 0.30) / 1_000_000

        return text, latency_ms, cost


# Registry for CLI use
EVALUATORS = {
    "claude-sonnet": ClaudeEvaluator,
    "gpt-4o": GPT4oEvaluator,
    "gemini-flash": GeminiEvaluator,
}
