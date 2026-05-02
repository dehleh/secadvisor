import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import {
  Badge,
  Card,
  CardBody,
  CardTitle,
  EmptyState,
  ErrorMessage,
  ScoreRing,
  SeverityBadge,
  StatusBadge,
} from "@/components/UI";

describe("UI primitives", () => {
  describe("<Badge />", () => {
    it("renders children", () => {
      render(<Badge>Label</Badge>);
      expect(screen.getByText("Label")).toBeInTheDocument();
    });

    it("applies variant classes", () => {
      const { rerender } = render(<Badge variant="success">ok</Badge>);
      expect(screen.getByText("ok").className).toContain("emerald");
      rerender(<Badge variant="danger">bad</Badge>);
      expect(screen.getByText("bad").className).toContain("red");
    });
  });

  describe("<SeverityBadge />", () => {
    it("renders the right label per severity", () => {
      const { rerender } = render(<SeverityBadge severity="critical" />);
      expect(screen.getByText("Critical")).toBeInTheDocument();
      rerender(<SeverityBadge severity="informational" />);
      expect(screen.getByText("Info")).toBeInTheDocument();
    });
  });

  describe("<StatusBadge />", () => {
    it("renders human-readable labels", () => {
      const { rerender } = render(<StatusBadge status="in_progress" />);
      expect(screen.getByText("In progress")).toBeInTheDocument();
      rerender(<StatusBadge status="todo" />);
      expect(screen.getByText("To do")).toBeInTheDocument();
    });
  });

  describe("<Card />", () => {
    it("composes nested parts", () => {
      render(
        <Card>
          <CardTitle>Title</CardTitle>
          <CardBody>Body</CardBody>
        </Card>,
      );
      expect(screen.getByText("Title")).toBeInTheDocument();
      expect(screen.getByText("Body")).toBeInTheDocument();
    });
  });

  describe("<EmptyState />", () => {
    it("renders title and description", () => {
      render(<EmptyState title="Nothing here" description="Try X" />);
      expect(screen.getByText("Nothing here")).toBeInTheDocument();
      expect(screen.getByText("Try X")).toBeInTheDocument();
    });
  });

  describe("<ErrorMessage />", () => {
    it("renders the message", () => {
      render(<ErrorMessage message="Something broke" />);
      expect(screen.getByText("Something broke")).toBeInTheDocument();
    });
  });

  describe("<ScoreRing />", () => {
    it("renders the rounded score", () => {
      render(<ScoreRing score={73.4} />);
      expect(screen.getByText("73")).toBeInTheDocument();
    });

    it("clamps score to 0-100", () => {
      const { rerender } = render(<ScoreRing score={150} />);
      expect(screen.getByText("100")).toBeInTheDocument();
      rerender(<ScoreRing score={-50} />);
      expect(screen.getByText("0")).toBeInTheDocument();
    });
  });
});
