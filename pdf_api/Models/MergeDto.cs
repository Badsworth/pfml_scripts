using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace PfmlPdfApi.Models
{
    public class MergeDto
    {
        [Required]
        public string BatchId { get; set; }
        
        [DefaultValue(100)]
        public int NumOfRecords { get; set; }
    }
}