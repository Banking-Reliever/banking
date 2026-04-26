using Microsoft.AspNetCore.Mvc;
using Naive.PolicyManagement.Infrastructure.Data.Domain;

namespace Naive.PolicyManagement.Presentation.Controllers;

[ApiController]
[Route("InsurancePolicy")]
[Produces("application/json")]
public class InsurancePolicyReadController : ControllerBase
{
    [HttpGet]
    [Route("{id}")]
    public async Task<IActionResult> GetById(
        Guid id,
        [FromServices] IRepositoryInsurancePolicy repository)
    {
        var aggregate = await repository.GetByAggregateRootId(id);
        return Ok(aggregate);
    }
}
