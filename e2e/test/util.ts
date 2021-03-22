/* 
  Note: Parts of the test are commented out due to functionality not being ready
  for testing.  Once feature is ready for testing we'll remove comments
*/

export const pdf = [
  [
    "Should submit a PDF document with file size less than 4.5MB successfully",
    "./cypress/fixtures/docTesting/small-150KB.pdf",
    "Successfully uploaded document",
    200,
  ],
  // [
  //   "Should submit a PDF document with file size right at 4.5MB successfully",
  //   "./cypress/fixtures/docTesting/limit-4.5MB.pdf",
  //   "Successfully uploaded document",
  //   200,
  // ],
  [
    "Should submit a PDF document with file size larger than 4.5MB (10MB) unsuccessfully and return API error",
    "./cypress/fixtures/docTesting/large-10MB.pdf",
    "Request Entity Too Large",
    413,
  ],
];

export const jpg = [
  [
    "Should submit a JPG document with file size less than 4.5MB successfully",
    "./cypress/fixtures/docTesting/xsmall-220KB.jpg",
    "Successfully uploaded document",
    200,
  ],
  // [
  //   "Should submit a JPG document with file size right at 4.5MB successfully",
  //   "./cypress/fixtures/docTesting/limit-4.5MB.jpg",
  //   "Successfully uploaded document",
  //   200,
  // ],
  [
    "Should submit a JPG document with file size larger than 4.5MB (15.5MB) unsuccessfully and return API error",
    "./cypress/fixtures/docTesting/large-15.5MB.jpg",
    "Request Entity Too Large",
    413,
  ],
];

export const png = [
  [
    "Should submit a PNG document with file size less than 4.5MB successfully",
    "./cypress/fixtures/docTesting/small-2.7MB.png",
    "Successfully uploaded document",
    200,
  ],
  // [
  //   "Should submit a PNG document with file size right at 4.5MB successfully",
  //   "./cypress/fixtures/docTesting/limit-4.5MB.png",
  //   "Successfully uploaded document",
  //   200,
  // ],
  [
    "Should submit a PNG document with file size larger than 4.5MB (15.5MB) unsuccessfully and return API error",
    "./cypress/fixtures/docTesting/large-14MB.png",
    "Request Entity Too Large",
    413,
  ],
];

export const badFileTypes = [
  [
    "Should receive error when trying to submit an incorrect file type (.gif)",
    "./cypress/fixtures/docTesting/small-275KB.gif",
    "File validation error.",
    400,
  ],
  [
    "Should receive error when trying to submit an incorrect file type (.bmp)",
    "./cypress/fixtures/docTesting/small-1MB.bmp",
    "File validation error.",
    400,
  ],
  [
    "Should receive error when trying to submit an incorrect file type (.svg)",
    "./cypress/fixtures/docTesting/small-387KB.svg",
    "File validation error.",
    400,
  ],
];
