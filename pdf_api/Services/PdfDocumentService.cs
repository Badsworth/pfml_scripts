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
        Task<ResponseMessage<CreatedDocumentDto>> UpdateTemplate();
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

        public async Task<ResponseMessage<CreatedDocumentDto>> UpdateTemplate()
        {
            var response = new ResponseMessage<CreatedDocumentDto>(null);
            string srcFileName = $"Assets/1099/{template1099}";
            string desFileName = template1099;

            try
            {
                var mStream = new MemoryStream(await File.ReadAllBytesAsync(srcFileName));
                var fileCreated = await _amazonS3Service.CreateFileAsync(desFileName, mStream, "text/html");
            }
            catch (Exception ex)
            {
                response.Status = MessageConstants.MsgStatusFailed;
                response.ErrorMessage = ex.Message;
            }

            return response;
        }

        public async Task<ResponseMessage<CreatedDocumentDto>> Generate(DocumentDto dto)
        {
            var response = new ResponseMessage<CreatedDocumentDto>(null);
            string folderName = $"Batch-{dto.BatchId}";
            string formsFolderName = $"{folderName}/Forms";
            string subBatchFolderName = $"{formsFolderName}/{dto.Name.Split("/")[0]}";
            string fileName = $"{subBatchFolderName}/{dto.Id}.pdf";

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
                    Name = fileName
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

                    createdDocumentDtoList.Add(new CreatedDocumentDto
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

        private string ReplaceValuesInTemplate(string template, DocumentDto dto)
        {
            template = template.Replace("[CORRECTED]", dto.Corrected ? "checked" : string.Empty);
            template = template.Replace("[PAY_AMOUNT]", dto.PaymentAmount.ToString());
            template = template.Replace("[YEAR]", dto.Year.ToString());
            template = template.Replace("[SSN]", dto.SocialNumber);
            template = template.Replace("[FED_TAX_WITHHELD]", dto.FederalTaxesWithheld.ToString());
            template = template.Replace("[NAME]", dto.Name.Split("/")[1]);
            template = template.Replace("[ADDRESS]", dto.Address);
            template = template.Replace("[CITY]", dto.City);
            template = template.Replace("[STATE]", dto.State);
            template = template.Replace("[ZIP]", dto.ZipCode);
            template = template.Replace("[ACCOUNT]", dto.AccountNumber.HasValue ? dto.AccountNumber.ToString() : string.Empty);
            template = template.Replace("[STATE_TAX_WITHHELD]", dto.StateTaxesWithheld.ToString());
            template = template.Replace("[REPAYMENTS]", dto.Repayments.ToString());
            template = template.Replace("[VERSION]", "1.0");

            return template;
        }
    }
}