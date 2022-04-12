using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace PfmlPdfApi.Models
{
    public class DocumentClaimantInfo
    {
        [Required]
        public string Id { get; }
        public string SubmissionTime { get; }

        // claimant data
        [Required]
        public string Name { get; }
        [Required]
        public string Address { get; }
        [Required]
        public string DateOfBirth { get; }
        [Required]
        public string Gender { get; }
        [Required]
        public string Email { get; }
        [Required]
        public string Phone { get; }
        [Required]
        public string IdType { get; }
        public string IdNumber { get; }
        public string TaxIdType { get; }
        public string SSN { get; }
        [Required]
        public string DateOfHire { get; }
        public string HoursWorkedPerWeek { get; }
        [Required]
        public string FEIN { get; }
        [Required]
        public string EmployerName { get; }
        public string EmployerAddress { get; }
        public string ContactName { get; }
        public string ContactPhone { get; }
        public string ContactEmail { get; }
        public string StillWorksForEmployer { get; }
        // public string Industry { get; }
        // public string State { get; }
        public string RequestedLeaveReason { get; }
        public string RequestedLeaveStartDate { get; }
        
    }
}
