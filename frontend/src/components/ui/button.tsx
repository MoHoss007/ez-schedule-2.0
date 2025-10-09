import React from "react";
export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
    const { className = "", ...rest } = props;
    return <button className={`rounded-2xl bg-white/10 px-3 py-2 hover:bg-white/20 ${className}`} {...rest} />;
}