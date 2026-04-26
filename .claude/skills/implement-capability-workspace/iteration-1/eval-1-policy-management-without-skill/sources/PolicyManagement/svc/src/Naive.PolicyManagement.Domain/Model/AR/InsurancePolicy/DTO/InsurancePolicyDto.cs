using System;
using Foodaroo.Component.DB.Repository.Base;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.Messaging;

namespace Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;

[Collection(Name = "InsurancePolicy")]
public class InsurancePolicyDto : IAggregateRootDto, IDbObject, IDbAggregate
{
    public long LastUpdateUnixTimestamp { get; set; }

    public Guid TechnicalId { get; set; }

    public Guid PolicyHolderId { get; set; }

    public string InsuranceType { get; set; } = string.Empty;

    /// <summary>
    /// Mapped from InsurancePolicyAR.InsurancePolicyState enum (int value).
    /// </summary>
    public int State { get; set; }

    public DateTime EffectiveDate { get; set; }

    public DateTime ExpirationDate { get; set; }

    public decimal PremiumAmount { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime? SuspendedAt { get; set; }

    public string? SuspensionReason { get; set; }
}
