using System;

namespace Maif.PolicyManagement.Contracts.DataProduct;

/// <summary>
/// Data product representing an insurance policy, exposed as a read model.
/// </summary>
public class InsurancePolicyDataProduct
{
    /// <summary>
    /// Unique identifier of the policy.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Identifier of the policy holder.
    /// </summary>
    public Guid PolicyHolderId { get; set; }

    /// <summary>
    /// Type of insurance (e.g. "Auto", "Home", "Health").
    /// </summary>
    public string InsuranceType { get; set; } = string.Empty;

    /// <summary>
    /// Current status of the policy.
    /// </summary>
    public string Status { get; set; } = string.Empty;

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

    /// <summary>
    /// Date and time when the policy was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>
    /// Date and time when the policy was suspended, if applicable.
    /// </summary>
    public DateTime? SuspendedAt { get; set; }

    /// <summary>
    /// Reason for suspension, if applicable.
    /// </summary>
    public string? SuspensionReason { get; set; }

    /// <summary>
    /// Version of the read model.
    /// </summary>
    public long Version { get; set; }

    /// <summary>
    /// Last update timestamp in Unix format.
    /// </summary>
    public long LastUpdateUnixTimestamp { get; set; }
}
