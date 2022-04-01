import "react-datetime/css/react-datetime.css";
import ActionMenu from "../components/ActionMenu";
import {
  ApiResponse,
  Flag,
  FlagWithLog,
  GETAdminFlagLogsByNameResponse,
  getAdminFlagLogsByName,
  patchAdminFlagsByName,
} from "../api";
import Alert from "../components/Alert";
import ConfirmationDialog from "../components/ConfirmationDialog";
import { Helmet } from "react-helmet-async";
import Link from "next/link";
import React from "react";
import { StaticPropsPermissions } from "../menus";
import Table from "../components/Table";
import Toggle from "../components/Toggle";
import moment from "moment-timezone";
import { useRouter } from "next/router";

export const Timezone = "America/New_York";
export const TimezoneAbbr = moment().tz(Timezone).zoneAbbr();

export default function Maintenance() {
  const [maintenanceHistory, setMaintenanceHistory] = React.useState<
    FlagWithLog[]
  >([]);
  const [maintenance, setMaintenance] = React.useState<Flag | null>(null);

  const router = useRouter();

  const [showConfirmationDialog, setShowConfirmationDialog] =
    React.useState(false);

  React.useEffect(() => {
    getAdminFlagLogsByName({ name: "maintenance" }).then(
      (response: ApiResponse<GETAdminFlagLogsByNameResponse>) => {
        // The stubbed API endpoint returns an object unfortunately. It will
        // be an array once the endpoint is updated.
        const logs = Array.isArray(response.data) ? response.data : [];
        setMaintenance(logs.shift() || null);
        setMaintenanceHistory(logs);
      },
    );
  }, [showConfirmationDialog]);

  type options = {
    name?: string;
  };

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = async () => {
    // disable at API.
    if (maintenance) {
      await patchAdminFlagsByName({ name: "maintenance" }, { enabled: false });
      setShowConfirmationDialog(false);
    }
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
  const getName = (m: Flag) => <>{(m?.options as options)?.name}</>;
  const getEnabled = (m: Flag) => (m?.enabled ? "True" : "False");
  const getDuration = (m: Flag) => (
    <>
      {(m.start ? formatHistoryDateTime(m.start) : "No start provided") +
        " - " +
        (m.end ? formatHistoryDateTime(m.end) : "No end provided")}
    </>
  );

  const getCreatedBy = (m: FlagWithLog) => (
    <>
      {m.first_name} {m.last_name}
    </>
  );

  const getCreatedAt = (m: FlagWithLog) =>
    moment.tz(m.updated_at, Timezone).format("YYYY-MM-DD HH:mm:ss z");

  const getLinkOptions = (
    m: Flag | null,
    includeDateTimes: boolean,
  ): { [key: string]: string | string[] } => {
    const linkValues: { [key: string]: string | string[] } = {};
    if (!m) {
      return linkValues;
    }
    linkValues.name = (m?.options as options)?.name ?? "";
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

  const getOptions = (m: Flag) => {
    return (
      <>
        <Link
          href={{
            pathname: "/maintenance/add",
            query: {
              ...getLinkOptions(m, false),
              action:
                "Clone " + ((m?.options as options)?.name || "Maintenance"),
            },
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
                href: {
                  pathname: "/maintenance/add",
                  query: { action: "Configure New Maintenance" },
                },
                text: "Configure",
                type: "link",
              },
              {
                enabled: getMaintenanceEnabled(),
                href: {
                  pathname: "/maintenance/add",
                  query: {
                    ...getLinkOptions(maintenance, true),
                    action: "Edit Maintenance",
                  },
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
            title: "Enabled",
            content: getEnabled,
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
            title: "Created at",
            content: getCreatedAt,
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
