import React, { useEffect, useState } from "react";
import { AppLogic } from "../hooks/useAppLogic";
import Spinner from "../components/Spinner";
import Withholding from "../models/Withholding";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface ComponentWithWithholdingProps {
  appLogic: AppLogic;
  query: {
    employer_id: string;
  };
}

/**
 * Higher order component that loads withholding data if not yet loaded,
 * then adds that data to the wrapped component based on query parameters and
 * user information.
 * @param {React.Component} Component - Component to receive withholding data prop
 * @returns {React.Component} - Component with withholding data
 */
const withWithholding = (Component) => {
  const ComponentWithWithholding = (props: ComponentWithWithholdingProps) => {
    const { appLogic, query } = props;
    const {
      users: { user },
    } = appLogic;
    const { t } = useTranslation();
    const [shouldLoadWithholding, setShouldLoadWithholding] = useState(true);
    const [withholding, setWithholding] = useState<Withholding>();

    const employer = user.user_leave_administrators.find((employer) => {
      return employer.employer_id === query.employer_id;
    });

    useEffect(() => {
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

    return (
      <React.Fragment>
        {!withholding && shouldLoadWithholding && (
          <div className="margin-top-8 text-center">
            <Spinner aria-valuetext={t("components.spinner.label")} />
          </div>
        )}
        {withholding && <Component {...props} withholding={withholding} />}
      </React.Fragment>
    );
  };

  return ComponentWithWithholding;
};

export default withWithholding;
