using Microsoft.AspNetCore.Mvc;
using Foodaroo.Component.Logging;
using Naive.PolicyManagement.Application.Contract.InsurancePolicy;
using Naive.PolicyManagement.Contracts.Commands;

namespace Naive.PolicyManagement.Presentation.Controllers;

[ApiController]
[Route("InsurancePolicy")]
[Produces("application/json")]
public class InsurancePolicyCmdController : ControllerBase
{
    [HttpPost]
    [Route("Create")]
    public async Task<IActionResult> Create(
        [FromBody] CreateInsurancePolicyCommand cmd,
        [FromServices] ICreateInsurancePolicyService service)
    {
        var id = await service.CreateAsync(cmd);
        return Ok(id);
    }

    [HttpPost]
    [Route("Suspend")]
    public async Task<IActionResult> Suspend(
        [FromBody] SuspendInsurancePolicyCommand cmd,
        [FromServices] ISuspendInsurancePolicyService service)
    {
        await service.SuspendAsync(cmd);
        return Ok();
    }
}
