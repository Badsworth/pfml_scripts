using iText.Html2pdf;
using iText.Kernel.Pdf;
using iText.Kernel.Utils;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using PfmlPdfApi.Models;
using PfmlPdfApi.Utilities;
using PfmlPdfApi.Common;
using Microsoft.Extensions.Configuration;

namespace PfmlPdfApi.Services
{
    public interface IPdfDocumentService
    {
        Task<ResponseMessage<CreatedDocumentDto>> Generate(DocumentDto dto);
        Task<ResponseMessage<IList<CreatedDocumentDto>>> Merge(MergeDto dto);
    }

    public class PdfDocumentService : IPdfDocumentService
    {
        private readonly IAmazonS3Service _amazonS3Service;
        private readonly string template1099;

        public PdfDocumentService(IConfiguration configuration, IAmazonS3Service amazonS3Service)
        {
            _amazonS3Service = amazonS3Service;
            template1099 = configuration.GetValue<string>("AppSettings:Template1099");
        }

        public async Task<ResponseMessage<CreatedDocumentDto>> Generate(DocumentDto dto)
        {
            var response = new ResponseMessage<CreatedDocumentDto>(null);
            string folderName = $"Batch{dto.BatchId}";
            string fileName = $"{folderName}/{dto.SocialNumber}-{dto.Name}.pdf";

            try
            {
                var template = await _amazonS3Service.GetFileAsync(template1099);
                string document = ReplaceValuesInTemplate(new StreamReader(template).ReadToEnd(), dto);
                var stream = new MemoryStream();
                HtmlConverter.ConvertToPdf(document, stream);
                var folderCreated = await _amazonS3Service.CreateFolderAsync(folderName);
                var fileCreated = await _amazonS3Service.CreateFileAsync(fileName, stream);

                var createdDocumentDto = new CreatedDocumentDto
                {
                    Name = fileName,
                    Content = Convert.ToBase64String(stream.ToArray())
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

        public async Task<ResponseMessage<IList<CreatedDocumentDto>>> Merge(MergeDto dto)
        {
            var response = new ResponseMessage<IList<CreatedDocumentDto>>(null);
            var createdDocumentDtoList = new List<CreatedDocumentDto>();
            string folderName = $"Batch{dto.BatchId}";
            string mergeFolderName = $"{folderName}/Merged";
            var files = await _amazonS3Service.GetFilesAsync(folderName);
            var folderCreated = await _amazonS3Service.CreateFolderAsync(mergeFolderName);
            int conMerge = 1;
            int skip = 0;
            int take = dto.NumOfRecords;
            List<Stream> filterFiles;

            try
            {
                do
                {
                    string fileName = $"{mergeFolderName}/{folderName}.{conMerge}.pdf";
                    filterFiles = files.Skip(skip).Take(take).ToList();
                    var stream = new MemoryStream();
                    var pdfWriter = new PdfWriter(stream);
                    var pdfMergedDocument = new PdfDocument(pdfWriter);
                    var merger = new PdfMerger(pdfMergedDocument);

                    foreach (var file in filterFiles)
                    {
                        var pdfReader = new PdfReader(file);
                        var pdfDocument = new PdfDocument(pdfReader);
                        merger.Merge(pdfDocument, 1, pdfDocument.GetNumberOfPages());
                    }

                    merger.Close();

                    var fileCreated = await _amazonS3Service.CreateFileAsync(fileName, stream);

                    createdDocumentDtoList.Add(new CreatedDocumentDto
                    {
                        Name = fileName,
                        Content = Convert.ToBase64String(stream.ToArray())
                    });

                    skip = take * conMerge;
                    conMerge++;

                } while (skip < files.Count);

                response.Payload = createdDocumentDtoList;
            }
            catch (Exception ex)
            {
                response.Status = MessageConstants.MsgStatusFailed;
                response.ErrorMessage = ex.Message;
            }

            return response;
        }

        private string ReplaceValuesInTemplate(string template, DocumentDto dto)
        {
            template = template.Replace("[CORRECTED]", dto.Corrected ? "checked" : string.Empty);
            template = template.Replace("[PAY_AMOUNT]", dto.PaymentAmount.ToString());
            template = template.Replace("[YEAR]", dto.Year.ToString());
            template = template.Replace("[SSN]", dto.SocialNumber.ToString());
            template = template.Replace("[FED_TAX_WITHHELD]", dto.FederalTaxesWithheld.ToString());
            template = template.Replace("[NAME]", dto.Name);
            template = template.Replace("[ADDRESS]", dto.Address);
            template = template.Replace("[ZIP]", dto.ZipCode);
            template = template.Replace("[ACCOUNT]", dto.AccountNumber.HasValue ? dto.AccountNumber.ToString() : string.Empty);
            template = template.Replace("[STATE_TAX_WITHHELD]", "0.00");
            template = template.Replace("[REPAYMENTS]", "0.00");
            template = template.Replace("[VERSION]", "123");

            return template;
        }
    }
}