import {
  ApplicationRequestBody,
  EmployerClaimRequestBody,
  PaymentPreferenceRequestBody,
} from "../api";
import { DocumentTypes } from "./documents";

export const fineosUserTypeNames = ["SAVILINX", "DFMLOPS"] as const;
export type FineosUserType = typeof fineosUserTypeNames[number];

// Represents a single claim that will be issued to the system.
export type SimulationClaim = {
  id: string;
  scenario: string;
  claim: ApplicationRequestBody;
  documents: ClaimDocument[];
  employerResponse?: SimulatedEmployerResponse;

  // Flag to control validity of a mass ID #. Used in RMV file generation.
  hasInvalidMassId?: boolean;
  // Flag to control financial eligibility of claimant. Used when DOR file is generated.
  financiallyIneligible?: boolean;
  // Flag to control whether the claim is submitted to the API. Used to provide claims
  // that have accompanying documents, but aren't actually in the system yet.
  skipSubmitClaim?: boolean;
  paymentPreference: PaymentPreferenceRequestBody;
  wages?: number;
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

export type SimulatedEmployerResponse = Pick<
  EmployerClaimRequestBody,
  "hours_worked_per_week" | "employer_decision" | "fraud" | "comment"
>;

export type WageSpecification =
  | "high"
  | "medium"
  | "low"
  | "eligible"
  | "ineligible"
  | number;

// EmployeeFactory is the interface for getting or generating an employee.
export interface EmployeeFactory {
  (
    wageSpec: WageSpecification,
    employerFactory?: EmployerFactory
  ): EmployeeRecord;
}

// ClaimUser is a partial of a pre-created user we can pass to scenario generators.
export type EmployeeRecord = {
  first_name: string;
  last_name: string;
  tax_identifier: string;
  employer_fein: string;
  wages: number;
};

// EmployerFactory is the interface for getting or generating an employer.
export interface EmployerFactory {
  (): Employer;
}

export type Employer = {
  accountKey: string;
  name: string;
  fein: string;
  street: string;
  city: string;
  state: string;
  zip: string;
  dba: string;
  family_exemption: boolean;
  medical_exemption: boolean;
  exemption_commence_date?: Date | string;
  exemption_cease_date?: Date | string;
  updated_date?: Date | string;
  size?: "small" | "medium" | "large";
  withholdings: number[];
};
