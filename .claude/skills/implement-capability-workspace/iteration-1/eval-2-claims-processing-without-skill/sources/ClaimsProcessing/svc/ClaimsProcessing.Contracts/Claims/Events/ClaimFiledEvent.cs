namespace FoodarooExperience.ClaimsProcessing.Contracts.Claims.Events;

/// <summary>
/// Integration event published to the message broker when a claim is filed.
/// This is the contract for external consumers.
/// </summary>
public sealed record ClaimFiledEvent(
    Guid EventId,
    DateTime OccurredOn,
    Guid ClaimId,
    string ClaimantId,
    string Description,
    decimal Amount,
    string Currency,
    DateTime FiledAt
);
