namespace FoodarooExperience.ClaimsProcessing.Domain.Common;

public abstract class Entity<TId>
{
    private readonly List<IDomainEvent> _domainEvents = new();

    protected Entity(TId id)
    {
        Id = id;
    }

    public TId Id { get; private set; }

    public IReadOnlyList<IDomainEvent> DomainEvents => _domainEvents.AsReadOnly();

    protected void RaiseDomainEvent(IDomainEvent domainEvent)
    {
        _domainEvents.Add(domainEvent);
    }

    public void ClearDomainEvents()
    {
        _domainEvents.Clear();
    }
}
