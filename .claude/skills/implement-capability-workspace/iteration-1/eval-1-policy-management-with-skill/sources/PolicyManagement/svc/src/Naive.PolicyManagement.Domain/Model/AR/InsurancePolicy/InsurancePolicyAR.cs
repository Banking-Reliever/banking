using Foodaroo.Component.Domain.Aggregate;
using Foodaroo.Component.Domain.Exceptions;
using Naive.PolicyManagement.Contracts.Events;
using Naive.PolicyManagement.Domain.Errors;

namespace Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;

public class InsurancePolicyAR : AggregateRoot<InsurancePolicyDto>
{
    private Guid _id;
    private InsurancePolicyState _state;

    public enum InsurancePolicyState
    {
        Created,
        Active,
        Closed
    }

    public InsurancePolicyAR(Guid id)
    {
        if (id == Guid.Empty) throw new ArgumentNullException(nameof(id));
        _id = id;
        _state = InsurancePolicyState.Created;
    }

    public InsurancePolicyAR(Guid id, int state)
    {
        _id = id;
        _state = (InsurancePolicyState)state;
    }

    public static InsurancePolicyAR Create(Guid id)
    {
        var ar = new InsurancePolicyAR(id);
        ar.RaiseEvent(new InsurancePolicyCreated { AggregateId = id });
        return ar;
    }

    public void Suspend()
    {
        if (_state == InsurancePolicyState.Closed)
            throw new DomainException(Code.InvalidState, $"Cannot suspend a closed policy.");
        _state = InsurancePolicyState.Closed;
        RaiseEvent(new InsurancePolicySuspended { AggregateId = _id });
    }

    public override InsurancePolicyDto ToDto(long lastUpdateUnixTimestamp) => new()
    {
        TechnicalId = _id,
        LastUpdateUnixTimestamp = lastUpdateUnixTimestamp,
        State = (int)_state
    };
}
