using Foodaroo.Component.DependencyInjection;
using Foodaroo.Component.DB.Repository.Mongo;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.Configuration;
using Foodaroo.Component.BackgroundServices;
using Microsoft.OpenApi.Models;
using FoodarooExperience.ClaimsProcessing.Application.Contract.Claim;
using FoodarooExperience.ClaimsProcessing.Application.Service.Claim;
using FoodarooExperience.ClaimsProcessing.Domain.Model.AR.Claim;
using FoodarooExperience.ClaimsProcessing.Infrastructure.Data.Domain;

var builder = WebApplication.CreateBuilder(args);

builder.Configuration.AddJsonFile("config/cold.json");
builder.Configuration.AddJsonFile("config/hot.json", true);

var envSettings = builder.Configuration.Get<EnvironmentSettings>();

if (envSettings?.Namespace == "Local")
    builder.WebHost.UseUrls("http://localhost:22618");
else
    builder.WebHost.UseUrls("http://*:8080");

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddComponentCorrelation();
builder.Services.AddHttpCorrelationPropagation();
builder.Services.AddComponentBus();
builder.Services.AddMongoLocker();
builder.Services.AddMessagePublishing();
builder.Services.AddComponentMongoRepositories();
builder.Services.AddComponentLogging();
builder.Services.AddComponentConfiguration();

builder.Services.AddHostedService<HostedMessagePublisherService>();

builder.Services.AddMongoAggregateRepository<IRepositoryClaim, ClaimMongoRepository, ClaimAR, ClaimDto>();
builder.Services.AddSingleton<ISessionFactory, MongoSessionFactory>();

builder.Services.AddTransient<IClaimFactory, ClaimFactory>();
builder.Services.AddTransient<IFileClaimService, FileClaimService>();
builder.Services.AddTransient<IRepositoryClaim, ClaimMongoRepository>();

var app = builder.Build();

if (envSettings?.Namespace != "Prod")
{
    app.UseSwagger(c =>
    {
        c.PreSerializeFilters.Add((swaggerDoc, httpRequest) =>
        {
            if (!httpRequest.Headers.ContainsKey("X-Forwarded-Host")) return;
            var basePath = "claims-processing";
            var serverUrl = $"{httpRequest.Scheme}://{httpRequest.Headers["X-Forwarded-Host"]}/{basePath}";
            swaggerDoc.Servers = new List<OpenApiServer> { new OpenApiServer { Url = serverUrl } };
        });
    });
    app.UseSwaggerUI();
}

app.UseHttpCorrelationPropagation();
app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
