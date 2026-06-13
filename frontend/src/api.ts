import type { RecognitionResult, TemplateInfo } from "./types";

export async function fetchTemplates(): Promise<TemplateInfo[]> {
  const response = await fetch("/api/templates");
  if (!response.ok) {
    throw new Error("模板列表加载失败");
  }
  return response.json();
}

export async function recognizeDocument(file: File, templateId: string): Promise<RecognitionResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("templateId", templateId);

  const response = await fetch("/api/recognize", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "图片识别失败");
  }

  return response.json();
}

export async function exportWorkbook(result: RecognitionResult): Promise<Blob> {
  const response = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "Excel 导出失败");
  }

  return response.blob();
}
