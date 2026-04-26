using Foodaroo.Component.DB.Repository.Base;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.Messaging;

namespace Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy;

[Collection(Name = "InsurancePolicy")]
public class InsurancePolicyDto : IAggregateRootDto, IDbObject, IDbAggregate
{
    public long LastUpdateUnixTimestamp { get; set; }
    public Guid TechnicalId { get; set; }
    public int State { get; set; }
}
