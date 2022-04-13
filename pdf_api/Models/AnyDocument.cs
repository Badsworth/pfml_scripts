using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace PfmlPdfApi.Models
{
    public class AnyDocument
    {
        [Required]
        public string Id { get; set; }
        // [Required]
        public string BatchId { get; set; }
        public string Type { get; set; }
    }

    public class Document1099 : AnyDocument {
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
    }
    
    public class DocumentClaimantInfo : AnyDocument
    {
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
    }
}
