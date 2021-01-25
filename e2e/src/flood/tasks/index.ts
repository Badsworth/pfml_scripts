import DocumentReview, { PreDocumentReview } from "./DocumentReview";
import RequestAdditionalInformation from "./RequestAdditionalInfo";
import AdjudicateAbsence, {
  PreAdjudicateAbsence,
  PostAdjudicateAbsence,
} from "./AdjudicateClaim";
import Approve from "./ApproveClaim";
import Deny from "./DenyClaim";

export default {
  PreDocumentReview,
  DocumentReview,
  RequestAdditionalInformation,
  PreAdjudicateAbsence,
  AdjudicateAbsence,
  PostAdjudicateAbsence,
  Approve,
  Deny,
};
