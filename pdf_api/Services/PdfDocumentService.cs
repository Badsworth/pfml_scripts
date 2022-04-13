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
        Task<ResponseMessage<CreatedDocumentDto>> Generate(Document1099 dto);
        Task<ResponseMessage<CreatedDocumentDto>> Generate(AnyDocument dto);
        Task<ResponseMessage<IList<CreatedDocumentDto>>> Merge(MergeDto dto);
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

        private void switchToBucket(string key) {
            bucket = _amazonS3Service.PickBucket(key);
          
            Console.WriteLine("Selected bucket: " + bucket.Key);
        }

        public async Task<ResponseMessage<CreatedDocumentDto>> UpdateTemplate()
        {
            var response = new ResponseMessage<CreatedDocumentDto>(null);
            string srcFileName = $"Assets/{bucket.Key}/{bucket.Template}";
            string desFileName = bucket.Template;

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

        public async Task<ResponseMessage<CreatedDocumentDto>> Generate(Document1099 dto)
        {
            switchToBucket("1099");
            string folderName = $"Batch-{dto.BatchId}";
            string formsFolderName = $"{folderName}/Forms";
            string subBatchFolderName = $"{formsFolderName}/{dto.Name.Split("/")[0]}";
            string fileName = $"{subBatchFolderName}/{dto.Id}.pdf";
            
            var response = await GenerateFile(dto, folderName, fileName);
            return response;
        }
 
        public async Task<ResponseMessage<CreatedDocumentDto>> Generate(AnyDocument dto)
        {
            // bucket and folder name needs to be dynamic
            Console.WriteLine(dto.Type);
            switchToBucket(dto.Type);
            string folderName = $"placeholderhere";
            string fileName = $"{folderName}/{dto.Id}.pdf";
            
            var response = await GenerateFile(dto, folderName, fileName);
            return response;
        }

        private async Task<ResponseMessage<CreatedDocumentDto>> GenerateFile(AnyDocument dto, string folderName, string fileName) {
            var response = new ResponseMessage<CreatedDocumentDto>(null);
            try
            {
                var template = await _amazonS3Service.GetFileAsync(bucket.Template);
                string document = "";
                switch (dto.Type) {
                    case "1099":
                        ReplaceValues1099(new StreamReader(template).ReadToEnd(), dto);
                        break;
                    case "UserNotFound":
                        ReplaceValuesUserNotFound(new StreamReader(template).ReadToEnd(), dto);
                        break;
                    default:
                        break;
                }
                
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

        private string ReplaceValues1099(string template, AnyDocument dto)
        {
            Document1099 newDto = (Document1099) dto;
            template = template.Replace("[CORRECTED]", newDto.Corrected ? "checked" : string.Empty);
            template = template.Replace("[PAY_AMOUNT]", newDto.PaymentAmount.ToString());
            template = template.Replace("[YEAR]", newDto.Year.ToString());
            template = template.Replace("[SSN]", newDto.SocialNumber);
            template = template.Replace("[FED_TAX_WITHHELD]", newDto.FederalTaxesWithheld.ToString());
            template = template.Replace("[NAME]", newDto.Name.Split("/")[1]);
            template = template.Replace("[ADDRESS]", newDto.Address);
            template = template.Replace("[ADDRESS2]", newDto.Address2);
            template = template.Replace("[CITY]", newDto.City);
            template = template.Replace("[STATE]", newDto.State);
            template = template.Replace("[ZIP]", newDto.ZipCode);
            template = template.Replace("[ACCOUNT]", newDto.AccountNumber.HasValue ? newDto.AccountNumber.ToString() : string.Empty);
            template = template.Replace("[STATE_TAX_WITHHELD]", newDto.StateTaxesWithheld.ToString());
            template = template.Replace("[REPAYMENTS]", newDto.Repayments.ToString());
            template = template.Replace("[VERSION]", "1.0");

            return template;
        }

        private string ReplaceValuesUserNotFound(string template, AnyDocument dto)
        {
            DocumentClaimantInfo newDto = JsonConvert.SerializeObject(JsonConvert.DeserializeObject<DocumentClaimantInfo>(dto));
            template = template.Replace("[FILENAME]", newDto.Id);
            template = template.Replace("[APPLICATIONID]", newDto.ApplicationId);
            template = template.Replace("[SUBMISSIONTIME]", newDto.SubmissionTime);
            template = template.Replace("[NAME]", newDto.Name);
            template = template.Replace("[ADDRESS]", newDto.Address);
            template = template.Replace("[DATEOFBIRTH]", newDto.DateOfBirth);
            template = template.Replace("[GENDER]", newDto.Gender);
            template = template.Replace("[EMAIL]", newDto.Email);
            template = template.Replace("[PHONE]", newDto.Phone);
            template = template.Replace("[IDNUMBER]", newDto.IdNumber);
            template = template.Replace("[SSN]", newDto.SSN);
            template = template.Replace("[DATEOFHIRE]", newDto.DateOfHire);
            template = template.Replace("[HOURSWORKEDPERWEEK]", newDto.HoursWorkedPerWeek);
            template = template.Replace("[FEIN]", newDto.FEIN);
            template = template.Replace("[EMPLOYERNAME]", newDto.EmployerName);
            template = template.Replace("[STILLWORKSFOREMPLOYER]", newDto.StillWorksForEmployer);
            template = template.Replace("[REQUESTEDLEAVEREASON]", newDto.RequestedLeaveReason);
            template = template.Replace("[REQUESTEDLEAVESTARTDATE]", newDto.RequestedLeaveStartDate);
            
            return template;
        }
    }
}