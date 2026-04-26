using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

using Maif.PolicyManagement.Contracts.Events;
using LEGO.AsyncAPI.Models;

namespace Maif.PolicyManagement.Presentation.AsyncApi;

public static class PolicyManagementAsyncApiDocumentFactory
{
    public static AsyncApiDocument Create()
    {
        var policyCreatedMessage = CreateMessage(
            messageId: "EVT.RES.MAIF.POLICY.POLICY_CREATED",
            title: "Policy Created",
            description: "Event produced by PolicyManagement when a new insurance policy is created.",
            payloadType: typeof(PolicyCreated));

        var policySuspendedMessage = CreateMessage(
            messageId: "EVT.RES.MAIF.POLICY.POLICY_SUSPENDED",
            title: "Policy Suspended",
            description: "Event produced by PolicyManagement when an active insurance policy is suspended.",
            payloadType: typeof(PolicySuspended));

        return new AsyncApiDocument
        {
            Id = "urn:maif:capability:PolicyManagement",
            DefaultContentType = "application/json",
            Info = new AsyncApiInfo
            {
                Title = "Maif.PolicyManagement Async API",
                Version = "1.0.0",
                Description = "Async API contract for the Maif PolicyManagement capability. " +
                              "This capability publishes PolicyCreated and PolicySuspended events " +
                              "on the maif-policy-management-channel."
            },
            Channels = new Dictionary<string, AsyncApiChannel>
            {
                ["maif-policy-management-channel/PolicyCreated"] = new AsyncApiChannel
                {
                    Description = "Outgoing event: a new insurance policy has been created.",
                    Publish = new AsyncApiOperation
                    {
                        OperationId = "EVT.RES.MAIF.POLICY.POLICY_CREATED",
                        Summary = "Publish Policy Created",
                        Description = "Emitted when CreatePolicy command completes successfully.",
                        Message = new List<AsyncApiMessage> { policyCreatedMessage }
                    }
                },
                ["maif-policy-management-channel/PolicySuspended"] = new AsyncApiChannel
                {
                    Description = "Outgoing event: an active insurance policy has been suspended.",
                    Publish = new AsyncApiOperation
                    {
                        OperationId = "EVT.RES.MAIF.POLICY.POLICY_SUSPENDED",
                        Summary = "Publish Policy Suspended",
                        Description = "Emitted when SuspendPolicy command completes successfully.",
                        Message = new List<AsyncApiMessage> { policySuspendedMessage }
                    }
                }
            }
        };
    }

    private static AsyncApiMessage CreateMessage(string messageId, string title, string description, Type payloadType)
    {
        return new AsyncApiMessage
        {
            MessageId = messageId,
            Name = messageId,
            Title = title,
            Summary = title,
            Description = description,
            ContentType = "application/json",
            Payload = CreateSchema(payloadType)
        };
    }

    private static AsyncApiSchema CreateSchema(Type type)
    {
        if (type == typeof(string))
            return new AsyncApiSchema { Type = SchemaType.String };

        if (type == typeof(Guid))
            return new AsyncApiSchema { Type = SchemaType.String, Format = "uuid" };

        if (type == typeof(DateTime) || type == typeof(DateTimeOffset))
            return new AsyncApiSchema { Type = SchemaType.String, Format = "date-time" };

        if (type == typeof(bool))
            return new AsyncApiSchema { Type = SchemaType.Boolean };

        if (type == typeof(byte) || type == typeof(short) || type == typeof(int) || type == typeof(long))
            return new AsyncApiSchema { Type = SchemaType.Integer };

        if (type == typeof(float) || type == typeof(double) || type == typeof(decimal))
            return new AsyncApiSchema { Type = SchemaType.Number };

        var nullableType = Nullable.GetUnderlyingType(type);
        if (nullableType != null)
            return CreateSchema(nullableType);

        if (type.IsArray)
            return new AsyncApiSchema
            {
                Type = SchemaType.Array,
                Items = CreateSchema(type.GetElementType() ?? typeof(object))
            };

        if (TryGetEnumerableElementType(type, out var itemType))
            return new AsyncApiSchema
            {
                Type = SchemaType.Array,
                Items = CreateSchema(itemType)
            };

        var properties = type
            .GetProperties(BindingFlags.Public | BindingFlags.Instance)
            .Where(p => p.CanRead)
            .ToDictionary(
                p => ToCamelCase(p.Name),
                p => CreateSchema(p.PropertyType));

        return new AsyncApiSchema
        {
            Type = SchemaType.Object,
            Properties = properties
        };
    }

    private static bool TryGetEnumerableElementType(Type type, out Type elementType)
    {
        if (!type.IsGenericType)
        {
            elementType = typeof(object);
            return false;
        }

        var genericType = type.GetGenericTypeDefinition();
        if (genericType == typeof(IEnumerable<>) || genericType == typeof(List<>))
        {
            elementType = type.GetGenericArguments()[0];
            return true;
        }

        var enumerableInterface = type
            .GetInterfaces()
            .FirstOrDefault(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IEnumerable<>));

        if (enumerableInterface == null)
        {
            elementType = typeof(object);
            return false;
        }

        elementType = enumerableInterface.GetGenericArguments()[0];
        return true;
    }

    private static string ToCamelCase(string name)
    {
        if (string.IsNullOrEmpty(name) || !char.IsUpper(name[0]))
            return name;

        return char.ToLowerInvariant(name[0]) + name[1..];
    }
}
