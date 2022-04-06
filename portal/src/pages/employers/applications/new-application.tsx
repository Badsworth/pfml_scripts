import { AppLogic } from "../../../hooks/useAppLogic";
import { useEffect } from "react";

export default function NewApplication({ appLogic }: { appLogic: AppLogic }) {
  /**
   * This page is deprecated, but was previously linked to in email notifications to leave admins,
   * so we want to preserve the URL and redirect to the new destination.
   */
  useEffect(() => {
    appLogic.portalFlow.goToPageFor("REDIRECT", {}, {}, { redirect: true });
  });
  return null;
}
