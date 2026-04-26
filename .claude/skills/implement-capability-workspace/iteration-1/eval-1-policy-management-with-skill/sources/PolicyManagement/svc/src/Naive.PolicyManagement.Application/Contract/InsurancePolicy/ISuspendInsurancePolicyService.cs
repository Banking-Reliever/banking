using Naive.PolicyManagement.Contracts.Commands;

namespace Naive.PolicyManagement.Application.Contract.InsurancePolicy;

public interface ISuspendInsurancePolicyService
{
    Task SuspendAsync(SuspendInsurancePolicyCommand command);
}
