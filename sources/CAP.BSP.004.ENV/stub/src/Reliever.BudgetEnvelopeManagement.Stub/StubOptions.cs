namespace Reliever.BudgetEnvelopeManagement.Stub;

/// <summary>
/// Strongly-typed configuration for the CAP.BSP.004.ENV development stub.
/// Bound from the "Stub" section of appsettings.json + config/stub.json + env vars.
/// </summary>
public sealed class StubOptions
{
    /// <summary>
    /// Master switch. When false (default), the stub starts but publishes nothing.
    /// MUST be false in production environments. Activate via env var STUB_Stub__Active=true
    /// (or by setting Stub:Active=true in configuration).
    /// </summary>
    public bool Active { get; set; } = false;

    /// <summary>
    /// Cadence of publication (events per minute). Default range 1..10. Outside that
    /// range requires explicit override via AllowOutOfRangeCadence=true.
    /// </summary>
    public double EventsPerMinute { get; set; } = 6;

    /// <summary>
    /// Explicit override required to allow EventsPerMinute outside the [1, 10] range.
    /// Per Definition of Done: 1..10/min default; outside requires explicit override.
    /// </summary>
    public bool AllowOutOfRangeCadence { get; set; } = false;

    /// <summary>
    /// Configurable simulated cases. Each case carries its own list of envelope categories
    /// (illustrative — the canonical authoritative set per tier is owned by CAP.REF.001.PAL).
    /// At least one case is required; multiple cases simulate distinct envelope category sets.
    /// </summary>
    public List<SimulatedCase> Cases { get; set; } = new()
    {
        new SimulatedCase
        {
            CaseId = "DOS-2026-000001",
            Categories = new() { "ALIMENTATION", "TRANSPORT", "SANTE" }
        },
        new SimulatedCase
        {
            CaseId = "DOS-2026-000002",
            Categories = new() { "ALIMENTATION", "LOGEMENT", "ENERGIE", "TRANSPORT" }
        },
        new SimulatedCase
        {
            CaseId = "DOS-2026-000003",
            Categories = new() { "ALIMENTATION", "TRANSPORT" }
        }
    };

    /// <summary>
    /// Default ceiling per envelope when the stub initialises a fresh allocation.
    /// Used by the PayloadFactory's deterministic envelope state machine.
    /// </summary>
    public double DefaultMontantPlafond { get; set; } = 200.00;

    /// <summary>
    /// Number of consumption transitions (publications) per envelope before the
    /// envelope is reset to a fresh period (montant_consomme=0). Smaller values
    /// produce more visible "envelope full" signals during a short demo run.
    /// </summary>
    public int TransitionsPerEnvelope { get; set; } = 6;

    public RabbitMqOptions RabbitMq { get; set; } = new();
    public BusOptions Bus { get; set; } = new();
    public SchemaOptions Schema { get; set; } = new();
}

/// <summary>
/// One simulated participation case — provides an identifiant_dossier and a list
/// of spending categories that the stub will use to round-robin allocations.
/// </summary>
public sealed class SimulatedCase
{
    public string CaseId { get; set; } = "";
    public List<string> Categories { get; set; } = new();
}

public sealed class RabbitMqOptions
{
    public string HostName { get; set; } = "localhost";
    public int Port { get; set; } = 45481;
    public string UserName { get; set; } = "guest";
    public string Password { get; set; } = "guest";
    public string VirtualHost { get; set; } = "/";
}

public sealed class BusOptions
{
    /// <summary>
    /// Topic exchange owned by CAP.BSP.004.ENV (ADR-TECH-STRAT-001 Rule 1, 5).
    /// Only this capability publishes on it.
    /// </summary>
    public string ExchangeName { get; set; } = "bsp.004.env-events";

    /// <summary>
    /// Routing key (ADR-TECH-STRAT-001 Rule 4): {BusinessEventName}.{ResourceEventName}.
    /// </summary>
    public string RoutingKey { get; set; } = "EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED";
}

public sealed class SchemaOptions
{
    /// <summary>
    /// Path to the runtime JSON Schema, relative to the binary working directory.
    /// Loaded once at startup; every outgoing payload is validated against it.
    /// </summary>
    public string RuntimeSchemaPath { get; set; } = "schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json";
}
