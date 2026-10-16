"use client";

import type { Flag, TimelineVisit } from "@/lib/api";

const FLAG_LABELS: Record<Flag, string> = {
  low: "↓ ниже",
  normal: "норма",
  high: "↑ выше",
  unknown: "—",
};

interface TimelineProps {
  /** Visits newest first, as the API returns them. */
  visits: TimelineVisit[];
  /** Highlight the results of the test shown on the trend chart. */
  selectedCode: string | null;
}

/** Patient visits with their confirmed results and computed flags. */
export default function Timeline({ visits, selectedCode }: TimelineProps) {
  if (visits.length === 0) {
    return <p className="muted">Подтверждённых визитов пока нет.</p>;
  }

  return (
    <ol className="timeline">
      {visits.map((visit) => (
        <li key={visit.visit_id} className="timeline-visit">
          <h3>
            {visit.collected_at}
            <span className="muted">
              {" "}
              · {visit.results.length} показ.{visit.model && <> · модель {visit.model}</>}
            </span>
          </h3>
          <table className="review-table">
            <thead>
              <tr>
                <th>Показатель</th>
                <th>Значение</th>
                <th>Ед.</th>
                <th>Флаг</th>
              </tr>
            </thead>
            <tbody>
              {visit.results.map((result) => (
                <tr
                  key={result.code}
                  className={result.code === selectedCode ? "selected" : undefined}
                >
                  <td>
                    {result.name_ru} <span className="muted">{result.code}</span>
                  </td>
                  <td>{result.value}</td>
                  <td>{result.unit}</td>
                  <td>
                    <span className={`flag flag-${result.flag}`}>{FLAG_LABELS[result.flag]}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </li>
      ))}
    </ol>
  );
}
