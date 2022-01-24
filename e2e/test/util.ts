/*
  @Note: Parts of the test are commented out due to functionality not being ready
  for testing.  Once feature is ready for testing we'll remove comments.

  We can uncomment uploads when NAVA API team has completed implementation
  for the new API upload using multipart: https://lwd.atlassian.net/browse/PORTAL-1390

  This file also contains other util functions/variables specifically for integration tests
*/

import { promises as fs } from 'fs';
import path from 'path';
import { exiftool } from "exiftool-vendored";
import { PDFDocument } from 'pdf-lib';
import config from "../src/config";

type DocumentType = 
  | "pdf"
  | "jpg"
  | "png";

export const withGeneratedDocument = async (
  type: DocumentType,
  size: [ number, "mb" | "kb" ],
  cb: 
    | ((filepath: string) => Promise<void>)
    | ((filepath: string) => void)
): Promise<void> => {
  const sizeTruncated = Math.max(Math.round(size[0]), 1);
  const targetSizeKb = sizeTruncated 
    * (size[1] === "mb" ? 1000 : 1);

  const tempDir = await fs.mkdtemp(`${type}-${targetSizeKb}kb-`);
  const documentPath = path.join(tempDir, `generated.${type}`);

  // create an array of garbage data that we'll use to pad out
  // files in order to get them close to the target size
  const junkData = new Array(targetSizeKb * 100)
      .fill(null)
      // generate random 10-character ASCII strings
      .map(() => Math.random().toString().slice(0, 10));

  if (type === "jpg" || type === "png") {
    const baseFile = type === "jpg"
      ? "./cypress/fixtures/docTesting/xxsmall-90B.jpg"
      : "./cypress/fixtures/docTesting/xxsmall-90B.png"

    await fs.copyFile(baseFile, documentPath);
  }

  if (type === "pdf") {
    const doc = await PDFDocument.create();

    await fs.writeFile(documentPath, await doc.save());
  }

  await exiftool.write(
    documentPath,
    { UserComment: junkData.join("") }
  );
  await exiftool.end();

  await cb(documentPath);

  // clean up
  await fs.rm(tempDir, { recursive: true });

  return;
}

export interface DocumentTestCase {
  description: string;
  filepath: string;
  statusCode: 200 | 413 | 400;
}

type DocumentTestSpec = 
  | Array<DocumentTestCase>
  | (() => Array<DocumentTestCase>);


/**
 *  Idea here is to test the file size limit (4.5MB) w/each accepted
 *  filetype: PDF/JPG/PNG in three different ways.
 *    - smaller than limit
 *    - right at limit ex. 4.4MB
 *    - larger than limit
 */
export const documentTests: Record<string, DocumentTestSpec> = {
  pdf: [
    {
      description: "Should submit a PDF document with file size less than 4.5MB successfully",
      filepath: "./cypress/fixtures/docTesting/small-150KB.pdf",
      statusCode: 200
    },
    {
      description: "Should submit a PDF document with file size larger than 4.5MB (10MB) unsuccessfully and return API error",
      filepath: "./cypress/fixtures/docTesting/large-10MB.pdf",
      statusCode: 413,
    },
  ],
  jpg: [
    {
      description: "Should submit a JPG document with file size less than 4.5MB successfully",
      filepath: "./cypress/fixtures/docTesting/xsmall-220KB.jpg",
      statusCode: 200,
    },
    {
      description: "Should submit a JPG document with file size larger than 4.5MB (15.5MB) unsuccessfully and return API error",
      filepath: "./cypress/fixtures/docTesting/large-15.5MB.jpg",
      statusCode: 413,
    },
  ],
  png: [
    {
      description: "Should submit a PNG document with file size less than 4.5MB successfully",
      filepath: "./cypress/fixtures/docTesting/small-2.7MB.png",
      statusCode: 200,
    },
    {
      description: "Should submit a PNG document with file size larger than 4.5MB (15.5MB) unsuccessfully and return API error",
      filepath: "./cypress/fixtures/docTesting/large-14MB.png",
      statusCode: 413,
    },
  ],
  badFileTypes:  [
    {
      description: "Should receive error when trying to submit an incorrect file type (.gif)",
      filepath: "./cypress/fixtures/docTesting/small-275KB.gif",
      statusCode: 400,
    },
    {
      description: "Should receive error when trying to submit an incorrect file type (.svg)",
      filepath: "./cypress/fixtures/docTesting/small-387KB.svg",
      statusCode: 400,
    },
  ],
  // Added logic to establish baseline of failures for Files right at limit
  rightAtLimit: () => {
    if(![
      "stage",  // not configured - expected failures for baseline
      "performance",
      "test",
      "cps-preview",
      "breakfix",
      "uat"
    ].includes(config("ENVIRONMENT"))) {
      return [];
    }
    return [
      {
        description: "Should submit a PDF document with file size right at 4.5MB successfully",
        filepath: "./cypress/fixtures/docTesting/limit-4.5MB.pdf",
        statusCode: 200,
      },
      {
        description: "Should submit a JPG document with file size right at 4.5MB successfully",
        filepath: "./cypress/fixtures/docTesting/limit-4.5MB.jpg",
        statusCode: 200,
      },
      {
        description: "Should submit a PNG document with file size right at 4.5MB successfully",
        filepath: "./cypress/fixtures/docTesting/limit-4.5MB.png",
        statusCode: 200,
      },
    ];
  } 
}

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
