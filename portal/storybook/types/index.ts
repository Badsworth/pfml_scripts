/* eslint-disable @typescript-eslint/no-explicit-any */

// Get the props for a React functional component. This is for typing the
// Story's Args param: https://storybook.js.org/docs/react/writing-stories/args
export type Props<TComponent extends (props: any) => any> =
  Parameters<TComponent>[0];
