import { DocumentUploadRequest } from "../../src/_api";

/**
 * This file contains TS types and enums for dealing with the Fineos UI.
 */

// Types of correspondance that can be added via the "Add Correspondance" button
// from the claim page.
export type FineosCorrespondanceType =
  | "Employer Reimbursement Formstack"
  | "Employer Reimbursement Policy"
  | "Overpayment Notice - Full Balance Recovery";

// Valid document types in Fineos. Contains documents that can be uploaded via the API,
// as well as a few that can only be uploaded through the Fineos UI.
export type FineosDocumentType =
  | DocumentUploadRequest["document_type"]
  | "Employer Reimbursement Formstack"
  | "Employer Reimbursement Policy"
  | "Overpayment Notice - Full Balance Recovery";
