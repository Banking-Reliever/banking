using Foodaroo.Component.Messaging;
using Maif.PolicyManagement.Application.Contract.InsurancePolicy;
using Maif.PolicyManagement.Contracts.Commands;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Maif.PolicyManagement.Infrastructure.Data.Domain;

namespace Maif.PolicyManagement.Application.Service.InsurancePolicy;

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
            await _publisher.PublishAsync(evt, "maif-policy-management-channel");

        aggregate.ClearDomainEvents();
        return id;
    }
}
