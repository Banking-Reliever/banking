using FoodarooExperience.ClaimsProcessing.Domain.Claims;
using MediatR;
using Microsoft.Extensions.Logging;

namespace FoodarooExperience.ClaimsProcessing.Application.Claims.Queries.GetClaim;

public sealed class GetClaimQueryHandler : IRequestHandler<GetClaimQuery, ClaimDto?>
{
    private readonly IClaimRepository _claimRepository;
    private readonly ILogger<GetClaimQueryHandler> _logger;

    public GetClaimQueryHandler(
        IClaimRepository claimRepository,
        ILogger<GetClaimQueryHandler> logger)
    {
        _claimRepository = claimRepository;
        _logger = logger;
    }

    public async Task<ClaimDto?> Handle(GetClaimQuery request, CancellationToken cancellationToken)
    {
        var claimId = ClaimId.From(request.ClaimId);
        var claim = await _claimRepository.GetByIdAsync(claimId, cancellationToken);

        if (claim is null)
        {
            _logger.LogWarning("Claim not found: {ClaimId}", request.ClaimId);
            return null;
        }

        return new ClaimDto(
            ClaimId: claim.Id.Value,
            ClaimantId: claim.ClaimantId,
            Description: claim.Description,
            Amount: claim.Amount.Value,
            Currency: claim.Amount.Currency,
            Status: claim.Status.ToString(),
            FiledAt: claim.FiledAt,
            LastModifiedAt: claim.LastModifiedAt);
    }
}
