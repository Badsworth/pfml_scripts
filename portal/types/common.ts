export type Integer = number;

export type ISO8601Timestamp = string;

// Get the props for a React functional component. This is used for typing in places like
// Story's Args param: https://storybook.js.org/docs/react/writing-stories/args
// and our test suite
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Props<TComponent extends (props: any) => any> =
  Parameters<TComponent>[0];
