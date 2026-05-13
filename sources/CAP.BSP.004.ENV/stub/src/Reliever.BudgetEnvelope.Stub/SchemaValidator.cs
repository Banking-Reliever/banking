using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using NJsonSchema;

namespace Reliever.BudgetEnvelope.Stub;

/// <summary>
/// Loads the runtime JSON Schema (Draft 2020-12) at startup and validates
/// every outgoing payload BEFORE it reaches the bus. Fail-fast: an invalid
/// payload is never published — invariant required by ADR-TECH-STRAT-001
/// (the bus contract is design-time-governed and runtime-enforced by the
/// producer).
/// </summary>
public sealed class SchemaValidator
{
    private readonly JsonSchema _schema;

    public SchemaValidator(JsonSchema schema)
    {
        _schema = schema ?? throw new ArgumentNullException(nameof(schema));
    }

    public static SchemaValidator FromFile(string path)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            throw new ArgumentException("Schema path must be set.", nameof(path));
        }

        var resolved = ResolvePath(path);
        if (!File.Exists(resolved))
        {
            throw new FileNotFoundException(
                $"RVT runtime JSON Schema not found at '{resolved}'. " +
                "The stub cannot start without it (ADR-TECH-STRAT-001 Rule 6 — design-time governance).",
                resolved);
        }

        var json = File.ReadAllText(resolved);
        // NJsonSchema understands Draft 2020-12 schemas via FromJsonAsync; the
        // worker startup is async-friendly so we synchronously block here only
        // because schema load is one-shot.
        var schema = JsonSchema.FromJsonAsync(json).GetAwaiter().GetResult();
        return new SchemaValidator(schema);
    }

    /// <summary>
    /// Returns the list of validation error messages (empty list = valid payload).
    /// </summary>
    public IReadOnlyList<string> Validate(JsonObject payload)
    {
        if (payload is null) throw new ArgumentNullException(nameof(payload));
        var errors = _schema.Validate(payload.ToJsonString());
        return errors.Select(e => $"{e.Path}: {e.Kind}").ToList();
    }

    /// <summary>
    /// Throws <see cref="InvalidPayloadException"/> if the payload does not
    /// validate against the runtime schema.
    /// </summary>
    public void EnsureValid(JsonObject payload)
    {
        var errors = Validate(payload);
        if (errors.Count > 0)
        {
            throw new InvalidPayloadException(errors);
        }
    }

    private static string ResolvePath(string path)
    {
        if (Path.IsPathRooted(path)) return path;
        var baseDir = AppContext.BaseDirectory;
        return Path.GetFullPath(Path.Combine(baseDir, path));
    }
}

public sealed class InvalidPayloadException : Exception
{
    public IReadOnlyList<string> Errors { get; }

    public InvalidPayloadException(IReadOnlyList<string> errors)
        : base($"Generated payload failed runtime schema validation: {string.Join("; ", errors)}")
    {
        Errors = errors;
    }
}
