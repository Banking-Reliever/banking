using System;

namespace Maif.PolicyManagement.Contracts.Commands;

/// <summary>
/// Command to create a new insurance policy.
/// </summary>
public class CreatePolicyCommand
{
    /// <summary>
    /// Identifier of the policy holder (insured person).
    /// </summary>
    public Guid PolicyHolderId { get; set; }

    /// <summary>
    /// Type of insurance (e.g. "Auto", "Home", "Health").
    /// </summary>
    public string InsuranceType { get; set; } = string.Empty;

    /// <summary>
    /// Date from which the policy is effective.
    /// </summary>
    public DateTime EffectiveDate { get; set; }

    /// <summary>
    /// Date on which the policy expires.
    /// </summary>
    public DateTime ExpirationDate { get; set; }

    /// <summary>
    /// Annual premium amount in euros.
    /// </summary>
    public decimal PremiumAmount { get; set; }
}
