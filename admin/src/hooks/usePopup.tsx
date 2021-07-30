import React, { ReactChild, ReactFragment, ReactPortal } from "react";
import { MouseEvent, useState } from "react";

export interface CommonProps<T> {
  isOpen: boolean;
  close: (event: MouseEvent) => void;
  open: (data?: T) => (event: MouseEvent) => void;
  data: T;
  children:
    | ((data?: T) => JSX.Element)
    | ReactChild
    | ReactFragment
    | ReactPortal;
}

// String Union helper
type Concat<S1 extends string, S2 extends string> = `${S1}${S2}`;
// Add any components' names here to allow type inference
type ComponentsAllowed = "SlideOut" | "ConfirmationDialog";
// The component's name will end with "Popup"
type ComponentsName = Concat<ComponentsAllowed, "Popup">;
// All possible components
type AllComponents<P> = {
  [Property in ComponentsName]?: React.ComponentType<P>;
};
// All methods named per component used
type AllMethods<T> = {
  [Property in keyof CommonProps<T> as Concat<
    Property,
    ComponentsAllowed
  >]?: CommonProps<T>[Property];
};
// Returns the component as "ComponentNamePopup"
// and methods like "openComponentName"
type PopupReturn<P, U> = AllComponents<P> & AllMethods<U>;

export default function usePopup<P, U = unknown>(
  Component: React.ComponentType<P>,
  props?: P & Partial<CommonProps<U>>,
): PopupReturn<P, U> {
  // console.log(P)
  // Whether Component is currently open or not
  const [isOpen, setIsOpen] = useState<boolean>(false);
  // Which data to render children with, optional
  const [data, setData] = useState<U>();
  // Standard closing onClick handler
  const close = (e: MouseEvent) => {
    e.preventDefault();
    if (typeof props?.close === "function") props?.close(e);
    setIsOpen(false);
  };
  // Standard opening onClick handler,
  // accepts new data before opening
  const open: CommonProps<U>["open"] = (componentData?: U) => {
    return (e: MouseEvent) => {
      e.preventDefault();
      if (typeof componentData !== "undefined") setData(componentData);
      if (typeof props?.open === "function") props?.open(componentData)(e);
      setIsOpen(true);
    };
  };
  // group all the extended functionality in extra props
  // order of props is very important here
  const extendedProps = { isOpen, data, ...props, open, close };
  // The component's name for the return object key naming
  const name: ComponentsAllowed = Component.name as ComponentsAllowed;
  return {
    ["data" + Component.name]: data,
    ["isOpen" + Component.name]: isOpen,
    ["close" + Component.name]: close,
    ["open" + Component.name]: open,
    [name + "Popup"]: (props: P) => {
      return <Component {...props} {...extendedProps} />;
    },
  };
}
