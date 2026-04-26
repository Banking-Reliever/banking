using FoodarooExperience.ClaimsProcessing.Application.Claims.Commands.FileClaim;
using FoodarooExperience.ClaimsProcessing.Application.Claims.Queries.GetClaim;
using FoodarooExperience.ClaimsProcessing.Contracts.Claims.Requests;
using FoodarooExperience.ClaimsProcessing.Contracts.Claims.Responses;
using MediatR;

namespace FoodarooExperience.ClaimsProcessing.Presentation.Endpoints;

public static class ClaimsEndpoints
{
    public static IEndpointRouteBuilder MapClaimsEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/claims")
            .WithTags("Claims")
            .WithOpenApi();

        group.MapPost("/", FileClaim)
            .WithName("FileClaim")
            .WithSummary("File a new claim")
            .Produces<FileClaimResponse>(StatusCodes.Status201Created)
            .ProducesValidationProblem()
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        group.MapGet("/{claimId:guid}", GetClaim)
            .WithName("GetClaim")
            .WithSummary("Get a claim by ID")
            .Produces<ClaimResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status404NotFound)
            .ProducesProblem(StatusCodes.Status500InternalServerError);

        return app;
    }

    private static async Task<IResult> FileClaim(
        FileClaimRequest request,
        ISender mediator,
        CancellationToken cancellationToken)
    {
        var command = new FileClaimCommand(
            ClaimantId: request.ClaimantId,
            Description: request.Description,
            Amount: request.Amount,
            Currency: request.Currency);

        var result = await mediator.Send(command, cancellationToken);

        var response = new FileClaimResponse(
            ClaimId: result.ClaimId,
            Status: result.Status,
            FiledAt: result.FiledAt);

        return Results.Created($"/api/claims/{result.ClaimId}", response);
    }

    private static async Task<IResult> GetClaim(
        Guid claimId,
        ISender mediator,
        CancellationToken cancellationToken)
    {
        var query = new GetClaimQuery(claimId);
        var claimDto = await mediator.Send(query, cancellationToken);

        if (claimDto is null)
            return Results.NotFound();

        var response = new ClaimResponse(
            ClaimId: claimDto.ClaimId,
            ClaimantId: claimDto.ClaimantId,
            Description: claimDto.Description,
            Amount: claimDto.Amount,
            Currency: claimDto.Currency,
            Status: claimDto.Status,
            FiledAt: claimDto.FiledAt,
            LastModifiedAt: claimDto.LastModifiedAt);

        return Results.Ok(response);
    }
}
