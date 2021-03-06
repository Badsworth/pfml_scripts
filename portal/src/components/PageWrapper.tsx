import {
  isInMaintenanceWindow,
  isMaintenancePageRoute,
  isMaintenanceUpcoming,
  maintenanceTime,
} from "../utils/maintenance";
import { AppLogic } from "../hooks/useAppLogic";
import ErrorBoundary from "./ErrorBoundary";
import ErrorsSummary from "./ErrorsSummary";
import Flag from "../models/Flag";
import Header from "./Header";
import { Helmet } from "react-helmet";
import React from "react";
import Spinner from "./core/Spinner";
import dynamic from "next/dynamic";
import { get } from "lodash";
import { isFeatureEnabled } from "../services/featureFlags";
import { useTranslation } from "../locales/i18n";

// Lazy-loaded components
// https://nextjs.org/docs/advanced-features/dynamic-import
const Footer = dynamic(() => import("./Footer"));
const MaintenanceTakeover = dynamic(() => import("./MaintenanceTakeover"));

interface PageWrapperProps {
  appLogic: AppLogic;
  children: React.ReactNode;
  isLoading?: boolean;
  maintenance?: Flag;
}

/**
 * This component renders the global page elements, such as header/footer, site-level
 * error alert, and maintenance page when enabled. Every page on the site is rendered
 * with this component as its parent.
 */
const PageWrapper = (props: PageWrapperProps) => {
  const { appLogic, isLoading, maintenance } = props;
  const { t } = useTranslation();

  // If no page routes are specified, the entire site should be under maintenance.
  const maintenancePageRoutes = get(maintenance, "options.page_routes", ["/*"]);
  const maintenanceStart = maintenance?.start;
  const maintenanceEnd = maintenance?.end;
  const maintenanceEnabled = !!maintenance?.enabled;

  /**
   * What to show to the user within our page wrapper. Depends on
   * the state of our app, such as loading state and feature flags.
   * @type {React.ElementType}
   */
  let pageBody;

  /**
   * Should this page display the maintenance alert bar?
   * Only shows on routes that are included in maintenance page_routes
   * and if the current date/time is within 48 hours of the
   * maintenance start date/time
   * @type {boolean}
   */
  const showUpcomingMaintenanceAlertBar =
    (maintenanceEnabled &&
      maintenanceStart &&
      isMaintenancePageRoute(
        maintenancePageRoutes,
        appLogic.portalFlow.pathname
      ) &&
      isMaintenanceUpcoming(maintenanceStart, 2)) ||
    false;

  /**
   * Should this page display a maintenance message instead of its normal content?
   */
  const showMaintenancePageBody =
    maintenanceEnabled &&
    isMaintenancePageRoute(
      maintenancePageRoutes,
      appLogic.portalFlow.pathname
    ) &&
    isInMaintenanceWindow(maintenanceStart, maintenanceEnd);

  // User-friendly representation of the maintenance times
  const maintenanceStartTime = maintenanceTime(maintenanceStart);
  const maintenanceEndTime = maintenanceTime(maintenanceEnd);

  // Prevent site from being rendered if this feature flag isn't enabled.
  // We render a vague but recognizable message that serves as an indicator
  // to folks who are aware, that the site is working as expected and they
  // need to enable the feature flag.
  // See: https://lwd.atlassian.net/browse/CP-459
  if (!isFeatureEnabled("pfmlTerriyay")) return <code>Hello world (?????????)</code>;

  if (isLoading) {
    pageBody = (
      <section id="page" className="margin-top-8 text-center">
        <Spinner aria-label={t("components.spinner.label")} />
      </section>
    );
  } else if (showMaintenancePageBody && !isFeatureEnabled("noMaintenance")) {
    pageBody = (
      <section id="page">
        <MaintenanceTakeover
          maintenanceStartTime={maintenanceStartTime}
          maintenanceEndTime={maintenanceEndTime}
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
        <div data-testid="Header">
          {/* Wrap header children in a div because its parent is a flex container */}
          <Header
            user={appLogic.users.user}
            onLogout={() => appLogic.auth.logout()}
            showUpcomingMaintenanceAlertBar={showUpcomingMaintenanceAlertBar}
            maintenanceStartTime={maintenanceStartTime}
            maintenanceEndTime={maintenanceEndTime}
          />
        </div>
        <main
          id="main"
          className="l-main grid-container margin-top-5 margin-bottom-8"
        >
          <div className="grid-row">
            <div className="grid-col-fill">
              {/* Include a second ErrorBoundary here so that we still render a site header if we catch an error before it bubbles up any further */}
              <ErrorBoundary>
                <ErrorsSummary errors={appLogic.errors} />
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

export default PageWrapper;
