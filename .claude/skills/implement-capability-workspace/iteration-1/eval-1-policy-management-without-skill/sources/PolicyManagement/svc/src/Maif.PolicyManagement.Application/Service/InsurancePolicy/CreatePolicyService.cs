using System;
using System.Threading.Tasks;

using Maif.PolicyManagement.Application.Contract.InsurancePolicy;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy.Factory;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy.ValueObject;
using Maif.PolicyManagement.Infrastructure.Data.Domain;

namespace Maif.PolicyManagement.Application.Service.InsurancePolicy;

public class CreatePolicyService : ICreatePolicyService
{
    private readonly IInsurancePolicyFactory _factory;
    private readonly IRepositoryInsurancePolicy _repoAgg;

    public CreatePolicyService(
        IInsurancePolicyFactory factory,
        IRepositoryInsurancePolicy repoAgg)
    {
        _factory = factory ?? throw new ArgumentNullException(nameof(factory));
        _repoAgg = repoAgg ?? throw new ArgumentNullException(nameof(repoAgg));
    }

    public async Task<Guid> CreatePolicy(
        Guid policyHolderId,
        string insuranceType,
        DateTime effectiveDate,
        DateTime expirationDate,
        decimal premiumAmount)
    {
        if (policyHolderId == Guid.Empty) throw new ArgumentNullException(nameof(policyHolderId));
        if (string.IsNullOrWhiteSpace(insuranceType)) throw new ArgumentNullException(nameof(insuranceType));

        var aggregateId = Guid.NewGuid();

        PolicyPremiumVO.TryParse(premiumAmount, out var premium);
        if (premium == null) throw new ArgumentException("Invalid premium amount.", nameof(premiumAmount));

        var agg = _factory.CreateInstance(aggregateId);

        agg.CreatePolicy(policyHolderId, insuranceType, effectiveDate, expirationDate, premium);

        await _repoAgg.SaveAggregate(agg);

        return aggregateId;
    }
}
