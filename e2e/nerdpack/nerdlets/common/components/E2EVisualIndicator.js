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

/**
 * @deprecated
 */
export function E2EVisualIndicator({ run, runId, simpleView = true }) {
  let state = "error";
  let morning_state = "none";
  let unstable_state = "none";
  let integration_state = "none";
  if (run.passPercent === 100) {
    state = "ok";
  } else if (run.passPercent >= 85) {
    state = "warn";
  }

  if (run.integration.total > 0) {
    if (run.integration.passPercent === 100) {
      integration_state = "ok";
    } else if (run.integration.passPercent >= 85) {
      integration_state = "warn";
    } else {
      integration_state = "error";
    }
  }

  if (run.morning.total > 0) {
    if (run.morning.passPercent === 100) {
      morning_state = "ok";
    } else if (run.morning.passPercent >= 85) {
      morning_state = "warn";
    } else {
      morning_state = "error";
    }
  }

  if (run.unstable.total > 0) {
    if (run.unstable.passPercent === 100) {
      unstable_state = "ok";
    } else if (run.unstable.passPercent >= 85) {
      unstable_state = "warn";
    } else {
      unstable_state = "error";
    }
  }

  const link = navigation.getOpenStackedNerdletLocation({
    id: "e2e-tests",
    urlState: { runIds: [runId] },
  });
  return (
    <Popover openOnHover={true}>
      <PopoverTrigger>
        <Link to={link} className={`e2e-run-indicator ${state}`}>
          <span className={"visually-hidden"}>{state}</span>
          {run.passPercent}
          {simpleView === false && (
            <span className={"bubbles"}>
              <span
                className={`bubble integration ${integration_state}`}
              ></span>
              <span className={`bubble morning ${morning_state}`}></span>
              <span className={`bubble unstable ${unstable_state}`}></span>
            </span>
          )}
        </Link>
      </PopoverTrigger>
      <PopoverBody>
        <Card style={{ width: "250px" }}>
          <CardBody>
            <HeadingText>{format(run.timestamp, "PPPppp")}</HeadingText>
            <BlockText
              spacingType={[
                BlockText.SPACING_TYPE.MEDIUM,
                BlockText.SPACING_TYPE.NONE,
              ]}
            >
              <div className={"runInfo"}>
                {run.total > 0 && (
                  <div className={"stable"}>
                    Stable: {run.passCount} / {run.total} ({run.passPercent}%)
                    {run.failCount > 0 && (
                      <span className={"errors"}>{run.failCount} Errors</span>
                    )}
                  </div>
                )}
                {run.integration.total > 0 && (
                  <div className={"integration"}>
                    Integration: {run.integration.passCount} /{" "}
                    {run.integration.total} ({run.integration.passPercent}%)
                    {run.integration.failCount > 0 && (
                      <span className={"errors"}>
                        {run.integration.failCount} Errors
                      </span>
                    )}
                  </div>
                )}
                {run.morning.total > 0 && (
                  <div className={"morning"}>
                    Morning: {run.morning.passCount} / {run.morning.total} (
                    {run.morning.passPercent}%)
                    {run.morning.failCount > 0 && (
                      <span className={"errors"}>
                        {run.morning.failCount} Errors
                      </span>
                    )}
                  </div>
                )}
                {run.unstable.total > 0 && (
                  <div className={"unstable"}>
                    Unstable: {run.unstable.passCount} / {run.unstable.total} (
                    {run.unstable.passPercent}%)
                    {run.unstable.failCount > 0 && (
                      <span className={"errors"}>
                        {run.unstable.failCount} Errors
                      </span>
                    )}
                  </div>
                )}
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
          <Link to={run.runUrl}>View in Cypress</Link>
        </PopoverFooter>
      </PopoverBody>
    </Popover>
  );
}
