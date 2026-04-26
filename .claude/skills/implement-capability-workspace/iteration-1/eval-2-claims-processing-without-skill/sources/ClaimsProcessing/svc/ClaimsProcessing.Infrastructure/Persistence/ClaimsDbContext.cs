using FoodarooExperience.ClaimsProcessing.Domain.Claims;
using Microsoft.EntityFrameworkCore;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure.Persistence;

public sealed class ClaimsDbContext : DbContext
{
    public ClaimsDbContext(DbContextOptions<ClaimsDbContext> options) : base(options)
    {
    }

    public DbSet<Claim> Claims => Set<Claim>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ClaimsDbContext).Assembly);
        base.OnModelCreating(modelBuilder);
    }
}
