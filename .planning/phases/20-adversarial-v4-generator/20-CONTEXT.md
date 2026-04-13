# Phase 20: Adversarial v4 Generator - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (research settled key decisions)

<domain>
## Phase Boundary

Users can generate behavioral adversarial scenarios where ground truth is assigned from context signals — not the deceptive narrative — and these scenarios are distinguishable from v2 signal-conflict adversarials.

</domain>

<decisions>
## Implementation Decisions

### Adversarial Design (from research)
- AdversarialV4Generator is a NEW class — does NOT extend _inject_adversarial_signals
- v2 adversarial = signal-conflict (flip severity/zone/time); v4 adversarial = behavioral (deceptive narratives)
- 3 behavioral patterns: loitering_as_waiting, authorized_as_intrusion, environmental_as_human
- GT from assign_ground_truth_v2 on actual context signals (not narrative)
- _meta.adversarial_type distinguishes v2 (signal_conflict) from v4 (behavioral subtypes)
- New ADV_V4_* description pools in distributions.py — SEPARATE from existing pools (no contamination)
- adversarial_v4 track added to ALERT_SCHEMA track enum
- Isolated RNG: AdversarialV4Generator owns self.rng = np.random.RandomState(seed)
- generation_version = "v4" in _meta

### Claude's Discretion
- Internal generator implementation details
- Exact description pool content for each behavioral pattern
- How context signals are set for each pattern type

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/generators.py — ContradictoryGenerator (reference pattern for new generator)
- psai_bench/distributions.py — assign_ground_truth_v2, existing description pools
- psai_bench/schema.py — ALERT_SCHEMA track enum, _META_SCHEMA_V2 with adversarial_type
- psai_bench/cli.py — needs adversarial_v4 track wiring

</code_context>

<specifics>
No specific requirements beyond research decisions.
</specifics>

<deferred>
None.
</deferred>
