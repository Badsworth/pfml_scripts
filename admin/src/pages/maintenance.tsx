import "react-datetime/css/react-datetime.css";
import {
  ApiResponse,
  Flag,
  FlagsResponse,
  getFlagsByNameLogs,
  getFlagsByName,
} from "../api";
import Alert from "../components/Alert";
import Link from "next/link";
import { Helmet } from "react-helmet-async";
import React from "react";
import Table from "../components/Table";
import Toggle from "../components/Toggle";
import moment from "moment";

export default function Maintenance() {
  const [maintenanceHistory, setMaintenanceHistory] =
    React.useState<FlagsResponse>([]);
  const [maintenance, setMaintenance] = React.useState<Flag | null>(null);

  React.useEffect(() => {
    getFlagsByName({ name: "maintenance" }).then(
      (response: ApiResponse<Flag>) => {
        setMaintenance(response.data);
      },
    );
    getFlagsByNameLogs({ name: "maintenance" }).then(
      (response: ApiResponse<FlagsResponse>) => {
        setMaintenanceHistory(response.data);
      },
    );
  }, []);

  type optionsObject = {
    name?: string;
    page_routes?: string[];
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
  const getName = (m: Flag) => <>{(m?.options as optionsObject)?.name}</>;
  const getDuration = (m: Flag) => (
    <>
      {(m.start ? formatDateTime(m.start) : "No start provided") +
        " - " +
        (m.end ? formatDateTime(m.end) : "No end provided")}
    </>
  );
  const getPageRoutes = (m: Flag) => {
    const routes = (m?.options as optionsObject)?.page_routes ?? [];

    return routes.join(", ");
  };
  const getCreatedBy = (m: Flag) => <>{"Admin"}</>;
  const getOptions = (m: Flag) => {
    const linkValues: { [key: string]: string | string[] } = {};
    linkValues.name = (m?.options as optionsObject)?.name ?? "";
    const page_routes =
      ((m?.options as optionsObject)?.page_routes as string[]) ?? [];
    linkValues.checked_page_routes = page_routes.filter((item) =>
      checkedValues.includes(item),
    );
    linkValues.custom_page_routes = page_routes.filter(
      (item) => !checkedValues.includes(item),
    );
    return (
      <>
        <button type="button" className="btn">
          <Link
            href={{
              pathname: "/maintenance/add",
              query: linkValues,
            }}
          >
            <a>Clone</a>
          </Link>
        </button>
      </>
    );
  };

  return (
    <>
      <Helmet>
        <title>Maintenance</title>
        <link
          href="https://fonts.googleapis.com/icon?family=Material+Icons"
          rel="stylesheet"
        />
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
          <Toggle status={false} />
          <button type="button" className="btn">
            <Link
              href={{
                pathname: "/maintenance/add",
              }}
            >
              <a className="maintenance-info__a-config"></a>
            </Link>
          </button>
        </div>
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
