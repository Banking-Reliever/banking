namespace Naive.PolicyManagement.Presentation;

public class AppSettings
{
    public string Namespace { get; set; } = string.Empty;
    public string ServiceBusConnectionString { get; set; } = string.Empty;
    public string MongoDbConnection { get; set; } = string.Empty;
    public string RabbitMQConnection { get; set; } = string.Empty;
    public int Port { get; set; }
}
