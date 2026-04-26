FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src

COPY ["ClaimsProcessing.Presentation/ClaimsProcessing.Presentation.csproj", "ClaimsProcessing.Presentation/"]
COPY ["ClaimsProcessing.Application/ClaimsProcessing.Application.csproj", "ClaimsProcessing.Application/"]
COPY ["ClaimsProcessing.Domain/ClaimsProcessing.Domain.csproj", "ClaimsProcessing.Domain/"]
COPY ["ClaimsProcessing.Infrastructure/ClaimsProcessing.Infrastructure.csproj", "ClaimsProcessing.Infrastructure/"]
COPY ["ClaimsProcessing.Contracts/ClaimsProcessing.Contracts.csproj", "ClaimsProcessing.Contracts/"]

RUN dotnet restore "ClaimsProcessing.Presentation/ClaimsProcessing.Presentation.csproj"

COPY . .

WORKDIR "/src/ClaimsProcessing.Presentation"
RUN dotnet build "ClaimsProcessing.Presentation.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "ClaimsProcessing.Presentation.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "ClaimsProcessing.Presentation.dll"]
