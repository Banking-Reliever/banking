namespace FoodarooExperience.ClaimsProcessing.Domain.Model.AR.Claim;

public class ClaimFactory : IClaimFactory
{
    public ClaimAR CreateInstance(Guid id)
        => new ClaimAR(id);

    public ClaimAR CreateInstance(ClaimDto payload)
        => new ClaimAR(payload.TechnicalId, payload.State);
}
