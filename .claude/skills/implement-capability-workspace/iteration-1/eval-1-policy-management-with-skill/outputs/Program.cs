using Foodaroo.Component.DependencyInjection;
using Foodaroo.Component.DB.Repository.Mongo;
using Foodaroo.Component.DB.Repository.Base.Interfaces;
using Foodaroo.Component.Configuration;
using Foodaroo.Component.BackgroundServices;
using Microsoft.OpenApi.Models;
using Naive.PolicyManagement.Application.Contract.InsurancePolicy;
using Naive.PolicyManagement.Application.Service.InsurancePolicy;
using Naive.PolicyManagement.Domain.Model.AR.InsurancePolicy;
using Naive.PolicyManagement.Infrastructure.Data.Domain;

var builder = WebApplication.CreateBuilder(args);

builder.Configuration.AddJsonFile("config/cold.json");
builder.Configuration.AddJsonFile("config/hot.json", true);

var envSettings = builder.Configuration.Get<EnvironmentSettings>();

if (envSettings?.Namespace == "Local")
    builder.WebHost.UseUrls("http://localhost:47412");
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

builder.Services.AddMongoAggregateRepository<IRepositoryInsurancePolicy, InsurancePolicyMongoRepository, InsurancePolicyAR, InsurancePolicyDto>();
builder.Services.AddSingleton<ISessionFactory, MongoSessionFactory>();

builder.Services.AddTransient<IInsurancePolicyFactory, InsurancePolicyFactory>();
builder.Services.AddTransient<ICreateInsurancePolicyService, CreateInsurancePolicyService>();
builder.Services.AddTransient<ISuspendInsurancePolicyService, SuspendInsurancePolicyService>();
builder.Services.AddTransient<IRepositoryInsurancePolicy, InsurancePolicyMongoRepository>();

var app = builder.Build();

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

app.Run();
