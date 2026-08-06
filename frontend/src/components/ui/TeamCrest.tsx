"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";
import { initials } from "@/lib/utils";

/**
 * Team crest image with a graceful initials fallback when the URL is missing or
 * fails to load. Plain <img> is used so crests from any host work without image
 * optimization config.
 */
export function TeamCrest({
  name,
  src,
  size = 24,
  className,
}: {
  name: string;
  src?: string | null;
  size?: number;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  const showImage = src && !failed;

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-border/50 text-[10px] font-semibold text-muted",
        className,
      )}
      style={{ width: size, height: size }}
    >
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={`${name} crest`}
          width={size}
          height={size}
          loading="lazy"
          className="h-full w-full object-contain"
          onError={() => setFailed(true)}
        />
      ) : (
        <span aria-hidden="true">{initials(name)}</span>
      )}
    </span>
  );
}
