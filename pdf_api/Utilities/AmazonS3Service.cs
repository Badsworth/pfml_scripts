using System;
using System.IO;
using System.Threading.Tasks;
using System.Net;
using System.Reflection;
using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
using Amazon;
using Amazon.S3;
using Amazon.S3.Model;
using Amazon.S3.Util;

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

            return true;
        }

        public async Task<bool> CreateFileAsync(string fileName, MemoryStream stream)
        {
            var request = new PutObjectRequest
            {
                BucketName = _amazonS3Setting.BucketName,
                Key = $"{_amazonS3Setting.Key}/{fileName}",
                InputStream = stream,
                ContentType = "application/pdf"
            };

            await CreateObjectAsync(request);

            return true;
        }

        public async Task<Stream> GetFileAsync(string fileName)
        {
            using (IAmazonS3 client = new AmazonS3Client(_amazonS3Setting.AccessKey, _amazonS3Setting.SecretAccessKey, RegionEndpoint.USEast1))
            {
                bool bucketExists = await AmazonS3Util.DoesS3BucketExistV2Async(client, _amazonS3Setting.BucketName);

                if (!bucketExists)
                    throw new Exception($"Amazon S3 bucket with name '{_amazonS3Setting.BucketName}' does not exists");

                Stream response = null;

                try
                {
                    using (var stream = await client.GetObjectStreamAsync(_amazonS3Setting.BucketName,
                                                                     $"{_amazonS3Setting.Key}/{fileName}",
                                                                     null, new System.Threading.CancellationToken()))
                    {
                        response = stream;
                    }
                }
                catch (Exception ex)
                {
                    var logMessage = $"Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}";
                    throw;
                }

                return response;
            }
        }

        public async Task<IList<Stream>> GetFilesAsync(string folderName)
        {
            using (IAmazonS3 client = new AmazonS3Client(_amazonS3Setting.AccessKey, _amazonS3Setting.SecretAccessKey, RegionEndpoint.USEast1))
            {
                bool bucketExists = await AmazonS3Util.DoesS3BucketExistV2Async(client, _amazonS3Setting.BucketName);

                if (!bucketExists)
                    throw new Exception($"Amazon S3 bucket with name '{_amazonS3Setting.BucketName}' does not exists");

                List<Stream> files = new List<Stream>();

                try
                {
                    var request = new ListObjectsV2Request
                    {
                        BucketName = _amazonS3Setting.BucketName,
                        Prefix = $"{_amazonS3Setting.Key}/{folderName}",
                        Delimiter = "/"
                    };

                    var objects = await client.ListObjectsV2Async(request, new System.Threading.CancellationToken());

                    foreach (var s3Object in objects.S3Objects)
                    {
                        var file = await client.GetObjectAsync(new GetObjectRequest { BucketName = s3Object.BucketName, Key = s3Object.Key }, new System.Threading.CancellationToken());
                        files.Add(file.ResponseStream);
                    }
                }
                catch (Exception ex)
                {
                    var logMessage = $"Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}";
                    throw;
                }

                return files;
            }
        }

        private async Task CreateObjectAsync(PutObjectRequest request)
        {
            using (IAmazonS3 client = new AmazonS3Client(_amazonS3Setting.AccessKey, _amazonS3Setting.SecretAccessKey, RegionEndpoint.USEast1))
            {
                bool bucketExists = await AmazonS3Util.DoesS3BucketExistV2Async(client, _amazonS3Setting.BucketName);

                if (!bucketExists)
                    throw new Exception($"Amazon S3 bucket with name '{_amazonS3Setting.BucketName}' does not exists");
                    
                try
                {
                    await client.PutObjectAsync(request);
                }
                catch (Exception ex)
                {
                    var logMessage = $"Amazon S3 Service Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}";
                    throw;
                }
            }
        }
    }
}