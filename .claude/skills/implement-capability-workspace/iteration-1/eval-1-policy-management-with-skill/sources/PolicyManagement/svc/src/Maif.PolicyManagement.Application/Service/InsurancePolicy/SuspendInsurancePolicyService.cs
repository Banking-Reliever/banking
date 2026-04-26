using Foodaroo.Component.Messaging;
using Maif.PolicyManagement.Application.Contract.InsurancePolicy;
using Maif.PolicyManagement.Contracts.Commands;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Maif.PolicyManagement.Infrastructure.Data.Domain;

namespace Maif.PolicyManagement.Application.Service.InsurancePolicy;

public class SuspendInsurancePolicyService : ISuspendInsurancePolicyService
{
    private readonly IRepositoryInsurancePolicy _repository;
    private readonly IPublish _publisher;

    public SuspendInsurancePolicyService(
        IRepositoryInsurancePolicy repository,
        IPublish publisher)
    {
        _repository = repository;
        _publisher = publisher;
    }

    public async Task SuspendAsync(SuspendInsurancePolicyCommand command)
    {
        var aggregate = await _repository.GetByAggregateRootId(command.Id);
        aggregate.Suspend();

        await _repository.SaveAggregate(aggregate);

        foreach (var evt in aggregate.GetDomainEvents())
            await _publisher.PublishAsync(evt, "maif-policy-management-channel");

        aggregate.ClearDomainEvents();
    }
}
