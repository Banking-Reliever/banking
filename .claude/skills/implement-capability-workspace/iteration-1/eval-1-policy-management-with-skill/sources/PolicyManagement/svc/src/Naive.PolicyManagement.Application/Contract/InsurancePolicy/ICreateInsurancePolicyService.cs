using Naive.PolicyManagement.Contracts.Commands;

namespace Naive.PolicyManagement.Application.Contract.InsurancePolicy;

public interface ICreateInsurancePolicyService
{
    Task<Guid> CreateAsync(CreateInsurancePolicyCommand command);
}
