import { AppLogic } from "../../../hooks/useAppLogic";
import { useEffect } from "react";

interface PageProps {
  appLogic: AppLogic;
  query: {
    absence_id?: string;
  };
}

export const NewApplication = (props: PageProps) => {
  /**
   * This page is deprecated, but was previously linked to in email notifications to leave admins,
   * so we want to preserve the URL and redirect to the new destination.
   */
  useEffect(() => {
    // The query is empty on initial page load, so we want to only redirect when we have the necessary params
    if (props.query?.absence_id) {
      props.appLogic.portalFlow.goToPageFor(
        "REDIRECT",
        {},
        { absence_id: props.query.absence_id },
        { redirect: true }
      );
    }
  });

  return null;
};

export default NewApplication;
