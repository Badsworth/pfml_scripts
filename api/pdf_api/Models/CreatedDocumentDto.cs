using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace PfmlPdfApi.Models
{
    public class CreatedDocumentDto
    {
        [Required]
        public string Name { get; set; }
        
        [Required]
        public string Content { get; set; }
    }
}