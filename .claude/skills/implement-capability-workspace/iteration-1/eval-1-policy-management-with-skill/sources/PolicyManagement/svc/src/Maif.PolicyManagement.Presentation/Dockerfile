FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/Maif.PolicyManagement.Presentation/Maif.PolicyManagement.Presentation.csproj", "src/Maif.PolicyManagement.Presentation/"]
COPY ["src/Maif.PolicyManagement.Application/Maif.PolicyManagement.Application.csproj", "src/Maif.PolicyManagement.Application/"]
COPY ["src/Maif.PolicyManagement.Domain/Maif.PolicyManagement.Domain.csproj", "src/Maif.PolicyManagement.Domain/"]
COPY ["src/Maif.PolicyManagement.Infrastructure/Maif.PolicyManagement.Infrastructure.csproj", "src/Maif.PolicyManagement.Infrastructure/"]
COPY ["src/Maif.PolicyManagement.Contracts/Maif.PolicyManagement.Contracts.csproj", "src/Maif.PolicyManagement.Contracts/"]
COPY ["nuget.config", "."]
RUN dotnet restore "src/Maif.PolicyManagement.Presentation/Maif.PolicyManagement.Presentation.csproj"
COPY . .
WORKDIR "/src/src/Maif.PolicyManagement.Presentation"
RUN dotnet build "Maif.PolicyManagement.Presentation.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Maif.PolicyManagement.Presentation.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Maif.PolicyManagement.Presentation.dll"]
