import OutstandingDocumentReceived, {
  PreOutstandingDocumentReceived,
} from "./OutDocReceived";
import RequestAdditionalInformation, {
  PreRequestAdditionalInfo,
} from "./RequestInfo";
import Adjudicate from "./AdjudicateClaim";
import Approve from "./ApproveClaim";
import Deny from "./DenyClaim";

export default {
  PreOutstandingDocumentReceived,
  OutstandingDocumentReceived,
  PreRequestAdditionalInfo,
  RequestAdditionalInformation,
  Adjudicate,
  Approve,
  Deny,
};
