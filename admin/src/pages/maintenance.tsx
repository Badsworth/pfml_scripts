import "react-datetime/css/react-datetime.css";
//import { ApiResponse, FlagsResponse, getFlagsByNameLogs } from "../api";
import Link from "next/link";
import { Helmet } from "react-helmet-async";
import React from "react";
import Table from "../components/Table";
import Toggle from "../components/Toggle";
import moment from "moment";

export default function Maintenance() {
  const [maintenanceHistory, setMaintenanceHistory] = React.useState<
    MaintenanceHistory[]
  >([
    {
      enabled: true,
      start: "2021-06-17 18:00:00-04",
      end: "2021-06-17 17:00:00-04",
      options: {
        maintenanceName: "Fineos downtime two custom page routes",
        page_routes: ["/applications/*", "/test/", "/another/"],
      },
    },
    {
      enabled: true,
      start: "2021-06-17 18:00:00-04",
      end: "2021-06-17 17:00:00-04",
      options: {
        maintenanceName: "Fineos downtime two checked page routes",
        page_routes: ["/applications/*", "/employers/*", "/test/", "/another/"],
      },
    },
  ]);

  /*
  React.useEffect(() => {
    getFlagsByNameLogs({ name: "maintenance" }).then(
      (response: ApiResponse<FlagsResponse>) => {
        setMaintenanceHistory(response.data);
      },
    );
  });
  */

  type optionsObject = {
    maintenanceName?: string;
    page_routes?: string[];
  };

  type MaintenanceHistory = {
    enabled?: boolean;
    start?: string | null;
    end?: string | null;
    options?: optionsObject | null;
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
  const getName = (m: MaintenanceHistory) => <>{m?.options?.maintenanceName}</>;
  const getDuration = (m: MaintenanceHistory) => (
    <>
      {(m.start ? formatDateTime(m.start) : "No start provided") +
        " - " +
        (m.end ? formatDateTime(m.end) : "No end provided")}
    </>
  );
  const getCreatedBy = (m: MaintenanceHistory) => <>{"Admin"}</>;
  const getOptions = (m: MaintenanceHistory) => {
    const linkValues: { [key: string]: string | string[] } = {};
    linkValues.maintenance_name = m?.options?.maintenanceName ?? "";
    const page_routes = m?.options?.page_routes ?? [];
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
      <div className="maintenance-status">
        <div className="maintenance-status__text">
          <h2 className="maintenance-status__title">Maintenance</h2>
          <p className="maintenance-status__body">
            When maintenance is scheduled for the future, a maintenance banner
            is displayed to users in the portal on the top of the page. When
            maintenance is currently enabled, a maintenance page is displayed to
            users instead of the normal page content.
          </p>
        </div>
        <Toggle status={false} />
        <button type="button" className="btn">
          <Link
            href={{
              pathname: "/maintenance/add",
            }}
          >
            <a className="maintenance-status__a-config">
            </a>
          </Link>
        </button>
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
