import { ApplicationRequestBody } from "../api";
import { DocumentTypes } from "@/simulation/documents";

export const fineosUserTypeNames = ["SAVILINX", "DFMLOPS"] as const;
export type FineosUserType = typeof fineosUserTypeNames[number];

// Represents a single claim that will be issued to the system.
export type SimulationClaim = {
  scenario: string;
  claim: ApplicationRequestBody;
  documents: ClaimDocument[];

  // Flag to control validity of a mass ID #. Used in RMV file generation.
  hasInvalidMassId?: boolean;
  // Flag to control financial eligibility of claimant. Used when DOR file is generated.
  financiallyIneligible?: boolean;
  // Flag to control whether the claim is submitted to the API. Used to provide claims
  // that have accompanying documents, but aren't actually in the system yet.
  skipSubmitClaim?: boolean;
};

// Represents a document that may be uploaded during final submission, or may
// be captured to a folder for "manual" delivery.
export type ClaimDocument = {
  // Type of document.
  type: DocumentTypes;
  // Filesystem path to the document.
  path: string;
  // Flag to control whether the document should be uploaded (default), or "manually"
  // submitted.
  submittedManually?: boolean;
};

// EmployeeSource is the interface for getting or generating an employee.
export interface EmployeeFactory {
  (financiallyIneligible: boolean): EmployeeRecord;
}

// ClaimUser is a partial of a pre-created user we can pass to scenario generators.
export type EmployeeRecord = Pick<
  ApplicationRequestBody,
  "first_name" | "last_name" | "tax_identifier" | "employer_fein"
>;

export { SimulationGenerator } from "./simulate";
