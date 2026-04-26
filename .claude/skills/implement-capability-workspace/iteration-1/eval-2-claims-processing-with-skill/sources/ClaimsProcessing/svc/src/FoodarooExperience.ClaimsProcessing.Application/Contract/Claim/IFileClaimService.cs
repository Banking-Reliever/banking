using FoodarooExperience.ClaimsProcessing.Contracts.Commands;

namespace FoodarooExperience.ClaimsProcessing.Application.Contract.Claim;

public interface IFileClaimService
{
    Task<Guid> FileAsync(FileClaimCommand command);
}
