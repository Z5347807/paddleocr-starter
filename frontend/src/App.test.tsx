import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const recognition = {
  documentType: "transformer_short_circuit_test_record",
  image: { filename: "sample.png", width: 64, height: 48 },
  fields: {
    centerNumber: { label: "中心编号", value: "B260112", confidence: 0.93, edited: false },
  },
  tables: [
    {
      id: "before_test_reactance",
      title: "试验前电抗测量",
      columns: ["分接", "AB", "BC"],
      rows: [{ "分接": "1", AB: "281.25", BC: "281.15" }],
    },
  ],
  rawOcr: [{ text: "中心编号：B260112", confidence: 0.93, box: [[1, 2], [3, 2], [3, 4], [1, 4]] }],
  warnings: [],
};

describe("App", () => {
  beforeEach(() => {
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:preview"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/templates") {
          return new Response(
            JSON.stringify([{ id: "transformer_short_circuit_test_record", name: "变压器短路承受能力试验现场记录" }]),
          );
        }
        if (url === "/api/recognize") {
          return new Response(JSON.stringify(recognition));
        }
        return new Response(null, { status: 404 });
      }),
    );
  });

  it("uploads an image and renders recognition results", async () => {
    render(<App />);
    const user = userEvent.setup();
    const file = new File(["image"], "sample.png", { type: "image/png" });

    await user.upload(screen.getByLabelText("上传表单照片"), file);
    await user.click(screen.getByRole("button", { name: "开始识别" }));

    expect(await screen.findByDisplayValue("B260112")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "表格结果" }));

    expect(screen.getByText("试验前电抗测量")).toBeInTheDocument();
    expect(screen.getByDisplayValue("281.25")).toBeInTheDocument();
  });
});
