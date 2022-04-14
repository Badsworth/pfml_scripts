using iText.Html2pdf;
using iText.Kernel.Pdf;
using iText.Kernel.Utils;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using PfmlPdfApi.Models;
using PfmlPdfApi.Utilities;
using PfmlPdfApi.Common;
using Microsoft.Extensions.Configuration;

namespace PfmlPdfApi.Services
{
    public interface IPdfDocumentService
    {
        Task<ResponseMessage<CreatedDocumentResponse>> Generate(Document dto);
        Task<ResponseMessage<IList<CreatedDocumentResponse>>> Merge(MergeDocumentsRequest dto);
        void switchToBucket(string key);
    }

    public class PdfDocumentService : IPdfDocumentService
    {
        private readonly IAmazonS3Service _amazonS3Service;
        private AmazonS3Setting bucket;

        public PdfDocumentService(IConfiguration configuration, IAmazonS3Service amazonS3Service)
        {
            _amazonS3Service = amazonS3Service;
            string defaultBucket = configuration.GetValue<string>("AppSettings:DefaultBucket");
            switchToBucket(defaultBucket);
        }

        public void switchToBucket(string key) {
            if (bucket == null || bucket.Key != key) {
                bucket = _amazonS3Service.PickBucket(key);
                Console.WriteLine("Selected new bucket: " + bucket.Key);
            }
        }

        public async Task<ResponseMessage<CreatedDocumentResponse>> Generate(Document dto)
        {
            switchToBucket(dto.Type);
            var response = new ResponseMessage<CreatedDocumentResponse>(null);
            try
            {
                var template = new MemoryStream(await File.ReadAllBytesAsync(dto.Template));
                string document = dto.ReplaceValuesInTemplate(new StreamReader(template).ReadToEnd());
                var stream = new MemoryStream();
                HtmlConverter.ConvertToPdf(document, stream);
                var folderCreated = await _amazonS3Service.CreateFolderAsync(dto.FolderName);
                var fileCreated = await _amazonS3Service.CreateFileAsync(dto.FileName, stream);

                var createdDocumentDto = new CreatedDocumentResponse
                {
                    Name = dto.FileName
                };
                response.Payload = createdDocumentDto;
            }
            catch (Exception ex)
            {
                response.Status = MessageConstants.MsgStatusFailed;
                response.ErrorMessage = ex.Message;
            }
            return response;
        }

        public async Task<ResponseMessage<IList<CreatedDocumentResponse>>> Merge(MergeDocumentsRequest dto)
        {
            switchToBucket(dto.Type);
            var response = new ResponseMessage<IList<CreatedDocumentResponse>>(null);
            var createdDocumentDtoList = new List<CreatedDocumentResponse>();
            string folderName = $"Batch-{dto.BatchId}";
            string formsFolderName = $"{folderName}/Forms";
            string mergedFolderName = $"{folderName}/Merged";
            var folderCreated = await _amazonS3Service.CreateFolderAsync(mergedFolderName);
            var subBatches = await _amazonS3Service.GetFoldersAsync(formsFolderName);
            int conMerge = 1;
            int take = dto.NumOfRecords;

            try
            {
                foreach (var subBatch in subBatches)
                {
                    var files = await _amazonS3Service.GetFilesAsync(subBatch);
                    string fileName = $"{mergedFolderName}/{folderName}.{conMerge}.pdf";
                    var stream = new MemoryStream();
                    var pdfWriter = new PdfWriter(stream);
                    var pdfMergedDocument = new PdfDocument(pdfWriter);
                    var merger = new PdfMerger(pdfMergedDocument);

                    try
                    {
                        foreach (var file in files)
                        {
                            var pdfReader = new PdfReader(file);
                            var pdfDocument = new PdfDocument(pdfReader);
                            merger.Merge(pdfDocument, 1, pdfDocument.GetNumberOfPages());
                        }

                        merger.Close();

                        Console.WriteLine($"Pfml Api: File {fileName} with {files.Count} Pdf(s) were successfully merged.");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine(ex.ToString());
                        response.Status = MessageConstants.MsgStatusFailed;
                        response.ErrorMessage = $"IText Exception detected! - {ex.Message}";
                        throw;
                    }

                    var fileCreated = await _amazonS3Service.CreateFileAsync(fileName, stream);

                    createdDocumentDtoList.Add(new CreatedDocumentResponse
                    {
                        Name = fileName
                    });

                    conMerge++;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.ToString());
                response.Status = MessageConstants.MsgStatusFailed;
                response.ErrorMessage = ex.Message;
            }

            return response;
        }

    }
}