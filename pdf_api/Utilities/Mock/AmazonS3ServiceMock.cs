using System.IO;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Configuration;

namespace PfmlPdfApi.Utilities.Mock
{
    public class AmazonS3ServiceMock : IAmazonS3Service
    {
        private readonly AmazonS3Setting _amazonS3Setting;
        private string BASEFOLDER = @"Assets";
        public AmazonS3ServiceMock(IConfiguration configuration)
        {
            _amazonS3Setting = configuration.GetSection("AmazonS3").Get<AmazonS3Setting>();
        }

        public async Task<bool> CreateFolderAsync(string folderName)
        {
            Directory.CreateDirectory($"{BASEFOLDER}//{_amazonS3Setting.Key}//{folderName}");

            return true;
        }

        public async Task<bool> CreateFileAsync(string fileName, MemoryStream stream)
        {
            var lstream = new MemoryStream(stream.ToArray());
            lstream.Seek(0, SeekOrigin.Begin);

            var fileStream = File.Create($"{BASEFOLDER}//{_amazonS3Setting.Key}//{fileName}");
            lstream.CopyTo(fileStream);
            fileStream.Close();

            return true;
        }

        public async Task<Stream> GetFileAsync(string fileName)
        {
            return File.OpenRead($"{BASEFOLDER}//{_amazonS3Setting.Key}//{fileName}");
        }

        public async Task<IList<Stream>> GetFilesAsync(string folderName)
        {
            List<Stream> streamList = new List<Stream>();
            string[] files = Directory.GetFiles($"{BASEFOLDER}//{_amazonS3Setting.Key}//{folderName}");

            foreach (var file in files)
            {
                streamList.Add(File.OpenRead(file));
            }

            return streamList;
        }

        public async Task<IList<string>> GetFoldersAsync(string folderName)
        {
            string[] files = Directory.GetFiles($"{BASEFOLDER}//{_amazonS3Setting.Key}//{folderName}");

            return files.ToList();
        }
    }
}