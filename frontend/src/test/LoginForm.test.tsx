import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { LoginForm } from '@/components/LoginForm'

describe('LoginForm', () => {
  describe('rendering', () => {
    it('renders login form with email and password inputs', () => {
      render(<LoginForm />)
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('renders the heading', () => {
      render(<LoginForm />)
      expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
    })
  })

  describe('validation', () => {
    it('shows error when email is empty', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
    })

    it('shows error for invalid email format', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)
      await user.type(screen.getByLabelText(/email/i), 'notanemail')
      await user.type(screen.getByLabelText(/password/i), '123456')
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      expect(await screen.findByText(/invalid email format/i)).toBeInTheDocument()
    })

    it('shows error when password is empty', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })

    it('shows error when password is too short', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)
      await user.type(screen.getByLabelText(/password/i), '12345')
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument()
    })

    it('clears previous errors on resubmit', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), '123456')
      await user.click(screen.getByRole('button', { name: /sign in/i }))

      expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument()
    })
  })

  describe('submission', () => {
    it('calls onSubmit with email and password when valid', async () => {
      const onSubmit = vi.fn()
      const user = userEvent.setup()
      render(<LoginForm onSubmit={onSubmit} />)

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /sign in/i }))

      expect(onSubmit).toHaveBeenCalledWith('test@example.com', 'password123')
      expect(onSubmit).toHaveBeenCalledTimes(1)
    })

    it('does not call onSubmit when validation fails', async () => {
      const onSubmit = vi.fn()
      const user = userEvent.setup()
      render(<LoginForm onSubmit={onSubmit} />)

      await user.click(screen.getByRole('button', { name: /sign in/i }))
      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('shows submitting state while onSubmit is pending', async () => {
      const onSubmit = vi.fn(() => new Promise((resolve) => setTimeout(resolve, 100)))
      const user = userEvent.setup()
      render(<LoginForm onSubmit={onSubmit} />)

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /sign in/i }))

      expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument()
    })

    it('disables button while submitting', async () => {
      let resolvePromise: () => void
      const onSubmit = vi.fn(() => new Promise<void>((resolve) => { resolvePromise = resolve }))
      const user = userEvent.setup()
      render(<LoginForm onSubmit={onSubmit} />)

      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'password123')
      await user.click(screen.getByRole('button', { name: /sign in/i }))

      expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()

      resolvePromise!()
    })
  })

  describe('error display', () => {
    it('displays server error when provided', () => {
      render(<LoginForm error="Invalid credentials" />)
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid credentials')
    })

    it('does not show error element when no error prop', () => {
      render(<LoginForm />)
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })
})
