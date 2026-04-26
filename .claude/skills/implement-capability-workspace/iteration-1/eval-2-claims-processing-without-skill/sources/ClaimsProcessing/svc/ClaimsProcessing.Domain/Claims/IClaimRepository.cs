namespace FoodarooExperience.ClaimsProcessing.Domain.Claims;

public interface IClaimRepository
{
    Task<Claim?> GetByIdAsync(ClaimId id, CancellationToken cancellationToken = default);
    Task AddAsync(Claim claim, CancellationToken cancellationToken = default);
    Task UpdateAsync(Claim claim, CancellationToken cancellationToken = default);
    Task<bool> ExistsAsync(ClaimId id, CancellationToken cancellationToken = default);
}
