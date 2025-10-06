import React from "react";
export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
    const { className = "", ...rest } = props;
    return <input className={`w-full rounded-md bg-neutral-800 p-2 ${className}`} {...rest} />;
}