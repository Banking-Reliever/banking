using Foodaroo.Component.Messaging;

namespace Maif.PolicyManagement.Contracts.Events;

public class InsurancePolicyCreated : IMessage
{
    public Guid AggregateId { get; set; }
}
