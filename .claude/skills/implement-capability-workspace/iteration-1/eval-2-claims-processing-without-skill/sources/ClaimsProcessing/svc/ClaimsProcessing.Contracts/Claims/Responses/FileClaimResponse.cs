namespace FoodarooExperience.ClaimsProcessing.Contracts.Claims.Responses;

public sealed record FileClaimResponse(
    Guid ClaimId,
    string Status,
    DateTime FiledAt
);
