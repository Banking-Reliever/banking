using FluentValidation;

namespace FoodarooExperience.ClaimsProcessing.Application.Claims.Commands.FileClaim;

public sealed class FileClaimCommandValidator : AbstractValidator<FileClaimCommand>
{
    public FileClaimCommandValidator()
    {
        RuleFor(x => x.ClaimantId)
            .NotEmpty().WithMessage("ClaimantId is required.");

        RuleFor(x => x.Description)
            .NotEmpty().WithMessage("Description is required.")
            .MaximumLength(2000).WithMessage("Description must not exceed 2000 characters.");

        RuleFor(x => x.Amount)
            .GreaterThan(0).WithMessage("Amount must be greater than zero.");

        RuleFor(x => x.Currency)
            .NotEmpty().WithMessage("Currency is required.")
            .Length(3).WithMessage("Currency must be a 3-letter ISO code.")
            .Matches("^[A-Za-z]{3}$").WithMessage("Currency must contain only letters.");
    }
}
