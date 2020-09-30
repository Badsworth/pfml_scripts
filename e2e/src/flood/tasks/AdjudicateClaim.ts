import Approve from "./ApproveClaim";
import Deny from "./DenyClaim";

const isGoingToApproveClaim = () => (Math.random() > 0.5 ? Approve : Deny);
export default isGoingToApproveClaim();
