using Foodaroo.Component.DB.Repository.Base;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.DB.Repository.Mongo;
using Foodaroo.Component.Configuration;
using Foodaroo.Component.Logging;
using Foodaroo.Component.Messaging;
using Foodaroo.Component.Correlation;
using FoodarooExperience.ClaimsProcessing.Domain.Model.AR.Claim;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure.Data.Domain;

public interface IRepositoryClaim
{
    Task<ClaimAR> GetByAggregateRootId(Guid id);
    Task SaveAggregate(ClaimAR aggregate);
    Task SaveAggregate(ClaimAR aggregate, IDbSession session);
    Task InsertAggregate(ClaimAR aggregate);
}

public class ClaimMongoRepository
    : MongoAggregateRepositoryBase<ClaimAR, ClaimDto>, IRepositoryClaim
{
    private readonly IClaimFactory _factory;
    private AggregateDocument<ClaimDto>? _currentDoc;

    public ClaimMongoRepository(
        ITransactionHandler tranHandler,
        IMongoHandle<AggregateDocument<ClaimDto>> mongoHandle,
        IMongoHandle<DbMessage> mongoHandleEvt,
        ILogFoodaroo logger,
        ICorrelationContextAccessor correlation,
        DBSerializationOptions serializationOptions,
        EnvironmentSettings environment)
        : base(tranHandler, mongoHandle, mongoHandleEvt, logger, correlation, serializationOptions, environment)
    {
        _factory = new ClaimFactory();
    }

    public async Task<ClaimAR> GetByAggregateRootId(Guid id)
    {
        _currentDoc = await SingleAsync(m => m.Payload != null && m.Payload.TechnicalId == id);
        if (_currentDoc?.Payload == null)
            throw new InvalidOperationException($"Aggregate with id {id} not found");
        return _factory.CreateInstance(_currentDoc.Payload);
    }

    public async Task SaveAggregate(ClaimAR aggregate)
    {
        if (_currentDoc == null)
            await InsertAsync(aggregate);
        else
            await ReplaceAsync(_currentDoc, aggregate);
    }

    public async Task SaveAggregate(ClaimAR aggregate, IDbSession session)
    {
        if (_currentDoc == null)
            await InsertAsync(aggregate, session);
        else
            await ReplaceAsync(_currentDoc, aggregate, session);
    }

    public async Task InsertAggregate(ClaimAR aggregate)
        => await InsertAsync(aggregate);
}
