import React, { useEffect, useState } from "react";
import withUser, { WithUserProps } from "./withUser";
import PageNotFound from "../components/PageNotFound";
import Spinner from "../components/core/Spinner";
import { UserLeaveAdministrator } from "../models/User";
import Withholding from "../models/Withholding";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export interface QueryForWithWithholding {
  employer_id?: string;
}

export interface WithWithholdingProps extends WithUserProps {
  employer: UserLeaveAdministrator;
  withholding: Withholding;
}
/**
 * Higher order component that loads withholding data if not yet loaded,
 * then adds that data to the wrapped component based on query parameters and
 * user information.
 */
function withWithholding<T extends WithWithholdingProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithWithholding = (
    props: Omit<T, "employer" | "withholding"> & {
      query: QueryForWithWithholding;
    }
  ) => {
    const { appLogic, query, user } = props;
    const { t } = useTranslation();
    const [shouldLoadWithholding, setShouldLoadWithholding] = useState(true);
    const [withholding, setWithholding] = useState<Withholding>();

    const employer = user.user_leave_administrators.find((employer) => {
      return employer.employer_id === query.employer_id;
    });

    useEffect(() => {
      if (!employer) return;

      if (employer.verified) {
        appLogic.portalFlow.goTo(routes.employers.verificationSuccess, {
          employer_id: query.employer_id,
        });
      } else {
        const loadWithholding = async () => {
          const data = await appLogic.employers.loadWithholding(
            employer.employer_id
          );
          setShouldLoadWithholding(false);
          setWithholding(data);
        };

        if (shouldLoadWithholding) {
          loadWithholding();
        }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [withholding, employer]);

    if (!employer) {
      return <PageNotFound />;
    }

    return (
      <React.Fragment>
        {!withholding && shouldLoadWithholding && (
          <div className="margin-top-8 text-center">
            <Spinner aria-label={t("components.spinner.label")} />
          </div>
        )}
        {withholding && (
          <Component
            {...(props as T & { query: QueryForWithWithholding })}
            employer={employer}
            withholding={withholding}
          />
        )}
      </React.Fragment>
    );
  };

  return withUser(ComponentWithWithholding);
}

export default withWithholding;
