using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace PfmlPdfApi.Models
{
    public abstract class AnyDocument
    {
        public string Id { get; set; }
        public string BatchId { get; set; }

        public abstract string Type { get; }
        public abstract string FolderName { get; }
        public abstract string FileName { get; }

        public abstract string ReplaceValuesInTemplate(string template);
    }

    public class Document1099 : AnyDocument 
    {
        public override string Type { 
            get {
                return "1099";
            }
        }

        public override string FolderName { 
            get {
                return $"Batch-{this.BatchId}";
            }
        }
        
        public override string FileName {
            get {
                string formsFolderName = $"{this.FolderName}/Forms";
                string subBatchFolderName = $"{formsFolderName}/{this.Name.Split("/")[0]}";
                return $"{subBatchFolderName}/{this.Id}.pdf";
            }
        }

        [Required]
        public int Year { get; set; }

        [Required]
        public bool Corrected { get; set; }

        [Required]
        public double PaymentAmount { get; set; }

        [Required]
        public string SocialNumber { get; set; }

        [Required]
        public double FederalTaxesWithheld { get; set; }

        [Required]
        public double StateTaxesWithheld { get; set; }

        [Required]
        public double Repayments { get; set; }

        [Required]
        public string Name { get; set; }

        [Required]
        public string Address { get; set; }

        public string Address2 { get; set; }

        [Required]
        public string City { get; set; }

        [Required]
        public string State { get; set; }

        [Required]
        public string ZipCode { get; set; }

        public int? AccountNumber { get; set; }

        public override string ReplaceValuesInTemplate(string template)
        {
            template = template.Replace("[CORRECTED]", this.Corrected ? "checked" : string.Empty);
            template = template.Replace("[PAY_AMOUNT]", this.PaymentAmount.ToString());
            template = template.Replace("[YEAR]", this.Year.ToString());
            template = template.Replace("[SSN]", this.SocialNumber);
            template = template.Replace("[FED_TAX_WITHHELD]", this.FederalTaxesWithheld.ToString());
            template = template.Replace("[NAME]", this.Name.Split("/")[1]);
            template = template.Replace("[ADDRESS]", this.Address);
            template = template.Replace("[ADDRESS2]", this.Address2);
            template = template.Replace("[CITY]", this.City);
            template = template.Replace("[STATE]", this.State);
            template = template.Replace("[ZIP]", this.ZipCode);
            template = template.Replace("[ACCOUNT]", this.AccountNumber.HasValue ? this.AccountNumber.ToString() : string.Empty);
            template = template.Replace("[STATE_TAX_WITHHELD]", this.StateTaxesWithheld.ToString());
            template = template.Replace("[REPAYMENTS]", this.Repayments.ToString());
            template = template.Replace("[VERSION]", "1.0");

            return template;
        }
    }
    
    public class DocumentClaimantInfo : AnyDocument
    {
        public override string Type {
            get {
                return "UserNotFound";
            }
        }

        public override string FolderName {
            get {
                return $"Batch-{this.BatchId}";
            }
        }
        
        public override string FileName {
            get {
                return $"{this.FolderName}/{this.Id}.pdf";
            }
        }

        public string ApplicationId { get; set; }
        public string SubmissionTime { get; set; }
        // claimant data
        public string Name { get; set; }
        public string Address { get; set; }
        public string DateOfBirth { get; set; }
        public string Gender { get; set; }
        public string Email { get; set; }
        public string Phone { get; set; }
        // public string IdType { get; set; }
        public string IdNumber { get; set; }
        // public string TaxIdType { get; set; }
        public string SSN { get; set; }
        public string DateOfHire { get; set; }
        public string HoursWorkedPerWeek { get; set; }
        public string FEIN { get; set; }
        public string EmployerName { get; set; }
        // public string EmployerAddress { get; set; }
        // public string ContactName { get; set; }
        // public string ContactPhone { get; set; }
        // public string ContactEmail { get; set; }
        public string StillWorksForEmployer { get; set; }
        // public string Industry { get; set; }
        // public string State { get; set; }
        public string RequestedLeaveReason { get; set; }
        public string RequestedLeaveStartDate { get; set; }

        public override string ReplaceValuesInTemplate(string template)
        {
            template = template.Replace("[FILENAME]", this.Id);
            template = template.Replace("[APPLICATIONID]", this.ApplicationId);
            template = template.Replace("[SUBMISSIONTIME]", this.SubmissionTime);
            template = template.Replace("[NAME]", this.Name);
            template = template.Replace("[ADDRESS]", this.Address);
            template = template.Replace("[DATEOFBIRTH]", this.DateOfBirth);
            template = template.Replace("[GENDER]", this.Gender);
            template = template.Replace("[EMAIL]", this.Email);
            template = template.Replace("[PHONE]", this.Phone);
            template = template.Replace("[IDNUMBER]", this.IdNumber);
            template = template.Replace("[SSN]", this.SSN);
            template = template.Replace("[DATEOFHIRE]", this.DateOfHire);
            template = template.Replace("[HOURSWORKEDPERWEEK]", this.HoursWorkedPerWeek);
            template = template.Replace("[FEIN]", this.FEIN);
            template = template.Replace("[EMPLOYERNAME]", this.EmployerName);
            template = template.Replace("[STILLWORKSFOREMPLOYER]", this.StillWorksForEmployer);
            template = template.Replace("[REQUESTEDLEAVEREASON]", this.RequestedLeaveReason);
            template = template.Replace("[REQUESTEDLEAVESTARTDATE]", this.RequestedLeaveStartDate);
            return template;
        }
    }
}
