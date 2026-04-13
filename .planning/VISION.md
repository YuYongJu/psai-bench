# PSAI-Bench Vision: What This Needs to Become

## The Problem We're Solving

Physical security companies are deploying LLM-based systems to triage camera alerts. Nobody has a rigorous way to test whether these systems actually work. The industry is selling "AI-powered security" without any standard way to measure if the AI adds value over a rule-based system or a coin flip.

PSAI-Bench exists to be **the benchmark that separates real AI triage from marketing.**

## What the Benchmark Provides (Our Job)

1. **Scenarios** — realistic, diverse, non-trivially-solvable security alert inputs
2. **Ground Truth** — defensible labels with clear justification
3. **Output Schema** — minimal contract for any system type (LLM, ML, rules, hybrid)
4. **Scoring Engine** — transparent, well-motivated metrics with documented formulas
5. **Statistical Tools** — significance testing, confidence intervals, run consistency
6. **Evaluation Protocol** — how to run a fair evaluation

## What the User Provides (Their Job)

1. **Their system** — prompt, model, pipeline, post-processing, whatever they built
2. **Their outputs** — conforming to our schema
3. That's it.

---

## v2.0: Fix the Foundation

### Scenario Quality Overhaul

**Problem:** v1.0 descriptions perfectly predict ground truth. Severity nearly perfectly predicts it. The benchmark is trivially solvable.

**Fix:**

1. **Context-dependent ground truth.** The same description ("Person detected near perimeter") can be THREAT, SUSPICIOUS, or BENIGN depending on:
   - Time: 2am at an unmanned solar farm → THREAT. 10am during scheduled maintenance → BENIGN.
   - Zone: Restricted high-voltage area → THREAT. Public parking lot → BENIGN.
   - Device history: Camera with 95% FPR → more likely BENIGN. Camera with 5% FPR → take seriously.
   - Recent events: Badge access 5 min ago → BENIGN (authorized). No badge access → SUSPICIOUS.

   Ground truth is determined by a **documented decision function** that combines context signals, not by category alone. The function is published so researchers can audit it.

2. **Shared description pool.** Descriptions appear across ALL ground truth classes. "Unusual movement detected" can be THREAT (nighttime, restricted zone, no badge) or BENIGN (daytime, parking lot, recent maintenance scheduled). Models must reason about the full context, not pattern-match on keywords.

3. **Severity as a noisy signal.** Real analytics systems miscategorize severity. A fire gets LOW because the analytics model was confused by fog. A bird gets HIGH because it was close to the camera. Severity correlates with ground truth (~70%) but doesn't determine it.

4. **Adversarial scenarios.** Deliberately constructed to have conflicting signals:
   - HIGH severity + BENIGN (analytics overreacted to wildlife)
   - LOW severity + THREAT (analytics underreacted to slow-moving intruder)
   - Night + restricted zone + recent badge access → BENIGN (authorized late-night maintenance)
   - Day + parking lot + no badge + loitering → THREAT (social engineering / tailgating)

### Ground Truth Justification

**Problem:** v1.0 mapping is "Arrest → SUSPICIOUS" with no justification. Different SOCs would disagree.

**Fix:**

1. **Decision rubric.** Published document explaining: "Given these context signals, here's why this is classified as X." Every ground truth label has a traceable reasoning chain.

2. **Consensus labels for ambiguous cases.** Some scenarios are genuinely ambiguous — reasonable operators would disagree. These get ground truth = SUSPICIOUS with a flag marking them as "ambiguous by design." A system that says THREAT or BENIGN on an ambiguous scenario isn't wrong — it's making a decisive call under uncertainty. Scoring handles this separately.

3. **Site-appropriate categories.** Remove shoplifting from solar farms. Remove road accidents from indoor facilities. Ground truth must make sense in the scenario's physical context.

### Scoring Formula v2

**Problem:** v1.0 aggregate formula is multiplicative, opaque, and has magic numbers (30% threshold, 2x multiplier).

**Fix:**

1. **Report metrics separately, don't collapse to one number.** The aggregate score hides more than it reveals. Report a dashboard:
   - **Threat Detection Rate** (TDR) — did you catch the threats?
   - **False Alarm Suppression Rate** (FASR) — did you suppress the noise?
   - **Decisiveness** — what fraction of predictions were definitive (THREAT or BENIGN vs SUSPICIOUS)?
   - **Calibration** (ECE) — are your confidence scores meaningful?
   - **Accuracy by difficulty** — easy/medium/hard breakdown

2. **If an aggregate is needed, make it additive and documented.**
   ```
   Aggregate = w1*TDR + w2*FASR + w3*Decisiveness + w4*(1-ECE)
   ```
   With published weights and justification for each. Users can also compute their own weighted aggregate with custom weights for their operational priorities.

3. **Decisiveness replaces SUSPICIOUS penalty.** Instead of a penalty cliff at 30%, measure the fraction of predictions that are definitive. This is a smoother, more informative metric.

### Output Schema v2

**Problem:** Requires reasoning (20-word min), assumes LLM, confidence is ambiguous.

**Fix:**

```json
{
  "alert_id": "string (required)",
  "verdict": "THREAT | SUSPICIOUS | BENIGN (required)",
  "confidence": "float 0-1, probability the verdict is correct (required)",
  "reasoning": "string (optional — for explainability analysis)",
  "processing_time_ms": "int (optional — for latency benchmarking)",
  "model_info": "object (optional — for reproducibility)"
}
```

- Confidence definition explicitly stated: P(verdict is correct)
- Reasoning optional — works for classifiers, not just LLMs
- Processing time optional — users measure on their infrastructure

---

## v3.0: Perception-Reasoning Gap (The Real Novel Contribution)

This is where the benchmark becomes genuinely interesting and publishable.

### Visual Track Done Right

**Problem:** v1.0 visual track just adds a video URI to the metadata. Nobody actually processes the video because the metadata already contains the answer.

**Fix:**

1. **Visual-only scenarios.** Some scenarios provide ONLY the video clip + minimal metadata (timestamp, camera ID). No description, no severity, no zone context. The system must derive everything from the video. This is the true test of visual perception.

2. **Contradictory scenarios.** Metadata says one thing, video shows another:
   - Description: "Routine activity" + Video: person cutting fence → THREAT (video overrides metadata)
   - Description: "Aggressive behavior" + Video: people playing basketball → BENIGN (video overrides metadata)
   
   This directly tests whether the model's visual perception can override textual priors.

3. **Frame extraction baseline.** Built-in baseline that extracts keyframes and uses image description, comparing to models that process the full video. Measures whether temporal understanding adds value.

### Temporal Sequences

Real security operations don't see isolated alerts — they see sequences. An alert in the context of what happened 5 minutes ago, 1 hour ago, that morning.

1. **Alert sequences.** Groups of 3-5 related alerts that build a narrative. The system must triage each alert in context of the previous ones.
2. **Escalation patterns.** Test whether the system correctly escalates when a pattern emerges across multiple alerts.

---

## v4.0: Operational Realism

### Dispatch Decisions

Move beyond 3-class classification to actual operational decisions:
- Dispatch armed response (highest cost, fastest)
- Dispatch security patrol (medium cost, slower)
- Queue for operator review in N minutes
- Auto-suppress (no action)
- Request additional data (pan camera, check adjacent cameras)

### Cost-Aware Scoring

Every decision has a cost:
- False dispatch: $200-500 per armed response
- Missed threat: potentially catastrophic (weighted by site type)
- Operator review: $5-15 per alert (operator time)
- Auto-suppress: $0

Score = expected operational cost under the system's decisions vs. ground truth optimal decisions.

### Multi-Site Generalization

Test on scenarios from different site types (solar, substation, commercial, campus) and measure whether a system trained/prompted for one generalizes to others.

### Adversarial Robustness

Scenarios deliberately designed to fool AI systems:
- Loitering that looks like authorized waiting
- Authorized access that looks like intrusion
- Environmental events that look like human activity
- Social engineering patterns

---

## What This Means for the Codebase

### Keep
- CLI architecture (click-based, well-structured)
- Scoring engine (technically sound, just needs metric updates)
- Statistical tools (McNemar's, bootstrap CIs, run consistency)
- Test infrastructure (103 tests, good patterns)
- "Bring your own system" scoring path

### Rebuild
- Scenario generation (context-dependent GT, shared descriptions, noisy severity)
- Ground truth assignment (documented decision function, not hardcoded lookup)
- Distributions module (needs adversarial and contradictory scenarios)
- Output schema (simplify, make reasoning optional)
- Scoring formula (separate metrics, optional aggregate)

### Add
- Decision rubric documentation
- Visual-only track
- Contradictory scenarios (metadata vs video)
- Evaluation protocol document
- Example "bring your own system" integration guide
