using System;
using System.Threading.Tasks;

using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.DB.Repository;

namespace Maif.PolicyManagement.Infrastructure.Data.Domain;

public interface IRepositoryInsurancePolicy
    : IRepoAggregate<InsurancePolicyAR, InsurancePolicyDto>,
      IAggregateRepository<InsurancePolicyAR, InsurancePolicyDto>
{
}
