using Foodaroo.Component.Messaging;

namespace Naive.PolicyManagement.Contracts.Events;

public class InsurancePolicyCreated : IMessage
{
    public Guid AggregateId { get; set; }
}
