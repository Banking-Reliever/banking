using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json.Nodes;

namespace Reliever.BudgetEnvelope.Stub;

/// <summary>
/// Generates simulated <c>RVT.BSP.004.CONSUMPTION_RECORDED</c> payloads.
/// Payload form: domain event DDD (ADR-TECH-STRAT-001 Rule 3) — the
/// transition data of a single envelope-consumption transition. Carries the
/// new post-transition <c>consumed_amount</c>, NOT a snapshot of
/// RES.BSP.004.OPEN_ENVELOPE and NOT a field patch.
///
/// Behavioural simulation: each (case_id, category) envelope has its
/// <c>consumed_amount</c> progress monotonically toward <c>cap_amount</c>
/// across successive publications. Once the envelope reaches its cap, it
/// resets to 0 to start a new cycle (so the stub continues to publish
/// indefinitely without producing a degenerate stream of "already capped"
/// events). Realistic increments are random fractions of the remaining
/// balance, bounded to avoid pathological tiny / huge debits.
///
/// Allocation IDs are stable per (case_id, category) within one cycle —
/// they regenerate when the envelope resets, mirroring the real engine
/// where a new period yields new OBJ.BSP.004.ALLOCATION instances.
/// </summary>
public sealed class PayloadFactory
{
    private readonly StubOptions _options;
    private readonly Random _random;

    /// <summary>
    /// Per-envelope mutable state — keyed by "{case_id}::{category}".
    /// </summary>
    private readonly Dictionary<string, EnvelopeState> _envelopeState = new();

    public PayloadFactory(StubOptions options) : this(options, new Random())
    {
    }

    /// <summary>Test-friendly constructor — deterministic via injected Random.</summary>
    public PayloadFactory(StubOptions options, Random random)
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _random = random ?? throw new ArgumentNullException(nameof(random));

        if (_options.SimulatedCases is null || _options.SimulatedCases.Count == 0)
        {
            throw new InvalidOperationException(
                "StubOptions.SimulatedCases must contain at least one case with envelopes.");
        }
        foreach (var simulatedCase in _options.SimulatedCases)
        {
            if (simulatedCase.Envelopes is null || simulatedCase.Envelopes.Count == 0)
            {
                throw new InvalidOperationException(
                    $"SimulatedCase '{simulatedCase.CaseId}' must declare at least one envelope.");
            }
        }
    }

    /// <summary>
    /// Build one simulated payload as a <see cref="JsonObject"/>. The shape
    /// matches the runtime JSON Schema 1:1 — verified by
    /// <see cref="SchemaValidator"/> before publication.
    /// </summary>
    public JsonObject BuildOne()
    {
        var simulatedCase = _options.SimulatedCases[_random.Next(_options.SimulatedCases.Count)];
        var envelope = simulatedCase.Envelopes[_random.Next(simulatedCase.Envelopes.Count)];

        var stateKey = $"{simulatedCase.CaseId}::{envelope.Category}";
        if (!_envelopeState.TryGetValue(stateKey, out var state))
        {
            state = NewState(simulatedCase.CaseId, envelope);
            _envelopeState[stateKey] = state;
        }

        // Decide the debit increment: a random fraction of the remaining
        // balance, bounded so we always make visible progress and never
        // overshoot the cap.
        var remaining = envelope.CapAmount - state.ConsumedAmount;
        var fraction = (decimal)(0.10 + _random.NextDouble() * 0.30); // 10..40% of remaining
        var increment = decimal.Round(remaining * fraction, 2, MidpointRounding.AwayFromZero);
        if (increment <= 0m) increment = 0.01m;
        if (increment > remaining) increment = remaining;

        state.ConsumedAmount = decimal.Round(state.ConsumedAmount + increment, 2, MidpointRounding.AwayFromZero);

        // If the envelope is now exactly at (or above, defensively) its cap,
        // schedule a reset on the next pick — but still publish this final
        // capping consumption first.
        if (state.ConsumedAmount >= envelope.CapAmount)
        {
            state.ConsumedAmount = envelope.CapAmount;
            // Reset for the next cycle.
            _envelopeState[stateKey] = NewState(simulatedCase.CaseId, envelope);
        }

        return new JsonObject
        {
            ["allocation_id"] = state.AllocationId,
            ["case_id"]       = simulatedCase.CaseId,
            ["category"]      = envelope.Category,
            ["cap_amount"]    = (double)envelope.CapAmount,
            ["consumed_amount"] = (double)state.ConsumedAmount,
            ["period_start"]  = simulatedCase.PeriodStart,
            ["period_end"]    = simulatedCase.PeriodEnd,
        };
    }

    private static EnvelopeState NewState(string caseId, SimulatedEnvelope envelope)
    {
        // allocation_id is stable per (case, category) within one cycle.
        // Regenerated when the envelope resets after reaching its cap,
        // mirroring the new OBJ.BSP.004.ALLOCATION the real engine would
        // create at the start of a new period.
        return new EnvelopeState
        {
            AllocationId = $"ALLOC-{caseId}-{envelope.Category}-{Guid.NewGuid():N}".Substring(0, 60),
            ConsumedAmount = 0m,
        };
    }

    private sealed class EnvelopeState
    {
        public string AllocationId { get; set; } = "";
        public decimal ConsumedAmount { get; set; }
    }
}
