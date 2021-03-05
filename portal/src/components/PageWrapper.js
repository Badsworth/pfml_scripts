import ErrorBoundary from "./ErrorBoundary";
import ErrorsSummary from "./ErrorsSummary";
import Header from "./Header";
import { Helmet } from "react-helmet";
import PropTypes from "prop-types";
import React from "react";
import Spinner from "../components/Spinner";
import dynamic from "next/dynamic";
import { isFeatureEnabled } from "../services/featureFlags";
import { useTranslation } from "../locales/i18n";

// Lazy-loaded components
// https://nextjs.org/docs/advanced-features/dynamic-import
const Footer = dynamic(() => import("./Footer"));
const MaintenanceTakeover = dynamic(() => import("./MaintenanceTakeover"));

/**
 * This component renders the global page elements, such as header/footer, site-level
 * error alert, and maintenance page when enabled. Every page on the site is rendered
 * with this component as its parent.
 */
const PageWrapper = (props) => {
  const {
    appLogic,
    isLoading,
    maintenancePageRoutes,
    maintenanceRemovalDayAndTime,
  } = props;
  const { t } = useTranslation();

  /**
   * What to show to the user within our page wrapper. Depends on
   * the state of our app, such as loading state and feature flags.
   * @type {React.ElementType}
   */
  let pageBody;

  /**
   * Should this page display a maintenance message instead of its normal content?
   * @type {boolean}
   */
  const showMaintenancePageBody =
    maintenancePageRoutes &&
    // includes specific page? (pathname doesn't include a trailing slash):
    (maintenancePageRoutes.includes(appLogic.portalFlow.pathname) ||
      // or pages matching a wildcard? (e.g /applications/* or /* for site-wide):
      maintenancePageRoutes.some(
        (maintenancePageRoute) =>
          maintenancePageRoute.endsWith("*") &&
          appLogic.portalFlow.pathname.startsWith(
            maintenancePageRoute.split("*")[0]
          )
      ));

  // Prevent site from being rendered if this feature flag isn't enabled.
  // We render a vague but recognizable message that serves as an indicator
  // to folks who are aware, that the site is working as expected and they
  // need to enable the feature flag.
  // See: https://lwd.atlassian.net/browse/CP-459
  if (!isFeatureEnabled("pfmlTerriyay")) return <code>Hello world (◕‿◕)</code>;

  if (isLoading) {
    pageBody = (
      <section id="page" className="margin-top-8 text-center">
        <Spinner aria-valuetext={t("components.spinner.label")} />
      </section>
    );
  } else if (showMaintenancePageBody && !isFeatureEnabled("noMaintenance")) {
    pageBody = (
      <section id="page" data-test="maintenance page">
        <MaintenanceTakeover
          scheduledRemovalDayAndTimeText={maintenanceRemovalDayAndTime}
        />
      </section>
    );
  } else {
    pageBody = <section id="page">{props.children}</section>;
  }

  return (
    <ErrorBoundary>
      <Helmet>
        {/* <title> is controlled through rendering a <Title> component on each page */}
        <meta name="description" content={t("pages.app.seoDescription")} />
      </Helmet>
      <div className="l-container">
        <div>
          {/* Wrap header children in a div because its parent is a flex container */}
          <Header user={appLogic.users.user} onLogout={appLogic.auth.logout} />
        </div>
        <main
          id="main"
          className="l-main grid-container margin-top-5 margin-bottom-8"
        >
          <div className="grid-row">
            <div className="grid-col-fill">
              {/* Include a second ErrorBoundary here so that we still render a site header if we catch an error before it bubbles up any further */}
              <ErrorBoundary>
                <ErrorsSummary errors={appLogic.appErrors} />
                {pageBody}
              </ErrorBoundary>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

PageWrapper.propTypes = {
  appLogic: PropTypes.object.isRequired,
  /** Page body */
  children: PropTypes.node.isRequired,
  /** Is this page changing or in process of loading? */
  isLoading: PropTypes.bool,
  /** Page routes that should render a maintenance page */
  maintenancePageRoutes: PropTypes.arrayOf(PropTypes.string),
  /** User friendly date and time when the maintenance page will be removed */
  maintenanceRemovalDayAndTime: PropTypes.string,
};

export default PageWrapper;
