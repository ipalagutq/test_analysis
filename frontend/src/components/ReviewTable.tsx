"use client";

import type { CatalogEntry, DraftRow, Flag, TestGroup } from "@/lib/api";

/** Local reviewer edit of one row; `value` is the raw input text. */
export interface RowEdit {
  code: string | null;
  value: string;
  include: boolean;
}

interface ReviewTableProps {
  rows: DraftRow[];
  edits: Record<number, RowEdit>;
  catalog: CatalogEntry[];
  invalidRowIds: number[];
  readOnly: boolean;
  onChange: (rowId: number, edit: RowEdit) => void;
}

const FLAG_LABELS: Record<Flag, string> = {
  low: "↓ ниже",
  normal: "норма",
  high: "↑ выше",
  unknown: "—",
};

const GROUP_LABELS: Record<TestGroup, string> = {
  cbc: "Общий анализ крови",
  biochem: "Биохимия",
};

/** Initial edit state from the server row. */
export function initialEdit(row: DraftRow): RowEdit {
  return {
    code: row.code,
    value: row.canonical_value === null ? "" : String(row.canonical_value),
    include: row.include,
  };
}

function isEdited(row: DraftRow, edit: RowEdit): boolean {
  const initial = initialEdit(row);
  return edit.code !== initial.code || edit.value !== initial.value;
}

/** Editable draft rows: code, canonical value and include; needs_review rows are highlighted. */
export default function ReviewTable({
  rows,
  edits,
  catalog,
  invalidRowIds,
  readOnly,
  onChange,
}: ReviewTableProps) {
  const unitByCode = new Map(catalog.map((entry) => [entry.code, entry.unit]));
  const groups = (Object.keys(GROUP_LABELS) as TestGroup[]).map((group) => ({
    group,
    entries: catalog.filter((entry) => entry.group === group),
  }));

  return (
    <table className="review-table">
      <thead>
        <tr>
          <th title="Записать строку в карту">В карту</th>
          <th>С бланка</th>
          <th>Показатель</th>
          <th>Значение</th>
          <th>Флаг</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const edit = edits[row.row_id] ?? initialEdit(row);
          const classes = [
            row.needs_review ? "needs-review" : "",
            invalidRowIds.includes(row.row_id) ? "invalid" : "",
            edit.include ? "" : "excluded",
          ].filter(Boolean);
          const unit = edit.code ? unitByCode.get(edit.code) : undefined;

          return (
            <tr key={row.row_id} className={classes.join(" ")}>
              <td>
                <input
                  type="checkbox"
                  aria-label={`Записать «${row.test_name_raw}» в карту`}
                  checked={edit.include}
                  disabled={readOnly}
                  onChange={(event) => onChange(row.row_id, { ...edit, include: event.target.checked })}
                />
              </td>
              <td>
                <div>
                  <strong>{row.test_name_raw}</strong>
                </div>
                <div className="muted">
                  {row.value_raw} {row.unit_raw ?? ""}
                  {row.ref_range_raw && <> · норма бланка {row.ref_range_raw}</>}
                </div>
                {row.needs_review && (
                  <div className="review-hint">
                    Проверьте · уверенность {Math.round(row.confidence * 100)}%
                  </div>
                )}
              </td>
              <td>
                <select
                  className="code-select"
                  aria-label={`Код показателя для «${row.test_name_raw}»`}
                  value={edit.code ?? ""}
                  disabled={readOnly}
                  onChange={(event) =>
                    onChange(row.row_id, { ...edit, code: event.target.value || null })
                  }
                >
                  <option value="">— не распознан —</option>
                  {groups.map(({ group, entries }) => (
                    <optgroup key={group} label={GROUP_LABELS[group]}>
                      {entries.map((entry) => (
                        <option key={entry.code} value={entry.code}>
                          {entry.code} — {entry.name_ru}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </td>
              <td>
                <input
                  className="value-input"
                  type="text"
                  inputMode="decimal"
                  aria-label={`Значение для «${row.test_name_raw}»`}
                  value={edit.value}
                  disabled={readOnly}
                  onChange={(event) => onChange(row.row_id, { ...edit, value: event.target.value })}
                />{" "}
                <span className="muted">{unit ?? ""}</span>
              </td>
              <td>
                {isEdited(row, edit) ? (
                  <span className="muted" title="Флаг пересчитает сервер по справочнику">
                    при подтверждении
                  </span>
                ) : (
                  <span className={`flag flag-${row.flag}`}>{FLAG_LABELS[row.flag]}</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
