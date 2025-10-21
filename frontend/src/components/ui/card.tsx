import React from "react";
export function Card({ className = "", children }: any) { return <div className={`rounded-xl bg-neutral-900 ${className}`}>{children}</div>; }
export function CardContent({ className = "", children }: any) { return <div className={`p-6 ${className}`}>{children}</div>; }