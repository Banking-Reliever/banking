using Naive.PolicyManagement.Application.Contract.InsurancePolicy;
using Naive.PolicyManagement.Application.Service.InsurancePolicy;
using Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy.Factory;
using Naive.PolicyManagement.Contracts.Events;
using Naive.PolicyManagement.Infrastructure.Data.Domain;
using Naive.PolicyManagement.Presentation.AsyncApi;

using Foodaroo.Component.DependencyInjection;
using Foodaroo.Component.DB.Repository.Mongo;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.Configuration;
using Foodaroo.Component.BackgroundServices;

using Microsoft.OpenApi.Models;
using LEGO.AsyncAPI;
using LEGO.AsyncAPI.Models;

var builder = WebApplication.CreateBuilder(args);

// Add configuration
builder.Configuration.AddJsonFile("config/cold.json");
builder.Configuration.AddJsonFile("config/hot.json", optional: true);

var envSettings = builder.Configuration.Get<EnvironmentSettings>();

if (envSettings?.Namespace == "Local")
    builder.WebHost.UseUrls("http://localhost:5000");
else
    builder.WebHost.UseUrls("http://*:8080");

// ASP.NET Core services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Platform components
builder.Services.AddComponentCorrelation();
builder.Services.AddHttpCorrelationPropagation();
builder.Services.AddComponentBus();
builder.Services.AddMongoLocker();
builder.Services.AddMessagePublishing();
builder.Services.AddComponentMongoRepositories();
builder.Services.AddComponentLogging();
builder.Services.AddComponentConfiguration();

builder.Services.AddHostedService<HostedMessagePublisherService>();

// Aggregate repository
builder.Services.AddMongoAggregateRepository<
    IRepositoryInsurancePolicy,
    InsurancePolicyMongoRepository,
    InsurancePolicyAR,
    InsurancePolicyDto>();

builder.Services.AddSingleton<ISessionFactory, MongoSessionFactory>();

// Domain factory
builder.Services.AddTransient<IInsurancePolicyFactory, InsurancePolicyFactory>();

// Application services
builder.Services.AddTransient<ICreatePolicyService, CreatePolicyService>();
builder.Services.AddTransient<ISuspendPolicyService, SuspendPolicyService>();

// Secondary repository binding (used by services directly)
builder.Services.AddTransient<IRepositoryInsurancePolicy, InsurancePolicyMongoRepository>();

var app = builder.Build();

// HTTP pipeline
if (envSettings?.Namespace != "Prod")
{
    app.UseSwagger(c =>
    {
        c.PreSerializeFilters.Add((swaggerDoc, httpRequest) =>
        {
            if (!httpRequest.Headers.ContainsKey("X-Forwarded-Host")) return;
            var basePath = "policy-management";
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

app.MapGet("/asyncapi.yaml", () =>
{
    var asyncApi = PolicyManagementAsyncApiDocumentFactory.Create();
    var payload = asyncApi.SerializeAsYaml(AsyncApiVersion.AsyncApi2_0);
    return Results.Text(payload, "application/yaml");
});

app.MapGet("/asyncapi.json", () =>
{
    var asyncApi = PolicyManagementAsyncApiDocumentFactory.Create();
    var payload = asyncApi.SerializeAsJson(AsyncApiVersion.AsyncApi2_0);
    return Results.Text(payload, "application/json");
});

app.Run();
