using Maif.PolicyManagement.Contracts.Commands;

namespace Maif.PolicyManagement.Application.Contract.InsurancePolicy;

public interface ICreateInsurancePolicyService
{
    Task<Guid> CreateAsync(CreateInsurancePolicyCommand command);
}
