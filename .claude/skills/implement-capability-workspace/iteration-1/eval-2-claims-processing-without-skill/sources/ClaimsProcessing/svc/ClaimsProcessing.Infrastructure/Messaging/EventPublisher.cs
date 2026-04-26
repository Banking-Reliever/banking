using FoodarooExperience.ClaimsProcessing.Application.Common.Interfaces;
using FoodarooExperience.ClaimsProcessing.Contracts.Claims.Events;
using FoodarooExperience.ClaimsProcessing.Domain.Claims;
using FoodarooExperience.ClaimsProcessing.Domain.Claims.Events;
using FoodarooExperience.ClaimsProcessing.Domain.Common;
using Microsoft.Extensions.Logging;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure.Messaging;

public sealed class EventPublisher : IEventPublisher
{
    private readonly IMessageBroker _messageBroker;
    private readonly ILogger<EventPublisher> _logger;

    public EventPublisher(IMessageBroker messageBroker, ILogger<EventPublisher> logger)
    {
        _messageBroker = messageBroker;
        _logger = logger;
    }

    public async Task PublishAsync(IDomainEvent domainEvent, CancellationToken cancellationToken = default)
    {
        switch (domainEvent)
        {
            case ClaimFiled claimFiled:
                await PublishClaimFiledAsync(claimFiled, cancellationToken);
                break;

            default:
                _logger.LogWarning(
                    "No integration event mapping found for domain event {DomainEventType}",
                    domainEvent.GetType().Name);
                break;
        }
    }

    private async Task PublishClaimFiledAsync(ClaimFiled domainEvent, CancellationToken cancellationToken)
    {
        var integrationEvent = new ClaimFiledEvent(
            EventId: domainEvent.EventId,
            OccurredOn: domainEvent.OccurredOn,
            ClaimId: domainEvent.ClaimId.Value,
            ClaimantId: domainEvent.ClaimantId,
            Description: domainEvent.Description,
            Amount: domainEvent.Amount.Value,
            Currency: domainEvent.Amount.Currency,
            FiledAt: domainEvent.FiledAt);

        await _messageBroker.PublishAsync(integrationEvent, cancellationToken);

        _logger.LogInformation(
            "Published integration event {EventType} for ClaimId: {ClaimId}",
            nameof(ClaimFiledEvent),
            domainEvent.ClaimId.Value);
    }
}
