import { AlertTriangle, FileText, LoaderCircle } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"

import {
  DegradedNotice,
  SourceBadge,
  StatusBadge,
} from "@/components/reca-visual-refresh"

import type { PdfEvidenceViewerViewModel } from "../model"

type NormalizedBox = {
  left: number
  top: number
  width: number
  height: number
}

const workerUrl = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString()

export function normalizeEvidenceBox(
  value: Record<string, unknown>,
  pageNumber: number,
): NormalizedBox | null {
  const page = Number(value.page)
  const left = Number(value.x)
  const top = Number(value.y)
  const width = Number(value.width)
  const height = Number(value.height)
  if (
    page !== pageNumber ||
    ![left, top, width, height].every(Number.isFinite) ||
    left < 0 ||
    top < 0 ||
    width <= 0 ||
    height <= 0 ||
    left + width > 1 ||
    top + height > 1
  ) {
    return null
  }
  return { left, top, width, height }
}

export function PdfEvidenceViewer({
  value,
}: {
  value: PdfEvidenceViewerViewModel
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [renderState, setRenderState] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle")
  const [renderError, setRenderError] = useState<string | null>(null)
  const boxes = useMemo(
    () =>
      (value.selectedSpan?.boundingBoxes ?? [])
        .map((box) => normalizeEvidenceBox(box, value.selectedPage))
        .filter((box): box is NormalizedBox => box !== null),
    [value.selectedPage, value.selectedSpan],
  )

  useEffect(() => {
    let cancelled = false
    let renderTask: import("pdfjs-dist").RenderTask | null = null
    let loadingTask: import("pdfjs-dist").PDFDocumentLoadingTask | null = null
    if (!value.authorizedPdfUrl || !canvasRef.current) {
      setRenderState("idle")
      return
    }
    const render = async () => {
      setRenderState("loading")
      setRenderError(null)
      try {
        const pdfjs = await import("pdfjs-dist")
        pdfjs.GlobalWorkerOptions.workerSrc = workerUrl
        loadingTask = pdfjs.getDocument({
          url: value.authorizedPdfUrl!,
          withCredentials: true,
        })
        const loadedPdf = await loadingTask.promise
        const page = await loadedPdf.getPage(value.selectedPage)
        const viewport = page.getViewport({ scale: 1.35 })
        const canvas = canvasRef.current
        if (!canvas || cancelled) return
        const context = canvas.getContext("2d")
        if (!context) throw new Error("Canvas rendering is unavailable.")
        canvas.width = Math.ceil(viewport.width)
        canvas.height = Math.ceil(viewport.height)
        const task = page.render({ canvas, canvasContext: context, viewport })
        renderTask = task
        await task.promise
        if (!cancelled) setRenderState("ready")
      } catch (error) {
        if (!cancelled) {
          setRenderState("error")
          setRenderError(
            error instanceof Error ? error.message : "PDF rendering failed.",
          )
        }
      }
    }
    void render()
    return () => {
      cancelled = true
      renderTask?.cancel()
      void loadingTask?.destroy()
    }
  }, [value.authorizedPdfUrl, value.selectedPage])

  return (
    <section className="m3-pdf-viewer" aria-label="PDF evidence viewer">
      <header className="m3-pdf-viewer__header">
        <div>
          <span className="m3-pdf-viewer__kicker">Document evidence</span>
          <strong>Page {value.selectedPage}</strong>
        </div>
        <div className="m3-pdf-viewer__status">
          <SourceBadge
            label={value.parserType ?? "Parser unknown"}
            kind={value.parserType === "PYPDF" ? "degraded" : "evidence"}
          />
          {value.selectedSpan ? (
            <StatusBadge
              label={value.selectedSpan.locationStatus}
              tone={value.selectedSpan.tone}
            />
          ) : null}
          {renderState === "loading" ? (
            <LoaderCircle className="m3-spin" aria-label="Loading PDF page" />
          ) : null}
        </div>
      </header>
      {value.degradedReason ? (
        <DegradedNotice
          title="Text-only evidence location"
          message={value.degradedReason}
        />
      ) : null}
      {value.authorizedPdfUrl ? (
        <div className="m3-pdf-canvas-wrap" data-render-state={renderState}>
          <canvas
            ref={canvasRef}
            aria-label={`PDF page ${value.selectedPage}`}
          />
          {renderState === "ready"
            ? boxes.map((box, index) => (
                <span
                  // The overlay is display-only; the server remains the coordinate authority.
                  key={`${box.left}-${box.top}-${index}`}
                  className="m3-pdf-highlight"
                  style={{
                    left: `${box.left * 100}%`,
                    top: `${box.top * 100}%`,
                    width: `${box.width * 100}%`,
                    height: `${box.height * 100}%`,
                  }}
                />
              ))
            : null}
        </div>
      ) : (
        <div className="m3-pdf-fallback">
          <FileText aria-hidden="true" />
          <p>Authorized PDF bytes are unavailable.</p>
        </div>
      )}
      {renderError ? (
        <p className="m3-evidence-notice" role="alert">
          <AlertTriangle aria-hidden="true" />
          {renderError}
        </p>
      ) : null}
      {value.selectedSpan ? (
        <blockquote className="m3-source-context">
          <header>
            <strong>Server evidence text</strong>
            <span>{value.selectedSpan.readScope}</span>
          </header>
          <p>{value.selectedSpan.sourceText}</p>
          <footer>
            <span>SHA-256</span>
            <code>{value.selectedSpan.sourceTextHash}</code>
          </footer>
        </blockquote>
      ) : value.pageText ? (
        <blockquote className="m3-source-context">
          <strong>Server page text</strong>
          <p>{value.pageText}</p>
        </blockquote>
      ) : null}
    </section>
  )
}
