import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

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
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
  });

  it("uploads an image and directly downloads the fixed form Excel file", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      expect(url).toBe("/api/export-form");
      expect(init?.method).toBe("POST");
      expect(init?.body).toBeInstanceOf(FormData);
      expect((init?.body as FormData).get("file")).toBeInstanceOf(File);
      return new Response(new Blob(["xlsx"]));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    const user = userEvent.setup();
    const file = new File(["image"], "sample.png", { type: "image/png" });

    await user.upload(screen.getByLabelText("上传表单照片"), file);
    await user.click(screen.getByRole("button", { name: "生成 Excel" }));

    expect(await screen.findByText("Excel 已生成")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalledTimes(1);
  });

  it("keeps the page focused on upload and output instead of field editing", async () => {
    render(<App />);

    expect(screen.getByText("上传照片，自动生成固定表单版 Excel。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "生成 Excel" })).toBeDisabled();
    expect(screen.queryByText("关键字段")).not.toBeInTheDocument();
    expect(screen.queryByText("表格结果")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.queryByLabelText("识别模板")).not.toBeInTheDocument());
  });
});
