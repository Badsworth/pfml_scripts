import OutstandingRequirementReceived, { PreORR } from "./OutReqReceived";
import RequestAdditionalInformation, {
  PreRequestAdditionalInfo,
} from "./RequestAdditionalInfo";
import AdjudicateAbsence, {
  PreAdjudicateAbsence,
  PostAdjudicateAbsence,
} from "./AdjudicateClaim";
import Approve from "./ApproveClaim";
import Deny from "./DenyClaim";

export default {
  PreORR,
  OutstandingRequirementReceived,
  PreRequestAdditionalInfo,
  RequestAdditionalInformation,
  PreAdjudicateAbsence,
  AdjudicateAbsence,
  PostAdjudicateAbsence,
  Approve,
  Deny,
};
