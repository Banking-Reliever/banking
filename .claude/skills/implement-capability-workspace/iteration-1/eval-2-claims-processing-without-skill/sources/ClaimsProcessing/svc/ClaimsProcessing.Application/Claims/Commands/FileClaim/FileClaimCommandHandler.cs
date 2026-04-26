using FoodarooExperience.ClaimsProcessing.Application.Common.Interfaces;
using FoodarooExperience.ClaimsProcessing.Domain.Claims;
using MediatR;
using Microsoft.Extensions.Logging;

namespace FoodarooExperience.ClaimsProcessing.Application.Claims.Commands.FileClaim;

public sealed class FileClaimCommandHandler : IRequestHandler<FileClaimCommand, FileClaimResult>
{
    private readonly IClaimRepository _claimRepository;
    private readonly IUnitOfWork _unitOfWork;
    private readonly IEventPublisher _eventPublisher;
    private readonly ILogger<FileClaimCommandHandler> _logger;

    public FileClaimCommandHandler(
        IClaimRepository claimRepository,
        IUnitOfWork unitOfWork,
        IEventPublisher eventPublisher,
        ILogger<FileClaimCommandHandler> logger)
    {
        _claimRepository = claimRepository;
        _unitOfWork = unitOfWork;
        _eventPublisher = eventPublisher;
        _logger = logger;
    }

    public async Task<FileClaimResult> Handle(FileClaimCommand request, CancellationToken cancellationToken)
    {
        var amount = ClaimAmount.Of(request.Amount, request.Currency);

        var claim = Claim.File(
            claimantId: request.ClaimantId,
            description: request.Description,
            amount: amount);

        await _claimRepository.AddAsync(claim, cancellationToken);
        await _unitOfWork.SaveChangesAsync(cancellationToken);

        foreach (var domainEvent in claim.DomainEvents)
        {
            await _eventPublisher.PublishAsync(domainEvent, cancellationToken);
        }

        claim.ClearDomainEvents();

        _logger.LogInformation(
            "Claim filed successfully. ClaimId: {ClaimId}, ClaimantId: {ClaimantId}",
            claim.Id.Value,
            claim.ClaimantId);

        return new FileClaimResult(
            ClaimId: claim.Id.Value,
            Status: claim.Status.ToString(),
            FiledAt: claim.FiledAt);
    }
}
