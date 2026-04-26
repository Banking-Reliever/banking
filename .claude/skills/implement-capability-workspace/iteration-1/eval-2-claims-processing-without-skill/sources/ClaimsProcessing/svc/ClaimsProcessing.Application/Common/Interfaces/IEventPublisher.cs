using FoodarooExperience.ClaimsProcessing.Domain.Common;

namespace FoodarooExperience.ClaimsProcessing.Application.Common.Interfaces;

public interface IEventPublisher
{
    Task PublishAsync(IDomainEvent domainEvent, CancellationToken cancellationToken = default);
}
