import { EmployeePickSpec } from "./Employee";
import { APIClaimSpec, BaseClaimSpecification, FineosClaimSpec } from "./Claim";
import { DocumentGenerationSpec } from "./documents";

/**
 * Describes a particular scenario.
 *
 * Consists of information about how the claim should be generated, including information about the employee
 * that should be used.
 */
export type ScenarioSpecification<T extends BaseClaimSpecification = Claims> = {
  employee: EmployeePickSpec;
  claim: T;
};

type Claims =
  | PrebirthClaim
  | MedicalClaim
  | BondingNewbornClaim
  | BondingFosterClaim
  | BondingAdoptionClaim
  | PregnancyClaim
  | CaringLeaveClaim;

/**Medical pre-birth claim */
export interface PrebirthClaim extends APIClaimSpec {
  reason: "Serious Health Condition - Employee";
  docs?: Pick<DocumentGenerationSpec, "MASSID" | "PREGNANCY_MATERNITY_FORM">;
  pregnant_or_recent_birth: true;
}
/**Medical claim */
export interface MedicalClaim extends APIClaimSpec {
  reason: "Serious Health Condition - Employee";
  docs?: Pick<DocumentGenerationSpec, "MASSID" | "HCP">;
}
/**Child bonding Newborn claim */
export interface BondingNewbornClaim extends APIClaimSpec {
  reason: "Child Bonding";
  reason_qualifier: "Newborn";
  docs?: Pick<DocumentGenerationSpec, "MASSID" | "BIRTHCERTIFICATE">;
}
/**Child bonding Foster Care claim */
export interface BondingFosterClaim extends APIClaimSpec {
  reason: "Child Bonding";
  reason_qualifier: "Foster Care";
  docs?: Pick<DocumentGenerationSpec, "MASSID" | "FOSTERPLACEMENT">;
}
/**Child bonding Adoption claim */
export interface BondingAdoptionClaim extends APIClaimSpec {
  reason: "Child Bonding";
  reason_qualifier: "Adoption";
  docs?: Pick<DocumentGenerationSpec, "MASSID" | "ADOPTIONCERT">;
}
/**Pregnancy/Maternity claim */
export interface PregnancyClaim extends APIClaimSpec {
  reason: "Pregnancy/Maternity";
  docs?: Pick<DocumentGenerationSpec, "MASSID" | "PREGNANCY_MATERNITY_FORM">;
}
/**Care for a Family Member claim */
export interface CaringLeaveClaim extends APIClaimSpec {
  reason: "Care for a Family Member";
  docs?: Pick<DocumentGenerationSpec, "MASSID" | "CARING">;
}

/**Fineos exlusive claim types */
export interface MilitaryExigencyClaim extends FineosClaimSpec {
  reason: "Military Exigency Family";
  docs?: Pick<
    DocumentGenerationSpec,
    "MILITARY_EXIGENCY_FORM" | "ACTIVE_SERVICE_PROOF" | "MASSID"
  >;
}
export interface MilitaryCaregiverClaim extends FineosClaimSpec {
  reason: "Military Caregiver";
  docs?: Pick<DocumentGenerationSpec, "COVERED_SERVICE_MEMBER_ID" | "MASSID">;
}
