import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table"
import {
  Check,
  CircleCheck,
  CircleDashed,
  FileSearch,
  Filter,
  Grid3X3,
  PanelRight,
  RotateCcw,
  TriangleAlert,
  X,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { MutationError, StatusBadge } from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

import type {
  EvidenceMatrixFieldViewModel,
  EvidenceMatrixRowViewModel,
  LiteratureFieldCode,
} from "../model"
import type { EvidenceMatrixWorkspaceProps } from "./contracts"
import { PdfEvidenceViewer } from "./PdfEvidenceViewer"
import "./evidence-matrix-workspace.css"

function fieldLabel(code: LiteratureFieldCode) {
  return code
    .toLowerCase()
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ")
}

function FieldCell({
  field,
  selected,
  onSelect,
}: {
  field: EvidenceMatrixFieldViewModel
  selected: boolean
  onSelect: () => void
}) {
  const disabled = !field.knownStatus
  const EvidenceIcon =
    field.evidenceStatus === "NO_LOCATED_EVIDENCE"
      ? CircleDashed
      : field.evidenceStatus === "LOCATION_UNCERTAIN"
        ? TriangleAlert
        : CircleCheck
  return (
    <button
      type="button"
      className="m3-matrix-field"
      data-selected={selected}
      data-evidence-status={field.evidenceStatus}
      disabled={disabled}
      title={
        disabled
          ? "Unknown field status; selection remains disabled."
          : (field.evidenceLimitations ?? undefined)
      }
      onClick={onSelect}
    >
      <span className="m3-matrix-field__value">
        {field.valueText ?? "No extracted value"}
      </span>
      <span className="m3-matrix-field__meta">
        <span data-status={field.evidenceStatus}>
          <EvidenceIcon aria-hidden="true" /> {field.evidenceStatus}
        </span>
        <span>{field.confidenceLevel} confidence</span>
      </span>
    </button>
  )
}

export function EvidenceMatrixWorkspace(props: EvidenceMatrixWorkspaceProps) {
  const data = props.content.state === "ready" ? props.content.data : null
  const [includedOnly, setIncludedOnly] = useState(false)
  const [sorting, setSorting] = useState<SortingState>([])
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null)
  const [selectedFieldCode, setSelectedFieldCode] =
    useState<LiteratureFieldCode | null>(null)
  const [editorValue, setEditorValue] = useState("")
  const [editorReason, setEditorReason] = useState("")
  const [mobileMode, setMobileMode] = useState<"matrix" | "pdf">("matrix")

  const rows = useMemo(
    () =>
      data?.rows.filter(
        (row) => !includedOnly || row.decision === "INCLUDED",
      ) ?? [],
    [data, includedOnly],
  )
  const includedCount = rows.filter((row) => row.decision === "INCLUDED").length
  const reviewCount = rows.filter(
    (row) => row.extractionStatus === "NEEDS_REVIEW",
  ).length
  const selectedRow =
    rows.find((row) => row.literatureRecordId === selectedRecordId) ??
    rows.find((row) =>
      row.fields.some((field) => field.fieldId === props.selectedFieldId),
    ) ??
    null
  const selectedField =
    selectedRow?.fields.find(
      (field) =>
        field.fieldId === props.selectedFieldId ||
        field.code === selectedFieldCode,
    ) ?? null

  useEffect(() => {
    setEditorValue(selectedField?.valueText ?? "")
    setEditorReason("")
  }, [selectedField?.fieldId, selectedField?.valueText])

  useEffect(() => {
    if (
      selectedRow?.documentId &&
      selectedRow.extractionId &&
      selectedField?.fieldId &&
      props.selectedFieldId !== selectedField.fieldId
    ) {
      props.onEvent({
        action: "open-pdf-location",
        input: {
          literatureRecordId: selectedRow.literatureRecordId,
          documentId: selectedRow.documentId,
          extractionId: selectedRow.extractionId,
          fieldCode: selectedField.code,
          fieldId: selectedField.fieldId,
          evidenceSpanId: selectedField.evidenceSpanId,
          pageNumber: null,
        },
      })
    }
  }, [
    props.onEvent,
    props.selectedFieldId,
    selectedField?.fieldId,
    selectedRow?.literatureRecordId,
  ])

  const selectField = (
    row: EvidenceMatrixRowViewModel,
    field: EvidenceMatrixFieldViewModel,
  ) => {
    setSelectedRecordId(row.literatureRecordId)
    setSelectedFieldCode(field.code)
    if (!row.documentId) return
    props.onEvent({
      action: "open-pdf-location",
      input: {
        literatureRecordId: row.literatureRecordId,
        documentId: row.documentId,
        extractionId: row.extractionId,
        fieldCode: field.code,
        fieldId: field.fieldId,
        evidenceSpanId: field.evidenceSpanId,
        pageNumber: null,
      },
    })
    setMobileMode("pdf")
  }

  const columns = useMemo<ColumnDef<EvidenceMatrixRowViewModel>[]>(
    () => [
      {
        id: "title",
        accessorKey: "title",
        header: "Literature",
        cell: ({ row }) => (
          <button
            type="button"
            className="m3-literature-cell"
            onClick={() => setSelectedRecordId(row.original.literatureRecordId)}
          >
            <strong>{row.original.title}</strong>
            <span>{row.original.authors ?? "Authors unavailable"}</span>
            <small>{row.original.year ?? "Year unknown"}</small>
          </button>
        ),
      },
      ...((data?.fixedFieldCodes ?? []).map((code) => ({
        id: code,
        header: fieldLabel(code),
        accessorFn: (row: EvidenceMatrixRowViewModel) =>
          row.fields.find((field) => field.code === code)?.valueText ?? "",
        enableSorting: false,
        cell: ({ row }: { row: { original: EvidenceMatrixRowViewModel } }) => {
          const field = row.original.fields.find((item) => item.code === code)
          return field ? (
            <FieldCell
              field={field}
              selected={selectedField?.fieldId === field.fieldId}
              onSelect={() => selectField(row.original, field)}
            />
          ) : null
        },
      })) as ColumnDef<EvidenceMatrixRowViewModel>[]),
      {
        id: "decision",
        accessorKey: "decision",
        header: "Decision",
        cell: ({ row }) => (
          <StatusBadge
            label={row.original.decision}
            tone={
              row.original.decision === "INCLUDED"
                ? "success"
                : row.original.decision === "EXCLUDED"
                  ? "danger"
                  : "warning"
            }
          />
        ),
      },
    ],
    [data?.fixedFieldCodes, selectedField?.fieldId],
  )
  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting },
    onSortingChange: (updater) => {
      const next = typeof updater === "function" ? updater(sorting) : updater
      setSorting(next)
      const first = next[0]
      if (first && ["title", "year", "decision"].includes(first.id)) {
        props.onEvent({
          action: "sort",
          input: {
            sort: first.id as "title" | "year" | "decision",
            order: first.desc ? "desc" : "asc",
          },
        })
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (props.content.state === "loading") {
    return (
      <section
        className="m3-evidence-workspace m3-workspace-state"
        aria-busy="true"
      >
        <h1>Evidence Matrix</h1>
        <div className="m3-stable-skeleton" />
      </section>
    )
  }
  if (props.content.state === "error") {
    return (
      <section className="m3-evidence-workspace m3-workspace-state">
        <h1>Evidence Matrix</h1>
        <MutationError {...props.content.error} onRetry={props.onRetry} />
      </section>
    )
  }
  if (props.content.state === "empty") {
    return (
      <section className="m3-evidence-workspace m3-workspace-state">
        <h1>Evidence Matrix</h1>
        <p>{props.content.message}</p>
      </section>
    )
  }
  if (!data) return null

  const canEditSelected =
    selectedRow?.extractionId &&
    selectedField?.fieldId &&
    selectedField.lockVersion !== null
  return (
    <section
      className="m3-evidence-workspace reca-visual-refresh"
      data-od-id="m3-evidence-matrix-workspace"
    >
      <header className="m3-evidence-toolbar">
        <div className="m3-evidence-toolbar__title">
          <h1>Evidence Matrix</h1>
          <div
            className="m3-evidence-toolbar__summary"
            aria-label="Matrix summary"
          >
            <span>{data.total} records</span>
            <span>{includedCount} included</span>
            <span>{reviewCount} awaiting review</span>
          </div>
        </div>
        <div
          className="m3-mode-switch"
          role="group"
          aria-label="Workspace mode"
        >
          <Button
            type="button"
            variant={mobileMode === "matrix" ? "default" : "ghost"}
            aria-pressed={mobileMode === "matrix"}
            onClick={() => setMobileMode("matrix")}
          >
            <Grid3X3 aria-hidden="true" /> Matrix
          </Button>
          <Button
            type="button"
            variant={mobileMode === "pdf" ? "default" : "ghost"}
            aria-pressed={mobileMode === "pdf"}
            onClick={() => setMobileMode("pdf")}
          >
            <PanelRight aria-hidden="true" /> Evidence
          </Button>
        </div>
        <label className="m3-filter-control">
          <input
            type="checkbox"
            checked={includedOnly}
            onChange={(event) => {
              setIncludedOnly(event.target.checked)
              props.onEvent({
                action: "filter",
                input: { includedOnly: event.target.checked, fieldCodes: [] },
              })
            }}
          />
          <Filter aria-hidden="true" /> Included only
        </label>
      </header>
      {data.degraded ? (
        <p className="m3-evidence-notice" role="status">
          Unknown status or permissions are present. Related actions remain
          disabled.
        </p>
      ) : null}
      {props.mutationError ? <MutationError {...props.mutationError} /> : null}
      <div className="m3-evidence-layout" data-mobile-mode={mobileMode}>
        <div className="m3-matrix-pane">
          <div
            className="m3-matrix-scroll"
            role="region"
            aria-label="Scrollable evidence matrix"
            tabIndex={0}
          >
            <table className="m3-matrix-table">
              <thead>
                {table.getHeaderGroups().map((group) => (
                  <tr key={group.id}>
                    {group.headers.map((header) => (
                      <th key={header.id} scope="col">
                        <button
                          type="button"
                          disabled={!header.column.getCanSort()}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                          {header.column.getIsSorted() === "asc"
                            ? " ↑"
                            : header.column.getIsSorted() === "desc"
                              ? " ↓"
                              : ""}
                        </button>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    data-selected={
                      row.original.literatureRecordId ===
                      selectedRow?.literatureRecordId
                    }
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {selectedRow ? (
            <aside
              className="m3-field-inspector"
              aria-label="Selected field and decision controls"
            >
              <header>
                <div>
                  <span className="m3-inspector-kicker">
                    Selected literature
                  </span>
                  <h2>{selectedRow.title}</h2>
                </div>
                <StatusBadge
                  label={selectedRow.decision}
                  tone={
                    selectedRow.decision === "INCLUDED"
                      ? "success"
                      : selectedRow.decision === "EXCLUDED"
                        ? "danger"
                        : "warning"
                  }
                />
              </header>
              {selectedField ? (
                <>
                  <div className="m3-field-inspector__status">
                    <div>
                      <span>Field</span>
                      <strong>{fieldLabel(selectedField.code)}</strong>
                    </div>
                    <StatusBadge
                      label={selectedField.evidenceStatus}
                      tone={
                        selectedField.evidenceStatus === "NO_LOCATED_EVIDENCE"
                          ? "danger"
                          : selectedField.evidenceStatus ===
                              "LOCATION_UNCERTAIN"
                            ? "warning"
                            : "evidence"
                      }
                    />
                  </div>
                  <label>
                    Field value
                    <Input
                      value={editorValue}
                      onChange={(event) => setEditorValue(event.target.value)}
                      disabled={!canEditSelected}
                    />
                  </label>
                  <label>
                    Correction reason
                    <Input
                      value={editorReason}
                      onChange={(event) => setEditorReason(event.target.value)}
                      disabled={!canEditSelected}
                    />
                  </label>
                  <div className="m3-command-row">
                    <Button
                      type="button"
                      disabled={
                        !canEditSelected ||
                        !selectedField.canCorrect ||
                        !editorReason.trim() ||
                        props.pendingAction !== null
                      }
                      title={
                        selectedField.correctionDisabledReason ?? undefined
                      }
                      onClick={() =>
                        props.onEvent({
                          action: "correct-field",
                          input: {
                            literatureRecordId: selectedRow.literatureRecordId,
                            extractionId: selectedRow.extractionId!,
                            fieldId: selectedField.fieldId!,
                            lockVersion: selectedField.lockVersion!,
                            valueText: editorValue || null,
                            evidenceSpanId: selectedField.evidenceSpanId,
                            reason: editorReason,
                          },
                        })
                      }
                    >
                      <RotateCcw aria-hidden="true" /> Correct
                    </Button>
                    <Button
                      type="button"
                      disabled={
                        !canEditSelected ||
                        !selectedField.canConfirm ||
                        !editorReason.trim() ||
                        props.pendingAction !== null
                      }
                      onClick={() =>
                        props.onEvent({
                          action: "confirm-field",
                          input: {
                            literatureRecordId: selectedRow.literatureRecordId,
                            extractionId: selectedRow.extractionId!,
                            fieldId: selectedField.fieldId!,
                            lockVersion: selectedField.lockVersion!,
                            valueText: editorValue || null,
                            evidenceSpanId: selectedField.evidenceSpanId,
                            reason: editorReason,
                          },
                        })
                      }
                    >
                      <Check aria-hidden="true" /> Confirm
                    </Button>
                  </div>
                </>
              ) : (
                <p>Select a field to inspect its evidence.</p>
              )}
              <div className="m3-decision-block">
                <div>
                  <span className="m3-inspector-kicker">Human decision</span>
                  <h3>Literature scope</h3>
                </div>
                <div
                  className="m3-command-row"
                  aria-label="Literature decision"
                >
                  <Button
                    type="button"
                    variant="outline"
                    disabled={
                      !selectedRow.canDecide || props.pendingAction !== null
                    }
                    onClick={() =>
                      props.onEvent({
                        action: "decide-literature",
                        input: {
                          literatureRecordId: selectedRow.literatureRecordId,
                          decision: "INCLUDED",
                          reasonCode: "RELEVANT_OBJECT_AND_METHOD",
                          reasonText: "Included after evidence review.",
                        },
                      })
                    }
                  >
                    <Check aria-hidden="true" /> Include
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={
                      !selectedRow.canDecide || props.pendingAction !== null
                    }
                    onClick={() =>
                      props.onEvent({
                        action: "decide-literature",
                        input: {
                          literatureRecordId: selectedRow.literatureRecordId,
                          decision: "UNCERTAIN",
                          reasonCode: "OTHER",
                          reasonText: "Further review is required.",
                        },
                      })
                    }
                  >
                    <FileSearch aria-hidden="true" /> Uncertain
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={
                      !selectedRow.canDecide || props.pendingAction !== null
                    }
                    onClick={() =>
                      props.onEvent({
                        action: "decide-literature",
                        input: {
                          literatureRecordId: selectedRow.literatureRecordId,
                          decision: "EXCLUDED",
                          reasonCode: "QUALITY_ISSUE",
                          reasonText: "Excluded after evidence review.",
                        },
                      })
                    }
                  >
                    <X aria-hidden="true" /> Exclude
                  </Button>
                </div>
              </div>
            </aside>
          ) : null}
        </div>
        <div className="m3-pdf-pane">
          {props.pdfViewer ? (
            <PdfEvidenceViewer value={props.pdfViewer} />
          ) : (
            <div className="m3-pdf-empty">
              <FileSearch aria-hidden="true" />
              <p>
                Select an evidence-backed field to open its server-authorized
                document location.
              </p>
            </div>
          )}
          {props.pdfViewer?.selectedSpan ? (
            <div className="m3-verification-controls">
              <Button
                type="button"
                disabled={
                  !props.pdfViewer.selectedSpan.canVerify ||
                  props.pendingAction !== null
                }
                title={
                  props.pdfViewer.selectedSpan.verifyDisabledReason ?? undefined
                }
                onClick={() =>
                  props.onEvent({
                    action: "verify-evidence",
                    input: {
                      literatureRecordId: selectedRow?.literatureRecordId ?? "",
                      evidenceSpanId:
                        props.pdfViewer!.selectedSpan!.evidenceSpanId,
                      locationStatus: "VERIFIED",
                      readScope: props.pdfViewer!.selectedSpan!.readScope as
                        | "UNKNOWN"
                        | "ABSTRACT"
                        | "SECTIONS"
                        | "FULL_TEXT_DECLARED",
                      reviewedPages: [props.pdfViewer!.selectedPage],
                      note: "Verified against the displayed server document page.",
                    },
                  })
                }
              >
                <Check aria-hidden="true" /> Verify location
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={
                  !props.pdfViewer.selectedSpan.canReject ||
                  props.pendingAction !== null
                }
                onClick={() =>
                  props.onEvent({
                    action: "reject-evidence",
                    input: {
                      literatureRecordId: selectedRow?.literatureRecordId ?? "",
                      evidenceSpanId:
                        props.pdfViewer!.selectedSpan!.evidenceSpanId,
                      locationStatus: "LOCATION_UNCERTAIN",
                      readScope: props.pdfViewer!.selectedSpan!.readScope as
                        | "UNKNOWN"
                        | "ABSTRACT"
                        | "SECTIONS"
                        | "FULL_TEXT_DECLARED",
                      reviewedPages: [props.pdfViewer!.selectedPage],
                      note: "Location rejected or remains uncertain after review.",
                    },
                  })
                }
              >
                <X aria-hidden="true" /> Reject
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}
