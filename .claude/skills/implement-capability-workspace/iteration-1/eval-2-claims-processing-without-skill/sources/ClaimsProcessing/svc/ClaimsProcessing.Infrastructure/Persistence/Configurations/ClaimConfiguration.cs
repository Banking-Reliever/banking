using FoodarooExperience.ClaimsProcessing.Domain.Claims;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace FoodarooExperience.ClaimsProcessing.Infrastructure.Persistence.Configurations;

public sealed class ClaimConfiguration : IEntityTypeConfiguration<Claim>
{
    public void Configure(EntityTypeBuilder<Claim> builder)
    {
        builder.ToTable("Claims");

        builder.HasKey(c => c.Id);

        builder.Property(c => c.Id)
            .HasConversion(
                id => id.Value,
                value => ClaimId.From(value))
            .IsRequired();

        builder.Property(c => c.ClaimantId)
            .HasMaxLength(256)
            .IsRequired();

        builder.Property(c => c.Description)
            .HasMaxLength(2000)
            .IsRequired();

        builder.OwnsOne(c => c.Amount, amountBuilder =>
        {
            amountBuilder.Property(a => a.Value)
                .HasColumnName("Amount")
                .HasPrecision(18, 4)
                .IsRequired();

            amountBuilder.Property(a => a.Currency)
                .HasColumnName("Currency")
                .HasMaxLength(3)
                .IsRequired();
        });

        builder.Property(c => c.Status)
            .HasConversion<string>()
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(c => c.FiledAt)
            .IsRequired();

        builder.Property(c => c.LastModifiedAt);

        builder.Ignore(c => c.DomainEvents);

        builder.HasIndex(c => c.ClaimantId);
        builder.HasIndex(c => c.Status);
        builder.HasIndex(c => c.FiledAt);
    }
}
