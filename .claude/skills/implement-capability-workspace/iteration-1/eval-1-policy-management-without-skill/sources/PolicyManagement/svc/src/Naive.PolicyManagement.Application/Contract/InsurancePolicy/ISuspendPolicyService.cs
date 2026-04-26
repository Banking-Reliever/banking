using System;
using System.Threading.Tasks;

namespace Naive.PolicyManagement.Application.Contract.InsurancePolicy;

public interface ISuspendPolicyService
{
    /// <summary>
    /// Suspends an existing active insurance policy.
    /// </summary>
    Task SuspendPolicy(Guid policyId, string reason);
}
