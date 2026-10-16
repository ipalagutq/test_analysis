"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import Timeline from "@/components/Timeline";
import TrendChart from "@/components/TrendChart";
import {
  ApiError,
  type Patient,
  type Sex,
  type TimelineVisit,
  type Trend,
  getTimeline,
  getTrend,
  listPatients,
} from "@/lib/api";

const SEX_LABELS: Record<Sex, string> = {
  M: "муж.",
  F: "жен.",
};

// shown first when the patient has it: present in every demo blank
const DEFAULT_CODE = "HGB";

interface TestOption {
  code: string;
  name: string;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.detail} (${error.code})`;
  }
  return "Неизвестная ошибка";
}

/** Tests the patient has at least one result for, sorted by name. */
function testOptions(visits: TimelineVisit[]): TestOption[] {
  const names = new Map<string, string>();
  for (const visit of visits) {
    for (const result of visit.results) {
      names.set(result.code, result.name_ru);
    }
  }
  return Array.from(names, ([code, name]) => ({ code, name })).sort((a, b) =>
    a.name.localeCompare(b.name, "ru"),
  );
}

function PatientScreen() {
  const idParam = useSearchParams().get("id");
  const patientId = idParam !== null && /^\d+$/.test(idParam) ? Number(idParam) : null;
  const [patient, setPatient] = useState<Patient | null>(null);
  const [visits, setVisits] = useState<TimelineVisit[] | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [trend, setTrend] = useState<Trend | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [trendError, setTrendError] = useState<string | null>(null);

  useEffect(() => {
    if (patientId === null) {
      return;
    }
    Promise.all([listPatients(), getTimeline(patientId)])
      .then(([patients, loadedVisits]) => {
        setPatient(patients.find((candidate) => candidate.id === patientId) ?? null);
        setVisits(loadedVisits);
        const options = testOptions(loadedVisits);
        const preferred = options.find((option) => option.code === DEFAULT_CODE) ?? options[0];
        setSelectedCode(preferred?.code ?? null);
      })
      .catch((loadError: unknown) => setError(errorMessage(loadError)));
  }, [patientId]);

  useEffect(() => {
    if (patientId === null || selectedCode === null) {
      return;
    }
    let cancelled = false;
    setTrendError(null);
    getTrend(patientId, selectedCode)
      .then((loadedTrend) => {
        if (!cancelled) {
          setTrend(loadedTrend);
        }
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setTrend(null);
          setTrendError(errorMessage(loadError));
        }
      });
    // a slow response for a previously selected test must not overwrite the current one
    return () => {
      cancelled = true;
    };
  }, [patientId, selectedCode]);

  if (patientId === null) {
    return (
      <p className="error" role="alert">
        Не указан пациент: откройте карту после подтверждения черновика.
      </p>
    );
  }

  if (visits === null) {
    return error ? (
      <p className="error" role="alert">
        {error}
      </p>
    ) : (
      <p className="muted">Загружаем карту пациента…</p>
    );
  }

  const options = testOptions(visits);
  const selectedName = options.find((option) => option.code === selectedCode)?.name ?? "";

  return (
    <div className="patient-page">
      <header className="patient-header">
        <h1>{patient ? patient.display_name : `Пациент #${patientId}`}</h1>
        <p className="muted">
          {patient && (
            <>
              {SEX_LABELS[patient.sex]} · {patient.birth_year} г.р. ·{" "}
            </>
          )}
          визитов: {visits.length} · <a href="/">Загрузить новый скан</a>
        </p>
      </header>

      <section className="card">
        <h2>Тренд показателя</h2>
        {options.length === 0 ? (
          <p className="muted">Нет результатов для графика.</p>
        ) : (
          <>
            <label htmlFor="trend-code">Показатель</label>
            <select
              id="trend-code"
              value={selectedCode ?? ""}
              onChange={(event) => setSelectedCode(event.target.value)}
            >
              {options.map((option) => (
                <option key={option.code} value={option.code}>
                  {option.name} ({option.code})
                </option>
              ))}
            </select>
            {trendError && (
              <p className="error" role="alert">
                {trendError}
              </p>
            )}
            {trend && trend.code === selectedCode && (
              <TrendChart trend={trend} title={selectedName} />
            )}
          </>
        )}
      </section>

      <section className="card">
        <h2>Визиты</h2>
        <Timeline visits={visits} selectedCode={selectedCode} />
      </section>
    </div>
  );
}

export default function PatientPage() {
  // useSearchParams needs a Suspense boundary in a static export
  return (
    <Suspense fallback={<p className="muted">Загружаем карту пациента…</p>}>
      <PatientScreen />
    </Suspense>
  );
}
