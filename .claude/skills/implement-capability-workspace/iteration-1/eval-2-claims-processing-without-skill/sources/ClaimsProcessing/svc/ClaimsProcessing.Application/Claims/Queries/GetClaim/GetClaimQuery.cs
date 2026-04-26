using MediatR;

namespace FoodarooExperience.ClaimsProcessing.Application.Claims.Queries.GetClaim;

public sealed record GetClaimQuery(Guid ClaimId) : IRequest<ClaimDto?>;
