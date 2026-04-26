using FoodarooExperience.ClaimsProcessing.Application.Common.Interfaces;
using FoodarooExperience.ClaimsProcessing.Domain.Claims;
using FoodarooExperience.ClaimsProcessing.Infrastructure.Messaging;
using FoodarooExperience.ClaimsProcessing.Infrastructure.Persistence;
using FoodarooExperience.ClaimsProcessing.Infrastructure.Persistence.Repositories;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<ClaimsDbContext>(options =>
        {
            var connectionString = configuration.GetConnectionString("ClaimsDb")
                ?? throw new InvalidOperationException("Connection string 'ClaimsDb' is not configured.");

            options.UseSqlServer(connectionString, sqlOptions =>
            {
                sqlOptions.EnableRetryOnFailure(
                    maxRetryCount: 5,
                    maxRetryDelay: TimeSpan.FromSeconds(30),
                    errorNumbersToAdd: null);
            });
        });

        services.AddScoped<IClaimRepository, ClaimRepository>();
        services.AddScoped<IUnitOfWork, UnitOfWork>();
        services.AddScoped<IEventPublisher, EventPublisher>();
        services.AddSingleton<IMessageBroker, InMemoryMessageBroker>();

        return services;
    }
}
