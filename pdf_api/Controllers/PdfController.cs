using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Net;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using PfmlPdfApi.Models;
using PfmlPdfApi.Services;
using PfmlPdfApi.Common;

namespace PfmlPdfApi.Controllers
{
    [ApiController]
    [Route("api/pdf")]
    public class PdfController : ControllerBase
    {
        private readonly IPdfDocumentService _pdfDocumentService;

        public PdfController(IPdfDocumentService pdfDocumentService)
        {
            _pdfDocumentService = pdfDocumentService;
        }

        [HttpGet]
        public async Task<ActionResult> Get()
        {
            return Ok(string.Format("{0} - Pfml Pdf Api is running.", Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT").Substring(0, 3)));
        }

        [HttpGet]
        [Route("updateTemplate")]
        public async Task<ActionResult> UpdateTemplate()
        {
            var response = await _pdfDocumentService.UpdateTemplate();

            if (response.Status == MessageConstants.MsgStatusSuccess)
                return Ok();

            return StatusCode((int)HttpStatusCode.InternalServerError, response.ErrorMessage);
        }

        [HttpPost]
        [Route("generate")]
        public async Task<ActionResult> Generate(DocumentDto dto)
        {
            var response = await _pdfDocumentService.Generate(dto);

            if (response.Status == MessageConstants.MsgStatusSuccess)
                return Ok();

            return StatusCode((int)HttpStatusCode.InternalServerError, response.ErrorMessage);
        }

        [HttpPost]
        [Route("merge")]
        public async Task<ActionResult> Merge(MergeDto dto)
        {
            var response = await _pdfDocumentService.Merge(dto);

            if (response.Status == MessageConstants.MsgStatusSuccess)
                return Ok();

            return StatusCode((int)HttpStatusCode.InternalServerError, response.ErrorMessage);
        }
    }
}
