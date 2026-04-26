using Foodaroo.Component.Messaging;
using Naive.PolicyManagement.Application.Contract.InsurancePolicy;
using Naive.PolicyManagement.Contracts.Commands;
using Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Naive.PolicyManagement.Infrastructure.Data.Domain;

namespace Naive.PolicyManagement.Application.Service.InsurancePolicy;

public class CreateInsurancePolicyService : ICreateInsurancePolicyService
{
    private readonly IRepositoryInsurancePolicy _repository;
    private readonly IInsurancePolicyFactory _factory;
    private readonly IPublish _publisher;

    public CreateInsurancePolicyService(
        IRepositoryInsurancePolicy repository,
        IInsurancePolicyFactory factory,
        IPublish publisher)
    {
        _repository = repository;
        _factory = factory;
        _publisher = publisher;
    }

    public async Task<Guid> CreateAsync(CreateInsurancePolicyCommand command)
    {
        var id = command.Id == Guid.Empty ? Guid.NewGuid() : command.Id;
        var aggregate = InsurancePolicyAR.Create(id);

        await _repository.InsertAggregate(aggregate);

        foreach (var evt in aggregate.GetDomainEvents())
            await _publisher.PublishAsync(evt, "naive-policy-management-channel");

        aggregate.ClearDomainEvents();
        return id;
    }
}
