using System;
using System.Threading.Tasks;

namespace Naive.PolicyManagement.Application.Contract.InsurancePolicy;

public interface ICreatePolicyService
{
    /// <summary>
    /// Creates a new insurance policy for the given policy holder.
    /// Returns the new aggregate id (policyId).
    /// </summary>
    Task<Guid> CreatePolicy(
        Guid policyHolderId,
        string insuranceType,
        DateTime effectiveDate,
        DateTime expirationDate,
        decimal premiumAmount);
}
