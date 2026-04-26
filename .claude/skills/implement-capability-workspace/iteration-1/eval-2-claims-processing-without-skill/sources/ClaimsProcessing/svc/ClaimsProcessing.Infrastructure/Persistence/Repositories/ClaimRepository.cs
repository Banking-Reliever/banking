using FoodarooExperience.ClaimsProcessing.Domain.Claims;
using Microsoft.EntityFrameworkCore;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure.Persistence.Repositories;

public sealed class ClaimRepository : IClaimRepository
{
    private readonly ClaimsDbContext _dbContext;

    public ClaimRepository(ClaimsDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task<Claim?> GetByIdAsync(ClaimId id, CancellationToken cancellationToken = default)
    {
        return await _dbContext.Claims
            .FirstOrDefaultAsync(c => c.Id == id, cancellationToken);
    }

    public async Task AddAsync(Claim claim, CancellationToken cancellationToken = default)
    {
        await _dbContext.Claims.AddAsync(claim, cancellationToken);
    }

    public Task UpdateAsync(Claim claim, CancellationToken cancellationToken = default)
    {
        _dbContext.Claims.Update(claim);
        return Task.CompletedTask;
    }

    public async Task<bool> ExistsAsync(ClaimId id, CancellationToken cancellationToken = default)
    {
        return await _dbContext.Claims
            .AnyAsync(c => c.Id == id, cancellationToken);
    }
}
