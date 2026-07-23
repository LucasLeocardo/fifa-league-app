"use client";

import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from "@headlessui/react";

import type { SelectOption } from "@/components/Select";

type MultiSelectProps = {
  options: SelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  "aria-label"?: string;
};

function ChevronIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 20 20"
      className="pointer-events-none size-4 shrink-0 text-[var(--muted)] transition-transform ui-open:rotate-180"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
    >
      <path
        d="M6 8l4 4 4-4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 20 20"
      className="size-4 text-[var(--lime)]"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path d="M4 10l4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function MultiSelect({
  options,
  value,
  onChange,
  disabled = false,
  placeholder = "Selecione",
  className,
  "aria-label": ariaLabel,
}: Readonly<MultiSelectProps>) {
  const selectedLabels = options
    .filter((option) => value.includes(option.value))
    .map((option) => option.label);

  const buttonLabel =
    selectedLabels.length === 0
      ? placeholder
      : selectedLabels.length <= 3
        ? selectedLabels.join(", ")
        : `${selectedLabels.length} selecionadas`;

  return (
    <Listbox value={value} onChange={onChange} multiple disabled={disabled}>
      <div className={["relative", className ?? ""].join(" ").trim()}>
        <ListboxButton
          aria-label={ariaLabel}
          className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-lg border border-[var(--stroke)] bg-[rgba(10,32,58,0.55)] px-4 py-2.5 text-left text-sm text-[var(--ink)] transition-colors hover:border-[var(--lime)] focus:border-[var(--lime)] focus:outline-none focus:ring-2 focus:ring-[var(--lime)]/30 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <span className="block truncate">{buttonLabel}</span>
          <ChevronIcon />
        </ListboxButton>

        <ListboxOptions
          anchor="bottom start"
          transition
          className="z-50 mt-2 max-h-72 w-[var(--button-width)] overflow-auto rounded-lg border border-[var(--stroke)] bg-[rgba(6,22,42,0.98)] p-1 text-sm shadow-xl backdrop-blur transition duration-150 ease-out [--anchor-gap:0.25rem] focus:outline-none data-[closed]:-translate-y-1 data-[closed]:opacity-0"
        >
          {options.map((option) => (
            <ListboxOption
              key={option.value}
              value={option.value}
              className="flex cursor-pointer items-center justify-between gap-3 rounded-md px-3 py-2 text-[var(--ink)] transition-colors data-[focus]:bg-[var(--lime)]/10 data-[selected]:text-[var(--lime)]"
            >
              {({ selected: isSelected }) => (
                <>
                  <span className="block truncate">{option.label}</span>
                  {isSelected ? <CheckIcon /> : null}
                </>
              )}
            </ListboxOption>
          ))}
        </ListboxOptions>
      </div>
    </Listbox>
  );
}
