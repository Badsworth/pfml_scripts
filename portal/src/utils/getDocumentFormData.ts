import { DocumentTypeEnum } from "../models/Document";
import assert from "assert";

const getDocumentFormData = (
  file: File,
  document_type: DocumentTypeEnum,
  mark_evidence_received: boolean
) => {
  const formData = new FormData();
  formData.append("document_type", document_type);

  assert(file);
  // we use Blob to support IE 11, formData is using "blob" as the default file name,
  // so we pass the actual file name here
  // https://developer.mozilla.org/en-US/docs/Web/API/FormData/append#append_parameters
  formData.append("file", file, file.name);
  formData.append("name", file.name);
  formData.append("mark_evidence_received", mark_evidence_received.toString());

  return formData;
};

export default getDocumentFormData;
