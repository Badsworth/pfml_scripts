import { compact, sortBy } from "lodash";
import { ManagedRequirement } from "../models/Claim";
import formatDate from "./formatDate";

const getClosestOpenFollowUpDate = (
  managedRequirements: ManagedRequirement[],
  formattedDate = true
) => {
  const followUpDates = compact(
    managedRequirements.map((managedRequirement) => {
      if (managedRequirement.status === "Open") {
        return managedRequirement.follow_up_date;
      }
      return undefined;
    })
  );
  if (followUpDates.length === 0) return;
  const followUpDate = sortBy(followUpDates)[0];
  if (formattedDate) {
    return formatDate(followUpDate).short();
  }
  return followUpDate;
};

export default getClosestOpenFollowUpDate;
