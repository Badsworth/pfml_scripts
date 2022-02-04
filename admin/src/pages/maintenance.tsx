import "react-datetime/css/react-datetime.css";
import {
  ApiResponse,
  Flag,
  FlagLog,
  FlagLogsResponse,
  FlagsResponse,
  getFlagsLogsByName,
  getFlagsByName,
  postFlagsByName,
} from "../api";
import Alert from "../components/Alert";
import ConfirmationDialog from "../components/ConfirmationDialog";
import Link from "next/link";
import { Helmet } from "react-helmet-async";
import { useRouter } from "next/router";
import React from "react";
import Table from "../components/Table";
import Toggle from "../components/Toggle";
import ActionMenu from "../components/ActionMenu";
import { StaticPropsPermissions } from "../menus";
import moment from "moment-timezone";

export const Timezone = "America/New_York";
export const TimezoneAbbr = moment().tz(Timezone).zoneAbbr();

export default function Maintenance() {
<<<<<<< HEAD
  const [maintenanceHistory, setMaintenanceHistory] =
    React.useState<FlagLogsResponse>([]);
  const [maintenance, setMaintenance] = React.useState<Flag | null>(null);

  const [showConfirmationDialog, setShowConfirmationDialog] =
    React.useState(false);
=======
  const router = useRouter();

  // Remove when Flag is in ../../api.
  interface Flag {
    start?: string | null;
    end?: string | null;
    name?: string;
    options?: object;
    enabled?: boolean;
  }
  type FlagsResponse = Flag[];

  const [showConfirmationDialog, setShowConfirmationDialog] =
    React.useState(false);
  const [maintenanceHistory, setMaintenanceHistory] =
    React.useState<FlagsResponse>([
      {
        enabled: true,
        end: "2022-01-23 18:00:00-04",
        name: "maintenance",
        options: {
          name: "Two checked page routes, one custom",
          page_routes: ["/*", "/applications/*", "/custom/*"],
        },
        start: "2022-01-23 17:00:00-04",
      },
    ]);
  const [maintenance, setMaintenance] = React.useState<Flag | null>({
    enabled: true,
    end: "2022-01-23 18:00:00-04",
    name: "maintenance",
    options: {
      name: "Current maintenance status",
      page_routes: ["/*", "/applications/*", "/custom/*"],
    },
    start: "2022-01-23 17:00:00-04",
  });
>>>>>>> origin/main

  React.useEffect(() => {
    getFlagsByName({ name: "maintenance" }).then(
      (response: ApiResponse<Flag>) => {
        setMaintenance(response.data);
      },
    );
    getFlagsLogsByName({ name: "maintenance" }).then(
      (response: ApiResponse<FlagLogsResponse>) => {
        setMaintenanceHistory(response.data);
      },
    );
  }, []);

  type options = {
    name?: string;
    page_routes?: string[];
  };

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = async () => {
    // disable at API.
    if (maintenance) {
      const response = await postFlagsByName(
        { name: "maintenance" },
        { enabled: false },
      );
      // TODO error check.
      setMaintenance({ enabled: false });
      setShowConfirmationDialog(false);
    }
  };

  const checked_page_routes: { [key: string]: string } = {
    "Entire Site": "/*",
    Applications: "/applications/*",
    Employers: "/employers/*",
    "Create Account": "/*create-account",
    Login: "/login",
  };

  // Functions to format table.
  const formatCurrentDateTime = (datetime: string) => {
    return (
      moment.tz(datetime, Timezone).format("MMMM DD, YYYY h:mmA") +
      " " +
      TimezoneAbbr
    );
  };

  const formatHistoryDateTime = (datetime: string) => {
    return (
      moment.tz(datetime, Timezone).format("MM/DD/YY hh:mmA") +
      " " +
      TimezoneAbbr
    );
  };
  const getName = (m: FlagLog) => <>{(m?.options as options)?.name}</>;
  const getDuration = (m: FlagLog) => (
    <>
      {(m.start ? formatHistoryDateTime(m.start) : "No start provided") +
        " - " +
        (m.end ? formatHistoryDateTime(m.end) : "No end provided")}
    </>
  );
<<<<<<< HEAD
  const getPageRoutes = (m: FlagLog) => {
=======

  const getPageRoutes = (m: Flag) => {
>>>>>>> origin/main
    const routes = (m?.options as options)?.page_routes ?? [];

    return (
      <ul className="maintenance-configure__page-routes">
        {routes.map((route, index) => {
          const label =
            Object.keys(checked_page_routes).find(
              (k) => checked_page_routes[k] === route,
            ) || "Custom";
          return (
            <li key={index}>
              {label}: <code>{route}</code>
            </li>
          );
        })}
      </ul>
    );
  };
<<<<<<< HEAD
  const getCreatedBy = (m: FlagLog) => (
    <>
      {m.family_name} {m.given_name}
    </>
  );

  const getMaintenanceLinkValues = (m: Flag) => {
    const linkValues: { [key: string]: string | string[] } = {};
    linkValues.name = (m?.options as options)?.name ?? "";

    const page_routes =
      ((m?.options as options)?.page_routes as string[]) ?? [];
    linkValues.checked_page_routes = page_routes.filter((item) =>
      checkedValues.includes(item),
    );
    linkValues.custom_page_routes = page_routes.filter(
      (item) => !checkedValues.includes(item),
    );
    return linkValues;
  };

  const getOptions = (m: FlagLog) => {
=======

  const getLinkOptions = (
    m: Flag | null,
    includeDateTimes: boolean,
  ): { [key: string]: string | string[] } => {
>>>>>>> origin/main
    const linkValues: { [key: string]: string | string[] } = {};
    if (!m) {
      return linkValues;
    }
    linkValues.name = (m?.options as options)?.name ?? "";
    const page_routes =
      ((m?.options as options)?.page_routes as string[]) ?? [];
    linkValues.checked_page_routes = page_routes.filter((item) =>
      Object.values(checked_page_routes).includes(item),
    );
    linkValues.custom_page_routes = page_routes.filter(
      (item) => !Object.values(checked_page_routes).includes(item),
    );
    if (!includeDateTimes) {
      return linkValues;
    }
    linkValues.start = m.start
      ? moment.tz(m.start, Timezone).format("YYYY-MM-DD HH:mm:ss z")
      : "";
    linkValues.end = m.end
      ? moment.tz(m.end, Timezone).format("YYYY-MM-DD HH:mm:ss z")
      : "";
    return linkValues;
  };

  const getCreatedBy = (m: Flag) => <>{"Admin"}</>;

  const getOptions = (m: Flag) => {
    const linkValues = getLinkOptions(m, false);
    return (
      <>
        <Link
          href={{
            pathname: "/maintenance/add",
            query: getMaintenanceLinkValues(m),
          }}
        >
          <a>Clone</a>
        </Link>
      </>
    );
  };

  const getMaintenanceEnabled = (): boolean => {
    return maintenance ? maintenance.enabled ?? false : false;
  };

  return (
    <>
      <Helmet>
        <title>Maintenance</title>
      </Helmet>

      <h1>Maintenance</h1>
      {router.query?.saved && (
        <Alert type="success" closeable={true}>
          Changes to Maintenance have been saved.
        </Alert>
      )}

      <div className="maintenance">
        <div className="maintenance-info">
          <div className="maintenance-info__text">
            <h2 className="maintenance-info__title">Maintenance</h2>
            <Toggle status={getMaintenanceEnabled()} />
            <p className="maintenance-info__body">
              When maintenance is scheduled for the future, a maintenance banner
              is displayed to users in the portal on the top of the page. When
              maintenance is currently enabled, a maintenance page is displayed
              to users instead of the normal page content.
            </p>
          </div>
          <ActionMenu
            options={[
              {
                enabled: !getMaintenanceEnabled(),
                href: "/maintenance/add",
                text: "Configure",
                type: "link",
              },
              {
                enabled: getMaintenanceEnabled(),
<<<<<<< HEAD
                // Add query params including start and end.
                href: {
                  pathname: "/maintenance/add",
                  query: maintenance
                    ? getMaintenanceLinkValues(maintenance)
                    : undefined,
=======
                href: {
                  pathname: "/maintenance/add",
                  query: getLinkOptions(maintenance, true),
>>>>>>> origin/main
                },
                text: "Edit",
                type: "link",
              },
              {
                enabled: getMaintenanceEnabled(),
                onClick: () => setShowConfirmationDialog(true),
                text: "Turn Off",
                type: "button",
              },
            ]}
          />
        </div>
        {showConfirmationDialog && (
          <ConfirmationDialog
            title="Turn off Maintenance"
            body="If maintenance is turned off, the maintenance takeover component will no longer be shown in the portal. The change may take up to 5 minutes for some users due to browser cache."
            handleCancelCallback={confirmationDialogCancelCallback}
            handleContinueCallback={confirmationDialogContinueCallback}
          />
        )}
        {maintenance && (maintenance.enabled ?? false) && (
          <div className="maintenance-status">
            <div className="maintenance-status__row">
              <div className="maintenance-status__label">Name</div>
              <div className="maintenance-status__value">
                {getName(maintenance)}
              </div>
            </div>
            <div className="maintenance-status__row">
              <div className="maintenance-status__label">Created By</div>
              <div className="maintenance-status__value">
                {getCreatedBy(maintenance)}
              </div>
            </div>
            <div className="maintenance-status__row">
              <div className="maintenance-status__label">Duration</div>
              <div className="maintenance-status__value">
                {maintenance && (
                  <>
                    {(maintenance.start
                      ? formatCurrentDateTime(maintenance.start)
                      : "No start provided") +
                      " to " +
                      (maintenance.end
                        ? formatCurrentDateTime(maintenance.end)
                        : "No end provided")}
                  </>
                )}
              </div>
            </div>
            <div className="maintenance-status__row">
              <div className="maintenance-status__label">Page Routes</div>
              <div className="maintenance-status__value">
                {getPageRoutes(maintenance)}
              </div>
            </div>
          </div>
        )}
      </div>

      <h2>History</h2>
      <Table
        rows={maintenanceHistory}
        cols={[
          {
            title: "Name",
            content: getName,
          },
          {
            title: "Duration",
            content: getDuration,
          },
          {
            title: "Created By",
            content: getCreatedBy,
          },
          {
            title: "",
            content: getOptions,
          },
        ]}
      />
    </>
  );
}

export async function getStaticProps(): Promise<StaticPropsPermissions> {
  return {
    props: {
      permissions: ["MAINTENANCE_READ"],
    },
  };
}
