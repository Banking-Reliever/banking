FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/FoodarooExperience.ClaimsProcessing.Presentation/FoodarooExperience.ClaimsProcessing.Presentation.csproj", "src/FoodarooExperience.ClaimsProcessing.Presentation/"]
COPY ["src/FoodarooExperience.ClaimsProcessing.Application/FoodarooExperience.ClaimsProcessing.Application.csproj", "src/FoodarooExperience.ClaimsProcessing.Application/"]
COPY ["src/FoodarooExperience.ClaimsProcessing.Domain/FoodarooExperience.ClaimsProcessing.Domain.csproj", "src/FoodarooExperience.ClaimsProcessing.Domain/"]
COPY ["src/FoodarooExperience.ClaimsProcessing.Infrastructure/FoodarooExperience.ClaimsProcessing.Infrastructure.csproj", "src/FoodarooExperience.ClaimsProcessing.Infrastructure/"]
COPY ["src/FoodarooExperience.ClaimsProcessing.Contracts/FoodarooExperience.ClaimsProcessing.Contracts.csproj", "src/FoodarooExperience.ClaimsProcessing.Contracts/"]
COPY ["nuget.config", "."]
RUN dotnet restore "src/FoodarooExperience.ClaimsProcessing.Presentation/FoodarooExperience.ClaimsProcessing.Presentation.csproj"
COPY . .
WORKDIR "/src/src/FoodarooExperience.ClaimsProcessing.Presentation"
RUN dotnet build "FoodarooExperience.ClaimsProcessing.Presentation.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "FoodarooExperience.ClaimsProcessing.Presentation.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "FoodarooExperience.ClaimsProcessing.Presentation.dll"]
