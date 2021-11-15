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

type PopupReturn<P, U> = {
  data?: U;
  isOpen: boolean;
  close: CommonProps<U>["close"];
  open: CommonProps<U>["open"];
  Popup: (props: P) => JSX.Element;
};

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
  return {
    data: data,
    isOpen: isOpen,
    close: close,
    open: open,
    Popup: (props: P) => {
      return <Component {...props} {...extendedProps} />;
    },
  };
}
