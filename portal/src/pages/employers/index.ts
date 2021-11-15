import { AppLogic } from "../../hooks/useAppLogic";
import routes from "../../routes";
import { useEffect } from "react";

export default function Page({ appLogic }: { appLogic: AppLogic }) {
  useEffect(() => {
    appLogic.portalFlow.goTo(routes.index, {}, { redirect: true });
  });

  return null;
}
