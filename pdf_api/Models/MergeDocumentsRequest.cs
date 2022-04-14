using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace PfmlPdfApi.Models
{
    public class MergeDocumentsRequest
    {
        [DefaultValue("1099")]
        public string Type { get; set; }

        [Required]
        public string BatchId { get; set; }
        
        [DefaultValue(100)]
        public int NumOfRecords { get; set; }
    }
}