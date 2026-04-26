namespace Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy.ValueObject;

/// <summary>
/// Value Object representing a policy premium amount.
/// Must be strictly positive and below a reasonable maximum.
/// </summary>
public class PolicyPremiumVO
{
    private readonly decimal _amount;

    private const decimal MinAmount = 0.01m;
    private const decimal MaxAmount = 1_000_000m;

    private PolicyPremiumVO(decimal amount)
    {
        _amount = amount;
    }

    private static bool Assert(decimal amount)
        => amount >= MinAmount && amount <= MaxAmount;

    public static bool TryParse(decimal amount, out PolicyPremiumVO? vo)
    {
        vo = null;
        if (!Assert(amount)) return false;
        vo = new PolicyPremiumVO(amount);
        return true;
    }

    public static PolicyPremiumVO Parse(decimal amount)
    {
        if (!Assert(amount)) throw new ArgumentException($"Premium amount {amount} is out of allowed range [{MinAmount}, {MaxAmount}].");
        return new PolicyPremiumVO(amount);
    }

    public decimal Value() => _amount;

    public override bool Equals(object? obj)
    {
        if (obj == null) return false;
        var other = obj as PolicyPremiumVO;
        return other != null && Equals(other);
    }

    public bool Equals(PolicyPremiumVO? other)
    {
        if (other == null) return false;
        return _amount == other._amount;
    }

    public override int GetHashCode()
    {
        var hash = 13;
        hash = (hash * 7) + _amount.GetHashCode();
        return hash;
    }
}
