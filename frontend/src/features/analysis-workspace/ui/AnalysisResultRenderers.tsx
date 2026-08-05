import { AlertTriangle, Braces, ShieldCheck } from "lucide-react"

import { SourceBadge, StatusBadge } from "@/components/reca-visual-refresh"

import type {
  AnalysisResultViewModel,
  ResultValue,
} from "@/features/analysis-workspace/model"

function numeric(value: ResultValue | undefined) {
  return typeof value === "number" ? value : null
}

function text(value: ResultValue | undefined) {
  return typeof value === "string" ? value : null
}

function record(value: ResultValue | undefined) {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Readonly<Record<string, ResultValue>>)
    : null
}

function list(value: ResultValue | undefined) {
  return Array.isArray(value) ? value : []
}

function formatNumber(value: number | null, digits = 4) {
  if (value === null || !Number.isFinite(value)) return "未提供"
  const magnitude = Math.abs(value)
  if (magnitude > 0 && magnitude < 0.0001) return value.toExponential(3)
  return new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
    useGrouping: true,
  }).format(value)
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="m5-metric">
      <span>{label}</span>
      <strong title={value}>{value}</strong>
    </div>
  )
}

function ConfidenceInterval({ value }: { value: ResultValue | undefined }) {
  const interval = record(value)
  if (!interval) return <Metric label="置信区间" value="未提供" />
  const lower = numeric(interval.lower)
  const upper = numeric(interval.upper)
  const level = numeric(interval.level)
  return (
    <Metric
      label={
        level === null ? "置信区间" : `${formatNumber(level * 100, 2)}% CI`
      }
      value={`${formatNumber(lower)} 至 ${formatNumber(upper)}`}
    />
  )
}

function DescriptiveNumeric({ result }: { result: AnalysisResultViewModel }) {
  const p = result.payload
  return (
    <div className="m5-result-body">
      <div className="m5-result-metrics">
        <Metric label="字段" value={text(p.column_name) ?? "未提供"} />
        <Metric label="N" value={formatNumber(numeric(p.n), 0)} />
        <Metric label="缺失 N" value={formatNumber(numeric(p.missing_n), 0)} />
        <Metric label="均值" value={formatNumber(numeric(p.mean))} />
        <Metric
          label="标准差"
          value={formatNumber(numeric(p.standard_deviation))}
        />
        <Metric label="中位数" value={formatNumber(numeric(p.median))} />
      </div>
      <div className="m5-quartile-track" aria-label="四分位摘要">
        <span>Q1 {formatNumber(numeric(p.q1))}</span>
        <span>Median {formatNumber(numeric(p.median))}</span>
        <span>Q3 {formatNumber(numeric(p.q3))}</span>
      </div>
    </div>
  )
}

function DescriptiveCategorical({
  result,
}: {
  result: AnalysisResultViewModel
}) {
  const p = result.payload
  const categories = record(p.categories) ?? {}
  return (
    <div className="m5-result-body">
      <div className="m5-result-metrics">
        <Metric label="字段" value={text(p.column_name) ?? "未提供"} />
        <Metric label="N" value={formatNumber(numeric(p.n), 0)} />
        <Metric label="缺失 N" value={formatNumber(numeric(p.missing_n), 0)} />
      </div>
      <div className="m5-result-table-wrap" tabIndex={0}>
        <table className="m5-result-table">
          <thead>
            <tr>
              <th>类别</th>
              <th>计数</th>
              <th>比例</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(categories).map(([label, raw]) => {
              const item = record(raw)
              return (
                <tr key={label}>
                  <td>{label}</td>
                  <td>{formatNumber(numeric(item?.count), 0)}</td>
                  <td>
                    {formatNumber((numeric(item?.proportion) ?? 0) * 100, 2)}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Correlation({ result }: { result: AnalysisResultViewModel }) {
  const p = result.payload
  return (
    <div className="m5-result-body">
      <div className="m5-result-metrics">
        <Metric
          label="相关系数"
          value={formatNumber(numeric(p.coefficient), 6)}
        />
        <Metric label="p 值" value={formatNumber(numeric(p.p_value), 6)} />
        <ConfidenceInterval value={p.confidence_interval} />
        <Metric
          label="有效 N"
          value={formatNumber(numeric(p.effective_n), 0)}
        />
        <Metric label="缺失 N" value={formatNumber(numeric(p.missing_n), 0)} />
        <Metric label="备择假设" value={text(p.alternative) ?? "未提供"} />
      </div>
      <div className="m5-scientific-warning" role="note">
        <AlertTriangle aria-hidden="true" />
        <span>相关关系不代表因果关系。结果结构不因显著或不显著而改变。</span>
      </div>
    </div>
  )
}

function GroupComparison({ result }: { result: AnalysisResultViewModel }) {
  const p = result.payload
  return (
    <div className="m5-result-body">
      <div className="m5-result-table-wrap" tabIndex={0}>
        <table className="m5-result-table">
          <thead>
            <tr>
              <th>组别</th>
              <th>N</th>
              <th>均值</th>
            </tr>
          </thead>
          <tbody>
            {list(p.groups).map((raw, index) => {
              const group = record(raw)
              return (
                <tr key={`${text(group?.label) ?? "group"}-${index}`}>
                  <td>{text(group?.label) ?? `组 ${index + 1}`}</td>
                  <td>{formatNumber(numeric(group?.n), 0)}</td>
                  <td>{formatNumber(numeric(group?.mean))}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className="m5-result-metrics">
        <Metric
          label="均值差"
          value={formatNumber(numeric(p.mean_difference))}
        />
        <Metric label="统计量" value={formatNumber(numeric(p.statistic), 6)} />
        <Metric label="df" value={formatNumber(numeric(p.df), 6)} />
        <Metric label="p 值" value={formatNumber(numeric(p.p_value), 6)} />
        <ConfidenceInterval value={p.confidence_interval} />
        <Metric
          label={text(record(p.effect_size)?.name) ?? "效应量"}
          value={formatNumber(numeric(record(p.effect_size)?.value), 6)}
        />
      </div>
    </div>
  )
}

function RegressionEstimate({
  label,
  value,
}: {
  label: string
  value: ResultValue | undefined
}) {
  const item = record(value)
  return (
    <tr>
      <td>{label}</td>
      <td>{formatNumber(numeric(item?.coefficient), 6)}</td>
      <td>{formatNumber(numeric(item?.standard_error), 6)}</td>
      <td>{formatNumber(numeric(item?.p_value), 6)}</td>
      <td>
        {item ? (
          <ConfidenceInterval value={item.confidence_interval} />
        ) : (
          "未提供"
        )}
      </td>
    </tr>
  )
}

function Regression({ result }: { result: AnalysisResultViewModel }) {
  const p = result.payload
  return (
    <div className="m5-result-body">
      <div className="m5-result-metrics">
        <Metric
          label="有效 N"
          value={formatNumber(numeric(p.effective_n), 0)}
        />
        <Metric label="R²" value={formatNumber(numeric(p.r_squared), 6)} />
      </div>
      <div className="m5-result-table-wrap" tabIndex={0}>
        <table className="m5-result-table m5-result-table--wide">
          <thead>
            <tr>
              <th>参数</th>
              <th>系数</th>
              <th>标准误</th>
              <th>p 值</th>
              <th>置信区间</th>
            </tr>
          </thead>
          <tbody>
            <RegressionEstimate label="截距" value={p.intercept} />
            <RegressionEstimate label="斜率" value={p.slope} />
          </tbody>
        </table>
      </div>
    </div>
  )
}

function UnknownResult({ result }: { result: AnalysisResultViewModel }) {
  return (
    <div className="m5-result-body">
      <div className="m5-unknown-result" role="status">
        <Braces aria-hidden="true" />
        <div>
          <strong>未识别的结构化结果</strong>
          <p>保留服务端键值，不从自由文本推导统计数字或图表。</p>
        </div>
      </div>
      <pre className="m5-json-viewer" tabIndex={0}>
        {JSON.stringify(result.payload, null, 2)}
      </pre>
    </div>
  )
}

export function AnalysisResultCard({
  result,
}: {
  result: AnalysisResultViewModel
}) {
  let content
  if (result.type === "DESCRIPTIVE_NUMERIC")
    content = <DescriptiveNumeric result={result} />
  else if (result.type === "DESCRIPTIVE_CATEGORICAL")
    content = <DescriptiveCategorical result={result} />
  else if (result.type === "CORRELATION")
    content = <Correlation result={result} />
  else if (result.type === "GROUP_COMPARISON")
    content = <GroupComparison result={result} />
  else if (result.type === "REGRESSION")
    content = <Regression result={result} />
  else content = <UnknownResult result={result} />

  return (
    <article
      className="m5-result-card"
      data-od-id={`analysis-result-${result.key}`}
    >
      <header className="m5-result-card__header">
        <div>
          <span className="m5-eyebrow">
            {result.primary ? "主要结果" : "补充结果"}
          </span>
          <h3>{result.type}</h3>
        </div>
        <div className="m5-result-card__badges">
          <SourceBadge label="确定性结果" kind="verified" />
          <StatusBadge label={result.status} tone={result.tone} />
        </div>
      </header>
      {content}
      <footer className="m5-result-card__footer">
        <span>
          <ShieldCheck aria-hidden="true" /> schema {result.schemaVersion}
        </span>
        <code title={result.resultHash}>
          {result.resultHash.slice(0, 10)}…{result.resultHash.slice(-6)}
        </code>
      </footer>
    </article>
  )
}
