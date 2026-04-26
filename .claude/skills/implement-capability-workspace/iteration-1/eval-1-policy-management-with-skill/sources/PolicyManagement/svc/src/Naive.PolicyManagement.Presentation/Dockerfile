FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/Naive.PolicyManagement.Presentation/Naive.PolicyManagement.Presentation.csproj", "src/Naive.PolicyManagement.Presentation/"]
COPY ["src/Naive.PolicyManagement.Application/Naive.PolicyManagement.Application.csproj", "src/Naive.PolicyManagement.Application/"]
COPY ["src/Naive.PolicyManagement.Domain/Naive.PolicyManagement.Domain.csproj", "src/Naive.PolicyManagement.Domain/"]
COPY ["src/Naive.PolicyManagement.Infrastructure/Naive.PolicyManagement.Infrastructure.csproj", "src/Naive.PolicyManagement.Infrastructure/"]
COPY ["src/Naive.PolicyManagement.Contracts/Naive.PolicyManagement.Contracts.csproj", "src/Naive.PolicyManagement.Contracts/"]
COPY ["nuget.config", "."]
RUN dotnet restore "src/Naive.PolicyManagement.Presentation/Naive.PolicyManagement.Presentation.csproj"
COPY . .
WORKDIR "/src/src/Naive.PolicyManagement.Presentation"
RUN dotnet build "Naive.PolicyManagement.Presentation.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Naive.PolicyManagement.Presentation.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Naive.PolicyManagement.Presentation.dll"]
