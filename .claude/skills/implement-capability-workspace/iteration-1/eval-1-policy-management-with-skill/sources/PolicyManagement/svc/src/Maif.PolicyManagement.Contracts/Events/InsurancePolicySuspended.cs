using Foodaroo.Component.Messaging;

namespace Maif.PolicyManagement.Contracts.Events;

public class InsurancePolicySuspended : IMessage
{
    public Guid AggregateId { get; set; }
}
