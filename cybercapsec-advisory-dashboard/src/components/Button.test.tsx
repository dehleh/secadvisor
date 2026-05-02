import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { Button } from "@/components/Button";

describe("<Button />", () => {
  it("renders children", () => {
    render(<Button>Submit</Button>);
    expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
  });

  it("disables while loading and shows spinner", () => {
    render(<Button loading>Saving</Button>);
    const button = screen.getByRole("button", { name: /Saving/ });
    expect(button).toBeDisabled();
  });

  it("does not invoke onClick when disabled", () => {
    const onClick = vi.fn();
    render(
      <Button disabled onClick={onClick}>
        x
      </Button>,
    );
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("invokes onClick when enabled", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>x</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("respects size variants", () => {
    const { rerender } = render(<Button size="sm">x</Button>);
    expect(screen.getByRole("button").className).toContain("h-8");
    rerender(<Button size="lg">x</Button>);
    expect(screen.getByRole("button").className).toContain("h-12");
  });
});
