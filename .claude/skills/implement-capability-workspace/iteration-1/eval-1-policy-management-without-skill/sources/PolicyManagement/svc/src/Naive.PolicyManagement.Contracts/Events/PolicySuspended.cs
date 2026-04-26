using System;
using Foodaroo.Component.Messaging.Event;
using Foodaroo.Component.Messaging.PubSub;

namespace Naive.PolicyManagement.Contracts.Events;

[EventBus("naive-policy-management-channel")]
[BusinessCapability("EVT.RES.NAIVE.POLICY.POLICY_SUSPENDED")]
public class PolicySuspended : IEventPayLoad
{
    public Guid AggregateId { get; set; }

    public long UnixTimestamp { get; set; }

    public string Reason { get; set; } = string.Empty;

    public DateTime SuspendedAt { get; set; }

    public override bool Equals(object? obj)
    {
        if (obj == null) return false;
        var other = obj as PolicySuspended;
        return other != null && Equals(other);
    }

    public bool Equals(PolicySuspended? other)
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
