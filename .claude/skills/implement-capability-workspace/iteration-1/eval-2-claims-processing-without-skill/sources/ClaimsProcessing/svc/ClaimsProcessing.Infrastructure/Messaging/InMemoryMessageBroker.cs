using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure.Messaging;

/// <summary>
/// In-memory message broker for development/testing. Replace with a real broker (e.g., RabbitMQ, Azure Service Bus) in production.
/// </summary>
public sealed class InMemoryMessageBroker : IMessageBroker
{
    private readonly ILogger<InMemoryMessageBroker> _logger;

    public InMemoryMessageBroker(ILogger<InMemoryMessageBroker> logger)
    {
        _logger = logger;
    }

    public Task PublishAsync<T>(T message, CancellationToken cancellationToken = default) where T : class
    {
        var json = JsonSerializer.Serialize(message);
        _logger.LogInformation(
            "[InMemoryMessageBroker] Published {MessageType}: {Payload}",
            typeof(T).Name,
            json);
        return Task.CompletedTask;
    }
}
