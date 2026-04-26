using System;

namespace Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy.Factory;

public class InsurancePolicyFactory : IInsurancePolicyFactory
{
    /// <summary>
    /// Creates a brand-new, empty aggregate (Draft state) ready to receive the CreatePolicy command.
    /// </summary>
    public InsurancePolicyAR CreateInstance(Guid aggregateId)
    {
        return new InsurancePolicyAR(aggregateId);
    }

    /// <summary>
    /// Reconstitutes the aggregate from its persisted DTO.
    /// </summary>
    public InsurancePolicyAR CreateInstance(InsurancePolicyDto payload)
    {
        return payload.State switch
        {
            (int)InsurancePolicyAR.InsurancePolicyState.Draft =>
                new InsurancePolicyAR(payload.TechnicalId),

            (int)InsurancePolicyAR.InsurancePolicyState.Active =>
                new InsurancePolicyAR(
                    payload.TechnicalId,
                    payload.PolicyHolderId,
                    payload.InsuranceType,
                    payload.EffectiveDate,
                    payload.ExpirationDate,
                    payload.PremiumAmount,
                    payload.CreatedAt),

            (int)InsurancePolicyAR.InsurancePolicyState.Suspended =>
                new InsurancePolicyAR(
                    payload.TechnicalId,
                    payload.PolicyHolderId,
                    payload.InsuranceType,
                    payload.EffectiveDate,
                    payload.ExpirationDate,
                    payload.PremiumAmount,
                    payload.CreatedAt,
                    payload.SuspendedAt ?? DateTime.MinValue,
                    payload.SuspensionReason ?? string.Empty),

            _ => throw new InvalidOperationException($"Unknown InsurancePolicyState: {payload.State}")
        };
    }
}
