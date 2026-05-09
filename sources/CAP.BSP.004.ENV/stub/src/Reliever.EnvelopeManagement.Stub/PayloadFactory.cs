using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Reliever.EnvelopeManagement.Stub;

/// <summary>
/// Generates simulated envelope-consumption payloads honoring the runtime contract
/// (RVT.BSP.004.CONSUMPTION_RECORDED — domain event DDD form).
///
/// Each simulated case carries its own set of envelopes (one per spending category).
/// At each emission:
///   - the factory picks the next case round-robin,
///   - within that case it picks an envelope (round-robin across categories),
///   - it computes a realistic debit amount, applies it to the in-memory envelope state,
///   - and emits the post-transition data (consumed_amount_after, remaining_amount).
///
/// Once an envelope reaches its cap, it wraps around to consumed=0 (representing a
/// fresh period) so the stub can keep publishing indefinitely without exhausting state.
/// </summary>
public sealed class PayloadFactory
{
    private readonly StubOptions _options;
    private readonly ILogger<PayloadFactory> _logger;
    private readonly Random _random = new();

    /// <summary>
    /// In-memory state per envelope: tracks the current consumed_amount.
    /// Keyed by allocation_id (unique across all simulated cases).
    /// </summary>
    private readonly Dictionary<string, double> _consumedByAllocation = new();

    /// <summary>
    /// Per-case rotation cursor — index of the next envelope to debit for the case.
    /// </summary>
    private readonly Dictionary<string, int> _envelopeCursorByCase = new();

    public static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = null,
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.Never,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };

    public PayloadFactory(IOptions<StubOptions> options, ILogger<PayloadFactory> logger)
    {
        _options = options.Value;
        _logger = logger;

        if (_options.Cases.Count == 0)
        {
            throw new InvalidOperationException(
                "Stub:Cases must contain at least one simulated case (with at least one envelope).");
        }

        foreach (var c in _options.Cases)
        {
            if (string.IsNullOrWhiteSpace(c.CaseId))
            {
                throw new InvalidOperationException("Every Stub:Cases entry must declare a non-empty CaseId.");
            }
            if (c.Envelopes.Count == 0)
            {
                throw new InvalidOperationException(
                    $"Stub:Cases[{c.CaseId}] must contain at least one envelope.");
            }
            _envelopeCursorByCase[c.CaseId] = 0;
            foreach (var env in c.Envelopes)
            {
                if (string.IsNullOrWhiteSpace(env.AllocationId))
                {
                    throw new InvalidOperationException(
                        $"Stub:Cases[{c.CaseId}].Envelopes must all declare a non-empty AllocationId.");
                }
                if (env.CapAmount <= 0)
                {
                    throw new InvalidOperationException(
                        $"Stub:Cases[{c.CaseId}].Envelopes[{env.AllocationId}].CapAmount must be > 0.");
                }
                _consumedByAllocation[env.AllocationId] = 0.0;
            }
        }
    }

    /// <summary>
    /// Builds the next simulated payload as a JSON string, advancing the case cursor.
    /// Round-robins across configured cases.
    /// </summary>
    public (string PayloadJson, string CaseId, string AllocationId) BuildNext(int rotationIndex)
    {
        var simulatedCase = _options.Cases[rotationIndex % _options.Cases.Count];

        // Pick the next envelope within the case.
        var envIdx = _envelopeCursorByCase[simulatedCase.CaseId];
        var envelope = simulatedCase.Envelopes[envIdx % simulatedCase.Envelopes.Count];
        _envelopeCursorByCase[simulatedCase.CaseId] = (envIdx + 1) % simulatedCase.Envelopes.Count;

        // Current consumed_amount (pre-transition).
        var consumedBefore = _consumedByAllocation[envelope.AllocationId];

        // Choose a realistic debit: a random fraction of the cap, clamped so the new
        // consumed_amount never exceeds cap. This produces a believable progression
        // toward the cap over time.
        var remainingBefore = envelope.CapAmount - consumedBefore;
        if (remainingBefore <= 0.01)
        {
            // Wrap-around: envelope exhausted, restart the period at 0.
            consumedBefore = 0.0;
            _consumedByAllocation[envelope.AllocationId] = 0.0;
            remainingBefore = envelope.CapAmount;
        }

        // Debit between 1% and 25% of the cap, but never more than what remains.
        var fraction = 0.01 + (_random.NextDouble() * 0.24);
        var rawAmount = Math.Round(envelope.CapAmount * fraction, 2);
        var amount = Math.Min(rawAmount, Math.Round(remainingBefore, 2));

        // Domain rule: amount must be strictly positive (INV.ENV.003).
        // The minimum debit is 0.01 to satisfy exclusiveMinimum:0 in the schema.
        if (amount < 0.01)
        {
            amount = 0.01;
            // Adjust if cap was already hit (defensive — should not happen after wrap-around).
            if (amount > remainingBefore)
            {
                amount = Math.Round(remainingBefore, 2);
            }
        }

        var consumedAfter = Math.Round(consumedBefore + amount, 2);
        if (consumedAfter > envelope.CapAmount)
        {
            // Defensive clamp — keep arithmetic consistent with the cap.
            consumedAfter = envelope.CapAmount;
            amount = Math.Round(consumedAfter - consumedBefore, 2);
        }

        var remainingAfter = Math.Round(envelope.CapAmount - consumedAfter, 2);
        if (remainingAfter < 0) remainingAfter = 0; // Defensive — keep schema 'minimum: 0' invariant.

        // Persist post-transition state for the next call.
        _consumedByAllocation[envelope.AllocationId] = consumedAfter;

        var payload = new ConsumptionRecordedPayload
        {
            event_id = $"EVT-{Guid.NewGuid():N}",
            occurred_at = DateTimeOffset.UtcNow.ToString("O"),
            case_id = simulatedCase.CaseId,
            period_index = simulatedCase.PeriodIndex,
            allocation_id = envelope.AllocationId,
            category = envelope.Category,
            amount = amount,
            consumed_amount_after = consumedAfter,
            remaining_amount = remainingAfter,
            transaction_id = $"TXN-{Guid.NewGuid():N}",
            causation_event_id = $"RVT-{Guid.NewGuid():N}"
        };

        var json = JsonSerializer.Serialize(payload, JsonOptions);
        _logger.LogDebug(
            "Built payload: case={CaseId} alloc={AllocationId} cat={Category} amount={Amount} consumed_after={ConsumedAfter} remaining={Remaining}",
            simulatedCase.CaseId, envelope.AllocationId, envelope.Category, amount, consumedAfter, remainingAfter);

        return (json, simulatedCase.CaseId, envelope.AllocationId);
    }

    /// <summary>
    /// Domain event DDD payload mirroring the runtime schema.
    /// Property names are snake_case to match the contract — no JsonPropertyName decoration needed
    /// because the property names already match the wire format.
    /// </summary>
#pragma warning disable IDE1006 // Naming styles — snake_case is the wire format.
    private sealed class ConsumptionRecordedPayload
    {
        public string event_id { get; set; } = "";
        public string occurred_at { get; set; } = "";
        public string case_id { get; set; } = "";
        public int period_index { get; set; }
        public string allocation_id { get; set; } = "";
        public string category { get; set; } = "";
        public double amount { get; set; }
        public double consumed_amount_after { get; set; }
        public double remaining_amount { get; set; }
        public string? transaction_id { get; set; }
        public string? causation_event_id { get; set; }
    }
#pragma warning restore IDE1006
}
