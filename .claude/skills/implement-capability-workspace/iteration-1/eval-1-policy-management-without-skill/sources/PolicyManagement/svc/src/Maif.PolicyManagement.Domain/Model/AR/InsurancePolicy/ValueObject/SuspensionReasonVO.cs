namespace Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy.ValueObject;

/// <summary>
/// Value Object representing the reason for policy suspension.
/// Must be non-empty and within a reasonable length.
/// </summary>
public class SuspensionReasonVO
{
    private readonly string _reason;

    private const int MaxLength = 500;

    private SuspensionReasonVO(string reason)
    {
        _reason = reason;
    }

    private static bool Assert(string reason)
        => !string.IsNullOrWhiteSpace(reason) && reason.Length <= MaxLength;

    public static bool TryParse(string reason, out SuspensionReasonVO? vo)
    {
        vo = null;
        if (!Assert(reason)) return false;
        vo = new SuspensionReasonVO(reason.Trim());
        return true;
    }

    public static SuspensionReasonVO Parse(string reason)
    {
        if (!Assert(reason)) throw new ArgumentException("Suspension reason must be non-empty and at most 500 characters.");
        return new SuspensionReasonVO(reason.Trim());
    }

    public string Value() => _reason;

    public override bool Equals(object? obj)
    {
        if (obj == null) return false;
        var other = obj as SuspensionReasonVO;
        return other != null && Equals(other);
    }

    public bool Equals(SuspensionReasonVO? other)
    {
        if (other == null) return false;
        return string.Equals(_reason, other._reason, StringComparison.OrdinalIgnoreCase);
    }

    public override int GetHashCode()
    {
        var hash = 13;
        hash = (hash * 7) + _reason.ToLowerInvariant().GetHashCode();
        return hash;
    }
}
