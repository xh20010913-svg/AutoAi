import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { SortableTaskCard } from '@/components/TaskCard'
import type { Task } from '@/lib/api'

function mockTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 'task-1',
    title: 'Test Task',
    description: '',
    status: 'todo',
    priority: 'medium',
    assignee_id: null,
    parent_id: null,
    position: 0,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('SortableTaskCard', () => {
  describe('rendering', () => {
    it('renders task title', () => {
      render(<SortableTaskCard task={mockTask()} onClick={vi.fn()} />)
      expect(screen.getByText('Test Task')).toBeInTheDocument()
    })

    it('renders priority badge', () => {
      render(<SortableTaskCard task={mockTask({ priority: 'high' })} onClick={vi.fn()} />)
      expect(screen.getByText('high')).toBeInTheDocument()
    })

    it('renders description when present', () => {
      render(<SortableTaskCard task={mockTask({ description: 'A description' })} onClick={vi.fn()} />)
      expect(screen.getByText('A description')).toBeInTheDocument()
    })

    it('does not render description when empty', () => {
      render(<SortableTaskCard task={mockTask({ description: '' })} onClick={vi.fn()} />)
      const title = screen.getByText('Test Task')
      const parent = title.parentElement!
      // No paragraph with description text
      expect(parent.querySelector('p')).toBeFalsy()
    })

    it('renders assignee when present', () => {
      render(<SortableTaskCard task={mockTask({ assignee_id: 'user-1' })} onClick={vi.fn()} />)
      expect(screen.getByText('user-1')).toBeInTheDocument()
    })

    it('does not render assignee when null', () => {
      render(<SortableTaskCard task={mockTask({ assignee_id: null })} onClick={vi.fn()} />)
      // Should not render the assignee span
      expect(screen.queryByText(/user-/)).not.toBeInTheDocument()
    })
  })

  describe('interaction', () => {
    it('calls onClick when title is clicked', async () => {
      const onClick = vi.fn()
      const user = userEvent.setup()
      render(<SortableTaskCard task={mockTask()} onClick={onClick} />)

      await user.click(screen.getByText('Test Task'))
      expect(onClick).toHaveBeenCalledTimes(1)
    })

    it('renders drag handle', () => {
      render(<SortableTaskCard task={mockTask()} onClick={vi.fn()} />)
      // The drag handle is an SVG icon from lucide-react
      const dragButton = document.querySelector('.cursor-grab')
      expect(dragButton).toBeInTheDocument()
    })
  })

  describe('priority display', () => {
    it.each(['high', 'medium', 'low', 'none'] as const)('displays %s priority', (priority) => {
      render(<SortableTaskCard task={mockTask({ priority })} onClick={vi.fn()} />)
      expect(screen.getByText(priority)).toBeInTheDocument()
    })
  })
})
