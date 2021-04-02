import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import User from "../models/User";
import routes from "../../src/routes";
import { useTranslation } from "../locales/i18n";

/**
 * Higher order component that loads withholding data if not yet loaded,
 * then adds that data to the wrapped component based on query parameters and
 * user information.
 * @param {React.Component} Component - Component to receive withholding data prop
 * @returns {React.Component} - Component with withholding data
 */
const withWithholding = (Component) => {
  const ComponentWithWithholding = (props) => {
    const { appLogic, query } = props;
    const {
      users: { user },
    } = appLogic;
    const { t } = useTranslation();
    const [shouldLoadWithholding, setShouldLoadWithholding] = useState(true);
    const [withholding, setWithholding] = useState();

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

  ComponentWithWithholding.propTypes = {
    appLogic: PropTypes.shape({
      employers: PropTypes.shape({
        loadWithholding: PropTypes.func.isRequired,
      }).isRequired,
      portalFlow: PropTypes.shape({
        goTo: PropTypes.func.isRequired,
      }).isRequired,
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
    }).isRequired,
    query: PropTypes.object.isRequired,
  };

  return ComponentWithWithholding;
};

export default withWithholding;
