import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { Input, Select, Textarea } from "@/components/Field";

describe("<Input />", () => {
  it("renders label and accepts input", () => {
    render(<Input label="Email" name="email" />);
    const input = screen.getByLabelText("Email");
    fireEvent.change(input, { target: { value: "x@y.z" } });
    expect((input as HTMLInputElement).value).toBe("x@y.z");
  });

  it("shows error message and sets aria-invalid", () => {
    render(<Input label="Pwd" name="pwd" error="Too short" />);
    const input = screen.getByLabelText("Pwd");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("Too short")).toBeInTheDocument();
  });

  it("renders required asterisk when required", () => {
    render(<Input label="Name" name="n" required />);
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("shows hint when no error", () => {
    render(<Input label="Pwd" name="p" hint="Min 8 chars" />);
    expect(screen.getByText("Min 8 chars")).toBeInTheDocument();
  });
});

describe("<Textarea />", () => {
  it("renders multiline input", () => {
    render(<Textarea label="Notes" name="n" />);
    const ta = screen.getByLabelText("Notes");
    expect(ta.tagName.toLowerCase()).toBe("textarea");
  });
});

describe("<Select />", () => {
  it("renders options", () => {
    render(
      <Select label="Country" name="c" defaultValue="NG">
        <option value="NG">Nigeria</option>
        <option value="KE">Kenya</option>
      </Select>,
    );
    const select = screen.getByLabelText("Country");
    expect((select as HTMLSelectElement).value).toBe("NG");
  });
});
