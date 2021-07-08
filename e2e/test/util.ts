/* 
  Note: Parts of the test are commented out due to functionality not being ready
  for testing.  Once feature is ready for testing we'll remove comments

  This file also contains other util functions/variables specifically for integration tests
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

export const id_proofing = [
  [
    "fraudulent",
    {
      absence_case_id: "z1pGihOsyBW4LBCqNyQr",
      first_name: "Willis",
      last_name: "Sierra",
      ssn_last_4: "9053",
      date_of_birth: "1975-06-02",
      mass_id_number: "SA2600200",
      residential_address_city: "Lynn",
      residential_address_line_1: "42 murray st",
      residential_address_zip_code: "01905",
    },
    "Verification failed because no record could be found for given ID information.",
    false,
  ],
  [
    "valid",
    {
      absence_case_id: "4LjXqd0kSJ1px8p6LF8P",
      first_name: "John",
      last_name: "Pinkham",
      ssn_last_4: "0105",
      date_of_birth: "1973-10-30",
      mass_id_number: "S46493908",
      residential_address_city: "Ashfield",
      residential_address_line_1: "83g bear mountain dr",
      residential_address_zip_code: "01330",
    },
    "Verification check passed.",
    true,
  ],
  [
    "a zipcode mismatch",
    {
      absence_case_id: "fyvrWPf6ZqV7ShOh5VnG",
      first_name: "John",
      last_name: "Pinkham",
      ssn_last_4: "0105",
      date_of_birth: "1973-10-30",
      mass_id_number: "S46493908",
      residential_address_city: "Ashfield",
      residential_address_line_1: "700 College St",
      residential_address_zip_code: "53511",
    },
    "Verification failed because residential zip code mismatch.",
    false,
  ],
  [
    "a city mismatch",
    {
      absence_case_id: "fyvrWPf6ZqV7ShOh5VnG",
      first_name: "John",
      last_name: "Pinkham",
      ssn_last_4: "0105",
      date_of_birth: "1973-10-30",
      mass_id_number: "S46493908",
      residential_address_city: "Beloit",
      residential_address_line_1: "700 College St",
      residential_address_zip_code: "01330",
    },
    "Verification failed because residential city mismatch.",
    false,
  ],
];
