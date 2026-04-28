using System.Collections.Generic;

namespace Reliever.BehaviouralScore.Stub;

/// <summary>
/// Configuration of the CAP.BSP.001.SCO development stub.
/// Bound from "Stub" in appsettings.json (or env vars STUB__*) at startup.
/// </summary>
public sealed class StubOptions
{
    public const string SectionName = "Stub";

    /// <summary>
    /// Master switch. False (default) = stub is inactive in production.
    /// Set STUB__ACTIVE=true to enable publication.
    /// </summary>
    public bool Active { get; set; } = false;

    /// <summary>
    /// Publication cadence, in events per minute. Default range: [1, 10].
    /// Values outside [1, 10] require <see cref="CadenceOutsideRangeOverride"/> = true.
    /// </summary>
    public int CadencePerMinute { get; set; } = 6;

    /// <summary>
    /// Explicit override allowing CadencePerMinute to be set outside the [1, 10]
    /// default range. Required by ADR-derived task DoD: "outside that range
    /// requires explicit override + justification".
    /// </summary>
    public bool CadenceOutsideRangeOverride { get; set; } = false;

    /// <summary>
    /// Topic exchange owned by CAP.BSP.001.SCO (ADR-TECH-STRAT-001 Rules 1, 5).
    /// </summary>
    public string ExchangeName { get; set; } = "bsp.001.sco-events";

    /// <summary>
    /// Routing key per ADR-TECH-STRAT-001 Rule 4
    /// ({BusinessEventName}.{ResourceEventName}).
    /// </summary>
    public string RoutingKey { get; set; } =
        "EVT.BSP.001.SCORE_RECALCULE.RVT.BSP.001.SCORE_COURANT_RECALCULE";

    /// <summary>
    /// Path to the runtime JSON Schema
    /// (RVT.BSP.001.SCORE_COURANT_RECALCULE.schema.json).
    /// Resolved relative to AppContext.BaseDirectory.
    /// </summary>
    public string SchemaPath { get; set; } =
        "../../../../plan/CAP.BSP.001.SCO/contracts/RVT.BSP.001.SCORE_COURANT_RECALCULE.schema.json";

    /// <summary>
    /// Scoring-model version label written into every payload.
    /// </summary>
    public string ModelVersion { get; set; } = "stub-1.0.0";

    /// <summary>
    /// Simulated case IDs (identifiant_dossier values) chosen at random
    /// for each generated payload. At least one default must be present.
    /// </summary>
    public List<string> SimulatedDossiers { get; set; } = new()
    {
        "DOS-RELIEVER-2026-000001"
    };

    /// <summary>
    /// Probability mix for type_evaluation field. Keys must be in
    /// {"INITIAL", "COURANT"}. Values are normalised at runtime.
    /// </summary>
    public Dictionary<string, double> TypeEvaluationMix { get; set; } = new()
    {
        ["INITIAL"] = 0.2,
        ["COURANT"] = 0.8,
    };
}

/// <summary>
/// RabbitMQ connection settings. Bound from "RabbitMq" in appsettings.json.
/// </summary>
public sealed class RabbitMqOptions
{
    public const string SectionName = "RabbitMq";
    public string Host { get; set; } = "localhost";
    public int Port { get; set; } = 5672;
    public string Username { get; set; } = "guest";
    public string Password { get; set; } = "guest";
    public string VirtualHost { get; set; } = "/";
}
