namespace Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy;

public interface IInsurancePolicyFactory
{
    InsurancePolicyAR CreateInstance(Guid id);
    InsurancePolicyAR CreateInstance(InsurancePolicyDto payload);
}
