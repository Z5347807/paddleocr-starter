export interface ImageInfo {
  filename: string;
  width: number;
  height: number;
}

export interface FieldValue {
  label: string;
  value: string;
  confidence: number;
  edited: boolean;
}

export interface TableData {
  id: string;
  title: string;
  columns: string[];
  rows: Record<string, string>[];
}

export interface RawOcrLine {
  text: string;
  confidence: number;
  box: number[][];
}

export interface WarningItem {
  code: string;
  message: string;
}

export interface RecognitionResult {
  documentType: string;
  image: ImageInfo;
  fields: Record<string, FieldValue>;
  tables: TableData[];
  rawOcr: RawOcrLine[];
  warnings: WarningItem[];
}

export interface TemplateInfo {
  id: string;
  name: string;
}
