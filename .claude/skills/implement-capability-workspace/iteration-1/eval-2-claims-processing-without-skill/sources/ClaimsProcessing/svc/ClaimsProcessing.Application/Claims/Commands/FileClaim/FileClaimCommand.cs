using MediatR;

namespace FoodarooExperience.ClaimsProcessing.Application.Claims.Commands.FileClaim;

public sealed record FileClaimCommand(
    string ClaimantId,
    string Description,
    decimal Amount,
    string Currency
) : IRequest<FileClaimResult>;
