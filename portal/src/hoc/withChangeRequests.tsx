import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import ApiResourceCollection from "../models/ApiResourceCollection";
import ChangeRequest from "../models/ChangeRequest";
import PageNotFound from "../components/PageNotFound";
import Spinner from "../components/core/Spinner";
import { useTranslation } from "../locales/i18n";

export interface WithChangeRequestsProps extends WithUserProps {
  change_requests: ApiResourceCollection<ChangeRequest>;
  query: QueryForWithChangeRequests;
}

interface QueryForWithChangeRequests {
  absence_id?: string;
}

function withChangeRequests<T extends WithChangeRequestsProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithChangeRequests = (props: WithChangeRequestsProps) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();
    const absence_id = query.absence_id;

    const { changeRequests, loadAll, isLoadingChangeRequests } =
      appLogic.changeRequests;

    useEffect(() => {
      if (absence_id) loadAll(absence_id);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoadingChangeRequests]);

    if (!absence_id) {
      return <PageNotFound />;
    }

    if (isLoadingChangeRequests) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-label={t("components.withChangeRequests.loadingLabel")}
          />
        </div>
      );
    }
    return <Component {...(props as T)} change_requests={changeRequests} />;
  };
  return withUser(ComponentWithChangeRequests);
}

export default withChangeRequests;
