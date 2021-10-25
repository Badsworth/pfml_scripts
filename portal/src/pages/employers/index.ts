import routes from "../../routes";
import { useEffect } from "react";

export default function Page({ appLogic }) {
  useEffect(() => {
    appLogic.portalFlow.goTo(routes.index, {}, { redirect: true });
  });

  return null;
}
