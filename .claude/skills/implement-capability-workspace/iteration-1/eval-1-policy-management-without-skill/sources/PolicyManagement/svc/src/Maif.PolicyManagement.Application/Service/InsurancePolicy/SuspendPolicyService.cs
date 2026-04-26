using System;
using System.Threading.Tasks;

using Maif.PolicyManagement.Application.Contract.InsurancePolicy;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy.ValueObject;
using Maif.PolicyManagement.Infrastructure.Data.Domain;

namespace Maif.PolicyManagement.Application.Service.InsurancePolicy;

public class SuspendPolicyService : ISuspendPolicyService
{
    private readonly IRepositoryInsurancePolicy _repoAgg;

    public SuspendPolicyService(IRepositoryInsurancePolicy repoAgg)
    {
        _repoAgg = repoAgg ?? throw new ArgumentNullException(nameof(repoAgg));
    }

    public async Task SuspendPolicy(Guid policyId, string reason)
    {
        if (policyId == Guid.Empty) throw new ArgumentNullException(nameof(policyId));

        SuspensionReasonVO.TryParse(reason, out var suspensionReason);
        if (suspensionReason == null) throw new ArgumentException("Invalid suspension reason.", nameof(reason));

        var agg = await _repoAgg.GetByAggregateRootId(policyId);

        agg.SuspendPolicy(suspensionReason);

        await _repoAgg.SaveAggregate(agg);
    }
}
