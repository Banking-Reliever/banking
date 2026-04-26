namespace FoodarooExperience.ClaimsProcessing.Domain.Model.AR.Claim;

public interface IClaimFactory
{
    ClaimAR CreateInstance(Guid id);
    ClaimAR CreateInstance(ClaimDto payload);
}
