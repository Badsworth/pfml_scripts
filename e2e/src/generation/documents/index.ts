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
import FileWrapper from "../FileWrapper";
import config from "../../config";
import { getCertificationDocumentType } from "../../util/documents";

const hasServicePack = config("HAS_FINEOS_SP") === "true";

export const generators = {
  MASSID: new MassID("Identification Proof"),
  OOSID: new OutOfStateID("Identification Proof"),
  PREBIRTH: new PrebirthLetter(
    getCertificationDocumentType("Child Bonding", hasServicePack)
  ),
  HCP: new HealthCareProviderForm(
    getCertificationDocumentType(
      "Serious Health Condition - Employee",
      hasServicePack
    )
  ),
  BIRTHCERTIFICATE: new BirthCertificate(
    getCertificationDocumentType("Child Bonding", hasServicePack)
  ),
  ADOPTIONCERT: new AdoptionCertificate(
    getCertificationDocumentType("Child Bonding", hasServicePack)
  ),
  FOSTERPLACEMENT: new FosterPlacementLetter(
    getCertificationDocumentType("Child Bonding", hasServicePack)
  ),
  PERSONALLETTER: new PersonalLetter(
    getCertificationDocumentType("Child Bonding", hasServicePack)
  ),
  CATPIC: new CatPicture(
    getCertificationDocumentType("Child Bonding", hasServicePack)
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
