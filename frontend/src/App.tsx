import { useEffect, useState } from "react";

import { exportLayoutWorkbook } from "./api";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [status, setStatus] = useState("请选择一张表单照片");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function handleGenerateExcel() {
    if (!file) {
      setStatus("请先选择图片");
      return;
    }

    setBusy(true);
    setStatus("正在识别并生成 Excel");
    try {
      const blob = await exportLayoutWorkbook(file);
      downloadBlob(blob, "ocr-layout-result.xlsx");
      setStatus("Excel 已生成");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Excel 生成失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>PaddleOCR 版式还原 Excel</h1>
          <p>上传照片，自动生成接近原表单版式的 Excel。</p>
        </div>
      </header>

      <section className="workspace">
        <section className="image-panel" aria-label="图片上传">
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
              setStatus(nextFile ? "图片已选择，点击生成 Excel" : "请选择一张表单照片");
            }}
          />

          <button type="button" disabled={!file || busy} onClick={handleGenerateExcel}>
            生成 Excel
          </button>
          <p className="status">{status}</p>

          <div className="preview-frame">
            {previewUrl ? <img src={previewUrl} alt="上传的表单预览" /> : <span>图片预览区</span>}
          </div>
        </section>

        <section className="output-panel" aria-label="输出说明">
          <h2>输出文件</h2>
          <div className="output-list">
            <div>
              <strong>版式还原</strong>
              <span>按 OCR 坐标把文字放回接近照片位置的 Excel 网格。</span>
            </div>
            <div>
              <strong>OCR明细</strong>
              <span>保留每个识别文本、置信度和原始坐标，方便后续排查。</span>
            </div>
          </div>
          <div className="note">
            当前流程不要求选择模板，也不进入字段校对页；上传后直接生成 Excel。识别精度仍由 PaddleOCR 模型决定，后续可以继续加表格线检测和自动纠错。
          </div>
        </section>
      </section>
    </main>
  );
}
