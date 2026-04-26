namespace FoodarooExperience.ClaimsProcessing.Contracts.Claims.Requests;

public sealed record FileClaimRequest(
    string ClaimantId,
    string Description,
    decimal Amount,
    string Currency
);
