using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Reliever.BehaviouralScore.Stub;

// CAP.BSP.001.SCO — development stub host.
//
// This .NET 10 worker publishes simulated RVT.BSP.001.CURRENT_SCORE_RECOMPUTED
// payloads on a RabbitMQ topic exchange owned by CAP.BSP.001.SCO, honoring
// the runtime JSON Schema shipped next to the assembly under schemas/.
// The whole stub is governed by:
//
//   - ADR-BCM-FUNC-0005 (L2 BSP001 — behavioural remediation)
//   - ADR-BCM-URBA-0007 (normalised event meta-model)
//   - ADR-BCM-URBA-0009 (definition of an event-driven capability)
//   - ADR-TECH-STRAT-001 (event infrastructure — NORMATIVE)
//
// Activation: STUB__ACTIVE=true (or appsettings.json Stub:Active=true).
// Inactive in production by default.

var builder = Host.CreateApplicationBuilder(args);

builder.Configuration
    .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
    .AddJsonFile($"appsettings.{builder.Environment.EnvironmentName}.json", optional: true, reloadOnChange: true)
    .AddEnvironmentVariables();

builder.Services.Configure<StubOptions>(builder.Configuration.GetSection(StubOptions.SectionName));
builder.Services.Configure<RabbitMqOptions>(builder.Configuration.GetSection(RabbitMqOptions.SectionName));

builder.Services.AddSingleton<PayloadFactory>(sp =>
{
    var opts = sp.GetRequiredService<Microsoft.Extensions.Options.IOptions<StubOptions>>().Value;
    return new PayloadFactory(opts);
});

builder.Services.AddSingleton<SchemaValidator>(sp =>
{
    var opts = sp.GetRequiredService<Microsoft.Extensions.Options.IOptions<StubOptions>>().Value;
    var logger = sp.GetRequiredService<ILogger<SchemaValidator>>();
    logger.LogInformation("Loading runtime JSON Schema from {Path}", opts.SchemaPath);
    return SchemaValidator.FromFile(opts.SchemaPath);
});

builder.Services.AddHostedService<Worker>();

var host = builder.Build();
await host.RunAsync();
