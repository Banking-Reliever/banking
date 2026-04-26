namespace FoodarooExperience.ClaimsProcessing.Domain.Claims;

public sealed record ClaimId(Guid Value)
{
    public static ClaimId New() => new(Guid.NewGuid());

    public static ClaimId From(Guid value)
    {
        if (value == Guid.Empty)
            throw new ArgumentException("ClaimId cannot be empty.", nameof(value));
        return new ClaimId(value);
    }

    public override string ToString() => Value.ToString();
}
