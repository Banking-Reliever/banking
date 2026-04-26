using FoodarooExperience.ClaimsProcessing.Domain.Claims.Events;
using FoodarooExperience.ClaimsProcessing.Domain.Common;

namespace FoodarooExperience.ClaimsProcessing.Domain.Claims;

public sealed class Claim : AggregateRoot<ClaimId>
{
    private Claim(
        ClaimId id,
        string claimantId,
        string description,
        ClaimAmount amount,
        DateTime filedAt)
        : base(id)
    {
        ClaimantId = claimantId;
        Description = description;
        Amount = amount;
        FiledAt = filedAt;
        Status = ClaimStatus.Filed;
    }

    public string ClaimantId { get; private set; }
    public string Description { get; private set; }
    public ClaimAmount Amount { get; private set; }
    public DateTime FiledAt { get; private set; }
    public ClaimStatus Status { get; private set; }
    public DateTime? LastModifiedAt { get; private set; }

    public static Claim File(
        string claimantId,
        string description,
        ClaimAmount amount)
    {
        if (string.IsNullOrWhiteSpace(claimantId))
            throw new DomainException("ClaimantId must be specified.");
        if (string.IsNullOrWhiteSpace(description))
            throw new DomainException("Description must be specified.");
        if (amount is null)
            throw new DomainException("Amount must be specified.");

        var claimId = ClaimId.New();
        var filedAt = DateTime.UtcNow;

        var claim = new Claim(claimId, claimantId, description, amount, filedAt);

        claim.RaiseDomainEvent(new ClaimFiled(claimId, claimantId, description, amount, filedAt));

        return claim;
    }

    public void MarkUnderReview()
    {
        if (Status != ClaimStatus.Filed)
            throw new DomainException($"Cannot move claim to UnderReview from status '{Status}'.");

        Status = ClaimStatus.UnderReview;
        LastModifiedAt = DateTime.UtcNow;
    }

    public void Approve()
    {
        if (Status != ClaimStatus.UnderReview)
            throw new DomainException($"Cannot approve claim from status '{Status}'.");

        Status = ClaimStatus.Approved;
        LastModifiedAt = DateTime.UtcNow;
    }

    public void Reject()
    {
        if (Status != ClaimStatus.UnderReview)
            throw new DomainException($"Cannot reject claim from status '{Status}'.");

        Status = ClaimStatus.Rejected;
        LastModifiedAt = DateTime.UtcNow;
    }
}
