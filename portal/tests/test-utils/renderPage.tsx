import { AppLogic } from "../../src/hooks/useAppLogic";
import React from "react";
import { render } from "@testing-library/react";
import useMockableAppLogic from "../../lib/mock-helpers/useMockableAppLogic";

type AddCustomSetup = (appLogic: AppLogic) => void;
// renderPage doesn't technically care what props the page takes
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type PageComponentProps = any;

function PageWithAppLogic({
  PageComponent,
  addCustomSetup,
  isLoggedIn = true,
  ...props
}: {
  [propName: string]: unknown;
  PageComponent: React.ComponentType<PageComponentProps>;
  addCustomSetup?: AddCustomSetup;
  isLoggedIn?: boolean;
}) {
  const appLogic = useMockableAppLogic(
    {
      // Our tests instead use addCustomSetup in order to mock appLogic properties,
      // since we often want to use jest.spyOn.
    },
    { isLoggedIn }
  );

  if (addCustomSetup) {
    addCustomSetup(appLogic);
  }

  return <PageComponent appLogic={appLogic} {...props} />;
}

/**
 * @param PageComponent - A function that returns React Component to be rendered
 * @param options - An object of custom options to pass through to the component
 * @param options.addCustomSetup - Function that receives appLogic as a param, used to customize appLogic setup
 * @param options.isLoggedIn - Boolean flag to specify whether or not to authenticate user
 * @param props - For any additional arbitrary props
 *
 * @returns RTL render function result: https://testing-library.com/docs/react-testing-library/api#render-result
 */
export function renderPage(
  PageComponent: React.ComponentType<PageComponentProps>,
  options: {
    addCustomSetup?: AddCustomSetup;
    isLoggedIn?: boolean;
  } = {},
  props: { [propName: string]: unknown } = {}
) {
  const component = (
    <PageWithAppLogic
      PageComponent={PageComponent}
      addCustomSetup={options.addCustomSetup}
      isLoggedIn={options.isLoggedIn}
      {...props}
    />
  );

  return render(component);
}
