using Foodaroo.Component.Messaging;
using Naive.PolicyManagement.Application.Contract.InsurancePolicy;
using Naive.PolicyManagement.Contracts.Commands;
using Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Naive.PolicyManagement.Infrastructure.Data.Domain;

namespace Naive.PolicyManagement.Application.Service.InsurancePolicy;

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
            await _publisher.PublishAsync(evt, "naive-policy-management-channel");

        aggregate.ClearDomainEvents();
    }
}
