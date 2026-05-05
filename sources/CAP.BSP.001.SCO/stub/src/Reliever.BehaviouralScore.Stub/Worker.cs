using System;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using RabbitMQ.Client;

namespace Reliever.BehaviouralScore.Stub;

/// <summary>
/// Background service publishing simulated
/// <c>RVT.BSP.001.CURRENT_SCORE_RECOMPUTED</c> payloads on the RabbitMQ
/// topic exchange owned by CAP.BSP.001.SCO.
///
/// Bus topology — ADR-TECH-STRAT-001:
///   Rule 1   Topic exchange owned by this L2 (one per L2)
///   Rule 2   Only the resource event is published; no autonomous EVT message
///   Rule 3   Domain event DDD payload (transition data, not snapshot, not patch)
///   Rule 4   Routing key {BusinessEventName}.{ResourceEventName}
///   Rule 5   Only this L2 publishes on this exchange
///   Rule 6   Schema governance is design-time; the runtime schema is loaded
///            from plan/CAP.BSP.001.SCO/contracts/ and used to fail-fast on
///            any non-conforming payload BEFORE publication.
/// </summary>
public sealed class Worker : BackgroundService
{
    private readonly ILogger<Worker> _logger;
    private readonly StubOptions _stubOptions;
    private readonly RabbitMqOptions _rabbitOptions;
    private readonly PayloadFactory _payloadFactory;
    private readonly SchemaValidator _validator;

    private IConnection? _connection;
    private IModel? _channel;

    public Worker(
        ILogger<Worker> logger,
        IOptions<StubOptions> stubOptions,
        IOptions<RabbitMqOptions> rabbitOptions,
        PayloadFactory payloadFactory,
        SchemaValidator validator)
    {
        _logger = logger;
        _stubOptions = stubOptions.Value;
        _rabbitOptions = rabbitOptions.Value;
        _payloadFactory = payloadFactory;
        _validator = validator;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (!_stubOptions.Active)
        {
            _logger.LogWarning(
                "Stub is INACTIVE (Stub:Active=false). Set STUB__ACTIVE=true to enable. " +
                "By design, the stub is inactive in production.");
            return;
        }

        ValidateCadence(_stubOptions);
        var periodMs = (int)Math.Round(60_000.0 / _stubOptions.CadencePerMinute);

        OpenChannel();

        _logger.LogInformation(
            "Stub active — exchange={Exchange} routingKey={RoutingKey} cadence={Cadence}/min ({PeriodMs}ms)",
            _stubOptions.ExchangeName, _stubOptions.RoutingKey, _stubOptions.CadencePerMinute, periodMs);

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var payload = _payloadFactory.BuildOne();
                _validator.EnsureValid(payload);
                Publish(payload);
            }
            catch (InvalidPayloadException ex)
            {
                _logger.LogError(ex,
                    "Generated payload was rejected by the runtime schema — NOT published. " +
                    "This is a bug in PayloadFactory and must be fixed before redeploying.");
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                _logger.LogError(ex, "Unexpected publication failure.");
            }

            try
            {
                await Task.Delay(periodMs, stoppingToken);
            }
            catch (TaskCanceledException)
            {
                // graceful shutdown
            }
        }
    }

    public override Task StopAsync(CancellationToken cancellationToken)
    {
        _channel?.Dispose();
        _connection?.Dispose();
        return base.StopAsync(cancellationToken);
    }

    /// <summary>
    /// Enforces the cadence range invariant: 1..10 events/min by default;
    /// outside that range requires <c>CadenceOutsideRangeOverride</c>.
    /// </summary>
    public static void ValidateCadence(StubOptions options)
    {
        if (options.CadencePerMinute <= 0)
        {
            throw new InvalidOperationException(
                $"Stub:CadencePerMinute must be > 0 (got {options.CadencePerMinute}).");
        }
        var inRange = options.CadencePerMinute >= 1 && options.CadencePerMinute <= 10;
        if (!inRange && !options.CadenceOutsideRangeOverride)
        {
            throw new InvalidOperationException(
                $"Stub:CadencePerMinute={options.CadencePerMinute} is outside the default [1, 10] range. " +
                "Set Stub:CadenceOutsideRangeOverride=true (with explicit operational justification) to override.");
        }
    }

    private void OpenChannel()
    {
        var factory = new ConnectionFactory
        {
            HostName = _rabbitOptions.Host,
            Port = _rabbitOptions.Port,
            UserName = _rabbitOptions.Username,
            Password = _rabbitOptions.Password,
            VirtualHost = _rabbitOptions.VirtualHost,
            DispatchConsumersAsync = true,
            AutomaticRecoveryEnabled = true,
        };

        _connection = factory.CreateConnection($"cap-bsp-001-sco-stub@{Environment.MachineName}");
        _channel = _connection.CreateModel();

        // Topic exchange owned by CAP.BSP.001.SCO (Rule 1). Durable so it
        // survives broker restarts without producer involvement.
        _channel.ExchangeDeclare(
            exchange: _stubOptions.ExchangeName,
            type: ExchangeType.Topic,
            durable: true,
            autoDelete: false,
            arguments: null);
    }

    private void Publish(JsonObject payload)
    {
        if (_channel is null) throw new InvalidOperationException("RabbitMQ channel not initialised.");

        var body = Encoding.UTF8.GetBytes(payload.ToJsonString());
        var props = _channel.CreateBasicProperties();
        props.ContentType = "application/json";
        props.DeliveryMode = 2; // persistent
        props.Headers = new System.Collections.Generic.Dictionary<string, object>
        {
            ["x-bcm-resource-event"] = "RVT.BSP.001.CURRENT_SCORE_RECOMPUTED",
            ["x-bcm-business-event"] = "EVT.BSP.001.SCORE_RECOMPUTED",
            ["x-bcm-version"] = "1.0.0",
            ["x-bcm-capability"] = "CAP.BSP.001.SCO",
        };

        _channel.BasicPublish(
            exchange: _stubOptions.ExchangeName,
            routingKey: _stubOptions.RoutingKey,
            mandatory: false,
            basicProperties: props,
            body: body);

        _logger.LogInformation(
            "Published RVT.BSP.001.CURRENT_SCORE_RECOMPUTED on routingKey={RoutingKey} dossier={Case}",
            _stubOptions.RoutingKey,
            payload["case_id"]?.GetValue<string>());
    }
}
