import { DateTime } from "luxon";
import ErrorBoundary from "./ErrorBoundary";
import ErrorsSummary from "./ErrorsSummary";
import Header from "./Header";
import { Helmet } from "react-helmet";
import PropTypes from "prop-types";
import React from "react";
import Spinner from "../components/Spinner";
import UpcomingMaintenanceBanner from "../components/UpcomingMaintenanceBanner";
import dynamic from "next/dynamic";
import { isFeatureEnabled } from "../services/featureFlags";
import { useTranslation } from "../locales/i18n";

// Lazy-loaded components
// https://nextjs.org/docs/advanced-features/dynamic-import
const Footer = dynamic(() => import("./Footer"));
const MaintenanceTakeover = dynamic(() => import("./MaintenanceTakeover"));

/**
 * @param {string} [start] - ISO 8601 date time
 * @param {string} [end] - ISO 8601 date time
 * @returns {boolean}
 */
const isInMaintenanceWindow = (start, end) => {
  // If no time frame is set, the maintenance window is considered
  // always open (when maintenance mode is On)
  if (!start && !end) return true;

  const now = DateTime.local();
  const isAfterStart = start ? now >= DateTime.fromISO(start) : true;
  const isBeforeEnd = end ? now < DateTime.fromISO(end) : true;

  return isAfterStart && isBeforeEnd;
};

/**
 * @param {string} [start] - ISO 8601 date time
 * @param {string} [end] - ISO 8601 date time
 * @returns {boolean}
 */
 const isBeforeMaintenanceWindow = (start) => {
  const now = DateTime.local();
  const isBeforeStart = start ? now < DateTime.fromISO(start) : true;

  return isBeforeStart;
};

/**
 * Check if a page route should include the maintenance message
 * @param {string[]} maintenancePageRoutes - routes to apply maintenance message to
 * @param {string} pathname - current page's path
 * @returns {boolean}
 */
const isMaintenancePageRoute = (maintenancePageRoutes, pathname) => {
  return (
    maintenancePageRoutes &&
    // includes specific page? (pathname doesn't include a trailing slash):
    (maintenancePageRoutes.includes(pathname) ||
      // or pages matching a wildcard? (e.g /applications/* or /* for site-wide):
      maintenancePageRoutes.some(
        (maintenancePageRoute) =>
          maintenancePageRoute.endsWith("*") &&
          pathname.startsWith(maintenancePageRoute.split("*")[0])
      ))
  );
};

/**
 * This component renders the global page elements, such as header/footer, site-level
 * error alert, and maintenance page when enabled. Every page on the site is rendered
 * with this component as its parent.
 */
const PageWrapper = (props) => {
  const {
    appLogic,
    isLoading,
    maintenance
  } = props;
  const { t } = useTranslation();

  const maintenancePageRoutes = maintenance.options.page_routes;
  const maintenanceStart = maintenance.start;
  const maintenanceEnd = maintenance.end;
  const maintenanceEnabled = maintenance.enabled;

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
    isMaintenancePageRoute(
      maintenancePageRoutes,
      appLogic.portalFlow.pathname
    ) && isInMaintenanceWindow(maintenanceStart, maintenanceEnd);

  // User-friendly representation of the maintenance times
  const maintenanceStartTime = maintenanceStart
    ? DateTime.fromISO(maintenanceStart).toLocaleString(DateTime.DATETIME_FULL)
    : null;

  const maintenanceEndTime = maintenanceEnd
    ? DateTime.fromISO(maintenanceEnd).toLocaleString(DateTime.DATETIME_FULL)
    : null;

  /**
   * Should this page display an upcoming maintenance banner?
   * @type {boolean}
   */
  const showUpcomingMaintenanceBanner = isBeforeMaintenanceWindow(maintenanceStart) && maintenanceEnabled;

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
  } else if (showMaintenancePageBody && maintenance.enabled) {
    pageBody = (
      <section id="page" data-test="maintenance page">
        <MaintenanceTakeover
          scheduledRemovalDayAndTimeText={maintenanceEndTime}
        />
      </section>
    );
  } else {
    pageBody = (
      <section id="page">
        {(showUpcomingMaintenanceBanner) ? <UpcomingMaintenanceBanner start={maintenanceStartTime} end={maintenanceEndTime} /> : ''}
        {props.children}
      </section>
    );
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
  /** Maintenance feature flag data */
  maintenance: PropTypes.object,
  /** Page routes that should render a maintenance page */
  maintenancePageRoutes: PropTypes.arrayOf(PropTypes.string),
  /** ISO 8601 date time for maintenance window start */
  maintenanceStart: PropTypes.string,
  /** ISO 8601 date time for maintenance window end */
  maintenanceEnd: PropTypes.string,
};

export default PageWrapper;
