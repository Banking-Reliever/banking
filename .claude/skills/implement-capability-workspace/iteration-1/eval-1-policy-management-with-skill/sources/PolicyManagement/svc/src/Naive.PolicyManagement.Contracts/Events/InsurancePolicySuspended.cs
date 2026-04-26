using Foodaroo.Component.Messaging;

namespace Naive.PolicyManagement.Contracts.Events;

public class InsurancePolicySuspended : IMessage
{
    public Guid AggregateId { get; set; }
}
