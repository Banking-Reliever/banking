using FoodarooExperience.ClaimsProcessing.Application.Common.Interfaces;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure.Persistence;

public sealed class UnitOfWork : IUnitOfWork
{
    private readonly ClaimsDbContext _dbContext;

    public UnitOfWork(ClaimsDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return await _dbContext.SaveChangesAsync(cancellationToken);
    }
}
