namespace Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;

public class InsurancePolicyFactory : IInsurancePolicyFactory
{
    public InsurancePolicyAR CreateInstance(Guid id)
        => new InsurancePolicyAR(id);

    public InsurancePolicyAR CreateInstance(InsurancePolicyDto payload)
        => new InsurancePolicyAR(payload.TechnicalId, payload.State);
}
