using FoodarooExperience.ClaimsProcessing.Application;
using FoodarooExperience.ClaimsProcessing.Infrastructure;
using FoodarooExperience.ClaimsProcessing.Presentation.Endpoints;
using FoodarooExperience.ClaimsProcessing.Presentation.Middleware;
using Scalar.AspNetCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();

builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);

builder.Services.AddProblemDetails();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference();
}

app.UseHttpsRedirection();
app.UseMiddleware<ExceptionHandlingMiddleware>();

app.MapClaimsEndpoints();

app.Run();

public partial class Program { }
