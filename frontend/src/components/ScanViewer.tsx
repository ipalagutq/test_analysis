"use client";

import { useState } from "react";

import { draftPageUrl } from "@/lib/api";

interface ScanViewerProps {
  draftId: string;
  pageCount: number;
}

/** Rendered scan pages of a draft with paging; pages are numbered from 0 on the backend. */
export default function ScanViewer({ draftId, pageCount }: ScanViewerProps) {
  const [page, setPage] = useState(0);

  return (
    <div className="scan-viewer">
      <div className="scan-pager">
        <button type="button" onClick={() => setPage(page - 1)} disabled={page === 0}>
          ←
        </button>
        <span>
          Страница {page + 1} из {pageCount}
        </span>
        <button type="button" onClick={() => setPage(page + 1)} disabled={page >= pageCount - 1}>
          →
        </button>
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element -- static export, images are unoptimized */}
      <img
        className="scan-page"
        src={draftPageUrl(draftId, page)}
        alt={`Скан, страница ${page + 1}`}
      />
    </div>
  );
}
