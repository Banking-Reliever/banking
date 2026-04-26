using FluentValidation;
using FoodarooExperience.ClaimsProcessing.Domain.Common;
using Microsoft.AspNetCore.Mvc;
using System.Text.Json;

namespace FoodarooExperience.ClaimsProcessing.Presentation.Middleware;

public sealed class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(RequestDelegate next, ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (ValidationException ex)
        {
            await HandleValidationExceptionAsync(context, ex);
        }
        catch (DomainException ex)
        {
            await HandleDomainExceptionAsync(context, ex);
        }
        catch (Exception ex)
        {
            await HandleUnhandledExceptionAsync(context, ex);
        }
    }

    private static async Task HandleValidationExceptionAsync(HttpContext context, ValidationException ex)
    {
        context.Response.StatusCode = StatusCodes.Status422UnprocessableEntity;
        context.Response.ContentType = "application/problem+json";

        var problem = new ValidationProblemDetails
        {
            Title = "Validation error",
            Status = StatusCodes.Status422UnprocessableEntity,
            Detail = "One or more validation errors occurred.",
            Instance = context.Request.Path
        };

        foreach (var error in ex.Errors)
        {
            if (!problem.Errors.ContainsKey(error.PropertyName))
                problem.Errors[error.PropertyName] = [];

            problem.Errors[error.PropertyName] =
                [.. problem.Errors[error.PropertyName], error.ErrorMessage];
        }

        await context.Response.WriteAsync(JsonSerializer.Serialize(problem));
    }

    private static async Task HandleDomainExceptionAsync(HttpContext context, DomainException ex)
    {
        context.Response.StatusCode = StatusCodes.Status400BadRequest;
        context.Response.ContentType = "application/problem+json";

        var problem = new ProblemDetails
        {
            Title = "Domain error",
            Status = StatusCodes.Status400BadRequest,
            Detail = ex.Message,
            Instance = context.Request.Path
        };

        await context.Response.WriteAsync(JsonSerializer.Serialize(problem));
    }

    private async Task HandleUnhandledExceptionAsync(HttpContext context, Exception ex)
    {
        _logger.LogError(ex, "Unhandled exception occurred");

        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        context.Response.ContentType = "application/problem+json";

        var problem = new ProblemDetails
        {
            Title = "Internal server error",
            Status = StatusCodes.Status500InternalServerError,
            Detail = "An unexpected error occurred.",
            Instance = context.Request.Path
        };

        await context.Response.WriteAsync(JsonSerializer.Serialize(problem));
    }
}
