# Architecture

## LangGraph flow

```
        ┌──────────┐
        │  detect  │  (rules only: data-quality gate)
        └────┬─────┘
             │
     ┌───────┴────────┐
   halted           continue
     │                 │
     │            ┌────▼─────┐
     │            │ diagnose │  (LLM: classify root cause per txn)
     │            └────┬─────┘
     │                 │
     │            ┌────▼─────┐
     │            │ allocate │  (rules: expected-value ranking, no LLM)
     │            └────┬─────┘
     │                 │
     │            ┌────▼─────┐
     │            │  decide  │  (rules + bandit: choose bounded action)
     │            └────┬─────┘
     │                 │
     │            ┌────▼──────┐
     │            │ negotiate │  (LLM, output clamped to hard limits)
     │            └────┬──────┘
     │                 │
     │            ┌────▼─────┐
     │            │ execute  │  (simulated action / real Razorpay API call)
     │            └────┬─────┘
     │                 │
     └───────────►┌────▼─────────────┐
                   │ build_audit_trail │
                   └────┬─────────────┘
                        ▼
                       END
```

## Design principles (map directly to the track's rubric)

1. **LLM never authorizes money movement.** `diagnosis_agent` and
   `negotiation_agent` are the only nodes that call an LLM, and both only
   produce *inputs* to a decision (a category, a draft offer) — never the
   final action. `policy_engine.py` is pure Python and is the sole
   authority on what actually happens.
2. **Hard gates over soft prompting.** Retry caps, discount caps,
   installment caps, and the fraud "do_not_touch" rule are enforced in code
   (`config.py` constants + `clamp_offer()`), not requested via prompt —
   so they cannot be bypassed by a bad LLM response.
3. **Halt on bad data.** `detect_node` computes a rough data-quality score;
   if it's below threshold, the graph routes straight to
   `build_audit_trail` with `halted=True` and skips diagnosis/decision/
   execution entirely. This mirrors the video's "Orchestrator halts on
   error" behavior and is a strong signal of engineering maturity in a demo.
4. **Portfolio allocation, not single-flow reaction.** `allocator.py`
   scores every transaction by `(recovery_probability * amount) / cost`
   across THREE leak types (failed payment, failed subscription, overdue
   invoice) at once, so the system is prioritizing a portfolio, not just
   reacting to one queue.
5. **Online learning without training a model.** `policy_engine.py`
   implements an epsilon-greedy bandit over 3 subscription dunning
   strategies, updated in `executor.py` after each simulated outcome. This
   lets you honestly claim the system "learns which intervention works
   best" without any offline model training.

## What to build first if short on time

Priority order for a hackathon timebox:
1. Data generator + detect/diagnose/decide/execute for `failed_payment` only
2. Wire up the React dashboard against real `/api/run-batch` output
3. Add `failed_subscription` + the bandit
4. Add `overdue_invoice` + negotiation agent (stretch goal, most impressive
   but also most complex — cut this first if time runs out)
5. Swap simulated `execute_node` actions for real Razorpay test-mode API
   calls where applicable (e.g. actually calling the retry/payment-link API)
