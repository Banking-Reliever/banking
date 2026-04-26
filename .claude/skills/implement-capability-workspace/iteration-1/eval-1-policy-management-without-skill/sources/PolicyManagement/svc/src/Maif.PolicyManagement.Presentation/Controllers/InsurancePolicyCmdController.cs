using System;
using System.Threading.Tasks;

using Microsoft.AspNetCore.Mvc;

using Foodaroo.Component.Logging;

using Maif.PolicyManagement.Contracts.Commands;
using Maif.PolicyManagement.Domain.Model.AR.InsurancePolicy.ValueObject;
using Maif.PolicyManagement.Application.Contract.InsurancePolicy;

namespace Maif.PolicyManagement.Presentation.Controllers;

/// <summary>
/// Command controller for the InsurancePolicy aggregate.
/// Exposes the CreatePolicy and SuspendPolicy commands over HTTP.
/// </summary>
[ApiController]
[Route("InsurancePolicy")]
[Produces("application/json")]
public class InsurancePolicyCmdController : ControllerBase
{
    public InsurancePolicyCmdController(ILogFoodaroo logger)
    {
    }

    /// <summary>
    /// Creates a new insurance policy.
    /// Returns the newly assigned policyId (aggregateId).
    /// </summary>
    /// <param name="cmd">Command payload carrying policy details.</param>
    /// <param name="service">Injected application service.</param>
    [HttpPost]
    [Route("CreatePolicy")]
    public async Task<IActionResult> CreatePolicy(
        [FromBody] CreatePolicyCommand cmd,
        [FromServices] ICreatePolicyService service)
    {
        if (cmd == null) return BadRequest();

        var policyId = await service.CreatePolicy(
            cmd.PolicyHolderId,
            cmd.InsuranceType,
            cmd.EffectiveDate,
            cmd.ExpirationDate,
            cmd.PremiumAmount);

        return Ok(policyId);
    }

    /// <summary>
    /// Suspends an existing active insurance policy.
    /// </summary>
    /// <param name="policyId">Identifier of the policy to suspend.</param>
    /// <param name="cmd">Command payload with the suspension reason.</param>
    /// <param name="service">Injected application service.</param>
    [HttpPost]
    [Route("InsurancePolicy/{policyId}/SuspendPolicy")]
    public async Task<IActionResult> SuspendPolicy(
        Guid policyId,
        [FromBody] SuspendPolicyCommand cmd,
        [FromServices] ISuspendPolicyService service)
    {
        if (cmd == null) return BadRequest();

        SuspensionReasonVO? reason = null;
        if (!SuspensionReasonVO.TryParse(cmd.Reason, out reason))
            return BadRequest("Suspension reason is invalid (must be non-empty, max 500 chars).");

        await service.SuspendPolicy(policyId, cmd.Reason);

        return Ok();
    }
}
