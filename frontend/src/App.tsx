import { useEffect, useMemo, useState } from "react";

import { exportWorkbook, fetchTemplates, recognizeDocument } from "./api";
import type { FieldValue, RecognitionResult, TemplateInfo } from "./types";

type Tab = "fields" | "tables" | "raw";

const DEFAULT_TEMPLATE_ID = "transformer_short_circuit_test_record";

function updateField(result: RecognitionResult, fieldId: string, value: string): RecognitionResult {
  const field: FieldValue = result.fields[fieldId];
  return {
    ...result,
    fields: {
      ...result.fields,
      [fieldId]: { ...field, value, edited: true },
    },
  };
}

function updateTableCell(
  result: RecognitionResult,
  tableIndex: number,
  rowIndex: number,
  columnName: string,
  value: string,
): RecognitionResult {
  return {
    ...result,
    tables: result.tables.map((table, currentTableIndex) => {
      if (currentTableIndex !== tableIndex) {
        return table;
      }
      return {
        ...table,
        rows: table.rows.map((row, currentRowIndex) =>
          currentRowIndex === rowIndex ? { ...row, [columnName]: value } : row,
        ),
      };
    }),
  };
}

export default function App() {
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [templateId, setTemplateId] = useState(DEFAULT_TEMPLATE_ID);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState<RecognitionResult | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("fields");
  const [status, setStatus] = useState("请选择一张表单照片");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchTemplates()
      .then((items) => {
        setTemplates(items);
        if (items[0]) {
          setTemplateId(items[0].id);
        }
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const canExport = useMemo(() => result !== null && !busy, [busy, result]);

  async function handleRecognize() {
    if (!file) {
      setStatus("请先选择图片");
      return;
    }
    setBusy(true);
    setStatus("正在识别图片");
    try {
      const nextResult = await recognizeDocument(file, templateId);
      setResult(nextResult);
      setActiveTab("fields");
      setStatus("识别完成，可以校对后导出 Excel");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "图片识别失败");
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    if (!result) {
      return;
    }
    setBusy(true);
    setStatus("正在生成 Excel");
    try {
      const blob = await exportWorkbook(result);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "recognition-result.xlsx";
      link.click();
      URL.revokeObjectURL(url);
      setStatus("Excel 已生成");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Excel 导出失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>PaddleOCR 表格识别</h1>
          <p>上传现场记录照片，校对识别结果并导出 Excel。</p>
        </div>
        <button type="button" disabled={!canExport} onClick={handleExport}>
          导出 Excel
        </button>
      </header>

      <section className="workspace">
        <aside className="image-panel">
          <label className="field-label" htmlFor="image-upload">
            上传表单照片
          </label>
          <input
            id="image-upload"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => {
              const nextFile = event.target.files?.[0] ?? null;
              setFile(nextFile);
              setResult(null);
              setStatus(nextFile ? "图片已选择，可以开始识别" : "请选择一张表单照片");
            }}
          />

          <label className="field-label" htmlFor="template-select">
            识别模板
          </label>
          <select id="template-select" value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            ))}
          </select>

          <button type="button" disabled={!file || busy} onClick={handleRecognize}>
            开始识别
          </button>
          <p className="status">{status}</p>

          <div className="preview-frame">
            {previewUrl ? <img src={previewUrl} alt="上传的表单预览" /> : <span>图片预览区</span>}
          </div>
        </aside>

        <section className="result-panel">
          <div className="tabs" role="tablist" aria-label="识别结果视图">
            <button type="button" className={activeTab === "fields" ? "active" : ""} onClick={() => setActiveTab("fields")}>
              关键字段
            </button>
            <button type="button" className={activeTab === "tables" ? "active" : ""} onClick={() => setActiveTab("tables")}>
              表格结果
            </button>
            <button type="button" className={activeTab === "raw" ? "active" : ""} onClick={() => setActiveTab("raw")}>
              原始OCR
            </button>
          </div>

          {!result && <div className="empty-state">识别完成后，结果会显示在这里。</div>}

          {result && activeTab === "fields" && (
            <div className="field-grid">
              {Object.entries(result.fields).map(([fieldId, field]) => (
                <label key={fieldId} htmlFor={`field-${fieldId}`}>
                  <span>{field.label}</span>
                  <input
                    id={`field-${fieldId}`}
                    value={field.value}
                    onChange={(event) => setResult(updateField(result, fieldId, event.target.value))}
                  />
                </label>
              ))}
            </div>
          )}

          {result && activeTab === "tables" && (
            <div className="table-stack">
              {result.tables.map((table, tableIndex) => (
                <section key={table.id}>
                  <h2>{table.title}</h2>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          {table.columns.map((column) => (
                            <th key={column}>{column}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {table.rows.map((row, rowIndex) => (
                          <tr key={`${table.id}-${rowIndex}`}>
                            {table.columns.map((column) => (
                              <td key={column}>
                                <input
                                  value={row[column] ?? ""}
                                  onChange={(event) =>
                                    setResult(updateTableCell(result, tableIndex, rowIndex, column, event.target.value))
                                  }
                                />
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              ))}
            </div>
          )}

          {result && activeTab === "raw" && (
            <ol className="raw-list">
              {result.rawOcr.map((line, index) => (
                <li key={`${line.text}-${index}`}>
                  <span>{line.text}</span>
                  <strong>{Math.round(line.confidence * 100)}%</strong>
                </li>
              ))}
            </ol>
          )}
        </section>
      </section>
    </main>
  );
}
