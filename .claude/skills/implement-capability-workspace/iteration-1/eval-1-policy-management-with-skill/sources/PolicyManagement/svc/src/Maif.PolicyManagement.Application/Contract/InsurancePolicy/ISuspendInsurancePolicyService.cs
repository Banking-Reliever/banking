using Maif.PolicyManagement.Contracts.Commands;

namespace Maif.PolicyManagement.Application.Contract.InsurancePolicy;

public interface ISuspendInsurancePolicyService
{
    Task SuspendAsync(SuspendInsurancePolicyCommand command);
}
