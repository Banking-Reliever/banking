using System;
using Foodaroo.Component.Messaging.Event;
using Foodaroo.Component.Messaging.PubSub;

namespace Naive.PolicyManagement.Contracts.Events;

[EventBus("naive-policy-management-channel")]
[BusinessCapability("EVT.RES.NAIVE.POLICY.POLICY_CREATED")]
public class PolicyCreated : IEventPayLoad
{
    public Guid AggregateId { get; set; }

    public long UnixTimestamp { get; set; }

    public Guid PolicyHolderId { get; set; }

    public string InsuranceType { get; set; } = string.Empty;

    public DateTime EffectiveDate { get; set; }

    public DateTime ExpirationDate { get; set; }

    public decimal PremiumAmount { get; set; }

    public DateTime CreatedAt { get; set; }

    public override bool Equals(object? obj)
    {
        if (obj == null) return false;
        var other = obj as PolicyCreated;
        return other != null && Equals(other);
    }

    public bool Equals(PolicyCreated? other)
    {
        if (other == null) return false;
        return this.AggregateId == other.AggregateId;
    }

    public override int GetHashCode()
    {
        var hash = 13;
        hash = (hash * 7) + AggregateId.GetHashCode();
        return hash;
    }
}
