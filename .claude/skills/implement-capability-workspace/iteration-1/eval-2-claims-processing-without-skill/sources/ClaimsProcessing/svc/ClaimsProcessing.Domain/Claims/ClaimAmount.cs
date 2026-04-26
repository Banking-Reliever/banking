using FoodarooExperience.ClaimsProcessing.Domain.Common;

namespace FoodarooExperience.ClaimsProcessing.Domain.Claims;

public sealed class ClaimAmount : ValueObject
{
    public decimal Value { get; }
    public string Currency { get; }

    private ClaimAmount(decimal value, string currency)
    {
        Value = value;
        Currency = currency;
    }

    public static ClaimAmount Of(decimal value, string currency)
    {
        if (value < 0)
            throw new DomainException("Claim amount cannot be negative.");
        if (string.IsNullOrWhiteSpace(currency))
            throw new DomainException("Currency must be specified.");

        return new ClaimAmount(value, currency.ToUpperInvariant());
    }

    protected override IEnumerable<object?> GetEqualityComponents()
    {
        yield return Value;
        yield return Currency;
    }

    public override string ToString() => $"{Value} {Currency}";
}
