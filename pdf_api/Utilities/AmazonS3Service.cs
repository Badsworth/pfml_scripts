using System;
using System.IO;
using System.Threading.Tasks;
using System.Reflection;
using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
using Amazon.Runtime.CredentialManagement;
using Amazon.S3;
using Amazon.S3.Model;
using Amazon.S3.Util;
using Amazon.Runtime;

namespace PfmlPdfApi.Utilities
{
    public interface IAmazonS3Service
    {
        /// <summary>
        /// Creates a folder
        /// </summary>
        /// <param name="folderName">The folder name</param>
        /// <returns></returns>
        Task<bool> CreateFolderAsync(string folderName);

        /// <summary>
        /// Creates a file
        /// </summary>
        /// <param name="fileName">The file name</param>
        /// <param name="stream">The stream object</param>
        /// <returns></returns>
        Task<bool> CreateFileAsync(string fileName, MemoryStream stream);

        /// <summary>
        /// Gets a file
        /// </summary>
        /// <param name="fileName">The file name</param>
        /// <returns></returns>
        Task<Stream> GetFileAsync(string fileName);

        /// <summary>
        /// Get files by folder
        /// </summary>
        /// <param name="folderName">The folder name</param>
        /// <returns></returns>
        Task<IList<Stream>> GetFilesAsync(string folderName);
    }

    public class AmazonS3Service : IAmazonS3Service
    {
        private readonly AmazonS3Setting _amazonS3Setting;

        public AmazonS3Service(IConfiguration configuration)
        {
            _amazonS3Setting = configuration.GetSection("AmazonS3").Get<AmazonS3Setting>();
        }

        public async Task<bool> CreateFolderAsync(string folderName)
        {
            var request = new PutObjectRequest()
            {
                BucketName = _amazonS3Setting.BucketName,
                Key = $"{_amazonS3Setting.Key}/{folderName}/",
                ContentBody = $"{_amazonS3Setting.Key}/{folderName}/"
            };

            await CreateObjectAsync(request);

            Console.WriteLine($"Amazon S3 Service - {folderName} was successfully created.");

            return true;
        }

        public async Task<bool> CreateFileAsync(string fileName, MemoryStream stream)
        {
            var mStream = new MemoryStream(stream.ToArray());
            mStream.Seek(0, SeekOrigin.Begin);

            var request = new PutObjectRequest
            {
                BucketName = _amazonS3Setting.BucketName,
                Key = $"{_amazonS3Setting.Key}/{fileName}",
                InputStream = mStream,
                ContentType = "application/pdf"
            };

            await CreateObjectAsync(request);

            Console.WriteLine($"Amazon S3 Service - {fileName} was successfully created.");

            return true;
        }

        public async Task<Stream> GetFileAsync(string fileName)
        {
            using (IAmazonS3 awsClient = await GetAWSClient())
            {
                Stream response = null;

                try
                {
                    response = await awsClient.GetObjectStreamAsync(_amazonS3Setting.BucketName,
                                                                     $"{_amazonS3Setting.Key}/{fileName}",
                                                                     null, new System.Threading.CancellationToken());
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}");
                    throw;
                }

                return response;
            }
        }

        public async Task<IList<Stream>> GetFilesAsync(string folderName)
        {
            using (IAmazonS3 awsClient = await GetAWSClient())
            {
                var files = new List<Stream>();

                try
                {
                    var request = new ListObjectsV2Request
                    {
                        BucketName = _amazonS3Setting.BucketName,
                        Prefix = $"{_amazonS3Setting.Key}/{folderName}"
                    };

                    var objects = await awsClient.ListObjectsV2Async(request, new System.Threading.CancellationToken());
                    Console.WriteLine($"Amazon S3 Service - {objects.S3Objects.Count} items were returned from S3 bucket");

                    foreach (var s3Object in objects.S3Objects)
                    {
                        var file = await awsClient.GetObjectAsync(new GetObjectRequest { BucketName = s3Object.BucketName, Key = s3Object.Key }, new System.Threading.CancellationToken());
                        
                        if (s3Object.Key.EndsWith(".pdf"))
                        {
                            files.Add(file.ResponseStream);
                            Console.WriteLine($"Amazon S3 Service - getting key: {s3Object.Key}");
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}");
                    throw;
                }

                return files;
            }
        }

        private async Task CreateObjectAsync(PutObjectRequest request)
        {
            using (IAmazonS3 awsClient = await GetAWSClient())
            {
                try
                {
                    await awsClient.PutObjectAsync(request);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Amazon S3 Service Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}");
                    throw;
                }
            }
        }

        private async Task<IAmazonS3> GetAWSClient()
        {
            var awsClient = new AmazonS3Client();

            bool bucketExists = await AmazonS3Util.DoesS3BucketExistV2Async(awsClient, _amazonS3Setting.BucketName);

            if (!bucketExists)
                throw new Exception($"Amazon S3 bucket with name '{_amazonS3Setting.BucketName}' does not exists");

            return awsClient;
        }
    }
}