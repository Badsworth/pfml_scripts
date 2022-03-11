using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace PfmlPdfApi.Models
{
    public class DocumentDto
    {
        [Required]
        public string Id { get; set; }

        [Required]
        public string BatchId { get; set; }

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
}
