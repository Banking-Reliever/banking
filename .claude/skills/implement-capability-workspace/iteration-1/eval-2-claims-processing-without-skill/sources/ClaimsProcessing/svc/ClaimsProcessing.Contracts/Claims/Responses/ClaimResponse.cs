namespace FoodarooExperience.ClaimsProcessing.Contracts.Claims.Responses;

public sealed record ClaimResponse(
    Guid ClaimId,
    string ClaimantId,
    string Description,
    decimal Amount,
    string Currency,
    string Status,
    DateTime FiledAt,
    DateTime? LastModifiedAt
);
