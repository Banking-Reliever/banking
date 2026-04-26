using Foodaroo.Component.Messaging;

namespace FoodarooExperience.ClaimsProcessing.Contracts.Events;

public class ClaimFiled : IMessage
{
    public Guid AggregateId { get; set; }
}
