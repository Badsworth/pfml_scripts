#-----------------------------------------------
# Pfml Pdf Api
#-----------------------------------------------
FROM mcr.microsoft.com/dotnet/aspnet:5.0-focal AS base
WORKDIR /app
EXPOSE 5001

ENV ASPNETCORE_URLS=https://+:5001

# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

FROM mcr.microsoft.com/dotnet/sdk:5.0-focal AS build
WORKDIR /src
COPY ["./PfmlPdfApi.csproj", "./"]
RUN dotnet restore "./PfmlPdfApi.csproj"
COPY . .
WORKDIR "/src/."
RUN dotnet build "PfmlPdfApi.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "PfmlPdfApi.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app/pdf_api
COPY --from=publish /app/publish .
COPY ./Assets ./Assets
ENTRYPOINT ["dotnet", "PfmlPdfApi.dll"]