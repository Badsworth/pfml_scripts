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

export const generators = {
  MASSID: new MassID(),
  OOSID: new OutOfStateID(),
  PREBIRTH: new PrebirthLetter(),
  HCP: new HealthCareProviderForm(),
  BIRTHCERTIFICATE: new BirthCertificate(),
  ADOPTIONCERT: new AdoptionCertificate(),
  FOSTERPLACEMENT: new FosterPlacementLetter(),
  PERSONALLETTER: new PersonalLetter(),
  CATPIC: new CatPicture(),
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
