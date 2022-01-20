
# Massachusetts PFML Pdf Api Layer
 
# Introduction

This is the PFML Pdf Api Service which contains endpoints to generate and merge 1099-G documents.

# Directory Structure

```
.
├── Assets              Folder which contains the 1099 Template and also to be used as a local file system for local development and testing
│── Controllers         Contains all endpoints for the Api
│── Services            Main code
│── Utilities           
│   └── Mock            Contains a mocking service to test with a local file system when a S3 bucket is not available
├── Dockerfile          Docker build file for project
├── docker-compose.yml  Config file for docker-compose tool, used for local development
```

# Local Development

## Environment Variable

The only environment variable we are using is ASPNETCORE_ENVIRONMENT=Development located in the file docker-compose.yml.
Depending on the value for this environment variable a specific `appsettings.<ASPNETCORE_ENVIRONMENT>.json` file containing other app settings that will be used in runtime.

## Application Settings

Each `appsettings.<ASPNETCORE_ENVIRONMENT>.json` file contains some settings that the AmazonS3Service needs to work properly with a real S3 bucket.

```sh
"AmazonS3": {
    "BucketName": "",
    "Key": "1099"
  },
  "AppSettings": {
    "Template1099": "Template/1099G_FORM.html"
  }
```

## Local File System

To test generation and merging of 1099-G documents locally, follow the next steps:

1. Move to directory `pdf_api`
2. Use `AmazonS3ServiceMock` instead of `AmazonS3Service` in the `Startup.cs` class

```sh
public void ConfigureServices(IServiceCollection services)
{

    services.AddControllers();
    services.AddSwaggerGen(c =>
    {
        c.SwaggerDoc("v1", new OpenApiInfo { Title = "PfmlPdfApi", Version = "v1" });
    });
    services.AddTransient<IPdfDocumentService, PdfDocumentService>();
    services.AddTransient<IAmazonS3Service, AmazonS3ServiceMock>();
    services.AddSingleton(Configuration);
}
```

3. Run a docker command to start the Api

```sh
docker-compose up
```

4. In the browser navigate to http://localhost:5000/api/pdf, a friendly message will be displayed on the page indicating that the Api is up and running.

```sh
Dev - Pfml Pdf Api is running.
```
## Test endpoints

Testing each endpoint can be done from your prefered client app sush as [Postman](https://www.postman.com/downloads/) or [Swagger](http://localhost:5000/swagger/index.html) interface.

1. When a 1099-G document is generated a new pdf file is created and the path file is: `Assets/1099/Batch-<batch_id>/Forms/Sub-batch-<index>/<pfml_1099_id>.pdf`
2. When multiple 1099-G documents are merged a new pdf file is created and the path file is `Assets/1099/Batch-<batch_id>/Merged/Batch-<batch_id>.<index>.pdf`
3. The template used as a base to generate a 1099-G document can be found in this path `Assets/1099/Template/1099G_FORM.HTML`

# Third Parties Packages

## itext library

The [itext](https://itextpdf.com/en/products/itext-7/convert-html-css-to-pdf-pdfhtml) package is used to convert html to pdf files. This package can be installed or updated by running the following command:

```sh
dotnet add package itext7.pdfhtml --version 3.0.5
```

## AWSSDK.S3

The [AWSSDK.S3](https://www.nuget.org/packages/AWSSDK.S3/) package is used to write and read objects from a S3 bucket. This package can be installed or updated by running the following command:

```sh
dotnet add package AWSSDK.S3 --version 3.3.104.39
```

