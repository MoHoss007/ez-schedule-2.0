import React from "react";
export function Label({ className = "", children }: any) { return <label className={`mb-1 block text-sm ${className}`}>{children}</label>; }