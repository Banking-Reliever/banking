namespace FoodarooExperience.ClaimsProcessing.Application.Claims.Queries.GetClaim;

public sealed record ClaimDto(
    Guid ClaimId,
    string ClaimantId,
    string Description,
    decimal Amount,
    string Currency,
    string Status,
    DateTime FiledAt,
    DateTime? LastModifiedAt
);
