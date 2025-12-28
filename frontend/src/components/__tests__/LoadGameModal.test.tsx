/**
 * Unit tests for LoadGameModal component
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LoadGameModal } from "@/components/LoadGameModal";

describe("LoadGameModal", () => {
  const mockOnClose = jest.fn();
  const mockOnLoad = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnFetchSaves = jest.fn();

  const mockSavedGames = [
    {
      game_id: "game-1",
      session_name: "Epic Adventure",
      character_name: "Warrior Bob",
      character_class: "warrior",
      level: 5,
      location: "Dark Cave",
      turn_count: 42,
      last_played: "2025-12-28T10:00:00Z",
      created_at: "2025-12-27T08:00:00Z",
    },
    {
      game_id: "game-2",
      session_name: "Wizard Quest",
      character_name: "Merlin",
      character_class: "wizard",
      level: 3,
      location: "Magic Tower",
      turn_count: 20,
      last_played: "2025-12-27T15:00:00Z",
      created_at: "2025-12-26T12:00:00Z",
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnFetchSaves.mockResolvedValue(mockSavedGames);
  });

  it("should not render when isOpen is false", () => {
    const { container } = render(
      <LoadGameModal
        isOpen={false}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("should fetch and display saved games when opened", async () => {
    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    expect(screen.getByText("Load Game")).toBeInTheDocument();
    expect(screen.getByText("Loading saved games...")).toBeInTheDocument();

    await waitFor(() => {
      expect(mockOnFetchSaves).toHaveBeenCalled();
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
      expect(screen.getByText("Wizard Quest")).toBeInTheDocument();
    });
  });

  it("should display saved game details correctly", async () => {
    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Warrior Bob - Level 5 warrior")
    ).toBeInTheDocument();
    expect(screen.getByText("Dark Cave")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("should show empty state when no saves exist", async () => {
    mockOnFetchSaves.mockResolvedValue([]);

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No saved games found.")).toBeInTheDocument();
    });
  });

  it("should call onLoad when Load button is clicked", async () => {
    mockOnLoad.mockResolvedValue(undefined);

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const loadButtons = screen.getAllByRole("button", { name: /^load$/i });
    fireEvent.click(loadButtons[0]);

    await waitFor(() => {
      expect(mockOnLoad).toHaveBeenCalledWith("game-1");
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it("should show confirmation before deleting", async () => {
    global.confirm = jest.fn(() => false);

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    expect(global.confirm).toHaveBeenCalledWith(
      "Are you sure you want to delete this save?"
    );
    expect(mockOnDelete).not.toHaveBeenCalled();
  });

  it("should delete save when confirmed", async () => {
    global.confirm = jest.fn(() => true);
    mockOnDelete.mockResolvedValue(undefined);

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(mockOnDelete).toHaveBeenCalledWith("game-1");
    });

    // Save should be removed from list
    await waitFor(() => {
      expect(screen.queryByText("Epic Adventure")).not.toBeInTheDocument();
      expect(screen.getByText("Wizard Quest")).toBeInTheDocument();
    });
  });

  it("should display error when fetch fails", async () => {
    mockOnFetchSaves.mockRejectedValue(new Error("Network error"));

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("should display error when load fails", async () => {
    mockOnLoad.mockRejectedValue(new Error("Failed to load game"));

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const loadButtons = screen.getAllByRole("button", { name: /^load$/i });
    fireEvent.click(loadButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Failed to load game")).toBeInTheDocument();
    });

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it("should display error when delete fails", async () => {
    global.confirm = jest.fn(() => true);
    mockOnDelete.mockRejectedValue(new Error("Failed to delete"));

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Failed to delete")).toBeInTheDocument();
    });
  });

  it("should disable buttons while loading a game", async () => {
    mockOnLoad.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const loadButtons = screen.getAllByRole("button", { name: /^load$/i });
    fireEvent.click(loadButtons[0]);

    // Wait for Loading... text to appear
    await waitFor(() => {
      expect(screen.getByText("Loading...")).toBeInTheDocument();
    });

    // The button that's loading should be disabled
    const loadingButton = screen.getByText("Loading...").closest("button");
    expect(loadingButton).toBeDisabled();
  });

  it("should disable buttons while deleting a game", async () => {
    global.confirm = jest.fn(() => true);
    mockOnDelete.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("Deleting...")).toBeInTheDocument();
    });
  });

  it("should call onClose when Close button is clicked", async () => {
    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    const closeButton = screen.getByRole("button", { name: /close/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should format dates correctly", async () => {
    render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Epic Adventure")).toBeInTheDocument();
    });

    // Date formatting will depend on locale, just check it renders something
    const dateElements = screen.getAllByText(/Last Played:/);
    expect(dateElements.length).toBeGreaterThan(0);
  });

  it("should refetch saves when modal reopens", async () => {
    const { rerender } = render(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(mockOnFetchSaves).toHaveBeenCalledTimes(1);
    });

    // Close modal
    rerender(
      <LoadGameModal
        isOpen={false}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    // Reopen modal
    rerender(
      <LoadGameModal
        isOpen={true}
        onClose={mockOnClose}
        onLoad={mockOnLoad}
        onDelete={mockOnDelete}
        onFetchSaves={mockOnFetchSaves}
      />
    );

    await waitFor(() => {
      expect(mockOnFetchSaves).toHaveBeenCalledTimes(2);
    });
  });
});
