using System;
using System.Collections.Generic;

using Foodaroo.Component.Messaging;
using Foodaroo.Component.Domain.Exceptions;
using Foodaroo.Component.Domain.Aggregate;

using Naive.PolicyManagement.Domain.Errors;
using Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy.ValueObject;
using Naive.PolicyManagement.Contracts.Events;

namespace Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;

/// <summary>
/// Aggregate Root for InsurancePolicy.
/// State Machine:
///   Draft -> Active -> Suspended
/// </summary>
public class InsurancePolicyAR : AggregateRoot<InsurancePolicyDto>
{
    private Guid _aggregateRootId;
    private Guid _policyHolderId;
    private string _insuranceType = string.Empty;
    private InsurancePolicyState _state;
    private DateTime _effectiveDate;
    private DateTime _expirationDate;
    private PolicyPremiumVO? _premium;
    private DateTime _createdAt;
    private DateTime? _suspendedAt;
    private SuspensionReasonVO? _suspensionReason;

    public enum InsurancePolicyState
    {
        Draft = 0,
        Active = 1,
        Suspended = 2
    }

    #region Constructors

    /// <summary>
    /// Constructor for creating a brand-new policy (Draft state, before CreatePolicy is called).
    /// </summary>
    public InsurancePolicyAR(Guid aggregateRootId)
    {
        if (aggregateRootId == Guid.Empty) throw new ArgumentNullException(nameof(aggregateRootId));

        _aggregateRootId = aggregateRootId;
        _state = InsurancePolicyState.Draft;
    }

    /// <summary>
    /// Reconstitution constructor for Active policies.
    /// </summary>
    public InsurancePolicyAR(
        Guid aggregateRootId,
        Guid policyHolderId,
        string insuranceType,
        DateTime effectiveDate,
        DateTime expirationDate,
        decimal premiumAmount,
        DateTime createdAt)
    {
        if (aggregateRootId == Guid.Empty) throw new ArgumentNullException(nameof(aggregateRootId));
        if (policyHolderId == Guid.Empty) throw new ArgumentNullException(nameof(policyHolderId));

        _aggregateRootId = aggregateRootId;
        _policyHolderId = policyHolderId;
        _insuranceType = insuranceType;
        _effectiveDate = effectiveDate;
        _expirationDate = expirationDate;
        _premium = PolicyPremiumVO.Parse(premiumAmount);
        _createdAt = createdAt;
        _state = InsurancePolicyState.Active;
    }

    /// <summary>
    /// Reconstitution constructor for Suspended policies.
    /// </summary>
    public InsurancePolicyAR(
        Guid aggregateRootId,
        Guid policyHolderId,
        string insuranceType,
        DateTime effectiveDate,
        DateTime expirationDate,
        decimal premiumAmount,
        DateTime createdAt,
        DateTime suspendedAt,
        string suspensionReason)
    {
        if (aggregateRootId == Guid.Empty) throw new ArgumentNullException(nameof(aggregateRootId));
        if (policyHolderId == Guid.Empty) throw new ArgumentNullException(nameof(policyHolderId));

        _aggregateRootId = aggregateRootId;
        _policyHolderId = policyHolderId;
        _insuranceType = insuranceType;
        _effectiveDate = effectiveDate;
        _expirationDate = expirationDate;
        _premium = PolicyPremiumVO.Parse(premiumAmount);
        _createdAt = createdAt;
        _suspendedAt = suspendedAt;
        SuspensionReasonVO.TryParse(suspensionReason, out _suspensionReason);
        _state = InsurancePolicyState.Suspended;
    }

    #endregion

    /// <summary>
    /// Creates the insurance policy, transitioning from Draft to Active.
    /// Raises a PolicyCreated event.
    /// </summary>
    public void CreatePolicy(
        Guid policyHolderId,
        string insuranceType,
        DateTime effectiveDate,
        DateTime expirationDate,
        PolicyPremiumVO premium)
    {
        if (_state != InsurancePolicyState.Draft)
            throw new BusinessException(Code.PolicyAlreadyExists, "Policy has already been created.");

        if (policyHolderId == Guid.Empty)
            throw new BusinessException(Code.PolicyAlreadyExists, "PolicyHolderId must be provided.");

        if (effectiveDate >= expirationDate)
            throw new BusinessException(Code.InvalidEffectiveDate, "Effective date must be before expiration date.");

        _policyHolderId = policyHolderId;
        _insuranceType = insuranceType;
        _effectiveDate = effectiveDate;
        _expirationDate = expirationDate;
        _premium = premium;
        _createdAt = DateTime.UtcNow;
        _state = InsurancePolicyState.Active;

        RaiseEvent(new PolicyCreated
        {
            AggregateId = _aggregateRootId,
            PolicyHolderId = _policyHolderId,
            InsuranceType = _insuranceType,
            EffectiveDate = _effectiveDate,
            ExpirationDate = _expirationDate,
            PremiumAmount = _premium.Value(),
            CreatedAt = _createdAt
        });
    }

    /// <summary>
    /// Suspends an active policy, transitioning from Active to Suspended.
    /// Raises a PolicySuspended event.
    /// </summary>
    public void SuspendPolicy(SuspensionReasonVO reason)
    {
        if (_state == InsurancePolicyState.Draft)
            throw new BusinessException(Code.PolicyNotActive, "Cannot suspend a policy that has not been created yet.");

        if (_state == InsurancePolicyState.Suspended)
            throw new BusinessException(
                Code.PolicyAlreadySuspended,
                "Policy is already suspended.",
                new Dictionary<string, string> { { "aggregateId", _aggregateRootId.ToString() } });

        _suspensionReason = reason;
        _suspendedAt = DateTime.UtcNow;
        _state = InsurancePolicyState.Suspended;

        RaiseEvent(new PolicySuspended
        {
            AggregateId = _aggregateRootId,
            Reason = _suspensionReason.Value(),
            SuspendedAt = _suspendedAt.Value
        });
    }

    public override InsurancePolicyDto ToDto(long lastUpdateUnixTimestamp)
    {
        return new InsurancePolicyDto
        {
            TechnicalId = _aggregateRootId,
            LastUpdateUnixTimestamp = lastUpdateUnixTimestamp,
            State = (int)_state,
            PolicyHolderId = _policyHolderId,
            InsuranceType = _insuranceType,
            EffectiveDate = _effectiveDate,
            ExpirationDate = _expirationDate,
            PremiumAmount = _premium?.Value() ?? 0m,
            CreatedAt = _createdAt,
            SuspendedAt = _suspendedAt,
            SuspensionReason = _suspensionReason?.Value()
        };
    }
}
