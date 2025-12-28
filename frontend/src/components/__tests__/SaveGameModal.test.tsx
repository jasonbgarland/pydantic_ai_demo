/**
 * Unit tests for SaveGameModal component
 */
import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { SaveGameModal } from "@/components/SaveGameModal";

describe("SaveGameModal", () => {
  const mockOnClose = jest.fn();
  const mockOnSave = jest.fn();
  const mockGameId = "test-game-123";

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should not render when isOpen is false", () => {
    const { container } = render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={false}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("should render when isOpen is true", () => {
    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByText("Save Game")).toBeInTheDocument();
    expect(screen.getByLabelText("Save Name:")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("My Adventure")).toBeInTheDocument();
  });

  it("should call onSave with session name when Save is clicked", async () => {
    mockOnSave.mockResolvedValue(undefined);

    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");
    const saveButton = screen.getByRole("button", { name: /save/i });

    fireEvent.change(input, { target: { value: "Epic Adventure" } });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith("Epic Adventure");
    });
  });

  it("should disable save button when name is empty", () => {
    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const saveButton = screen.getByRole("button", { name: /^save$/i });

    // Save button should be disabled when input is empty
    expect(saveButton).toBeDisabled();
    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it("should trim whitespace from session name", async () => {
    mockOnSave.mockResolvedValue(undefined);

    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");
    const saveButton = screen.getByRole("button", { name: /save/i });

    fireEvent.change(input, { target: { value: "  Spaced Out  " } });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith("Spaced Out");
    });
  });

  it("should show error message when save fails", async () => {
    mockOnSave.mockRejectedValue(new Error("Network error"));

    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");
    const saveButton = screen.getByRole("button", { name: /save/i });

    fireEvent.change(input, { target: { value: "Test Save" } });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("should show success message and auto-close after successful save", async () => {
    jest.useFakeTimers();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");
    const saveButton = screen.getByRole("button", { name: /save/i });

    fireEvent.change(input, { target: { value: "Test Save" } });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(
        screen.getByText("✓ Game saved successfully!")
      ).toBeInTheDocument();
    });

    // Fast-forward time to trigger auto-close (wrapped in act)
    await act(async () => {
      jest.advanceTimersByTime(1500);
    });

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });

    jest.useRealTimers();
  });

  it("should call onClose when Cancel is clicked", () => {
    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it("should handle Enter key to submit", async () => {
    mockOnSave.mockResolvedValue(undefined);

    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");

    fireEvent.change(input, { target: { value: "Quick Save" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith("Quick Save");
    });
  });

  it("should handle Escape key to close", () => {
    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");

    fireEvent.keyDown(input, { key: "Escape", code: "Escape" });

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should disable buttons while saving", async () => {
    mockOnSave.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");
    const saveButton = screen.getByRole("button", { name: /save/i });
    const cancelButton = screen.getByRole("button", { name: /cancel/i });

    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.click(saveButton);

    // Buttons should be disabled during save
    await waitFor(() => {
      expect(saveButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
      expect(input).toBeDisabled();
    });
  });

  it("should reset form when closed", () => {
    const { rerender } = render(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const input = screen.getByPlaceholderText("My Adventure");
    fireEvent.change(input, { target: { value: "Test Save" } });

    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancelButton);

    // Reopen modal
    rerender(
      <SaveGameModal
        gameId={mockGameId}
        isOpen={true}
        onClose={mockOnClose}
        onSave={mockOnSave}
      />
    );

    const newInput = screen.getByPlaceholderText("My Adventure");
    expect(newInput).toHaveValue("");
  });
});
