using System.Collections.Generic;

namespace Reliever.BudgetEnvelope.Stub;

/// <summary>
/// Configuration of the CAP.BSP.004.ENV development stub.
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
    /// default range. Required by the task DoD: "outside that range requires
    /// explicit override".
    /// </summary>
    public bool CadenceOutsideRangeOverride { get; set; } = false;

    /// <summary>
    /// Topic exchange owned by CAP.BSP.004.ENV (ADR-TECH-STRAT-001 Rules 1, 5).
    /// </summary>
    public string ExchangeName { get; set; } = "bsp.004.env-events";

    /// <summary>
    /// Routing key per ADR-TECH-STRAT-001 Rule 4
    /// ({BusinessEventName}.{ResourceEventName}).
    /// </summary>
    public string RoutingKey { get; set; } =
        "EVT.BSP.004.ENVELOPE_CONSUMED.RVT.BSP.004.CONSUMPTION_RECORDED";

    /// <summary>
    /// Path to the runtime JSON Schema
    /// (RVT.BSP.004.CONSUMPTION_RECORDED.schema.json).
    /// Resolved relative to AppContext.BaseDirectory; the file is shipped
    /// next to the assembly via the csproj CopyToOutputDirectory rule.
    /// </summary>
    public string SchemaPath { get; set; } =
        "schemas/RVT.BSP.004.CONSUMPTION_RECORDED.schema.json";

    /// <summary>
    /// Pool of simulated cases. Each case carries its own envelope set with
    /// realistic categories and caps. The stub picks a case at random for
    /// each publication and progresses one of its envelopes.
    /// At least one default case must be present.
    /// </summary>
    public List<SimulatedCase> SimulatedCases { get; set; } = new()
    {
        new SimulatedCase
        {
            CaseId = "CASE-RELIEVER-2026-000001",
            TierLabel = "T1",
            PeriodStart = "2026-05-01",
            PeriodEnd = "2026-05-31",
            Envelopes = new List<SimulatedEnvelope>
            {
                new() { Category = "ALIMENTATION", CapAmount = 250.00m },
                new() { Category = "TRANSPORT",    CapAmount =  80.00m },
                new() { Category = "LOGEMENT",     CapAmount = 400.00m },
            }
        }
    };
}

/// <summary>
/// One simulated beneficiary case with its own envelope set.
/// </summary>
public sealed class SimulatedCase
{
    /// <summary>The case_id correlation key (cf. CAP.BSP.002.ENR).</summary>
    public string CaseId { get; set; } = "";

    /// <summary>Illustrative tier label (e.g. T0, T1, T2, T3) — informational only.</summary>
    public string TierLabel { get; set; } = "";

    /// <summary>ISO-8601 calendar date — start of the active envelope period.</summary>
    public string PeriodStart { get; set; } = "";

    /// <summary>ISO-8601 calendar date — end of the active envelope period.</summary>
    public string PeriodEnd { get; set; } = "";

    /// <summary>Envelope set for this case (one envelope per spending category).</summary>
    public List<SimulatedEnvelope> Envelopes { get; set; } = new();
}

/// <summary>
/// One simulated envelope (allocation) belonging to a case.
/// Caps are illustrative; the canonical category vocabulary per tier is
/// owned by CAP.REF.001.TIE.
/// </summary>
public sealed class SimulatedEnvelope
{
    /// <summary>Spending category (e.g. ALIMENTATION, TRANSPORT, LOGEMENT, SANTE, LOISIRS).</summary>
    public string Category { get; set; } = "";

    /// <summary>Maximum amount authorised on this envelope for the active period.</summary>
    public decimal CapAmount { get; set; }
}

/// <summary>
/// RabbitMQ connection settings. Bound from "RabbitMq" in appsettings.json.
/// </summary>
public sealed class RabbitMqOptions
{
    public const string SectionName = "RabbitMq";
    public string Host { get; set; } = "localhost";
    public int Port { get; set; } = 49656;
    public string Username { get; set; } = "guest";
    public string Password { get; set; } = "guest";
    public string VirtualHost { get; set; } = "/";
}
