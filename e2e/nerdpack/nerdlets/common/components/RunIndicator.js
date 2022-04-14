import {
  BlockText,
  Card,
  CardBody,
  HeadingText,
  Link,
  navigation,
  Popover,
  PopoverBody,
  PopoverFooter,
  PopoverTrigger,
} from "nr1";
import { format } from "date-fns";
import React from "react";
import { GROUPS } from "../index";

function getPercent(group) {
  return Math.round((group.passCount / group.total) * 100);
}

export function RunIndicator({ run, simpleView = true }) {
  /**
   * Turn groups into an object for status per group
   * @type {stable: string, unstable: string, morning: string, integration: string}
   */
  const status = GROUPS.reduce((obj, group) => {
    return { ...obj, [group.toLowerCase()]: "none" };
  }, {});

  /**
   * Process status and calculate percentage passed
   */
  Object.keys(status).forEach((key) => {
    key = key.toLowerCase();
    if (run[key].total > 0) {
      run[key].percent = getPercent(run[key]);
      if (run[key].percent === 100) {
        status[key] = "ok";
      } else if (key !== "integration" && run[key].percent >= 85) {
        status[key] = "warn";
      } else {
        status[key] = "error";
      }
    }
  });

  const runIds = run.runId.includes("-failed-specs")
    ? [run.runId, run.runId.replace("-failed-specs", "")]
    : [run.runId];
  /**
   * Generate Nerdlet link for testgrid view.
   */
  const link = navigation.getOpenStackedNerdletLocation({
    id: "panel-testgrid",
    urlState: { runIds: runIds },
  });
  return (
    <Popover openOnHover={true}>
      <PopoverTrigger>
        {status?.targeted != "none" ? (
          <Link
            to={link}
            className={`RunIndicator ${status.targeted} targeted`}
          >
            <span className={"visually-hidden"}>{status.targeted}</span>
            {run.targeted.percent}
            {simpleView === false && (
              <span className={"bubbles"}>
                <span
                  className={`bubble integration ${status.integration}`}
                ></span>
              </span>
            )}
          </Link>
        ) : (
          <Link to={link} className={`RunIndicator ${status.stable}`}>
            <span className={"visually-hidden"}>{status.stable}</span>
            {run.stable.percent}
            {simpleView === false && (
              <span className={"bubbles"}>
                <span
                  className={`bubble integration ${status.integration}`}
                ></span>
                <span className={`bubble morning ${status.morning}`}></span>
                <span className={`bubble unstable ${status.unstable}`}></span>
              </span>
            )}
          </Link>
        )}
      </PopoverTrigger>
      <PopoverBody>
        <Card style={{ width: "250px" }}>
          <CardBody>
            <HeadingText>{format(run.start, "PPpp")}</HeadingText>
            <BlockText
              spacingType={[
                BlockText.SPACING_TYPE.MEDIUM,
                BlockText.SPACING_TYPE.NONE,
              ]}
            >
              <div className={"runInfo"}>
                {Object.keys(status).map((key) => {
                  if (run[key].total > 0) {
                    return (
                      <div className={"group"}>
                        {key}: {run[key].passCount} / {run[key].total} (
                        {run[key].percent}
                        %)
                        {run.failCount > 0 && (
                          <span className={"errors"}>
                            {run[key].failCount} Errors
                          </span>
                        )}
                      </div>
                    );
                  }
                })}
                <code className={"tag"}>
                  {run.tag.filter(
                    (tag) => !tag.includes("Env-") && tag != "Deploy"
                  )}
                </code>
                <br />
                {run.branch !== "main" && (
                  <code className={"tag"}>{run.branch}</code>
                )}
              </div>
            </BlockText>
          </CardBody>
        </Card>
        <PopoverFooter style={{ textAlign: "right" }}>
          {run.stable?.runUrl && (
            <Link to={run.stable.runUrl}>View in Cypress</Link>
          )}
        </PopoverFooter>
      </PopoverBody>
    </Popover>
  );
}
