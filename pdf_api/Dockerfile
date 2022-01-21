#-----------------------------------------------
# Pfml Pdf Api
#-----------------------------------------------

# Installer image
FROM mcr.microsoft.com/dotnet/aspnet:6.0.1-bullseye-slim-amd64 as base

ENV ASPNETCORE_URLS=http://+:5000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        git \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install .NET SDK
RUN curl -fSL --output dotnet.tar.gz https://dotnetcli.azureedge.net/dotnet/Sdk/6.0.101/dotnet-sdk-6.0.101-linux-x64.tar.gz \
    && dotnet_sha512='ca21345400bcaceadad6327345f5364e858059cfcbc1759f05d7df7701fec26f1ead297b6928afa01e46db6f84e50770c673146a10b9ff71e4c7f7bc76fbf709' \
    && echo "$dotnet_sha512  dotnet.tar.gz" | sha512sum -c - \
    && mkdir -p /usr/share/dotnet \
    && tar -C /usr/share/dotnet -oxzf dotnet.tar.gz ./packs ./sdk ./sdk-manifests ./templates ./LICENSE.txt ./ThirdPartyNotices.txt \
    && rm dotnet.tar.gz \
    # Trigger first run experience by running arbitrary cmd
    && dotnet help

WORKDIR /app
EXPOSE 5000

# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

FROM base AS publish
WORKDIR /src
COPY ["./PfmlPdfApi.csproj", "./"]
RUN dotnet restore "./PfmlPdfApi.csproj"
COPY . .
WORKDIR "/src/."
RUN dotnet publish "PfmlPdfApi.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app/pdf_api
COPY --from=publish /app/publish .
COPY ./Assets ./Assets
ENTRYPOINT ["dotnet", "PfmlPdfApi.dll"]