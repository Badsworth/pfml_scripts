import OutstandingDocumentReceived, {
  PreOutstandingDocumentReceived,
} from "./OutDocReceived";
import RequestAdditionalInformation, {
  PreRequestAdditionalInfo,
} from "./RequestInfo";
import AdjudicateAbsence, {
  PreAdjudicateAbsence,
  PostAdjudicateAbsence,
} from "./AdjudicateClaim";
import Approve from "./ApproveClaim";
import Deny from "./DenyClaim";

export default {
  PreOutstandingDocumentReceived,
  OutstandingDocumentReceived,
  PreRequestAdditionalInfo,
  RequestAdditionalInformation,
  PreAdjudicateAbsence,
  AdjudicateAbsence,
  PostAdjudicateAbsence,
  Approve,
  Deny,
};
