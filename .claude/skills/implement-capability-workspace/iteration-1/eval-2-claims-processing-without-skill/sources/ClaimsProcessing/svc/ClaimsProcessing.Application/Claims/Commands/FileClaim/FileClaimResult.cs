namespace FoodarooExperience.ClaimsProcessing.Application.Claims.Commands.FileClaim;

public sealed record FileClaimResult(
    Guid ClaimId,
    string Status,
    DateTime FiledAt
);
