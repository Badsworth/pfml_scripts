using System;
using System.IO;
using System.Threading.Tasks;
using System.Reflection;
using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
using Amazon.S3;
using Amazon.S3.Model;
using Amazon.S3.Util;

namespace PfmlPdfApi.Utilities
{
    public interface IAmazonS3Service
    {
        /// <summary>
        /// Selects the current S3 bucket to use
        /// </summary>
        /// <param name="key">The Key is a bucket's unique identifier</param>
        /// <returns></returns>
        AmazonS3Setting PickBucket(string key);

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
        /// <param name="contentType">The contentType value</param>
        /// <returns></returns>
        Task<bool> CreateFileAsync(string fileName, MemoryStream stream, string contentType = "application/pdf");

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

        /// <summary>
        /// Gets subfolders by folder
        /// </summary>
        /// <param name="folderName">The folder name</param>
        /// <returns>A list of folders</returns>
        Task<IList<string>> GetFoldersAsync(string folderName);
    }

    public class AmazonS3Service : IAmazonS3Service
    {
        private readonly List<AmazonS3Setting> _amazonS3Settings;
        public AmazonS3Setting _amazonS3Setting;

        public AmazonS3Service(IConfiguration configuration)
        {
            _amazonS3Settings = configuration.GetSection("AmazonS3").Get<List<AmazonS3Setting>>();
        }

        public AmazonS3Setting PickBucket(string key) {
            _amazonS3Setting = _amazonS3Settings.Find(bucket => bucket.Key == key);
            return _amazonS3Setting;
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

            Console.WriteLine($"Amazon S3 Service: Prefix {folderName} was successfully created.");

            return true;
        }

        public async Task<bool> CreateFileAsync(string fileName, MemoryStream stream, string contentType = "application/pdf")
        {
            var mStream = new MemoryStream(stream.ToArray());
            mStream.Seek(0, SeekOrigin.Begin);

            var request = new PutObjectRequest
            {
                BucketName = _amazonS3Setting.BucketName,
                Key = $"{_amazonS3Setting.Key}/{fileName}",
                InputStream = mStream,
                ContentType = contentType
            };

            await CreateObjectAsync(request);

            Console.WriteLine($"Amazon S3 Service: Key {fileName} was successfully created.");

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
                        Prefix = folderName
                    };

                    var objects = await awsClient.ListObjectsV2Async(request, new System.Threading.CancellationToken());
                    Console.WriteLine($"Amazon S3 Service: Prefix {folderName} returned {objects.S3Objects.Count} keys.");

                    foreach (var s3Object in objects.S3Objects)
                    {
                        var file = await awsClient.GetObjectAsync(new GetObjectRequest { BucketName = s3Object.BucketName, Key = s3Object.Key }, new System.Threading.CancellationToken());

                        if (s3Object.Key.EndsWith(".pdf"))
                        {
                            files.Add(file.ResponseStream);
                            Console.WriteLine($"Amazon S3 Service: Prefix {folderName} - key {s3Object.Key}.");
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

        public async Task<IList<string>> GetFoldersAsync(string folderName)
        {
            using (IAmazonS3 awsClient = await GetAWSClient())
            {
                var folders = new List<string>();

                try
                {
                    var request = new ListObjectsV2Request
                    {
                        BucketName = _amazonS3Setting.BucketName,
                        Prefix = $"{_amazonS3Setting.Key}/{folderName}/",
                        Delimiter = "/"
                    };

                    var objects = await awsClient.ListObjectsV2Async(request, new System.Threading.CancellationToken());

                    Console.WriteLine($"Amazon S3 Service: {objects.CommonPrefixes.Count} prefixes returned.");

                    foreach (var prefix in objects.CommonPrefixes)
                    {
                        folders.Add(prefix);
                        Console.WriteLine($"Amazon S3 Service: Prefix: {prefix}");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}");
                    throw;
                }

                return folders;
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
                    Console.WriteLine($"Exception Detected! - {GetType().Name}/{MethodBase.GetCurrentMethod().Name}{Environment.NewLine}{ex.Message}");
                    throw;
                }
            }
        }

        private async Task<IAmazonS3> GetAWSClient()
        {
            try
            {
                var awsClient = new AmazonS3Client();
                bool bucketExists = await AmazonS3Util.DoesS3BucketExistV2Async(awsClient, _amazonS3Setting.BucketName);

                if (bucketExists)
                    Console.WriteLine($"Amazon S3 Service: Succesfully connected to S3 Bucket {_amazonS3Setting.BucketName}");
                else
                    throw new Exception($"Amazon S3 Service: Amazon S3 bucket with name '{_amazonS3Setting.BucketName}' does not exist.");

                return awsClient;
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
                throw;
            }
        }
    }
}