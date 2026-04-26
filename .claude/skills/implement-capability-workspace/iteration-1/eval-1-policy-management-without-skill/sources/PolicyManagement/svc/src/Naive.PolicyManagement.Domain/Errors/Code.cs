namespace Naive.PolicyManagement.Domain.Errors;

public static class Code
{
    public const string PolicyAlreadyExists = "PolicyAlreadyExists";
    public const string PolicyNotActive = "PolicyNotActive";
    public const string PolicyAlreadySuspended = "PolicyAlreadySuspended";
    public const string InvalidEffectiveDate = "InvalidEffectiveDate";
    public const string InvalidPremiumAmount = "InvalidPremiumAmount";
}
