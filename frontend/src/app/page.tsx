"use client";

import { useRouter } from "next/navigation";
import { type ChangeEvent, type DragEvent, useEffect, useRef, useState } from "react";

import {
  ApiError,
  type Patient,
  type SampleInfo,
  listPatients,
  listSamples,
  sampleUrl,
  uploadScan,
} from "@/lib/api";

const ACCEPTED_TYPES = "application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `${error.detail} (${error.code})`;
  }
  return "Неизвестная ошибка";
}

export default function UploadPage() {
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [samples, setSamples] = useState<SampleInfo[]>([]);
  const [patientId, setPatientId] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listPatients(), listSamples()])
      .then(([loadedPatients, loadedSamples]) => {
        setPatients(loadedPatients);
        setSamples(loadedSamples);
      })
      .catch((loadError: unknown) => setError(errorMessage(loadError)));
  }, []);

  function chooseFile(chosen: File | undefined) {
    if (chosen) {
      setFile(chosen);
      setError(null);
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    chooseFile(event.dataTransfer.files[0]);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(true);
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    chooseFile(event.target.files?.[0]);
  }

  async function handleUpload() {
    if (file === null || patientId === null) {
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const { draft_id } = await uploadScan(file, patientId);
      router.push(`/review/?id=${encodeURIComponent(draft_id)}`);
    } catch (uploadError) {
      setError(errorMessage(uploadError));
      setUploading(false);
    }
  }

  return (
    <>
      <h1>Загрузка скана анализа</h1>

      <section className="card">
        <h2>1. Пациент</h2>
        <label htmlFor="patient">Демо-пациент</label>
        <select
          id="patient"
          value={patientId ?? ""}
          onChange={(event) => setPatientId(event.target.value ? Number(event.target.value) : null)}
          disabled={uploading}
        >
          <option value="">— выберите пациента —</option>
          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.display_name} ({patient.sex === "M" ? "м" : "ж"}, {patient.birth_year})
            </option>
          ))}
        </select>
      </section>

      <section className="card">
        <h2>2. Файл скана</h2>
        <div
          className={dragActive ? "drop-zone active" : "drop-zone"}
          role="button"
          tabIndex={0}
          onClick={() => fileInput.current?.click()}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              fileInput.current?.click();
            }
          }}
          onDragOver={handleDragOver}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
        >
          {file ? (
            <strong>{file.name}</strong>
          ) : (
            <span>Перетащите файл сюда или нажмите, чтобы выбрать</span>
          )}
          <div className="muted">PDF, JPG или PNG</div>
        </div>
        <input
          ref={fileInput}
          type="file"
          accept={ACCEPTED_TYPES}
          hidden
          onChange={handleInputChange}
        />
      </section>

      <section className="card">
        <h2>Примеры сканов</h2>
        <p className="muted">
          Скачайте демо-бланк и загрузите его выше. Пациент из примера выбирается автоматически.
        </p>
        <ul className="samples">
          {samples.map((sample) => (
            <li key={sample.name}>
              <span>{sample.title}</span>
              <a href={sampleUrl(sample.name)} download onClick={() => setPatientId(sample.patient_id)}>
                Скачать пример
              </a>
            </li>
          ))}
        </ul>
      </section>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <div className="actions">
        <button
          type="button"
          onClick={handleUpload}
          disabled={uploading || file === null || patientId === null}
        >
          Распознать
        </button>
        {uploading && <span className="muted">Распознаём скан, это может занять до пары минут…</span>}
      </div>
    </>
  );
}
