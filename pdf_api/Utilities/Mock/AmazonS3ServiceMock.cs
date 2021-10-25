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
using PfmlPdfApi.Utilities;

namespace PfmlPdfApi.Utilities.Mock
{
    public class AmazonS3ServiceMock : IAmazonS3Service
    {
        private readonly AmazonS3Setting _amazonS3Setting;
        private string BASEFOLDER = @"C:\Temp\PFML";
        public AmazonS3ServiceMock(IConfiguration configuration)
        {
            _amazonS3Setting = configuration.GetSection("AmazonS3").Get<AmazonS3Setting>();
        }

        public async Task<bool> CreateFolderAsync(string folderName)
        {
            Directory.CreateDirectory($"{BASEFOLDER}\\{folderName}");

            return true;
        }

        public async Task<bool> CreateFileAsync(string fileName, MemoryStream stream)
        {
            var lstream = new MemoryStream(stream.ToArray());
            lstream.Seek(0, SeekOrigin.Begin);
            
            var fileStream = File.Create($"{BASEFOLDER}\\{fileName}");
            lstream.CopyTo(fileStream);
            
            return true;
        }

        public async Task<Stream> GetFileAsync(string fileName)
        {
            return File.OpenRead($"{BASEFOLDER}\\{fileName}");
        }

        public async Task<IList<Stream>> GetFilesAsync(string folderName)
        {
            List<Stream> streamList = new List<Stream>();
            string[] files = Directory.GetFiles($"{BASEFOLDER}\\{folderName}");

            foreach (var file in files)
            {
                streamList.Add(File.OpenRead(file));
            }

            return streamList;
        }
    }
}