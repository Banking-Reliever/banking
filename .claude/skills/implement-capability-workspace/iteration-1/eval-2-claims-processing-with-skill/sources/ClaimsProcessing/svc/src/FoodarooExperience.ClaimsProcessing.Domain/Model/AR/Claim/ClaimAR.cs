using Foodaroo.Component.Domain.Aggregate;
using Foodaroo.Component.Domain.Exceptions;
using FoodarooExperience.ClaimsProcessing.Contracts.Events;
using FoodarooExperience.ClaimsProcessing.Domain.Errors;

namespace FoodarooExperience.ClaimsProcessing.Domain.Model.AR.Claim;

public class ClaimAR : AggregateRoot<ClaimDto>
{
    private Guid _id;
    private ClaimState _state;

    public enum ClaimState
    {
        Created,
        Active,
        Closed
    }

    public ClaimAR(Guid id)
    {
        if (id == Guid.Empty) throw new ArgumentNullException(nameof(id));
        _id = id;
        _state = ClaimState.Created;
    }

    public ClaimAR(Guid id, int state)
    {
        _id = id;
        _state = (ClaimState)state;
    }

    public static ClaimAR Create(Guid id)
    {
        var ar = new ClaimAR(id);
        ar.RaiseEvent(new ClaimFiled { AggregateId = id });
        return ar;
    }

    public override ClaimDto ToDto(long lastUpdateUnixTimestamp) => new()
    {
        TechnicalId = _id,
        LastUpdateUnixTimestamp = lastUpdateUnixTimestamp,
        State = (int)_state
    };
}
