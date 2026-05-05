using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Reliever.BudgetEnvelopeManagement.Stub;

/// <summary>
/// Generates simulated envelope-consumption payloads honoring the runtime contract
/// (RVT.BSP.004.CONSUMPTION_RECORDED — domain event DDD form).
///
/// The factory maintains an in-memory state machine for each (case, category) pair:
///   - one allocation per (case, category) pair, with a fixed montant_plafond and
///     a monotonically increasing montant_consomme;
///   - each invocation advances montant_consomme by an irregular increment until
///     the cap is reached, then the allocation is reset (fresh period, montant_consomme=0)
///     to keep the simulation alive and exercise the full transition range.
/// Round-robins across configured (case × category) pairs.
///
/// The category vocabulary used here is illustrative ONLY — the canonical authoritative
/// source per tier is CAP.REF.001.PAL (Tier Catalogue). The future real envelope engine
/// MUST source categories from CAP.REF.001.PAL; this stub hard-codes them for offline dev.
/// </summary>
public sealed class PayloadFactory
{
    private readonly StubOptions _options;
    private readonly ILogger<PayloadFactory> _logger;
    private readonly Random _random;

    /// <summary>
    /// Per-envelope state: keyed by (caseId, categorie) tuple expressed as "caseId|categorie".
    /// </summary>
    private readonly Dictionary<string, EnvelopeState> _envelopeStates = new();

    /// <summary>
    /// Flat ordered list of (caseId, categorie) pairs to round-robin through.
    /// </summary>
    private readonly List<(string CaseId, string Category)> _allocations = new();

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
        _random = new Random();

        if (_options.Cases.Count == 0)
        {
            throw new InvalidOperationException(
                "Cases must contain at least one simulated participation case.");
        }
        if (_options.TransitionsPerEnvelope < 1)
        {
            throw new InvalidOperationException(
                "TransitionsPerEnvelope must be >= 1 to produce at least one consumption per envelope.");
        }

        foreach (var simulatedCase in _options.Cases)
        {
            if (string.IsNullOrWhiteSpace(simulatedCase.CaseId))
            {
                throw new InvalidOperationException("Each simulated case must have a non-empty CaseId.");
            }
            if (simulatedCase.Categories.Count == 0)
            {
                throw new InvalidOperationException(
                    $"Case '{simulatedCase.CaseId}' must have at least one category.");
            }
            foreach (var category in simulatedCase.Categories)
            {
                _allocations.Add((simulatedCase.CaseId, category));
                var key = StateKey(simulatedCase.CaseId, category);
                _envelopeStates[key] = NewEnvelopeState(simulatedCase.CaseId, category);
            }
        }

        _logger.LogInformation(
            "PayloadFactory initialised: {AllocationCount} (case × category) allocations across {CaseCount} cases.",
            _allocations.Count, _options.Cases.Count);
    }

    /// <summary>
    /// Builds the next simulated payload as a JSON string.
    /// Round-robins across all configured (case, category) allocations.
    /// </summary>
    public (string PayloadJson, string CaseId, string Category) BuildNext(int rotationIndex)
    {
        var allocation = _allocations[rotationIndex % _allocations.Count];
        var key = StateKey(allocation.CaseId, allocation.Category);
        var state = _envelopeStates[key];

        // Advance the consumption: irregular increment, but bounded by remaining cap.
        // Aim to consume the cap within roughly TransitionsPerEnvelope transitions.
        var nominalIncrement = state.MontantPlafond / _options.TransitionsPerEnvelope;
        var jitter = (_random.NextDouble() - 0.5) * 0.4 * nominalIncrement; // ±20%
        var increment = Math.Max(0.01, nominalIncrement + jitter);
        var newConsumed = Math.Min(state.MontantPlafond, Math.Round(state.MontantConsomme + increment, 2));

        state.MontantConsomme = newConsumed;
        state.TransitionCount++;

        // If the envelope reached cap (or exceeded the configured transitions per envelope),
        // reset to a fresh allocation period — montant_consomme=0, new allocation id, next period.
        var capReached = state.MontantConsomme >= state.MontantPlafond;
        var transitionsExhausted = state.TransitionCount >= _options.TransitionsPerEnvelope;
        if (capReached || transitionsExhausted)
        {
            _logger.LogDebug(
                "Resetting envelope state for case={CaseId} category={Category} (capReached={Cap} transitionsExhausted={Exhausted})",
                allocation.CaseId, allocation.Category, capReached, transitionsExhausted);
            _envelopeStates[key] = NewEnvelopeState(allocation.CaseId, allocation.Category);
        }

        var payload = new ConsumptionRecordedPayload
        {
            identifiant_allocation = state.IdentifiantAllocation,
            identifiant_dossier = allocation.CaseId,
            categorie = allocation.Category,
            montant_plafond = state.MontantPlafond,
            montant_consomme = newConsumed,
            periode_debut = state.PeriodeDebut.ToString("yyyy-MM-dd"),
            periode_fin = state.PeriodeFin.ToString("yyyy-MM-dd"),
            timestamp_consommation = DateTimeOffset.UtcNow.ToString("O")
        };

        var json = JsonSerializer.Serialize(payload, JsonOptions);
        _logger.LogDebug(
            "Built payload: case={CaseId} category={Category} consumed={Consumed}/{Cap}",
            allocation.CaseId, allocation.Category, newConsumed, state.MontantPlafond);

        return (json, allocation.CaseId, allocation.Category);
    }

    private EnvelopeState NewEnvelopeState(string caseId, string category)
    {
        var startOfMonth = new DateOnly(DateTime.UtcNow.Year, DateTime.UtcNow.Month, 1);
        var endOfMonth = startOfMonth.AddMonths(1).AddDays(-1);
        return new EnvelopeState
        {
            IdentifiantAllocation = $"ALC-{Guid.NewGuid():N}",
            MontantPlafond = _options.DefaultMontantPlafond,
            MontantConsomme = 0,
            PeriodeDebut = startOfMonth,
            PeriodeFin = endOfMonth,
            TransitionCount = 0
        };
    }

    private static string StateKey(string caseId, string category) => $"{caseId}|{category}";

    private sealed class EnvelopeState
    {
        public string IdentifiantAllocation { get; set; } = "";
        public double MontantPlafond { get; set; }
        public double MontantConsomme { get; set; }
        public DateOnly PeriodeDebut { get; set; }
        public DateOnly PeriodeFin { get; set; }
        public int TransitionCount { get; set; }
    }

    /// <summary>
    /// Domain event DDD payload mirroring the runtime schema.
    /// Property names are snake_case to match the contract — no JsonPropertyName decoration needed
    /// because the property names already match the wire format.
    /// </summary>
    private sealed class ConsumptionRecordedPayload
    {
        public string identifiant_allocation { get; set; } = "";
        public string identifiant_dossier { get; set; } = "";
        public string categorie { get; set; } = "";
        public double montant_plafond { get; set; }
        public double montant_consomme { get; set; }
        public string periode_debut { get; set; } = "";
        public string periode_fin { get; set; } = "";
        public string timestamp_consommation { get; set; } = "";
    }
}
