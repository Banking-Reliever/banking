using System;

namespace Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy.Factory;

public interface IInsurancePolicyFactory
{
    InsurancePolicyAR CreateInstance(Guid aggregateId);
    InsurancePolicyAR CreateInstance(InsurancePolicyDto payload);
}
