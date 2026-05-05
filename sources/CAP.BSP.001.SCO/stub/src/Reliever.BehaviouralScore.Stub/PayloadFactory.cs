using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

namespace Reliever.BehaviouralScore.Stub;

/// <summary>
/// Generates simulated <c>RVT.BSP.001.CURRENT_SCORE_RECOMPUTED</c> payloads.
/// Payload form: domain event DDD (ADR-TECH-STRAT-001 Rule 3) — the data of
/// the score recomputation transition (new value, delta, factors,
/// triggering event, timestamp, model version, evaluation type), keyed
/// by the <c>case_id</c> correlation key.
/// </summary>
public sealed class PayloadFactory
{
    private static readonly string[] FactorTypes = new[]
    {
        "transaction_categorie",
        "budget_respect",
        "recurrence",
        "comportement_signal",
        "regulation_emotionnelle",
    };

    private readonly StubOptions _options;
    private readonly Random _random;
    private readonly Dictionary<string, double> _previousScoreByDossier = new();

    public PayloadFactory(StubOptions options) : this(options, new Random())
    {
    }

    /// <summary>Test-friendly constructor.</summary>
    public PayloadFactory(StubOptions options, Random random)
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _random = random ?? throw new ArgumentNullException(nameof(random));
    }

    /// <summary>
    /// Build one simulated payload as a <see cref="JsonObject"/>. The shape
    /// matches the runtime JSON Schema 1:1 — verified by
    /// <see cref="SchemaValidator"/> before publication.
    /// </summary>
    public JsonObject BuildOne()
    {
        var dossier = PickCase();
        var evaluationType = PickEvaluationType();
        var newScore = Math.Round(_random.NextDouble() * 1000.0, 2);

        // delta_score is the transition delta — domain-event-DDD field
        var previous = _previousScoreByDossier.TryGetValue(dossier, out var p) ? p : newScore;
        var delta = Math.Round(newScore - previous, 2);
        _previousScoreByDossier[dossier] = newScore;

        var factorsCount = _random.Next(1, 4);
        var factors = new JsonArray();
        for (var i = 0; i < factorsCount; i++)
        {
            factors.Add(new JsonObject
            {
                ["type"] = FactorTypes[_random.Next(FactorTypes.Length)],
                ["poids"] = Math.Round((_random.NextDouble() * 2.0) - 1.0, 3),
                ["valeur"] = Math.Round(_random.NextDouble(), 3),
            });
        }

        return new JsonObject
        {
            ["evaluation_id"] = $"EVAL-{Guid.NewGuid():N}",
            ["case_id"] = dossier,
            ["score_value"] = newScore,
            ["delta_score"] = delta,
            ["contributing_factors"] = factors,
            ["evaluation_type"] = evaluationType,
            ["evenement_declencheur"] = $"TXN-{Guid.NewGuid():N}",
            ["computation_timestamp"] = DateTime.UtcNow.ToString("o"),
            ["model_version"] = _options.ModelVersion,
        };
    }

    private string PickCase()
    {
        if (_options.SimulatedCases is null || _options.SimulatedCases.Count == 0)
        {
            throw new InvalidOperationException(
                "StubOptions.SimulatedCases must contain at least one entry.");
        }
        return _options.SimulatedCases[_random.Next(_options.SimulatedCases.Count)];
    }

    private string PickEvaluationType()
    {
        // Fall back to CURRENT if mix is malformed — the stub still produces valid payloads.
        var mix = _options.EvaluationTypeMix ?? new Dictionary<string, double>();
        var pInitial = mix.TryGetValue("INITIAL", out var v) ? Math.Max(0.0, v) : 0.2;
        var pCurrent = mix.TryGetValue("CURRENT", out var w) ? Math.Max(0.0, w) : 0.8;
        var total = pInitial + pCurrent;
        if (total <= 0) return "CURRENT";
        return _random.NextDouble() * total < pInitial ? "INITIAL" : "CURRENT";
    }
}
