import { AppLogic } from "../../../hooks/useAppLogic";

interface PageProps {
  appLogic: AppLogic;
}

export const NewApplication = (props: PageProps) => {
  /**
   * This page is deprecated, but was previously linked to in email notifications to leave admins,
   * so we want to preserve the URL and redirect to the new destination.
   */
  props.appLogic.portalFlow.goToPageFor("REDIRECT", {}, {}, { redirect: true });

  return null;
};

export default NewApplication;
