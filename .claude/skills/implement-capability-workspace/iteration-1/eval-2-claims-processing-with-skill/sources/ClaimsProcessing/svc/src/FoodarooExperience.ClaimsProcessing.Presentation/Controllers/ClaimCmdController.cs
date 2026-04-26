using Microsoft.AspNetCore.Mvc;
using Foodaroo.Component.Logging;
using FoodarooExperience.ClaimsProcessing.Application.Contract.Claim;
using FoodarooExperience.ClaimsProcessing.Contracts.Commands;

namespace FoodarooExperience.ClaimsProcessing.Presentation.Controllers;

[ApiController]
[Route("Claim")]
[Produces("application/json")]
public class ClaimCmdController : ControllerBase
{
    [HttpPost]
    [Route("File")]
    public async Task<IActionResult> File(
        [FromBody] FileClaimCommand cmd,
        [FromServices] IFileClaimService service)
    {
        var id = await service.FileAsync(cmd);
        return Ok(id);
    }
}
