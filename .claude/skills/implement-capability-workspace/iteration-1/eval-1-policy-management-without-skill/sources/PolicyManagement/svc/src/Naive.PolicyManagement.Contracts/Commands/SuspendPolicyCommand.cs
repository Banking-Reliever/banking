using System;

namespace Naive.PolicyManagement.Contracts.Commands;

/// <summary>
/// Command to suspend an active insurance policy.
/// </summary>
public class SuspendPolicyCommand
{
    /// <summary>
    /// Reason for the suspension.
    /// </summary>
    public string Reason { get; set; } = string.Empty;
}
