namespace Reliever.EnvelopeManagement.Stub;

/// <summary>
/// Strongly-typed configuration for the CAP.BSP.004.ENV development stub.
/// Bound from the "Stub" section of appsettings.json + config/stub.json + env vars.
/// </summary>
public sealed class StubOptions
{
    /// <summary>
    /// Master switch. When false (default), the stub starts but publishes nothing.
    /// MUST be false in production environments. Activate via env var STUB_Stub__Active=true
    /// (or STUB_ACTIVE=true via the STUB_ prefix mapping).
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
    /// Configurable list of simulated cases. Each case carries its own envelope set
    /// (one envelope per spending category) — illustrative categories per the
    /// canonical source CAP.REF.001.TIE (hard-coded here for stub purposes only).
    /// </summary>
    public List<SimulatedCase> Cases { get; set; } = new();

    public RabbitMqOptions RabbitMq { get; set; } = new();
    public BusOptions Bus { get; set; } = new();
    public SchemaOptions Schema { get; set; } = new();
}

/// <summary>
/// One simulated case = one beneficiary participation case (case_id, period_index)
/// with its own set of envelopes. Mirrors the AGG.BSP.004.ENV.PERIOD_BUDGET aggregate
/// granularity declared in process/CAP.BSP.004.ENV/aggregates.yaml.
/// </summary>
public sealed class SimulatedCase
{
    public string CaseId { get; set; } = "";
    public int PeriodIndex { get; set; } = 0;
    public string PeriodStart { get; set; } = ""; // ISO-8601 date (yyyy-MM-dd)
    public string PeriodEnd { get; set; } = "";
    public List<SimulatedEnvelope> Envelopes { get; set; } = new();
}

/// <summary>
/// One simulated envelope (inner entity of the period budget) — one per spending category.
/// </summary>
public sealed class SimulatedEnvelope
{
    public string AllocationId { get; set; } = "";
    public string Category { get; set; } = "";
    public double CapAmount { get; set; } = 0.0;
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
    /// Routing key for envelope-consumption events (ADR-TECH-STRAT-001 Rule 4):
    /// {BusinessEventName}.{ResourceEventName}.
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
