"use client";

import { useState } from "react";

/** Interactive 0.5–5 star rating with half steps. */
export default function StarRating({
  value,
  onChange,
  readOnly = false,
}: {
  value: number | null;
  onChange?: (value: number) => void;
  readOnly?: boolean;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const shown = hover ?? value ?? 0;

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => {
        const full = shown >= star;
        const half = !full && shown >= star - 0.5;
        return (
          <span key={star} className="relative inline-block h-6 w-6 leading-none">
            <span className="absolute inset-0 text-2xl text-white/20">★</span>
            {(full || half) && (
              <span
                className="absolute inset-0 overflow-hidden text-2xl text-orange-400"
                style={{ width: half ? "50%" : "100%" }}
              >
                ★
              </span>
            )}
            {!readOnly && (
              <>
                <button
                  type="button"
                  aria-label={`${star - 0.5} stars`}
                  className="absolute inset-y-0 left-0 w-1/2 cursor-pointer"
                  onMouseEnter={() => setHover(star - 0.5)}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => onChange?.(star - 0.5)}
                />
                <button
                  type="button"
                  aria-label={`${star} stars`}
                  className="absolute inset-y-0 right-0 w-1/2 cursor-pointer"
                  onMouseEnter={() => setHover(star)}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => onChange?.(star)}
                />
              </>
            )}
          </span>
        );
      })}
    </div>
  );
}
