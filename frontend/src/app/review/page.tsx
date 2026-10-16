"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import ReviewTable, { type RowEdit, initialEdit } from "@/components/ReviewTable";
import ScanViewer from "@/components/ScanViewer";
import {
  ApiError,
  type CatalogEntry,
  type ConfirmRow,
  type Draft,
  type DraftStatus,
  confirmDraft,
  discardDraft,
  getDraft,
  listCatalog,
} from "@/lib/api";

const STATUS_LABELS: Record<DraftStatus, string> = {
  draft: "черновик",
  confirmed: "подтверждён",
  discarded: "отклонён",
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.detail} (${error.code})`;
  }
  return "Неизвестная ошибка";
}

/** Today's date in local time as `YYYY-MM-DD`. */
function today(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/** Parse the value input; accepts a decimal comma, empty or non-numeric text gives null. */
function parseValue(text: string): number | null {
  const normalized = text.trim().replace(",", ".");
  if (normalized === "") {
    return null;
  }
  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

function initialEdits(draft: Draft): Record<number, RowEdit> {
  return Object.fromEntries(draft.rows.map((row) => [row.row_id, initialEdit(row)]));
}

function ReviewScreen() {
  const router = useRouter();
  const draftId = useSearchParams().get("id");
  const [draft, setDraft] = useState<Draft | null>(null);
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [edits, setEdits] = useState<Record<number, RowEdit>>({});
  const [collectedAt, setCollectedAt] = useState(today);
  const [invalidRowIds, setInvalidRowIds] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!draftId) {
      return;
    }
    Promise.all([getDraft(draftId), listCatalog()])
      .then(([loadedDraft, loadedCatalog]) => {
        setDraft(loadedDraft);
        setEdits(initialEdits(loadedDraft));
        setCatalog(loadedCatalog);
      })
      .catch((loadError: unknown) => setError(errorMessage(loadError)));
  }, [draftId]);

  if (!draftId) {
    return (
      <p className="error" role="alert">
        Не указан черновик: откройте экран проверки после загрузки скана.
      </p>
    );
  }

  if (draft === null) {
    return error ? (
      <p className="error" role="alert">
        {error}
      </p>
    ) : (
      <p className="muted">Загружаем черновик…</p>
    );
  }

  const readOnly = draft.status !== "draft" || busy;
  const includedCount = draft.rows.filter((row) => edits[row.row_id]?.include).length;

  function handleRowChange(rowId: number, edit: RowEdit) {
    setEdits((current) => ({ ...current, [rowId]: edit }));
    setInvalidRowIds((current) => current.filter((id) => id !== rowId));
  }

  async function handleConfirm() {
    if (draft === null) {
      return;
    }
    const rows: ConfirmRow[] = draft.rows.map((row) => {
      const edit = edits[row.row_id] ?? initialEdit(row);
      return {
        row_id: row.row_id,
        code: edit.code,
        canonical_value: parseValue(edit.value),
        include: edit.include,
      };
    });
    setBusy(true);
    setError(null);
    try {
      await confirmDraft(draft.id, { collected_at: collectedAt, rows });
      router.push(`/patient/?id=${draft.patient_id}`);
    } catch (confirmError) {
      if (confirmError instanceof ApiError && confirmError.code === "invalid_confirm_rows") {
        setInvalidRowIds(confirmError.rowIds);
        setError(
          "Ничего не записано: у отмеченных красным строк нет кода из справочника или числового значения. Исправьте их или снимите галочку «В карту».",
        );
      } else {
        setError(errorMessage(confirmError));
        if (confirmError instanceof ApiError && confirmError.status === 409) {
          getDraft(draft.id).then(setDraft).catch(() => undefined);
        }
      }
      setBusy(false);
    }
  }

  async function handleDiscard() {
    if (draft === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setDraft(await discardDraft(draft.id));
    } catch (discardError) {
      setError(errorMessage(discardError));
    }
    setBusy(false);
  }

  return (
    <div className="review-page">
      <h1>Проверка распознанных показателей</h1>

      <p className="muted">
        Статус: <strong>{STATUS_LABELS[draft.status]}</strong> · экстрактор {draft.extractor}
        {draft.model && <> · модель {draft.model}</>}
      </p>

      {draft.status !== "draft" && (
        <p className="status-note" role="status">
          Черновик {STATUS_LABELS[draft.status]}, открыт только для просмотра.
          {draft.status === "confirmed" && (
            <>
              {" "}
              <a href={`/patient/?id=${draft.patient_id}`}>Открыть карту пациента</a>
            </>
          )}
        </p>
      )}

      <div className="review-layout">
        <section className="card">
          <ScanViewer draftId={draft.id} pageCount={draft.page_count} />
        </section>

        <section className="card">
          <ReviewTable
            rows={draft.rows}
            edits={edits}
            catalog={catalog}
            invalidRowIds={invalidRowIds}
            readOnly={readOnly}
            onChange={handleRowChange}
          />

          {draft.status === "draft" && (
            <div className="review-footer">
              <div>
                <label htmlFor="collected-at">Дата забора</label>
                <input
                  id="collected-at"
                  type="date"
                  value={collectedAt}
                  max={today()}
                  disabled={busy}
                  onChange={(event) => setCollectedAt(event.target.value)}
                />
              </div>

              {error && (
                <p className="error" role="alert">
                  {error}
                </p>
              )}

              <div className="actions">
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={busy || collectedAt === "" || includedCount === 0}
                >
                  Подтвердить ({includedCount})
                </button>
                <button type="button" className="secondary" onClick={handleDiscard} disabled={busy}>
                  Отклонить
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  // useSearchParams needs a Suspense boundary in a static export
  return (
    <Suspense fallback={<p className="muted">Загружаем черновик…</p>}>
      <ReviewScreen />
    </Suspense>
  );
}
