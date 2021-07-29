import { ApplicationRequestBody, DocumentUploadRequest } from "../../api";
import MassID from "./MassID";
import OutOfStateID from "./OutOfStateID";
import PrebirthLetter from "./PreBirthLetter";
import HealthCareProviderForm from "./HealthCareProviderForm";
import BirthCertificate from "./BirthCertificate";
import AdoptionCertificate from "./AdoptionCertificate";
import FosterPlacementLetter from "./FosterPlacementLetter";
import PersonalLetter from "./PersonalLetter";
import CatPicture from "./CatPicture";
import CaringLeaveProviderForm from "./CaringLeaveProviderForm";
import FileWrapper from "../FileWrapper";
import { getCertificationDocumentType } from "../../util/documents";
import StubFineosDoc from "./StubFineosDoc";

export const generators = {
  MASSID: new MassID("Identification Proof"),
  OOSID: new OutOfStateID("Identification Proof"),
  PREBIRTH: new PrebirthLetter(getCertificationDocumentType("Child Bonding")),
  HCP: new HealthCareProviderForm(
    getCertificationDocumentType("Serious Health Condition - Employee")
  ),
  BIRTHCERTIFICATE: new BirthCertificate(
    getCertificationDocumentType("Child Bonding")
  ),
  ADOPTIONCERT: new AdoptionCertificate(
    getCertificationDocumentType("Child Bonding")
  ),
  FOSTERPLACEMENT: new FosterPlacementLetter(
    getCertificationDocumentType("Child Bonding")
  ),
  PERSONALLETTER: new PersonalLetter(
    getCertificationDocumentType("Child Bonding")
  ),
  CATPIC: new CatPicture(getCertificationDocumentType("Child Bonding")),
  CARING: new CaringLeaveProviderForm(
    getCertificationDocumentType("Care for a Family Member")
  ),
  PREGNANCY_MATERNITY_FORM: new HealthCareProviderForm(
    "Pregnancy/Maternity form"
  ),
  /**Stub document for use only when submitting fineos specific claims */
  MILITARY_EXIGENCY_FORM: new StubFineosDoc("Military exigency form"),
  /**Stub document for use only when submitting fineos specific claims */
  ACTIVE_SERVICE_PROOF: new StubFineosDoc(
    "Family Member Active Duty Service Proof"
  ),
  /**Stub document for use only when submitting fineos specific claims */
  COVERED_SERVICE_MEMBER_ID: new StubFineosDoc(
    "Covered Service Member Identification Proof"
  ),
};

export type DocumentWithPromisedFile = Omit<DocumentUploadRequest, "file"> & {
  file: () => Promise<FileWrapper>;
};
export type DehydratedDocument = Omit<DocumentUploadRequest, "file"> & {
  file: string;
};

export type DocumentGenerationSpec = {
  [P in keyof typeof generators]?: Parameters<
    typeof generators[P]["generateDocumentRequestBody"]
  >[1];
};

/**
 * This is the main entrypoint into document generation.
 *
 * @param claim
 * @param spec
 */
export default function generateDocuments(
  claim: ApplicationRequestBody,
  spec: DocumentGenerationSpec
): DocumentWithPromisedFile[] {
  return Object.entries(spec).map(([type, docOptions]) => {
    if (!(type in generators)) {
      throw new Error(`Invalid document type: ${type}`);
    }
    const generator = generators[type as keyof typeof generators];
    return generator.generateDocumentRequestBody(claim, docOptions ?? {});
  });
}
