using Microsoft.AspNetCore.Mvc;
using FoodarooExperience.ClaimsProcessing.Infrastructure.Data.Domain;

namespace FoodarooExperience.ClaimsProcessing.Presentation.Controllers;

[ApiController]
[Route("Claim")]
[Produces("application/json")]
public class ClaimReadController : ControllerBase
{
    [HttpGet]
    [Route("{id}")]
    public async Task<IActionResult> GetById(
        Guid id,
        [FromServices] IRepositoryClaim repository)
    {
        var aggregate = await repository.GetByAggregateRootId(id);
        return Ok(aggregate);
    }
}
