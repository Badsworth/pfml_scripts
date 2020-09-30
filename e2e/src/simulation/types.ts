import { ApplicationRequestBody } from "../api";

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
  type: "HCP" | "ID-front" | "ID-back";
  // Filesystem path to the document.
  path: string;
  // Flag to control whether the document should be uploaded (default), or "manually"
  // submitted.
  submittedManually?: boolean;
};

/**
 * SimulationGenerator is a function that generates a single SimulationClaim.
 *
 * This is an interface, but it will actually be implemented by two functions that look a lot
 * like scenario() and chance() do today. That is - which scenario we actually run will be
 * determined by probability at the time the function is called.
 */
export type SimulationGeneratorOpts = {
  documentDirectory: string;
};
export interface SimulationGenerator {
  // The generator returns a promise of a SimulationClaim so that it can
  // do asynchronous operations, like writing documents to the filesystem.
  (opts: SimulationGeneratorOpts): Promise<SimulationClaim>;
}
