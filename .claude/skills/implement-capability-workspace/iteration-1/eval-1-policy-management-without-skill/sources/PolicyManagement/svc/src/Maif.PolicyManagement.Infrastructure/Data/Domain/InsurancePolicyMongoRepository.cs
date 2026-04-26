using System;
using System.Threading.Tasks;

using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy.Factory;

using Foodaroo.Component.DB.Repository.Base;
using Foodaroo.Component.Configuration;
using Foodaroo.Component.Logging;
using Foodaroo.Component.Messaging;
using Foodaroo.Component.DB.Repository.Mongo;
using Foodaroo.Component.DB.Repository;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.Correlation;

namespace Maif.PolicyManagement.Infrastructure.Data.Domain;

public class InsurancePolicyMongoRepository
    : MongoAggregateRepositoryBase<InsurancePolicyAR, InsurancePolicyDto>,
      IRepositoryInsurancePolicy
{
    private readonly IInsurancePolicyFactory _factory;
    private AggregateDocument<InsurancePolicyDto>? _currentDoc;

    public InsurancePolicyMongoRepository(
        ITransactionHandler tranHandler,
        IMongoHandle<AggregateDocument<InsurancePolicyDto>> mongoHandle,
        IMongoHandle<DbMessage> mongoHandleEvt,
        ILogFoodaroo logger,
        ICorrelationContextAccessor correlation,
        DBSerializationOptions serializationOptions,
        EnvironmentSettings environment)
        : base(tranHandler, mongoHandle, mongoHandleEvt, logger, correlation, serializationOptions, environment)
    {
        _factory = new InsurancePolicyFactory();
    }

    public async Task<InsurancePolicyAR> GetByAggregateRootId(Guid id)
    {
        _currentDoc = await SingleAsync(m => m.Payload != null && m.Payload.TechnicalId == id);

        if (_currentDoc?.Payload == null)
            throw new InvalidOperationException($"InsurancePolicy with id {id} not found.");

        return _factory.CreateInstance(_currentDoc.Payload);
    }

    public async Task SaveAggregate(InsurancePolicyAR aggregate)
    {
        if (_currentDoc == null)
            await InsertAggregate(aggregate);
        else
            await ReplaceAsync(_currentDoc, aggregate);
    }

    public async Task SaveAggregate(InsurancePolicyAR aggregate, IDbSession session)
    {
        if (_currentDoc == null)
            await InsertAggregate(aggregate, session);
        else
            await ReplaceAsync(_currentDoc, aggregate, session);
    }

    public async Task InsertAggregate(InsurancePolicyAR aggregate)
    {
        await InsertAsync(aggregate);
    }

    public async Task InsertAggregate(InsurancePolicyAR aggregate, IDbSession session)
    {
        await InsertAsync(aggregate, session);
    }
}
