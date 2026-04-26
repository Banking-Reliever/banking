using FoodarooExperience.ClaimsProcessing.Domain.Common;

namespace FoodarooExperience.ClaimsProcessing.Domain.Claims.Events;

public sealed class ClaimFiled : IDomainEvent
{
    public ClaimFiled(
        ClaimId claimId,
        string claimantId,
        string description,
        ClaimAmount amount,
        DateTime filedAt)
    {
        EventId = Guid.NewGuid();
        OccurredOn = DateTime.UtcNow;
        ClaimId = claimId;
        ClaimantId = claimantId;
        Description = description;
        Amount = amount;
        FiledAt = filedAt;
    }

    public Guid EventId { get; }
    public DateTime OccurredOn { get; }
    public ClaimId ClaimId { get; }
    public string ClaimantId { get; }
    public string Description { get; }
    public ClaimAmount Amount { get; }
    public DateTime FiledAt { get; }
}
