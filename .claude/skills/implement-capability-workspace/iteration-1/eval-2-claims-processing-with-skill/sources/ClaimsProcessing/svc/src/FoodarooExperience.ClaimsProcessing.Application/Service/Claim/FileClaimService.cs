using Foodaroo.Component.Messaging;
using FoodarooExperience.ClaimsProcessing.Application.Contract.Claim;
using FoodarooExperience.ClaimsProcessing.Contracts.Commands;
using FoodarooExperience.ClaimsProcessing.Domain.Model.AR.Claim;
using FoodarooExperience.ClaimsProcessing.Infrastructure.Data.Domain;

namespace FoodarooExperience.ClaimsProcessing.Application.Service.Claim;

public class FileClaimService : IFileClaimService
{
    private readonly IRepositoryClaim _repository;
    private readonly IClaimFactory _factory;
    private readonly IPublish _publisher;

    public FileClaimService(
        IRepositoryClaim repository,
        IClaimFactory factory,
        IPublish publisher)
    {
        _repository = repository;
        _factory = factory;
        _publisher = publisher;
    }

    public async Task<Guid> FileAsync(FileClaimCommand command)
    {
        var id = command.Id == Guid.Empty ? Guid.NewGuid() : command.Id;
        var aggregate = ClaimAR.Create(id);

        await _repository.InsertAggregate(aggregate);

        foreach (var evt in aggregate.GetDomainEvents())
            await _publisher.PublishAsync(evt, "foodaroo-experience-claims-processing-channel");

        aggregate.ClearDomainEvents();
        return id;
    }
}
