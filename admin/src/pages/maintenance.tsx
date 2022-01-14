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
import React from "react";
import Table from "../components/Table";
import Toggle from "../components/Toggle";
import VerticalMenu from "../components/VerticalMenu";
import moment from "moment";
import { StaticPropsPermissions } from "../menus";

export default function Maintenance() {
  const [maintenanceHistory, setMaintenanceHistory] =
    React.useState<FlagLogsResponse>([]);
  const [maintenance, setMaintenance] = React.useState<Flag | null>(null);

  const [showConfirmationDialog, setShowConfirmationDialog] =
    React.useState(false);

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

  const checkedValues = [
    "/*",
    "/applications/*",
    "/employers/*",
    "/*create-account",
    "/login",
  ];

  // Functions to format table.
  const formatDateTime = (datetime: string) => {
    return moment(datetime).format("MM-DD-YY hh:mmA");
  };
  const getName = (m: FlagLog) => <>{(m?.options as options)?.name}</>;
  const getDuration = (m: FlagLog) => (
    <>
      {(m.start ? formatDateTime(m.start) : "No start provided") +
        " - " +
        (m.end ? formatDateTime(m.end) : "No end provided")}
    </>
  );
  const getPageRoutes = (m: FlagLog) => {
    const routes = (m?.options as options)?.page_routes ?? [];

    return routes.join(", ");
  };
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
      <Alert type="success" closeable={true}>
        Maintenance has been turned on.
      </Alert>
      <div className="maintenance">
        <div className="maintenance-info">
          <div className="maintenance-info__text">
            <h2 className="maintenance-info__title">Maintenance</h2>
            <p className="maintenance-info__body">
              When maintenance is scheduled for the future, a maintenance banner
              is displayed to users in the portal on the top of the page. When
              maintenance is currently enabled, a maintenance page is displayed
              to users instead of the normal page content.
            </p>
          </div>
          <Toggle status={getMaintenanceEnabled()} />
          <VerticalMenu
            options={[
              {
                enabled: !getMaintenanceEnabled(),
                href: "/maintenance/add",
                text: "Configure",
                type: "link",
              },
              {
                enabled: getMaintenanceEnabled(),
                // Add query params including start and end.
                href: "/maintenance/add",
                query: maintenance
                  ? getMaintenanceLinkValues(maintenance)
                  : undefined,
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
                {getDuration(maintenance)}
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
